# Embedding Service

A microservice for document processing, text extraction, chunking, and vector storage for RAG (Retrieval-Augmented Generation) functionality.

## Overview

The Embedding Service handles the complete document processing pipeline:

1. **Document Upload** - Accepts various document formats
2. **OCR Processing** - Extracts text using the OCR service
3. **Text Chunking** - Splits text into manageable chunks with overlap
4. **Vector Storage** - Stores chunks with embeddings in the Vector DB
5. **Document Management** - Provides APIs for retrieval and deletion

## Features

- ✅ **Multi-format Support** - Programming languages, PDF, DOC, DOCX, images, configuration files, and more
- ✅ **OCR Integration** - Seamless text extraction via OCR service
- ✅ **Smart Chunking** - Configurable chunk size with overlap
- ✅ **Vector Storage** - Integration with Vector DB service
- ✅ **Client-side Storage** - Documents stored on client, only embeddings on server
- ✅ **RESTful API** - Clean REST endpoints for all operations
- ✅ **Docker Support** - Containerized deployment
- ✅ **Health Monitoring** - Built-in health checks
- ✅ **Error Handling** - Comprehensive error handling and cleanup

## Architecture

```
Client Document → Embedding Service → OCR Service → Text Extraction
                       ↓
                 Text Chunking → Vector DB → Embeddings Storage
                       ↓
                 Return document_id → Client stores document locally
```

## API Endpoints

### Document Processing
- `POST /embed/document` - Process and embed a document
- `GET /embed/document/{document_id}/chunks` - Get all chunks for a document
- `DELETE /embed/document/{document_id}` - Delete document chunks

### Search
- `POST /embed/search` - Search across documents

### Health
- `GET /health` - Service health check

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `HOST` | `0.0.0.0` | Server host |
| `PORT` | `8085` | Server port |
| `OCR_SERVICE_URL` | `http://localhost:8082` | OCR service URL |
| `VECTOR_DB_URL` | `http://localhost:8084` | Vector DB service URL |
| `MAX_FILE_SIZE_MB` | `50` | Maximum file size |
| `CHUNK_SIZE` | `1000` | Text chunk size |
| `CHUNK_OVERLAP` | `200` | Chunk overlap size |
| `MIN_CHUNK_SIZE` | `100` | Minimum chunk size |
| `MAX_CHUNKS_PER_DOCUMENT` | `1000` | Maximum chunks per document |
| `OCR_TIMEOUT` | `180` | OCR service timeout (seconds) |
| `VECTOR_DB_TIMEOUT` | `60` | Vector DB timeout (seconds) |

## Quick Start

### Using Docker Compose

```bash
# Build and start the service
docker-compose up --build

# Check health
curl http://localhost:8085/health
```

### Manual Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export OCR_SERVICE_URL=http://localhost:8082
export VECTOR_DB_URL=http://localhost:8084

# Run the service
python app.py
```

## Usage Examples

### Process a Document

```bash
curl -X POST http://localhost:8085/embed/document \
  -F "file=@document.pdf"
```

Response:
```json
{
  "status": "success",
  "document_id": "doc_abc123def456",
  "filename": "document.pdf",
  "chunks_created": 15,
  "chunks_stored": 15,
  "text_length": 12450,
  "timestamp": 1703123456789
}
```

### Get Document Chunks

```bash
curl http://localhost:8085/embed/document/doc_abc123def456/chunks
```

### Search Documents

```bash
curl -X POST http://localhost:8085/embed/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning algorithms",
    "limit": 5
  }'
```

### Delete Document

```bash
curl -X DELETE http://localhost:8085/embed/document/doc_abc123def456
```

## Dependencies

- **OCR Service** (port 8082) - For text extraction
- **Vector DB Service** (port 8084) - For embedding storage

## Development

### Project Structure

```
embedding-service/
├── app.py                 # Main application
├── config/
│   └── settings.py        # Configuration
├── services/
│   └── embedding_service.py # Core service logic
├── routes/
│   └── embedding_routes.py  # API routes
├── utils/
│   └── logger.py          # Logging utilities
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker configuration
├── docker-compose.yml    # Docker Compose setup
└── README.md            # This file
```

### Error Handling

The service includes comprehensive error handling:
- File validation and size limits
- OCR service connectivity
- Vector DB connectivity
- Automatic cleanup on failures
- Detailed error logging

## Monitoring

- Health check endpoint: `GET /health`
- Structured logging with timestamps
- Docker health checks
- Service dependency monitoring
