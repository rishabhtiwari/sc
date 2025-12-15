import express from 'express';
import cors from 'cors';
import path from 'path';
import { fileURLToPath } from 'url';
import axios from 'axios';
import FormData from 'form-data';
import multer from 'multer';

// ES module equivalent of __dirname
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 3002;
const API_SERVER_URL = process.env.API_SERVER_URL || 'http://localhost:8080';
const NEWS_FETCHER_URL = process.env.NEWS_FETCHER_URL || 'http://ichat-news-fetcher:8093';
const IOPAINT_URL = process.env.IOPAINT_URL || 'http://ichat-iopaint:8096';
const YOUTUBE_UPLOADER_URL = process.env.YOUTUBE_UPLOADER_URL || 'http://ichat-youtube-uploader:8097';
const VOICE_GENERATOR_URL = process.env.VOICE_GENERATOR_URL || 'http://ichat-voice-generator:8094';
const VIDEO_GENERATOR_URL = process.env.VIDEO_GENERATOR_URL || 'http://ichat-video-generator:8095';

// Middleware
app.use(cors());

// Configure multer for file uploads (store in memory)
const upload = multer({ storage: multer.memoryStorage() });

// Increase body size limit to 50MB for image uploads
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ extended: true, limit: '50mb' }));

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({
        status: 'healthy',
        service: 'news-automation-frontend',
        timestamp: new Date().toISOString(),
        api_server: API_SERVER_URL
    });
});

// Special route for background audio file upload (must come before general API proxy)
app.post('/api/videos/background-audio', upload.single('file'), async (req, res) => {
    try {
        if (!req.file) {
            return res.status(400).json({ status: 'error', error: 'No file provided' });
        }

        const formData = new FormData();
        formData.append('file', req.file.buffer, {
            filename: req.file.originalname,
            contentType: req.file.mimetype
        });

        const targetUrl = `${VIDEO_GENERATOR_URL}/background-audio`;
        console.log(`🔄 Proxying file upload ${req.method} ${req.originalUrl} -> ${targetUrl} (video-generator)`);

        const response = await axios.post(targetUrl, formData, {
            headers: {
                ...formData.getHeaders()
            },
            validateStatus: () => true
        });

        res.status(response.status).json(response.data);
    } catch (error) {
        console.error(`❌ File upload proxy error: ${error.message}`);
        res.status(500).json({
            error: 'File upload proxy error',
            message: error.message
        });
    }
});

