import yt_dlp
import ssl
import certifi
import urllib.request
import base64
import os
from pathlib import Path
from typing import Dict, Any

# Globally patch SSL context for urllib (used by yt-dlp) to avoid CERTIFICATE_VERIFY_FAILED
try:
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    ssl._create_default_https_context = lambda: ssl_context
except Exception:
    pass

class YouTubeExtractor:
    @staticmethod
    def _cookie_file() -> str | None:
        """Return an optional Netscape cookie file supplied as a deploy secret."""
        configured_path = os.getenv("YOUTUBE_COOKIES_FILE", "").strip()
        if configured_path and Path(configured_path).is_file():
            return configured_path

        encoded_cookies = os.getenv("YOUTUBE_COOKIES_BASE64", "").strip()
        if not encoded_cookies:
            return None

        cookie_path = Path(os.getenv("DETEC_YOUTUBE_COOKIE_PATH", "/tmp/detec-youtube-cookies.txt"))
        if not cookie_path.is_file():
            cookie_path.write_bytes(base64.b64decode(encoded_cookies, validate=True))
            try:
                cookie_path.chmod(0o600)
            except OSError:
                pass
        return str(cookie_path)

    @staticmethod
    def get_stream_url(youtube_url: str) -> Dict[str, Any]:
        """
        Returns: {"url": str, "is_live": bool, "title": str, "resolution": str, "fps": int, "error": str}
        """
        ydl_opts = {
            'quiet': True,
            # Prefer a single HLS/combined stream.  A video-only DASH URL often
            # expires quickly and is less reliable for long-running live input.
            # AI processing only needs video. Many YouTube live channels expose
            # HLS as separate video/audio tracks, so a combined "best" format
            # may not exist at all.
            'format': 'bestvideo[protocol^=m3u8]/bestvideo/best',
            'noplaylist': True,
            'live_from_start': False,
            'socket_timeout': 15,
            'nocheckcertificate': True,
            # The production image provides Node 22 plus yt-dlp-ejs for
            # YouTube's current JavaScript challenge flow.
            'js_runtimes': {'node': {}},
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            }
        }

        try:
            cookie_file = YouTubeExtractor._cookie_file()
            if cookie_file:
                ydl_opts['cookiefile'] = cookie_file
        except Exception as e:
            return {
                "url": "",
                "is_live": False,
                "title": "",
                "resolution": "",
                "fps": 0,
                "error": f"Invalid YouTube cookie configuration: {e}",
            }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(youtube_url, download=False)
                
                is_live = info_dict.get('is_live', False)
                title = info_dict.get('title', '')
                
                url = info_dict.get('url', '')
                if not url:
                    requested_formats = info_dict.get('requested_formats') or []
                    video_format = next(
                        (item for item in requested_formats if item.get('vcodec') != 'none' and item.get('url')),
                        None,
                    )
                    url = video_format.get('url', '') if video_format else ''
                
                width = info_dict.get('width')
                height = info_dict.get('height')
                resolution = f"{width}x{height}" if width and height else ""
                
                fps_val = info_dict.get('fps')
                fps = int(fps_val) if fps_val is not None else 0
                
                return {
                    "url": url,
                    "is_live": is_live,
                    "title": title,
                    "resolution": resolution,
                    "fps": fps,
                    "error": ""
                }
        except Exception as e:
            return {
                "url": "",
                "is_live": False,
                "title": "",
                "resolution": "",
                "fps": 0,
                "error": str(e)
            }
