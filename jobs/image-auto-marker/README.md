# Image Auto-Marker Job

## Overview

The Image Auto-Marker Job is a **scheduled background service** that automatically marks images as "cleaned" for customers who have enabled the `auto_mark_cleaned` setting. This allows customers to bypass manual watermark removal when their images are already clean.

## Architecture

This job follows the **BaseJob pattern** used across all jobs in the system:
- Extends `BaseJob` for consistent scheduling and monitoring
- Multi-tenant aware (runs separately for each customer)
- Integrates with the job instance tracking system
- Provides health check and on-demand execution endpoints

## How It Works

### Scheduled Execution (Every 5 minutes)
1. Job runs for each customer independently
2. Checks if `auto_mark_cleaned` is enabled for the customer
3. If enabled, finds pending images (have `image`, have `short_summary`, no `clean_image`)
4. Marks each image as cleaned by setting `clean_image = image` (original URL)
5. Sets `auto_marked_cleaned: true` flag to distinguish from manually cleaned images
6. Processes up to 50 images per run (configurable)

### Default Behavior
- **New customers**: `auto_mark_cleaned = true` (auto-processing enabled by default)
- **Existing customers**: Controlled via UI toggle on Image Processing page

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `JOB_INTERVAL_MINUTES` | `5` | How often the job runs (in minutes) |
| `AUTO_MARK_BATCH_SIZE` | `50` | Max images to process per run |
| `MONGODB_URL` | `mongodb://...` | MongoDB connection string |
| `FLASK_PORT` | `8098` | Port for health check and API endpoints |
| `LOG_FILE` | `/var/log/image-auto-marker.log` | Log file path |

## API Endpoints

### Health Check
```bash
GET http://localhost:8098/health
```

### Trigger On-Demand Job
```bash
POST http://localhost:8098/api/jobs/trigger
Headers:
  X-Customer-ID: customer_123
  X-User-ID: user_456
```

### Get Job Status
```bash
GET http://localhost:8098/api/jobs/{job_id}
```

### List Recent Jobs
```bash
GET http://localhost:8098/api/jobs?limit=10
```

## Deployment

### Docker Compose

```bash
# Start the service
docker-compose up -d job-image-auto-marker

# View logs
docker-compose logs -f job-image-auto-marker

# Check health
curl http://localhost:8098/health
```

### Configuration in docker-compose.yml

```yaml
job-image-auto-marker:
  build:
    context: ./jobs
    dockerfile: ./image-auto-marker/Dockerfile
  container_name: ichat-image-auto-marker
  ports:
    - "8098:8098"
  environment:
    - JOB_INTERVAL_MINUTES=5
    - AUTO_MARK_BATCH_SIZE=50
    - MONGODB_URL=mongodb://...
```

## Database Schema

### image_config Collection
```javascript
{
  "_id": ObjectId("..."),
  "customer_id": "customer_123",
  "auto_mark_cleaned": true,  // Default: true
  "created_at": ISODate("2026-01-20T10:00:00Z"),
  "updated_at": ISODate("2026-01-20T12:00:00Z")
}
```

### news_document Collection (After Auto-Mark)
```javascript
{
  "_id": ObjectId("..."),
  "customer_id": "customer_123",
  "image": "https://example.com/image.jpg",
  "clean_image": "https://example.com/image.jpg",  // Same as original
  "auto_marked_cleaned": true,  // Flag indicating auto-processing
  "clean_image_updated_at": ISODate("2026-01-20T10:00:05Z")
}
```

## Monitoring

### Logs

```bash
# View all logs
docker-compose logs -f job-image-auto-marker

# Filter for specific customer
docker-compose logs job-image-auto-marker | grep "customer_123"

# Filter for errors
docker-compose logs job-image-auto-marker | grep "ERROR"
```

Sample log output:
```
2026-01-20 10:00:00 - image-auto-marker - INFO - 🚀 Starting image auto-marker job for customer: customer_123
2026-01-20 10:00:01 - image-auto-marker - INFO - 🔍 Processing pending images for customer: customer_123
2026-01-20 10:00:02 - image-auto-marker - INFO - 📸 Found 25 pending images for customer customer_123
2026-01-20 10:00:05 - image-auto-marker - INFO - ✅ Marked image 507f1f77bcf86cd799439011 as cleaned (auto-mark)
2026-01-20 10:00:10 - image-auto-marker - INFO - ✅ Auto-mark completed for customer customer_123: 25/25 images marked
```

## Integration with Pipeline

Once images are auto-marked:
1. **Voice Generator Job** picks up images with `clean_image` set
2. Generates audio for the news article
3. **Video Generator Job** creates video using the cleaned image
4. **YouTube Uploader** publishes the video

## Performance

- **Processing Speed**: ~100 images/second (no AI processing)
- **Memory Usage**: ~256MB
- **CPU Usage**: Minimal (database operations only)
- **Network**: No image downloads (uses URLs)

## Troubleshooting

### Job Not Running

```bash
# Check service status
docker-compose ps job-image-auto-marker

# Check health
curl http://localhost:8098/health

# View recent logs
docker-compose logs --tail=100 job-image-auto-marker
```

### Images Not Being Marked

1. Check if auto_mark_cleaned is enabled:
```javascript
db.image_config.findOne({customer_id: "customer_123"})
```

2. Check if images meet criteria:
```javascript
db.news_document.find({
  customer_id: "customer_123",
  image: {$ne: null},
  clean_image: null,
  short_summary: {$ne: null, $ne: ""}
})
```

3. Trigger on-demand job:
```bash
curl -X POST http://localhost:8098/api/jobs/trigger \
  -H "X-Customer-ID: customer_123"
```

## Related Services

- **IOPaint Service** (`iopaint`): Manual watermark removal UI
- **Voice Generator Job** (`job-voice-generator`): Generates audio for cleaned images
- **Video Generator Job** (`job-video-generator`): Creates videos from audio + images

