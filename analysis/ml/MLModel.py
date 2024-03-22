import pandas as pd
import numpy as np
import os, requests
import pickle

def get_vectorizer_model():
    filepath = os.path.join('models','vectorizer.sav')
    pickle_in = open(filepath,"rb")
    vectorizer_model =pickle.load(pickle_in)
    print(vectorizer_model)
    return vectorizer_model

def get_ml_model():
    modelpath = os.path.join('models','k_means_model.sav')
    pickle_in = open(modelpath,"rb")
    k_means_model =pickle.load(pickle_in)
    return k_means_model
    

def remove_one_two(x):
  x = x.split(' ')
  for i in range(0,len(x)):
    if len(x[i]) == 1 or len(x[i]) == 2:
      x[i] = ''
  x = ' '.join(x)
  return x

def preprocess(data):
  data = pd.DataFrame(data)
  data = data.replace(np.nan, 0)
  data['balance'] = data['balance']/100
  data['amount'] = data['amount']/100
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