import express from 'express';
import cors from 'cors';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { VoiceService } from './services/VoiceService.js';

// ES module equivalent of __dirname
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static('public'));
// app.use('/temp', express.static('data/temp')); // Serve temp files for Kokoro model

// Voice service instance with cache directory
const cacheDir = path.join(__dirname, 'data', 'models');
const voiceService = new VoiceService(path.join(__dirname, 'public'), cacheDir);

// Initialize default models
async function initializeModels() {
    console.log('Initializing voice models...');
    try {
        // Load Kokoro-82M as primary English model (high quality)
        await voiceService.loadModel('kokoro-82m', false);
        console.log('✅ Kokoro-82M English model loaded successfully!');

        // Hindi model disabled for now
        // await voiceService.loadModel('mms-tts-hin', true);
        // console.log('✅ Hindi MMS model loaded successfully!');

        console.log('🎉 Voice model(s) initialized successfully!');
    } catch (error) {
        console.error('Failed to initialize voice models:', error);
        process.exit(1);
    }
}

// Health check endpoint
app.get('/health', (req, res) => {
    res.json(voiceService.getHealthStatus());
});

// TTS endpoint - unified endpoint for all TTS models
app.post('/tts', async (req, res) => {
    try {
        const { text, model, voice, format = 'wav', news_id, filename } = req.body;

        if (!text) {
            return res.status(400).json({ error: 'Text is required' });
        }

        console.log(`🎤 Generating speech for: "${text.substring(0, 100)}${text.length > 100 ? '...' : ''}"`);
        console.log(`🤖 Model: ${model || 'default'}`);
        if (voice) console.log(`🎭 Voice: ${voice}`);
        if (news_id) console.log(`📰 News ID: ${news_id}`);
        if (filename) console.log(`📁 Filename: ${filename}`);

        // Build options object
        const options = { model, format };
        if (voice) options.voice = voice;
        if (news_id) options.news_id = news_id;
        if (filename) options.filename = filename;

        const result = await voiceService.generateAudioFile(text, options);

        // Add voice information to response if available
        const response = { ...result };
        if (voice) response.voice_used = voice;
        if (news_id) response.news_id = news_id;
        if (filename) response.filename = filename;

        res.json(response);

    } catch (error) {
        console.error('TTS generation error:', error);
        res.status(500).json({
            error: 'Failed to generate speech',
            details: error.message
        });
    }
});

// Get loaded models info
app.get('/models', (req, res) => {
    res.json(voiceService.getLoadedModels());
});

// Get available models (not necessarily loaded)
app.get('/models/available', (req, res) => {
    res.json({
        available_models: voiceService.getAvailableModels()
    });
});

// Get models by language
app.get('/models/language/:language', (req, res) => {
    const { language } = req.params;
    res.json({
        language: language,
        models: voiceService.getModelsByLanguage(language)
    });
});

// Load a new model
app.post('/models/load', async (req, res) => {
    try {
        const { modelKey, setAsDefault = false } = req.body;

        if (!modelKey) {
            return res.status(400).json({ error: 'modelKey is required' });
        }

        await voiceService.loadModel(modelKey, setAsDefault);
        res.json({
            success: true,
            message: `Model ${modelKey} loaded successfully`,
            model_info: voiceService.getLoadedModels()
        });

    } catch (error) {
        console.error('Model loading error:', error);
        res.status(500).json({
            error: 'Failed to load model',
            details: error.message
        });
    }
});

// Unload a model
app.delete('/models/:modelKey', async (req, res) => {
    try {
        const { modelKey } = req.params;
        const success = await voiceService.unloadModel(modelKey);

        if (success) {
            res.json({
                success: true,
                message: `Model ${modelKey} unloaded successfully`
            });
        } else {
            res.status(404).json({
                error: `Model ${modelKey} not found or not loaded`
            });
        }

    } catch (error) {
        console.error('Model unloading error:', error);
        res.status(500).json({
            error: 'Failed to unload model',
            details: error.message
        });
    }
});

