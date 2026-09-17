import cv2
import numpy as np
import asyncio
import requests
import base64
import math
import os
from datetime import datetime, timezone
from collections import deque
from ultralytics import YOLO
import supervision as sv

try:
    model = YOLO('yolo26m.pt')
    MODEL_NAME = "YOLO26m"
except Exception:
    model = YOLO('yolo11m.pt')
    MODEL_NAME = "YOLO11m"

print(f"[AI Engine] Loaded standard model: {MODEL_NAME}")

TARGET_CLASSES = [1, 2, 3, 5, 7]

class VideoProcessor:
    def __init__(self, camera_id: int, source_url: str, cam_type: str, config: dict):
        self.camera_id = camera_id
        self.source_url = source_url
        self.cam_type = cam_type
        self.config = config
        self.running = False
        self.latest_frame = None
        self.frame_version = 0
        self.frame_condition = asyncio.Condition()
        self.viewer_lock = asyncio.Lock()
        self.viewer_count = 0
        self.max_viewers = max(1, int(os.getenv("DETEC_MAX_VIEWERS_PER_CAMERA", "30")))
        
        self.tracker = sv.ByteTrack()
        self.track_history = {} 
        
        self.engine = config.get("engine", "yolo") if config else "yolo"
        self.latest_stats = None
        self.rf_model_id = config.get("roboflow_model_id") if config else None
        self.rf_api_key = config.get("roboflow_api_key") if config else None
        
        if self.engine == "roboflow":
            print(f"[AI Engine] Using Roboflow Cloud API for Model: {self.rf_model_id}")
        
        self.line_zone = None
        self.line_zone_annotator = None
        
        if self.config and self.config.get("counting_line"):
            line_coords = self.config["counting_line"]
            if len(line_coords) == 2:
                start = sv.Point(x=line_coords[0][0], y=line_coords[0][1])
                end = sv.Point(x=line_coords[1][0], y=line_coords[1][1])
                if start.x == end.x and start.y == end.y:
                    end = sv.Point(x=end.x + 10, y=end.y + 10)
                self.line_zone = sv.LineZone(start=start, end=end)
                self.line_zone_annotator = sv.LineZoneAnnotator()

        if self.config and self.config.get("wait_zone"):
            self.wait_zone_polygon = np.array(self.config["wait_zone"], dtype=np.float32)
        else:
            self.wait_zone_polygon = None

    def process_frame_raw(self, frame):
        conf_thresh = self.config.get("confidence_threshold", 0.15) if self.config else 0.15
        infer_size = 1536 if self.cam_type == "file" else 1280
        
        if self.engine == "roboflow" and self.rf_model_id and self.rf_api_key:
            retval, buffer = cv2.imencode('.jpg', frame)
            img_str = base64.b64encode(buffer).decode("ascii")
            url = f"https://detect.roboflow.com/{self.rf_model_id}?api_key={self.rf_api_key}&confidence={int(conf_thresh*100)}"
            try:
                resp = requests.post(url, data=img_str, headers={"Content-Type": "application/x-www-form-urlencoded"})
                data = resp.json()
                xyxy, confidences, class_ids, roboflow_classes = [], [], [], []
                if "predictions" in data:
                    for p in data["predictions"]:
                        x, y, w, h = p["x"], p["y"], p["width"], p["height"]
                        xyxy.append([x - w/2, y - h/2, x + w/2, y + h/2])
                        confidences.append(p["confidence"])
                        class_ids.append(p.get("class_id", 0))
                        roboflow_classes.append(p["class"])
                
                if len(xyxy) > 0:
                    raw_detections = sv.Detections(
                        xyxy=np.array(xyxy), confidence=np.array(confidences), class_id=np.array(class_ids)
                    )
                    raw_detections.data = {"class_name": roboflow_classes}
                else:
                    raw_detections = sv.Detections.empty()
            except Exception as e:
                print(f"Roboflow API error: {e}")
                raw_detections = sv.Detections.empty()
        else:
            results = model(frame, verbose=False, classes=TARGET_CLASSES, 
                           conf=conf_thresh, imgsz=infer_size, iou=0.45, max_det=1000)[0]
            raw_detections = sv.Detections.from_ultralytics(results)
            
        tracked_detections = self.tracker.update_with_detections(raw_detections)
        
        current_ids = []
        total_displacement = 0
        valid_speed_samples = 0
        stopped_inside = 0
        stopped_outside = 0
        
        for i in range(len(tracked_detections)):
            tracker_id = tracked_detections.tracker_id[i]
            bbox = tracked_detections.xyxy[i]
            cx, cy = (bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2
            
            current_ids.append(tracker_id)
            if tracker_id not in self.track_history:
                self.track_history[tracker_id] = deque(maxlen=20)
                
            history = self.track_history[tracker_id]
            history.append((cx, cy))
            
            if len(history) >= 5:
                start_cx, start_cy = history[0]
                displacement = math.hypot(cx - start_cx, cy - start_cy)
                total_displacement += displacement
                valid_speed_samples += 1
                
                if displacement < 15: # Slow or stopped
                    if self.wait_zone_polygon is not None:
                        # scale normalized coords to ai_frame
                        h, w = frame.shape[:2]
                        scaled_poly = (self.wait_zone_polygon * [w, h]).astype(np.int32)
                        if cv2.pointPolygonTest(scaled_poly, (cx, cy), False) >= 0:
                            stopped_inside += 1
                        else:
                            stopped_outside += 1
                    else:
                        stopped_outside += 1

        self.track_history = {k: v for k, v in self.track_history.items() if k in current_ids}
        avg_speed = total_displacement / valid_speed_samples if valid_speed_samples > 0 else 0
        total_vehicles = len(raw_detections)
        
        # Macro State Evaluation with Smart ROI (Wait Zone)
        if total_vehicles == 0:
            macro_state = "CLEAR"
            congestion_index = 0
        elif avg_speed > 25:
            macro_state = "FLOWING"
            congestion_index = min(30, total_vehicles * 2)
        elif avg_speed > 8:
            macro_state = "SLOWING"
            congestion_index = min(70, 40 + total_vehicles * 2)
        else:
            if self.wait_zone_polygon is not None and stopped_inside >= stopped_outside and stopped_inside > 0:
                macro_state = "WAITING"
                congestion_index = 40 # Keeps the status out of the RED zone
            else:
                if total_vehicles > 3:
                    macro_state = "JAMMED"
                    congestion_index = min(100, 75 + total_vehicles * 3)
                else:
                    macro_state = "NORMAL"
                    congestion_index = 10

        if macro_state == "WAITING":
            density_level = "blue"
        elif macro_state in ["CLEAR", "FLOWING", "NORMAL"]:
            density_level = "green"
        elif macro_state == "SLOWING":
            density_level = "yellow"
        else:
            density_level = "red"
        
        in_count, out_count = 0, 0
        if self.line_zone:
            self.line_zone.trigger(detections=tracked_detections)
            in_count = self.line_zone.in_count
            out_count = self.line_zone.out_count
            
        stats = {
            "camera_id": self.camera_id,
            "density": density_level,
            "congestion_index": congestion_index,
            "average_speed": round(float(avg_speed), 2),
            "speed_unit": "px/window",
            "traffic_state": macro_state,
            "current_vehicles": total_vehicles,
            "person_count": 0,
            "car_count": total_vehicles,
            "motorcycle_count": 0,
            "truck_count": 0,
            "in_count": in_count,
            "out_count": out_count,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        print(f"[AI Macro] State: {macro_state} | Speed: {avg_speed:.1f} | Jam Index: {congestion_index}%")
        boxes = tracked_detections.xyxy.tolist() if len(tracked_detections) else []
        return macro_state, avg_speed, self.track_history.copy(), boxes, stats

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
        """Fan out the already encoded latest frame without rerunning AI per viewer."""
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

    async def run(self, broadcast_queue: asyncio.Queue):
        cap = cv2.VideoCapture(self.source_url)
        self.running = True
        
        last_macro_state = "CLEAR"
        last_avg_speed = 0.0
        last_track_trails = {}
        last_boxes = []
        last_stats = {"congestion_index": 0, "current_vehicles": 0}
        
        processing_task = None
        
        while self.running and cap.isOpened():
            # Run cap.read() in a thread so it doesn't block the async event loop (Fixes stuttering)
            success, raw_frame = await asyncio.to_thread(cap.read)
            if not success:
                if self.cam_type == "file":
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                break
                
            h, w = raw_frame.shape[:2]
            
            ai_max = 1280 if self.cam_type == "file" else 1024 # Reduced AI size slightly for speed
            ai_scale = 1.0
            if max(h, w) > ai_max:
                ai_scale = ai_max / max(h, w)
                ai_frame = cv2.resize(raw_frame, (int(w * ai_scale), int(h * ai_scale)))
            else:
                ai_frame = raw_frame.copy()

            # Reduce display resolution to 800px (fast JPEG encoding & drawing, reduces UI lag)
            display_max = 800 
            display_scale = 1.0
            if max(h, w) > display_max:
                display_scale = display_max / max(h, w)
                display_frame = cv2.resize(raw_frame, (int(w * display_scale), int(h * display_scale)))
            else:
                display_frame = raw_frame.copy()
            
            if processing_task is None or processing_task.done():
                if processing_task and processing_task.done():
                    try:
                        last_macro_state, last_avg_speed, last_track_trails, last_boxes, stats = processing_task.result()
                        last_stats = stats
                        self.latest_stats = stats
                        try:
                            broadcast_queue.put_nowait(stats)
                        except asyncio.QueueFull:
                            pass
                    except Exception as e:
                        print("YOLO Inference Error:", e)
                
                processing_task = asyncio.create_task(asyncio.to_thread(self.process_frame_raw, ai_frame.copy()))
            
            annotated_frame = display_frame.copy()
            scale_ratio = display_scale / ai_scale
            
            overlay = annotated_frame.copy()
            
            if last_macro_state == "JAMMED":
                color_bgr = (0, 0, 255) # Red
            elif last_macro_state == "WAITING":
                color_bgr = (255, 150, 0) # Cyan/Blue for Waiting Light
            elif last_macro_state == "SLOWING":
                color_bgr = (0, 255, 255) # Yellow
            else:
                color_bgr = (0, 255, 0) # Green

            cv2.rectangle(overlay, (0, 0), (w, 125), color_bgr, -1)
            cv2.rectangle(overlay, (0, 0), (w, h), color_bgr, 15)
            
            # Draw Wait Zone
            if self.wait_zone_polygon is not None:
                scaled_pts = (self.wait_zone_polygon * [w, h]).astype(np.int32)
                cv2.fillPoly(overlay, [scaled_pts], (255, 100, 0)) # Translucent blue zone
                cv2.polylines(annotated_frame, [scaled_pts], True, (255, 200, 0), 2)
            
            cv2.addWeighted(overlay, 0.25, annotated_frame, 0.75, 0, annotated_frame)
            
            for track_id, history in last_track_trails.items():
                if len(history) > 1:
                    pts = np.array([(int(x * scale_ratio), int(y * scale_ratio)) for x, y in history], np.int32)
                    pts = pts.reshape((-1, 1, 2))
                    cv2.polylines(annotated_frame, [pts], False, color_bgr, 3)
                    
                    cx, cy = int(history[-1][0] * scale_ratio), int(history[-1][1] * scale_ratio)
                    cv2.circle(annotated_frame, (cx, cy), 6, (255, 255, 255), -1)
                    cv2.circle(annotated_frame, (cx, cy), 8, color_bgr, 2)

            for x1, y1, x2, y2 in last_boxes:
                cv2.rectangle(
                    annotated_frame,
                    (int(x1 * scale_ratio), int(y1 * scale_ratio)),
                    (int(x2 * scale_ratio), int(y2 * scale_ratio)),
                    color_bgr,
                    2,
                )
            
            cv2.putText(annotated_frame, f"TRAFFIC FLOW: {last_macro_state}", (30, 38), cv2.FONT_HERSHEY_DUPLEX, 1.0, (255, 255, 255), 3)
            cv2.putText(annotated_frame, f"JAM INDEX: {last_stats['congestion_index']}% | VEHICLES: {last_stats['current_vehicles']}", (30, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            cv2.putText(annotated_frame, f"AVG SPEED: {last_avg_speed:.1f} px/window", (30, 106), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (240, 240, 240), 2)
            
            if self.config and self.config.get("counting_line"):
                line_coords = self.config["counting_line"]
                if len(line_coords) == 2:
                    lx1 = int(line_coords[0][0] * scale_ratio)
                    ly1 = int(line_coords[0][1] * scale_ratio)
                    lx2 = int(line_coords[1][0] * scale_ratio)
                    ly2 = int(line_coords[1][1] * scale_ratio)
                    cv2.line(annotated_frame, (lx1, ly1), (lx2, ly2), (255, 0, 255), 4)
            
            # Optimize JPEG encoding (Quality 60 is plenty for dashboard, drastically reduces bandwidth & lag)
            ret, buffer = cv2.imencode('.jpg', annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
            if not ret:
                continue
            frame_bytes = buffer.tobytes()
            async with self.frame_condition:
                self.latest_frame = frame_bytes
                self.frame_version += 1
                self.frame_condition.notify_all()
            
            if self.cam_type == "file":
                await asyncio.sleep(0.04) # Cap at 25fps for smoother web streaming
            else:
                await asyncio.sleep(0.005) # Yield event loop slightly more often
                
        cap.release()
        self.running = False
        async with self.frame_condition:
            self.frame_condition.notify_all()
