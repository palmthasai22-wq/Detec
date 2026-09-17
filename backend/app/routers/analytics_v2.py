from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import List, Optional
import psutil
from .. import models, schemas
from ..database import get_db

try:
    import pynvml
    HAS_GPU = True
except ImportError:
    HAS_GPU = False

router = APIRouter(prefix="/api/analytics_v2", tags=["analytics_v2"])

@router.get("/history")
def get_history(
    channel_id: Optional[int] = None,
    zone_id: Optional[int] = None,
    range: str = Query("24h", description="1h, 6h, 12h, 24h, 7d, 30d"),
    db: Session = Depends(get_db)
):
    """Get time-series history for charts"""
    time_map = {
        "1h": 1, "6h": 6, "12h": 12, "24h": 24, "7d": 24*7, "30d": 24*30
    }
    hours = time_map.get(range, 24)
    time_threshold = datetime.utcnow() - timedelta(hours=hours)
    
    query = db.query(models.ZoneAnalytics).filter(models.ZoneAnalytics.timestamp >= time_threshold)
    
    if channel_id:
        query = query.filter(models.ZoneAnalytics.channel_id == channel_id)
    if zone_id:
        query = query.filter(models.ZoneAnalytics.zone_id == zone_id)
    else:
        query = query.filter(models.ZoneAnalytics.zone_id == None)
        
    # Grouping logic (simplified, TimescaleDB continuous aggregates would be better here)
    # We will return the raw data and let the frontend aggregate if using SQLite, 
    # but since this is TimescaleDB compatible, we can just return raw for now.
    results = query.order_by(models.ZoneAnalytics.timestamp.asc()).all()
    
    return [
        {
            "timestamp": r.timestamp,
            "density_index": r.density_index,
            "traffic_index": r.traffic_index,
            "total_objects": r.total_objects
        }
        for r in results
    ]

@router.get("/dashboard")
def get_dashboard_kpis(db: Session = Depends(get_db)):
    """Get high-level KPIs for the system"""
    channels_count = db.query(models.Channel).count()
    online_count = db.query(models.Channel).filter(models.Channel.status == "online").count()
    
    return {
        "total_channels": channels_count,
        "online_channels": online_count,
        "active_ai_workers": online_count,
        "system_health": "good"
    }

@router.get("/system")
def get_system_resources():
    """Get CPU, RAM, and GPU usage"""
    cpu_percent = psutil.cpu_percent(interval=0.1)
    ram = psutil.virtual_memory()
    
    gpu_stats = []
    if HAS_GPU:
        try:
            pynvml.nvmlInit()
            device_count = pynvml.nvmlDeviceGetCount()
            for i in range(device_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                gpu_stats.append({
                    "id": i,
                    "name": pynvml.nvmlDeviceGetName(handle),
                    "memory_used": info.used / 1024**2,
                    "memory_total": info.total / 1024**2,
                    "gpu_utilization": util.gpu,
                    "memory_utilization": util.memory
                })
        except Exception as e:
            print(f"NVML Error: {e}")
            
    return {
        "cpu_percent": cpu_percent,
        "ram_percent": ram.percent,
        "ram_used_gb": round(ram.used / 1024**3, 2),
        "ram_total_gb": round(ram.total / 1024**3, 2),
        "gpu_stats": gpu_stats
    }
