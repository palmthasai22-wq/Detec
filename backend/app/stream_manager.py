import asyncio
from typing import Dict
from .video_processor import VideoProcessor
from .routers.analytics import broadcast_analytics
from .database import SessionLocal
from .models import TrafficLog
from datetime import datetime

class StreamManager:
    def __init__(self):
        self.active_streams: Dict[int, VideoProcessor] = {}
        self.stats_queues: Dict[int, asyncio.Queue] = {}
        self.db_tasks: Dict[int, asyncio.Task] = {}
        self.processing_tasks: Dict[int, asyncio.Task] = {}

    def get_or_create_stream(self, camera_id: int, source_url: str, cam_type: str, config: dict):
        processing_task = self.processing_tasks.get(camera_id)
        if camera_id not in self.active_streams or processing_task is None or processing_task.done():
            old_db_task = self.db_tasks.pop(camera_id, None)
            if old_db_task:
                old_db_task.cancel()
            processor = VideoProcessor(camera_id, source_url, cam_type, config)
            processor.running = True
            self.active_streams[camera_id] = processor
            self.stats_queues[camera_id] = asyncio.Queue(maxsize=10)
            
            # Start background task to broadcast and save stats
            self.db_tasks[camera_id] = asyncio.create_task(self._process_stats(camera_id))
            self.processing_tasks[camera_id] = asyncio.create_task(
                processor.run(self.stats_queues[camera_id])
            )
            
        return self.active_streams[camera_id], self.stats_queues[camera_id]
        
    async def _process_stats(self, camera_id: int):
        queue = self.stats_queues[camera_id]
        last_log_time = datetime.utcnow()
        
        while True:
            stats = await queue.get()
            
            # Broadcast to WebSocket
            await broadcast_analytics(stats)
            
            # Save to DB every 5 seconds
            now = datetime.utcnow()
            if (now - last_log_time).total_seconds() >= 5.0:
                db = SessionLocal()
                try:
                    log = TrafficLog(
                        camera_id=camera_id,
                        person_count=stats.get("person_count", 0),
                        car_count=stats.get("car_count", 0),
                        motorcycle_count=stats.get("motorcycle_count", 0),
                        truck_count=stats.get("truck_count", 0),
                        density_level=stats["density"]
                    )
                    db.add(log)
                    db.commit()
                finally:
                    db.close()
                last_log_time = now

    def stop_stream(self, camera_id: int):
        if camera_id in self.active_streams:
            self.active_streams[camera_id].running = False
            del self.active_streams[camera_id]
        if camera_id in self.db_tasks:
            self.db_tasks[camera_id].cancel()
            del self.db_tasks[camera_id]
        if camera_id in self.processing_tasks:
            self.processing_tasks[camera_id].cancel()
            del self.processing_tasks[camera_id]
        if camera_id in self.stats_queues:
            del self.stats_queues[camera_id]

stream_manager = StreamManager()
