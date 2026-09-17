import os
# Set User-Agent for OpenCV's FFmpeg backend so YouTube doesn't block cv2.VideoCapture(url)
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "user_agent;Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from .database import engine, Base
from .routers import channels, zones, streams, analytics, public, analytics_v2, auth
from .auth import get_password_hash
from . import models

# Create all tables (including new Channel, Zone, ZoneAnalytics, SystemLog tables)
Base.metadata.create_all(bind=engine)

# Seed default admin user
from .database import SessionLocal
db = SessionLocal()
admin_user = db.query(models.User).filter(models.User.username == "admin").first()
if not admin_user:
    db.add(models.User(username="admin", hashed_password=get_password_hash("admin")))
else:
    # Force reset password to 'admin' in case of previous broken hashes
    admin_user.hashed_password = get_password_hash("admin")
db.commit()
db.close()

app = FastAPI(title="AI Video Intelligence & Real-Time Streaming Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# New Phase 1, 3, 5, 6 routers
app.include_router(auth.router)               # /api/auth
app.include_router(channels.router)           # /api/channels
app.include_router(channels.cameras_router)    # /api/cameras (backward compat)
app.include_router(zones.router)              # /api/channels/{id}/zones
app.include_router(public.router)             # /api/public/{slug}
app.include_router(analytics_v2.router)       # /api/analytics_v2

# Legacy routers (still needed for video streaming & analytics)
app.include_router(streams.router)             # /api/streams
app.include_router(streams.public_router)      # /live/{public_id}
app.include_router(analytics.router)           # /api/analytics

@app.get("/")
def root():
    index_file = Path("frontend_dist/index.html")
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "AI Video Intelligence API is running"}

frontend_assets = Path("frontend_dist/assets")
if frontend_assets.is_dir():
    app.mount("/assets", StaticFiles(directory=frontend_assets), name="frontend-assets")

@app.get("/{frontend_path:path}", include_in_schema=False)
def frontend_fallback(frontend_path: str):
    """Serve built frontend files and fall back to the SPA entry point."""
    frontend_root = Path("frontend_dist").resolve()
    requested_file = (frontend_root / frontend_path).resolve()
    if frontend_root in requested_file.parents and requested_file.is_file():
        return FileResponse(requested_file)
    index_file = frontend_root / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    raise HTTPException(status_code=404, detail="Frontend is not built")
