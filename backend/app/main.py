from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import shutil
from sqlalchemy import inspect, text
from uuid import uuid4
from .database import engine, Base, SessionLocal
from . import models
from .routers import cameras, streams, analytics

# Create tables
Base.metadata.create_all(bind=engine)

# create_all does not add columns to an existing SQLite database. Keep this
# additive migration here so old Railway/local volumes remain compatible.
with engine.begin() as connection:
    camera_columns = {column["name"] for column in inspect(connection).get_columns("cameras")}
    for column_name in ("embed_url", "embed_mode", "public_id"):
        if column_name not in camera_columns:
            connection.execute(text(f"ALTER TABLE cameras ADD COLUMN {column_name} VARCHAR"))
    missing_public_ids = connection.execute(
        text("SELECT id FROM cameras WHERE public_id IS NULL OR public_id = ''")
    ).fetchall()
    for row in missing_public_ids:
        connection.execute(
            text("UPDATE cameras SET public_id = :public_id WHERE id = :camera_id"),
            {"public_id": uuid4().hex, "camera_id": row.id},
        )
    connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_cameras_public_id ON cameras (public_id)"))

# Keep uploaded files on the same persistent volume as the production database.
# A local-snapshot deploy may still contain legacy /app/uploads files, so move a
# copy into the volume and update their database paths once.
with SessionLocal() as session:
    for camera in session.query(models.Camera).filter(models.Camera.type == models.CameraType.file).all():
        if not camera.url:
            continue
        source = Path(camera.url)
        if not source.is_absolute():
            source = (Path.cwd() / source).resolve()
        target = (streams.UPLOAD_DIR / source.name).resolve()
        if source != target and source.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                shutil.copy2(source, target)
            camera.url = str(target)
    session.commit()

app = FastAPI(title="Traffic Detection & Analytics System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For development
    allow_credentials=False, # Must be false if origins is *
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cameras.router)
app.include_router(streams.router)
app.include_router(streams.public_router)
app.include_router(analytics.router)

@app.get("/")
def root():
    index_file = Path("frontend_dist/index.html")
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "Traffic Detection API is running"}

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
