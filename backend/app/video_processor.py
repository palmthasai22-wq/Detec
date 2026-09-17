import cv2
import numpy as np
import asyncio
import time
from datetime import datetime, timezone
from collections import deque
from ultralytics import YOLO
import supervision as sv

from . import models
from .density_analyzer import DensityAnalyzer
from .traffic_analyzer import TrafficAnalyzer
from .source_validator import SourceValidator
from .youtube_extractor import YouTubeExtractor

# Fallback classes map for labeling
CLASS_NAMES_DICT = {
    0: 'person', 1: 'bicycle', 2: 'car', 3: 'motorcycle', 5: 'bus', 7: 'truck'
}

class VideoProcessor:
    def __init__(self, channel: models.Channel, zones: list[models.Zone]):
        self.channel_id = channel.id
        self.source_url = channel.source_url
        self.source_type = channel.source_type
        self.ai_model_name = channel.ai_model or "yolo11m"
        self.conf_thresh = channel.confidence_threshold or 0.25
        self.target_classes = channel.object_classes or [0, 1, 2, 3, 5, 7]
        
        self.running = False
        self.latest_frame = None
        self.frame_version = 0
        self.frame_condition = asyncio.Condition()
        self.viewer_lock = asyncio.Lock()
        self.viewer_count = 0
        self.max_viewers = 30
        
        self.tracker = sv.ByteTrack()
        self.zones_config = zones
        
        self.sv_zones = {}
        self.density_analyzers = {}
        self.traffic_analyzers = {}
        self.track_history = {}
        
        try:
            self.model = YOLO(f"{self.ai_model_name}.pt")
        except Exception:
            print(f"Fallback to yolo11m.pt for channel {self.channel_id}")
            self.model = YOLO("yolo11m.pt")
            
        self.frame_resolution = None

    def _init_zones(self, resolution):
        """Initialize Supervision polygons and analyzers once resolution is known"""
        if self.frame_resolution == resolution:
            return
            
        self.frame_resolution = resolution
        w, h = resolution
        
        self.sv_zones = {}
        self.density_analyzers = {}
        self.traffic_analyzers = {}
        
        for z in self.zones_config:
            if z.polygon:
                # Convert normalized coords [0-1] to absolute pixels
                pts = np.array(z.polygon, dtype=np.float32)
                scaled_pts = (pts * [w, h]).astype(np.int32)
                self.sv_zones[z.id] = sv.PolygonZone(polygon=scaled_pts, frame_resolution_wh=(w, h))
                
                # Zone capacity could be a config, defaulting to 50 for now
                self.density_analyzers[z.id] = DensityAnalyzer(zone_polygon=scaled_pts, zone_capacity=50)
                self.traffic_analyzers[z.id] = TrafficAnalyzer()

    def process_frame_raw(self, frame):
        h, w = frame.shape[:2]
        self._init_zones((w, h))
        
        results = self.model(frame, verbose=False, classes=self.target_classes, 
                           conf=self.conf_thresh, iou=0.45)[0]
                           
        raw_detections = sv.Detections.from_ultralytics(results)
        tracked_detections = self.tracker.update_with_detections(raw_detections)
        
        current_ids = []
        for i in range(len(tracked_detections)):
            tracker_id = tracked_detections.tracker_id[i]
            bbox = tracked_detections.xyxy[i]
            cx, cy = (bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2
            
            current_ids.append(tracker_id)
            if tracker_id not in self.track_history:
                self.track_history[tracker_id] = deque(maxlen=20)
            self.track_history[tracker_id].append((cx, cy))
            
        # Clean up lost tracks
        self.track_history = {k: v for k, v in self.track_history.items() if k in current_ids}
        
        # Analyze each zone
        zone_stats_list = []
        
        for z in self.zones_config:
            if z.id not in self.sv_zones:
                continue
                
            zone_obj = self.sv_zones[z.id]
            mask = zone_obj.trigger(detections=tracked_detections)
            zone_detections = tracked_detections[mask]
            
            # Count objects by class
            counts = {}
            for class_id in zone_detections.class_id:
                c_name = CLASS_NAMES_DICT.get(int(class_id), f"class_{class_id}")
                counts[c_name] = counts.get(c_name, 0) + 1
                
            density_data = {"density_index": 0}
            if z.density_enabled:
                density_data = self.density_analyzers[z.id].calculate_density(zone_detections)
                
            traffic_data = {"traffic_index": 0, "traffic_level": "NORMAL"}
            if z.traffic_enabled:
                traffic_data = self.traffic_analyzers[z.id].calculate_traffic(
                    zone_detections, self.track_history, density_data["density_index"]
                )
                
            zone_stats_list.append({
                "zone_id": z.id,
                "name": z.name,
                "object_counts": counts,
                "total_objects": len(zone_detections),
                "density_index": density_data["density_index"],
                "traffic_index": traffic_data["traffic_index"],
                "traffic_level": traffic_data["traffic_level"]
            })
            
        # Channel level aggregates
        total_counts = {}
        for class_id in tracked_detections.class_id:
            c_name = CLASS_NAMES_DICT.get(int(class_id), f"class_{class_id}")
            total_counts[c_name] = total_counts.get(c_name, 0) + 1
            
        avg_density = 0
        avg_traffic = 0
        if zone_stats_list:
            avg_density = sum(s["density_index"] for s in zone_stats_list) // len(zone_stats_list)
            avg_traffic = sum(s["traffic_index"] for s in zone_stats_list) // len(zone_stats_list)
            
        channel_stats = {
            "object_counts": total_counts,
            "total_objects": len(tracked_detections),
            "density_index": avg_density,
            "traffic_index": avg_traffic,
            "traffic_level": "NORMAL" if avg_traffic < 25 else "HIGH" # Simplified aggregate
        }
        
        # Prepare broadcast payload
        stats = {
            "camera_id": self.channel_id,
            "channel_stats": channel_stats,
            "zone_stats": zone_stats_list,
            # Backward compat fields for existing frontend (until Phase 4)
            "density": "green" if avg_density < 50 else "red",
            "congestion_index": avg_density,
            "traffic_state": channel_stats["traffic_level"],
            "current_vehicles": channel_stats["total_objects"],
            "car_count": total_counts.get("car", 0),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        return tracked_detections, stats

    async def reserve_viewer(self):
        async with self.viewer_lock:
            if self.viewer_count >= self.max_viewers:
                return False
            self.viewer_count += 1
            return True

    async def release_viewer(self):
        async with self.viewer_lock:
            self.viewer_count = max(0, self.viewer_count - 1)

    async def mjpeg_frames(self):
        last_version = -1
        try:
            while True:
                async with self.frame_condition:
                    await self.frame_condition.wait_for(
                        lambda: self.frame_version != last_version or not self.running
                    )
                    if self.latest_frame is None and not self.running:
                        break
                    frame_bytes = self.latest_frame
                    last_version = self.frame_version
                if frame_bytes is not None:
                    yield (
                        b'--frame\r\n'
                        b'Content-Type: image/jpeg\r\n'
                        b'Cache-Control: no-cache\r\n\r\n' + frame_bytes + b'\r\n'
                    )
                if not self.running:
                    break
        finally:
            await self.release_viewer()

import subprocess

class FFmpegCapture:
    """A wrapper to read frames directly from FFmpeg stdout to bypass OpenCV HTTPS limitations"""
    def __init__(self, url):
        self.url = url
        self.pipe = None
        self.width = 1280
        self.height = 720
        
    def isOpened(self):
        return self.pipe is not None
        
    def open(self):
        # We probe first or just hardcode 720p for fast loading
        command = [
            'ffmpeg', '-y', '-hide_banner', '-loglevel', 'error',
            '-i', self.url,
            '-f', 'image2pipe', '-pix_fmt', 'bgr24',
            '-vcodec', 'rawvideo',
            '-s', f"{self.width}x{self.height}", '-'
        ]
        try:
            self.pipe = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=10**8)
            return True
        except Exception:
            return False
            
    def read(self):
        if not self.pipe:
            return False, None
        
        frame_size = self.width * self.height * 3
        raw_image = self.pipe.stdout.read(frame_size)
        if len(raw_image) != frame_size:
            return False, None
            
        frame = np.frombuffer(raw_image, dtype=np.uint8).reshape((self.height, self.width, 3))
        return True, frame
        
    def release(self):
        if self.pipe:
            self.pipe.terminate()
            self.pipe = None

    def set(self, prop, val):
        pass

def _open_capture(url, source_type):
    # If youtube, prefer OpenCV but if it's HTTPS it might fail. Actually FFmpegCapture is much safer for HLS/YouTube
    if source_type in ["youtube", "youtube_live"]:
        cap = FFmpegCapture(url)
        if cap.open():
            return cap
            
    cap = cv2.VideoCapture(url)
    return cap

    def get_actual_url(self):
        if self.source_type in ["youtube", "youtube_live"]:
            yt_info = YouTubeExtractor.get_stream_url(self.source_url)
            if yt_info.get("url"):
                return yt_info["url"]
        return self.source_url

    async def run(self, broadcast_queue: asyncio.Queue):
        # Run yt-dlp in a background thread so we don't block the async event loop!
        actual_url = await asyncio.to_thread(self.get_actual_url)
        
        # Open capture in a background thread
        cap = await asyncio.to_thread(_open_capture, actual_url, self.source_type)
        
        self.running = True
        
        processing_task = None
        last_stats = None
        last_detections = None
        
        while self.running and await asyncio.to_thread(cap.isOpened):
            success, raw_frame = await asyncio.to_thread(cap.read)
            if not success:
                if self.source_type == "mp4":
                    await asyncio.to_thread(cap.set, cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                break
                
            h, w = raw_frame.shape[:2]
            ai_scale = min(1.0, 1024 / max(h, w))
            ai_frame = cv2.resize(raw_frame, (int(w * ai_scale), int(h * ai_scale))) if ai_scale < 1.0 else raw_frame.copy()
            
            display_scale = min(1.0, 800 / max(h, w))
            annotated_frame = cv2.resize(raw_frame, (int(w * display_scale), int(h * display_scale))) if display_scale < 1.0 else raw_frame.copy()
            
            if processing_task is None or processing_task.done():
                if processing_task and processing_task.done():
                    try:
                        last_detections, stats = processing_task.result()
                        last_stats = stats
                        try:
                            broadcast_queue.put_nowait(stats)
                        except asyncio.QueueFull:
                            pass
                    except Exception as e:
                        print("YOLO Inference Error:", e)
                
                processing_task = asyncio.create_task(asyncio.to_thread(self.process_frame_raw, ai_frame.copy()))
            
            # Draw overlay
            overlay = annotated_frame.copy()
            scale_ratio = display_scale / ai_scale
            
            if last_stats:
                # Draw Zones
                for z in self.zones_config:
                    if z.polygon:
                        pts = np.array(z.polygon, dtype=np.float32)
                        scaled_pts = (pts * [int(w * display_scale), int(h * display_scale)]).astype(np.int32)
                        cv2.fillPoly(overlay, [scaled_pts], (255, 100, 0))
                        cv2.polylines(annotated_frame, [scaled_pts], True, (255, 200, 0), 2)
                        
                cv2.addWeighted(overlay, 0.25, annotated_frame, 0.75, 0, annotated_frame)
                
                # Draw BBoxes
                if last_detections:
                    for i in range(len(last_detections)):
                        bbox = last_detections.xyxy[i]
                        x1, y1, x2, y2 = (bbox * scale_ratio).astype(int)
                        cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                
                # Draw Stats Text
                cv2.rectangle(annotated_frame, (0, 0), (int(w * display_scale), 100), (0, 0, 0), -1)
                cv2.putText(annotated_frame, f"DENSITY: {last_stats['channel_stats']['density_index']}/100", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                cv2.putText(annotated_frame, f"TRAFFIC: {last_stats['channel_stats']['traffic_level']}", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                
            ret, buffer = cv2.imencode('.jpg', annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
            if ret:
                async with self.frame_condition:
                    self.latest_frame = buffer.tobytes()
                    self.frame_version += 1
                    self.frame_condition.notify_all()
            
            await asyncio.sleep(0.01)
                
        cap.release()
        self.running = False
        async with self.frame_condition:
            self.frame_condition.notify_all()
