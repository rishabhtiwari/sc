# Phase 4: Quick Start Guide

## 🚀 Getting Started

### 1. Rebuild and Start Services

```bash
# Navigate to project directory
cd /Users/rishabh.tiwari/IdeaProjects/sc

# Rebuild API server with new features
docker-compose up -d --build ichat-api

# Rebuild frontend (optional)
docker-compose up -d --build news-automation-frontend

# Check logs
docker logs ichat-api-server --tail 50 -f
```

---

## 🔐 Authentication

### Login to the System

**Default Credentials:**
- **Admin**: `admin` / `admin123`
- **User**: `user` / `user123`

**Login Page:** http://localhost:3002/login

### Using Authentication in Code

```javascript
// Login
import api from './services/api';

const login = async (username, password) => {
  const response = await api.post('/auth/login', {
    username,
    password
  });
  
  // Store token
  localStorage.setItem('auth_token', response.data.token);
  
  // Set default header for future requests
  api.defaults.headers.common['Authorization'] = `Bearer ${response.data.token}`;
};

// Logout
const logout = () => {
  localStorage.removeItem('auth_token');
  delete api.defaults.headers.common['Authorization'];
};

// Check if authenticated
const isAuthenticated = () => {
  return !!localStorage.getItem('auth_token');
};
```

### Protecting Backend Routes

```python
from routes.auth_routes import token_required, admin_required

# Require authentication
@app.route('/api/protected', methods=['GET'])
@token_required
def protected_route():
    user = request.current_user
    return jsonify({'message': f'Hello {user["username"]}!'})

# Require admin role
@app.route('/api/admin', methods=['GET'])
@admin_required
def admin_route():
    return jsonify({'message': 'Admin access granted'})
```

---

## 🌐 Centralized API Proxy

### Using Frontend Proxy Routes

Instead of calling services directly, use the centralized proxy:

```javascript
// ❌ OLD WAY - Direct service calls
axios.get('http://ichat-news-fetcher:8093/news/fetch/run')
axios.get('http://ichat-iopaint:8096/api/stats')
axios.get('http://ichat-youtube-uploader:8097/api/stats')

// ✅ NEW WAY - Through API server proxy
axios.get('/api/frontend/news-fetcher/news/fetch/run')
axios.get('/api/frontend/watermark/api/stats')
axios.get('/api/frontend/youtube/api/stats')
```

### Check Service Health

```javascript
// Get status of all backend services
const checkServices = async () => {
  const response = await api.get('/api/frontend/services/status');
  console.log(response.data);
  /*
  {
    "news-fetcher": {
      "status": "online",
      "url": "http://ichat-news-fetcher:8093",
      "response_time": 45.2
    },
    "watermark-remover": { ... },
    ...
  }
  */
};

// Get service information
const getServiceInfo = async () => {
  const response = await api.get('/api/frontend/services/info');
  console.log(response.data);
};
```

---

## 🔌 Real-time WebSocket Updates

### Using WebSocket Hooks

```javascript
import { useNewsFetcherUpdates } from '../hooks/useWebSocket';
import RealtimeStatus from '../components/Common/RealtimeStatus';

function NewsFetcherPage() {
  const [status, setStatus] = useState(null);
  
  // Subscribe to real-time updates
  const { isConnected } = useNewsFetcherUpdates((data) => {
    console.log('Update received:', data);
    setStatus(data);
  });
  
  return (
    <div>
      <h1>News Fetcher</h1>
      
      {/* Display real-time status */}
      <RealtimeStatus
        title="Fetch Progress"
        statusData={status}
        isConnected={isConnected}
        icon="📰"
      />
    </div>
  );
}
```

### Available WebSocket Hooks

```javascript
import {
  useNewsFetcherUpdates,
  useAudioGenerationUpdates,
  useVideoGenerationUpdates,
  useYouTubeUploadUpdates,
  useImageCleaningUpdates,
  useNotifications
} from '../hooks/useWebSocket';

// News Fetcher updates
useNewsFetcherUpdates((data) => {
  // data: { status, progress, current_source, articles_fetched, ... }
});

// Audio Generation updates
useAudioGenerationUpdates((data) => {
  // data: { status, progress, current_article, articles_processed, ... }
});

// YouTube Upload updates
useYouTubeUploadUpdates((data) => {
  // data: { status, progress, current_video, videos_uploaded, video_url, ... }
});

// General notifications
useNotifications((data) => {
  // data: { type, title, message, timestamp }
  toast.show(data.message);
});
```

### Broadcasting Updates from Backend

```python
from routes.websocket_routes import (
    broadcast_news_fetch_status,
    broadcast_audio_generation_status,
    broadcast_youtube_upload_status,
    broadcast_general_notification
)

# In your backend service
def fetch_news():
    # Start fetching
    broadcast_news_fetch_status({
        'status': 'running',
        'progress': 0,
        'current_source': 'BBC News',
        'articles_fetched': 0,
        'total_sources': 5,
        'message': 'Starting news fetch...'
    })
    
    # Update progress
    for i, source in enumerate(sources):
        broadcast_news_fetch_status({
            'status': 'running',
            'progress': int((i / len(sources)) * 100),
            'current_source': source.name,
            'articles_fetched': i,
            'total_sources': len(sources),
            'message': f'Fetching from {source.name}...'
        })
        
        # Fetch articles...
    
    # Complete
    broadcast_news_fetch_status({
        'status': 'completed',
        'progress': 100,
        'articles_fetched': len(sources),
        'total_sources': len(sources),
        'message': 'News fetch completed!'
    })
```

