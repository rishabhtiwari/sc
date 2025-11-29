# Frontend Server Architecture

## Overview

The News Automation Frontend is a well-structured, modular React application designed for scalability and maintainability. It follows industry best practices and modern React patterns.

## Technology Stack

- **Frontend Framework**: React 18
- **Build Tool**: Vite (fast, modern bundler)
- **Styling**: Tailwind CSS (utility-first CSS)
- **Routing**: React Router v6
- **HTTP Client**: Axios
- **Backend**: Express.js (API proxy server)

## Project Structure

```
frontend-server/
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── common/          # Generic components (Button, Card, Table, etc.)
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
│   │   ├── imageService.js  # Image/Watermark API calls
│   │   └── index.js         # Barrel export
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
└── README.md                # Documentation

```

## Architecture Principles

### 1. **Separation of Concerns**
- **Components**: UI presentation only
- **Services**: API communication logic
- **Hooks**: Reusable stateful logic
- **Utils**: Pure utility functions
- **Pages**: Route-level components that compose smaller components

### 2. **Component Organization**

#### Common Components (`src/components/common/`)
Reusable, generic UI components that can be used across the app:
- `Button.jsx` - Customizable button with variants, sizes, loading states
- `Card.jsx` - Container component with header, content, actions
- `Table.jsx` - Data table with sorting, pagination support
- `Modal.jsx` - Popup modal with customizable size
- `Input.jsx` - Form input with label, error, helper text
- `Spinner.jsx` - Loading spinner with sizes and colors
- `Badge.jsx` - Status badge with variants

**Usage Example**:
```jsx
import { Button, Card, Table } from '../components/common';

<Card title="News Articles">
  <Table columns={columns} data={data} />
  <Button variant="primary" onClick={handleClick}>
    Fetch News
  </Button>
</Card>
```

#### Layout Components (`src/components/Layout/`)
App-wide layout components:
- `Layout.jsx` - Main layout with sidebar navigation and top bar

### 3. **Service Layer Architecture**

Each service module handles API calls for a specific domain:

```javascript
// Example: newsService.js
import api from './api';

export const getNews = (params) => api.get('/news', { params });
export const runNewsFetchJob = () => api.post('/news/fetch/run');

export default { getNews, runNewsFetchJob };
```

**Benefits**:
- Centralized API logic
- Easy to mock for testing
- Type-safe with JSDoc comments
- Reusable across components

### 4. **Custom Hooks**

#### `useApi` Hook
Manages API call state (loading, error, data):

```javascript
import { useApi } from '../hooks/useApi';
import { newsService } from '../services';

const { data, loading, error, execute } = useApi(newsService.getNews);

// Call API
await execute({ page: 1, pageSize: 25 });
```

#### `useToast` Hook
Manages toast notifications:

```javascript
import { useToast } from '../hooks/useToast';

const { showToast } = useToast();

showToast('News fetched successfully!', 'success');
```

### 5. **Utility Functions**

#### Formatters (`src/utils/formatters.js`)
- `formatDate()` - Format dates
- `formatRelativeTime()` - "2 hours ago"
- `formatNumber()` - Add commas to numbers
- `formatPercentage()` - Calculate and format percentages
- `formatFileSize()` - Convert bytes to KB/MB/GB
- `formatDuration()` - Convert seconds to readable duration
- `truncateText()` - Truncate long text with ellipsis

#### Validators (`src/utils/validators.js`)
- `isValidEmail()` - Email validation
- `isValidUrl()` - URL validation
- `isRequired()` - Required field check
- `minLength()` / `maxLength()` - Length validation
- `inRange()` - Number range validation

### 6. **Configuration Management**

All constants in one place (`src/config/constants.js`):
- Routes
- Navigation items
- API configuration
- Status colors
- Pagination defaults
- WebSocket events

**Benefits**:
- Single source of truth
- Easy to update
- No magic strings in code

## API Proxy Pattern

The Express server (`server.js`) acts as a proxy for all `/api/*` requests:

```javascript
// Frontend makes request to: /api/news
// Server proxies to: http://ichat-api-server:8080/api/news
```

