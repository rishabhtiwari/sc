# 🔌 Canva-Like Platform - API Specifications

## Overview

This document defines all REST API endpoints for the Canva-like design platform.

---

## 🏗️ Service Architecture

```
Port 8080: API Server (Proxy + Auth)
Port 5010: Template Service (existing)
Port 5011: Design Service (NEW)
Port 5012: Asset Service (NEW)
Port 5013: Render Service (NEW)
```

---

## 📋 Categories API

### GET /api/categories

Get all design categories.

**Response:**
```json
{
  "categories": [
    {
      "category_id": "social_media",
      "name": "Social Media",
      "icon": "📱",
      "description": "Create stunning social media posts",
      "order": 3,
      "subcategories": [
        {
          "id": "instagram_post",
          "name": "Instagram Post",
          "dimensions": { "width": 1080, "height": 1080 },
          "template_count": 25
        }
      ]
    }
  ]
}
```

### GET /api/categories/:categoryId

Get specific category with templates.

**Response:**
```json
{
  "category_id": "social_media",
  "name": "Social Media",
  "subcategories": [...],
  "templates": [
    {
      "template_id": "instagram_minimal_1",
      "name": "Minimal Instagram Post",
      "thumbnail": "https://s3.../thumb.jpg",
      "preview_video": "https://s3.../preview.mp4",
      "popularity_score": 0.95,
      "is_premium": false
    }
  ]
}
```

---

## 🎨 Designs API

### POST /api/designs

Create or update a design.

**Request:**
```json
{
  "design_id": "design_abc123",  // Optional for create
  "name": "My Instagram Post",
  "category": "social_media",
  "subcategory": "instagram_post",
  "dimensions": {
    "width": 1080,
    "height": 1080
  },
  "canvas_state": {
    "version": "5.3.0",
    "objects": [
      {
        "type": "text",
        "text": "Hello World",
        "left": 100,
        "top": 100,
        "fontSize": 40,
        "fill": "#000000"
      }
    ]
  },
  "timeline": {
    "duration": 10.0,
    "tracks": []
  },
  "assets": ["asset_1", "asset_2"]
}
```

**Response:**
```json
{
  "status": "success",
  "design_id": "design_abc123",
  "message": "Design saved successfully"
}
```

### GET /api/designs/:designId

Get a specific design.

**Response:**
```json
{
  "design_id": "design_abc123",
  "customer_id": "customer_xyz",
  "user_id": "user_123",
  "name": "My Instagram Post",
  "category": "social_media",
  "subcategory": "instagram_post",
  "canvas_state": { /* Fabric.js JSON */ },
  "timeline": { /* Timeline data */ },
  "assets": [...],
  "created_at": "2025-12-01T10:00:00Z",
  "updated_at": "2025-12-31T15:30:00Z",
  "status": "draft",
  "thumbnail": "https://s3.../thumb.jpg"
}
```

### GET /api/designs

List all designs for current user.

**Query Parameters:**
- `category` (optional): Filter by category
- `status` (optional): Filter by status (draft, published, archived)
- `limit` (optional): Number of results (default: 50)
- `offset` (optional): Pagination offset

**Response:**
```json
{
  "designs": [
    {
      "design_id": "design_abc123",
      "name": "My Instagram Post",
      "thumbnail": "https://s3.../thumb.jpg",
      "updated_at": "2025-12-31T15:30:00Z",
      "category": "social_media"
    }
  ],
  "total": 42,
  "limit": 50,
  "offset": 0
}
```

### DELETE /api/designs/:designId

Delete a design (soft delete).

**Response:**
```json
{
  "status": "success",
  "message": "Design deleted successfully"
}
```

---

## 📁 Assets API

### POST /api/assets/upload

Upload a new asset (image, video, audio).

**Request:** `multipart/form-data`
- `file`: File to upload
- `type`: Asset type (image, video, audio, font)
- `folder`: Optional folder name

**Response:**
```json
{
  "status": "success",
  "asset": {
    "asset_id": "asset_abc123",
    "type": "image",
    "filename": "my-photo.jpg",
    "url": "https://s3.../my-photo.jpg",
    "thumbnail": "https://s3.../thumb.jpg",
    "size": 1024000,
    "dimensions": { "width": 1920, "height": 1080 },
    "uploaded_at": "2025-12-31T15:30:00Z"
  }
}
```

