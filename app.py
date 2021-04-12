
import pandas as pd
import joblib
from flask import Flask, render_template, request


app = Flask(__name__)


prod_ranking_model = joblib.load("prod_ranking_model.pkl")
cust_prod_ranking_model = joblib.load("cust_prod_ranking_model.pkl")
cust_correlation_model = joblib.load("cust_correlation_model.pkl")
prod_correlation_model = joblib.load("prod_correlation_model.pkl")

@app.route("/")
def home():

    return render_template('index.html')

@app.route("/predict", methods=['POST','GET'])
def predict():
 #if (request.method == 'POST'):
    #cust_name = str(request.form['name']).upper()
    cust_name = str(request.args.get('name')).upper()

    if cust_name in cust_prod_ranking_model['reviews_username'].unique():
        similar_custs_corr = cust_correlation_model.loc[cust_name].sort_values(ascending=False)
        prod_by_similar_custs = pd.DataFrame()

        for i in range(len(similar_custs_corr)):
            if similar_custs_corr.index[i] != cust_name:
                cust_top_sell_prods = cust_prod_ranking_model[cust_prod_ranking_model['reviews_username'] == similar_custs_corr.index[i]]
                cust_top_sell_prods = cust_top_sell_prods[['id', 'Top_Sell_Rank', 'Popularity_Rank']].reset_index(drop=True)
                cust_top_sell_prods['Qty_Corr'] = cust_top_sell_prods['Top_Sell_Rank'] * similar_custs_corr.iloc[i]
                prod_by_similar_custs = pd.concat([cust_top_sell_prods, prod_by_similar_custs])

        prod_by_similar_custs = prod_by_similar_custs.groupby('id').agg({'Qty_Corr': 'sum', 'Popularity_Rank': 'max'})
        prod_by_similar_custs.reset_index(inplace=True)
            # print(prod_by_similar_custs.head(20))

        input_cust_top_sell_prods = cust_prod_ranking_model[
        cust_prod_ranking_model['reviews_username'] == cust_name]
        df_merge = pd.merge(prod_by_similar_custs, input_cust_top_sell_prods[['id', 'No_of_Orders']], how='left',on='id')
        prod_recommend_to_cust = df_merge[df_merge['No_of_Orders'].isnull()]
            # sort the dataframe on Qty_Corr
        prod_recommend_to_cust = prod_recommend_to_cust.sort_values('Qty_Corr', ascending=False)[['id', 'Popularity_Rank']].head(10).reset_index(drop=True)
            #prod_recommend_to_cust1.to_html(header="true", table_id="table")
    #return render_template('simple.html', tables=[prod_recommend_to_cust.to_html(classes='data')], titles=prod_recommend_to_cust.columns.values)
        #return render_template('index.html', prediction_text='Recommended Output {}'.prod_recommend_to_cust)
        return render_template('index.html', tables=[prod_recommend_to_cust.to_html(classes='data', header="true")])
    else:
        return render_template('index.html')



if __name__ == "__main__":
    app.run(debug=True)


