from datetime import datetime, timedelta

def get_transaction_date_range():
    current_date = datetime.now()
    end_date = current_date.strftime("%d-%m-%Y")
    start_date = (current_date - timedelta(days=365)).strftime("%d-%m-%Y")
    return start_date, end_date
