# 📄 **Paddle OCR Document Converter Service**

A professional OCR (Optical Character Recognition) microservice built with PaddleOCR for converting documents and images to text.

## 🚀 **Features**

### **Document Support**
- **Images**: PNG, JPG, JPEG, BMP, TIFF, WEBP
- **Documents**: PDF (multi-page), DOCX
- **Output Formats**: Plain text, JSON, Markdown

### **OCR Capabilities**
- **Multi-language Support**: English, Chinese, French, German, Korean, Japanese
- **High Accuracy**: Powered by PaddleOCR 2.7.0.3
- **Batch Processing**: Multi-page PDF support
- **Confidence Scoring**: Quality metrics for extracted text

### **Production Ready**
- **Docker Containerized**: Easy deployment and scaling
- **Health Monitoring**: Built-in health checks and status endpoints
- **Error Handling**: Comprehensive error reporting
- **Security**: Non-root container execution

## 🏗️ **Architecture**

```
ocr-service/
├── app.py                    # Main Flask application
├── config/
│   └── ocr_config.py        # Configuration management
├── services/
│   ├── ocr_service.py       # PaddleOCR wrapper
│   └── document_service.py  # Document processing logic
├── Dockerfile               # Container definition
├── docker-run.sh           # Container management script
└── requirements.txt        # Python dependencies
```

## 🚀 **Quick Start**

### **Option 1: Docker (Recommended)**

1. **Build and run the service:**
   ```bash
   cd ocr-service
   ./docker-run.sh build
   ./docker-run.sh run
   ```

2. **Check service health:**
   ```bash
   curl http://localhost:8081/health
   ```

3. **Convert a document:**
   ```bash
   curl -X POST -F "file=@document.pdf" \
        -F "language=en" \
        -F "format=text" \
        http://localhost:8081/convert
   ```

### **Option 2: Docker Compose (Full Stack)**

Run both API server and OCR service together:

```bash
# From project root
docker-compose up -d

# Check both services
curl http://localhost:8080/api/health  # Main API
curl http://localhost:8081/health      # OCR Service
```

## 📡 **API Endpoints**

### **POST /convert**
Convert document to text using OCR.

**Parameters:**
- `file` (required): Document file to process
- `language` (optional): OCR language (default: 'en')
- `format` (optional): Output format ('text', 'json', 'markdown')

**Example:**
```bash
curl -X POST \
  -F "file=@sample.pdf" \
  -F "language=en" \
  -F "format=json" \
  http://localhost:8081/convert
```

**Response:**
```json
{
  "status": "success",
  "text": "Extracted text content...",
  "confidence": 0.95,
  "filename": "sample.pdf",
  "file_type": "pdf",
  "language": "en",
  "pages_processed": 3,
  "timestamp": 1640995200000
}
```

### **GET /health**
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "message": "OCR service is operational",
  "ocr_engine": "PaddleOCR",
  "supported_languages": ["en", "ch", "fr", "german", "korean", "japan"]
}
```

### **GET /formats**
Get supported file formats and languages.

### **GET /status**
Detailed service status with system metrics.

## 🌐 **Supported Languages**

| Code | Language |
|------|----------|
| `en` | English |
| `ch` | Chinese |
| `fr` | French |
| `german` | German |
| `korean` | Korean |
| `japan` | Japanese |

## 🔧 **Configuration**

### **Environment Variables**

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_HOST` | `0.0.0.0` | Server host |
| `FLASK_PORT` | `8081` | Server port |
| `OCR_DEFAULT_LANGUAGE` | `en` | Default OCR language |
| `OCR_USE_GPU` | `false` | Enable GPU acceleration |
| `MAX_FILE_SIZE` | `10485760` | Max file size (10MB) |

### **Docker Environment**
```bash
docker run -d \
  -p 8081:8081 \
  -e OCR_DEFAULT_LANGUAGE=en \
  -e OCR_USE_GPU=false \
  -e MAX_FILE_SIZE=10485760 \
  ichat-ocr-service
```

## 🛠️ **Development**

### **Local Setup**
```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
python app.py
```

### **Testing**
```bash
# Test with sample image
curl -X POST -F "file=@test.png" http://localhost:8081/convert

# Test health endpoint
curl http://localhost:8081/health
```

## 🐳 **Docker Commands**

The `docker-run.sh` script provides convenient commands:

```bash
./docker-run.sh build     # Build Docker image
./docker-run.sh run       # Run container
./docker-run.sh stop      # Stop container
./docker-run.sh restart   # Restart container
./docker-run.sh logs      # Show logs
./docker-run.sh shell     # Open container shell
./docker-run.sh health    # Check service health
./docker-run.sh status    # Show container status
./docker-run.sh clean     # Clean up resources
```

## 🔗 **Integration with iChat**

The OCR service integrates seamlessly with the main iChat API server:

1. **Microservice Architecture**: Runs as separate container on port 8081
2. **Network Communication**: Connected via Docker network
3. **Health Monitoring**: Both services monitor each other's health
4. **Scalable**: Can be scaled independently based on OCR workload

## 📊 **Performance**

- **Image Processing**: ~1-3 seconds per image
- **PDF Processing**: ~2-5 seconds per page
- **Memory Usage**: ~500MB-1GB depending on document size
- **Concurrent Requests**: Supports multiple simultaneous conversions

## 🔒 **Security**

- **Non-root Execution**: Container runs as `ocruser`
- **File Size Limits**: Configurable maximum file size
- **Temporary Files**: Automatic cleanup of processed files
- **Input Validation**: Comprehensive file format validation

## 🚨 **Troubleshooting**

### **Common Issues**

1. **OCR Service Not Starting**
   ```bash
   # Check logs
   ./docker-run.sh logs
   
   # Verify dependencies
   docker exec -it ichat-ocr-service pip list
   ```

2. **Low OCR Accuracy**
   - Try different language settings
   - Ensure image quality is good
   - Check confidence scores in response

3. **Memory Issues**
   - Reduce concurrent processing
   - Increase Docker memory limits
   - Process smaller files

Your OCR service is now ready to convert documents and images to text with high accuracy! 🎉