**Benefits**:
- Avoids CORS issues
- Single entry point
- Can add authentication middleware
- Can cache responses
- Can transform requests/responses

## Routing Structure

```javascript
/ → Dashboard (overview, stats, quick actions)
/news-fetcher → News Fetcher UI (manage sources, view articles)
/image-cleaning → Image Cleaning UI (watermark removal)
/voice-llm → Voice & LLM Config (prompts, voice settings)
/youtube → YouTube Uploader (upload videos, view history)
```

## State Management

Currently using **React hooks** for state management:
- `useState` - Component-level state
- `useEffect` - Side effects
- Custom hooks - Reusable stateful logic

**Future**: Can easily add Redux/Zustand if global state becomes complex.

## Styling Approach

**Tailwind CSS** utility-first approach:
- Rapid development
- Consistent design system
- Small bundle size (purges unused CSS)
- Responsive by default

**Custom theme** in `tailwind.config.js`:
- Primary colors (blue)
- Accent colors (red)
- Extended color palette

## Error Handling

### API Level
```javascript
// Axios interceptor in api.js
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Log error
    // Show toast notification
    // Redirect to login if 401
    return Promise.reject(error);
  }
);
```

### Component Level
```javascript
const { data, loading, error, execute } = useApi(apiFunction);

if (error) return <ErrorMessage message={error} />;
if (loading) return <Spinner />;
return <DataDisplay data={data} />;
```

## Performance Optimizations

1. **Code Splitting**: React Router lazy loading (future)
2. **Memoization**: `React.memo()`, `useMemo()`, `useCallback()`
3. **Vite**: Fast HMR (Hot Module Replacement)
4. **Tailwind**: Purges unused CSS in production
5. **Docker Multi-stage**: Smaller production image

## Development Workflow

### Adding a New Page

1. Create page component in `src/pages/`
2. Add route in `src/App.jsx`
3. Add navigation item in `src/config/constants.js`
4. Create service functions if needed in `src/services/`

### Adding a New Component

1. Create component in `src/components/common/` or feature folder
2. Export from `index.js` for easy imports
3. Add JSDoc comments for props
4. Make it reusable and configurable

### Adding a New API Endpoint

1. Add function to appropriate service file in `src/services/`
2. Use the `api` instance from `api.js`
3. Add JSDoc comments
4. Export from service module

## Testing Strategy (Future)

- **Unit Tests**: Jest + React Testing Library
- **Integration Tests**: Test API service calls
- **E2E Tests**: Cypress or Playwright
- **Component Tests**: Storybook for component library

## Deployment

### Development
```bash
docker-compose up -d news-automation-frontend
```

### Production
Multi-stage Docker build:
1. Build stage: Install deps, build React app
2. Production stage: Copy built files, run Express server

## Future Enhancements

1. **WebSocket Integration**: Real-time job status updates
2. **Authentication**: JWT-based auth with protected routes
3. **Dark Mode**: Theme switcher
4. **Internationalization**: Multi-language support
5. **Analytics**: Track user interactions
6. **Offline Support**: Service workers, PWA
7. **Advanced Filtering**: Complex search and filters
8. **Drag & Drop**: File uploads, reordering
9. **Charts**: Data visualization with Chart.js/Recharts
10. **Export**: Download data as CSV/PDF

## Best Practices

✅ **Component Design**
- Single Responsibility Principle
- Props validation with PropTypes or TypeScript
- Meaningful component names
- Small, focused components

✅ **Code Organization**
- Group by feature, not by type
- Barrel exports for clean imports
- Consistent file naming (PascalCase for components)

✅ **Performance**
- Avoid unnecessary re-renders
- Use React.memo for expensive components
- Lazy load routes and heavy components

✅ **Accessibility**
- Semantic HTML
- ARIA labels
- Keyboard navigation
- Screen reader support

✅ **Security**
- Sanitize user input
- Validate on both client and server
- Use HTTPS in production
- Implement CSRF protection

## Conclusion

This architecture provides a solid foundation for building a scalable, maintainable frontend application. The modular structure makes it easy to add new features, test components, and onboard new developers.

