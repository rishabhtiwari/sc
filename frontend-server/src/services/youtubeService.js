import api from './api';

/**
 * YouTube Service - API calls for YouTube operations
 */

/**
 * Get YouTube upload statistics
 * @returns {Promise} API response
 */
export const getStats = () => {
  return api.get('/youtube/stats');
};

/**
 * Upload latest 20 news to YouTube
 * @returns {Promise} API response
 */
export const uploadLatest20 = () => {
  return api.post('/youtube/upload-latest-20');
};

/**
 * Get pending YouTube Shorts (ready to upload)
 * @returns {Promise} API response
 */
export const getPendingShorts = () => {
  return api.get('/youtube/shorts/pending');
};

/**
 * Upload a single YouTube Short
 * @param {string} articleId - Article ID
 * @returns {Promise} API response
 */
export const uploadShort = (articleId) => {
  return api.post(`/youtube/shorts/upload/${articleId}`);
};

/**
 * Handle OAuth callback
 * @param {string} code - OAuth authorization code
 * @returns {Promise} API response
 */
export const handleOAuthCallback = (code) => {
  return api.post('/youtube/oauth-callback', { code });
};

export default {
  getStats,
  uploadLatest20,
  getPendingShorts,
  uploadShort,
  handleOAuthCallback,
};

