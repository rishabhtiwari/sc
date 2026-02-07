# Export Generator Job Service

## Overview

The Export Generator Job Service is a microservice that handles project export generation for the Design Editor. It follows the BaseJob framework pattern used by other job services in the system (video-generator, voice-generator, etc.).

## Architecture

This service extends the `BaseJob` framework and provides:

- **On-demand export processing** (no scheduled runs)
- **Multi-tenant support** (per-customer job execution)
- **Job tracking** via JobInstanceService in MongoDB
- **Multiple export formats**: MP4, MP3, JSON
- **Video library integration** (MP4 exports automatically saved)
- **Project metadata updates** (export history stored in projects)

## Features

### Export Formats

1. **MP4 Video Export**
   - Renders slides to frame sequences
   - Creates video from frames using FFmpeg
   - Mixes audio tracks if requested
   - Supports multiple quality settings (720p, 1080p, 1440p, 4K)
   - Supports multiple FPS settings (24, 30, 60)
   - Automatically saves to video library

2. **MP3 Audio Export**
   - Extracts and mixes all audio tracks
   - Encodes to MP3 format
   - Supports custom bitrate settings

3. **JSON Data Export**
   - Exports complete project data as JSON
   - Useful for backups and data portability

### Video Rendering Pipeline

1. **Slide Rendering**
   - Renders each slide to an image using PIL/Pillow
   - Supports backgrounds (solid, gradient, image)
   - Renders elements (text, images, shapes)
   - Respects z-index ordering

2. **Frame Generation**
   - Generates frame sequences based on slide duration and FPS
   - Saves frames as PNG images

3. **Video Encoding**
   - Uses FFmpeg to create video from frames
   - Supports H.264 codec (libx264)
   - Configurable bitrate and quality

4. **Audio Mixing**
   - Downloads audio tracks from MinIO or external URLs
   - Mixes multiple audio tracks using FFmpeg
   - Applies volume adjustments
   - Syncs audio with video duration

## API Endpoints

### POST /export
Create a new export job

**Request Body:**
```json
{
  "project_id": "string",
  "customer_id": "string",
  "user_id": "string",
  "format": "mp4|mp3|json",
  "settings": {
    "quality": "720p|1080p|1440p|2160p",
    "fps": 24|30|60,
    "includeAudio": true|false,
    "codec": "libx264",
    "bitrate": "5M",
    "audioBitrate": "192k"
  }
}
```

**Response:**
```json
{
  "success": true,
  "export_job_id": "uuid",
  "status": "pending",
  "message": "Export job created successfully"
}
```

### GET /status/:job_id
Get export job status (inherited from BaseJob)

**Response:**
```json
{
  "job_id": "uuid",
  "job_type": "export-generator",
  "customer_id": "string",
  "status": "pending|running|completed|failed",
  "progress": 0-100,
  "result": {
    "status": "success",
    "output_url": "/api/assets/download/...",
    "video_id": "uuid",
    "file_size": 12345,
    "duration": 60.5,
    "format": "mp4"
  }
}
```

### DELETE /cancel/:job_id
Cancel a running export job (inherited from BaseJob)

## Configuration

See `config/settings.py` for all configuration options:

- MongoDB connection settings
- MinIO storage settings
- FFmpeg paths
- Video quality settings
- Processing timeouts
- Logging configuration

## Dependencies

- **Flask**: Web framework
- **pymongo**: MongoDB client
- **minio**: MinIO object storage client
- **Pillow**: Image processing
- **ffmpeg-python**: FFmpeg wrapper
- **requests**: HTTP client
- **APScheduler**: Job scheduling (from BaseJob)

## Deployment

### Docker

Build the Docker image:
```bash
docker build -t export-generator:latest .
```

Run the container:
```bash
docker run -p 8097:8097 \
  -e MONGODB_URL=mongodb://... \
  -e MINIO_ENDPOINT=minio:9000 \
  -e MINIO_ACCESS_KEY=... \
  -e MINIO_SECRET_KEY=... \
  export-generator:latest
```

### Environment Variables

Required:
- `MONGODB_URL`: MongoDB connection string
- `MINIO_ENDPOINT`: MinIO server endpoint
- `MINIO_ACCESS_KEY`: MinIO access key
- `MINIO_SECRET_KEY`: MinIO secret key

Optional:
- `FLASK_PORT`: Service port (default: 8097)
- `LOG_LEVEL`: Logging level (default: INFO)
- `TEMP_DIR`: Temporary directory (default: /app/temp)
- `EXPORT_OUTPUT_DIR`: Export output directory (default: /app/exports)

## Integration

### Frontend Integration

The frontend should call the export API through the api-server proxy:

```javascript
// Create export
const response = await api.post('/projects/export', {
  project_id: projectId,
  customer_id: customerId,
  user_id: userId,
  format: 'mp4',
  settings: {
    quality: '1080p',
    fps: 30,
    includeAudio: true
  }
});

const jobId = response.data.export_job_id;

// Poll for status
const statusInterval = setInterval(async () => {
  const status = await api.get(`/projects/export/${jobId}/status`);
  if (status.data.status === 'completed') {
    clearInterval(statusInterval);
    // Download or preview the export
  }
}, 2000);
```

## Next Steps

1. **Update asset-service routes** to proxy to export-generator instead of processing directly
2. **Update api-server routes** to point to export-generator service
3. **Add to docker-compose.yml** with proper networking and volumes
4. **Test end-to-end flow** from frontend to export completion
5. **Add monitoring and metrics** for export job performance

