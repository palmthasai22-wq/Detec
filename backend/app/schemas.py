from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from .models import SourceType, ChannelStatus

class ChannelBase(BaseModel):
    source_url: Optional[str] = None
    source_username: Optional[str] = None
    source_password: Optional[str] = None
    source_port: Optional[int] = None
    source_resolution: Optional[str] = None
    source_fps: Optional[int] = None
    source_codec: Optional[str] = None
    source_transport: Optional[str] = None
    loop_playback: Optional[bool] = True
    ai_model: Optional[str] = "yolo11m"
    confidence_threshold: Optional[float] = 0.25
    object_classes: Optional[List[int]] = None
    status: Optional[ChannelStatus] = ChannelStatus.offline
    is_shared: Optional[bool] = False
    share_token: Optional[str] = None
    share_expires_at: Optional[datetime] = None
    public_url_slug: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    embed_url: Optional[str] = None
    embed_mode: Optional[str] = None
    engine: Optional[str] = "yolo"
    roboflow_model_id: Optional[str] = None
    roboflow_api_key: Optional[str] = None
    counting_line: Optional[Any] = None
    wait_zone: Optional[Any] = None
    density_green_threshold: Optional[int] = 10
    density_yellow_threshold: Optional[int] = 20

class ChannelCreate(ChannelBase):
    name: str
    source_type: SourceType
    source_url: Optional[str] = None # Optional for mp4 types based on request logic

class ChannelUpdate(BaseModel):
    name: Optional[str] = None
    source_type: Optional[SourceType] = None
    source_url: Optional[str] = None
    source_username: Optional[str] = None
    source_password: Optional[str] = None
    source_port: Optional[int] = None
    source_resolution: Optional[str] = None
    source_fps: Optional[int] = None
    source_codec: Optional[str] = None
    source_transport: Optional[str] = None
    loop_playback: Optional[bool] = None
    ai_model: Optional[str] = None
    confidence_threshold: Optional[float] = None
    object_classes: Optional[List[int]] = None
    status: Optional[ChannelStatus] = None
    is_shared: Optional[bool] = None
    share_token: Optional[str] = None
    share_expires_at: Optional[datetime] = None
    public_url_slug: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    embed_url: Optional[str] = None
    embed_mode: Optional[str] = None
    engine: Optional[str] = None
    roboflow_model_id: Optional[str] = None
    roboflow_api_key: Optional[str] = None
    counting_line: Optional[Any] = None
    wait_zone: Optional[Any] = None
    density_green_threshold: Optional[int] = None
    density_yellow_threshold: Optional[int] = None

class Channel(ChannelBase):
    id: int
    public_id: str
    name: str
    source_type: SourceType
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ZoneBase(BaseModel):
    name: str
    color: Optional[str] = "#3b82f6"
    polygon: Any
    object_classes: Optional[List[int]] = None
    density_enabled: Optional[bool] = True
    traffic_enabled: Optional[bool] = True
    counting_enabled: Optional[bool] = True
    alert_enabled: Optional[bool] = False
    counting_line: Optional[Any] = None

class ZoneCreate(ZoneBase):
    name: str
    polygon: Any

class ZoneUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None
    polygon: Optional[Any] = None
    object_classes: Optional[List[int]] = None
    density_enabled: Optional[bool] = None
    traffic_enabled: Optional[bool] = None
    counting_enabled: Optional[bool] = None
    alert_enabled: Optional[bool] = None
    counting_line: Optional[Any] = None

class Zone(ZoneBase):
    id: int
    channel_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ZoneAnalyticsBase(BaseModel):
    channel_id: int
    zone_id: Optional[int] = None
    object_counts: Dict[str, int]
    total_objects: Optional[int] = 0
    density_index: Optional[int] = 0
    traffic_index: Optional[int] = 0
    traffic_level: Optional[str] = "normal"
    average_speed: Optional[float] = 0.0
    queue_length: Optional[int] = 0
    stopped_count: Optional[int] = 0
    in_count: Optional[int] = 0
    out_count: Optional[int] = 0

class ZoneAnalyticsOut(ZoneAnalyticsBase):
    id: int
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

class AnalyticsQuery(BaseModel):
    channel_id: Optional[int] = None
    zone_id: Optional[int] = None
    time_range: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

class SystemLogOut(BaseModel):
    id: int
    timestamp: datetime
    channel_id: Optional[int] = None
    event_type: str
    message: str
    metadata: Optional[Any] = Field(default=None, alias="metadata_")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class TrafficLogBase(BaseModel):
    camera_id: int
    object_type: str
    count: int
    direction: Optional[str] = None

class TrafficLogCreate(TrafficLogBase):
    pass

class TrafficLog(TrafficLogBase):
    id: int
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

# Aliases for backward compatibility
CameraBase = ChannelBase
CameraCreate = ChannelCreate
CameraUpdate = ChannelUpdate
Camera = Channel
