import asyncio
from typing import Dict
from sqlalchemy.orm import Session
from datetime import datetime

from .video_processor import VideoProcessor
from .routers.analytics import broadcast_analytics
from .database import SessionLocal
from . import models

class StreamManager:
    def __init__(self):
        self.active_streams: Dict[int, VideoProcessor] = {}
        self.stats_queues: Dict[int, asyncio.Queue] = {}
        self.db_tasks: Dict[int, asyncio.Task] = {}
        self.processing_tasks: Dict[int, asyncio.Task] = {}

    def get_stream_status(self, channel_id: int) -> dict:
        if channel_id in self.active_streams:
            vp = self.active_streams[channel_id]
            return {
                "is_active": vp.running,
                "fps": getattr(vp, 'current_fps', 0),
                "latency": getattr(vp, 'processing_latency', 0),
                "viewer_count": vp.viewer_count
            }
        return None

    def is_active(self, channel_id: int) -> bool:
        return channel_id in self.active_streams and self.active_streams[channel_id].running

    def get_or_create_stream(self, channel: models.Channel, zones: list[models.Zone]):
        channel_id = channel.id
        processing_task = self.processing_tasks.get(channel_id)
        
        if channel_id not in self.active_streams or processing_task is None or processing_task.done():
            # Clean up old tasks if they exist
            old_db_task = self.db_tasks.pop(channel_id, None)
            if old_db_task:
                old_db_task.cancel()
                
            # Initialize new processor with full channel config
            processor = VideoProcessor(channel, zones)
            processor.running = True
            
            self.active_streams[channel_id] = processor
            self.stats_queues[channel_id] = asyncio.Queue(maxsize=10)
            
            # Start background tasks
            self.db_tasks[channel_id] = asyncio.create_task(self._process_stats(channel_id))
            self.processing_tasks[channel_id] = asyncio.create_task(
                processor.run(self.stats_queues[channel_id])
            )
            
        return self.active_streams[channel_id], self.stats_queues[channel_id]
        
    def update_stream_config(self, channel_id: int, update_data: dict):
        if channel_id in self.active_streams:
            vp = self.active_streams[channel_id]
            # Live-update confidence or classes if implemented in VideoProcessor
            if "confidence_threshold" in update_data:
                vp.conf_thresh = update_data["confidence_threshold"]
            if "object_classes" in update_data:
                # Person detection is always enabled alongside road vehicles.
                vp.target_classes = sorted(set(update_data["object_classes"] or [0,1,2,3,5,7]) | {0})
        
    async def _process_stats(self, channel_id: int):
        queue = self.stats_queues[channel_id]
        last_log_time = datetime.utcnow()
        
        while True:
            try:
                stats = await queue.get()
                
                # Broadcast real-time stats to WebSocket
                await broadcast_analytics(stats)
                
                # Save to Time-Series DB (ZoneAnalytics) every 5 seconds
                now = datetime.utcnow()
                if (now - last_log_time).total_seconds() >= 5.0:
                    db = SessionLocal()
                    try:
                        # Find the channel-level stats (zone_id = None)
                        # We extract it from the aggregated stats dictionary
                        channel_stats = stats.get("channel_stats", {})
                        
                        if channel_stats:
                            # Save backward-compatible TrafficLog
                            log = models.TrafficLog(
                                camera_id=channel_id,
                                object_type="aggregate",
                                count=channel_stats.get("total_objects", 0),
                                direction="none"
                            )
                            db.add(log)
                            
                            # Save new ZoneAnalytics for channel
                            za = models.ZoneAnalytics(
                                channel_id=channel_id,
                                zone_id=None,
                                object_counts=channel_stats.get("object_counts", {}),
                                total_objects=channel_stats.get("total_objects", 0),
                                density_index=channel_stats.get("density_index", 0),
                                traffic_index=channel_stats.get("traffic_index", 0),
                                traffic_level=channel_stats.get("traffic_level", "NORMAL")
                            )
                            db.add(za)
                            
                        # Save zone-specific analytics
                        zone_stats_list = stats.get("zone_stats", [])
                        for z_stat in zone_stats_list:
                            za_zone = models.ZoneAnalytics(
                                channel_id=channel_id,
                                zone_id=z_stat.get("zone_id"),
                                object_counts=z_stat.get("object_counts", {}),
                                total_objects=z_stat.get("total_objects", 0),
                                density_index=z_stat.get("density_index", 0),
                                traffic_index=z_stat.get("traffic_index", 0),
                                traffic_level=z_stat.get("traffic_level", "NORMAL")
                            )
                            db.add(za_zone)
                            
                        db.commit()
                    except Exception as e:
                        print(f"Error saving analytics for channel {channel_id}: {e}")
                    finally:
                        db.close()
                        
                    last_log_time = now
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in _process_stats for channel {channel_id}: {e}")

    def stop_stream(self, channel_id: int):
        if channel_id in self.active_streams:
            self.active_streams[channel_id].running = False
            del self.active_streams[channel_id]
        if channel_id in self.db_tasks:
            self.db_tasks[channel_id].cancel()
            del self.db_tasks[channel_id]
        if channel_id in self.processing_tasks:
            self.processing_tasks[channel_id].cancel()
            del self.processing_tasks[channel_id]
        if channel_id in self.stats_queues:
            del self.stats_queues[channel_id]

stream_manager = StreamManager()
