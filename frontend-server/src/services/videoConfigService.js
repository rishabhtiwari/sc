/**
 * Video Configuration Service - API calls for managing long video configurations
 */

import api from './api';

/**
 * Create a new video configuration
 * @param {Object} config - Configuration data
 * @returns {Promise} API response
 */
export const createConfig = (config) => {
  return api.post('/videos/configs', config);
};

/**
 * Get all video configurations
 * @param {string} status - Filter by status (optional)
 * @param {number} limit - Number of configs to return (optional)
 * @returns {Promise} API response
 */
export const getConfigs = (status = null, limit = 50) => {
  const params = {};
  if (status) params.status = status;
  if (limit) params.limit = limit;
  
  return api.get('/videos/configs', { params });
};

/**
 * Get a specific video configuration by ID
 * @param {string} configId - Configuration ID
 * @returns {Promise} API response
 */
export const getConfigById = (configId) => {
  return api.get(`/videos/configs/${configId}`);
};

/**
 * Update a video configuration
 * @param {string} configId - Configuration ID
 * @param {Object} updateData - Fields to update
 * @returns {Promise} API response
 */
export const updateConfig = (configId, updateData) => {
  return api.put(`/videos/configs/${configId}`, updateData);
};

/**
 * Delete a video configuration
 * @param {string} configId - Configuration ID
 * @returns {Promise} API response
 */
export const deleteConfig = (configId) => {
  return api.delete(`/videos/configs/${configId}`);
};

/**
 * Trigger video merge for a configuration
 * @param {string} configId - Configuration ID
 * @param {Array<string>} articleIds - Optional array of article IDs for manual selection
 * @returns {Promise} API response
 */
export const mergeConfig = (configId, articleIds = null) => {
  const payload = articleIds ? { article_ids: articleIds } : {};
  return api.post(`/videos/configs/${configId}/merge`, payload);
};

/**
 * Get merge status for a configuration
 * @param {string} configId - Configuration ID
 * @returns {Promise} API response
 */
export const getMergeStatus = (configId) => {
  return api.get(`/videos/configs/${configId}/merge-status`);
};

export default {
  createConfig,
  getConfigs,
  getConfigById,
  updateConfig,
  deleteConfig,
  mergeConfig,
  getMergeStatus
};