### GET /api/assets

List user's uploaded assets.

**Query Parameters:**
- `type` (optional): Filter by type
- `folder` (optional): Filter by folder
- `limit` (optional): Number of results
- `offset` (optional): Pagination offset

**Response:**
```json
{
  "assets": [
    {
      "asset_id": "asset_abc123",
      "type": "image",
      "filename": "my-photo.jpg",
      "url": "https://s3.../my-photo.jpg",
      "thumbnail": "https://s3.../thumb.jpg",
      "uploaded_at": "2025-12-31T15:30:00Z"
    }
  ],
  "total": 100
}
```

### DELETE /api/assets/:assetId

Delete an asset.

**Response:**
```json
{
  "status": "success",
  "message": "Asset deleted successfully"
}
```

---

## 🎬 Render API

### POST /api/render/image

Export design as image.

**Request:**
```json
{
  "design_id": "design_abc123",
  "format": "png",  // png, jpg, svg, pdf
  "quality": "high",  // low, medium, high
  "scale": 1.0,  // Export scale (1.0 = original size)
  "transparent": true  // PNG only
}
```

**Response:**
```json
{
  "status": "success",
  "export_id": "export_xyz789",
  "url": "https://s3.../export.png",
  "size": 2048000,
  "dimensions": { "width": 1080, "height": 1080 }
}
```

### POST /api/render/video

Export design as video.

**Request:**
```json
{
  "design_id": "design_abc123",
  "format": "mp4",  // mp4, webm, gif
  "quality": "high",  // low (720p), medium (1080p), high (4K)
  "fps": 30,
  "codec": "h264"  // h264, h265, vp9
}
```

**Response:**
```json
{
  "status": "queued",
  "job_id": "job_123",
  "message": "Video rendering started",
  "estimated_time": 120  // seconds
}
```

### GET /api/render/status/:jobId

Check rendering job status.

**Response:**
```json
{
  "job_id": "job_123",
  "status": "processing",  // queued, processing, completed, failed
  "progress": 45,  // percentage
  "url": null,  // Available when completed
  "error": null,  // Error message if failed
  "created_at": "2025-12-31T15:30:00Z",
  "completed_at": null
}
```

---

## 🖼️ Stock Assets API

### GET /api/stock/images

Search stock images (Unsplash/Pexels).

**Query Parameters:**
- `query`: Search query
- `page`: Page number (default: 1)
- `per_page`: Results per page (default: 20)

**Response:**
```json
{
  "images": [
    {
      "id": "unsplash_abc123",
      "url": "https://images.unsplash.com/...",
      "thumbnail": "https://images.unsplash.com/.../thumb",
      "width": 4000,
      "height": 3000,
      "author": "John Doe",
      "source": "unsplash"
    }
  ],
  "total": 1000,
  "page": 1,
  "per_page": 20
}
```

### GET /api/stock/videos

Search stock videos (Pexels).

**Query Parameters:**
- `query`: Search query
- `page`: Page number
- `per_page`: Results per page

**Response:**
```json
{
  "videos": [
    {
      "id": "pexels_abc123",
      "url": "https://videos.pexels.com/...",
      "thumbnail": "https://images.pexels.com/.../thumb",
      "duration": 15.5,
      "width": 1920,
      "height": 1080,
      "author": "Jane Smith",
      "source": "pexels"
    }
  ],
  "total": 500,
  "page": 1
}
```

### GET /api/stock/fonts

Get available fonts (Google Fonts).

**Response:**
```json
{
  "fonts": [
    {
      "family": "Roboto",
      "variants": ["regular", "italic", "700", "700italic"],
      "subsets": ["latin", "latin-ext"],
      "category": "sans-serif",
      "url": "https://fonts.googleapis.com/css?family=Roboto"
    }
  ]
}
```

---

## 🎵 Timeline API (Video Editor)

### POST /api/timeline/validate

Validate timeline data before rendering.

