from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import shutil
import os
import cv2
from .. import models
from ..database import get_db
from ..stream_manager import stream_manager

router = APIRouter(
    prefix="/api/streams",
    tags=["streams"],
)

os.makedirs("uploads", exist_ok=True)

@router.get("/{camera_id}")
async def video_stream(camera_id: int, db: Session = Depends(get_db)):
    camera = db.query(models.Camera).filter(models.Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
        
    config = {
        "density_green_threshold": camera.density_green_threshold,
        "density_yellow_threshold": camera.density_yellow_threshold,
        "confidence_threshold": camera.confidence_threshold,
        "counting_line": camera.counting_line
    }
    
    # URL depends on type
    url = camera.url
    if camera.type == models.CameraType.file:
        url = os.path.join(os.getcwd(), url)
        
    processor, queue = stream_manager.get_or_create_stream(
        camera.id, url, camera.type.value, config
    )
    
    return StreamingResponse(
        processor.generate_frames(queue), 
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@router.post("/upload")
async def upload_video(file: UploadFile = File(...), db: Session = Depends(get_db)):
    file_path = f"uploads/{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Create a camera entry for this file
    new_camera = models.Camera(
        name=f"Upload: {file.filename}",
        type=models.CameraType.file,
        url=file_path
    )
    db.add(new_camera)
    db.commit()
    db.refresh(new_camera)
    
    return {"id": new_camera.id, "camera_id": new_camera.id, "filename": file.filename, "path": file_path}

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
