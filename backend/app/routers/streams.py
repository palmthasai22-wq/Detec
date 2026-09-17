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

def _get_processor(camera):
    if camera.type == models.CameraType.embed or not camera.url:
        raise HTTPException(status_code=409, detail="This camera is view-only; use its embed_url")
        
    config = {
        "density_green_threshold": camera.density_green_threshold,
        "density_yellow_threshold": camera.density_yellow_threshold,
        "confidence_threshold": camera.confidence_threshold,
        "counting_line": camera.counting_line,
        "wait_zone": camera.wait_zone,
        "engine": camera.engine,
        "roboflow_model_id": camera.roboflow_model_id,
        "roboflow_api_key": camera.roboflow_api_key,
    }
    
    # URL depends on type
    url = camera.url
    if camera.type == models.CameraType.file:
        url = os.path.join(os.getcwd(), url)
        
    processor, queue = stream_manager.get_or_create_stream(
        camera.id, url, camera.type.value, config
    )
    return processor

async def _stream_response(camera):
    processor = _get_processor(camera)
    if not await processor.reserve_viewer():
        return Response(
            content="ผู้ชมเต็ม กรุณาลองใหม่ภายหลัง",
            status_code=503,
            media_type="text/plain; charset=utf-8",
            headers={"Retry-After": "10"},
        )
    return StreamingResponse(
        processor.mjpeg_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={"Cache-Control": "no-store, no-cache, must-revalidate"},
    )

@router.get("/{camera_id}")
async def video_stream(camera_id: int, db: Session = Depends(get_db)):
    camera = db.query(models.Camera).filter(models.Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    return await _stream_response(camera)

@public_router.get("/live/{public_id}", response_class=HTMLResponse)
def public_monitor(public_id: str, db: Session = Depends(get_db)):
    camera = db.query(models.Camera).filter(models.Camera.public_id == public_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    title = escape(camera.name)
    html = f"""<!doctype html>
<html lang="th"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title><style>
html,body{{width:100%;height:100%;margin:0;background:#000;overflow:hidden}}
main{{width:100%;height:100%;display:flex;align-items:center;justify-content:center}}
img{{width:100%;height:100%;object-fit:contain;background:#000}}
#status{{display:none;position:fixed;inset:0;align-items:center;justify-content:center;color:#fff;font:600 16px system-ui;background:#050810}}
</style></head><body><main><img src="/live/{public_id}/stream.mjpg" alt="ภาพสด {title}"
onerror="this.style.display='none';document.getElementById('status').style.display='flex'"></main>
<div id="status">ไม่สามารถเปิดภาพสดได้ หรือผู้ชมเต็ม กรุณาลองใหม่ภายหลัง</div></body></html>"""
    return HTMLResponse(
        html,
        headers={
            "Cache-Control": "no-store",
            "Content-Security-Policy": "default-src 'none'; img-src 'self'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; frame-ancestors *",
        },
    )

@public_router.get("/live/{public_id}/stream.mjpg")
async def public_mjpeg_stream(public_id: str, db: Session = Depends(get_db)):
    camera = db.query(models.Camera).filter(models.Camera.public_id == public_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    return await _stream_response(camera)

@router.post("/upload")
async def upload_video(file: UploadFile = File(...), db: Session = Depends(get_db)):
    original_name = Path(file.filename or "video.mp4").name
    stored_name = f"{uuid4().hex}_{original_name}"
    file_path = UPLOAD_DIR / stored_name
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Create a camera entry for this file
    new_camera = models.Camera(
        name=f"Upload: {original_name}",
        type=models.CameraType.file,
        url=str(file_path),
    )
    db.add(new_camera)
    db.commit()
    db.refresh(new_camera)
    
    return {
        "id": new_camera.id,
        "camera_id": new_camera.id,
        "public_id": new_camera.public_id,
        "monitor_path": f"/live/{new_camera.public_id}",
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
