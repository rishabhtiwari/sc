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
// This proxies to API server (not directly to video-generator) to maintain API Gateway pattern
app.post('/api/videos/background-audio', upload.single('file'), async (req, res) => {
    try {
        if (!req.file) {
            return res.status(400).json({ status: 'error', error: 'No file provided' });
        }

        const formData = new FormData();
        // IMPORTANT: Pass the file buffer as a stream with proper filename and content type
        formData.append('file', req.file.buffer, {
            filename: req.file.originalname,
            contentType: req.file.mimetype,
            knownLength: req.file.size
        });

        // IMPORTANT: Proxy to API server (API Gateway), not directly to video-generator
        const targetUrl = `${API_SERVER_URL}/api/videos/background-audio`;
        console.log(`🔄 Proxying file upload ${req.method} ${req.originalUrl} -> ${targetUrl} (api-server)`);
        console.log(`📎 File details: name=${req.file.originalname}, size=${req.file.size}, type=${req.file.mimetype}`);

        const headers = {
            ...formData.getHeaders()
        };

        // Forward Authorization header (CRITICAL for multi-tenant isolation)
        if (req.headers['authorization']) {
            headers['Authorization'] = req.headers['authorization'];
        }

        const response = await axios.post(targetUrl, formData, {
            headers: headers,
            maxBodyLength: Infinity,
            maxContentLength: Infinity,
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

// Special route for product media file uploads (must come before general API proxy)
// This proxies to API server to maintain API Gateway pattern
app.post('/api/products/:productId/upload-media', upload.array('files', 20), async (req, res) => {
    try {
        const productId = req.params.productId;

        // Check if files were uploaded
        if (!req.files || req.files.length === 0) {
            // No files - this might be JSON data with URLs
            // Check if there's JSON body data
            if (req.body && Object.keys(req.body).length > 0) {
                console.log(`🔄 Proxying product media URL upload (JSON) for product ${productId}`);
                console.log(`📎 JSON data:`, req.body);

                const targetUrl = `${API_SERVER_URL}/api/products/${productId}/upload-media`;

                const headers = {
                    'Content-Type': 'application/json'
                };

                // Forward Authorization header (CRITICAL for multi-tenant isolation)
                if (req.headers['authorization']) {
                    headers['Authorization'] = req.headers['authorization'];
                }

                // Forward multi-tenant headers
                if (req.headers['x-customer-id']) {
                    headers['X-Customer-ID'] = req.headers['x-customer-id'];
                }
                if (req.headers['x-user-id']) {
                    headers['X-User-ID'] = req.headers['x-user-id'];
                }

                const response = await axios.post(targetUrl, req.body, {
                    headers: headers,
                    validateStatus: () => true
                });

                return res.status(response.status).json(response.data);
            }

            // No files and no JSON data
            return res.status(400).json({ status: 'error', error: 'No files or media URLs provided' });
        }

        const formData = new FormData();

        // Append all files
        req.files.forEach((file, index) => {
            console.log(`📎 File ${index}: name=${file.originalname}, size=${file.size}, type=${file.mimetype}`);
            formData.append('files', file.buffer, {
                filename: file.originalname,
                contentType: file.mimetype,
                knownLength: file.size
            });
        });

        const targetUrl = `${API_SERVER_URL}/api/products/${productId}/upload-media`;
        console.log(`🔄 Proxying product media upload ${req.method} ${req.originalUrl} -> ${targetUrl} (api-server)`);
        console.log(`📎 Uploading ${req.files.length} files for product ${productId}`);

        const headers = {
            ...formData.getHeaders()
        };

        // Forward Authorization header (CRITICAL for multi-tenant isolation)
        if (req.headers['authorization']) {
            headers['Authorization'] = req.headers['authorization'];
        }

        // Forward multi-tenant headers
        if (req.headers['x-customer-id']) {
            headers['X-Customer-ID'] = req.headers['x-customer-id'];
        }
        if (req.headers['x-user-id']) {
            headers['X-User-ID'] = req.headers['x-user-id'];
        }

        const response = await axios.post(targetUrl, formData, {
            headers: headers,
            maxBodyLength: Infinity,
            maxContentLength: Infinity,
            validateStatus: () => true
        });

        res.status(response.status).json(response.data);
    } catch (error) {
        console.error(`❌ Product media upload proxy error: ${error.message}`);
        res.status(500).json({
            error: 'Product media upload proxy error',
            message: error.message
        });
    }
});

// API Proxy Routes - Forward ALL /api/* requests to API server (API Gateway pattern)
// IMPORTANT: This must come BEFORE static file middleware to prevent /api routes from being caught by static handler
// The API server will handle routing to appropriate backend services with proper JWT middleware
app.use('/api', async (req, res) => {
    try {
        // ALL requests go through API server - it acts as the API Gateway
        const targetUrl = `${API_SERVER_URL}${req.originalUrl}`;
        const targetService = 'api-server';

        console.log(`🔄 Proxying ${req.method} ${req.originalUrl} -> ${targetUrl} (${targetService})`);

        // Check if this is an image endpoint that returns binary data
        const isImageEndpoint = req.originalUrl.startsWith('/api/proxy-image') ||
                                req.originalUrl.startsWith('/api/image/cleaned/') ||
                                req.originalUrl.startsWith('/api/cleaned-image/');

        // Check if this is an audio endpoint that returns binary data
        const isAudioEndpoint = req.originalUrl.startsWith('/api/news/audio/serve') ||
                                req.originalUrl.startsWith('/api/voice/preview/audio/') ||
                                req.originalUrl.startsWith('/api/audio/proxy/') ||
                                req.originalUrl.match(/\/api\/videos\/background-audio\/[^\/]+\/download$/);

        // Check if this is a video endpoint that returns binary data
        const isVideoEndpoint = req.originalUrl.startsWith('/api/templates/preview/video/') ||
                                req.originalUrl.startsWith('/api/ecommerce/public/product/') ||
                                req.originalUrl.match(/\.mp4$/) ||
                                req.originalUrl.match(/\.webm$/) ||
                                req.originalUrl.match(/\.mov$/);

        // Check if this is a video endpoint that returns binary data
        const isVideoBinaryEndpoint = req.originalUrl.startsWith('/api/news/videos/shorts/') ||
                                      req.originalUrl.match(/\/api\/news\/videos\/[^\/]+\/(latest\.mp4|latest-thumbnail\.jpg)$/);

        // Check if this is a binary endpoint (image, audio, or video)
        const isBinaryEndpoint = isImageEndpoint || isAudioEndpoint || isVideoBinaryEndpoint || isVideoEndpoint;

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

        // Forward multi-tenant headers (CRITICAL for data isolation)
        if (req.headers['x-customer-id']) {
            headers['X-Customer-ID'] = req.headers['x-customer-id'];
        }
        if (req.headers['x-user-id']) {
            headers['X-User-ID'] = req.headers['x-user-id'];
        }

        const axiosConfig = {
            method: req.method,
            url: targetUrl,
            headers: headers,
            params: req.query,
            timeout: 600000, // 10 minutes for long-running operations (audio/video generation)
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
            } else if ((isVideoBinaryEndpoint || isVideoEndpoint) && !contentType) {
                // Determine content type based on file extension
                if (req.originalUrl.endsWith('.mp4')) {
                    contentType = 'video/mp4';
                } else if (req.originalUrl.endsWith('.webm')) {
                    contentType = 'video/webm';
                } else if (req.originalUrl.endsWith('.mov')) {
                    contentType = 'video/quicktime';
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

