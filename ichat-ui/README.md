# iChat UI - Grok-Inspired Chat Interface

A modern, responsive chat interface inspired by Grok and similar to ChatGPT's design. Built with React and Tailwind CSS.

## Features

- 🎨 **Modern Dark Theme**: Sleek dark interface with gradient accents
- 💬 **Real-time Chat**: Smooth message animations and typing indicators
- 📱 **Responsive Design**: Works on desktop and mobile devices
- 🤖 **AI Assistant UI**: Professional chat interface for AI interactions
- ⚡ **Fast Loading**: Single HTML file with CDN dependencies
- 🎭 **Animated Elements**: Gradient text animations and smooth transitions

## Quick Start

### Option 1: Docker Deployment (Recommended)
```bash
cd ichat-ui
./docker-run.sh start
```
Then open http://localhost:3000

### Option 2: Docker Compose (Full Stack)
```bash
# From project root
docker-compose up ichat-ui
```
Or to start all services:
```bash
docker-compose up
```

### Option 3: Simple HTTP Server (Development)
```bash
cd ichat-ui
python -m http.server 3000 --directory public
```
Then open http://localhost:3000

### Option 4: Using npm scripts (Development)
```bash
cd ichat-ui
npm run start    # Starts on port 3000
npm run dev      # Starts on port 8080
npm run serve    # Starts on port 5000
```

### Option 5: Direct File Access
Simply open `public/index.html` in your web browser.

## Project Structure

```
ichat-ui/
├── public/
│   └── index.html          # Main application file
├── src/
│   ├── components/         # Future React components (if needed)
│   ├── services/          # API service files (if needed)
│   └── styles/            # Additional CSS files (if needed)
├── Dockerfile             # Docker configuration
├── .dockerignore          # Docker ignore file
├── docker-run.sh          # Docker run script
├── package.json           # Project configuration
└── README.md             # This file
```

## Docker Deployment

### Docker Commands
```bash
# Build and start the service
./docker-run.sh start

# Stop the service
./docker-run.sh stop

# Restart the service
./docker-run.sh restart

# View service status
./docker-run.sh status

# View logs
./docker-run.sh logs

# Clean up (remove container and image)
./docker-run.sh clean
```

### Docker Compose Integration
The UI service is integrated into the main `docker-compose.yml`:
- **Service Name**: `ichat-ui`
- **Container Name**: `ichat-ui-frontend`
- **Port**: `3000:80`
- **Network**: `ichat-network`
- **Dependencies**: `ichat-api`

### Production Configuration
- **Web Server**: Nginx Alpine (lightweight)
- **Compression**: Gzip enabled
- **Security Headers**: XSS protection, content type sniffing protection
- **Caching**: Static assets cached for 1 year
- **Health Check**: `/health` endpoint
- **SPA Routing**: All routes fallback to `index.html`

## UI Components

### ChatMessage Component
- User and assistant message bubbles
- Timestamps and sender identification
- Smooth animations and responsive design

### ChatInput Component
- Multi-line text input with auto-resize
- Send button with keyboard shortcuts
- Disabled state during API calls

### TypingIndicator Component
- Animated dots showing assistant is typing
- Consistent with message bubble design

### ChatHeader Component
- Gradient animated title
- Assistant branding and status
- Menu options (expandable)

## Customization

### Colors and Themes
The interface uses Tailwind CSS classes. Key color schemes:
- **Background**: `bg-gray-900` (main), `bg-gray-800` (containers)
- **User Messages**: `bg-blue-500` to `bg-blue-600` gradient
- **Assistant Messages**: `bg-gray-700` with `border-gray-600`
- **Accent Colors**: Purple and pink gradients for branding

### Fonts and Icons
- **Icons**: Font Awesome 6.4.0 (CDN)
- **Fonts**: System fonts via Tailwind CSS
- **Animations**: Custom CSS keyframes for gradients and typing

## Integration

### Backend API Integration
To connect with your backend services, modify the `handleSend` function in the main App component:

```javascript
const handleSend = async (text) => {
  // Add your API call here
  const response = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: text })
  });
  
  const data = await response.json();
  // Handle response...
};
```

### WebSocket Support
For real-time features, you can add WebSocket connections:

```javascript
const ws = new WebSocket('ws://localhost:8080/chat');
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  setMessages(prev => [...prev, message]);
};
```

## Browser Support

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

## Dependencies

All dependencies are loaded via CDN:
- React 18.2.0
- ReactDOM 18.2.0
- Babel Standalone 7.20.15
- Tailwind CSS (latest)
- Font Awesome 6.4.0

## License

MIT License - feel free to use in your projects!
