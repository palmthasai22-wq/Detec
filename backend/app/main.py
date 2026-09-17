from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .routers import cameras, streams, analytics

# Create tables
Base.metadata.create_all(bind=engine)

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
app.include_router(analytics.router)

@app.get("/")
def root():
    return {"message": "Traffic Detection API is running"}
