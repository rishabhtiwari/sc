# Phase 4: API Server Integration - Implementation Guide

## Overview
Phase 4 adds centralized API routing, authentication, and real-time WebSocket updates to the News Automation System.

---

## ✅ Task 4.1: Frontend API Routes in API Server

### Files Created

#### 1. **api-server/routes/frontend_routes.py** (~280 lines)
Centralized API proxy for all frontend services.

**Features:**
- Generic proxy function for forwarding requests
- Proxy routes for all backend services:
  - `/api/frontend/news-fetcher/*` → News Fetcher service
  - `/api/frontend/watermark/*` → IOPaint service
  - `/api/frontend/youtube/*` → YouTube Uploader service
  - `/api/frontend/voice/*` → Voice Generator service
  - `/api/frontend/audio/*` → Audio Generation service
- Service status endpoints:
  - `GET /api/frontend/services/status` - Health check for all services
  - `GET /api/frontend/services/info` - Service information
- File upload support for image processing
- Request timeout handling (30 seconds)
- Error handling for connection errors and timeouts

**Usage Example:**
```javascript
// Instead of calling service directly:
// axios.get('http://ichat-news-fetcher:8093/news/fetch/run')

// Now call through API server:
axios.get('/api/frontend/news-fetcher/news/fetch/run')
```

---

## ✅ Task 4.2: Authentication System

### Backend Files Created

#### 1. **api-server/routes/auth_routes.py** (~300 lines)
JWT-based authentication system.

**Features:**
- User authentication with JWT tokens
- Token expiration (24 hours)
- Password hashing with werkzeug
- Role-based access control (admin, user)
- Decorators for protected routes:
  - `@token_required` - Requires valid JWT token
  - `@admin_required` - Requires admin role

**API Endpoints:**
- `POST /api/auth/login` - User login
- `GET /api/auth/verify` - Verify token validity
- `POST /api/auth/logout` - User logout
- `GET /api/auth/me` - Get current user info
- `GET /api/auth/users` - Get all users (admin only)
- `GET /api/auth/protected` - Example protected route
- `GET /api/auth/admin-only` - Example admin-only route

**Default Users:**
```
Admin: username=admin, password=admin123
User:  username=user, password=user123
```

**Request/Response Example:**
```bash
# Login
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Response
{
  "success": true,
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "username": "admin",
    "role": "admin",
    "email": "admin@newsautomation.com"
  }
}

# Use token in subsequent requests
curl -X GET http://localhost:8080/api/auth/me \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

### Frontend Files Created

#### 2. **frontend-server/src/components/Auth/Login.jsx** (~130 lines)
Login page component.

**Features:**
- Username/password form
- Error handling and display
- Loading state
- Token storage in localStorage
- Automatic redirect after login
- Demo credentials display

#### 3. **frontend-server/src/components/Common/ProgressBar.jsx** (~80 lines)
Reusable progress bar component for real-time updates.

**Features:**
- Configurable size (sm, md, lg)
- Status-based colors (idle, running, completed, error)
- Percentage display
- Animated shimmer effect for running status
- Optional message display

#### 4. **frontend-server/src/components/Common/RealtimeStatus.jsx** (~160 lines)
Real-time status panel component.

**Features:**
- WebSocket connection indicator
- Status badge (idle, running, completed, error)
- Progress bar integration
- Dynamic details display
- Support for different job types (news fetch, audio generation, etc.)

---

## ✅ Task 4.3: WebSocket Support for Real-time Updates

### Backend Files Created

#### 1. **api-server/routes/websocket_routes.py** (~300 lines)
Socket.IO implementation for real-time updates.

**Features:**
- Socket.IO server with Flask integration
- Room-based updates for different job types:
  - `news-fetcher` - News fetching updates
  - `audio-generation` - Audio generation updates
  - `video-generation` - Video generation updates
  - `youtube-upload` - YouTube upload updates
  - `image-cleaning` - Image cleaning updates
- Broadcast functions for each job type
- Test endpoints for triggering updates
- Connection/disconnection handling
- Ping/pong for connection health

**WebSocket Events:**
- `connect` - Client connected
- `disconnect` - Client disconnected
- `join_room` - Join a specific room
- `leave_room` - Leave a room
- `ping` / `pong` - Connection health check
- `news_fetch_update` - News fetch progress
- `audio_generation_update` - Audio generation progress
- `video_generation_update` - Video generation progress
- `youtube_upload_update` - YouTube upload progress
- `image_cleaning_update` - Image cleaning progress
- `notification` - General notifications

**Test Endpoints:**
- `POST /api/websocket/test/news-fetch` - Test news fetch update
- `POST /api/websocket/test/audio-generation` - Test audio generation update
- `POST /api/websocket/test/youtube-upload` - Test YouTube upload update
- `POST /api/websocket/test/notification` - Test notification
- `GET /api/websocket/status` - WebSocket server status

**Usage Example:**
```python
# In your backend service, broadcast an update:
from routes.websocket_routes import broadcast_news_fetch_status