// API Proxy Routes - Forward all /api/* requests to appropriate backend
// IMPORTANT: This must come BEFORE static file middleware to prevent /api routes from being caught by static handler
app.use('/api', async (req, res) => {
    try {
        // Determine target URL based on endpoint
        // News-fetcher specific endpoints go directly to news-fetcher service
        const newsFetcherEndpoints = [
            '/api/news/seed-urls',
            '/api/news/enrichment/status',
            '/api/news/enrichment/config',
            '/api/news/run'
        ];

        // IOPaint specific endpoints go directly to IOPaint service
        const iopaintEndpoints = [
            '/api/image/stats',
            '/api/image/images',
            '/api/image/next',
            '/api/image/process',
            '/api/image/save',
            '/api/image/replace-image',
            '/api/image/skip',
            '/api/image/cleaned',
            '/api/proxy-image',
            '/api/cleaned-image',
            '/api/stats',
            '/api/images',
            '/api/next-image',
            '/api/skip'
        ];

        // YouTube uploader specific endpoints go directly to YouTube uploader service
        const youtubeEndpoints = [
            '/api/youtube/stats',
            '/api/youtube/upload-latest-20',
            '/api/youtube/upload-config',
            '/api/youtube/shorts/pending',
            '/api/youtube/shorts/upload',
            '/api/youtube/oauth-callback',
            '/api/youtube/auth/start',
            '/api/youtube/credentials'
        ];

        // Voice generator specific endpoints go directly to voice-generator service
        const voiceEndpoints = [
            '/api/news/audio/stats',
            '/api/news/audio/generate',
            '/api/news/audio/list',
            '/api/news/audio/serve'
        ];

        // Video generator specific endpoints go directly to video-generator service
        const videoEndpoints = [
            '/api/videos/background-audio',
            '/api/videos/configs',
            '/api/videos/merge',
            '/api/videos/recompute'
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

        // Check if this is a voice generator specific endpoint
        const isVoiceEndpoint = voiceEndpoints.some(endpoint =>
            req.originalUrl.startsWith(endpoint)
        );

        // Check if this is a video generator specific endpoint
        const isVideoEndpoint = videoEndpoints.some(endpoint =>
            req.originalUrl.startsWith(endpoint)
        );

        if (isNewsFetcherEndpoint) {
            // Remove /api/news prefix and forward to news-fetcher service
            const path = req.originalUrl.replace('/api/news', '');
            targetUrl = `${NEWS_FETCHER_URL}${path}`;
            targetService = 'news-fetcher';
        } else if (isIopaintEndpoint) {
            // Map /api/image endpoints to IOPaint service endpoints
            let path = req.originalUrl;

            // Handle specific endpoint mappings
            if (path.startsWith('/api/proxy-image')) {
                // Keep /api/proxy-image as-is
                path = path;
            } else if (path.startsWith('/api/cleaned-image')) {
                // Keep /api/cleaned-image as-is
                path = path;
            } else if (path.startsWith('/api/stats') ||
                       path.startsWith('/api/images') ||
                       path.startsWith('/api/next-image') ||
                       path.startsWith('/api/skip')) {
                // Keep direct IOPaint API endpoints as-is
                path = path;
            } else if (path.startsWith('/api/image/next')) {
                path = path.replace('/api/image/next', '/api/next-image');
            } else if (path.startsWith('/api/image/cleaned/')) {
                path = path.replace('/api/image/cleaned/', '/api/cleaned-image/');
            } else {
                // For other endpoints, just replace /api/image with /api
                path = path.replace('/api/image', '/api');
            }

            targetUrl = `${IOPAINT_URL}${path}`;
            targetService = 'iopaint';
        } else if (isYoutubeEndpoint) {
            // Remove /api/youtube prefix and forward to YouTube uploader service
            const path = req.originalUrl.replace('/api/youtube', '/api');
            targetUrl = `${YOUTUBE_UPLOADER_URL}${path}`;
            targetService = 'youtube-uploader';
        } else if (isVoiceEndpoint) {
            // Forward to voice-generator service with full path
            targetUrl = `${VOICE_GENERATOR_URL}${req.originalUrl}`;
            targetService = 'voice-generator';
        } else if (isVideoEndpoint) {
            // Remove /api/videos prefix and forward to video-generator service
            const path = req.originalUrl.replace('/api/videos', '');
            targetUrl = `${VIDEO_GENERATOR_URL}${path}`;
            targetService = 'video-generator';
        } else {
            // Forward to API server
            targetUrl = `${API_SERVER_URL}${req.originalUrl}`;
            targetService = 'api-server';
        }

        console.log(`🔄 Proxying ${req.method} ${req.originalUrl} -> ${targetUrl} (${targetService})`);

        // Check if this is an image endpoint that returns binary data
        const isImageEndpoint = req.originalUrl.startsWith('/api/proxy-image') ||
                                req.originalUrl.startsWith('/api/image/cleaned/') ||
                                req.originalUrl.startsWith('/api/cleaned-image/');

        // Check if this is an audio endpoint that returns binary data
        const isAudioEndpoint = req.originalUrl.startsWith('/api/news/audio/serve') ||
                                req.originalUrl.match(/\/api\/videos\/background-audio\/[^\/]+\/download$/);

        // Check if this is a video endpoint that returns binary data
        const isVideoBinaryEndpoint = req.originalUrl.startsWith('/api/news/videos/shorts/') ||
                                      req.originalUrl.match(/\/api\/news\/videos\/[^\/]+\/(latest\.mp4|latest-thumbnail\.jpg)$/);

        // Check if this is a binary endpoint (image, audio, or video)
        const isBinaryEndpoint = isImageEndpoint || isAudioEndpoint || isVideoBinaryEndpoint;

        // Prepare headers
        const headers = {};

        // For non-binary endpoints, use JSON content type
        if (!isBinaryEndpoint && (req.method === 'POST' || req.method === 'PUT')) {
            headers['Content-Type'] = 'application/json';
        }

        if (!isBinaryEndpoint) {
            headers['Accept'] = 'application/json';
        }

        // Add authorization if present
        if (req.headers['authorization']) {
            headers['Authorization'] = req.headers['authorization'];
        }

        const axiosConfig = {
            method: req.method,
            url: targetUrl,
            headers: headers,
            params: req.query,
            validateStatus: () => true // Don't throw on any status code
        };

        // Add request body for POST/PUT/PATCH
        if (req.body && (req.method === 'POST' || req.method === 'PUT' || req.method === 'PATCH')) {
            axiosConfig.data = req.body;
        }

        // For binary endpoints (image/audio), request binary data
        if (isBinaryEndpoint) {
            axiosConfig.responseType = 'arraybuffer';
        }

        const response = await axios(axiosConfig);

        // Forward response
        if (isBinaryEndpoint) {
            // For binary endpoints, forward the binary data with correct content type
            let contentType = response.headers['content-type'];
            if (isImageEndpoint && !contentType) {
                contentType = 'image/jpeg';
            } else if (isAudioEndpoint && !contentType) {
                contentType = 'audio/wav';
            } else if (isVideoBinaryEndpoint && !contentType) {
                // Determine content type based on file extension
                if (req.originalUrl.endsWith('.mp4')) {
                    contentType = 'video/mp4';
                } else if (req.originalUrl.endsWith('.jpg')) {
                    contentType = 'image/jpeg';
                }
            }
            res.set('Content-Type', contentType);
            res.set('Cache-Control', 'no-cache');
            res.status(response.status).send(response.data);
        } else {
            // For JSON endpoints, send JSON response
            res.status(response.status).json(response.data);
        }

    } catch (error) {
        console.error(`❌ Proxy error: ${error.message}`);
        res.status(500).json({
            error: 'Proxy error',
            message: error.message
        });
    }
});

// Serve static files from dist directory (production build)
// IMPORTANT: This must come AFTER API proxy middleware to prevent /api routes from being caught
app.use(express.static(path.join(__dirname, 'dist')));

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

