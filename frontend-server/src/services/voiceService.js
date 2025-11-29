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
 */
export const preview = async (voiceId, text) => {
  const response = await api.post('/voice/preview', {
    voice: voiceId,
    text: text,
  });
  return response.data.audioUrl;
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

export default {
  getAudioStats,
  generateAudio,
  getAvailableVoices,
  getConfig,
  updateConfig,
  preview,
  testVoice,
};

