import { BaseVoiceModel } from './BaseVoiceModel.js';
import { pipeline } from '@xenova/transformers';

/**
 * SpeechT5 Voice Model implementation
 * Uses SpeechT5 architecture which is supported by transformers.js
 */
export class SpeechT5VoiceModel extends BaseVoiceModel {
    constructor(modelId, config = {}) {
        super(modelId, config);
        this.language = config.language || 'English';
        this.baseModel = config.baseModel || modelId;
        this.architecture = 'SpeechT5';
        this.format = 'ONNX';
    }

    async initialize() {
        if (this.isInitialized) {
            return;
        }

        const isCached = this.isModelCached();
        const cachePath = this.getModelCachePath();

        console.log(`Initializing SpeechT5 TTS model: ${this.modelId} (${this.language})`);
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
            console.error(`Failed to initialize SpeechT5 TTS model ${this.modelId}:`, error);
            throw error;
        }
    }

    async generateSpeech(text, options = {}) {
        if (!this.isReady()) {
            throw new Error(`Model ${this.modelId} is not initialized`);
        }

        console.log(`Generating speech with ${this.modelId} for: "${text}"`);

        const startTime = Date.now();

        try {
            // SpeechT5 requires speaker embeddings - use default if not provided
            const speakerEmbeddings = options.speaker_embeddings ||
                'https://huggingface.co/datasets/Xenova/transformers.js-docs/resolve/main/speaker_embeddings.bin';

            const result = await this.pipeline(text, {
                speaker_embeddings: speakerEmbeddings,
                ...options
            });

            const endTime = Date.now();
            const generationTime = endTime - startTime;

            console.log(`✅ Speech generated in ${generationTime}ms`);

            return {
                audio: result.audio,
                sampling_rate: result.sampling_rate || 16000,
                generation_time_ms: generationTime
            };

        } catch (error) {
            console.error(`Speech generation failed for ${this.modelId}:`, error);
            throw error;
        }
    }

    getModelInfo() {
        return {
            ...super.getModelInfo(),
            language: this.language,
            architecture: this.architecture,
            format: this.format,
            baseModel: this.baseModel
        };
    }
}
