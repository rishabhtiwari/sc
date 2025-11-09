import fs from 'fs';
import path from 'path';

/**
 * Base class for all voice generation models
 */
export class BaseVoiceModel {
    constructor(modelId, config = {}) {
        this.modelId = modelId;
        this.config = config;
        this.isInitialized = false;
        this.pipeline = null;
        this.cacheDir = config.cacheDir || '/app/data/models';
        this.ensureCacheDir();
    }

    /**
     * Ensure cache directory exists
     */
    ensureCacheDir() {
        if (!fs.existsSync(this.cacheDir)) {
            fs.mkdirSync(this.cacheDir, { recursive: true });
            console.log(`Created cache directory: ${this.cacheDir}`);
        }
    }

    /**
     * Get model cache path
     */
    getModelCachePath() {
        const modelName = this.modelId.replace(/[^a-zA-Z0-9-_]/g, '_');
        return path.join(this.cacheDir, modelName);
    }

    /**
     * Check if model is cached
     */
    isModelCached() {
        const cachePath = this.getModelCachePath();
        return fs.existsSync(cachePath) && fs.readdirSync(cachePath).length > 0;
    }

    /**
     * Initialize the model - must be implemented by subclasses
     */
    async initialize() {
        throw new Error('initialize() method must be implemented by subclasses');
    }

    /**
     * Generate speech from text - must be implemented by subclasses
     */
    async generateSpeech(text, options = {}) {
        throw new Error('generateSpeech() method must be implemented by subclasses');
    }

    /**
     * Get model information
     */
    getModelInfo() {
        return {
            modelId: this.modelId,
            isInitialized: this.isInitialized,
            isCached: this.isModelCached(),
            cachePath: this.getModelCachePath(),
            config: this.config
        };
    }

    /**
     * Check if model is ready for use
     */
    isReady() {
        return this.isInitialized && this.pipeline !== null;
    }

    /**
     * Cleanup resources
     */
    async cleanup() {
        this.pipeline = null;
        this.isInitialized = false;
    }
}
