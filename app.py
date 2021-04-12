#!/usr/bin/env python
# coding: utf-8

# In[15]:


import pandas as pd
import os
from os  import getcwd
import pickle
from flask import Flask, render_template, request


app = Flask(__name__)

directory = getcwd()


prod_ranking_model = pickle.load(open(os.path.join(directory,'prod_ranking_model.pkl'),'rb'))
cust_prod_ranking_model = pickle.load(open(os.path.join(directory,'cust_prod_ranking_model.pkl'),'rb'))
cust_correlation_model = pickle.load(open(os.path.join(directory,'cust_correlation_model.pkl'),'rb'))
prod_correlation_model = pickle.load(open(os.path.join(directory,'prod_correlation_model.pkl'),'rb'))


# # HTML code for displaying Table

# In[7]:


# This function structures the HTML code for displaying the table on website
def html_code_table(prod_df,table_name,file_name,side):
    table_style = '<table style="border: 2px solid; float: ' + side + '; width: 40%;">'
    table_head = '<caption style="text-align: center; caption-side: top; font-size: 140%; font-weight: bold; color:black;"><strong>' + table_name + '</strong></caption>'
    table_head_row = '<tr><th>Product Name</th><th>Price (in Rs.)</th></tr>'
    
    html_code = table_style + table_head + table_head_row
    
    for i in range(len(prod_df.index)):
        row = '<tr><td>' + str(prod_df['id'][i]) + '</td><td>' + str(prod_df['Rating'][i]) + '</td></tr>'
        html_code = html_code + row
        
    html_code = html_code + '</table>'
    
    file_path = os.path.join(directory,'templates/')
    
    hs = open(file_path + file_name + '.html', 'w')
    hs.write(html_code)


def recommend_prod_cust(cust_name):
    similar_custs_corr = cust_correlation_model.loc[cust_name].sort_values(ascending=False)
    
    prod_by_similar_custs = pd.DataFrame()
    
    # get the products purchased by each customer and multiply with the customer correlation coefficient
    for i in range(len(similar_custs_corr)):
        if similar_custs_corr.index[i] != cust_name:
            cust_top_sell_prods = cust_prod_ranking_model[cust_prod_ranking_model['reviews_username'] == similar_custs_corr.index[i]]
            cust_top_sell_prods = cust_top_sell_prods[['id','Rating']].reset_index(drop=True)
            cust_top_sell_prods['Qty_Corr'] = cust_top_sell_prods['Qty'] * similar_custs_corr.iloc[i]
            prod_by_similar_custs = pd.concat([cust_top_sell_prods,prod_by_similar_custs])
    
    # aggregate the Qty Correlation by Product
    prod_by_similar_custs = prod_by_similar_custs.groupby('id').agg({'Qty_Corr':'sum','Rating':'max'})
    prod_by_similar_custs.reset_index(inplace=True)
    print(prod_by_similar_custs.head(20))
    
    # ignore the products already purchased by the input customer
    # merge prod_by_similar_custs and customer purchased products and drop the rows with No_of_orders being Not Null
    input_cust_top_sell_prods = cust_prod_ranking_model[cust_prod_ranking_model['reviews_username'] == cust_name]
    df_merge = pd.merge(prod_by_similar_custs,input_cust_top_sell_prods[['id','No_of_Users']],how='left',on='id')
    prod_recommend_to_cust = df_merge[df_merge['No_of_Users'].isnull()]
    
    # sort the dataframe on Qty_Corr
    prod_recommend_to_cust = prod_recommend_to_cust.sort_values('Qty_Corr',ascending=False)[['Product','Rate']].head(10).reset_index(drop=True)
    
   # print(prod_recommend_to_cust)
    
    html_code_table(prod_recommend_to_cust,'Products you may like','prodrecommendtable','center')


def similar_prods(prod_name):
    similar_prods_corr = prod_correlation_model.loc[prod_name].sort_values(ascending=False)
    
    similar_prods = pd.merge(similar_prods_corr,prod_ranking_model[['id','Rating']],how='left',on='id')
    
    prod_price = similar_prods[similar_prods['id'] == prod_name]['Rating'].values[0]
    
    input_prod_index = similar_prods[similar_prods['id'] == prod_name].index
    similar_prods.drop(index=input_prod_index,inplace=True)
    
    similar_prods = similar_prods[['id','Rating']].head(10).reset_index(drop=True)


     #print(similar_prods)
    
    html_code_table(similar_prods,'Customers who purchased this product also purchased these','similarprodtable','left')
    
    return prod_price


@app.route("/")
def home():

    return render_template('index.html')

@app.route("/predict", methods=['POST','GET'])
def predict():
    cust_name = str(request.args.get('name')).upper()
    if cust_name in cust_prod_ranking_model['reviews_username'].unique():
        output = recommend_prod_cust(cust_name)
        return render_template('index.html', prediction_text='Churn Output {}'.format(output))
    else:
        return render_template('index.html')


if __name__ == "__main__":
    app.run(debug=True)


