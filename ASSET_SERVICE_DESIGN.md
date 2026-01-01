# Asset Service Architecture Design

## Overview
A dedicated microservice for managing all types of assets (audio, images, videos, documents) with integrated MinIO object storage.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Asset Service                            │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   REST API   │  │  WebSocket   │  │   GraphQL    │      │
│  │  (FastAPI)   │  │  (Optional)  │  │  (Optional)  │      │
│  └──────┬───────┘  └──────────────┘  └──────────────┘      │
│         │                                                     │
│  ┌──────▼──────────────────────────────────────────┐        │
│  │         Asset Management Layer                   │        │
│  │  - Upload/Download                               │        │
│  │  - Metadata Management                           │        │
│  │  - Access Control                                │        │
│  │  - Versioning                                    │        │
│  └──────┬──────────────────────────────────────────┘        │
│         │                                                     │
│  ┌──────▼──────────┐  ┌──────────────┐                      │
│  │  Storage Layer  │  │  DB Layer    │                      │
│  │    (MinIO)      │  │  (MongoDB)   │                      │
│  └─────────────────┘  └──────────────┘                      │
└─────────────────────────────────────────────────────────────┘
```

## Features

### 1. Asset Types Support
- **Audio**: WAV, MP3, OGG, FLAC
- **Images**: PNG, JPG, WEBP, SVG
- **Videos**: MP4, WEBM, AVI
- **Documents**: PDF, DOCX, TXT

### 2. Core Capabilities
- **Upload**: Multipart upload with progress tracking
- **Download**: Streaming download with range support
- **Storage**: MinIO object storage with buckets per asset type
- **Metadata**: MongoDB for searchable metadata
- **Organization**: Folders, tags, categories
- **Access Control**: User/customer-based permissions
- **Versioning**: Track asset versions
- **CDN Ready**: Pre-signed URLs for direct access

### 3. API Endpoints

#### Asset Management
- `POST /api/assets/upload` - Upload asset
- `GET /api/assets/{asset_id}` - Get asset metadata
- `GET /api/assets/{asset_id}/download` - Download asset
- `DELETE /api/assets/{asset_id}` - Delete asset
- `PUT /api/assets/{asset_id}` - Update metadata
- `GET /api/assets/search` - Search assets

#### Library Management
- `GET /api/library/{type}` - List assets by type
- `POST /api/library/{type}/folder` - Create folder
- `GET /api/library/{type}/folders` - List folders
- `PUT /api/library/{type}/move` - Move assets

#### Audio Library (Migration from api-server)
- `GET /api/audio-library` - List audio files
- `POST /api/audio-library` - Save audio to library
- `DELETE /api/audio-library/{id}` - Delete audio
- `GET /api/audio-library/stats` - Get statistics

## Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.11)
- **Storage**: MinIO (S3-compatible)
- **Database**: MongoDB (metadata)
- **Authentication**: JWT (shared with other services)
- **File Processing**: 
  - Audio: pydub, mutagen
  - Images: Pillow
  - Videos: ffmpeg-python

### Infrastructure
- **Container**: Docker
- **Orchestration**: Docker Compose
- **Networking**: Internal Docker network
- **Volumes**: Persistent storage for MinIO data

## Database Schema

### MongoDB Collections

#### `assets` Collection
```json
{
  "_id": "ObjectId",
  "asset_id": "string (UUID)",
  "customer_id": "string",
  "user_id": "string",
  "type": "audio|image|video|document",
  "name": "string",
  "original_filename": "string",
  "mime_type": "string",
  "size": "number (bytes)",
  "duration": "number (seconds, for audio/video)",
  "dimensions": {
    "width": "number",
    "height": "number"
  },
  "storage": {
    "bucket": "string",
    "key": "string",
    "url": "string (MinIO URL)"
  },
  "metadata": {
    "title": "string",
    "description": "string",
    "tags": ["string"],
    "folder": "string",
    "custom": {}
  },
  "versions": [{
    "version": "number",
    "created_at": "datetime",
    "size": "number",
    "storage_key": "string"
  }],
  "created_at": "datetime",
  "updated_at": "datetime",
  "deleted_at": "datetime (soft delete)"
}
```

## MinIO Configuration

### Buckets
- `audio-assets` - Audio files
- `image-assets` - Images
- `video-assets` - Videos
- `document-assets` - Documents
- `temp-uploads` - Temporary uploads

### Access Policies
- Private by default
- Pre-signed URLs for temporary access
- Public buckets for CDN-ready assets (optional)

## Migration Plan

### Phase 1: Setup Infrastructure
1. Create asset-service directory structure
2. Setup MinIO in docker-compose
3. Create FastAPI application skeleton
4. Setup MongoDB connection

### Phase 2: Core Implementation
1. Implement MinIO client wrapper
2. Create upload/download endpoints
3. Implement metadata management
4. Add authentication middleware

### Phase 3: Audio Library Migration
1. Migrate audio library endpoints from api-server
2. Update frontend to use new endpoints
3. Migrate existing audio data (if any)
4. Remove old endpoints from api-server

### Phase 4: Enhancement
1. Add image/video support
2. Implement versioning
3. Add search and filtering
4. Implement CDN integration

