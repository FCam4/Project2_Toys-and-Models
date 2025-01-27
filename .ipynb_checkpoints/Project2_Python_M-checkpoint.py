# import libraries

import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
import numpy as np
#import datetime
import mysql.connector 
import seaborn as sns

st.title("Project: Toys and Models")

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
order by turnover''' 

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


query_logistics= '''select p.productname, sum(od.quantityordered) as sumOrdered, p.quantityinstock from products p join orderdetails od on p.productcode=od.productCode
group by p.productname
order by sumOrdered desc
limit 5'''

df_logistics=pd.read_sql(query_logistics, con=connection)

query_hr= '''WITH top_sellers AS (select e.employeeNumber, e.firstname, jobTitle, e.lastname, DATE_FORMAT(o.orderdate, "%c %Y") as DateOrd, year(o.orderdate) as YearOrd, sum(od.quantityordered*od.priceeach) as highest_turnover,
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
#df_hr.head(53)
df_hr = df_hr[df_hr['YearOrd'] == 2021]
#print(df_hr)





add_selectbox = st.sidebar.radio(
    "Topics",
    ("Sales", "Finance_turnover","Finance_orders", "Logistics", "HR"))

if add_selectbox=='Sales':
    st.markdown ('''The number of products sold by category and by month, with comparison and rate of change compared to the same month of the previous year:''')
    st.dataframe(df_sales)
elif add_selectbox == 'Finance_turnover':
    st.markdown('''The turnover of the orders of the last two months by country:''')
    st.dataframe(df_finances_to)
elif add_selectbox == 'Finance_orders':
    st.markdown('''Orders that have not yet been paid:''')
    st.dataframe(df_finances_o)
    fig, ax = plt.subplots(figsize=(10, 4))
    ax = sns.barplot(x="customernumber", y="difference", data=df_finances_o, order=df_finances_o.sort_values('difference',ascending = False).customernumber, color='blue')
    ax.set_title('$ orders not yet paid x customer')
    ax.set_xlabel("customernumber")
    ax.set_ylabel("difference")
    st.pyplot(fig)   
elif add_selectbox == 'Logistics':
    st.markdown('''The stock of the 5 most ordered products:''')
    st.dataframe(df_logistics)
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.bar(df_logistics["productname"], df_logistics["quantityinstock"], color='blue')
    ax.set_title('Qty in stock x product')
    ax.set_ylabel('Qty in stock (nº)')
    ax.set_xlabel('Product')
    fig.autofmt_xdate()
    st.pyplot(fig)
    st.set_option('deprecation.showPyplotGlobalUse', False)
else: 
    st.markdown('''Each month, the 2 sellers with the highest turnover:''')
    st.dataframe(df_hr)
    
#fig,axes=np.random.normal(figsize=(12,8))
#sales= sns.barplot(data=df_sales, x="order_month", y="order_quantity", hue="order_year", ci=None).set(title='# products by month')
#axes.set_xlabel("Month")
#axes.set_ylabel("# orders")
#axes.legend(title="Year:")