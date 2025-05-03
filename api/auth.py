from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from datetime import datetime, timedelta

import requests
import os
import dotenv

from core.config import supabase
from jose import jwt

dotenv.load_dotenv()

router = APIRouter()

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
JWT_SECRET = os.getenv("JWT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
SCOPE = os.getenv("SCOPE")

@router.get("/")
def index():
    auth_url = (
        'https://accounts.google.com/o/oauth2/v2/auth'
        f'?client_id={CLIENT_ID}'
        f'&redirect_uri={REDIRECT_URI}'
        f'&response_type=code'
        f'&scope={SCOPE}'
        f'&access_type=offline'
        f'&prompt=consent'
    )
    return RedirectResponse(auth_url)

@router.get("/oauth2callback")
def oauth2callback(code: str):
    token_url = 'https://oauth2.googleapis.com/token'
    data = {
        'code': code,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'redirect_uri': REDIRECT_URI,
        'grant_type': 'authorization_code',
    }

    response = requests.post(token_url, data=data)
    response.raise_for_status()
    tokens = response.json()

    access_token = tokens.get('access_token')
    refresh_token = tokens.get('refresh_token')

    userinfo = requests.get("https://www.googleapis.com/oauth2/v2/userinfo", headers={
        "Authorization": f"Bearer {access_token}"
    }).json()

    email = userinfo.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Gagal mendapatkan email pengguna.")

    supabase.table("users").upsert({
        "email": email,
        "google_id": userinfo.get("id"),
        "name": userinfo.get("name")
    }).execute()

    supabase.table("google_tokens").upsert({
        "email": email,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "updated_at": datetime.now().isoformat()
    }).execute()

    jwt_token = jwt.encode({
        "sub": email,
        "email": email,
        "aud": "authenticated",
        "exp": datetime.now() + timedelta(hours=1),
        "iat": datetime.now()
    }, JWT_SECRET, algorithm="HS256")

    return JSONResponse(content={
        "message": "Login berhasil!",
        "jwt_token": jwt_token,
        "email": email,
        "access_token": access_token,
        "refresh_token": refresh_token
    })