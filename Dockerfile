FROM python:3.10-slim

# Install system dependencies for OpenCV and ByteTrack
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1-mesa-glx \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set up a new user named "user" with user ID 1000 for Hugging Face
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

# Copy the backend requirements and install
COPY --chown=user:user backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire backend directory to the container
COPY --chown=user:user backend/ .

# Ensure uploads and database have correct permissions
RUN mkdir -p uploads && chmod 777 uploads
RUN touch detec.db && chmod 777 detec.db

# Expose port (default 8000, but can be overridden by PORT)
EXPOSE 8000

# Use shell form for CMD so environment variables like $PORT are expanded
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
