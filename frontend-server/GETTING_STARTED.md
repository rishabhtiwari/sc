# Getting Started with News Automation Frontend

Welcome! This guide will help you get started with the News Automation Frontend Server.

## 🎯 What is This?

The News Automation Frontend is a **unified web interface** for managing your entire news automation pipeline:

```
News Fetching → LLM Enrichment → Audio Generation → Video Creation → YouTube Upload
```

All controlled from one beautiful, modern web interface.

## 🚀 Quick Start (5 Minutes)

### Step 1: Start the Server
```bash
# From project root
cd /Users/rishabh.tiwari/IdeaProjects/sc
docker-compose up -d news-automation-frontend
```

### Step 2: Open in Browser
```
http://localhost:3002
```

### Step 3: Explore
- 📊 **Dashboard** - See overview and stats
- 📰 **News Fetcher** - Manage news sources (coming in Phase 2)
- 🖼️ **Image Cleaning** - Remove watermarks (coming in Phase 2)
- 🎤 **Voice & LLM** - Configure prompts (coming in Phase 3)
- 📺 **YouTube** - Upload videos (coming in Phase 2)

## 📋 Prerequisites

- Docker and Docker Compose installed
- API Server running (`ichat-api-server` on port 8080)
- MongoDB running (`ichat-mongodb`)

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Browser (localhost:3002)                  │
│                                                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │ Dashboard  │  │News Fetcher│  │   Voice    │  ...       │
│  └────────────┘  └────────────┘  └────────────┘            │
│                                                              │
│                    React App (Vite)                          │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           │ /api/* requests
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              Express Server (API Proxy)                      │
│                                                              │
│  Forwards all /api/* requests to API Server                 │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           │ Proxied requests
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              API Server (ichat-api-server:8080)              │
│                                                              │
│  Handles all business logic and database operations         │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Project Structure (Simplified)

```
frontend-server/
├── src/
│   ├── components/      # UI components
│   ├── pages/           # Page components
│   ├── services/        # API calls
│   ├── hooks/           # Custom hooks
│   ├── utils/           # Helper functions
│   └── config/          # Constants
├── server.js            # Express server
├── Dockerfile           # Docker build
└── package.json         # Dependencies
```

## 🎨 Key Features

### 1. **Modern UI**
- Clean, professional design
- Responsive (works on mobile, tablet, desktop)
- Smooth animations
- Intuitive navigation

### 2. **Modular Code**
- Easy to add new features
- Reusable components
- Clean separation of concerns
- Well-documented

### 3. **Developer-Friendly**
- Fast hot reload (Vite)
- Clear folder structure
- Comprehensive docs
- Docker-first approach

## 🛠️ Common Tasks

### View Logs
```bash
docker logs -f news-automation-frontend
```

### Restart Service
```bash
docker-compose restart news-automation-frontend
```

### Rebuild After Code Changes
```bash
docker-compose up -d --build news-automation-frontend
```

### Stop Service
```bash
docker-compose stop news-automation-frontend
```

## 📚 Documentation

- **[README.md](./README.md)** - Quick start and development guide
- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - Detailed architecture (60+ sections)
- **[QUICK_REFERENCE.md](./QUICK_REFERENCE.md)** - Code examples and patterns
- **[PHASE1_COMPLETE.md](./PHASE1_COMPLETE.md)** - What was built in Phase 1

## 🎓 Learning Path

### For Users
1. Read this file (GETTING_STARTED.md)
2. Start the server and explore the UI
3. Check out the Dashboard page

### For Developers
1. Read GETTING_STARTED.md (this file)
2. Read ARCHITECTURE.md for detailed design
3. Read QUICK_REFERENCE.md for code examples
4. Explore the codebase starting from `src/App.jsx`

## 🔧 Development Workflow

### Adding a New Feature

1. **Create Service Function** (if needed)
```javascript
// src/services/myService.js
export const getMyData = () => api.get('/my-endpoint');
```

2. **Create Component**
```javascript
// src/components/MyFeature.jsx
import { useApi } from '../hooks/useApi';
import { myService } from '../services';

const MyFeature = () => {
  const { data, loading } = useApi(myService.getMyData);
  return <div>{data}</div>;
};
```

3. **Add to Page**
```javascript
// src/pages/MyPage.jsx
import MyFeature from '../components/MyFeature';

const MyPage = () => {
  return <MyFeature />;
};
```

4. **Test in Docker**
```bash
docker-compose up -d --build news-automation-frontend
```

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Find what's using port 3002
lsof -i :3002

# Kill the process
kill -9 <PID>
```

### Container Won't Start
```bash
# Check logs
docker logs news-automation-frontend

# Rebuild from scratch
docker-compose build --no-cache news-automation-frontend
docker-compose up -d news-automation-frontend
```

### API Calls Failing
1. Check API server is running: `docker ps | grep ichat-api-server`
2. Check network: `docker network inspect ichat-network`
3. Check environment variables in docker-compose.yml

### Build Errors
```bash
# Clean rebuild
docker-compose down news-automation-frontend
docker-compose build --no-cache news-automation-frontend
docker-compose up -d news-automation-frontend
```

## 🎯 Next Steps

### Phase 2: Migrate Existing UIs
- [ ] News Fetcher UI (from jobs/news-fetcher)
- [ ] Image Cleaning UI (from jobs/watermark-remover)
- [ ] YouTube Uploader UI (from youtube-uploader)

### Phase 3: New Features
- [ ] LLM Prompt Configuration UI
- [ ] Voice Settings UI
- [ ] Prompt Testing Interface

### Phase 4: Enhancements
- [ ] Real-time updates (WebSocket)
- [ ] Advanced filtering
- [ ] Data visualization
- [ ] Export functionality

## 💡 Tips

1. **Use Common Components** - Don't reinvent the wheel
   ```javascript
   import { Button, Card, Table } from '../components/common';
   ```

2. **Use Service Layer** - Keep API logic separate
   ```javascript
   import { newsService } from '../services';
   const data = await newsService.getNews();
   ```

3. **Use Custom Hooks** - Reuse stateful logic
   ```javascript
   import { useApi } from '../hooks/useApi';
   const { data, loading, error } = useApi(apiFunction);
   ```

4. **Follow Patterns** - Look at existing code for examples

5. **Read Docs** - Comprehensive documentation available

## 🤝 Contributing

When adding new features:
1. Follow existing folder structure
2. Use common components where possible
3. Add JSDoc comments
4. Keep components small and focused
5. Test in Docker before committing

## 📞 Support

- Check documentation files
- Review existing code for patterns
- Look at QUICK_REFERENCE.md for examples

## 🎉 You're Ready!

You now have a solid understanding of the News Automation Frontend. Start exploring the code and building amazing features!

**Happy coding! 🚀**

