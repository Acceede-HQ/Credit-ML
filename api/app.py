import uvicorn
import requests, json
from os import environ as env
from dotenv import load_dotenv
from .constants import *
import logging

from fastapi import FastAPI, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordBearer

from .utils import *
from .schemas import FinancialStatementRequestVM

from analysis.ml.MLModel import preprocess, modelling
import analysis.ml.Cluster as Cluster
import analysis.Analysis as Analysis

load_dotenv()

logger = logging.getLogger(__name__)
app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def api_key_auth(api_key: str = Depends(oauth2_scheme)):
    api_keys = env.get(AUTH_TOKENS).split(",")
    if api_key not in api_keys:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Forbidden")
    
@app.post('/token')
async def get_token():
    return {"access_token": env.get(AUTH_TOKENS).split(",")[0]}

@app.post('/',dependencies=[Depends(api_key_auth)])
def display_analysis(input_data:FinancialStatementRequestVM):
    try:
        account_id=input_data.account_id
        loan_reference = input_data.loan_reference

        if account_id.strip() == "" or loan_reference.strip() == "":
            return api_response(message="Invalid account_id or loan_reference 😕")
        
        transactions = get_transactions(account_id)
        if not transactions:
            return api_response(message="No transactions found for this account 😕")

        analysis_result = analyze(transactions)

        final_resp = {"account": account_id, "mls": analysis_result}
        headers = {'content-type': 'application/json', "mls-access-token": env.get(ACCEEDE_ACCESS_TOKEN) }

        response_json = json.dumps(final_resp, default=Analysis.type_converter,allow_nan = True)
        response = json.loads(response_json)

        acceede_route = '/loans/mls/'+ loan_reference
        result_1 = requests.put(BASE_URL+acceede_route, headers = headers, data = response_json)
        result_2 = requests.put(BASE_URL2+acceede_route, headers = headers, data = response_json)    

        return api_response(data=response)
    except Exception:
        logger.error("Error Alert!!! 🫥", exc_info=True)
        return api_response(message="Something went wrong! 😕")

def analyze(transactions):
    features,data = preprocess(transactions)
    data, _  = modelling(features,data)
    data['category'] = data['cluster'].map(Cluster.clusters())
    ml_resp = Analysis.combined_analysis(data)
    return ml_resp

def get_transactions(account_id: str):
    start_date, end_date = get_transaction_date_range()
    url = f"{MONO_BASE_URL}/{account_id}/transactions?paginate=false&{start_date}&{end_date}"
    headers = {"accept": "application/json", "mono-sec-key": env.get(MONO_SECRET_KEY)}
    response = requests.get(url, headers=headers)
    response = response.json()['data']
    return response

if __name__ == '__main__':
    uvicorn.run(app)