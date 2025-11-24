# YouTube Uploader Service

Automated service for uploading news videos to YouTube with a web-based UI.

## Features

- 📺 Upload videos to YouTube automatically
- 🎯 Web UI for easy management
- 📊 Real-time statistics dashboard
- 🔄 Batch upload support (latest 20 videos)
- 📝 Automatic metadata from news articles
- ✅ Upload tracking in MongoDB

## Setup

### 1. Get YouTube API Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable **YouTube Data API v3**
4. Create OAuth 2.0 credentials (Desktop app)
5. Download the credentials JSON file
6. Save it as `credentials/client_secrets.json`

### 2. First-Time Authentication

On first run, the service will open a browser window for OAuth authentication:

1. Start the service: `docker-compose up youtube-uploader`
2. The service will prompt for authentication
3. Follow the browser prompts to authorize the app
4. Credentials will be saved to `credentials/youtube_credentials.json`

### 3. Access the UI

Open http://localhost:8097 in your browser

## API Endpoints

### GET /
Web UI for managing uploads

### GET /api/stats
Get upload statistics
```json
{
  "ready_to_upload": 15,
  "already_uploaded": 5,
  "total_videos": 20
}
```

### POST /api/upload-latest-20
Upload latest 20 news videos to YouTube
```json
{
  "status": "success",
  "message": "Uploaded 18 out of 20 videos",
  "total": 20,
  "success": 18,
  "failed": 2,
  "results": [...]
}
```

### GET /health
Health check endpoint

## Configuration

Environment variables:

- `FLASK_PORT`: Service port (default: 8097)
- `MONGODB_URL`: MongoDB connection string
- `VIDEO_BASE_PATH`: Base path for video files
- `DEFAULT_CATEGORY_ID`: YouTube category (default: 25 = News & Politics)
- `DEFAULT_PRIVACY_STATUS`: Video privacy (public/private/unlisted)
- `DEFAULT_TAGS`: Comma-separated tags

## MongoDB Schema

The service adds these fields to `news_document` collection:

```javascript
{
  "youtube_video_id": "string",      // YouTube video ID
  "youtube_video_url": "string",     // Full YouTube URL
  "youtube_uploaded_at": "Date"      // Upload timestamp
}
```

## Usage

1. Generate news videos using the video-generator service
2. Open YouTube Uploader UI at http://localhost:8097
3. Click "Upload Latest 20 News to YouTube"
4. Monitor upload progress in real-time
5. Videos are automatically marked as uploaded in MongoDB

## Notes

- Only videos with `video_path` and without `youtube_video_id` are uploaded
- Duplicate uploads are prevented by checking `youtube_video_id`
- Failed uploads can be retried (they won't be marked as uploaded)
- OAuth credentials are persisted in `credentials/` directory

