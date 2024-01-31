import requests
import os
import jwt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, HTTPException
from dotenv import load_dotenv

load_dotenv()
algorithm = 'HS256'
security = HTTPBearer()


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        secret_key = os.environ.get('SECRET')

        payload = jwt.decode(token, secret_key, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def request_api_for_user_data(email):
    url = f'http://localhost:8000/auth/get-user-data{email}'
    payload = {
        "email": email
    }
    response = requests.get(url, json=payload)
    response_data = response.json()
    return response_data
