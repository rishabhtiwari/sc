# Audio Library Service

## Overview

The `AudioLibraryService` handles all heavy lifting for audio library operations in the asset-service. This keeps the API routes lightweight and delegates complex processing to a dedicated service layer.

## Architecture

```
api-server (lightweight gateway)
    ↓
asset-service/routes/audio_library_routes.py (lightweight route handler)
    ↓
asset-service/services/audio_library_service.py (heavy lifting)
    ↓
    ├── Download from audio-generation service
    ├── Upload to MinIO
    ├── Save metadata to MongoDB
    └── Cleanup temp files
```

## Key Features

### 1. Download Audio from Audio-Generation Service
- Handles both relative (`/temp/file.wav`) and absolute URLs
- Configurable audio-generation service URL via `AUDIO_GENERATION_SERVICE_URL`
- Robust error handling with detailed logging

### 2. Upload to MinIO
- Organized storage: `{customer_id}/{user_id}/audio/{asset_id}.wav`
- Automatic presigned URL generation (7-day expiry)
- Metadata attachment for better organization

### 3. MongoDB Metadata Management
- Comprehensive asset metadata storage
- Custom fields for TTS-specific data (voice, model, language, etc.)
- Version tracking support

### 4. Automatic Cleanup
- Removes temporary files from audio-generation service
- Configurable via `CLEANUP_TEMP_AUDIO` environment variable
- Non-blocking (fire-and-forget) to avoid delays

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AUDIO_GENERATION_SERVICE_URL` | `http://audio-generation-factory:3000` | URL of audio-generation service |
| `CLEANUP_TEMP_AUDIO` | `true` | Enable/disable automatic temp file cleanup |

## Usage Example

```python
from services.audio_library_service import audio_library_service

# Save audio to library
result = audio_library_service.save_audio_to_library(
    asset_id="123e4567-e89b-12d3-a456-426614174000",
    customer_id="customer_123",
    user_id="user_456",
    audio_url="/temp/audio_xyz.wav",
    text="Hello world",
    duration=2.5,
    voice="kokoro-82m",
    voice_name="Kokoro",
    language="en",
    speed=1.0,
    model="kokoro-82m",
    folder="greetings",
    tags=["test", "demo"]
)

# Returns:
# {
#     "asset_id": "123e4567-e89b-12d3-a456-426614174000",
#     "storage": {
#         "bucket": "audio-assets",
#         "key": "customer_123/user_456/audio/123e4567-e89b-12d3-a456-426614174000.wav",
#         "size": 12345,
#         "url": "https://minio.example.com/..."
#     }
# }
```

## Error Handling

The service provides detailed error messages for:
- Download failures from audio-generation service
- Upload failures to MinIO
- Database operation failures
- Cleanup failures (logged but don't fail the request)

## Integration with Audio-Generation Service

The audio-generation service must provide:
1. **Audio file endpoint**: Serves generated audio files
2. **Cleanup endpoint**: `DELETE /api/cleanup/temp/{filename}` for temp file removal

## Future Enhancements

- [ ] Support for multiple audio formats (MP3, OGG, etc.)
- [ ] Batch processing for multiple audio files
- [ ] Audio transcoding/optimization
- [ ] CDN integration for faster delivery
- [ ] Retry logic for failed downloads/uploads

