import numpy as np
import cv2
import supervision as sv
from typing import Dict, Any

class TrafficAnalyzer:
    def __init__(self):
        self.history = {} # store object histories for speed/stop calculation
        
    def calculate_traffic(self, detections: sv.Detections, track_history: Dict[int, list], density_index: int) -> Dict[str, Any]:
        """
        Returns a dict with:
        - traffic_index: int (0-100)
        - traffic_level: str ("NORMAL", "LOW", "MEDIUM", "HIGH")
        - avg_speed: float
        - stopped_count: int
        - details: dict of raw factors
        
        Levels:
          0-25  -> NORMAL
          26-50 -> LOW
          51-75 -> MEDIUM
          76-100-> HIGH
          
        Formula:
        traffic_index = weighted_avg(
            density_factor    * 0.40,  # use density_index / 100
            stopped_ratio     * 0.40,  # % of tracked vehicles with speed ~0
            slow_ratio        * 0.20   # % of tracked vehicles moving slowly
        )
        """
        speeds = []
        stopped_count = 0
        slow_count = 0
        total_tracked = 0

        # Define thresholds for speeds (pixels per frame)
        # Note: These values should ideally be calibrated based on resolution and framerate
        STOP_THRESHOLD = 2.0
        SLOW_THRESHOLD = 10.0
        
        for track_id, points in track_history.items():
            if len(points) >= 2:
                # Calculate speed using Euclidean distance between last two points
                p1, p2 = np.array(points[-2]), np.array(points[-1])
                speed = np.linalg.norm(p2 - p1)
                speeds.append(speed)
                total_tracked += 1
                
                if speed <= STOP_THRESHOLD:
                    stopped_count += 1
                elif speed <= SLOW_THRESHOLD:
                    slow_count += 1
                    
        avg_speed = float(np.mean(speeds)) if speeds else 0.0
        
        density_factor = min(1.0, max(0.0, density_index / 100.0))
        
        stopped_ratio = (stopped_count / total_tracked) if total_tracked > 0 else 0.0
        slow_ratio = (slow_count / total_tracked) if total_tracked > 0 else 0.0
        
        traffic_value = (density_factor * 0.40) + (stopped_ratio * 0.40) + (slow_ratio * 0.20)
        traffic_index = int(np.clip(traffic_value * 100, 0, 100))
        
        if traffic_index <= 25:
            traffic_level = "NORMAL"
        elif traffic_index <= 50:
            traffic_level = "LOW"
        elif traffic_index <= 75:
            traffic_level = "MEDIUM"
        else:
            traffic_level = "HIGH"
            
        return {
            "traffic_index": traffic_index,
            "traffic_level": traffic_level,
            "avg_speed": avg_speed,
            "stopped_count": stopped_count,
            "details": {
                "density_factor": float(density_factor),
                "stopped_ratio": float(stopped_ratio),
                "slow_ratio": float(slow_ratio)
            }
        }
