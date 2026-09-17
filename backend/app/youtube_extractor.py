import yt_dlp
from typing import Dict, Any

class YouTubeExtractor:
    @staticmethod
    def get_stream_url(youtube_url: str) -> Dict[str, Any]:
        """
        Returns: {"url": str, "is_live": bool, "title": str, "resolution": str, "fps": int, "error": str}
        """
        ydl_opts = {'quiet': True, 'format': 'best', 'no_check_certificate': True}
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(youtube_url, download=False)
                
                is_live = info_dict.get('is_live', False)
                title = info_dict.get('title', '')
                
                url = info_dict.get('url', '')
                
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
