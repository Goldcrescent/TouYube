import os
import shutil
import subprocess
import tempfile
import asyncio
import uuid
from typing import Optional
import httpx


# IMPORTANT!!! 
# run in terminal which yt-dlp and it should return a path, put that below

PATH = "/opt/homebrew/bin/yt-dlp"

# Just run the script to test, everything important to use it is at the bottom


BUCKY_URL = "https://bucky.hackclub.com/"
DOWNLOAD_TIMEOUT = 120.0


_http: Optional[httpx.AsyncClient] = None

def _get_http() -> httpx.AsyncClient:
    global _http
    if _http is None or _http.is_closed:
        _http = httpx.AsyncClient(timeout=10.0)
    return _http

def _resolve_ytdlp() -> Optional[str]:
    candidate = os.getenv("YTDLP_PATH") or shutil.which("yt-dlp")
    if candidate and os.path.exists(candidate):
        return candidate
    fallback = os.path.expanduser(PATH)
    return fallback if os.path.exists(fallback) else None

async def upload_to_bucky(filename: str, content, mimetype: str) -> str:
    resp = await _get_http().post(
        BUCKY_URL, files={"file": (filename, content, mimetype)}, timeout=60.0
    )
    resp.raise_for_status()
    return resp.text.strip()

async def dl(url: str) -> str:
    ytdlp = _resolve_ytdlp()
    if not ytdlp:
        raise RuntimeError("yt-dlp binary could not be found on the server.")

    with tempfile.TemporaryDirectory() as tmpdir:
        out_template = os.path.join(tmpdir, "download.%(ext)s")
        
        dl_result = await asyncio.wait_for(
            asyncio.to_thread(
                subprocess.run,
                [
                    ytdlp,
                    "--no-playlist",
                    "-f",
                    (
                        "best[vcodec!=none][acodec!=none][ext=mp4][filesize<45M]"
                        "/best[vcodec!=none][acodec!=none][filesize<45M]"
                        "/best[vcodec!=none][acodec!=none]"
                    ),
                    "--merge-output-format", "mp4",
                    "-o", out_template,
                    url,
                ],
                capture_output=True,
                text=True,
            ),
            timeout=DOWNLOAD_TIMEOUT,
        )
        
        if dl_result.returncode != 0:
            error_msg = (dl_result.stderr or dl_result.stdout or "")[-500:]
            raise RuntimeError(f"yt-dlp failed: {error_msg or 'Unknown error'}")

        files = [f for f in os.listdir(tmpdir) if not f.startswith(".")]
        if not files:
            raise RuntimeError("No file was downloaded by yt-dlp.")

        video_path = os.path.join(tmpdir, files[0])
        safe_filename = f"{uuid.uuid4()}.mp4"

        with open(video_path, "rb") as vf:
            bucky_url = await upload_to_bucky(safe_filename, vf, "video/mp4")
            
        return bucky_url





# CODE TO USE


async def main():
    target_url = input("Enter URL: ")

    print(f"⏳ Processing download for: {target_url}...")
    subprocess.run(["yt-dlp", target_url])
    try:
        bucky_link = await dl(target_url)
        print("\n🎉 Download and upload complete!")
        print(f"🔗 Bucky URL: {bucky_link}")
    except Exception as e:
        print(f"\n❌ Failed to process video: {e}")
    finally:
        if _http and not _http.is_closed:
            await _http.aclose()


asyncio.run(main())