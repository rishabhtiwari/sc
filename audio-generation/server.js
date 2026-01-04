import express from 'express';
import cors from 'cors';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import multer from 'multer';
import { VoiceService } from './services/VoiceService.js';

// ES module equivalent of __dirname
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json({ limit: '10mb' })); // Increase limit for large text content
app.use(express.urlencoded({ limit: '10mb', extended: true }));
app.use(express.static('public'));
app.use('/temp', express.static('public/temp')); // Serve temp files for preview and temporary audio

// Configure multer for file uploads
const storage = multer.diskStorage({
    destination: function (req, file, cb) {
        // Check if product_id is provided in the request body or query
        const productId = req.body.product_id || req.query.product_id;

        let uploadDir;
        if (productId) {
            // For product audio, use public/product/{product_id}/ directory
            uploadDir = path.join(__dirname, 'public', 'product', productId);
        } else {
            // For other uploads, use temp directory
            uploadDir = path.join(__dirname, 'public', 'temp');
        }

        // Ensure directory exists
        if (!fs.existsSync(uploadDir)) {
            fs.mkdirSync(uploadDir, { recursive: true });
        }
        cb(null, uploadDir);
    },
    filename: function (req, file, cb) {
        // Use original filename or generate unique name
        const uniqueName = file.originalname || `upload_${Date.now()}.wav`;
        cb(null, uniqueName);
    }
});

const upload = multer({ storage: storage });

// Voice service instance with cache directory
const cacheDir = path.join(__dirname, 'data', 'models');
const voiceService = new VoiceService(path.join(__dirname, 'public'), cacheDir);