// Get cache status
app.get('/cache/status', (req, res) => {
    try {
        const availableModels = voiceService.getAvailableModels();
        const cacheStatus = availableModels.map(model => {
            const tempModel = voiceService.models.get(model.key) ||
                             { isModelCached: () => false, getModelCachePath: () => path.join(cacheDir, model.key.replace(/[^a-zA-Z0-9-_]/g, '_')) };

            return {
                modelKey: model.key,
                language: model.language,
                isCached: fs.existsSync(path.join(cacheDir, model.modelId.replace(/[^a-zA-Z0-9-_]/g, '_'))),
                cachePath: path.join(cacheDir, model.modelId.replace(/[^a-zA-Z0-9-_]/g, '_'))
            };
        });

        res.json({
            cache_directory: cacheDir,
            total_models: availableModels.length,
            cached_models: cacheStatus.filter(m => m.isCached).length,
            models: cacheStatus
        });

    } catch (error) {
        console.error('Cache status error:', error);
        res.status(500).json({
            error: 'Failed to get cache status',
            details: error.message
        });
    }
});

// API endpoint to serve audio files for video generation service
app.get('/api/audio/:articleId/:audioType', (req, res) => {
    try {
        const { articleId, audioType } = req.params;

        // Validate audio type
        const validAudioTypes = ['title', 'description', 'content', 'short_summary'];
        if (!validAudioTypes.includes(audioType)) {
            return res.status(400).json({
                error: 'Invalid audio type',
                valid_types: validAudioTypes
            });
        }

        // Construct file path
        const audioFileName = `${audioType}.wav`;
        const audioFilePath = path.join(__dirname, 'public', articleId, audioFileName);

        // Check if file exists
        if (!fs.existsSync(audioFilePath)) {
            return res.status(404).json({
                error: 'Audio file not found',
                path: audioFilePath,
                article_id: articleId,
                audio_type: audioType
            });
        }

        // Get file stats
        const stats = fs.statSync(audioFilePath);

        // Set appropriate headers
        res.setHeader('Content-Type', 'audio/wav');
        res.setHeader('Content-Length', stats.size);
        res.setHeader('Content-Disposition', `attachment; filename="${articleId}_${audioType}.wav"`);

        // Stream the file
        const fileStream = fs.createReadStream(audioFilePath);
        fileStream.pipe(res);

        console.log(`Serving audio file: ${audioFilePath}`);

    } catch (error) {
        console.error('Audio file serving error:', error);
        res.status(500).json({
            error: 'Failed to serve audio file',
            details: error.message
        });
    }
});

// API endpoint to check if audio file exists
app.get('/api/audio/:articleId/:audioType/exists', (req, res) => {
    try {
        const { articleId, audioType } = req.params;

        // Validate audio type
        const validAudioTypes = ['title', 'description', 'content', 'short_summary'];
        if (!validAudioTypes.includes(audioType)) {
            return res.status(400).json({
                error: 'Invalid audio type',
                valid_types: validAudioTypes
            });
        }

        // Construct file path
        const audioFileName = `${audioType}.wav`;
        const audioFilePath = path.join(__dirname, 'public', articleId, audioFileName);

        // Check if file exists
        const exists = fs.existsSync(audioFilePath);

        res.json({
            exists: exists,
            article_id: articleId,
            audio_type: audioType,
            path: exists ? audioFilePath : null,
            size: exists ? fs.statSync(audioFilePath).size : null
        });

    } catch (error) {
        console.error('Audio file check error:', error);
        res.status(500).json({
            error: 'Failed to check audio file',
            details: error.message
        });
    }
});

// Start server
async function startServer() {
    // Create public directory for audio files
    const publicDir = path.join(__dirname, 'public');
    if (!fs.existsSync(publicDir)) {
        fs.mkdirSync(publicDir);
    }

    // Initialize voice models
    await initializeModels();

    // Start HTTP server
    app.listen(PORT, () => {
        console.log(`🚀 Voice Generation Server running on port ${PORT}`);
        console.log(`📋 Health check: http://localhost:${PORT}/health`);
        console.log(`🎤 TTS endpoint: POST http://localhost:${PORT}/tts`);
        console.log(`📊 Models info: GET http://localhost:${PORT}/models`);
        console.log(`📚 Available models: GET http://localhost:${PORT}/models/available`);
        console.log(`⚙️  Load model: POST http://localhost:${PORT}/models/load`);
        console.log(`🌍 Supported Languages: English (kokoro-82m)`);
    });
}

// Handle graceful shutdown
process.on('SIGINT', async () => {
    console.log('Shutting down gracefully...');
    await voiceService.cleanup();
    process.exit(0);
});

// Start the server
startServer().catch(console.error);
