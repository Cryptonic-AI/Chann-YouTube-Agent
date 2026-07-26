"""
upload_youtube.py
-------------------
Uploads the finished video to YouTube using the OAuth token generated
during setup (stored as GitHub Secrets: YOUTUBE_CLIENT_ID,
YOUTUBE_CLIENT_SECRET, YOUTUBE_TOKEN_JSON).

Sets the title from script.json, writes a simple description, uploads
the custom thumbnail, and tags it as "Not made for kids" by default
(change made_for_kids below if that's wrong for your channel).
"""

import os
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
SCRIPT_PATH = os.path.join(BASE_DIR, "data", "script.json")
VIDEO_PATH = os.path.join(BASE_DIR, "data", "output", "final_video.mp4")
THUMBNAIL_PATH = os.path.join(BASE_DIR, "data", "slides", "thumbnail.png")

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def load_credentials() -> Credentials:
    token_info = json.loads(os.environ["YOUTUBE_TOKEN_JSON"])
    creds = Credentials(
        token=token_info.get("token"),
        refresh_token=token_info["refresh_token"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["YOUTUBE_CLIENT_ID"],
        client_secret=os.environ["YOUTUBE_CLIENT_SECRET"],
        scopes=SCOPES,
    )
    return creds


def build_description(script: dict) -> str:
    return (
        f"{script['title']}\n\n"
        "Ever wondered why this happens? In this video we break it down "
        "in a simple, relatable way.\n\n"
        "New videos every week — subscribe for more relatable discoveries!"
    )


def main():
    with open(SCRIPT_PATH, encoding="utf-8") as f:
        script = json.load(f)

    creds = load_credentials()
    youtube = build("youtube", "v3", credentials=creds)

    body = {
        "snippet": {
            "title": script["title"][:100],
            "description": build_description(script),
            "tags": ["relatable", "did you know", "psychology", "discovery"],
            "categoryId": "27",  # Education
        },
        "status": {
            "privacyStatus": "private",  # change to "public" once you trust the pipeline
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(VIDEO_PATH, chunksize=-1, resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Upload progress: {int(status.progress() * 100)}%")

    video_id = response["id"]
    print(f"Uploaded: https://youtu.be/{video_id}")

    if os.path.exists(THUMBNAIL_PATH):
        youtube.thumbnails().set(videoId=video_id, media_body=MediaFileUpload(THUMBNAIL_PATH)).execute()
        print("Custom thumbnail set.")


if __name__ == "__main__":
    main()
