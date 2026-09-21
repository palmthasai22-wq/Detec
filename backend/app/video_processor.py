import cv2
import numpy as np
import asyncio
import time
import math
from datetime import datetime, timezone
from collections import deque
from ultralytics import YOLO
import supervision as sv

from . import models
from .density_analyzer import DensityAnalyzer
from .traffic_analyzer import TrafficAnalyzer
from .source_validator import SourceValidator
from .youtube_extractor import YouTubeExtractor
import subprocess

VEHICLE_CLASS_IDS = {1, 2, 3, 5, 7}

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
        if not self.url or "youtube.com" in self.url or "youtu.be" in self.url:
            return False
            
        # We probe first or just hardcode 720p for fast loading
        command = [
            'ffmpeg', '-y', '-hide_banner', '-loglevel', 'error',
            '-reconnect', '1', '-reconnect_streamed', '1', '-reconnect_delay_max', '5',
            '-rw_timeout', '15000000',
            '-user_agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
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

    def get(self, prop):
        if prop == cv2.CAP_PROP_FRAME_WIDTH:
            return float(self.width)
        if prop == cv2.CAP_PROP_FRAME_HEIGHT:
            return float(self.height)
        if prop == cv2.CAP_PROP_FPS:
            return 30.0
        return 0.0

def _open_capture(url, source_type):
    if not url:
        return cv2.VideoCapture()
    # Auto-detect youtube if the user selected wrong source_type
    is_youtube = source_type in ["youtube", "youtube_live"] or "youtube.com" in url or "youtu.be" in url or "manifest.googlevideo.com" in url
    
    if is_youtube:
        cap = FFmpegCapture(url)
        if cap.open():
            return cap
            
    cap = cv2.VideoCapture(url)
    return cap

# Fallback classes map for labeling
CLASS_NAMES_DICT = {
    0: 'person', 1: 'bicycle', 2: 'car', 3: 'motorcycle', 5: 'bus', 7: 'truck'
}

class VideoProcessor:
    def __init__(self, channel: models.Channel, zones: list[models.Zone]):
        self.channel_id = channel.id
        self.source_url = channel.source_url
        self.source_type = channel.source_type
        self.loop_playback = channel.loop_playback is not False
        self.ai_model_name = channel.ai_model or "yolo11m"
        self.conf_thresh = channel.confidence_threshold if channel.confidence_threshold is not None else 0.15
        self.target_classes = sorted(set(channel.object_classes or [0, 1, 2, 3, 5, 7]) | {0})
        self.green_threshold = max(1, channel.density_green_threshold or 5)
        self.red_threshold = max(self.green_threshold + 1, channel.density_yellow_threshold or 10)
        
        # Save models in UPLOAD_DIR (which maps to /data) to persist across Railway deployments
        from .routers.streams import UPLOAD_DIR
        model_path = UPLOAD_DIR / f"{self.ai_model_name}.pt"
        try:
            self.model = YOLO(str(model_path))
        except Exception:
            print(f"Fallback to yolo11m.pt for channel {self.channel_id}")
            self.model = YOLO("yolo11m.pt")
        
        self.running = False
        self.latest_frame = None
        self.latest_stats = None
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
                
                # Use the camera's red threshold so smaller queues can be
                # classified as congestion instead of requiring ~50 objects.
                self.density_analyzers[z.id] = DensityAnalyzer(
                    zone_polygon=scaled_pts,
                    zone_capacity=self.red_threshold,
                )
                self.traffic_analyzers[z.id] = TrafficAnalyzer()

    def _count_congestion_index(self, vehicle_count: int) -> int:
        """Map configurable vehicle counts to the shared 0-100 traffic scale."""
        if vehicle_count < self.green_threshold:
            return int((vehicle_count / self.green_threshold) * 39)
        if vehicle_count < self.red_threshold:
            span = self.red_threshold - self.green_threshold
            return 40 + int(((vehicle_count - self.green_threshold) / span) * 34)
        return min(
            100,
            75 + int(((vehicle_count - self.red_threshold) / self.red_threshold) * 25),
        )

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
            class_id = int(tracked_detections.class_id[i])
            if class_id not in VEHICLE_CLASS_IDS:
                continue
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
            vehicle_mask = np.isin(zone_detections.class_id, list(VEHICLE_CLASS_IDS))
            zone_vehicles = zone_detections[vehicle_mask]
            
            # Count objects by class
            counts = {}
            for class_id in zone_detections.class_id:
                c_name = CLASS_NAMES_DICT.get(int(class_id), f"class_{class_id}")
                counts[c_name] = counts.get(c_name, 0) + 1
                
            density_data = {"density_index": 0}
            if z.density_enabled:
                density_data = self.density_analyzers[z.id].calculate_density(zone_vehicles)
                
            traffic_data = {"traffic_index": 0, "traffic_level": "NORMAL"}
            if z.traffic_enabled:
                tracker_ids = zone_vehicles.tracker_id
                zone_track_ids = set(
                    int(item) for item in (tracker_ids if tracker_ids is not None else [])
                    if item is not None
                )
                zone_track_history = {
                    track_id: points
                    for track_id, points in self.track_history.items()
                    if track_id in zone_track_ids
                }
                traffic_data = self.traffic_analyzers[z.id].calculate_traffic(
                    zone_vehicles, zone_track_history, density_data["density_index"]
                )
                count_index = self._count_congestion_index(len(zone_vehicles))
                traffic_data["traffic_index"] = max(traffic_data["traffic_index"], count_index)
                traffic_data["traffic_level"] = (
                    "NORMAL" if traffic_data["traffic_index"] < 40
                    else "MEDIUM" if traffic_data["traffic_index"] < 75
                    else "HIGH"
                )
                
            zone_stats_list.append({
                "zone_id": z.id,
                "name": z.name,
                "object_counts": counts,
                "total_objects": len(zone_detections),
                "vehicle_count": len(zone_vehicles),
                "density_index": density_data["density_index"],
                "traffic_index": traffic_data["traffic_index"],
                "traffic_level": traffic_data["traffic_level"]
            })
            
        # Channel level aggregates
        total_counts = {}
        for class_id in tracked_detections.class_id:
            c_name = CLASS_NAMES_DICT.get(int(class_id), f"class_{class_id}")
            total_counts[c_name] = total_counts.get(c_name, 0) + 1

        vehicle_count = sum(total_counts.get(CLASS_NAMES_DICT[class_id], 0) for class_id in VEHICLE_CLASS_IDS)
            
        avg_density = 0
        avg_traffic = 0
        if zone_stats_list:
            # A jam in one configured road zone should not be diluted by empty
            # zones elsewhere in the same camera.
            avg_density = max(s["density_index"] for s in zone_stats_list)
            avg_traffic = max(s["traffic_index"] for s in zone_stats_list)
        else:
            # The defaults (5/10 vehicles) intentionally detect smaller jams.
            avg_density = self._count_congestion_index(vehicle_count)
            avg_traffic = avg_density
            
        channel_stats = {
            "object_counts": total_counts,
            "total_objects": len(tracked_detections),
            "vehicle_count": vehicle_count,
            "density_index": avg_density,
            "traffic_index": avg_traffic,
            "traffic_level": "FLOWING" if avg_traffic < 40 else ("SLOWING" if avg_traffic < 75 else "JAMMED")
        }
        
        # Prepare broadcast payload
        stats = {
            "camera_id": self.channel_id,
            "channel_stats": channel_stats,
            "zone_stats": zone_stats_list,
            # Backward compat fields for existing frontend (until Phase 4)
            "density": "green" if avg_traffic < 40 else ("yellow" if avg_traffic < 75 else "red"),
            "congestion_index": avg_traffic,
            "traffic_state": channel_stats["traffic_level"],
            "current_vehicles": vehicle_count,
            "person_count": total_counts.get("person", 0),
            "car_count": total_counts.get("car", 0),
            "motorcycle_count": total_counts.get("motorcycle", 0),
            "truck_count": total_counts.get("truck", 0) + total_counts.get("bus", 0),
            "in_count": 0,
            "out_count": 0,
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



    def get_actual_url(self):
        is_youtube = self.source_type in ["youtube", "youtube_live"] or "youtube.com" in self.source_url or "youtu.be" in self.source_url
        if is_youtube:
            yt_info = YouTubeExtractor.get_stream_url(self.source_url)
            if yt_info.get("url"):
                return yt_info["url"]
            return ""
        return self.source_url

    async def run(self, broadcast_queue: asyncio.Queue):
        self.running = True
        processing_task = None
        last_stats = None
        last_detections = None
        is_live_source = self.source_type not in ("mp4", "file")

        try:
            while self.running:
                # YouTube playback URLs expire. Resolve the public watch URL
                # again on every reconnect instead of storing a stale URL.
                actual_url = await asyncio.to_thread(self.get_actual_url)
                if not actual_url:
                    await asyncio.sleep(3)
                    continue

                cap = await asyncio.to_thread(_open_capture, actual_url, self.source_type)
                if not await asyncio.to_thread(cap.isOpened):
                    await asyncio.to_thread(cap.release)
                    if not is_live_source:
                        break
                    await asyncio.sleep(3)
                    continue

                fps = await asyncio.to_thread(cap.get, cv2.CAP_PROP_FPS)
                if not fps or fps <= 0 or math.isnan(fps):
                    fps = 30.0
                self.current_fps = fps
                frame_delay = 1.0 / fps

                while self.running and await asyncio.to_thread(cap.isOpened):
                    start_time = time.time()
                    success, raw_frame = await asyncio.to_thread(cap.read)
                    if not success:
                        if not is_live_source and self.loop_playback:
                            await asyncio.to_thread(cap.set, cv2.CAP_PROP_POS_FRAMES, 0)
                            continue
                        break

                    h, w = raw_frame.shape[:2]
                    # Preserve more pixels for distant/small people and cars.
                    ai_scale = min(1.0, 1280 / max(h, w))
                    ai_frame = cv2.resize(raw_frame, (int(w * ai_scale), int(h * ai_scale))) if ai_scale < 1.0 else raw_frame.copy()

                    # Keep the published MJPEG reasonably sized while the
                    # browser scales it to the panel/fullscreen viewport.
                    display_scale = min(1.0, 1280 / max(h, w))
                    annotated_frame = cv2.resize(raw_frame, (int(w * display_scale), int(h * display_scale))) if display_scale < 1.0 else raw_frame.copy()

                    if processing_task is None or processing_task.done():
                        if processing_task and processing_task.done():
                            try:
                                last_detections, stats = processing_task.result()
                                last_stats = stats
                                self.latest_stats = stats
                                try:
                                    broadcast_queue.put_nowait(stats)
                                except asyncio.QueueFull:
                                    pass
                            except Exception as e:
                                print("YOLO Inference Error:", e)

                        processing_task = asyncio.create_task(asyncio.to_thread(self.process_frame_raw, ai_frame.copy()))

                    overlay = annotated_frame.copy()
                    scale_ratio = display_scale / ai_scale

                    if last_stats:
                        for z in self.zones_config:
                            if z.polygon:
                                pts = np.array(z.polygon, dtype=np.float32)
                                scaled_pts = (pts * [int(w * display_scale), int(h * display_scale)]).astype(np.int32)
                                cv2.fillPoly(overlay, [scaled_pts], (255, 100, 0))
                                cv2.polylines(annotated_frame, [scaled_pts], True, (255, 200, 0), 2)

                        cv2.addWeighted(overlay, 0.25, annotated_frame, 0.75, 0, annotated_frame)

                        if last_detections is not None:
                            for i in range(len(last_detections)):
                                bbox = last_detections.xyxy[i]
                                x1, y1, x2, y2 = (bbox * scale_ratio).astype(int)
                                class_id = int(last_detections.class_id[i])
                                label = CLASS_NAMES_DICT.get(class_id, f"class_{class_id}")
                                color = (255, 170, 0) if class_id == 0 else (0, 255, 0)
                                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
                                cv2.putText(
                                    annotated_frame,
                                    label,
                                    (x1, max(18, y1 - 6)),
                                    cv2.FONT_HERSHEY_SIMPLEX,
                                    0.5,
                                    color,
                                    2,
                                )

                        cv2.rectangle(annotated_frame, (0, 0), (int(w * display_scale), 100), (0, 0, 0), -1)
                        cv2.putText(annotated_frame, f"PEOPLE: {last_stats['person_count']}  VEHICLES: {last_stats['current_vehicles']}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                        cv2.putText(annotated_frame, f"TRAFFIC: {last_stats['channel_stats']['traffic_level']} ({last_stats['congestion_index']}%)", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

                    ret, buffer = cv2.imencode('.jpg', annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, 72])
                    if ret:
                        async with self.frame_condition:
                            self.latest_frame = buffer.tobytes()
                            self.frame_version += 1
                            self.frame_condition.notify_all()

                    elapsed = time.time() - start_time
                    self.processing_latency = elapsed * 1000
                    await asyncio.sleep(max(0.005, frame_delay - elapsed))

                await asyncio.to_thread(cap.release)
                if not is_live_source:
                    break
                await asyncio.sleep(2)
        finally:
            if processing_task and not processing_task.done():
                processing_task.cancel()
            self.running = False
            async with self.frame_condition:
                self.frame_condition.notify_all()
