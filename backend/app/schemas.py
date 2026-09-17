from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from .models import CameraType

class CameraBase(BaseModel):
    name: str
    type: CameraType
    url: str
    density_green_threshold: Optional[int] = 10
    density_yellow_threshold: Optional[int] = 20
    confidence_threshold: Optional[float] = 0.15
    counting_line: Optional[List[List[int]]] = None
    wait_zone: Optional[List[List[float]]] = None
    engine: Optional[str] = "yolo"
    roboflow_model_id: Optional[str] = None
    roboflow_api_key: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None

class CameraCreate(CameraBase):
    pass

class CameraUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[CameraType] = None
    url: Optional[str] = None
    density_green_threshold: Optional[int] = None
    density_yellow_threshold: Optional[int] = None
    confidence_threshold: Optional[float] = None
    counting_line: Optional[List[List[int]]] = None
    wait_zone: Optional[List[List[float]]] = None
    engine: Optional[str] = None
    roboflow_model_id: Optional[str] = None
    roboflow_api_key: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None

class Camera(CameraBase):
    id: int

    class Config:
        from_attributes = True

class TrafficLogBase(BaseModel):
    camera_id: int
    person_count: int
    car_count: int
    motorcycle_count: int
    truck_count: int
    density_level: str

class TrafficLogCreate(TrafficLogBase):
    pass

class TrafficLog(TrafficLogBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True
