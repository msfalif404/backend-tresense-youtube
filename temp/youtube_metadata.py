import requests

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
        'maxResults': 100
    }

    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        print(f"Gagal ambil reply untuk {comment_id}: {response.text}")
        return []
    return response.json().get('items', [])

def get_video_metadata(video_id: str, access_token: str):
    url = 'https://youtube.googleapis.com/youtube/v3/videos'
    headers = {'Authorization': f'Bearer {access_token}'}
    params = {
        'part': 'snippet',
        'id': video_id
    }

    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        print(f"Gagal ambil metadata untuk {video_id}: {response.text}")
        return {}
    
    items = response.json().get('items', [])
    if not items:
        return {}

    snippet = items[0].get('snippet', {})
    return {
        "title": snippet.get("title", ""),
        "description": snippet.get("description", "")
    }