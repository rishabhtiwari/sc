# iChat API Server v2.0

A professionally structured Flask API server for the iChat application with proper MVC architecture.

## 🏗️ Architecture

The API server follows a clean MVC (Model-View-Controller) pattern:

```
api-server/
├── app.py                    # Main application entry point
├── config/
│   ├── __init__.py
│   └── app_config.py        # Configuration management
├── controllers/
│   ├── __init__.py
│   ├── chat_controller.py   # Chat business logic
│   └── health_controller.py # Health check logic
├── handlers/
│   ├── __init__.py
│   ├── chat_handler.py      # HTTP request/response handling
│   └── health_handler.py    # Health endpoint handling
├── routes/
│   ├── __init__.py
│   ├── chat_routes.py       # Chat URL routing
│   └── health_routes.py     # Health URL routing
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## 🚀 Quick Start

### Option 1: Docker (Recommended)

#### Using Docker Run Script
```bash
cd api-server

# Build and run
./docker-run.sh build
./docker-run.sh run

# Check status
./docker-run.sh status
./docker-run.sh health
```

#### Using Docker Compose
```bash
cd api-server
docker-compose up -d
```

#### Manual Docker Commands
```bash
cd api-server

# Build image
docker build -t ichat-api-server .

# Run container
docker run -d -p 8080:8080 --name ichat-api-server ichat-api-server
```

### Option 2: Local Python

#### 1. Install Dependencies
```bash
cd api-server
pip install -r requirements.txt
```

#### 2. Run the Server
```bash
python3 app.py
```

### 3. Test the API
```bash
# Health check
curl http://localhost:8080/api/health

# Send a chat message
curl -X POST http://localhost:8080/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!", "client": "test"}'
```

## 📡 API Endpoints

### Chat Endpoints
- **POST /api/chat** - Send chat message and get response
- **GET /api/chat/stats** - Get chat statistics
- **GET /api/chat/test** - Test chat endpoint connectivity

### Health & Monitoring
- **GET /api/health** - Basic health check
- **GET /api/status** - Detailed system status
- **GET /api/ping** - Simple connectivity test
- **GET /api/version** - API version information

### Root
- **GET /** - API information and available endpoints

## 🔧 Configuration

Configure the server using environment variables:

```bash
# Server settings
export FLASK_HOST=0.0.0.0
export FLASK_PORT=8080
export FLASK_DEBUG=True

# Chat settings
export CHAT_RESPONSE_DELAY=0.5
export MAX_MESSAGE_LENGTH=1000

# Security
export SECRET_KEY=your-secret-key-here
```

## 🏛️ Architecture Benefits

### **Separation of Concerns**
- **Routes**: Handle URL routing and HTTP methods
- **Handlers**: Process HTTP requests/responses
- **Controllers**: Contain business logic
- **Config**: Centralized configuration management

### **Scalability**
- Easy to add new endpoints
- Modular structure for team development
- Clear separation makes testing easier
- Configuration-driven behavior

### **Maintainability**
- Clean code organization
- Single responsibility principle
- Easy to debug and modify
- Professional Flask patterns

## 🐳 Docker Management

### Docker Run Script Commands
```bash
./docker-run.sh build     # Build Docker image
./docker-run.sh run       # Run container
./docker-run.sh stop      # Stop container
./docker-run.sh restart   # Restart container
./docker-run.sh logs      # Show logs
./docker-run.sh shell     # Open shell in container
./docker-run.sh clean     # Remove container and image
./docker-run.sh status    # Show container status
./docker-run.sh health    # Check API health
```

### Docker Compose Commands
```bash
docker-compose up -d      # Start services in background
docker-compose down       # Stop and remove services
docker-compose logs -f    # Follow logs
docker-compose ps         # Show running services
```

### Docker Benefits
- **Consistent Environment** - Same runtime across all systems
- **Easy Deployment** - Single container with all dependencies
- **Isolation** - No conflicts with system Python packages
- **Scalability** - Easy to scale with orchestration tools
- **Production Ready** - Optimized for production deployment

## 🧪 Testing

```bash
# Install test dependencies
pip install pytest pytest-flask

# Run tests (when implemented)
pytest tests/
```

## 🎯 Production Ready

This API server is built with production-grade features:

- **Professional MVC Architecture** - Clean separation of concerns
- **Comprehensive Error Handling** - Structured error responses
- **System Monitoring** - Built-in health checks and performance metrics
- **Configuration Management** - Environment-based settings
- **Scalable Design** - Easy to extend and maintain
- **Team Development Ready** - Modular structure for collaboration
