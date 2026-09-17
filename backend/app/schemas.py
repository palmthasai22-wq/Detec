from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from urllib.parse import urlparse
from .models import CameraType

class CameraBase(BaseModel):
    name: str
    type: CameraType
    url: Optional[str] = None
    embed_url: Optional[str] = None
    embed_mode: Optional[str] = None
    density_green_threshold: Optional[int] = 10
    density_yellow_threshold: Optional[int] = 20
    confidence_threshold: Optional[float] = 0.15
    counting_line: Optional[List[List[int]]] = None
    wait_zone: Optional[List[List[float]]] = None
    engine: Optional[str] = "yolo"
    roboflow_model_id: Optional[str] = None
    roboflow_api_key: Optional[str] = None
    lat: Optional[float] = Field(default=None, ge=-90, le=90)
    lng: Optional[float] = Field(default=None, ge=-180, le=180)

    @field_validator("embed_url")
    @classmethod
    def validate_embed_url(cls, value):
        if value in (None, ""):
            return None
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("embed_url must be an http(s) URL")
        return value

    @field_validator("embed_mode")
    @classmethod
    def validate_embed_mode(cls, value):
        if value in (None, ""):
            return None
        if value not in {"image", "iframe"}:
            raise ValueError("embed_mode must be image or iframe")
        return value

    @model_validator(mode="after")
    def coordinates_must_be_a_pair(self):
        if (self.lat is None) != (self.lng is None):
            raise ValueError("lat and lng must be provided together")
        if not self.url and not self.embed_url:
            raise ValueError("url or embed_url is required")
        if self.type == CameraType.embed and not self.embed_url:
            raise ValueError("embed_url is required for embed cameras")
        return self

class CameraCreate(CameraBase):
    pass

class CameraUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[CameraType] = None
    url: Optional[str] = None
    embed_url: Optional[str] = None
    embed_mode: Optional[str] = None
    density_green_threshold: Optional[int] = None
    density_yellow_threshold: Optional[int] = None
    confidence_threshold: Optional[float] = None
    counting_line: Optional[List[List[int]]] = None
    wait_zone: Optional[List[List[float]]] = None
    engine: Optional[str] = None
    roboflow_model_id: Optional[str] = None
    roboflow_api_key: Optional[str] = None
    lat: Optional[float] = Field(default=None, ge=-90, le=90)
    lng: Optional[float] = Field(default=None, ge=-180, le=180)

    _validate_embed_url = field_validator("embed_url")(CameraBase.validate_embed_url.__func__)
    _validate_embed_mode = field_validator("embed_mode")(CameraBase.validate_embed_mode.__func__)

    @model_validator(mode="after")
    def coordinates_must_be_a_pair(self):
        if (self.lat is None) != (self.lng is None):
            raise ValueError("lat and lng must be provided together")
        return self

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
