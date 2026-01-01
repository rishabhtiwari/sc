import { useState, useCallback } from 'react';
import api from '../services/api';

/**
 * Hook for audio generation
 * Handles TTS generation with different models and voices
 */
export const useAudioGeneration = () => {
  const [generating, setGenerating] = useState(false);
  const [audioUrl, setAudioUrl] = useState(null);
  const [audioConfig, setAudioConfig] = useState({
    model: 'kokoro-82m',
    language: 'en',
    voice: 'am_adam'
  });
  const [error, setError] = useState(null);

  /**
   * Auto-detect language from text
   */
  const detectLanguage = useCallback((text) => {
    if (!text) return 'en';

    // Check for Chinese characters
    if (/[\u4e00-\u9fa5]/.test(text)) return 'zh';

    // Check for Japanese characters
    if (/[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]/.test(text)) return 'ja';

    // Check for Korean characters
    if (/[\uac00-\ud7af]/.test(text)) return 'ko';

    // Check for Arabic characters
    if (/[\u0600-\u06ff]/.test(text)) return 'ar';

    // Check for Hindi/Devanagari characters
    if (/[\u0900-\u097f]/.test(text)) return 'hi';

    // Default to English
    return 'en';
  }, []);

  /**
   * Generate audio from text
   * @param {Object} options - Generation options
   * @param {string} options.endpoint - API endpoint to call
   * @param {string} options.text - Text to convert to speech
   * @param {string} options.model - TTS model (optional)
   * @param {string} options.language - Language code (optional)
   * @param {string} options.voice - Voice ID (optional)
   * @param {Object} options.sectionSpeeds - Section-specific speed adjustments (optional)
   * @param {Function} options.onSuccess - Callback on success
   * @param {Function} options.onError - Callback on error
   */
  const generate = useCallback(async (options) => {
    const {
      endpoint,
      text,
      model = audioConfig.model,
      language = audioConfig.language,
      voice = audioConfig.voice,
      sectionSpeeds = {},
      onSuccess,
      onError
    } = options;

    setGenerating(true);
    setError(null);

    try {
      const response = await api.post(endpoint, {
        text,
        model,
        language,
        voice,
        sectionPitches: sectionSpeeds // Backend expects sectionPitches
      });

      if (response.data.status === 'success') {
        const url = response.data.audio_url || response.data.url;
        setAudioUrl(url);
        setAudioConfig({ model, language, voice });
        
        if (onSuccess) {
          onSuccess(url, response.data);
        }

        return { success: true, audioUrl: url, data: response.data };
      } else {
        const errorMsg = response.data.message || 'Audio generation failed';
        setError(errorMsg);
        
        if (onError) {
          onError(errorMsg);
        }

        return { success: false, error: errorMsg };
      }
    } catch (err) {
      console.error('Audio generation error:', err);
      const errorMsg = err.response?.data?.message || err.message || 'Failed to generate audio';
      setError(errorMsg);
      
      if (onError) {
        onError(errorMsg);
      }

      return { success: false, error: errorMsg };
    } finally {
      setGenerating(false);
    }
  }, [audioConfig]);

  /**
   * Preview a voice with sample text
   */
  const previewVoice = useCallback(async (options) => {
    const {
      voice,
      model = audioConfig.model,
      language = audioConfig.language,
      sampleText = 'Hello, this is a voice preview.',
      onSuccess,
      onError
    } = options;

    return generate({
      endpoint: '/api/voice/preview',
      text: sampleText,
      model,
      language,
      voice,
      onSuccess,
      onError
    });
  }, [audioConfig, generate]);

  /**
   * Simple audio generation for Audio Studio
   * @param {Object} options - Generation options
   * @param {string} options.text - Text to convert to speech
   * @param {string} options.model - TTS model
   * @param {string} options.voice - Voice ID
   * @param {number} options.speed - Speech speed
   */
  const generateAudio = useCallback(async ({ text, model, voice, speed = 1.0 }) => {
    setGenerating(true);
    setError(null);

    try {
      // Call audio generation service via API proxy
      const response = await api.post('/audio/generate', {
        text,
        model,
        voice,
        speed,
        format: 'wav'
      });

      if (response.data.success) {
        const url = response.data.audio_url;
        setAudioUrl(url);
        return {
          success: true,
          audio_url: url,
          audio_info: response.data.audio_info
        };
      } else {
        throw new Error(response.data.error || 'Audio generation failed');
      }
    } catch (err) {
      const errorMessage = err.response?.data?.error || err.message || 'Failed to generate audio';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setGenerating(false);
    }
  }, []);

  /**
   * Reset the hook state
   */
  const reset = useCallback(() => {
    setGenerating(false);
    setAudioUrl(null);
    setError(null);
  }, []);

  return {
    generating,
    audioUrl,
    audioConfig,
    error,
    generate,
    generateAudio,
    previewVoice,
    detectLanguage,
    setAudioUrl,
    setAudioConfig,
    reset
  };
};

