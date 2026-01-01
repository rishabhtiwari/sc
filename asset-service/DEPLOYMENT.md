# Asset Service Deployment Guide

## Quick Start

### 1. Start the Services

```bash
# From the project root
cd /Users/rishabh.tiwari/IdeaProjects/sc

# Build and start MinIO and Asset Service
docker-compose up -d --build minio asset-service

# Check logs
docker-compose logs -f asset-service
docker-compose logs -f minio
```

### 2. Verify Services

```bash
# Check MinIO
curl http://localhost:9000/minio/health/live

# Check Asset Service
curl http://localhost:8099/health

# Expected response:
# {"status":"healthy","service":"Asset Service","version":"1.0.0"}
```

### 3. Access MinIO Console

Open http://localhost:9001 in your browser

- Username: `minioadmin`
- Password: `minioadmin`

You should see 4 buckets created:
- `audio-assets`
- `image-assets`
- `video-assets`
- `document-assets`

## Testing

### Test Health Endpoint

```bash
curl http://localhost:8099/health
```

### Test Upload (requires JWT token)

```bash
# Get a JWT token from your auth system first
TOKEN="your-jwt-token-here"

# Upload an audio file
curl -X POST "http://localhost:8099/api/assets/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test.wav" \
  -F "asset_type=audio" \
  -F "name=Test Audio" \
  -F "folder=Test" \
  -F "tags=test,demo"
```

### Test List Assets

```bash
curl "http://localhost:8099/api/assets/?page=1&page_size=10" \
  -H "Authorization: Bearer $TOKEN"
```

### Test Audio Library

```bash
# Save to library
curl -X POST "http://localhost:8099/api/audio-library/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This is a test",
    "audio_url": "http://example.com/test.wav",
    "duration": 5.5,
    "voice": "af_sky",
    "voice_name": "Sky",
    "language": "en",
    "speed": 1.0,
    "model": "kokoro-82m"
  }'

# Get library
curl "http://localhost:8099/api/audio-library/" \
  -H "Authorization: Bearer $TOKEN"
```

## Integration with Frontend

### Update Environment Variables

The frontend-server already has the asset service URL configured:

```bash
ASSET_SERVICE_URL=http://ichat-asset-service:8099
```

### Update Audio Studio Component

In `frontend-server/src/components/AudioStudio/TextToSpeechPanel.jsx`:

```javascript
// Change the save to library endpoint
const saveToLibrary = async (message) => {
  const response = await fetch('/api/audio-library/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      text: message.text,
      audio_url: message.audioUrl,
      duration: message.duration,
      voice: message.voice,
      voice_name: message.voiceName,
      language: message.language,
      speed: message.speed,
      model: 'kokoro-82m',
      folder: selectedFolder,
      tags: message.tags || []
    })
  });
  
  if (!response.ok) {
    throw new Error('Failed to save to library');
  }
  
  return response.json();
};
```

### Add Proxy Route in Frontend Server

In `frontend-server/server.js`, add:

```javascript
// Proxy to asset service
app.use('/api/audio-library', createProxyMiddleware({
  target: process.env.ASSET_SERVICE_URL || 'http://localhost:8099',
  changeOrigin: true,
  pathRewrite: {
    '^/api/audio-library': '/api/audio-library'
  }
}));

app.use('/api/assets', createProxyMiddleware({
  target: process.env.ASSET_SERVICE_URL || 'http://localhost:8099',
  changeOrigin: true,
  pathRewrite: {
    '^/api/assets': '/api/assets'
  }
}));
```

## Troubleshooting

### MinIO Connection Issues

```bash
# Check if MinIO is running
docker ps | grep minio

# Check MinIO logs
docker-compose logs minio

# Restart MinIO
docker-compose restart minio
```

### Asset Service Issues

```bash
# Check logs
docker-compose logs asset-service

# Restart service
docker-compose restart asset-service

# Rebuild if needed
docker-compose up -d --build asset-service
```

### Bucket Not Found

```bash
# Run initialization script manually
docker-compose exec asset-service python scripts/init_minio.py
```

## Production Considerations

### 1. Security

- Change MinIO credentials in production
- Use strong JWT secret key
- Enable HTTPS for MinIO
- Implement proper CORS policies
- Add rate limiting

### 2. Storage

- Configure MinIO with persistent volumes
- Set up backup strategy
- Implement lifecycle policies for old assets
- Consider using external S3 for production

### 3. Performance

- Increase worker count based on load
- Add caching layer (Redis)
- Use CDN for asset delivery
- Implement connection pooling

### 4. Monitoring

- Add Prometheus metrics
- Set up logging aggregation
- Monitor storage usage
- Track API performance

## Next Steps

1. ✅ Deploy services
2. ✅ Verify health checks
3. ✅ Test API endpoints
4. [ ] Update frontend to use asset service
5. [ ] Migrate existing audio data
6. [ ] Remove old audio library code from api-server
7. [ ] Test end-to-end workflow
8. [ ] Deploy to production