### Testing WebSocket Updates

```bash
# Test news fetch update
curl -X POST http://localhost:8080/api/websocket/test/news-fetch \
  -H "Content-Type: application/json" \
  -d '{
    "status": "running",
    "progress": 75,
    "current_source": "Test Source",
    "articles_fetched": 15,
    "total_sources": 20,
    "message": "Fetching articles..."
  }'

# Test notification
curl -X POST http://localhost:8080/api/websocket/test/notification \
  -H "Content-Type: application/json" \
  -d '{
    "type": "success",
    "title": "Test Notification",
    "message": "This is a test notification"
  }'

# Check WebSocket status
curl http://localhost:8080/api/websocket/status
```

---

## 📊 Using Progress Components

### ProgressBar Component

```javascript
import ProgressBar from '../components/Common/ProgressBar';

<ProgressBar
  progress={75}
  status="running"  // 'idle' | 'running' | 'completed' | 'error'
  message="Processing articles..."
  showPercentage={true}
  size="md"  // 'sm' | 'md' | 'lg'
/>
```

### RealtimeStatus Component

```javascript
import RealtimeStatus from '../components/Common/RealtimeStatus';

<RealtimeStatus
  title="News Fetcher"
  statusData={{
    status: 'running',
    progress: 75,
    message: 'Fetching articles...',
    current_source: 'BBC News',
    articles_fetched: 15,
    total_sources: 20
  }}
  isConnected={true}
  icon="📰"
/>
```

---

## 🧪 Testing Checklist

### Authentication
- [ ] Login with admin credentials
- [ ] Login with user credentials
- [ ] Invalid credentials show error
- [ ] Token stored in localStorage
- [ ] Protected routes require authentication
- [ ] Logout clears token

### API Proxy
- [ ] Service status endpoint works
- [ ] Service info endpoint works
- [ ] Proxy routes forward requests correctly
- [ ] File uploads work through proxy
- [ ] Error handling works (timeout, connection error)

### WebSocket
- [ ] WebSocket connects successfully
- [ ] Can join/leave rooms
- [ ] Updates received in real-time
- [ ] Connection indicator shows status
- [ ] Progress bar updates smoothly
- [ ] Test endpoints trigger updates

---

## 🐛 Troubleshooting

### Authentication Issues

**Problem:** "Invalid or expired token"
```javascript
// Solution: Clear localStorage and login again
localStorage.removeItem('auth_token');
localStorage.removeItem('user');
window.location.href = '/login';
```

**Problem:** "CORS error on login"
```python
# Solution: Check CORS configuration in api-server/app.py
CORS(app, origins=['http://localhost:3002'], supports_credentials=True)
```

### WebSocket Issues

**Problem:** "WebSocket not connecting"
```bash
# Check if Socket.IO is initialized
docker logs ichat-api-server | grep "Socket.IO"

# Should see: "✅ Socket.IO initialized successfully"
```

**Problem:** "Updates not received"
```javascript
// Check if joined correct room
const { joinRoom } = useWebSocket();
joinRoom('news-fetcher');

// Check browser console for WebSocket messages
```

### API Proxy Issues

**Problem:** "Service unavailable (503)"
```bash
# Check if backend service is running
docker ps | grep ichat-news-fetcher

# Check service health
curl http://localhost:8080/api/frontend/services/status
```

---

## 📚 API Reference

### Authentication Endpoints
- `POST /api/auth/login` - Login
- `GET /api/auth/verify` - Verify token
- `POST /api/auth/logout` - Logout
- `GET /api/auth/me` - Get current user
- `GET /api/auth/users` - Get all users (admin)

### Frontend Proxy Endpoints
- `* /api/frontend/news-fetcher/*` - News Fetcher proxy
- `* /api/frontend/watermark/*` - Watermark Remover proxy
- `* /api/frontend/youtube/*` - YouTube Uploader proxy
- `* /api/frontend/voice/*` - Voice Generator proxy
- `* /api/frontend/audio/*` - Audio Generation proxy
- `GET /api/frontend/services/status` - Service health
- `GET /api/frontend/services/info` - Service information

### WebSocket Endpoints
- `POST /api/websocket/test/*` - Test update broadcast
- `GET /api/websocket/status` - WebSocket status

### WebSocket Events
- `news_fetch_update` - News fetch progress
- `audio_generation_update` - Audio generation progress
- `video_generation_update` - Video generation progress
- `youtube_upload_update` - YouTube upload progress
- `image_cleaning_update` - Image cleaning progress
- `notification` - General notifications

---

## 🎉 You're All Set!

Phase 4 is now complete with:
- ✅ Centralized API routing
- ✅ JWT authentication
- ✅ Real-time WebSocket updates
- ✅ Progress tracking components

**Next:** Start using these features in your frontend pages!

