from pydantic import BaseModel

class FinancialStatementRequestVM(BaseModel):
    account_id: str
    loan_reference: str