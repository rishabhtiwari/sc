/**
 * Audio Models Configuration
 * Centralized configuration for TTS models, voices, and languages
 *
 * @deprecated This file contains hardcoded model configurations.
 * New components should fetch configuration from /api/audio/config instead.
 * This ensures the frontend adapts to the actual models loaded on the backend
 * (e.g., Bark on GPU, Kokoro on CPU).
 *
 * Migration guide:
 * 1. Fetch config: const response = await api.get('/audio/config');
 * 2. Use response.data.models for available models
 * 3. Use response.data.default_model for the default model
 * 4. Use model.voices for available voices per model
 */

export const AUDIO_MODELS = {
  'kokoro-82m': {
    id: 'kokoro-82m',
    name: 'Kokoro TTS',
    description: 'High-quality English text-to-speech',
    languages: ['en'],
    voices: {
      male: [
        { id: 'am_adam', name: 'Adam', description: 'American Male - Deep, authoritative' },
        { id: 'am_michael', name: 'Michael', description: 'American Male - Energetic, friendly' },
        { id: 'bm_george', name: 'George', description: 'British Male - Professional, clear' },
        { id: 'bm_lewis', name: 'Lewis', description: 'British Male - Warm, engaging' },
      ],
      female: [
        { id: 'af_heart', name: 'Heart', description: 'American Female - Soft, gentle' },
        { id: 'af_bella', name: 'Bella', description: 'American Female - Warm, friendly' },
        { id: 'af_nicole', name: 'Nicole', description: 'American Female - Professional, clear' },
        { id: 'af_sarah', name: 'Sarah', description: 'American Female - Energetic, upbeat' },
        { id: 'af_sky', name: 'Sky', description: 'American Female - Clear, professional' },
        { id: 'bf_emma', name: 'Emma', description: 'British Female - Elegant, refined' },
        { id: 'bf_isabella', name: 'Isabella', description: 'British Female - Sophisticated' },
      ]
    }
  },
  'mms-tts-hin': {
    id: 'mms-tts-hin',
    name: 'MMS Hindi TTS',
    description: 'Hindi text-to-speech',
    languages: ['hi'],
    voices: {
      default: [
        { id: 'hi_default', name: 'Default Hindi Voice', description: 'Standard Hindi voice' }
      ]
    }
  }
};

export const LANGUAGES = [
  { id: 'en', name: 'English', flag: '🇺🇸' },
  { id: 'hi', name: 'Hindi', flag: '🇮🇳' }
];

/**
 * Get available voices for a specific model
 * @param {string} modelId - The model ID
 * @returns {Array} Array of voice objects with category
 */
export const getAvailableVoices = (modelId) => {
  const model = AUDIO_MODELS[modelId];
  if (!model) return [];

  const voices = [];
  Object.entries(model.voices).forEach(([category, voiceList]) => {
    voices.push(...voiceList.map(v => ({ ...v, category })));
  });
  return voices;
};

/**
 * Auto-detect language from text
 * Simple heuristic: Check for common non-English characters
 * @param {string} text - The text to analyze
 * @returns {string} Detected language code
 */
export const detectLanguage = (text) => {
  if (!text) return 'en';

  // Check for Chinese characters
  if (/[\u4e00-\u9fa5]/.test(text)) return 'zh';

  // Check for Japanese characters (Hiragana, Katakana, Kanji)
  if (/[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]/.test(text)) return 'ja';

  // Check for Korean characters
  if (/[\uac00-\ud7af]/.test(text)) return 'ko';

  // Check for Arabic characters
  if (/[\u0600-\u06ff]/.test(text)) return 'ar';

  // Check for Hindi/Devanagari characters
  if (/[\u0900-\u097f]/.test(text)) return 'hi';

  // Default to English
  return 'en';
};

/**
 * Get default voice for a language
 * @param {string} language - Language code
 * @returns {string} Default voice ID
 */
export const getDefaultVoice = (language) => {
  switch (language) {
    case 'en':
      return 'am_adam';
    case 'hi':
      return 'hi_default';
    default:
      return 'am_adam';
  }
};

/**
 * Get default model for a language
 * @param {string} language - Language code
 * @returns {string} Default model ID
 */
export const getDefaultModel = (language) => {
  switch (language) {
    case 'en':
      return 'kokoro-82m';
    case 'hi':
      return 'mms-tts-hin';
    default:
      return 'kokoro-82m';
  }
};

