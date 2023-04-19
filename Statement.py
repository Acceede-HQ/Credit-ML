from pydantic import BaseModel
#import datetime

class FinancialStatement(BaseModel):
    account_id: str
    # user: str
    loan_reference: str
    # account: dict
    # choose_wards: list
    # approved_wards: list
    # total_wards_fee: float
    # total_approved_wards_fee: float
    # amount_to_payback: float
    # interest_on_amount: float
    # length_of_payback: int
    # amount_to_pay_monthly: float
    # fully_paid: bool
    
