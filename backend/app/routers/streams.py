from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from fastapi.responses import StreamingResponse, HTMLResponse, Response
from sqlalchemy.orm import Session
import shutil
import os
import cv2
from html import escape
from pathlib import Path
from uuid import uuid4
from .. import models
from ..database import get_db
from ..stream_manager import stream_manager

router = APIRouter(
    prefix="/api/streams",
    tags=["streams"],
)
public_router = APIRouter(tags=["public-live"])

def _upload_directory():
    configured = os.getenv("DETEC_UPLOAD_DIR")
    if configured:
        return Path(configured)
    database_path = Path(os.getenv("DETEC_DB_PATH", "./detec.db"))
    if database_path.is_absolute():
        return database_path.parent / "uploads"
    return Path("uploads")

UPLOAD_DIR = _upload_directory()
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Removed legacy MJPEG stream endpoints that depended on models.Camera

@router.post("/upload")
async def upload_video(file: UploadFile = File(...), db: Session = Depends(get_db)):
    original_name = Path(file.filename or "video.mp4").name
    stored_name = f"{uuid4().hex}_{original_name}"
    file_path = UPLOAD_DIR / stored_name
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    new_channel = models.Channel(
        name=f"Upload: {original_name}",
        source_type=models.SourceType.mp4.value,
        source_url=str(file_path),
    )
    db.add(new_channel)
    db.commit()
    db.refresh(new_channel)
    
    return {
        "id": new_channel.id,
        "camera_id": new_channel.id,
        "public_id": new_channel.public_id,
        "monitor_path": f"/view/{new_channel.public_url_slug}",
        "filename": original_name,
        "path": str(file_path),
    }

@router.post("/test-connection")
def test_connection(payload: dict):
    """Test if a video stream URL (RTSP/RTMP) is reachable."""
    url = payload.get("url", "")
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")
    
    try:
        cap = cv2.VideoCapture(url)
        if not cap.isOpened():
            return {"success": False, "error": "Could not open stream. Check URL/credentials."}
        
        ret, frame = cap.read()
        if not ret:
            cap.release()
            return {"success": False, "error": "Stream opened but could not read frame."}
        
        h, w = frame.shape[:2]
        cap.release()
        return {"success": True, "resolution": f"{w}x{h}", "message": f"Connected! Resolution: {w}x{h}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/{camera_id}/stop")
def stop_video_stream(camera_id: int):
    stream_manager.stop_stream(camera_id)
    return {"ok": True}
