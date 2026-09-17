from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict
import json
import asyncio
from .. import models, schemas
from ..database import get_db

router = APIRouter(
    prefix="/api/analytics",
    tags=["analytics"],
)

class ConnectionManager:
# ... existing ConnectionManager code ...
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass

manager = ConnectionManager()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # We just keep connection alive, frontend doesn't need to send much
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@router.get("/live_traffic")
def get_live_traffic(db: Session = Depends(get_db)):
    """Returns the live traffic stats and coordinates for all cameras."""
    from ..stream_manager import stream_manager
    cameras = db.query(models.Camera).all()
    results = []
    for cam in cameras:
        # Check if stream is active and has stats
        processor = stream_manager.active_streams.get(cam.id)
        stats = processor.latest_stats if processor else None
        
        # If no active stats, return default structure but with lat/lng
        cam_data = {
            "camera_id": cam.id,
            "name": cam.name,
            "lat": cam.lat,
            "lng": cam.lng,
            "active": processor is not None and stats is not None,
            "jam_index": stats["congestion_index"] if stats else 0,
            "density_level": stats["density"] if stats else "green",
            "current_vehicles": stats["current_vehicles"] if stats else 0
        }
        results.append(cam_data)
        
    return results

@router.get("/logs", response_model=List[schemas.TrafficLog])
def read_logs(skip: int = 0, limit: int = 100, camera_id: int = None, db: Session = Depends(get_db)):
    query = db.query(models.TrafficLog)
    if camera_id:
        query = query.filter(models.TrafficLog.camera_id == camera_id)
    return query.order_by(models.TrafficLog.timestamp.desc()).offset(skip).limit(limit).all()

async def broadcast_analytics(data: dict):
    await manager.broadcast(json.dumps(data))
