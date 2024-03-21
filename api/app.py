import uvicorn
import requests
import json

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from .schemas import FinancialStatementRequestVM

from analysis.ml.MLModel import preprocess,modelling,get_transactions
import analysis.ml.Cluster as Cluster
import analysis.Analysis as Analysis

app = FastAPI()

api_keys = [
   "MLS-PASS","asd"
]

BASE_URL = "https://staging-s55s.onrender.com"
BASE_URL2 = "https://acceedeapi.herokuapp.com"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def api_key_auth(api_key: str = Depends(oauth2_scheme)):
    if api_key not in api_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Forbidden"
        )

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
            headers = {'content-type': 'application/json', "mls-access-token": "MLS_ACCESS_TOKEN" }
            url1 = BASE_URL + '/loans/mls/'+ loan_reference
            url2 = BASE_URL2 + '/loans/mls/'+ loan_reference

            res = json.dumps(final_resp, default=Analysis.type_converter,
                             allow_nan = True)
            res = json.loads(res)

            response = requests.put(url1, 
                                    data = json.dumps(final_resp, default=Analysis.type_converter, allow_nan = True),
                                    headers = headers )
            response1 = requests.put(url2, 
                                     data = json.dumps(final_resp, default=Analysis.type_converter, allow_nan = True),
                                     headers = headers )        
            return res
        except:
            raise HTTPException(status_code = 404, detail=  "Something went wrong!")

if __name__ == '__main__':
    uvicorn.run(app)