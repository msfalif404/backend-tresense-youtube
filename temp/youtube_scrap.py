from fastapi import FastAPI, Request, Query, APIRouter, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from typing import List
import requests
import pandas as pd
import os
import dotenv

dotenv.load_dotenv()

app = FastAPI()

CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')
REDIRECT_URI = 'http://localhost:8000/oauth2callback'
SCOPE = 'https://www.googleapis.com/auth/youtube.force-ssl'

user_tokens = {}

@app.get("/")
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

@app.get("/oauth2callback")
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
    tokens = response.json()
    access_token = tokens.get('access_token')
    refresh_token = tokens.get('refresh_token')

    user_tokens['access_token'] = access_token
    user_tokens['refresh_token'] = refresh_token

    return HTMLResponse(content="Login berhasil! Kunjungi endpoint `/scrape_comments?video_ids=ID1&video_ids=ID2...`")

@app.get("/scrape_comments")
def scrape_comments(video_ids: List[str] = Query(..., max_length=10)):
    # access_token = user_tokens.get('access_token')

    access_token = "6apewNWzvD2VugE64O/Qr+8vz1Ya5ma03gtOXNc80Araf8LVl+DQGDTf5yOigK6TzzAJ6PKGD47XSNzK0h1NcQ=="
    if not access_token:
        return {"error": "Belum login, silakan autentikasi dulu."}

    all_results = []

    for video_id in video_ids:
        comments = get_comments(video_id, access_token)
        if not comments:
            continue

        for item in comments:
            comment = item['snippet']['topLevelComment']['snippet']
            all_results.append({
                "video_id": video_id,
                "author": comment['authorDisplayName'],
                "comment": comment['textDisplay'],
                "published_at": comment['publishedAt']
            })

    if not all_results:
        return {"message": "Tidak ada komentar ditemukan dari video manapun."}

    df = pd.DataFrame(all_results)
    df.to_csv('comments.csv', index=False)

    return {"message": f"Berhasil mengambil komentar dari {len(video_ids)} video.", "total_komentar": len(df)}

def get_comments(video_id: str, access_token: str):
    url = 'https://youtube.googleapis.com/youtube/v3/commentThreads'
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    params = {
        'part': 'snippet',
        'videoId': video_id,
        'maxResults': 100,
        'textFormat': 'plainText',
    }

    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        print(f'Gagal ambil komentar dari video {video_id}:', response.text)
        return []
    return response.json().get('items', [])
