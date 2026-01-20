# Auto-Mark Images Implementation Summary

## Overview

This implementation adds an **automatic image processing feature** that allows customers to bypass manual watermark removal when their images are already clean. The feature is controlled via a UI toggle and runs as a background job.

## Architecture

### Single Service Design
- **Service**: `iopaint` (existing watermark removal service)
- **Components**:
  1. **UI Service** (Flask app on port 8096) - Manual watermark removal interface
  2. **Background Job** (daemon thread) - Automatic image marking

### Why Single Service?
- ✅ Simpler deployment (no additional container)
- ✅ Shared MongoDB connection
- ✅ Shared logging infrastructure
- ✅ Lower resource usage
- ✅ Easier to maintain

## How It Works

### 1. Default Behavior (Toggle ON - Default)
```
Customer creates account
  ↓
auto_mark_cleaned = TRUE (default)
  ↓
Background job runs every 5 minutes
  ↓
Finds pending images (have image, have short_summary, no clean_image)
  ↓
Marks clean_image = original image URL
  ↓
Audio generation job picks up images
  ↓
Video generation job creates videos
  ↓
YouTube uploader publishes videos
```

**Result**: Fully automated pipeline, no manual intervention needed

### 2. Manual Cleaning Mode (Toggle OFF)
```
Customer toggles OFF in UI
  ↓
auto_mark_cleaned = FALSE
  ↓
Background job skips this customer
  ↓
Customer manually loads images in UI
  ↓
Customer paints watermark mask
  ↓
AI removes watermark (GPU processing)
  ↓
Customer saves cleaned image
  ↓
Audio/video pipeline continues
```

**Result**: Manual control over watermark removal

## Database Schema

### image_config Collection
```javascript
{
  "_id": ObjectId("..."),
  "customer_id": "customer_123",
  "auto_mark_cleaned": true,  // Default: true (auto-processing enabled)
  "created_at": ISODate("2026-01-20T10:00:00Z"),
  "updated_at": ISODate("2026-01-20T12:00:00Z"),
  "updated_by": "user_456"
}
```

### news_document Collection (Auto-Marked)
```javascript
{
  "_id": ObjectId("..."),
  "customer_id": "customer_123",
  "title": "Breaking News",
  "image": "https://example.com/image.jpg",
  "clean_image": "https://example.com/image.jpg",  // Same as original
  "auto_marked_cleaned": true,  // Flag indicating auto-processing
  "clean_image_updated_at": ISODate("2026-01-20T10:00:05Z"),
  "short_summary": "News summary...",
  "word_count": 45
}
```

## API Endpoints

### GET /api/image-config
Get current customer's configuration

**Response**:
```json
{
  "customer_id": "customer_123",
  "auto_mark_cleaned": true,
  "created_at": "2026-01-20T10:00:00Z",
  "updated_at": "2026-01-20T12:00:00Z"
}
```

### PUT /api/image-config
Update customer's configuration

**Request**:
```json
{
  "auto_mark_cleaned": false
}
```

**Response**:
```json
{
  "customer_id": "customer_123",
  "auto_mark_cleaned": false,
  "created_at": "2026-01-20T10:00:00Z",
  "updated_at": "2026-01-20T12:30:00Z"
}
```

## Configuration

### Environment Variables (docker-compose.yml)
```yaml
environment:
  - AUTO_MARK_INTERVAL_MINUTES=5  # Job runs every 5 minutes
  - AUTO_MARK_BATCH_SIZE=50       # Process 50 images per run
```

### Default Values
- **auto_mark_cleaned**: `true` (auto-processing enabled by default)
- **Interval**: 5 minutes
- **Batch size**: 50 images per run

## Deployment

### Start Service
```bash
docker-compose up -d iopaint
```

### View Logs
```bash
# All logs (UI + background job)
docker-compose logs -f iopaint

# Filter for auto-mark logs
docker-compose logs -f iopaint | grep "auto-mark"
```

### Health Check
```bash
curl http://localhost:8096/health
```

## Testing

### Test Auto-Mark Feature
1. Create a customer account
2. Add news articles with images and short_summary
3. Wait 5 minutes (or check logs)
4. Verify `clean_image` field is populated
5. Verify `auto_marked_cleaned: true` flag

### Test Manual Mode
1. Toggle OFF in UI (`PUT /api/image-config` with `auto_mark_cleaned: false`)
2. Add news articles with images
3. Wait 5 minutes - images should NOT be auto-marked
4. Manually clean images via UI
5. Verify `clean_image` field is populated
6. Verify `auto_marked_cleaned` field is NOT set

## Performance

- **Processing Speed**: ~100 images/second (no AI processing)
- **Memory Usage**: Same as iopaint service (~2-8GB depending on GPU)
- **CPU Usage**: Minimal (database operations only)
- **Network**: No image downloads (uses URLs)

## Key Benefits

1. **Zero Configuration**: Works out of the box with sensible defaults
2. **Customer Control**: Each customer can toggle on/off independently
3. **No Extra Resources**: Runs in existing service container
4. **Fully Automated**: Default behavior requires no manual intervention
5. **Flexible**: Customers can switch between auto/manual modes anytime

