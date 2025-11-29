# News Automation Frontend Server

Unified, well-structured frontend interface for the News Automation System.

## ✨ Features

- 📊 **Dashboard** - Overview of entire news automation pipeline with real-time stats
- 📰 **News Fetcher** - Manage news sources, seed URLs, and fetch articles
- 🖼️ **Image Cleaning** - Remove watermarks from images with AI-powered tools
- 🎤 **Voice & LLM Config** - Configure LLM prompts and voice settings for audio generation
- 📺 **YouTube Uploader** - Upload videos to YouTube with automated metadata

## 🛠️ Tech Stack

- **Frontend**: React 18 + Vite (fast, modern development)
- **Styling**: Tailwind CSS (utility-first, responsive)
- **Routing**: React Router v6 (declarative routing)
- **HTTP Client**: Axios (promise-based HTTP client)
- **Backend**: Express.js (API proxy server)
- **Containerization**: Docker (multi-stage builds)

## Development

### Prerequisites

- Node.js 18+
- npm or yarn

### Install Dependencies

```bash
npm install
```

### Run Development Server

```bash
# Start Vite dev server (with hot reload)
npm run dev
```

The app will be available at http://localhost:5173

### Build for Production

```bash
npm run build
```

### Run Production Server

```bash
# Build first
npm run build

# Start Express server
npm start
```

The app will be available at http://localhost:3001

## Docker

### Build Image

```bash
docker build -t news-automation-frontend .
```

### Run Container

```bash
docker run -p 3001:3001 \
  -e API_SERVER_URL=http://localhost:8080 \
  news-automation-frontend
```

## Environment Variables

