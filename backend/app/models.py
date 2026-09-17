from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, JSON
from datetime import datetime
from .database import Base
import enum
import uuid

class CameraType(str, enum.Enum):
    rtsp = "rtsp"
    rtmp = "rtmp"
    file = "file"
    embed = "embed"

class Camera(Base):
    __tablename__ = "cameras"

    id = Column(Integer, primary_key=True, index=True)
    public_id = Column(String, unique=True, index=True, nullable=False, default=lambda: uuid.uuid4().hex)
    name = Column(String, index=True)
    type = Column(Enum(CameraType), default=CameraType.rtsp)
    url = Column(String, nullable=True)  # AI stream URL or file path
    embed_url = Column(String, nullable=True)  # Safe src extracted from an image URL or iframe
    embed_mode = Column(String, nullable=True)  # "image" or "iframe"
    density_green_threshold = Column(Integer, default=10) # 0-10 vehicles -> green
    density_yellow_threshold = Column(Integer, default=20) # 11-20 -> yellow, >20 -> red
    confidence_threshold = Column(Float, default=0.10)
    counting_line = Column(JSON, nullable=True) # For files: [[x1,y1], [x2,y2]]
    engine = Column(String, default="yolo") # "yolo" or "roboflow"
    roboflow_model_id = Column(String, nullable=True)
    roboflow_api_key = Column(String, nullable=True)
    wait_zone = Column(JSON, nullable=True) # For traffic light waiting zones: [[x,y], [x,y], ...]
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)

class TrafficLog(Base):
    __tablename__ = "traffic_logs"

    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(Integer, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    person_count = Column(Integer, default=0)
    car_count = Column(Integer, default=0)
    motorcycle_count = Column(Integer, default=0)
    truck_count = Column(Integer, default=0)
    density_level = Column(String) # 'green', 'yellow', 'red', 'blue'
