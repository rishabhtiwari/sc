# Asset Service

A dedicated microservice for managing all types of assets (audio, images, videos, documents) with integrated MinIO object storage.

## Features

- **Multi-Asset Support**: Audio, images, videos, and documents
- **Object Storage**: MinIO (S3-compatible) for scalable file storage
- **Metadata Management**: MongoDB for searchable asset metadata
- **Authentication**: JWT-based authentication
- **Organization**: Folders, tags, and categories
- **Access Control**: User and customer-based permissions
- **Pre-signed URLs**: Temporary access URLs for assets
- **RESTful API**: FastAPI-based REST API

## Architecture

```
Asset Service
├── FastAPI Application
├── MinIO Storage (Object Storage)
├── MongoDB (Metadata)
└── JWT Authentication
```

## API Endpoints

### Asset Management
- `POST /api/assets/upload` - Upload asset
- `GET /api/assets/{asset_id}` - Get asset metadata
- `GET /api/assets/{asset_id}/download` - Download asset
- `GET /api/assets/{asset_id}/url` - Get pre-signed URL
- `DELETE /api/assets/{asset_id}` - Delete asset
- `GET /api/assets/` - List assets

### Audio Library (Migration Compatible)
- `POST /api/audio-library/` - Save audio to library
- `GET /api/audio-library/` - Get audio library
- `DELETE /api/audio-library/{id}` - Delete from library

## Environment Variables

```bash
# MongoDB
MONGODB_URL=mongodb://ichat-mongodb:27017/
MONGODB_DB_NAME=ichat_db

# MinIO
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_SECURE=false

# JWT
JWT_SECRET_KEY=your-secret-key

# Logging
LOG_LEVEL=INFO
```

## Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run the service
python app.py
```

## Running with Docker

```bash
# Build
docker build -t asset-service .

# Run
docker run -p 8099:8099 asset-service
```

## Usage Examples

### Upload Asset
```bash
curl -X POST "http://localhost:8099/api/assets/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@audio.wav" \
  -F "asset_type=audio" \
  -F "name=My Audio" \
  -F "folder=Music"
```

### Get Asset
```bash
curl "http://localhost:8099/api/assets/{asset_id}" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Download Asset
```bash
curl "http://localhost:8099/api/assets/{asset_id}/download" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o downloaded_file.wav
```

## Development

### Project Structure
```
asset-service/
├── app.py                 # Main application
├── config/               # Configuration
│   └── settings.py
├── routes/               # API routes
│   ├── asset_routes.py
│   └── audio_library_routes.py
├── services/             # Business logic
│   ├── storage_service.py
│   └── database_service.py
├── models/               # Data models
│   └── asset.py
├── middleware/           # Middleware
│   └── auth_middleware.py
├── utils/                # Utilities
│   └── file_utils.py
└── requirements.txt      # Dependencies
```

## License

MIT