- `PORT` - Server port (default: 3001)
- `API_SERVER_URL` - Backend API server URL (default: http://localhost:8080)

## 📁 Project Structure

```
frontend-server/
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── common/          # Generic components (Button, Card, Table, Modal, etc.)
│   │   └── Layout/          # Layout components (Navbar, Sidebar)
│   ├── pages/               # Page components (one per route)
│   │   ├── Dashboard.jsx
│   │   ├── NewsFetcherPage.jsx
│   │   ├── ImageCleaningPage.jsx
│   │   ├── VoiceLLMPage.jsx
│   │   └── YouTubePage.jsx
│   ├── services/            # API service modules
│   │   ├── api.js           # Axios instance with interceptors
│   │   ├── newsService.js   # News API calls
│   │   ├── voiceService.js  # Voice/Audio API calls
│   │   ├── videoService.js  # Video API calls
│   │   ├── youtubeService.js # YouTube API calls
│   │   ├── llmService.js    # LLM/Prompt API calls
│   │   └── imageService.js  # Image/Watermark API calls
│   ├── hooks/               # Custom React hooks
│   │   ├── useApi.js        # API call hook with loading/error states
│   │   └── useToast.js      # Toast notification hook
│   ├── utils/               # Utility functions
│   │   ├── formatters.js    # Date, number, text formatting
│   │   └── validators.js    # Input validation functions
│   ├── config/              # Configuration files
│   │   └── constants.js     # App-wide constants
│   ├── App.jsx              # Main app component with routing
│   ├── main.jsx             # React entry point
│   └── index.css            # Global styles
├── public/                  # Static assets
├── server.js                # Express server (API proxy)
├── vite.config.js           # Vite configuration
├── tailwind.config.js       # Tailwind CSS configuration
├── postcss.config.js        # PostCSS configuration
├── package.json             # Dependencies and scripts
├── Dockerfile               # Multi-stage Docker build
├── ARCHITECTURE.md          # Detailed architecture documentation
└── README.md                # This file
```

See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed architecture documentation.

## 🏗️ Architecture Highlights

### Modular Service Layer
Each domain has its own service module with clean API abstractions:
```javascript
import { newsService } from './services';

// Clean, reusable API calls
const articles = await newsService.getNews({ page: 1, pageSize: 25 });
await newsService.runNewsFetchJob();
```

### Reusable Components
Well-designed common components for rapid development:
```javascript
import { Button, Card, Table, Modal } from './components/common';

<Card title="News Articles" actions={<Button>Refresh</Button>}>
  <Table columns={columns} data={data} />
</Card>
```

### Custom Hooks
Encapsulated logic for common patterns:
```javascript
import { useApi } from './hooks/useApi';

const { data, loading, error, execute } = useApi(newsService.getNews);
```

### API Proxy Pattern
Express server proxies all `/api/*` requests to the backend API server:
- Avoids CORS issues
- Single entry point
- Can add authentication middleware
- Can cache responses

## 🚀 Quick Start

### Start the Service
```bash
# From project root
docker-compose up -d news-automation-frontend
```

Access the app at: **http://localhost:3002**

### View Logs
```bash
docker logs -f news-automation-frontend
```

### Rebuild After Changes
```bash
docker-compose up -d --build news-automation-frontend
```

### Stop the Service
```bash
docker-compose stop news-automation-frontend
```

## 🔧 Development Guide

### Adding a New Page

1. **Create page component** in `src/pages/`:
```javascript
// src/pages/MyNewPage.jsx
import React from 'react';
import { Card } from '../components/common';

const MyNewPage = () => {
  return (
    <Card title="My New Feature">
      <p>Content here</p>
    </Card>
  );
};

export default MyNewPage;
```

2. **Add route** in `src/App.jsx`:
```javascript
import MyNewPage from './pages/MyNewPage';

<Route path="/my-new-page" element={<MyNewPage />} />
```

3. **Add navigation item** in `src/config/constants.js`:
```javascript
export const NAV_ITEMS = [
  // ... existing items
  { path: '/my-new-page', icon: '🆕', label: 'My New Feature' },
];
```

### Adding a New API Service

1. **Create service file** in `src/services/`:
```javascript
// src/services/myService.js
import api from './api';

export const getData = (params) => {
  return api.get('/my-endpoint', { params });
};

export const postData = (data) => {
  return api.post('/my-endpoint', data);
};

export default { getData, postData };
```

2. **Export from index**:
```javascript
// src/services/index.js
export { default as myService } from './myService';
```

3. **Use in component**:
```javascript
import { useApi } from '../hooks/useApi';
import { myService } from '../services';

const { data, loading, execute } = useApi(myService.getData);
```

### Adding a New Component

1. **Create component** in `src/components/common/`:
```javascript
// src/components/common/MyComponent.jsx
import React from 'react';

/**
 * My reusable component
 * @param {Object} props - Component props
 * @param {string} props.title - Component title
 */
const MyComponent = ({ title, children }) => {
  return (
    <div className="p-4 bg-white rounded-lg shadow">
      <h3 className="font-bold">{title}</h3>
      {children}
    </div>
  );
};

export default MyComponent;
```

2. **Export from index**:
```javascript
// src/components/common/index.js
export { default as MyComponent } from './MyComponent';
```

## 📚 Available Components

### Common Components
- **Button** - Customizable button with variants (primary, secondary, success, danger, warning)
- **Card** - Container with header, content, and actions
- **Table** - Data table with loading and empty states
- **Modal** - Popup modal with customizable size
- **Input** - Form input with label, error, and helper text
- **Spinner** - Loading spinner with sizes and colors
- **Badge** - Status badge with variants

### Utility Functions
- **Formatters**: `formatDate`, `formatRelativeTime`, `formatNumber`, `formatPercentage`, `formatFileSize`, `formatDuration`, `truncateText`
- **Validators**: `isValidEmail`, `isValidUrl`, `isRequired`, `minLength`, `maxLength`, `inRange`

## 🗺️ Development Roadmap

- [x] **Phase 1** - Basic structure and navigation ✅
- [ ] **Phase 2** - Migrate existing UIs (News Fetcher, Image Cleaning, YouTube)
- [ ] **Phase 3** - Create Voice/LLM Configuration UI
- [ ] **Phase 4** - API integration and real-time updates
- [ ] **Phase 5** - Enhanced features (monitoring, logs, analytics)
- [ ] **Phase 6** - Production deployment and optimization

## 🤝 Contributing

When adding new features:
1. Follow the existing folder structure
2. Use common components where possible
3. Add JSDoc comments to functions
4. Keep components small and focused
5. Use Tailwind CSS for styling
6. Test in Docker before committing

## 📖 Documentation

- [ARCHITECTURE.md](./ARCHITECTURE.md) - Detailed architecture and design patterns
- [README.md](./README.md) - This file (quick start and development guide)

## 🐛 Troubleshooting

### Port already in use
```bash
# Check what's using port 3002
lsof -i :3002

# Stop the container
docker-compose stop news-automation-frontend
```

### Build fails
```bash
# Clean rebuild
docker-compose build --no-cache news-automation-frontend
docker-compose up -d news-automation-frontend
```

### API calls failing
- Check that `ichat-api-server` is running
- Verify `API_SERVER_URL` environment variable
- Check Docker network connectivity

## 📄 License

MIT

