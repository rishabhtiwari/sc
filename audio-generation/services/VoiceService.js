import { VoiceModelFactory } from '../models/VoiceModelFactory.js';
import pkg from 'wavefile';
const { WaveFile } = pkg;
import fs from 'fs';
import path from 'path';

/**
 * Voice Service for managing multiple TTS models
 */
export class VoiceService {
    constructor(outputDir = 'public', cacheDir = '/app/data/models') {
        this.models = new Map(); // modelKey -> model instance
        this.defaultModel = null;
        this.outputDir = outputDir;
        this.cacheDir = cacheDir;
        this.initializeOutputDir();
        this.initializeCacheDir();
    }

    initializeOutputDir() {
        if (!fs.existsSync(this.outputDir)) {
            fs.mkdirSync(this.outputDir, { recursive: true });
        }
    }

    initializeCacheDir() {
        if (!fs.existsSync(this.cacheDir)) {
            fs.mkdirSync(this.cacheDir, { recursive: true });
            console.log(`Created model cache directory: ${this.cacheDir}`);
        }
    }

    /**
     * Load a model by key
     */
    async loadModel(modelKey, setAsDefault = false) {
        if (this.models.has(modelKey)) {
            console.log(`Model ${modelKey} already loaded`);
            return this.models.get(modelKey);
        }

        console.log(`Loading model: ${modelKey}`);
        
        try {
            const model = VoiceModelFactory.createModel(modelKey, { cacheDir: this.cacheDir });
            await model.initialize();

            this.models.set(modelKey, model);

            if (setAsDefault || !this.defaultModel) {
                this.defaultModel = modelKey;
                console.log(`Set ${modelKey} as default model`);
            }

            return model;
        } catch (error) {
            console.error(`Failed to load model ${modelKey}:`, error);
            throw error;
        }
    }

    /**
     * Unload a model
     */
    async unloadModel(modelKey) {
        if (!this.models.has(modelKey)) {
            return false;
        }

        const model = this.models.get(modelKey);
        await model.cleanup();
        this.models.delete(modelKey);

        if (this.defaultModel === modelKey) {
            this.defaultModel = this.models.size > 0 ? this.models.keys().next().value : null;
        }

        console.log(`Unloaded model: ${modelKey}`);
        return true;
    }

    /**
     * Generate speech using specified model or default
     */
    async generateSpeech(text, options = {}) {
        const modelKey = options.model || this.defaultModel;
        
        if (!modelKey) {
            throw new Error('No model specified and no default model set');
        }

        if (!this.models.has(modelKey)) {
            throw new Error(`Model ${modelKey} is not loaded`);
        }

        const model = this.models.get(modelKey);
        const result = await model.generateSpeech(text, options);
        
        return result;
    }

    /**
     * Generate speech and save as audio file
     */
    async generateAudioFile(text, options = {}) {
        const result = await this.generateSpeech(text, options);

        // Check if result already contains a file path (for models like Kokoro that generate files directly)
        if (result.audioPath) {
            // Model already generated a file, just return the path info
            const filename = path.basename(result.audioPath);
            const modelKey = options.model || this.defaultModel;

            // Determine the correct audio_url based on the file location
            let audio_url;
            if (result.audioPath.includes('/app/public/')) {
                // For news records in public folder: /public/{news_id}/{filename}
                const relativePath = result.audioPath.replace('/app/public/', '');
                audio_url = `/${relativePath}`;
            } else {
                // For temp files in /app/public/temp/: /temp/{filename}
                audio_url = `/temp/${filename}`;
            }

            return {
                success: true,
                text: text,
                model: modelKey,
                audio_url: audio_url,
                filepath: result.audioPath,
                generation_time_ms: result.generation_time_ms || 0,
                audio_info: {
                    duration: result.duration,
                    sample_rate: result.sampleRate,
                    voice: result.voice
                }
            };
        }

        // For models that return raw audio data, create WAV file
        const wav = new WaveFile();
        wav.fromScratch(1, result.sampling_rate, '32f', result.audio);
        const audioBuffer = wav.toBuffer();

        // Generate filename
        const timestamp = Date.now();
        const modelKey = options.model || this.defaultModel;
        const filename = options.filename || `tts_${modelKey}_${timestamp}.wav`;
        const filepath = path.join(this.outputDir, filename);

        // Save audio file
        fs.writeFileSync(filepath, audioBuffer);

        return {
            success: true,
            text: text,
            model: modelKey,
            audio_url: `/${filename}`,
            filepath: filepath,
            generation_time_ms: result.generation_time_ms,
            audio_info: {
                samples: result.audio.length,
                sampling_rate: result.sampling_rate,
                duration_seconds: result.audio.length / result.sampling_rate
            }
        };
    }

    /**
     * Get loaded models info
     */
    getLoadedModels() {
        const loadedModels = {};
        for (const [key, model] of this.models) {
            loadedModels[key] = model.getModelInfo();
        }
        return {
            loaded_models: loadedModels,
            default_model: this.defaultModel,
            total_loaded: this.models.size
        };
    }

    /**
     * Get available models (not necessarily loaded)
     */
    getAvailableModels() {
        return VoiceModelFactory.getAvailableModels();
    }

    /**
     * Get models by language
     */
    getModelsByLanguage(language) {
        return VoiceModelFactory.getModelsByLanguage(language);
    }

    /**
     * Check service health
     */
    getHealthStatus() {
        return {
            status: 'ok',
            models_loaded: this.models.size,
            default_model: this.defaultModel,
            available_models: Object.keys(VoiceModelFactory.modelConfigs).length,
            timestamp: new Date().toISOString()
        };
    }

    /**
     * Cleanup all models
     */
    async cleanup() {
        for (const [key, model] of this.models) {
            await model.cleanup();
        }
        this.models.clear();
        this.defaultModel = null;
    }
}
