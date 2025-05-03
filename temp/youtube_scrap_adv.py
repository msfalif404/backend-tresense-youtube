from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import requests
import json
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
    return HTMLResponse(f"<a href='{auth_url}'>Login with Google</a>")

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
    user_tokens['access_token'] = tokens.get('access_token')
    user_tokens['refresh_token'] = tokens.get('refresh_token')

    return HTMLResponse(content="Login berhasil! Sekarang kunjungi /scrape_all")

@app.get("/scrape_all")
def scrape_all():
    # access_token = user_tokens.get('access_token')

    access_token = "ya29.a0AZYkNZjRX6fmV61LRzK2dN-P2KCTEbN0pscVTzk5pb78tPY9M2t41_iK8EuPzDYAP746I8BiPyl2lDj7ZLYBaW3sbNSYb1V0hF4BvJG7U4IKkG6Ja_wHc0h2Sbulna72jffW-axJxcTIrBWFaSCoyrVxsg-GSLqldrD2FXJXaCgYKATUSARYSFQHGX2Mi33HDNsmMYeCHwN7jI294Rw0175"
    if not access_token:
        return {"error": "Belum login, silakan autentikasi dulu."}

    video_ids = [
        "WznY5JDmgkY", "FZ8S9ug5DsQ", "VqLdt2LkW64", "e5gGf--7YtU", "m5v0Waoj0qQ",
        "6trY1WoTE2s", "W5UmbaQKgz8", "d7QGTGG3NVI", "Tl6fDFA4xNI", "yjMq_VX7Jyk"
    ]

    all_results = []

    for video_id in video_ids:
        comments = get_comments(video_id, access_token)
        for item in comments:
            comment = item['snippet']['topLevelComment']['snippet']
            comment_id = item['id']
            reply_count = item['snippet'].get('totalReplyCount', 0)

            comment_data = {
                "video_id": video_id,
                "author": comment['authorDisplayName'],
                "comment": comment['textDisplay'],
                "published_at": comment['publishedAt'],
                "reply_count": reply_count,
                "replies": []
            }

            if reply_count > 0:
                replies = get_replies(comment_id, access_token)
                for reply in replies:
                    snippet = reply['snippet']
                    comment_data['replies'].append({
                        "author": snippet['authorDisplayName'],
                        "comment": snippet['textDisplay'],
                        "published_at": snippet['publishedAt']
                    })

            all_results.append(comment_data)

    with open("comments_with_replies.json", "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    return {"message": "Komentar berhasil di-scrape dan disimpan ke comments_with_replies.json"}

def get_comments(video_id: str, access_token: str):
    url = 'https://youtube.googleapis.com/youtube/v3/commentThreads'
    headers = {'Authorization': f'Bearer {access_token}'}
    params = {
        'part': 'snippet',
        'videoId': video_id,
        'maxResults': 100,
        'textFormat': 'plainText',
    }

    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        print(f"Gagal ambil komentar untuk {video_id}: {response.text}")
        return []
    return response.json().get('items', [])

def get_replies(comment_id: str, access_token: str):
    url = 'https://youtube.googleapis.com/youtube/v3/comments'
    headers = {'Authorization': f'Bearer {access_token}'}
    params = {
        'part': 'snippet',
        'parentId': comment_id,
        'maxResults': 150
    }

    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        print(f"Gagal ambil reply untuk {comment_id}: {response.text}")
        return []
    return response.json().get('items', [])
