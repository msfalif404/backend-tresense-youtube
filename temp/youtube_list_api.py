import random
import dotenv
import os
import requests

dotenv.load_dotenv()
API_KEY = os.getenv("API_KEY")

def get_random_video_ids_from_indonesia(max_channels=10, videos_per_channel=10):
    POPULAR_KEYWORDS = [
        "musik", "berita", "film", "komedi", "game", "politik", "selebriti", "hiburan", 
        "vlog", "live", "tutorial", "review", "travel", "masakan", "teknologi", "seni", 
        "olahraga", "kesehatan", "pendidikan", "fashion"
    ]
    collected_video_ids = []

    for _ in range(max_channels):
        keyword = random.choice(POPULAR_KEYWORDS)
        print(f"🔍 Mencari dengan keyword: {keyword}")

        search_url = "https://www.googleapis.com/youtube/v3/search"
        search_params = {
            "part": "snippet",
            "q": keyword,
            "type": "video",
            "regionCode": "ID",
            "maxResults": 10,
            "key": API_KEY
        }

        res = requests.get(search_url, params=search_params)
        data = res.json()

        if "items" not in data:
            continue

        channels = list(set([item['snippet']['channelId'] for item in data['items']]))

        for channel_id in channels[:1]:
            channel_video_url = "https://www.googleapis.com/youtube/v3/search"
            channel_params = {
                "part": "snippet",
                "channelId": channel_id,
                "order": "date",
                "maxResults": videos_per_channel,
                "type": "video",
                "key": API_KEY
            }

            video_res = requests.get(channel_video_url, params=channel_params)
            video_data = video_res.json()

            if "items" in video_data:
                for item in video_data['items']:
                    video_id = item['id']['videoId']
                    collected_video_ids.append(video_id)

    return list(set(collected_video_ids))