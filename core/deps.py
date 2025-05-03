import requests
import os

from jose import jwt, JWTError
from datetime import datetime
from fastapi import HTTPException, Header
from typing import Optional
from core.config import supabase

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
JWT_SECRET = os.getenv("JWT_SECRET")
ALGORITHM = "HS256"

def refresh_access_token(refresh_token: str) -> Optional[str]:
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token'
    }
    response = requests.post("https://oauth2.googleapis.com/token", data=data)
    if response.status_code == 200:
        new_token = response.json().get("access_token")
        return new_token
    return None

def get_valid_access_token(email: str) -> str:
    res = supabase.table("google_tokens").select("*").eq("email", email).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Token untuk email ini tidak ditemukan.")

    token_data = res.data[0]
    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")

    test = requests.get("https://www.googleapis.com/oauth2/v2/userinfo", headers={
        "Authorization": f"Bearer {access_token}"
    })

    if test.status_code == 401 and refresh_token:
        new_token = refresh_access_token(refresh_token)
        if new_token:
            supabase.table("google_tokens").update({
                "access_token": new_token,
                "updated_at": datetime.now().isoformat()
            }).eq("email", email).execute()
            return new_token
        else:
            raise HTTPException(status_code=401, detail="Token kedaluwarsa dan gagal diperbarui.")
    elif test.status_code != 200:
        raise HTTPException(status_code=401, detail="Access token tidak valid.")
    
    return access_token

def verify_token(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization Header")

    token = authorization.split(" ")[1]

    try:
        payload = jwt.decode(
            token=token, 
            key=JWT_SECRET, 
            algorithms=[ALGORITHM],
            audience="authenticated",
        )
        return payload  
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")