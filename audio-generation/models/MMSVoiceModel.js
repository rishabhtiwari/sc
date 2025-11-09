import { pipeline } from '@xenova/transformers';
import { BaseVoiceModel } from './BaseVoiceModel.js';

/**
 * MMS (Massively Multilingual Speech) Voice Model implementation
 */
export class MMSVoiceModel extends BaseVoiceModel {
    constructor(modelId, config = {}) {
        super(modelId, config);
        this.language = config.language || 'Unknown';
        this.baseModel = config.baseModel || modelId;
        this.architecture = 'VITS';
        this.format = 'ONNX';
    }

    async initialize() {
        if (this.isInitialized) {
            return;
        }

        const isCached = this.isModelCached();
        const cachePath = this.getModelCachePath();

        console.log(`Initializing MMS TTS model: ${this.modelId} (${this.language})`);
        console.log(`Model cached: ${isCached ? 'Yes' : 'No'} at ${cachePath}`);

        if (isCached) {
            console.log(`Loading cached model from: ${cachePath}`);
        } else {
            console.log(`Downloading model for first time...`);
        }

        try {
            this.pipeline = await pipeline('text-to-speech', this.modelId, {
                quantized: this.config.quantized || false,
                cache_dir: cachePath,
                local_files_only: false, // Allow downloading if not cached
                ...this.config.pipelineOptions
            });

            this.isInitialized = true;

            if (!isCached && this.isModelCached()) {
                console.log(`✅ Model ${this.modelId} downloaded and cached successfully!`);
            } else if (isCached) {
                console.log(`✅ Model ${this.modelId} loaded from cache successfully!`);
            } else {
                console.log(`✅ Model ${this.modelId} initialized successfully!`);
            }

        } catch (error) {
            console.error(`Failed to initialize MMS TTS model ${this.modelId}:`, error);
            throw error;
        }
    }

    async generateSpeech(text, options = {}) {
        if (!this.isReady()) {
            throw new Error(`Model ${this.modelId} is not initialized`);
        }

        console.log(`Generating speech with ${this.modelId} for: "${text}"`);
        
        const startTime = Date.now();
        const output = await this.pipeline(text, options);
        const generationTime = Date.now() - startTime;
        
        console.log(`Speech generated in ${generationTime}ms`);
        console.log(`Audio length: ${output.audio.length} samples`);
        console.log(`Sampling rate: ${output.sampling_rate} Hz`);
        
        return {
            audio: output.audio,
            sampling_rate: output.sampling_rate,
            generation_time_ms: generationTime,
            model_id: this.modelId,
            text: text
        };
    }

    getModelInfo() {
        return {
            ...super.getModelInfo(),
            language: this.language,
            baseModel: this.baseModel,
            architecture: this.architecture,
            format: this.format,
            type: 'MMS'
        };
    }
}
