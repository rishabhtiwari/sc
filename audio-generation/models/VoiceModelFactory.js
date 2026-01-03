import { MMSVoiceModel } from './MMSVoiceModel.js';
import { SpeechT5VoiceModel } from './SpeechT5VoiceModel.js';
import { KokoroVoiceModelPython } from './KokoroVoiceModelPython.js';
import { BarkVoiceModel } from './BarkVoiceModel.js';
import { CoquiVoiceModel } from './CoquiVoiceModel.js';

/**
 * Factory for creating voice generation models
 */
export class VoiceModelFactory {
    static modelConfigs = {
        // Bark TTS Models (Multi-language with voice cloning, emotions, and music)
        'bark-en': {
            modelId: 'suno/bark',
            type: 'Bark',
            language: 'English',
            baseModel: 'suno/bark',
            config: {
                speaker: 'v2/en_speaker_0'
            }
        },
        'bark-de': {
            modelId: 'suno/bark',
            type: 'Bark',
            language: 'German',
            baseModel: 'suno/bark',
            config: {
                speaker: 'v2/de_speaker_0'
            }
        },
        'bark-es': {
            modelId: 'suno/bark',
            type: 'Bark',
            language: 'Spanish',
            baseModel: 'suno/bark',
            config: {
                speaker: 'v2/es_speaker_0'
            }
        },
        'bark-fr': {
            modelId: 'suno/bark',
            type: 'Bark',
            language: 'French',
            baseModel: 'suno/bark',
            config: {
                speaker: 'v2/fr_speaker_0'
            }
        },
        'bark-hi': {
            modelId: 'suno/bark',
            type: 'Bark',
            language: 'Hindi',
            baseModel: 'suno/bark',
            config: {
                speaker: 'v2/hi_speaker_0'
            }
        },
        'bark-it': {
            modelId: 'suno/bark',
            type: 'Bark',
            language: 'Italian',
            baseModel: 'suno/bark',
            config: {
                speaker: 'v2/it_speaker_0'
            }
        },
        'bark-ja': {
            modelId: 'suno/bark',
            type: 'Bark',
            language: 'Japanese',
            baseModel: 'suno/bark',
            config: {
                speaker: 'v2/ja_speaker_0'
            }
        },
        'bark-ko': {
            modelId: 'suno/bark',
            type: 'Bark',
            language: 'Korean',
            baseModel: 'suno/bark',
            config: {
                speaker: 'v2/ko_speaker_0'
            }
        },
        'bark-pl': {
            modelId: 'suno/bark',
            type: 'Bark',
            language: 'Polish',
            baseModel: 'suno/bark',
            config: {
                speaker: 'v2/pl_speaker_0'
            }
        },
        'bark-pt': {
            modelId: 'suno/bark',
            type: 'Bark',
            language: 'Portuguese',
            baseModel: 'suno/bark',
            config: {
                speaker: 'v2/pt_speaker_0'
            }
        },
        'bark-ru': {
            modelId: 'suno/bark',
            type: 'Bark',
            language: 'Russian',
            baseModel: 'suno/bark',
            config: {
                speaker: 'v2/ru_speaker_0'
            }
        },
        'bark-tr': {
            modelId: 'suno/bark',
            type: 'Bark',
            language: 'Turkish',
            baseModel: 'suno/bark',
            config: {
                speaker: 'v2/tr_speaker_0'
            }
        },
        'bark-zh': {
            modelId: 'suno/bark',
            type: 'Bark',
            language: 'Chinese',
            baseModel: 'suno/bark',
            config: {
                speaker: 'v2/zh_speaker_0'
            }
        },
        'bark-bn': {
            modelId: 'suno/bark',
            type: 'Bark',
            language: 'Bengali',
            baseModel: 'suno/bark',
            config: {
                speaker: 'v2/en_speaker_0' // Fallback to English
            }
        },
        'bark-ta': {
            modelId: 'suno/bark',
            type: 'Bark',
            language: 'Tamil',
            baseModel: 'suno/bark',
            config: {
                speaker: 'v2/en_speaker_0' // Fallback to English
            }
        },
        'bark-te': {
            modelId: 'suno/bark',
            type: 'Bark',
            language: 'Telugu',
            baseModel: 'suno/bark',
            config: {
                speaker: 'v2/en_speaker_0' // Fallback to English
            }
        },
        'bark-mr': {
            modelId: 'suno/bark',
            type: 'Bark',
            language: 'Marathi',
            baseModel: 'suno/bark',
            config: {
                speaker: 'v2/en_speaker_0' // Fallback to English
            }
        },
        'bark-gu': {
            modelId: 'suno/bark',
            type: 'Bark',
            language: 'Gujarati',
            baseModel: 'suno/bark',
            config: {
                speaker: 'v2/en_speaker_0' // Fallback to English
            }
        },
        'bark-kn': {
            modelId: 'suno/bark',
            type: 'Bark',
            language: 'Kannada',
            baseModel: 'suno/bark',
            config: {
                speaker: 'v2/en_speaker_0' // Fallback to English
            }
        },
        'bark-ml': {
            modelId: 'suno/bark',
            type: 'Bark',
            language: 'Malayalam',
            baseModel: 'suno/bark',
            config: {
                speaker: 'v2/en_speaker_0' // Fallback to English
            }
        },
        'bark-pa': {
            modelId: 'suno/bark',
            type: 'Bark',
            language: 'Punjabi',
            baseModel: 'suno/bark',
            config: {
                speaker: 'v2/en_speaker_0' // Fallback to English
            }
        },

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

        // Coqui TTS XTTS v2 - Universal Multi-lingual Model (58 speakers, 17 languages, voice cloning)
        'coqui-xtts': {
            modelId: 'tts_models/multilingual/multi-dataset/xtts_v2',
            type: 'Coqui',
            language: 'Multi-lingual',
            baseModel: 'coqui/XTTS-v2',
            config: {
                speaker: 'Claribel Dervla', // Default speaker (can speak all languages)
                language: 'en' // Default language (can be overridden per request)
            }
        },

        // Legacy language-specific aliases (all use the same universal XTTS v2 model)
        'coqui-en': {
            modelId: 'tts_models/multilingual/multi-dataset/xtts_v2',
            type: 'Coqui',
            language: 'English',
            baseModel: 'coqui/XTTS-v2',
            config: {
                speaker: 'Claribel Dervla',
                language: 'en'
            }
        },
        'coqui-hi': {
            modelId: 'tts_models/multilingual/multi-dataset/xtts_v2',
            type: 'Coqui',
            language: 'Hindi',
            baseModel: 'coqui/XTTS-v2',
            config: {
                speaker: 'Damien Black',
                language: 'hi'
            }
        },
        'coqui-es': {
            modelId: 'tts_models/multilingual/multi-dataset/xtts_v2',
            type: 'Coqui',
            language: 'Spanish',
            baseModel: 'coqui/XTTS-v2',
            config: {
                speaker: 'Claribel Dervla',
                language: 'es'
            }
        },
        'coqui-fr': {
            modelId: 'tts_models/multilingual/multi-dataset/xtts_v2',
            type: 'Coqui',
            language: 'French',
            baseModel: 'coqui/XTTS-v2',
            config: {
                speaker: 'Claribel Dervla',
                language: 'fr'
            }
        },
        'coqui-de': {
            modelId: 'tts_models/multilingual/multi-dataset/xtts_v2',
            type: 'Coqui',
            language: 'German',
            baseModel: 'coqui/XTTS-v2',
            config: {
                speaker: 'Claribel Dervla',
                language: 'de'
            }
        },
        'coqui-it': {
            modelId: 'tts_models/multilingual/multi-dataset/xtts_v2',
            type: 'Coqui',
            language: 'Italian',
            baseModel: 'coqui/XTTS-v2',
            config: {
                speaker: 'Claribel Dervla',
                language: 'it'
            }
        },
        'coqui-pt': {
            modelId: 'tts_models/multilingual/multi-dataset/xtts_v2',
            type: 'Coqui',
            language: 'Portuguese',
            baseModel: 'coqui/XTTS-v2',
            config: {
                speaker: 'Claribel Dervla',
                language: 'pt'
            }
        },
        'coqui-pl': {
            modelId: 'tts_models/multilingual/multi-dataset/xtts_v2',
            type: 'Coqui',
            language: 'Polish',
            baseModel: 'coqui/XTTS-v2',
            config: {
                speaker: 'Claribel Dervla',
                language: 'pl'
            }
        },
        'coqui-tr': {
            modelId: 'tts_models/multilingual/multi-dataset/xtts_v2',
            type: 'Coqui',
            language: 'Turkish',
            baseModel: 'coqui/XTTS-v2',
            config: {
                speaker: 'Claribel Dervla',
                language: 'tr'
            }
        },
        'coqui-ru': {
            modelId: 'tts_models/multilingual/multi-dataset/xtts_v2',
            type: 'Coqui',
            language: 'Russian',
            baseModel: 'coqui/XTTS-v2',
            config: {
                speaker: 'Claribel Dervla',
                language: 'ru'
            }
        },
        'coqui-nl': {
            modelId: 'tts_models/multilingual/multi-dataset/xtts_v2',
            type: 'Coqui',
            language: 'Dutch',
            baseModel: 'coqui/XTTS-v2',
            config: {
                speaker: 'Claribel Dervla',
                language: 'nl'
            }
        },
        'coqui-cs': {
            modelId: 'tts_models/multilingual/multi-dataset/xtts_v2',
            type: 'Coqui',
            language: 'Czech',
            baseModel: 'coqui/XTTS-v2',
            config: {
                speaker: 'Claribel Dervla',
                language: 'cs'
            }
        },
        'coqui-ar': {
            modelId: 'tts_models/multilingual/multi-dataset/xtts_v2',
            type: 'Coqui',
            language: 'Arabic',
            baseModel: 'coqui/XTTS-v2',
            config: {
                speaker: 'Claribel Dervla',
                language: 'ar'
            }
        },
        'coqui-zh': {
            modelId: 'tts_models/multilingual/multi-dataset/xtts_v2',
            type: 'Coqui',
            language: 'Chinese',
            baseModel: 'coqui/XTTS-v2',
            config: {
                speaker: 'Claribel Dervla',
                language: 'zh-cn'
            }
        },
        'coqui-ja': {
            modelId: 'tts_models/multilingual/multi-dataset/xtts_v2',
            type: 'Coqui',
            language: 'Japanese',
            baseModel: 'coqui/XTTS-v2',
            config: {
                speaker: 'Claribel Dervla',
                language: 'ja'
            }
        },
        'coqui-ko': {
            modelId: 'tts_models/multilingual/multi-dataset/xtts_v2',
            type: 'Coqui',
            language: 'Korean',
            baseModel: 'coqui/XTTS-v2',
            config: {
                speaker: 'Claribel Dervla',
                language: 'ko'
            }
        },
        'coqui-hu': {
            modelId: 'tts_models/multilingual/multi-dataset/xtts_v2',
            type: 'Coqui',
            language: 'Hungarian',
            baseModel: 'coqui/XTTS-v2',
            config: {
                speaker: 'Claribel Dervla',
                language: 'hu'
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
            case 'Bark':
                return new BarkVoiceModel(modelConfig.modelId, config);
            case 'Kokoro':
                return new KokoroVoiceModelPython(modelConfig.modelId, config);
            case 'Coqui':
                return new CoquiVoiceModel(modelConfig.modelId, config);
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
