from typing import List
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/channels/{channel_id}/zones", tags=["zones"])

@router.get("", response_model=List[schemas.Zone])
def list_zones(channel_id: int, db: Session = Depends(get_db)):
    """List all zones for a channel"""
    channel = db.query(models.Channel).filter(models.Channel.id == channel_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
        
    zones = db.query(models.Zone).filter(models.Zone.channel_id == channel_id).all()
    return zones

@router.get("/{zone_id}", response_model=schemas.Zone)
def get_zone(channel_id: int, zone_id: int, db: Session = Depends(get_db)):
    """Get single zone"""
    zone = db.query(models.Zone).filter(models.Zone.id == zone_id, models.Zone.channel_id == channel_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    return zone

@router.post("", response_model=schemas.Zone)
def create_zone(channel_id: int, zone_in: schemas.ZoneCreate, db: Session = Depends(get_db)):
    """Create zone"""
    channel = db.query(models.Channel).filter(models.Channel.id == channel_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
        
    db_zone = models.Zone(**zone_in.model_dump())
    db_zone.channel_id = channel_id
    
    db.add(db_zone)
    db.commit()
    db.refresh(db_zone)
    return db_zone

@router.put("/{zone_id}", response_model=schemas.Zone)
def update_zone(channel_id: int, zone_id: int, zone_in: schemas.ZoneUpdate, db: Session = Depends(get_db)):
    """Update zone"""
    db_zone = db.query(models.Zone).filter(models.Zone.id == zone_id, models.Zone.channel_id == channel_id).first()
    if not db_zone:
        raise HTTPException(status_code=404, detail="Zone not found")
        
    update_data = zone_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_zone, key, value)
        
    db.commit()
    db.refresh(db_zone)
    return db_zone

@router.delete("/{zone_id}")
def delete_zone(channel_id: int, zone_id: int, db: Session = Depends(get_db)):
    """Delete zone"""
    db_zone = db.query(models.Zone).filter(models.Zone.id == zone_id, models.Zone.channel_id == channel_id).first()
    if not db_zone:
        raise HTTPException(status_code=404, detail="Zone not found")
        
    db.query(models.ZoneAnalytics).filter(models.ZoneAnalytics.zone_id == zone_id).delete()
    db.delete(db_zone)
    db.commit()
    return {"ok": True}

@router.get("/{zone_id}/analytics", response_model=List[schemas.ZoneAnalyticsOut])
def get_zone_analytics(
    channel_id: int, 
    zone_id: int, 
    limit: int = Query(100), 
    hours: int = Query(24), 
    db: Session = Depends(get_db)
):
    """Get zone analytics history"""
    zone = db.query(models.Zone).filter(models.Zone.id == zone_id, models.Zone.channel_id == channel_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
        
    time_threshold = datetime.utcnow() - timedelta(hours=hours)
    
    analytics = db.query(models.ZoneAnalytics)\
        .filter(models.ZoneAnalytics.zone_id == zone_id)\
        .filter(models.ZoneAnalytics.timestamp >= time_threshold)\
        .order_by(models.ZoneAnalytics.timestamp.desc())\
        .limit(limit)\
        .all()
        
    return analytics
