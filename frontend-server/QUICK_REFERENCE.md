# Quick Reference Guide

## 🚀 Common Commands

### Docker Commands
```bash
# Start the frontend server
docker-compose up -d news-automation-frontend

# View logs
docker logs -f news-automation-frontend

# Rebuild and restart
docker-compose up -d --build news-automation-frontend

# Stop the service
docker-compose stop news-automation-frontend

# Remove container
docker-compose down news-automation-frontend
```

### Development Commands (Local)
```bash
# Install dependencies
cd frontend-server && npm install

# Start dev server (with hot reload)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Start Express server
npm start
```

## 📦 Import Patterns

### Common Components
```javascript
import { Button, Card, Table, Modal, Input, Spinner, Badge } from '../components/common';

// Usage
<Button variant="primary" onClick={handleClick}>Click Me</Button>
<Card title="My Card">Content</Card>
<Table columns={columns} data={data} loading={loading} />
```

### Services
```javascript
import { newsService, voiceService, videoService } from '../services';

// Usage
const articles = await newsService.getNews({ page: 1 });
await voiceService.generateAudio();
```

### Hooks
```javascript
import { useApi } from '../hooks/useApi';
import { useToast } from '../hooks/useToast';

// Usage
const { data, loading, error, execute } = useApi(newsService.getNews);
const { showToast } = useToast();
```

### Utils
```javascript
import { formatDate, formatNumber, truncateText } from '../utils/formatters';
import { isValidEmail, isRequired } from '../utils/validators';

// Usage
const formatted = formatDate(new Date());
const isValid = isValidEmail('test@example.com');
```

### Constants
```javascript
import { ROUTES, NAV_ITEMS, STATUS_COLORS } from '../config/constants';

// Usage
<Link to={ROUTES.DASHBOARD}>Dashboard</Link>
```

## 🎨 Component Examples

### Button
```javascript
<Button variant="primary" size="md" icon="🚀" onClick={handleClick}>
  Fetch News
</Button>

// Variants: primary, secondary, success, danger, warning, outline
// Sizes: sm, md, lg
```

### Card
```javascript
<Card 
  title="News Articles" 
  subtitle="Latest news from all sources"
  actions={<Button>Refresh</Button>}
>
  <p>Card content here</p>
</Card>
```

### Table
```javascript
const columns = [
  { key: 'title', label: 'Title' },
  { key: 'date', label: 'Date', render: (val) => formatDate(val) },
  { key: 'status', label: 'Status', render: (val) => <Badge variant="success">{val}</Badge> },
];

<Table 
  columns={columns} 
  data={articles} 
  loading={loading}
  emptyMessage="No articles found"
  onRowClick={(row) => console.log(row)}
/>
```

### Modal
```javascript
const [isOpen, setIsOpen] = useState(false);

<Modal 
  isOpen={isOpen} 
  onClose={() => setIsOpen(false)}
  title="Add News Source"
  size="md"
>
  <p>Modal content</p>
</Modal>
```

### Input
```javascript
<Input
  label="Email Address"
  type="email"
  placeholder="Enter your email"
  icon="📧"
  error={errors.email}
  helperText="We'll never share your email"
/>
```

## 🔌 API Service Examples

### News Service
```javascript
import { newsService } from '../services';

// Get news with filters
const articles = await newsService.getNews({
  page: 1,
  pageSize: 25,
  category: 'technology',
  language: 'en'
});

// Get single article
const article = await newsService.getNewsById('123');

// Run fetch job
await newsService.runNewsFetchJob();

// Manage seed URLs
const seeds = await newsService.getSeedUrls();
await newsService.addSeedUrl({ url: 'https://...', category: 'tech' });
await newsService.updateSeedUrl('partner-id', { enabled: true });
await newsService.deleteSeedUrl('partner-id');
```

### Voice Service
```javascript
import { voiceService } from '../services';

// Get stats
const stats = await voiceService.getAudioStats();

// Generate audio
await voiceService.generateAudio({ jobId: 'manual-123' });

// Get available voices
const voices = await voiceService.getAvailableVoices();

// Test voice
await voiceService.testVoice({ 
  text: 'Hello world', 
  voice: 'kavya', 
  language: 'hi' 
});
```

