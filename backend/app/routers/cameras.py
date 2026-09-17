from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas
from ..database import get_db

router = APIRouter(
    prefix="/api/cameras",
    tags=["cameras"],
)

@router.get("", response_model=List[schemas.Camera])
def read_cameras(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    cameras = db.query(models.Camera).offset(skip).limit(limit).all()
    return cameras

@router.get("/{camera_id}", response_model=schemas.Camera)
def read_camera(camera_id: int, db: Session = Depends(get_db)):
    camera = db.query(models.Camera).filter(models.Camera.id == camera_id).first()
    if camera is None:
        raise HTTPException(status_code=404, detail="Camera not found")
    return camera

@router.post("", response_model=schemas.Camera)
def create_camera(camera: schemas.CameraCreate, db: Session = Depends(get_db)):
    db_camera = models.Camera(**camera.dict())
    db.add(db_camera)
    db.commit()
    db.refresh(db_camera)
    return db_camera

@router.put("/{camera_id}", response_model=schemas.Camera)
def update_camera(camera_id: int, camera: schemas.CameraUpdate, db: Session = Depends(get_db)):
    db_camera = db.query(models.Camera).filter(models.Camera.id == camera_id).first()
    if db_camera is None:
        raise HTTPException(status_code=404, detail="Camera not found")
    
    update_data = camera.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_camera, key, value)
    db.commit()
    db.refresh(db_camera)
    
    # Update running stream config dynamically
    from .streams import stream_manager
    if camera_id in stream_manager.active_streams:
        processor = stream_manager.active_streams[camera_id]
        processor.config = {
            "density_green_threshold": db_camera.density_green_threshold,
            "density_yellow_threshold": db_camera.density_yellow_threshold,
            "confidence_threshold": db_camera.confidence_threshold,
            "counting_line": db_camera.counting_line,
            "wait_zone": db_camera.wait_zone,
            "engine": db_camera.engine,
            "roboflow_model_id": db_camera.roboflow_model_id,
            "roboflow_api_key": db_camera.roboflow_api_key
        }
        
    return db_camera

@router.delete("/{camera_id}")
def delete_camera(camera_id: int, db: Session = Depends(get_db)):
    db_camera = db.query(models.Camera).filter(models.Camera.id == camera_id).first()
    if db_camera is None:
        raise HTTPException(status_code=404, detail="Camera not found")
    db.delete(db_camera)
    db.commit()
    return {"ok": True}
