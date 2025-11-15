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

// Voice service instance with cache directory
const cacheDir = path.join(__dirname, 'data', 'models');
const voiceService = new VoiceService(path.join(__dirname, 'public'), cacheDir);

// Initialize default models
async function initializeModels() {
    console.log('Initializing voice models...');
    try {
        // Load default MMS Hindi model for Hindi voice generation
        await voiceService.loadModel('mms-tts-hin', true);
        console.log('✅ Hindi MMS model loaded successfully!');

        // Load English MMS model for English voice generation
        await voiceService.loadModel('mms-tts-eng', false);
        console.log('✅ English MMS model loaded successfully!');

        // Load SpeechT5 English model as alternative English option
        await voiceService.loadModel('speecht5-tts', false);
        console.log('✅ SpeechT5 English model loaded successfully!');

        console.log('🎉 All voice models initialized successfully!');
    } catch (error) {
        console.error('Failed to initialize voice models:', error);
        process.exit(1);
    }
}

// Health check endpoint
app.get('/health', (req, res) => {
    res.json(voiceService.getHealthStatus());
});

// TTS endpoint
app.post('/tts', async (req, res) => {
    try {
        const { text, model, format = 'wav' } = req.body;

        if (!text) {
            return res.status(400).json({ error: 'Text is required' });
        }

        console.log(`Generating speech for: "${text}" using model: ${model || 'default'}`);

        const result = await voiceService.generateAudioFile(text, { model, format });
        res.json(result);

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
        console.log(`🌍 Supported Languages: Hindi (mms-tts-hin), English (mms-tts-eng, speecht5-tts)`);
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
