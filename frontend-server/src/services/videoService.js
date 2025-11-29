import api from './api';

/**
 * Video Service - API calls for video operations
 */

/**
 * Get video generation statistics
 * @returns {Promise} API response
 */
export const getVideoStats = () => {
  return api.get('/news/videos/stats');
};

/**
 * Generate videos for news articles
 * @param {Object} data - Generation parameters
 * @returns {Promise} API response
 */
export const generateVideos = (data = {}) => {
  return api.post('/news/videos/generate', data);
};

/**
 * Merge latest videos into compilation
 * @returns {Promise} API response
 */
export const mergeLatestVideos = () => {
  return api.post('/news/videos/merge-latest');
};

/**
 * Get video by ID
 * @param {string} id - Video ID
 * @returns {Promise} API response
 */
export const getVideoById = (id) => {
  return api.get(`/news/videos/${id}`);
};

export default {
  getVideoStats,
  generateVideos,
  mergeLatestVideos,
  getVideoById,
};

