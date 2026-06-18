import json
import os
from urllib.parse import urlencode
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import subprocess

def youtube_search(query, api_key, max_results=20):
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max_results,
        "key": api_key
    }
    request = Request(f"{url}?{urlencode(params)}")
    try:
        with urlopen(request) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        print(f"Error: {exc.code} {exc.reason}")
        if error_body:
            print(error_body)
        return None
    except Exception as exc:
        print(f"Error: {exc}")
        return None
    
def main():
    api_key = os.getenv("YOUTUBE_API_KEY", "ENTER_YOUTUBE_API_KEY_HERE").strip()
    if not api_key:
        api_key = input("Enter YOUTUBE_API_KEY: ").strip()
        if not api_key:
            print("Error: YOUTUBE_API_KEY not provided.")
            return
    query = input("Enter search query: ")
    results = youtube_search(query, api_key)
    if results:
        for item in results.get("items", []):
            video_id = item["id"]["videoId"]
            title = item["snippet"]["title"]
            print(f"{title} - https://www.youtube.com/watch?v={video_id}")

if __name__ == "__main__":
    main()
    subprocess.run(["python", "downloadvid.py"])