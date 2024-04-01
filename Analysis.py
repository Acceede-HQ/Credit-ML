import pandas as pd
import numpy as np
import math
import datetime
def type_converter(obj):
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, datetime.datetime):
        return obj.__str__()

def date_engineering(data):
    data['date'] = pd.to_datetime(data['date'])
    data['year'] = data['date'].dt.year
    data['month'] = data['date'].dt.month_name()

def cashflow_analysis(data):
    opening_date = str(data.tail(1)['date']).split(' ')[3]
    closing_date = str(data.head(1)['date']).split(' ')[3]
    opening_balance = round(float(data.head(1)['balance']),2)
    closing_balance = round(float(data.tail(1)['balance']),2)
    year_in_statement = list(pd.to_datetime(data['date']).dt.year.unique())
    #year_in_statement = [int(i) for i in year_in_statement]
    average_credits = round(float(data[data.type == 'credit']['amount'].mean()),2)
    account_activity = round(float(1 - (data[(data.category == 'atm_withdrawal_charges') | (data.category =='card_request_commission')| 
         (data.category =='bank_charges')| (data.category =='miscellaneous')]['amount'].count()/len(data))),2)
    average_balance = round(float(data['balance'].mean()),2)
    total_credit_turnover = round(float(data[data.type == 'credit']['amount'].sum()),2)
    total_debit_turnover = round(float(data[data.type == 'debit']['amount'].sum()),2)
    average_debits = round(float(data[data.type == 'debit']['amount'].mean()),2)
    max_monthly_repayment = None
    
    cash_flow = {
            'opening_date': opening_date,
            'closing_date': closing_date,
            'opening_balance': opening_balance,
            'closing_balance': closing_balance,
            'year_in_statement': year_in_statement,
            'average_credits':average_credits,
            'average_debits':average_debits,
            'account_activity': account_activity,
            'average_balance':average_balance,
            'total_credit_turnover':total_credit_turnover,
            'total_debit_turnover':total_debit_turnover,
            'max_monthly_repayment':max_monthly_repayment
            }
    return cash_flow

def income_analysis(data):
    salary_earner = False
    income = None
    if 'salary' in list(data.category):
      salary_earner = True
      last_salary_date = str(pd.to_datetime(data[data.category == 'salary'].tail(1)['date']).dt.date.to_string().split(' ')[-1])
      average_of_other_income = round(float(data[(data.type == 'credit') & (data.category != 'salary')]['amount'].mean()),2)
      max_month = pd.to_datetime(data.head(1).date).dt.date.to_string().split(' ')[-1]
      min_month = pd.to_datetime(data.tail(1).date).dt.date.to_string().split(' ')[-1]
      salary_frequency = int(math.ceil(len(data[data.category == 'salary'])/len(pd.period_range(min_month, max_month, freq='M'))))
      
      number_of_salary_payments = int(len(data[data.category == 'salary']))
      number_of_other_income_payments = int(len(data[(data.type == 'credit') & (data.category != 'salary')]))
      average_salary = round(float(data[data.category == 'salary']['amount'].mean()),2)
      expected_salary_day = str(data[data.category == 'salary']['date'].mode()[0]).split(' ')[0]
      median_income = round(float(data[data.type == 'credit']['amount'].median()),2)
      gig_worker = None
      if salary_frequency > 2:
        gig_worker = True
      else:
        gig_worker = False
      income = {
            'last_salary_date':last_salary_date,
            'average_of_other_income':average_of_other_income,
            'salary_frequency':salary_frequency,
            'number_of_salary_payments':number_of_salary_payments,
            'number_of_other_income_payments':number_of_other_income_payments,
            'average_salary':average_salary,
            'expected_salary_day':expected_salary_day,
            'salary_earner':salary_earner,
            'median_income':median_income,
            'gig_worker':gig_worker
            }
    
    return income

def spend_analysis(data):
    #recurring_expenses = list(pd.DataFrame(data.groupby('category')['category'].count().sort_values(ascending=False)).head(1).to_dict()['category'].keys())[0]
    #recurring_expenses_frequency = list(pd.DataFrame(data.groupby('category')['category'].count().sort_values(ascending=False)).head(1).to_dict()['category'].values())[0]
    #average_recurring_expense = float(data[data.category == recurring_expenses]['amount'].mean())
    atm_spend = round(float(data[data.category == 'atm_withdrawal']['amount'].sum()),2)
    web_spend = round(float(data[data.category == 'online_transactions']['amount'].sum()),2)
    pos_spend = round(float(data[data.category == 'offline_transactions']['amount'].sum()),2)
    mobile_spend = round(float(data[data.category == 'phone_and_internet']['amount'].sum()),2)
    spend_on_transfer = round(float(data[(data.category == 'transfer') &(data.type == 'debit' )]['amount'].sum()),2)
    
    bills = round(float(data[data.category == 'bills_fees']['amount'].sum()),2)
    entertainment = round(float(data[(data.category == 'events') | (data.category == 'gadget') | (data.category == 'food')]['amount'].sum()),2)
    savings_investments = round(float(data[data.category == 'investment']['amount'].sum()),2)
    bank_charges = round(float(data[(data.category == 'bank_charges') | (data.category =="atm_withdrawal_charges")]['amount'].sum()),2)
    miscellaneous = round(float(data[(data.category == 'miscellaneous')|(data.category == 'others')]['amount'].sum()),2)
    
    spend = {
            #'average_recurring_expense':average_recurring_expense,
            #'recurring_expenses_frequency': recurring_expenses_frequency,
            #'recurring_expenses': recurring_expenses,
            'atm_spend':atm_spend,
            'web_spend':web_spend,
            'pos_spend':pos_spend,
            'mobile_spend': mobile_spend,
            'spend_on_transfer': spend_on_transfer,
            'bills':bills,
            'entertainment':entertainment,
            'savings_investments': savings_investments,
            'bank_charges':bank_charges,
            'miscellaneous': miscellaneous
            }
    return spend

