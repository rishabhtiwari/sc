# Auto-Mark Images Feature

## Overview

The Auto-Mark Images feature is a **background job integrated into the IOPaint service** that automatically marks images as "cleaned" for customers who have enabled the `auto_mark_cleaned` setting. This allows customers to bypass manual watermark removal when their images are already clean.

**Architecture**: The auto-mark job runs as a background thread within the existing `iopaint` service, eliminating the need for a separate container.

## How It Works

### 1. Configuration Check
- The job runs every 5 minutes (configurable)
- For each customer, it checks the `image_config` collection
- If `auto_mark_cleaned: true`, the job processes that customer's images
- If `auto_mark_cleaned: false`, the job skips that customer

### 2. Image Processing
When auto-mark is enabled for a customer:
1. Finds all pending images (have `image`, have `short_summary`, no `clean_image`)
2. Marks each image as cleaned by setting `clean_image` to the original `image` URL
3. Sets `auto_marked_cleaned: true` flag to distinguish from manually cleaned images
4. Processes up to 50 images per run (configurable via `AUTO_MARK_BATCH_SIZE`)

### 3. Downstream Pipeline
Once images are marked as cleaned:
- They become available for audio generation (voice-generator job)
- Audio generation triggers video generation (video-generator job)
- Videos are uploaded to YouTube (youtube-uploader job)
- **No watermark removal occurs** - original images are used

## Configuration

### Environment Variables

These are configured in the `iopaint` service in `docker-compose.yml`:

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_AUTO_MARK_JOB` | `true` | Enable/disable the background job |
| `AUTO_MARK_INTERVAL_MINUTES` | `5` | How often the job runs (in minutes) |
| `AUTO_MARK_BATCH_SIZE` | `50` | Max images to process per run |
| `MONGODB_URL` | `mongodb://...` | MongoDB connection string |
| `FLASK_PORT` | `8096` | Port for the IOPaint service |

### Customer Settings

Customers control this feature via the UI toggle on the Image Processing page:

**Toggle OFF (Default)**:
```json
{
  "customer_id": "customer_123",
  "auto_mark_cleaned": false
}
```
- Job skips this customer
- Customer must manually clean images via UI

**Toggle ON**:
```json
{
  "customer_id": "customer_123",
  "auto_mark_cleaned": true
}
```
- Job automatically processes this customer's images
- No manual intervention needed

## Deployment

### Docker Compose

The auto-mark job is **integrated into the existing `iopaint` service**:

```yaml
iopaint:
  build:
    context: ./jobs
    dockerfile: ./watermark-remover/Dockerfile
  container_name: ichat-iopaint
  ports:
    - "8096:8096"
  environment:
    - FLASK_PORT=8096
    - MONGODB_URL=mongodb://...
    # Auto-mark job configuration
    - ENABLE_AUTO_MARK_JOB=true
    - AUTO_MARK_INTERVAL_MINUTES=5
    - AUTO_MARK_BATCH_SIZE=50
```

### Start the Service

```bash
# Build and start (includes auto-mark job)
docker-compose up -d iopaint

# View logs (includes auto-mark job logs)
docker-compose logs -f iopaint

# Check health
curl http://localhost:8096/health
```

### Disable Auto-Mark Job

To disable the background job entirely:

```yaml
environment:
  - ENABLE_AUTO_MARK_JOB=false
```

## Monitoring

### Health Check

```bash
curl http://localhost:8096/health
```

Response:
```json
{
  "status": "healthy",
  "service": "iopaint-ui",
  "model": "lama",
  "device": "cuda:0",
  "mongodb": "connected",
  "gpu": {
    "available": true,
    "device_name": "NVIDIA GeForce RTX 3090"
  }
}
```

### Logs

The auto-mark job logs are integrated with the IOPaint service logs:

```bash
docker-compose logs -f iopaint
```

Sample output:
```
2026-01-20 10:00:00 - iopaint_ui_service - INFO - 🤖 Starting auto-mark background job...
2026-01-20 10:00:00 - iopaint_ui_service - INFO - ⏰ Auto-mark job will run every 5 minutes
2026-01-20 10:05:00 - iopaint_ui_service - INFO - 🔄 Running auto-mark job...
2026-01-20 10:05:01 - iopaint_ui_service - INFO - ✅ Found 2 customers with auto-mark enabled
2026-01-20 10:05:01 - iopaint_ui_service - INFO - 🔍 Processing customer: customer_123
2026-01-20 10:05:02 - iopaint_ui_service - INFO - 📸 Found 25 pending images for customer customer_123
2026-01-20 10:05:05 - iopaint_ui_service - INFO - ✅ Marked image 507f1f77bcf86cd799439011 as cleaned (auto-mark)
2026-01-20 10:05:10 - iopaint_ui_service - INFO - ✅ Auto-mark completed for customer customer_123: 25/25 images marked
```

## Database Schema

### image_config Collection

```javascript
{
  "_id": ObjectId("..."),
  "customer_id": "customer_123",
  "auto_mark_cleaned": true,  // Toggle state
  "created_at": ISODate("2026-01-20T10:00:00Z"),
  "updated_at": ISODate("2026-01-20T12:00:00Z"),
  "updated_by": "user_456"
}
```

### news_document Collection (After Auto-Mark)

```javascript
{
  "_id": ObjectId("507f1f77bcf86cd799439011"),
  "customer_id": "customer_123",
  "title": "Breaking News",
  "image": "https://example.com/image.jpg",
  "clean_image": "https://example.com/image.jpg",  // Same as original
  "auto_marked_cleaned": true,  // Flag indicating auto-mark
  "clean_image_updated_at": ISODate("2026-01-20T10:00:05Z"),
  "short_summary": "This is a news summary...",
  "word_count": 45
}
```

## Workflow Comparison

### Manual Cleaning Mode (auto_mark_cleaned: false)

```
1. User loads image in UI
2. User paints watermark mask
3. User clicks "Remove Watermark"
4. AI processes image (GPU intensive)
5. User clicks "Save & Mark Done"
6. Cleaned image saved to disk
7. MongoDB updated with clean_image path
8. Audio generation triggered
9. Video generation triggered
```

### Auto-Mark Mode (auto_mark_cleaned: true)

```
1. Job runs every 5 minutes
2. Job finds pending images
3. Job marks images as cleaned (instant)
4. MongoDB updated with clean_image = original image URL
5. Audio generation triggered
6. Video generation triggered
```

## Performance

- **Processing Speed**: ~100 images/second (no AI processing)
- **Memory Usage**: ~256MB
- **CPU Usage**: Minimal (database operations only)
- **Network**: No image downloads (uses URLs)

## Troubleshooting

### Job Not Running

Check if the service is healthy and the job is enabled:
```bash
docker-compose ps iopaint
curl http://localhost:8096/health

# Check if auto-mark job is enabled
docker-compose exec iopaint env | grep ENABLE_AUTO_MARK_JOB
```

Check the logs for auto-mark activity:
```bash
docker-compose logs iopaint | grep "auto-mark"
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

3. Check job logs:
```bash
docker-compose logs job-auto-mark-images | grep ERROR
```

### Disable Auto-Mark for a Customer

Via UI: Toggle OFF on Image Processing page

Via MongoDB:
```javascript
db.image_config.updateOne(
  {customer_id: "customer_123"},
  {$set: {auto_mark_cleaned: false}}
)
```

## Future Enhancements

- [ ] Add metrics/statistics endpoint
- [ ] Support for selective auto-marking (by category, source, etc.)
- [ ] Notification when batch completes
- [ ] Integration with monitoring/alerting systems