// Initialize default models
async function initializeModels() {
    console.log('Initializing voice models...');

    // Detect if GPU is available by checking environment variable
    const useGPU = process.env.USE_GPU === 'true' || process.env.CUDA_VISIBLE_DEVICES !== undefined;

    try {
        if (useGPU) {
            console.log('🎮 GPU detected - Loading Coqui TTS XTTS v2 (GPU-accelerated)');

            // Load Coqui TTS as the default model (single universal model supports all 17 languages)
            await voiceService.loadModel('coqui-xtts', true);
            console.log('✅ Coqui TTS XTTS v2 loaded successfully (default)!');

            console.log('🎉 Coqui TTS XTTS v2 initialized successfully with GPU acceleration!');
            console.log('🎭 Features: 58 universal speakers, 17 languages, voice cloning, fast generation');
            console.log('🌐 Supported languages: English, Hindi, Spanish, French, German, Italian, Portuguese, Polish, Turkish, Russian, Dutch, Czech, Arabic, Chinese, Japanese, Korean, Hungarian');
            console.log('📊 Available speakers: Claribel Dervla, Damien Black, and 56 more');
            console.log('💡 All speakers can speak all languages - just specify language code in request (en, hi, es, fr, etc.)');
        } else {
            console.log('💻 CPU mode - Loading Kokoro-82M model (optimized for CPU)');

            // Load Kokoro-82M as the default model for CPU (faster on CPU than Coqui)
            await voiceService.loadModel('kokoro-82m', true);
            console.log('✅ Kokoro-82M model loaded successfully (default)!');

            console.log('🎉 Kokoro-82M model initialized successfully for CPU!');
            console.log('💡 For GPU acceleration and multi-language support, deploy with --gpu flag');
        }
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
        const { text, model, voice, speed, format = 'wav', language, news_id, product_id, filename } = req.body;

        if (!text) {
            return res.status(400).json({ error: 'Text is required' });
        }

        console.log(`🎤 Generating speech for: "${text.substring(0, 100)}${text.length > 100 ? '...' : ''}"`);
        console.log(`🤖 Model: ${model || 'default'}`);
        if (voice) console.log(`🎭 Voice: ${voice}`);
        if (language) console.log(`🌍 Language: ${language}`);
        if (speed) console.log(`⚡ Speed: ${speed}`);
        if (news_id) console.log(`📰 News ID: ${news_id}`);
        if (product_id) console.log(`🛍️ Product ID: ${product_id}`);
        if (filename) console.log(`📁 Filename: ${filename}`);

        // Build options object
        const options = { model, format };
        if (voice) options.voice = voice;
        if (language) options.language = language;
        if (speed) options.speed = speed;
        if (news_id) options.news_id = news_id;
        if (product_id) options.product_id = product_id;
        if (filename) options.filename = filename;

        const result = await voiceService.generateAudioFile(text, options);

        // Add voice information to response if available
        const response = { ...result };
        if (voice) response.voice_used = voice;
        if (speed) response.speed_used = speed;
        if (news_id) response.news_id = news_id;
        if (product_id) response.product_id = product_id;
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

// Upload audio file endpoint (for combined audio files)
app.post('/upload', upload.single('file'), (req, res) => {
    try {
        if (!req.file) {
            return res.status(400).json({ error: 'No file uploaded' });
        }

        console.log(`📤 File uploaded: ${req.file.filename}`);

        // Get file info
        const stats = fs.statSync(req.file.path);
        const fileSizeInBytes = stats.size;
        const fileSizeInMB = (fileSizeInBytes / (1024 * 1024)).toFixed(2);

        // Determine the correct URL based on product_id
        const productId = req.body.product_id || req.query.product_id;
        let audioUrl;
        if (productId) {
            audioUrl = `/product/${productId}/${req.file.filename}`;
        } else {
            audioUrl = `/temp/${req.file.filename}`;
        }

        console.log(`✅ File saved to: ${audioUrl}`);

        res.json({
            success: true,
            message: 'File uploaded successfully',
            audio_url: audioUrl,
            filename: req.file.filename,
            size_mb: fileSizeInMB,
            path: req.file.path
        });

    } catch (error) {
        console.error('Upload error:', error);
        res.status(500).json({
            error: 'Failed to upload file',
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

// Get available speakers for Coqui TTS XTTS v2
app.get('/speakers', async (req, res) => {
    try {
        const { CoquiVoiceModel } = await import('./models/CoquiVoiceModel.js');
        const speakers = await CoquiVoiceModel.getAvailableSpeakers();

        res.json({
            total: speakers.length,
            speakers: speakers,
            model: 'Coqui TTS XTTS v2',
            description: 'Pre-trained speakers supporting 16+ languages (dynamically loaded from server)'
        });
    } catch (error) {
        console.error('Speakers error:', error);
        res.status(500).json({ error: 'Failed to get speakers list' });
    }
});

// Get TTS configuration (default model, available voices, etc.)
app.get('/config', (req, res) => {
    try {
        const loadedModels = voiceService.getLoadedModels();
        const availableModels = voiceService.getAvailableModels();
        const defaultModel = loadedModels.default_model;

        // Get voices/speakers for loaded models
        const models = {};
        for (const [modelKey, modelInfo] of Object.entries(loadedModels.loaded_models)) {
            models[modelKey] = {
                name: modelInfo.model_name || modelKey,
                language: modelInfo.language || 'Unknown',
                voices: modelInfo.availableSpeakers || modelInfo.voices || [],
                voicesWithMetadata: modelInfo.voicesWithMetadata || [],  // Include gender metadata
                default_voice: modelInfo.defaultSpeaker || (modelInfo.availableSpeakers && modelInfo.availableSpeakers[0]) || null,
                supports_emotions: modelInfo.supportsEmotions || false,
                supports_music: modelInfo.supportsMusic || false,
                supports_voice_cloning: modelInfo.supportsVoiceCloning || false,
                supported_languages: modelInfo.supportedLanguages || [],
                supported_language_names: modelInfo.supportedLanguageNames || [],
                sampleTexts: modelInfo.sampleTexts || {},  // Include language-specific sample texts
                description: modelInfo.description || ''
            };
        }

        res.json({
            default_model: defaultModel,
            models: models,
            gpu_enabled: process.env.USE_GPU === 'true'
        });
    } catch (error) {
        console.error('Config error:', error);
        res.status(500).json({ error: 'Failed to get configuration' });
    }
});

// Get models by language
app.get('/models/language/:language', (req, res) => {
    const { language } = req.params;
    res.json({
        language: language,
        models: voiceService.getModelsByLanguage(language)
    });
});

// Preview endpoint with caching support
app.post('/preview', async (req, res) => {
    try {
        const { text, model, voice, language } = req.body;
        const customerId = req.headers['x-customer-id'] || 'default';
        const userId = req.headers['x-user-id'] || 'default';

        console.log(`🎤 Preview request - Model: ${model}, Voice: ${voice}, Language: ${language}`);

        // Step 1: Check if preview already exists in database AND MinIO
        const ASSET_SERVICE_URL = process.env.ASSET_SERVICE_URL || 'http://ichat-asset-service:8099';

        try {
            console.log(`🔍 Checking cache for: voice=${voice}, model=${model}, language=${language}`);

            const checkResponse = await axios.get(`${ASSET_SERVICE_URL}/api/audio-library/`, {
                params: {
                    page: 1,
                    page_size: 100,
                    folder: 'voice-previews'
                },
                headers: {
                    'x-customer-id': customerId,
                    'x-user-id': userId
                }
            });

            // Asset service returns 'audio_files' not 'items'
            const audioFiles = checkResponse.data.audio_files || checkResponse.data.items || [];

            if (checkResponse.data.success && audioFiles.length > 0) {
                console.log(`📚 Found ${audioFiles.length} cached previews in database`);

                // Find matching preview
                const existingPreview = audioFiles.find(item => {
                    const config = item.generation_config || {};
                    const matches = config.voice === voice &&
                                  config.model === model &&
                                  (config.language === language || item.language === language);

                    if (matches) {
                        console.log(`🎯 Match found: ${item.audio_id}`);
                    }
                    return matches;
                });

                if (existingPreview && existingPreview.url) {
                    // Verify the URL is accessible (MinIO check)
                    try {
                        const urlCheck = await axios.head(existingPreview.url, { timeout: 5000 });
                        if (urlCheck.status === 200) {
                            console.log(`✅ Found cached preview in DB + MinIO verified for ${voice} (${language})`);
                            console.log(`   URL: ${existingPreview.url}`);
                            return res.json({
                                success: true,
                                audio_url: existingPreview.url,
                                duration: existingPreview.duration || 0,
                                cached: true,
                                audio_id: existingPreview.audio_id
                            });
                        } else {
                            console.warn(`⚠️ Preview found in DB but MinIO returned status ${urlCheck.status}`);
                        }
                    } catch (urlError) {
                        console.warn(`⚠️ Preview found in DB but MinIO verification failed: ${urlError.message}`);
                        console.warn(`   URL: ${existingPreview.url}`);
                        // Continue to regenerate if MinIO file is missing
                    }
                } else {
                    console.log(`📝 No matching preview found in database`);
                }
            } else {
                console.log(`📝 No cached previews found in database`);
            }
        } catch (error) {
            console.warn(`⚠️ Could not check cache: ${error.message}`);
            // Continue to generate new preview
        }

        // Step 2: Generate new preview audio
        console.log(`🎙️ Generating new preview for ${voice} (${language})`);
        console.log(`   Text length: ${text.length} characters`);

        const options = {
            model: model,
            voice: voice,
            language: language,
            speed: 1.0
        };

        const result = await voiceService.generateAudioFile(text, options);
        console.log(`✅ Audio generated: ${result.audio_url}`);

        // Step 3: Save to audio library (asset service will handle MinIO upload)
        try {
            console.log(`💾 Saving preview to asset service...`);
            console.log(`   Customer: ${customerId}, User: ${userId}`);

            const saveResponse = await axios.post(
                `${ASSET_SERVICE_URL}/api/audio-library/`,
                {
                    text: text,
                    audio_url: result.audio_url,
                    duration: result.duration || 0,
                    voice: voice,
                    voice_name: voice,
                    language: language,
                    speed: 1.0,
                    model: model,
                    folder: 'voice-previews',
                    tags: ['preview', model, language, voice]
                },
                {
                    headers: {
                        'x-customer-id': customerId,
                        'x-user-id': userId,
                        'Content-Type': 'application/json'
                    }
                }
            );

            if (saveResponse.data.success) {
                const savedUrl = saveResponse.data.audio_url || saveResponse.data.url;
                const audioId = saveResponse.data.audio_id || saveResponse.data.id;

                console.log(`✅ Preview saved to MinIO + MongoDB`);
                console.log(`   Audio ID: ${audioId}`);
                console.log(`   MinIO URL: ${savedUrl}`);

                return res.json({
                    success: true,
                    audio_url: savedUrl,
                    duration: result.duration || 0,
                    cached: false,
                    audio_id: audioId
                });
            } else {
                console.warn(`⚠️ Asset service returned success=false`);
                console.warn(`   Response: ${JSON.stringify(saveResponse.data)}`);
            }
        } catch (error) {
            console.error(`❌ Could not save to library: ${error.message}`);
            if (error.response) {
                console.error(`   Status: ${error.response.status}`);
                console.error(`   Data: ${JSON.stringify(error.response.data)}`);
            }
            // Return temp URL if saving fails
        }

        // Step 4: Return temp URL if saving to library failed
        console.log(`⚠️ Returning temp URL (not saved to MinIO)`);
        res.json({
            success: true,
            audio_url: result.audio_url,
            duration: result.duration || 0,
            cached: false
        });

    } catch (error) {
        console.error('Preview generation error:', error);
        res.status(500).json({
            success: false,
            error: 'Failed to generate preview',
            details: error.message
        });
    }
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

// Delete product audio folder
app.delete('/product/:productId', (req, res) => {
    try {
        const { productId } = req.params;
        const productDir = path.join(__dirname, 'public', 'product', productId);

        console.log(`🗑️ Deleting product audio folder: ${productDir}`);

        // Check if directory exists
        if (!fs.existsSync(productDir)) {
            return res.status(404).json({
                success: false,
                message: 'Product audio folder not found',
                product_id: productId
            });
        }

        // Delete directory recursively
        fs.rmSync(productDir, { recursive: true, force: true });

        console.log(`✅ Deleted product audio folder: ${productId}`);

        res.json({
            success: true,
            message: 'Product audio folder deleted successfully',
            product_id: productId
        });

    } catch (error) {
        console.error('Delete product folder error:', error);
        res.status(500).json({
            success: false,
            error: 'Failed to delete product audio folder',
            details: error.message
        });
    }
});

// Cleanup temp audio file (called by asset-service after saving to library)
app.delete('/api/cleanup/temp/:filename', (req, res) => {
    try {
        const { filename } = req.params;
        const tempFilePath = path.join(__dirname, 'public', 'temp', filename);

        console.log(`🗑️ Cleanup request for temp file: ${filename}`);

        // Security check: ensure filename doesn't contain path traversal
        if (filename.includes('..') || filename.includes('/') || filename.includes('\\')) {
            return res.status(400).json({
                success: false,
                error: 'Invalid filename',
                message: 'Filename cannot contain path separators'
            });
        }

        // Check if file exists
        if (!fs.existsSync(tempFilePath)) {
            console.log(`⚠️ Temp file not found (may have been already deleted): ${filename}`);
            return res.json({
                success: true,
                message: 'File not found (may have been already deleted)',
                filename: filename
            });
        }

        // Delete the file
        fs.unlinkSync(tempFilePath);
        console.log(`✅ Deleted temp file: ${filename}`);

        res.json({
            success: true,
            message: 'Temp file deleted successfully',
            filename: filename
        });

    } catch (error) {
        console.error('Cleanup temp file error:', error);
        res.status(500).json({
            success: false,
            error: 'Failed to delete temp file',
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

        // Show default model info
        const loadedModels = voiceService.getLoadedModels();
        const defaultModel = loadedModels.default_model;

        if (defaultModel && defaultModel.startsWith('coqui')) {
            console.log(`🌍 Default Model: Coqui TTS XTTS v2 (${defaultModel})`);
            console.log(`🎭 Features: 58 speakers, 17 languages, voice cloning, fast generation`);
            console.log(`🌐 Languages: English, Hindi, Spanish, French, German, Italian, Portuguese, Polish, Turkish, Russian, Dutch, Czech, Arabic, Chinese, Japanese, Korean, Hungarian`);
            console.log(`💡 Specify language in request: { "language": "es" } for Spanish, { "language": "fr" } for French, etc.`);
        } else if (defaultModel && defaultModel.startsWith('bark')) {
            console.log(`🌍 Default Model: Bark (${defaultModel})`);
            console.log(`🎭 Bark Features: Voice cloning, emotions, music, 13+ languages`);
            console.log(`📝 Emotion tags: [laughs], [sighs], [gasps], [clears throat]`);
            console.log(`🎵 Music: Wrap lyrics in ♪ symbols`);
        } else if (defaultModel && defaultModel.startsWith('kokoro')) {
            console.log(`🌍 Default Model: Kokoro (${defaultModel})`);
            console.log(`🎭 Kokoro Features: Fast CPU inference, natural English voices`);
        } else {
            console.log(`🌍 Default Model: ${defaultModel || 'None'}`);
        }
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
