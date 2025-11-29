import express from 'express';
import cors from 'cors';
import path from 'path';
import { fileURLToPath } from 'url';
import axios from 'axios';

// ES module equivalent of __dirname
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 3002;
const API_SERVER_URL = process.env.API_SERVER_URL || 'http://localhost:8080';
const NEWS_FETCHER_URL = process.env.NEWS_FETCHER_URL || 'http://ichat-news-fetcher:8093';
const IOPAINT_URL = process.env.IOPAINT_URL || 'http://ichat-iopaint:8096';
const YOUTUBE_UPLOADER_URL = process.env.YOUTUBE_UPLOADER_URL || 'http://ichat-youtube-uploader:8097';

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Serve static files from dist directory (production build)
app.use(express.static(path.join(__dirname, 'dist')));

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({
        status: 'healthy',
        service: 'news-automation-frontend',
        timestamp: new Date().toISOString(),
        api_server: API_SERVER_URL
    });
});

// API Proxy Routes - Forward all /api/* requests to appropriate backend
app.use('/api', async (req, res) => {
    try {
        // Determine target URL based on endpoint
        // News-fetcher specific endpoints go directly to news-fetcher service
        const newsFetcherEndpoints = [
            '/api/news/seed-urls',
            '/api/news/enrichment/status',
            '/api/news/fetch/run'
        ];

        // IOPaint specific endpoints go directly to IOPaint service
        const iopaintEndpoints = [
            '/api/image/stats',
            '/api/image/next',
            '/api/image/process',
            '/api/image/save',
            '/api/image/skip',
            '/api/image/cleaned'
        ];

        // YouTube uploader specific endpoints go directly to YouTube uploader service
        const youtubeEndpoints = [
            '/api/youtube/stats',
            '/api/youtube/upload-latest-20',
            '/api/youtube/shorts/pending',
            '/api/youtube/shorts/upload',
            '/api/youtube/oauth-callback'
        ];

        let targetUrl;
        let targetService;

        // Check if this is a news-fetcher specific endpoint
        const isNewsFetcherEndpoint = newsFetcherEndpoints.some(endpoint =>
            req.originalUrl.startsWith(endpoint)
        );

        // Check if this is an IOPaint specific endpoint
        const isIopaintEndpoint = iopaintEndpoints.some(endpoint =>
            req.originalUrl.startsWith(endpoint)
        );

        // Check if this is a YouTube uploader specific endpoint
        const isYoutubeEndpoint = youtubeEndpoints.some(endpoint =>
            req.originalUrl.startsWith(endpoint)
        );

        if (isNewsFetcherEndpoint) {
            // Remove /api/news prefix and forward to news-fetcher service
            const path = req.originalUrl.replace('/api/news', '');
            targetUrl = `${NEWS_FETCHER_URL}${path}`;
            targetService = 'news-fetcher';
        } else if (isIopaintEndpoint) {
            // Remove /api/image prefix and forward to IOPaint service
            const path = req.originalUrl.replace('/api/image', '/api');
            targetUrl = `${IOPAINT_URL}${path}`;
            targetService = 'iopaint';
        } else if (isYoutubeEndpoint) {
            // Remove /api/youtube prefix and forward to YouTube uploader service
            const path = req.originalUrl.replace('/api/youtube', '/api');
            targetUrl = `${YOUTUBE_UPLOADER_URL}${path}`;
            targetService = 'youtube-uploader';
        } else {
            // Forward to API server
            targetUrl = `${API_SERVER_URL}${req.originalUrl}`;
            targetService = 'api-server';
        }

        console.log(`🔄 Proxying ${req.method} ${req.originalUrl} -> ${targetUrl} (${targetService})`);

        const response = await axios({
            method: req.method,
            url: targetUrl,
            data: req.body,
            headers: {
                ...req.headers,
                host: new URL(targetUrl).host
            },
            params: req.query,
            validateStatus: () => true // Don't throw on any status code
        });

        // Forward response
        res.status(response.status).json(response.data);

    } catch (error) {
        console.error(`❌ Proxy error: ${error.message}`);
        res.status(500).json({
            error: 'Proxy error',
            message: error.message
        });
    }
});

// Serve React app for all other routes (SPA fallback)
app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, 'dist', 'index.html'));
});

// Start server
app.listen(PORT, () => {
    console.log(`🚀 News Automation Frontend Server running on port ${PORT}`);
    console.log(`📋 Health check: http://localhost:${PORT}/health`);
    console.log(`🔗 API Server: ${API_SERVER_URL}`);
    console.log(`🔗 News Fetcher: ${NEWS_FETCHER_URL}`);
    console.log(`🌐 Frontend: http://localhost:${PORT}`);
});

// Graceful shutdown
process.on('SIGINT', () => {
    console.log('\n👋 Shutting down gracefully...');
    process.exit(0);
});

