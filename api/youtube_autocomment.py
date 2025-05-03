from fastapi import APIRouter, Depends, HTTPException, Query, Body
from datetime import datetime
from models.schema import CommentUpdateRequest
from core.config import SUPABASE_KEY, SUPABASE_URL

import requests
import json
import uuid
import httpx

from core.deps import verify_token
from core.deps import get_valid_access_token
from utils.autoreply import generate_reply_with_gemini, generate_sentiment_with_gemini
from core.config import supabase 

router = APIRouter()

@router.get("/autocomment")
def get_autocomment(
    video_name: str = Query(None),
    email: str = Query(...),
    user=Depends(verify_token)
):
    if user.get("email") != email:
        raise HTTPException(status_code=403, detail="Akses ditolak.")

    access_token = get_valid_access_token(email)
    headers = {"Authorization": f"Bearer {access_token}"}

    channel_url = "https://www.googleapis.com/youtube/v3/channels"
    channel_params = {"part": "contentDetails", "mine": "true"}
    channel_res = requests.get(channel_url, headers=headers, params=channel_params).json()

    try:
        uploads_playlist_id = channel_res['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    except:
        raise HTTPException(status_code=400, detail="Gagal mendapatkan playlist uploads.")

    playlist_url = "https://www.googleapis.com/youtube/v3/playlistItems"
    playlist_params = {
        "part": "snippet",
        "playlistId": uploads_playlist_id,
        "maxResults": 50
    }
    playlist_res = requests.get(playlist_url, headers=headers, params=playlist_params).json()

    videos = playlist_res.get("items", [])
    selected_video = None

    for video in videos:
        if video_name and video["snippet"]["title"].lower() == video_name.lower():
            selected_video = video
            break

    if not selected_video:
        if not videos:
            raise HTTPException(status_code=404, detail="Tidak ada video tersedia.")
        selected_video = videos[0]

    video_id = selected_video["snippet"]["resourceId"]["videoId"]

    comment_url = "https://www.googleapis.com/youtube/v3/commentThreads"
    comment_params = {
        "part": "snippet",
        "videoId": video_id,
        "maxResults": 100
    }

    comment_res = requests.get(comment_url, headers=headers, params=comment_params).json()
    comment_items = comment_res.get("items", [])

    try:
        data = []

        for item in comment_items:
            thread_id = item["id"]  
            comment_snippet = item["snippet"]["topLevelComment"]["snippet"]
            comment_text = comment_snippet.get("textDisplay")

            sentiment = generate_sentiment_with_gemini(comment_text)  
            suggested_reply = generate_reply_with_gemini(comment_text)

            comment_id = str(uuid.uuid4())

            supabase.table("autocomments").insert({
                "id": comment_id,
                "thread_id": thread_id,
                "video_id": video_id,
                "video_title": selected_video["snippet"]["title"],
                "comment": comment_text,
                "sentiment": sentiment,
                "suggested_reply": suggested_reply,
                "status": "Pending",
                "executed_at": None,
                "email": email
            }).execute()

            data.append({
                "id": comment_id,
                "thread_id": thread_id, 
                "executed_at": None,
                "comment": comment_text,
                "sentiment": sentiment,
                "suggested_reply": suggested_reply,
                "status": "Pending"
            })

        return {
            "video_id": video_id,
            "video_title": selected_video["snippet"]["title"],
            "comment_table": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal mendapatkan komentar: {str(e)}")

@router.patch("/autocomment/action")
async def update_comment_action(
    data: CommentUpdateRequest,
    email: str = Query(...),
    user=Depends(verify_token)
):
    if user.get("email") != email:
        raise HTTPException(status_code=403, detail="Unauthorized.")

    if data.status not in ["Approved", "Rejected"]:
        raise HTTPException(status_code=400, detail="Status tidak valid. Gunakan Approved/Rejected.")

    update_payload = {
        "status": data.status,
        "executed_at": datetime.now().isoformat()
    }

    if data.suggested_reply is not None:
        update_payload["suggested_reply"] = data.suggested_reply

    async with httpx.AsyncClient() as client:
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json"
        }

        response = await client.patch(
            f"{SUPABASE_URL}/rest/v1/autocomments?id=eq.{data.comment_id}",
            headers=headers,
            json=update_payload
        )

        if response.status_code not in [200, 204]:
            raise HTTPException(
                status_code=500,
                detail=f"Gagal menyimpan ke Supabase. Error: {response.text}"
            )

    return {
        "message": "Komentar berhasil diupdate.",
        "updated_data": update_payload
    }

@router.post("/autocomment/push")
async def push_autocomment(
    video_id: str = Body(...),
    comment_id: str = Body(...),
    email: str = Query(...),
    user=Depends(verify_token)
):
    if user.get("email") != email:
        raise HTTPException(status_code=403, detail="Akses ditolak.")

    response = supabase.table("autocomments").select("*").eq("id", comment_id).eq("email", email).single().execute()

    if not response.data:
        raise HTTPException(status_code=404, detail="Komentar tidak ditemukan di database.")

    comment = response.data

    if comment["status"] != "Approved":
        raise HTTPException(status_code=400, detail="Komentar belum disetujui.")

    if not comment["suggested_reply"]:
        raise HTTPException(status_code=400, detail="Suggested reply kosong.")

    thread_id = comment.get("thread_id")
    if not thread_id:
        raise HTTPException(status_code=400, detail="Thread ID tidak ditemukan.")

    access_token = get_valid_access_token(email)
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    reply_url = "https://www.googleapis.com/youtube/v3/comments?part=snippet"
    payload = {
        "snippet": {
            "parentId": thread_id,
            "textOriginal": comment["suggested_reply"]
        }
    }

    async with httpx.AsyncClient() as client:
        yt_response = await client.post(reply_url, headers=headers, json=payload)

        if yt_response.status_code != 200:
            raise HTTPException(status_code=500, detail="Gagal mengirim balasan ke YouTube.")

    executed_time = datetime.now().isoformat()

    return {
        "message": "Balasan berhasil dikirim ke YouTube.",
        "comment_id": comment_id,
        "reply": comment["suggested_reply"],
        "executed_at": executed_time
    }