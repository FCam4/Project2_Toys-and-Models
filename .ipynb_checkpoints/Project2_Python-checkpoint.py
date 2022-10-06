# import libraries

import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
import numpy as np
#import datetime
import mysql.connector 
import seaborn as sns


connection=mysql.connector.connect(user = 'toyscie', password = 'WILD4Rdata!', host = '51.68.18.102', port = '23456', database = 'toys_and_models')


query_sales= '''WITH productline_quantity AS (
SELECT productline, YEAR(orderDate) order_year, SUM(quantityordered) order_quantity, MONTH(orderDate) order_month
FROM orders
INNER JOIN orderdetails USING (orderNumber)
INNER JOIN products USING (productCode)
GROUP BY productline, order_year, order_month
)
SELECT productline, order_year, order_month, order_quantity,
LAG(order_quantity, 1) OVER (
PARTITION BY productLine, order_month
ORDER BY order_month, order_year) as prev_year_order_quantity, (order_quantity * 100)/lag(order_quantity, 1) OVER (
        PARTITION BY productLine, order_month
        ORDER BY order_month, order_year) as ratechange
FROM
    productline_quantity'''

df_sales= pd.read_sql(query_sales, con=connection)


query_finances_to='''select country, sum(priceeach*quantityordered) as turnover
from orders o
join orderdetails od on od.ordernumber=o.ordernumber
join customers c on c.customernumber=o.customernumber
WHERE orderdate >= DATE_FORMAT(CURDATE(), '%Y-%m-01') - INTERVAL 2 MONTH
Group by country
order by turnover desc''' 

df_finances_to = pd.read_sql(query_finances_to, con=connection)
df_finances_to.head(7)

query_finances_o= '''select o.customernumber, sum(distinct od.quantityordered*od.priceEach) as Total_Amount_Ordered, sum(distinct p.amount) as Total_Amount_Paid, sum(distinct od.quantityordered*od.priceEach) - sum(distinct p.amount) as difference
from orderdetails od
join orders o on o.ordernumber=od.ordernumber
join payments p on p.customernumber=o.customernumber
group by customernumber
having difference > 0'''


df_finances_o = pd.read_sql(query_finances_o, con=connection)
df_finances_o.head(12)


query_logistics= '''select p.productname,p.productline, sum(od.quantityordered) as sumOrdered, p.quantityinstock from products p join orderdetails od on p.productcode=od.productCode
group by p.productname
order by sumOrdered desc
limit 5'''

df_logistics=pd.read_sql(query_logistics, con=connection)

query_hr= '''WITH top_sellers AS (select e.employeeNumber, e.firstname, jobTitle, e.lastname, DATE_FORMAT(o.orderdate, "%c %Y") as DateOrd, year(o.orderdate) as YearOrd, month(o.orderdate) as month_,sum(od.quantityordered*od.priceeach) as highest_turnover,
RANK() OVER (PARTITION BY DateOrd ORDER BY highest_turnover DESC) sell_rank from employees e
join customers c on e.employeeNumber=c.salesRepEmployeeNumber
join orders o on c.customerNumber=o.customerNumber
join orderdetails od on o.orderNumber=od.orderNumber
WHERE jobTitle like 'Sales Rep%' and o.status <> 'Cancelled'
Group by DateOrd, employeeNumber
Order by DateOrd, highest_turnover DESC)
select * from top_sellers
where sell_rank=1 or sell_rank=2;'''

df_hr = pd.read_sql(query_hr, con=connection)
df_hr.head(53)
df_hr = df_hr[df_hr['YearOrd'] == 2021]
print(df_hr)


add_selectbox = st.sidebar.radio(
    "Topics",
    ("Sales", "Finance Turnover","Finance Orders", "Logistics", "HR"))