### LLM Service
```javascript
import { llmService } from '../services';

// Get all prompts
const prompts = await llmService.getPrompts();

// Get specific prompt
const summaryPrompt = await llmService.getPromptByType('summary');

// Save prompt
await llmService.savePrompt('summary', {
  template: 'Summarize this article: {{content}}',
  maxTokens: 100
});

// Test prompt
const result = await llmService.testPrompt({
  prompt: 'Summarize: {{text}}',
  sampleText: 'Long article text...'
});
```

## 🪝 Hook Examples

### useApi Hook
```javascript
import { useApi } from '../hooks/useApi';
import { newsService } from '../services';

function MyComponent() {
  const { data, loading, error, execute, reset } = useApi(newsService.getNews);

  useEffect(() => {
    execute({ page: 1, pageSize: 25 });
  }, []);

  if (loading) return <Spinner />;
  if (error) return <div>Error: {error}</div>;
  
  return <Table data={data} />;
}
```

### useToast Hook
```javascript
import { useToast } from '../hooks/useToast';

function MyComponent() {
  const { showToast } = useToast();

  const handleSuccess = () => {
    showToast('Operation successful!', 'success', 3000);
  };

  const handleError = () => {
    showToast('Something went wrong', 'error', 5000);
  };

  return <Button onClick={handleSuccess}>Save</Button>;
}
```

## 🛠️ Utility Examples

### Formatters
```javascript
import { 
  formatDate, 
  formatRelativeTime, 
  formatNumber, 
  formatPercentage,
  formatFileSize,
  formatDuration,
  truncateText 
} from '../utils/formatters';

formatDate(new Date());                    // "Jan 15, 2024, 10:30 AM"
formatRelativeTime(new Date());            // "2 hours ago"
formatNumber(1234567);                     // "1,234,567"
formatPercentage(75, 100);                 // "75%"
formatFileSize(1024 * 1024);               // "1 MB"
formatDuration(3665);                      // "1h 1m 5s"
truncateText("Long text...", 50);          // "Long text... (truncated)"
```

### Validators
```javascript
import { 
  isValidEmail, 
  isValidUrl, 
  isRequired, 
  minLength, 
  maxLength, 
  inRange 
} from '../utils/validators';

isValidEmail('test@example.com');          // true
isValidUrl('https://example.com');         // true
isRequired('value');                       // true
minLength('hello', 3);                     // true
maxLength('hello', 10);                    // true
inRange(50, 0, 100);                       // true
```

## 🎨 Tailwind CSS Classes

### Common Patterns
```javascript
// Container
<div className="bg-white rounded-xl shadow-md p-6">

// Grid Layout
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">

// Flex Layout
<div className="flex items-center justify-between gap-4">

// Button
<button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">

// Input
<input className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">

// Card
<div className="bg-white rounded-xl shadow-md overflow-hidden">

// Badge
<span className="px-2.5 py-1 bg-green-100 text-green-800 rounded-full text-sm">
```

## 📁 File Naming Conventions

- **Components**: PascalCase (e.g., `Button.jsx`, `NewsTable.jsx`)
- **Services**: camelCase (e.g., `newsService.js`, `voiceService.js`)
- **Hooks**: camelCase with `use` prefix (e.g., `useApi.js`, `useToast.js`)
- **Utils**: camelCase (e.g., `formatters.js`, `validators.js`)
- **Constants**: UPPER_SNAKE_CASE in file (e.g., `API_BASE_URL`)
- **Pages**: PascalCase with `Page` suffix (e.g., `DashboardPage.jsx`)

## 🔍 Debugging Tips

### Check API Calls
```javascript
// In browser console
localStorage.setItem('debug', 'axios');

// Or add console.log in api.js interceptor
```

### React DevTools
- Install React DevTools browser extension
- Inspect component props and state
- Track re-renders

### Network Tab
- Open browser DevTools → Network tab
- Filter by XHR/Fetch
- Check request/response

## 📚 Resources

- [React Docs](https://react.dev/)
- [Vite Docs](https://vitejs.dev/)
- [Tailwind CSS Docs](https://tailwindcss.com/)
- [React Router Docs](https://reactrouter.com/)
- [Axios Docs](https://axios-http.com/)