def behavioral_analysis(data):
    total_credit_turnover = round(float(data[data.type == 'credit']['amount'].sum()),2)
    total_debit_turnover = round(float(data[data.type == 'debit']['amount'].sum()),2)
    top_incoming_transfer_account = None
    loan_repayments = round(float(data[(data.category == 'mature_loan_installment')|(data.category == 'loan_repayment')]['amount'].sum()),2)
    loan_inflow_rate = None
    account_sweep = None
    loan_repayment_inflow_rate = round(float(loan_repayments/total_credit_turnover),2)
    on_top_recipient_account_found = None
    inflow_outflow_rate = round(float(total_credit_turnover - total_debit_turnover),2)
    loan_amount = None
    behavioral = {
        'top_incoming_transfer_account':top_incoming_transfer_account,
        'loan_repayments':loan_repayments,
        'loan_inflow_rate':loan_inflow_rate,
        'account_sweep':account_sweep,
        'loan_repayment_inflow_rate':loan_repayment_inflow_rate,
        'on_top_recipient_account_found': on_top_recipient_account_found,
        'inflow_outflow_rate':inflow_outflow_rate,
        'loan_amount':loan_amount
        }
    return behavioral

def transaction_pattern_analysis(data):
    nodw_balance_less = None
    most_frequent_balance_range = [float(data['balance'].quantile(0.35)), float(data['balance'].quantile(0.65))]
    mawo_credit = [None]
    mawo_credit.extend(list(pd.DataFrame(data[data.type == 'credit'].groupby('month')['amount'].sum().sort_values(ascending = False)).head(1).to_dict()['amount'].keys()))
    highest_mawo_credit = (mawo_credit[-1])
    transaction_btw_100000_500000 = int(len(data[(data.amount >= 100000) & (data.amount <= 500000)]))
    nodw_balance_less_than_5000 = int(len(data[(data.balance < 5000)].groupby('date')['date'].count()))
    transactions_btw_10000_100000 = int(len(data[(data.amount >= 10000) & (data.amount <= 100000)]))
    transaction_less_than_10000 = int(len(data[(data.amount < 10000)]))
    transaction_ranges = [float(data['amount'].quantile(0.3)), float(data['amount'].quantile(0.7))]
    mawo_debit = [None]
    mawo_debit.extend(list(pd.DataFrame(data[data.type == 'debit'].groupby('month')['amount'].sum().sort_values(ascending = False)).head(1).to_dict()['amount'].keys()))
    highest_mawo_debit = (mawo_debit[-1])
    zero_balance =[None]
    zero_balance.extend(list(pd.DataFrame(data[data.balance == 0].groupby('month')['amount'].sum().sort_values(ascending = False)).head(1).to_dict()['amount'].keys()))
    maww_zero_balance = zero_balance[-1]
    most_frequent_transaction_range = [float(data['amount'].quantile(0.45)), float(data['amount'].quantile(0.55))]
    last_date_of_credit = str(pd.to_datetime(data[data.type == 'credit'].tail(1)['date']).dt.date.to_string().split(' ')[-1])
    last_date_of_debit = str(pd.to_datetime(data[data.type == 'debit'].tail(1)['date']).dt.date.to_string().split(' ')[-1])
    transactions_greater_than_500000 = int(len(data[(data.amount > 500000)]))
    transaction_pattern = {
            'nodw_balance_less':nodw_balance_less,
            'most_frequent_balance_range':most_frequent_balance_range,
            'highest_mawo_credit':highest_mawo_credit,
            'transaction_btw_100000_500000': transaction_btw_100000_500000,
            'nodw_balance_less_than_5000': nodw_balance_less_than_5000,
            'transactions_btw_10000_100000': transactions_btw_10000_100000,
            'transaction_less_than_10000': transaction_less_than_10000,
            'transaction_ranges':transaction_ranges,
            'highest_mawo_debit': highest_mawo_debit,
            'maww_zero_balance':maww_zero_balance,
            'most_frequent_transaction_range': most_frequent_transaction_range,
            'last_date_of_debit': last_date_of_debit,
            'last_date_of_credit': last_date_of_credit,
            'transactions_greater_than_500000':transactions_greater_than_500000
            }
    return transaction_pattern

def combined_analysis(data):
    date_engineering(data)
    resp = {
        'cash_flow': cashflow_analysis(data),
        'income': income_analysis(data),
        'spend': spend_analysis(data),
        'behavioral': dict(behavioral_analysis(data)),
        'transaction_pattern': dict(transaction_pattern_analysis(data))
        }
        
    return resp

def get_income(data):
    recurring_amount_list = []
    credit_rows = data['type'] == 'credit'
    credit_transactions = data[credit_rows]

    for _, rows in credit_transactions.iterrows():
        # group credit transactions by category and amount, then count occurence
        credits_by_cat_amount = credit_transactions.groupby(['category', 'amount']).size().reset_index(name='count')

        # sort categories by count in descending order 
        sorted_cat_amount = credits_by_cat_amount.sort_values(by='count', ascending = False)

        # top 3 category and amount
        top_cat_amount = sorted_cat_amount.head(3)

    recurring_amount_list.append(top_cat_amount)

    return recurring_amount_list



