# Scalability Guide

The AI Video Intelligence & Real-Time Public Streaming Platform is designed to scale horizontally across multiple instances to handle 1,000+ concurrent viewers and numerous camera channels.

## 1. Multi-Container Deployment

In production, the system is split into three core layers:

1. **AI Processing Node (FastAPI)**: Handles video ingestion, decoding, YOLO inference, ByteTrack, and Zone analytics. This is CPU/GPU intensive.
2. **Database (TimescaleDB/PostgreSQL)**: Handles relational data (channels, users) and time-series data (analytics).
3. **Streaming Server (MediaMTX)**: Receives H.264 video streams from the AI nodes via FFmpeg and muxes them into HLS and WebRTC streams for clients.

## 2. Scaling the AI Processing Layer

If you have more cameras than a single server can handle:
- **GPU Acceleration**: Ensure `ultralytics` uses a CUDA-enabled PyTorch build.
- **Horizontal Pod Autoscaling**: You can deploy multiple instances of the backend. To do this, you must introduce a message broker (e.g., Redis) or configure the StreamManager to only process a subset of channels per node. Currently, StreamManager attempts to process all active channels. A simple shard key (`hash(channel_id) % num_nodes`) can distribute the workload.

## 3. Scaling the Streaming Layer (MediaMTX)

MediaMTX can comfortably handle hundreds of WebRTC connections. However, for 1,000+ concurrent public viewers, **HLS + CDN** is required.
- Enable `hls: true` in `mediamtx.yml`.
- Place a CDN (like Cloudflare or AWS CloudFront) in front of the MediaMTX `:8888` port.
- The CDN will cache the `.m3u8` playlists (cache for 1s) and `.ts` segments (cache for 1 year), reducing the load on your server to near zero regardless of viewer count.

## 4. Scaling the Database Layer

- TimescaleDB automatically partitions time-series data into chunks.
- Continuous aggregates (`zone_analytics` hourly/daily rollups) ensure historical queries remain lightning-fast even with millions of rows.
- The `resource_monitor.py` task checks system health to prevent Out-Of-Memory (OOM) crashes by logging GPU/RAM utilization.
