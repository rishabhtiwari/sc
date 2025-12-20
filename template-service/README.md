# Template Service

Video template management and resolution service for the news automation platform.

## Overview

The Template Service is a standalone microservice that manages video templates and resolves them with customer-specific configurations and article variables. It follows industry-standard approaches (similar to Canva, Shotstack) using JSON-based templates with variable substitution.

## Architecture

```
┌─────────────────┐
│ Video Generator │
│   (Consumer)    │
└────────┬────────┘
         │ HTTP Request
         ▼
┌─────────────────┐      ┌──────────┐
│ Template Service│◄─────┤ MongoDB  │
│   (Provider)    │      │ (Config) │
└────────┬────────┘      └──────────┘
         │
         ▼
┌─────────────────┐
│ JSON Templates  │
│  (Files)        │
└─────────────────┘
```

## Features

- **Template Management**: Load, list, and cache video templates
- **Variable Resolution**: Substitute `{{placeholders}}` with actual values
- **Customer Configuration**: Merge customer-specific overrides
- **3-Layer Merging**: Template defaults → Customer config → Article variables
- **REST API**: Simple HTTP API for template operations
- **Caching**: In-memory template caching for performance

## API Endpoints

### List Templates
```http
GET /api/templates?category=news
```

Response:
```json
{
  "status": "success",
  "count": 2,
  "templates": [
    {
      "template_id": "modern_news_v1",
      "name": "Modern News",
      "category": "news",
      "description": "Professional news video with banner, ticker, and effects",
      "version": "1.0.0"
    }
  ]
}
```

### Get Template
```http
GET /api/templates/modern_news_v1
```

### Resolve Template (Main Endpoint)
```http
POST /api/templates/resolve
Content-Type: application/json

{
  "customer_id": "customer_123",
  "template_type": "long_video",
  "variables": {
    "title": "Breaking News",
    "background_image": "/app/public/article_123/bg.png",
    "audio_file": "/app/public/article_123/audio.wav"
  }
}
```

Response:
```json
{
  "status": "success",
  "template_id": "modern_news_v1",
  "resolved_template": {
    "layers": [...],
    "audio": {...}
  }
}
```

## Template Structure

Templates are JSON files with the following structure:

```json
{
  "template_id": "modern_news_v1",
  "name": "Modern News",
  "version": "1.0.0",
  "category": "news",
  "layers": [
    {
      "id": "background",
      "type": "image",
      "source": "{{background_image}}",
      "effects": [{"type": "ken_burns"}]
    }
  ],
  "variables": {
    "background_image": {
      "type": "image",
      "required": true
    }
  }
}
```

## Template Categories

- **news**: Long-form news videos (16:9)
- **shorts**: Vertical short videos (9:16)
- **ecommerce**: Product showcase videos

## Environment Variables

```bash
# Server
FLASK_HOST=0.0.0.0
FLASK_PORT=5000

# MongoDB
MONGODB_URL=mongodb://user:pass@host:27017/news

# Templates
TEMPLATE_DIR=/app/templates
TEMPLATE_CACHE_ENABLED=true
TEMPLATE_CACHE_TTL=300

# Defaults
DEFAULT_LONG_VIDEO_TEMPLATE=modern_news_v1
DEFAULT_SHORTS_TEMPLATE=vertical_overlay_v1
```

## Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run the service
python app.py
```

## Docker

```bash
# Build
docker build -t template-service .

# Run
docker run -p 5000:5000 \
  -e MONGODB_URL=mongodb://localhost:27017/news \
  template-service
```

## Adding New Templates

1. Create JSON file in `templates/{category}/{template_id}.json`
2. Define layers, effects, and variables
3. Template is automatically available via API

## Integration Example

```python
# In video-generator service
import requests

response = requests.post('http://template-service:5000/api/templates/resolve', json={
    'customer_id': customer_id,
    'template_type': 'long_video',
    'variables': {
        'title': article['title'],
        'background_image': bg_path,
        'audio_file': audio_path
    }
})

resolved_template = response.json()['resolved_template']
# Use resolved_template to build video
```

