FROM node:20-alpine AS frontend-builder

WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM node:22-bookworm-slim AS node-runtime

FROM python:3.10-slim

# Install system dependencies for OpenCV and FFmpeg.
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# yt-dlp's EJS challenge solver requires Node 22+.
COPY --from=node-runtime /usr/local/bin/node /usr/local/bin/node

WORKDIR /app

# Copy the backend requirements and install
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire backend directory to the container
COPY backend/ .
COPY --from=frontend-builder /frontend/dist ./frontend_dist

# Ensure uploads and database have correct permissions
RUN mkdir -p uploads && chmod 777 uploads
RUN touch detec.db && chmod 777 detec.db
RUN mkdir -p /data && chmod 777 /data

# Expose port (default 8000, but can be overridden by PORT)
EXPOSE 8000

# Use shell form for CMD so environment variables like $PORT are expanded
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
