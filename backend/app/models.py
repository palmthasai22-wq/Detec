import enum
import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)

class SourceType(str, enum.Enum):
    mp4 = "mp4"
    rtsp = "rtsp"
    rtmp = "rtmp"
    srt = "srt"
    hls = "hls"
    webrtc = "webrtc"
    youtube = "youtube"
    youtube_live = "youtube_live"

class ChannelStatus(str, enum.Enum):
    online = "online"
    offline = "offline"
    error = "error"
    reconnecting = "reconnecting"
    processing = "processing"

class Channel(Base):
    __tablename__ = "channels"

    id = Column(Integer, primary_key=True, index=True)
    public_id = Column(String, unique=True, default=lambda: uuid.uuid4().hex)
    name = Column(String, index=True)
    source_type = Column(String)
    source_url = Column(String, nullable=True)
    source_username = Column(String, nullable=True)
    source_password = Column(String, nullable=True)
    source_port = Column(Integer, nullable=True)
    source_resolution = Column(String, nullable=True)
    source_fps = Column(Integer, nullable=True)
    source_codec = Column(String, nullable=True)
    source_transport = Column(String, nullable=True)
    loop_playback = Column(Boolean, default=True)
    ai_model = Column(String, default="yolo11m")
    confidence_threshold = Column(Float, default=0.15)
    object_classes = Column(JSON, nullable=True)
    status = Column(String, default=ChannelStatus.offline.value)
    is_shared = Column(Boolean, default=False)
    share_token = Column(String, nullable=True, unique=True)
    share_expires_at = Column(DateTime, nullable=True)
    public_url_slug = Column(String, nullable=True, unique=True)
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # backward compatibility fields
    embed_url = Column(String, nullable=True)
    embed_mode = Column(String, nullable=True)
    engine = Column(String, default="yolo")
    roboflow_model_id = Column(String, nullable=True)
    roboflow_api_key = Column(String, nullable=True)
    counting_line = Column(JSON, nullable=True)
    wait_zone = Column(JSON, nullable=True)
    density_green_threshold = Column(Integer, default=5)
    density_yellow_threshold = Column(Integer, default=10)

    zones = relationship("Zone", back_populates="channel")


class Zone(Base):
    __tablename__ = "zones"

    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, ForeignKey("channels.id"), index=True)
    name = Column(String)
    color = Column(String, default="#3b82f6")
    polygon = Column(JSON)
    object_classes = Column(JSON, nullable=True)
    density_enabled = Column(Boolean, default=True)
    traffic_enabled = Column(Boolean, default=True)
    counting_enabled = Column(Boolean, default=True)
    alert_enabled = Column(Boolean, default=False)
    counting_line = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    channel = relationship("Channel", back_populates="zones")


class ZoneAnalytics(Base):
    __tablename__ = "zone_analytics"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    channel_id = Column(Integer, ForeignKey("channels.id"), index=True)
    zone_id = Column(Integer, ForeignKey("zones.id"), nullable=True)
    object_counts = Column(JSON)
    total_objects = Column(Integer, default=0)
    density_index = Column(Integer, default=0)
    traffic_index = Column(Integer, default=0)
    traffic_level = Column(String, default="normal")
    average_speed = Column(Float, default=0.0)
    queue_length = Column(Integer, default=0)
    stopped_count = Column(Integer, default=0)
    in_count = Column(Integer, default=0)
    out_count = Column(Integer, default=0)


class SystemLog(Base):
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    channel_id = Column(Integer, nullable=True)
    event_type = Column(String, index=True)
    message = Column(String)
    # Using alias to avoid conflict with Base.metadata
    metadata_ = Column("metadata", JSON, nullable=True)


class TrafficLog(Base):
    __tablename__ = "traffic_logs"

    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(Integer, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    object_type = Column(String)
    count = Column(Integer)
    direction = Column(String, nullable=True)
