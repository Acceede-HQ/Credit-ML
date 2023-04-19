
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, status
from Statement import FinancialStatement
from MLModel import preprocess,modelling,get_transactions
from fastapi.security import OAuth2PasswordBearer
import Cluster
import Analysis
#import pickle
import requests
import json
api_keys = [
   "MLS-PASS","asd"
]  # This is encrypted in the database
BASE_URL = "https://staging-s55s.onrender.com"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")  # use token authentication


def api_key_auth(api_key: str = Depends(oauth2_scheme)):
    if api_key not in api_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Forbidden"
        )

app = FastAPI()
#import nest_asyncio
#nest_asyncio.apply()



@app.post('/',dependencies=[Depends(api_key_auth)])
def display_analysis(input_data:FinancialStatement):
    account_id=input_data.account_id
    #user_id = input_data.user_id
    loan_reference = input_data.loan_reference
    print(loan_reference)
    print(account_id)
    try:
        df = get_transactions(account_id)
        features,data = preprocess(df)
        data,model  = modelling(features,data)
        data['category'] = data['cluster'].map(Cluster.clusters())
        ml_resp = Analysis.combined_analysis(data)
        
        
        
        
        final_resp = {
            
          # "user": user_id,
          # "account_id": account_id,
          "account": input_data.account_id,
          # "choose_wards": input_data.choose_wards,
          # "approved_wards": input_data.approved_wards,
          # "total_wards_fee": input_data.total_wards_fee,
          # "total_approved_wards_fee": input_data.total_approved_wards_fee,
          "mls": ml_resp,
          # "amount_to_payback": input_data.amount_to_payback,
          # "interest_on_amount": input_data.interest_on_amount,
          # "length_of_payback": input_data.length_of_payback,
          # "amount_to_pay_monthly": input_data.amount_to_pay_monthly,
          # "fully_paid": input_data.fully_paid
    
            }
        headers = {'content-type': 'application/json',
                   "mls-access-token": "MLS_ACCESS_TOKEN"
                   }
        url = BASE_URL + '/loans/mls/'+ loan_reference
        print(final_resp)
        res = json.dumps(final_resp, default=Analysis.type_converter,
                         allow_nan = True)
        res = json.loads(res)
        #print("hey")
        response = requests.put(url, 
                                data = json.dumps(final_resp, default=Analysis.type_converter,
                                                 allow_nan = True),
                                headers = headers
                                )
        print("response is ", response.status_code)
        #print("Pass")
        #print("the response content is: ", response.text)
    
        return res
    except:
        raise HTTPException(status_code = 404, detail=  "Something went wrong!")

#    Will run on http://127.0.0.1:8000
if __name__ == '__main__':
    uvicorn.run(app)
    
