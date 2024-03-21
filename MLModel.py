import pandas as pd
import numpy as np
import requests
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import re
from datetime import datetime, timedelta

def get_transaction_date_range():
    current_date = datetime.now()
    end_date = current_date.strftime("%d-%m-%Y")
    start_date = (current_date - timedelta(days=365)).strftime("%d-%m-%Y")
    return start_date, end_date

def get_transactions(account_id):
    (start_date, end_date) = get_transaction_date_range()
    url = f"https://api.withmono.com/accounts/{account_id}/transactions?paginate=false&start_date&end_date"
    headers = {"accept": "application/json",
          "mono-sec-key": "live_sk_CA7jLNrlfqEDOy30yLZi"}
    response = requests.get(url, headers=headers)
    response = response.json()
    print(response)
    resp = pd.DataFrame(response['data'])
    resp = resp.replace(np.nan, 0)
    resp['balance'] = resp['balance']/100
    resp['amount'] = resp['amount']/100
    return resp

def get_vectorizer_model():
    pickle_in = open("vectorizer.sav","rb")
    vectorizer_model =pickle.load(pickle_in)
    print(vectorizer_model)
    return vectorizer_model

def get_ml_model():
    pickle_in = open("k_means_model.sav","rb")
    k_means_model =pickle.load(pickle_in)
    return k_means_model
    

def remove_one_two(x):
  x = x.split(' ')
  for i in range(0,len(x)):
    if len(x[i]) == 1 or len(x[i]) == 2:
      x[i] = ''
  x = ' '.join(x)
  return x

def preprocess(df):
  data = df.copy()
  data['text'] = data['narration'].copy()
  stop = ["to"]
  data["text"] = data["text"].str.lower()
  data['text'] = data['text'].apply(lambda x: " ".join(x for x in x.split() if x not in stop))
  
  for i in ['-','\d+','[\b\d+(?:|!@/\.\d+)?\s+]+','bank','ref','gtworld','lang','trf']:
    data['text'] = data['text'].str.replace(i,' ')
    
  data["text"]= data["text"].apply(remove_one_two)
  data["text"]= data["text"].astype(str)
  data["text"]= data["text"].str.replace(r'\s+', ' ', regex=True)
  #data['text'] = data['text'].str.slice(start=6)
  documents = data['text'].values.astype('U')
  vectorizer = get_vectorizer_model()
  print(documents)
  features = vectorizer.transform(documents)
  return features, data

def modelling(features,data):
  model = get_ml_model()
  pred = model.predict(features)
  data['cluster'] = pred
  return data, model