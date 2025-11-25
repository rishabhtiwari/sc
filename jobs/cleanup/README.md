# Cleanup Job Service

Automated service for cleaning up old news articles and their associated files (audio, video, images) from the system.

## Overview

The Cleanup Job Service automatically deletes news articles that are older than a configurable retention period (default: 36 hours) along with all their associated files:

- Audio files (title, description, content, short_summary)
- Video files (regular and shorts)
- Clean images (watermark-removed)
- MongoDB documents

## Features

- ✅ **Automatic Scheduled Cleanup**: Runs every 6 hours by default
- ✅ **Configurable Retention Period**: Set how long to keep articles (default: 36 hours)
- ✅ **Dry-Run Mode**: Preview what would be deleted without actually deleting
- ✅ **Manual Trigger**: Run cleanup on-demand via API
- ✅ **Batch Processing**: Processes articles in configurable batches
- ✅ **Safety Limits**: Maximum articles per run to prevent accidents
- ✅ **Detailed Statistics**: Track files deleted, space freed, errors
- ✅ **Comprehensive Logging**: Full audit trail of all deletions

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CLEANUP_RETENTION_HOURS` | `36` | Delete articles older than this many hours |
| `CLEANUP_DRY_RUN` | `false` | If true, only preview deletions without actually deleting |
| `CLEANUP_BATCH_SIZE` | `100` | Number of articles to process in each batch |
| `CLEANUP_MAX_ARTICLES_PER_RUN` | `10000` | Maximum articles to delete in a single run (safety limit) |
| `JOB_INTERVAL_SECONDS` | `21600` | Run cleanup every N seconds (21600 = 6 hours) |
| `FLASK_PORT` | `8099` | Port for the cleanup service API |

### File Paths

The service expects the following volume mounts:

- `/app/video_public` - Video files directory
- `/app/audio_public` - Audio files directory
- `/app/image_public` - Image files directory

## API Endpoints

### Health Check
```bash
GET /health
```

### Run Cleanup (Manual Trigger)
```bash
POST /run
Content-Type: application/json

{
  "retention_hours": 36,  # Optional, defaults to config
  "dry_run": false        # Optional, defaults to config
}
```

### Preview Cleanup (Dry-Run)
```bash
POST /cleanup/preview
Content-Type: application/json

{
  "retention_hours": 36  # Optional
}
```

### Get Cleanup Statistics
```bash
GET /cleanup/stats
```

Returns statistics from the last completed cleanup job.

### Get Job Status
```bash
GET /status/<job_id>
```

### List All Jobs
```bash
GET /jobs
```

## Usage Examples

### Preview What Would Be Deleted
```bash
curl -X POST http://localhost:8099/cleanup/preview \
  -H "Content-Type: application/json" \
  -d '{"retention_hours": 48}'
```

### Run Cleanup Manually
```bash
curl -X POST http://localhost:8099/run \
  -H "Content-Type: application/json" \
  -d '{"retention_hours": 36, "dry_run": false}'
```

### Get Last Cleanup Statistics
```bash
curl http://localhost:8099/cleanup/stats
```

## Docker Deployment

The service is deployed as part of the docker-compose stack:

```yaml
job-cleanup:
  build:
    context: ./jobs
    dockerfile: cleanup/Dockerfile
  container_name: ichat-cleanup
  environment:
    - CLEANUP_RETENTION_HOURS=36
    - CLEANUP_DRY_RUN=false
    - JOB_INTERVAL_SECONDS=21600
  volumes:
    - ./jobs/video-generator/public:/app/video_public
    - ./jobs/voice-generator/public:/app/audio_public
    - ./jobs/watermark-remover/public:/app/image_public
  depends_on:
    - mongodb
  restart: unless-stopped
```

## Cleanup Process

1. **Query MongoDB**: Find articles with `created_at` older than retention period
2. **Process in Batches**: Handle articles in configurable batch sizes
3. **Delete Files**: Remove article directories from video/audio/image public folders
4. **Delete Documents**: Remove MongoDB documents for cleaned articles
5. **Track Statistics**: Log files deleted, space freed, errors encountered
6. **Report Results**: Return comprehensive statistics

## Safety Features

- **Dry-Run Mode**: Test cleanup without actually deleting anything
- **Batch Processing**: Prevents memory issues with large datasets
- **Maximum Limit**: Safety cap on articles per run
- **Error Handling**: Continues processing even if individual deletions fail
- **Detailed Logging**: Full audit trail of all operations

## Monitoring

### Logs

Logs are written to `logs/cleanup.log` and include:

- Articles processed
- Files and directories deleted
- Space freed
- Errors encountered
- Execution time

### Statistics

Each cleanup run tracks:

- Total articles found
- Total articles deleted
- Total files deleted
- Total directories deleted
- Total space freed (bytes)
- Errors encountered
- Execution time

## Troubleshooting

### No Articles Being Deleted

Check:
1. Is `CLEANUP_DRY_RUN` set to `true`? (Change to `false` for actual deletion)
2. Are there articles older than `CLEANUP_RETENTION_HOURS`?
3. Check logs for errors

### Permission Errors

Ensure the container has write permissions to the mounted volumes:
```bash
chmod -R 755 jobs/video-generator/public
chmod -R 755 jobs/voice-generator/public
chmod -R 755 jobs/watermark-remover/public
```

### MongoDB Connection Issues

Verify MongoDB connection string in environment variables:
```bash
docker logs ichat-cleanup
```

## Development

### Local Testing

1. Set dry-run mode:
   ```bash
   export CLEANUP_DRY_RUN=true
   ```

2. Run the service:
   ```bash
   cd jobs/cleanup
   python app.py
   ```

3. Trigger cleanup:
   ```bash
   curl -X POST http://localhost:8099/run
   ```

### Testing with Docker

```bash
# Build and start
docker-compose build job-cleanup
docker-compose up -d job-cleanup

# View logs
docker logs -f ichat-cleanup

# Trigger manual cleanup
curl -X POST http://localhost:8099/run
```

