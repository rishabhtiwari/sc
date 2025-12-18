import api from './api';

/**
 * Voice Service - API calls for voice/audio operations
 */

/**
 * Get audio generation statistics
 * @returns {Promise} API response
 */
export const getAudioStats = async () => {
  const response = await api.get('/news/audio/stats');
  return response.data;
};

/**
 * Generate audio for news articles
 * @param {Object} data - Generation parameters
 * @returns {Promise} API response
 */
export const generateAudio = async (data = {}) => {
  const response = await api.post('/news/audio/generate', data);
  return response.data;
};

/**
 * Get available voices
 * @returns {Promise} API response
 */
export const getAvailableVoices = async () => {
  const response = await api.get('/voice/voices');
  return response.data;
};

/**
 * Get available TTS models with their voices
 * @returns {Promise} API response
 */
export const getAvailableModels = async () => {
  const response = await api.get('/voice/available-models');
  return response.data;
};

/**
 * Get voice configuration
 * @returns {Promise} API response
 */
export const getConfig = async () => {
  const response = await api.get('/voice/config');
  return response.data;
};

/**
 * Update voice configuration
 * @param {Object} data - Configuration data
 * @returns {Promise} API response
 */
export const updateConfig = async (data) => {
  const response = await api.put('/voice/config', data);
  return response.data;
};

/**
 * Preview voice with sample text
 * @param {string} voiceId - Voice ID
 * @param {string} text - Sample text
 * @returns {Promise<string>} Audio URL
 * @throws {Error} Error with model_loading flag if model is still loading
 */
export const preview = async (voiceId, text) => {
  try {
    const response = await api.post('/voice/preview', {
      voice: voiceId,
      text: text,
    });
    return response.data.audioUrl;
  } catch (error) {
    // Check if error is due to model loading
    if (error.response?.status === 503 && error.response?.data?.model_loading) {
      const err = new Error(error.response.data.message || 'Model is loading, please try again');
      err.model_loading = true;
      err.model = error.response.data.model;
      throw err;
    }
    throw error;
  }
};

/**
 * Test voice with sample text
 * @param {Object} data - { text, voice, language }
 * @returns {Promise} API response
 */
export const testVoice = async (data) => {
  const response = await api.post('/voice/test', data);
  return response.data;
};

/**
 * Get list of audio files with pagination and filtering
 * @param {number} page - Page number
 * @param {string} status - Status filter (all, pending, generated)
 * @param {number} limit - Items per page
 * @returns {Promise} API response
 */
export const getAudioList = async (page = 1, status = 'all', limit = 20) => {
  const response = await api.get('/news/audio/list', {
    params: { page, status, limit }
  });
  return response.data;
};

export default {
  getAudioStats,
  generateAudio,
  getAvailableVoices,
  getAvailableModels,
  getConfig,
  updateConfig,
  preview,
  testVoice,
  getAudioList,
};

