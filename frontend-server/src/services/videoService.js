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
 * Merge latest videos into compilation with configuration
 * @param {Object} config - Configuration for video merging
 * @param {Array} config.categories - Categories to filter (optional)
 * @param {string} config.country - Country to filter (optional)
 * @param {string} config.language - Language to filter (optional)
 * @param {number} config.videoCount - Number of videos to merge
 * @param {string} config.title - Title for the video
 * @returns {Promise} API response
 */
export const mergeLatestVideos = (config = {}) => {
  return api.post('/news/videos/merge-latest', config);
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

