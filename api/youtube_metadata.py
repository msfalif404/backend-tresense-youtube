from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from core.deps import get_valid_access_token
from core.config import supabase
from core.deps import verify_token

import requests
import json


router = APIRouter()

@router.get("/get_all_video")
def get_all_video(email: str = Query(...), user=Depends(verify_token)):
    if user.get("email") != email:
        raise HTTPException(status_code=403, detail="Akses ditolak.")

    access_token = get_valid_access_token(email)

    url = "https://www.googleapis.com/youtube/v3/channels"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"part": "contentDetails", "mine": "true"}
    channel_res = requests.get(url, headers=headers, params=params).json()

    try:
        uploads_playlist_id = channel_res['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    except:
        raise HTTPException(status_code=400, detail="Gagal mendapatkan playlist uploads.")

    videos = []
    next_page_token = None

    while True:
        playlist_url = "https://www.googleapis.com/youtube/v3/playlistItems"
        playlist_params = {
            "part": "snippet,contentDetails",
            "playlistId": uploads_playlist_id,
            "maxResults": 50,
            "pageToken": next_page_token
        }

        res = requests.get(playlist_url, headers=headers, params=playlist_params).json()
        for item in res.get("items", []):
            snippet = item["snippet"]
            video_id = snippet["resourceId"]["videoId"]

            video_url = f"https://www.googleapis.com/youtube/v3/videos"
            video_params = {
                "part": "statistics",
                "id": video_id
            }
            video_res = requests.get(video_url, headers=headers, params=video_params).json()
            video_statistics = video_res.get("items", [])[0].get("statistics", {})

            comments = []
            comment_page_token = None

            while True:
                comment_url = "https://www.googleapis.com/youtube/v3/commentThreads"
                comment_params = {
                    "part": "snippet",
                    "videoId": video_id,
                    "maxResults": 100,
                    "pageToken": comment_page_token
                }

                comment_res = requests.get(comment_url, headers=headers, params=comment_params).json()
                for c in comment_res.get("items", []):
                    top_comment = c["snippet"]["topLevelComment"]["snippet"]
                    comment_id = c["snippet"]["topLevelComment"]["id"]
                    comment_data = {
                        "author": top_comment.get("authorDisplayName"),
                        "message": top_comment.get("textDisplay"),
                        "like_count": top_comment.get("likeCount"),
                        "published_at": top_comment.get("publishedAt"),
                        "updated_at": top_comment.get("updatedAt"),
                        "replies": []
                    }

                    if c["snippet"].get("totalReplyCount", 0) > 0:
                        reply_page_token = None
                        while True:
                            replies_url = "https://www.googleapis.com/youtube/v3/comments"
                            replies_params = {
                                "part": "snippet",
                                "parentId": comment_id,
                                "maxResults": 100,
                                "pageToken": reply_page_token
                            }
                            replies_res = requests.get(replies_url, headers=headers, params=replies_params).json()
                            for r in replies_res.get("items", []):
                                reply_snippet = r["snippet"]
                                comment_data["replies"].append({
                                    "author": reply_snippet.get("authorDisplayName"),
                                    "message": reply_snippet.get("textDisplay"),
                                    "like_count": reply_snippet.get("likeCount"),
                                    "published_at": reply_snippet.get("publishedAt"),
                                    "updated_at": reply_snippet.get("updatedAt")
                                })

                            reply_page_token = replies_res.get("nextPageToken")
                            if not reply_page_token:
                                break

                    comments.append(comment_data)

                comment_page_token = comment_res.get("nextPageToken")
                if not comment_page_token:
                    break

            videos.append({
                "video_id": video_id,
                "title": snippet["title"],
                "thumbnail": snippet["thumbnails"]["standard"]["url"],
                "description": snippet["description"],
                "published_at": snippet["publishedAt"],
                "channel_title": snippet["channelTitle"],
                "statistics": {
                    "view_count": video_statistics.get("viewCount", 0),
                    "like_count": video_statistics.get("likeCount", 0),
                    "dislike_count": video_statistics.get("dislikeCount", 0),
                    "comment_count": video_statistics.get("commentCount", 0)
                },
                "comments": comments
            })

        next_page_token = res.get("nextPageToken")
        if not next_page_token:
            break

    with open(f"videos_{email}.json", "w") as f:
        json.dump(videos, f, indent=4)

    return JSONResponse({
        "message": f"Berhasil mengambil {len(videos)} video dari channel user.",
        "data": videos,
    })