# Vector Database Service

A ChromaDB-based vector database service for storing and retrieving document embeddings, designed for RAG (Retrieval-Augmented Generation) applications.

## 🚀 Features

- **ChromaDB Integration**: Persistent vector storage with automatic embedding generation
- **Sentence Transformers**: Built-in embedding model (all-MiniLM-L6-v2)
- **RESTful API**: Complete CRUD operations for documents and collections
- **Semantic Search**: Vector similarity search with metadata filtering
- **Docker Support**: Containerized deployment with health checks
- **Scalable Architecture**: Designed for integration with LLM services

## 📋 API Endpoints

### Core Endpoints

- `GET /health` - Service health check
- `GET /vector/collections` - Get collection information
- `POST /vector/documents` - Add documents to vector database
- `POST /vector/search` - Search for similar documents
- `DELETE /vector/documents` - Delete documents by IDs
- `POST /vector/embeddings` - Generate embeddings for text

### Health Check

```bash
curl http://localhost:8084/health
```

### Add Documents

```bash
curl -X POST http://localhost:8084/vector/documents \
  -H "Content-Type: application/json" \
  -d '{
    "documents": ["This is a sample document", "Another document"],
    "metadatas": [{"source": "file1.txt"}, {"source": "file2.txt"}],
    "ids": ["doc1", "doc2"]
  }'
```

### Search Documents

```bash
curl -X POST http://localhost:8084/vector/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "sample document",
    "n_results": 5,
    "where": {"source": "file1.txt"}
  }'
```

### Delete Documents

```bash
curl -X DELETE http://localhost:8084/vector/documents \
  -H "Content-Type: application/json" \
  -d '{
    "ids": ["doc1", "doc2"]
  }'
```

### Generate Embeddings

```bash
curl -X POST http://localhost:8084/vector/embeddings \
  -H "Content-Type: application/json" \
  -d '{
    "texts": ["Hello world", "Another text"]
  }'
```

## 🔧 Configuration

### Default Settings

- **Host**: 0.0.0.0
- **Port**: 8084
- **Embedding Model**: all-MiniLM-L6-v2 (384 dimensions)
- **Chunk Size**: 1000 characters
- **Chunk Overlap**: 200 characters
- **Default Search Results**: 5
- **Max Search Results**: 50

### Customization

Edit `config/settings.py` to customize:

```python
# Server configuration
HOST = '0.0.0.0'
PORT = 8084

# Embedding configuration
EMBEDDING_MODEL = 'all-MiniLM-L6-v2'
EMBEDDING_DIMENSION = 384

# Search configuration
DEFAULT_SEARCH_RESULTS = 5
MAX_SEARCH_RESULTS = 50
```

## 🐳 Docker Deployment

### Build and Run

```bash
# Build the image
docker build -t vector-db-service .

# Run the container
docker run -d \
  --name ichat-vector-db \
  -p 8084:8084 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  vector-db-service
```

### Using Docker Compose

```bash
# Start the service
docker-compose up -d

# Check logs
docker-compose logs -f vector-db

# Stop the service
docker-compose down
```

## 📁 Project Structure

```
llm/vector-db/
├── app.py                 # Main Flask application
├── Dockerfile            # Docker configuration
├── docker-compose.yml    # Docker Compose configuration
├── requirements.txt      # Python dependencies
├── README.md             # This file
├── config/
│   └── settings.py       # Configuration settings
├── services/
│   └── vector_service.py # Core vector database operations
├── routes/
│   └── vector_routes.py  # API route definitions
└── utils/
    └── logger.py         # Logging utilities
```

## 🔗 Integration

This service is designed to integrate with:

- **LLM Service**: For RAG-enhanced text generation
- **API Server**: For document processing and chat routing
- **OCR Service**: For document text extraction and indexing

## 📊 Performance

- **Embedding Generation**: ~100ms per document (CPU)
- **Search Latency**: ~10ms for similarity search
- **Storage**: Persistent ChromaDB with automatic indexing
- **Memory Usage**: ~500MB base + model size (~100MB)

## 🛠️ Development

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the service
python app.py
```

### Testing

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests
pytest tests/
```

## 🔒 Security

- Non-root user execution in Docker
- Input validation for all endpoints
- Rate limiting ready (can be added via middleware)
- CORS enabled for cross-origin requests
