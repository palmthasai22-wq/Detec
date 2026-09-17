import uuid
import random
import string
import re
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

try:
    from .. import stream_manager
except ImportError:
    stream_manager = None

router = APIRouter(prefix="/api/channels", tags=["channels"])
cameras_router = APIRouter(prefix="/api/cameras", tags=["cameras (legacy)"])

def generate_slug(name: str) -> str:
    slug = name.lower()
    slug = re.sub(r'[^a-z0-9]+', '-', slug).strip('-')
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
    return f"{slug}-{suffix}" if slug else suffix

@router.get("", response_model=List[schemas.Channel])
@cameras_router.get("", response_model=List[schemas.Channel])
def list_channels(skip: int = 0, limit: int = 100, status: Optional[str] = None, db: Session = Depends(get_db)):
    """List all channels"""
    query = db.query(models.Channel)
    if status:
        query = query.filter(models.Channel.status == status)
    return query.offset(skip).limit(limit).all()

@router.get("/{channel_id}", response_model=schemas.Channel)
@cameras_router.get("/{channel_id}", response_model=schemas.Channel)
def get_channel(channel_id: int, db: Session = Depends(get_db)):
    """Get single channel"""
    channel = db.query(models.Channel).filter(models.Channel.id == channel_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    return channel

@router.post("", response_model=schemas.Channel)
@cameras_router.post("", response_model=schemas.Channel)
def create_channel(channel_in: schemas.ChannelCreate, db: Session = Depends(get_db)):
    """Create channel"""
    db_channel = models.Channel(**channel_in.model_dump())
    db_channel.public_id = uuid.uuid4().hex
    db_channel.share_token = uuid.uuid4().hex[:12]
    
    name_for_slug = channel_in.name if channel_in.name else "channel"
    db_channel.public_url_slug = generate_slug(name_for_slug)
    
    db.add(db_channel)
    db.commit()
    db.refresh(db_channel)
    return db_channel

@router.put("/{channel_id}", response_model=schemas.Channel)
@cameras_router.put("/{channel_id}", response_model=schemas.Channel)
def update_channel(channel_id: int, channel_in: schemas.ChannelUpdate, db: Session = Depends(get_db)):
    """Update channel"""
    db_channel = db.query(models.Channel).filter(models.Channel.id == channel_id).first()
    if not db_channel:
        raise HTTPException(status_code=404, detail="Channel not found")
        
    update_data = channel_in.model_dump(exclude_unset=True)
    
    # Check if we need to update stream
    needs_stream_update = False
    if "confidence_threshold" in update_data or "object_classes" in update_data:
        needs_stream_update = True
        
    for key, value in update_data.items():
        setattr(db_channel, key, value)
        
    db.commit()
    db.refresh(db_channel)
    
    if needs_stream_update and stream_manager:
        if hasattr(stream_manager, 'update_stream_config'):
            stream_manager.update_stream_config(channel_id, update_data)
            
    return db_channel

@router.delete("/{channel_id}")
@cameras_router.delete("/{channel_id}")
def delete_channel(channel_id: int, db: Session = Depends(get_db)):
    """Delete channel"""
    db_channel = db.query(models.Channel).filter(models.Channel.id == channel_id).first()
    if not db_channel:
        raise HTTPException(status_code=404, detail="Channel not found")
        
    # Delete related zones and analytics
    db.query(models.ZoneAnalytics).filter(models.ZoneAnalytics.channel_id == channel_id).delete()
    db.query(models.Zone).filter(models.Zone.channel_id == channel_id).delete()
    db.delete(db_channel)
    db.commit()
    
    if stream_manager and hasattr(stream_manager, 'stop_stream'):
        stream_manager.stop_stream(channel_id)
        
    return {"ok": True}

@router.post("/{channel_id}/share")
@cameras_router.post("/{channel_id}/share")
def enable_sharing(channel_id: int, db: Session = Depends(get_db)):
    """Enable sharing"""
    db_channel = db.query(models.Channel).filter(models.Channel.id == channel_id).first()
    if not db_channel:
        raise HTTPException(status_code=404, detail="Channel not found")
        
    db_channel.is_shared = True
    if not db_channel.share_token:
        db_channel.share_token = uuid.uuid4().hex[:12]
    if not db_channel.public_url_slug:
        name_for_slug = db_channel.name if db_channel.name else "channel"
        db_channel.public_url_slug = generate_slug(name_for_slug)
        
    db.commit()
    db.refresh(db_channel)
    
    return {
        "shared": True,
        "public_url": f"/view/{db_channel.public_url_slug}",
        "share_token": db_channel.share_token
    }

@router.delete("/{channel_id}/share")
@cameras_router.delete("/{channel_id}/share")
def disable_sharing(channel_id: int, db: Session = Depends(get_db)):
    """Disable sharing"""
    db_channel = db.query(models.Channel).filter(models.Channel.id == channel_id).first()
    if not db_channel:
        raise HTTPException(status_code=404, detail="Channel not found")
        
    db_channel.is_shared = False
    db.commit()
    db.refresh(db_channel)
    
    return {"shared": False}

@router.post("/{channel_id}/share/regenerate")
@cameras_router.post("/{channel_id}/share/regenerate")
def regenerate_share_token(channel_id: int, db: Session = Depends(get_db)):
    """Regenerate share token"""
    db_channel = db.query(models.Channel).filter(models.Channel.id == channel_id).first()
    if not db_channel:
        raise HTTPException(status_code=404, detail="Channel not found")
        
    db_channel.share_token = uuid.uuid4().hex[:12]
    name_for_slug = db_channel.name if db_channel.name else "channel"
    db_channel.public_url_slug = generate_slug(name_for_slug)
    
    db.commit()
    db.refresh(db_channel)
    
    return {
        "shared": db_channel.is_shared,
        "public_url": f"/view/{db_channel.public_url_slug}",
        "share_token": db_channel.share_token
    }

@router.get("/{channel_id}/status")
@cameras_router.get("/{channel_id}/status")
def get_channel_status(channel_id: int, db: Session = Depends(get_db)):
    """Get channel real-time status"""
    db_channel = db.query(models.Channel).filter(models.Channel.id == channel_id).first()
    if not db_channel:
        raise HTTPException(status_code=404, detail="Channel not found")
        
    status_info = {
        "is_active": False,
        "fps": 0,
        "latency": 0,
        "viewer_count": 0
    }
    
    if stream_manager:
        if hasattr(stream_manager, 'get_stream_status'):
            stream_info = stream_manager.get_stream_status(channel_id)
            if stream_info:
                status_info.update(stream_info)
        elif hasattr(stream_manager, 'is_active'):
            status_info["is_active"] = stream_manager.is_active(channel_id)
            
    return status_info
