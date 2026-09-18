from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from .. import models, schemas
from ..database import get_db

try:
    from ..stream_manager import stream_manager
except ImportError:
    stream_manager = None

router = APIRouter(prefix="/api/public", tags=["public"])

@router.get("/{slug}/stream")
def get_public_stream(slug: str, db: Session = Depends(get_db)):
    """Returns HLS and WebRTC URLs for a public channel"""
    channel = db.query(models.Channel).filter(
        models.Channel.public_url_slug == slug,
        models.Channel.is_shared == True
    ).first()
    
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found or not public")
        
    # In production, these should map to the actual CDN or external domain
    # For now, we return relative URLs or localhost ports assuming same origin
    return {
        "channel_name": channel.name,
        "status": channel.status,
        "hls_url": f"http://localhost:8888/{slug}/index.m3u8",
        "webrtc_url": f"http://localhost:8889/{slug}/whep",
        "mjpeg_url": f"/api/streams/{channel.id}"
    }

@router.get("/{slug}/stats")
def get_public_stats(slug: str, db: Session = Depends(get_db)):
    """Returns real-time analytics for public display without exposing admin info"""
    channel = db.query(models.Channel).filter(
        models.Channel.public_url_slug == slug,
        models.Channel.is_shared == True
    ).first()
    
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found or not public")
        
    # Get latest stats from time-series DB
    latest_stat = db.query(models.ZoneAnalytics).filter(
        models.ZoneAnalytics.channel_id == channel.id,
        models.ZoneAnalytics.zone_id == None
    ).order_by(models.ZoneAnalytics.timestamp.desc()).first()
    
    if not latest_stat:
        return {
            "density_index": 0,
            "traffic_index": 0,
            "traffic_level": "UNKNOWN",
            "total_objects": 0
        }
        
    return {
        "density_index": latest_stat.density_index,
        "traffic_index": latest_stat.traffic_index,
        "traffic_level": latest_stat.traffic_level,
        "total_objects": latest_stat.total_objects
    }
