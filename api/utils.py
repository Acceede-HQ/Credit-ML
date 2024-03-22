from datetime import datetime, timedelta
from fastapi import status, Response
from fastapi.responses import JSONResponse


def api_response(message=None, data = None, status_code = None):
    has_error = False
    if data:
        status_code = status.HTTP_200_OK
        message = message or "Successful"
    else:
        status_code = status_code or status.HTTP_400_BAD_REQUEST
        has_error = True
        message = message or "An error occurred"
    
    response_data = {"message": message, "data": data, "has_error": has_error}
    return JSONResponse(content=response_data, status_code=status_code)


def get_transaction_date_range():
    current_date = datetime.now()
    end_date = current_date.strftime("%d-%m-%Y")
    start_date = (current_date - timedelta(days=365)).strftime("%d-%m-%Y")
    return start_date, end_date