broadcast_news_fetch_status({
    'status': 'running',
    'progress': 50,
    'current_source': 'BBC News',
    'articles_fetched': 10,
    'total_sources': 5,
    'message': 'Fetching articles from BBC News...'
})
```

### Frontend Files Created

#### 2. **frontend-server/src/hooks/useWebSocket.js** (~280 lines)
Custom React hooks for WebSocket connection.

**Features:**
- Main `useWebSocket` hook with full control
- Specialized hooks for each job type:
  - `useNewsFetcherUpdates`
  - `useAudioGenerationUpdates`
  - `useVideoGenerationUpdates`
  - `useYouTubeUploadUpdates`
  - `useImageCleaningUpdates`
  - `useNotifications`
- Auto-reconnection support
- Room management (join/leave)
- Event subscription/unsubscription
- Connection state tracking

**Usage Example:**
```javascript
import { useNewsFetcherUpdates } from '../hooks/useWebSocket';

function NewsFetcherPage() {
  const [status, setStatus] = useState(null);
  
  // Subscribe to news fetcher updates
  const { isConnected } = useNewsFetcherUpdates((data) => {
    console.log('News fetch update:', data);
    setStatus(data);
  });
  
  return (
    <div>
      <RealtimeStatus
        title="News Fetcher"
        statusData={status}
        isConnected={isConnected}
        icon="📰"
      />
    </div>
  );
}
```

---

## 📦 Dependencies Added

### Backend (api-server/requirements.txt)
```
flask-socketio==5.3.4
python-socketio==5.9.0
eventlet==0.33.3
PyJWT==2.8.0
werkzeug==2.3.7
```

### Frontend (frontend-server/package.json)
```json
{
  "dependencies": {
    "socket.io-client": "^4.7.2"  // Already present
  }
}
```

---

## 🔧 Configuration Changes

### 1. **api-server/app.py**
- Imported new blueprints: `frontend_bp`, `websocket_bp`, `auth_bp`
- Registered new blueprints with `/api` prefix
- Initialized Socket.IO with `init_socketio(app)`
- Changed from `app.run()` to `socketio.run()` for WebSocket support
- Updated endpoint documentation in home route

### 2. **docker-compose.yml** (No changes needed)
- Existing configuration already supports WebSocket
- Port 8080 already exposed for API server

---

## 🚀 Deployment Instructions

### 1. Rebuild API Server
```bash
cd /Users/rishabh.tiwari/IdeaProjects/sc
docker-compose up -d --build ichat-api
```

### 2. Rebuild Frontend (if needed)
```bash
docker-compose up -d --build news-automation-frontend
```

### 3. Verify Services
```bash
# Check API server logs
docker logs ichat-api-server --tail 50

# Check frontend logs
docker logs news-automation-frontend --tail 50
```

---

## 🧪 Testing

### Test Authentication
```bash
# Login
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Verify token (replace TOKEN with actual token)
curl -X GET http://localhost:8080/api/auth/verify \
  -H "Authorization: Bearer TOKEN"
```

### Test Frontend Proxy
```bash
# Get service status
curl http://localhost:8080/api/frontend/services/status

# Get service info
curl http://localhost:8080/api/frontend/services/info
```

### Test WebSocket
```bash
# Get WebSocket status
curl http://localhost:8080/api/websocket/status

# Trigger test update
curl -X POST http://localhost:8080/api/websocket/test/news-fetch \
  -H "Content-Type: application/json" \
  -d '{"status": "running", "progress": 75, "message": "Test update"}'
```

---

## 📊 Phase 4 Summary

| Component | Status | Files Created | Lines of Code |
|-----------|--------|---------------|---------------|
| **Task 4.1: Frontend API Routes** | ✅ Complete | 1 | ~280 |
| **Task 4.2: Authentication** | ✅ Complete | 3 | ~430 |
| **Task 4.3: WebSocket Support** | ✅ Complete | 3 | ~660 |
| **TOTAL** | ✅ **COMPLETE** | **7** | **~1,370** |

---

## 🎯 Next Steps

1. **Rebuild Services**: Run `docker-compose up -d --build ichat-api` to apply changes
2. **Test Authentication**: Try logging in at http://localhost:3002/login
3. **Test WebSocket**: Monitor real-time updates in browser console
4. **Update Frontend Routes**: Optionally update frontend to use centralized proxy routes
5. **Add Protected Routes**: Apply `@token_required` decorator to sensitive endpoints

---

## 🔐 Security Notes

⚠️ **IMPORTANT**: Change default credentials in production!

1. Update `JWT_SECRET_KEY` in `auth_routes.py`
2. Change default user passwords
3. Use environment variables for secrets
4. Enable HTTPS in production
5. Implement rate limiting for login endpoint
6. Add CORS restrictions for production

---

## 📝 Additional Features to Consider

- [ ] Password reset functionality
- [ ] User registration
- [ ] Session management
- [ ] Token refresh mechanism
- [ ] OAuth integration (Google, GitHub)
- [ ] Two-factor authentication
- [ ] Audit logging
- [ ] Rate limiting
- [ ] IP whitelisting


