import numpy as np
import cv2
import supervision as sv
from typing import Dict, Any

class DensityAnalyzer:
    def __init__(self, zone_polygon: np.ndarray, zone_capacity: int = 100):
        # zone_polygon: numpy array of shape (N, 2)
        # zone_capacity: max number of objects the zone can comfortably hold
        self.zone_polygon = zone_polygon
        self.zone_capacity = max(1, zone_capacity)
        self.zone_area = cv2.contourArea(self.zone_polygon) if len(self.zone_polygon) >= 3 else 1.0

    def calculate_density(self, detections: sv.Detections) -> Dict[str, Any]:
        """
        Returns a dict with:
        - density_index: int (0-100)
        - details: dict of raw factors
        
        Formula:
        density_index = weighted_avg(
            object_count_ratio    * 0.35,   # count / zone capacity
            occupancy_ratio       * 0.35,   # bbox area / zone area
            spatial_spread        * 0.30    # standard deviation of centers normalized
        )
        """
        if len(detections) == 0:
            return {
                "density_index": 0,
                "details": {
                    "object_count_ratio": 0.0,
                    "occupancy_ratio": 0.0,
                    "spatial_spread": 0.0
                }
            }

        count = len(detections)
        object_count_ratio = min(1.0, count / self.zone_capacity)

        total_bbox_area = 0.0
        centers = []
        for bbox in detections.xyxy:
            x1, y1, x2, y2 = bbox
            area = (x2 - x1) * (y2 - y1)
            total_bbox_area += area
            centers.append([(x1 + x2) / 2, (y1 + y2) / 2])
        
        occupancy_ratio = min(1.0, total_bbox_area / max(1.0, self.zone_area))
        
        if count > 1:
            centers_np = np.array(centers)
            std_dev = np.std(centers_np, axis=0)
            avg_std = np.mean(std_dev)
            
            # Normalize spatial spread: max possible spread approx sqrt(zone_area)/2
            max_spread = np.sqrt(max(1.0, self.zone_area)) / 2
            spatial_spread = min(1.0, avg_std / max(1.0, max_spread))
        else:
            spatial_spread = 0.0

        density_value = (object_count_ratio * 0.35) + (occupancy_ratio * 0.35) + (spatial_spread * 0.30)
        density_index = int(np.clip(density_value * 100, 0, 100))

        return {
            "density_index": density_index,
            "details": {
                "object_count_ratio": float(object_count_ratio),
                "occupancy_ratio": float(occupancy_ratio),
                "spatial_spread": float(spatial_spread)
            }
        }
