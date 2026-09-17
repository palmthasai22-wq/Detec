import subprocess
import os
import asyncio
from datetime import datetime

class MediaMTXStreamPusher:
    def __init__(self, channel_slug: str, width: int = 1280, height: int = 720, fps: int = 25):
        self.channel_slug = channel_slug
        self.width = width
        self.height = height
        self.fps = fps
        self.process = None
        self.mediamtx_url = os.getenv("MEDIAMTX_URL", "rtsp://localhost:8554")
        self.stream_url = f"{self.mediamtx_url}/{self.channel_slug}"

    def start(self):
        if self.process:
            self.stop()
            
        command = [
            'ffmpeg',
            '-y',
            '-f', 'rawvideo',
            '-vcodec', 'rawvideo',
            '-pix_fmt', 'bgr24',
            '-s', f"{self.width}x{self.height}",
            '-r', str(self.fps),
            '-i', '-',
            '-c:v', 'libx264',
            '-preset', 'ultrafast',
            '-tune', 'zerolatency',
            '-pix_fmt', 'yuv420p',
            '-f', 'rtsp',
            '-rtsp_transport', 'tcp',
            self.stream_url
        ]
        
        self.process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print(f"[MediaMTX] Started pushing to {self.stream_url}")

    def push_frame(self, frame):
        """Pushes a raw BGR numpy array to the FFmpeg pipe."""
        if not self.process or self.process.poll() is not None:
            # Restart if crashed
            self.start()
            
        if self.process and self.process.stdin:
            try:
                self.process.stdin.write(frame.tobytes())
                self.process.stdin.flush()
            except Exception as e:
                print(f"[MediaMTX] Error writing to FFmpeg pipe: {e}")
                self.stop()

    def stop(self):
        if self.process:
            if self.process.stdin:
                self.process.stdin.close()
            self.process.terminate()
            self.process.wait()
            self.process = None
        print(f"[MediaMTX] Stopped pushing to {self.stream_url}")