**Request:**
```json
{
  "timeline": {
    "duration": 30.0,
    "fps": 30,
    "tracks": [
      {
        "id": "track_video_1",
        "type": "video",
        "clips": [
          {
            "id": "clip_1",
            "asset_id": "asset_123",
            "start": 0.0,
            "end": 5.0,
            "trim_start": 0.0,
            "trim_end": 5.0,
            "effects": ["fade_in"],
            "transitions": {
              "out": { "type": "crossfade", "duration": 1.0 }
            }
          }
        ]
      }
    ]
  }
}
```

**Response:**
```json
{
  "valid": true,
  "errors": [],
  "warnings": [
    "Clip 'clip_1' has no audio track"
  ],
  "total_duration": 30.0,
  "asset_count": 5
}
```

---

## 🔐 Authentication

All API endpoints require JWT authentication.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**JWT Payload:**
```json
{
  "customer_id": "customer_xyz",
  "user_id": "user_123",
  "email": "user@example.com",
  "exp": 1735689600
}
```

---

## 📊 Error Responses

### 400 Bad Request
```json
{
  "status": "error",
  "error": "Invalid request data",
  "details": {
    "field": "dimensions.width",
    "message": "Width must be a positive integer"
  }
}
```

### 401 Unauthorized
```json
{
  "status": "error",
  "error": "Authentication required"
}
```

### 403 Forbidden
```json
{
  "status": "error",
  "error": "Access denied to this resource"
}
```

### 404 Not Found
```json
{
  "status": "error",
  "error": "Design not found"
}
```

### 413 Payload Too Large
```json
{
  "status": "error",
  "error": "File size exceeds limit",
  "max_size": 10485760  // 10MB in bytes
}
```

### 429 Too Many Requests
```json
{
  "status": "error",
  "error": "Rate limit exceeded",
  "retry_after": 60  // seconds
}
```

### 500 Internal Server Error
```json
{
  "status": "error",
  "error": "Internal server error",
  "request_id": "req_abc123"
}
```

---

## 🚀 Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| POST /api/designs | 100 | 1 hour |
| POST /api/assets/upload | 50 | 1 hour |
| POST /api/render/video | 10 | 1 hour |
| POST /api/render/image | 100 | 1 hour |
| GET /api/stock/* | 1000 | 1 hour |

---

## 📦 Webhooks (Optional)

### Render Completion Webhook

When a render job completes, send POST to customer's webhook URL.

**Payload:**
```json
{
  "event": "render.completed",
  "job_id": "job_123",
  "design_id": "design_abc123",
  "status": "completed",
  "url": "https://s3.../export.mp4",
  "format": "mp4",
  "size": 5242880,
  "duration": 30.0,
  "completed_at": "2025-12-31T15:35:00Z"
}
```

---

## 🔧 WebSocket API (Real-time Collaboration - Optional)

### Connection

```javascript
const ws = new WebSocket('wss://api.example.com/ws/design/:designId?token=<jwt>');
```

### Events

**Client → Server:**
```json
{
  "type": "cursor_move",
  "x": 100,
  "y": 200
}
```

```json
{
  "type": "object_update",
  "object_id": "obj_123",
  "properties": {
    "left": 150,
    "top": 250
  }
}
```

**Server → Client:**
```json
{
  "type": "user_joined",
  "user_id": "user_456",
  "name": "Jane Doe",
  "cursor_color": "#ff0000"
}
```

```json
{
  "type": "object_updated",
  "user_id": "user_456",
  "object_id": "obj_123",
  "properties": {
    "left": 150,
    "top": 250
  }
}
```

---

## 📝 API Versioning

All APIs are versioned using URL path:

```
/api/v1/designs
/api/v2/designs  (future)
```

Current version: **v1** (default, can omit `/v1/`)

---

## 🧪 Testing Endpoints

### Health Check

```
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "api_server": "ok",
    "template_service": "ok",
    "design_service": "ok",
    "mongodb": "ok",
    "s3": "ok"
  }
}
```

---

**API Documentation Complete! 🎉**

For interactive API testing, use the Swagger UI at:
```
http://localhost:8080/api/docs
```