if add_selectbox=='Sales':
    st.title('''Sales''')
    st.subheader('''The rate of change compared to the same month of the previous year:''')
    fig2, ax2 = plt.subplots(figsize=(10,4))
    colors=['grey', 'black']
    sns.barplot(data=df_sales, x="order_month", y="ratechange", hue="order_year", ci=None, palette=colors)
    ax2.set_xlabel("Month")
    ax2.set_ylabel("Rate of change (%)")
    ax2.legend(title="Year: ")
    ax2.set_title('Rate of change')
    st.pyplot(fig2)
    st.write("  ")
    #Second Graphic
    st.subheader('''The number of products sold by category:''')
    fig3, ax3 = plt.subplots(figsize=(10,4))
    colors=['grey', 'black', 'blue']
    sns.barplot(data=df_sales, x="productline", y="order_quantity", hue="order_year", ci=None, palette=colors)
    ax3.set_xlabel("Categories")
    ax3.set_ylabel("# orders")
    ax3.legend(title="Year: ")
    ax3.set_title('# products by category')
    st.pyplot(fig3)
elif add_selectbox == 'Finance Turnover':
    st.title('''Finances''')
    st.subheader('''The turnover of the orders of the last two months by country:''')
    st.info('Information from last 2 months', icon="ℹ️")
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.bar(df_finances_to["country"], df_finances_to["turnover"], color="grey")
    ax.set_title('The turnover of orders')
    ax.set_ylabel('Orders')
    ax.set_xlabel('Country')
    fig.autofmt_xdate()
    st.pyplot(fig)
    st.set_option('deprecation.showPyplotGlobalUse', False)
elif add_selectbox == 'Finance Orders':
    st.title('''Finances''')
    st.subheader('''Orders that have not yet been paid:''')
    st.write("  ")
    st.subheader('Total amount yet to be paid = 470 985,19')
    fig, ax = plt.subplots(figsize=(10, 4))
    ax = sns.barplot(x="customernumber", y="difference", data=df_finances_o, order=df_finances_o.sort_values('difference',ascending = False).customernumber, color='grey')
    ax.set_title('Amount orders not yet paid x customer')
    ax.set_xlabel("Customernumber")
    ax.set_ylabel("Difference")
    st.pyplot(fig)  
elif add_selectbox == 'Logistics':
    st.title('''Logistics''')
    st.subheader('''The stock of the 5 most ordered products:''')
    fig, ax1 = plt.subplots(figsize=(10, 4))
    ax1.bar(df_logistics["productname"], df_logistics["quantityinstock"], color='grey')
    ax1.set_title('# stock x product')
    ax1.set_ylabel('Qty in stock (nº)')
    ax1.set_xlabel('Product')
    fig.autofmt_xdate()
    ax2 = ax1.twinx()
    ax2.set_ylabel('# orders')
    ax2.plot(df_logistics["productname"], df_logistics["sumOrdered"], color = 'blue')
    ax2.set_yticks(range(0, 1600, 500))
    st.pyplot(fig)
    st.set_option('deprecation.showPyplotGlobalUse', False)
    st.dataframe(df_logistics)
else:
    st.title('''HR''')
    st.subheader('''Each month, the 2 sellers with the highest turnover:''')
    st.info('Information related to the year 2021', icon="ℹ️")
    df_hr = pd.read_sql(query_hr, con=connection)
    df_hr = df_hr[df_hr['YearOrd'] == 2021]
    df_hrv2 = df_hr.loc[:, ["month_", "firstname", "lastname", "sell_rank", "highest_turnover","DateOrd"]]
    df_hrv3 = df_hrv2.sort_values(by=["month_", "sell_rank"], ascending=True)
    
    fig, axes = plt.subplots(figsize=(10,4))
    colors=['grey', 'black']
    sns.barplot(data=df_hrv3, x="DateOrd", y="highest_turnover", hue="sell_rank", ci=None, palette=colors).set(title='Top 2 sellers with the highest   turnover')
    axes.set_xlabel("Month")
    axes.set_ylabel("Turnover")
    axes.legend(title="Sell Rank: ")
    st.pyplot(fig)
    df_hr = pd.read_sql(query_hr, con=connection)
    df_hr = df_hr[df_hr['YearOrd'] == 2021]
    df_hrv2 = df_hr.loc[:, ["month_", "firstname", "lastname", "sell_rank", "highest_turnover","DateOrd"]]
    df_hrv3 = df_hrv2.sort_values(by=["month_", "sell_rank"], ascending=True)
    st.dataframe (df_hrv3)
