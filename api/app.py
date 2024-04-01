import uvicorn
import requests, json
from os import environ as env
from dotenv import load_dotenv
from .constants import *

import pandas as pd
import numpy as np

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from .utils import get_transaction_date_range
from .schemas import FinancialStatementRequestVM

from analysis.ml.MLModel import preprocess, modelling
import analysis.ml.Cluster as Cluster
import analysis.Analysis as Analysis

load_dotenv()
app = FastAPI()

BASE_URL = "https://staging-s55s.onrender.com"
BASE_URL2 = "https://acceedeapi.herokuapp.com"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def api_key_auth(api_key: str = Depends(oauth2_scheme)):
    api_keys = env.get("AUTH_TOKENS").split(",")
    if api_key not in api_keys:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Forbidden")

@app.post('/',dependencies=[Depends(api_key_auth)])
def display_analysis(input_data:FinancialStatementRequestVM):
    account_id=input_data.account_id
    loan_reference = input_data.loan_reference
    if account_id.strip() == "" or loan_reference.strip() == "":
        raise HTTPException(status_code = 400, detail=  "missing parameter")
    else:
        try:
            df = get_transactions(account_id)
            features,data = preprocess(df)
            data, _  = modelling(features,data)
            data['category'] = data['cluster'].map(Cluster.clusters())
            ml_resp = Analysis.combined_analysis(data)
            
            final_resp = {"account": input_data.account_id, "mls": ml_resp}
            headers = {'content-type': 'application/json', "mls-access-token": env.get(ACCEEDE_ACCESS_TOKEN) }

            url1 = BASE_URL + '/loans/mls/'+ loan_reference
            url2 = BASE_URL2 + '/loans/mls/'+ loan_reference

            res = json.dumps(final_resp, default=Analysis.type_converter,allow_nan = True)
            res = json.loads(res)

            response = requests.put(url1, headers = headers,
                                    data = json.dumps(final_resp, default=Analysis.type_converter, allow_nan = True))
            response1 = requests.put(url2, headers = headers,
                                     data = json.dumps(final_resp, default=Analysis.type_converter, allow_nan = True))        
            return res
        except:
            raise HTTPException(status_code = 404, detail=  "Something went wrong!")


def get_transactions(account_id):
    start_date, end_date = get_transaction_date_range()
    url = f"{MONO_BASE_URL}/{account_id}/transactions?paginate=false&{start_date}&{end_date}"
    headers = {"accept": "application/json", "mono-sec-key": env.get(MONO_SECRET_KEY)}
    response = requests.get(url, headers=headers)
    response = response.json()
    resp = pd.DataFrame(response['data'])
    resp = resp.replace(np.nan, 0)
    resp['balance'] = resp['balance']/100
    resp['amount'] = resp['amount']/100
    return resp

if __name__ == '__main__':
    uvicorn.run(app)