import { MMSVoiceModel } from './MMSVoiceModel.js';
import { SpeechT5VoiceModel } from './SpeechT5VoiceModel.js';
import { KokoroVoiceModelPython } from './KokoroVoiceModelPython.js';

/**
 * Factory for creating voice generation models
 */
export class VoiceModelFactory {
    static modelConfigs = {
        // Kokoro-82M TTS Model (High-quality English TTS with 82M parameters)
        'kokoro-82m': {
            modelId: 'onnx-community/Kokoro-82M-v1.0-ONNX',
            type: 'Kokoro',
            language: 'English',
            baseModel: 'hexgrad/Kokoro-82M',
            config: {
                dtype: 'q8', // Options: fp32, fp16, q8, q4, q4f16
                voice: 'am_adam' // Default male voice
            }
        },

        // MMS Models for Hindi
        'mms-tts-hin': {
            modelId: 'Xenova/mms-tts-hin',
            type: 'MMS',
            language: 'Hindi',
            baseModel: 'facebook/mms-tts-hin',
            config: { quantized: false }
        },
        
        // Bengali Models
        'mms-tts-ben': {
            modelId: 'Xenova/mms-tts-ben',
            type: 'MMS',
            language: 'Bengali',
            baseModel: 'facebook/mms-tts-ben',
            config: { quantized: false }
        },
        
        // Tamil Models
        'mms-tts-tam': {
            modelId: 'Xenova/mms-tts-tam',
            type: 'MMS',
            language: 'Tamil',
            baseModel: 'facebook/mms-tts-tam',
            config: { quantized: false }
        },
        
        // Telugu Models
        'mms-tts-tel': {
            modelId: 'Xenova/mms-tts-tel',
            type: 'MMS',
            language: 'Telugu',
            baseModel: 'facebook/mms-tts-tel',
            config: { quantized: false }
        },
        
        // Marathi Models
        'mms-tts-mar': {
            modelId: 'Xenova/mms-tts-mar',
            type: 'MMS',
            language: 'Marathi',
            baseModel: 'facebook/mms-tts-mar',
            config: { quantized: false }
        },
        
        // Gujarati Models
        'mms-tts-guj': {
            modelId: 'Xenova/mms-tts-guj',
            type: 'MMS',
            language: 'Gujarati',
            baseModel: 'facebook/mms-tts-guj',
            config: { quantized: false }
        },
        
        // Kannada Models
        'mms-tts-kan': {
            modelId: 'Xenova/mms-tts-kan',
            type: 'MMS',
            language: 'Kannada',
            baseModel: 'facebook/mms-tts-kan',
            config: { quantized: false }
        },
        
        // Malayalam Models
        'mms-tts-mal': {
            modelId: 'Xenova/mms-tts-mal',
            type: 'MMS',
            language: 'Malayalam',
            baseModel: 'facebook/mms-tts-mal',
            config: { quantized: false }
        },
        
        // Punjabi Models
        'mms-tts-pan': {
            modelId: 'Xenova/mms-tts-pan',
            type: 'MMS',
            language: 'Punjabi',
            baseModel: 'facebook/mms-tts-pan',
            config: { quantized: false }
        }
    };

    /**
     * Create a voice model instance
     */
    static createModel(modelKey, customConfig = {}) {
        const modelConfig = this.modelConfigs[modelKey];
        
        if (!modelConfig) {
            throw new Error(`Unknown model key: ${modelKey}. Available models: ${Object.keys(this.modelConfigs).join(', ')}`);
        }

        const config = {
            ...modelConfig.config,
            ...customConfig,
            language: modelConfig.language,
            baseModel: modelConfig.baseModel
        };

        switch (modelConfig.type) {
            case 'Kokoro':
                return new KokoroVoiceModelPython(modelConfig.modelId, config);
            case 'MMS':
                return new MMSVoiceModel(modelConfig.modelId, config);
            case 'SpeechT5':
                return new SpeechT5VoiceModel(modelConfig.modelId, config);
            default:
                throw new Error(`Unsupported model type: ${modelConfig.type}`);
        }
    }

    /**
     * Get available model configurations
     */
    static getAvailableModels() {
        return Object.keys(this.modelConfigs).map(key => ({
            key,
            ...this.modelConfigs[key]
        }));
    }

    /**
     * Get model configuration by key
     */
    static getModelConfig(modelKey) {
        return this.modelConfigs[modelKey] || null;
    }

    /**
     * Register a new model configuration
     */
    static registerModel(key, config) {
        this.modelConfigs[key] = config;
    }

    /**
     * Get models by language
     */
    static getModelsByLanguage(language) {
        return Object.keys(this.modelConfigs)
            .filter(key => this.modelConfigs[key].language.toLowerCase() === language.toLowerCase())
            .map(key => ({
                key,
                ...this.modelConfigs[key]
            }));
    }
}
