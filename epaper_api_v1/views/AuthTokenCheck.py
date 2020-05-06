import datetime

from ..models import Token
from ..consts import LOGIN_TIME

def check_token(token):
    if token is None:
        return {
            "status": False,
            "details": "token is None"
        }

    token_obj = Token.objects.filter(token=token)
    if token_obj.count() == 0:
        return {
            "status": False,
            "details": "No token in database"
        }

    if datetime.datetime.now().timestamp() > (token_obj[0].access_datetime.timestamp() + LOGIN_TIME):
        return {
            "status":False,
            "details": "time over"
        }
    
    return {
        "status": True,
        "user": token_obj[0].user,
        "details": ""
    }