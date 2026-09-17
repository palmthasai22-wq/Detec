import cv2
from typing import Dict, Any
from .youtube_extractor import YouTubeExtractor

class SourceValidator:
    @staticmethod
    def validate(source_type: str, url: str) -> Dict[str, Any]:
        """
        Returns: {"valid": bool, "protocol": str, "resolution": str, "fps": int, "codec": str, "error": str}
        """
        result = {
            "valid": False,
            "protocol": source_type,
            "resolution": "",
            "fps": 0,
            "codec": "",
            "error": ""
        }
        
        if source_type in ["youtube", "youtube_live"]:
            yt_info = YouTubeExtractor.get_stream_url(url)
            if yt_info.get("error"):
                result["error"] = yt_info["error"]
                return result
            
            result["valid"] = True
            result["resolution"] = yt_info.get("resolution", "")
            result["fps"] = yt_info.get("fps", 0)
            return result
            
        elif source_type in ["rtsp", "rtmp", "srt", "mp4"]:
            cap = cv2.VideoCapture(url)
            if not cap.isOpened():
                result["error"] = "Cannot open stream or file"
                return result
                
            ret, frame = cap.read()
            if not ret:
                result["error"] = "Cannot read frame from stream or file"
                cap.release()
                return result
                
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
            codec = ""
            if fourcc > 0:
                codec = "".join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)])
            
            result["valid"] = True
            result["resolution"] = f"{width}x{height}"
            result["fps"] = fps
            result["codec"] = codec.strip()
            
            cap.release()
            return result
            
        else:
            result["error"] = f"Unsupported source type: {source_type}"
            return result
