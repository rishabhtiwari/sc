import api from './api';

/**
 * News Service - API calls for news operations
 */

/**
 * Get news articles with filtering and pagination
 * @param {Object} params - Query parameters
 * @param {number} params.page - Page number
 * @param {number} params.pageSize - Articles per page
 * @param {string} params.category - Category filter
 * @param {string} params.language - Language filter
 * @param {string} params.country - Country filter
 * @param {string} params.status - Status filter
 * @returns {Promise} API response
 */
export const getNews = (params = {}) => {
  const queryParams = {
    page: params.page || 1,
    page_size: params.pageSize || 25,
  };

  if (params.category) queryParams.category = params.category;
  if (params.language) queryParams.language = params.language;
  if (params.country) queryParams.country = params.country;
  if (params.status) queryParams.status = params.status;

  return api.get('/news', { params: queryParams });
};

/**
 * Get news article by ID
 * @param {string} id - Article ID
 * @returns {Promise} API response
 */
export const getNewsById = (id) => {
  return api.get(`/news/${id}`);
};

/**
 * Get news categories with counts
 * @returns {Promise} API response
 */
export const getCategories = () => {
  return api.get('/news/categories');
};

/**
 * Get news filters (languages, countries)
 * @returns {Promise} API response
 */
export const getFilters = () => {
  return api.get('/news/filters');
};

/**
 * Get news statistics (from enrichment status)
 * @returns {Promise} API response
 */
export const getNewsStats = () => {
  return api.get('/news/enrichment/status');
};

/**
 * Run news fetch job
 * @returns {Promise} API response
 */
export const runNewsFetchJob = () => {
  return api.post('/news/run');
};

/**
 * Get seed URLs with status
 * @returns {Promise} API response
 */
export const getSeedUrls = () => {
  return api.get('/news/seed-urls/status');
};

/**
 * Get seed URL by partner ID
 * @param {string} partnerId - Partner ID
 * @returns {Promise} API response
 */
export const getSeedUrlById = (partnerId) => {
  return api.get(`/news/seed-urls/${partnerId}`);
};

/**
 * Get supported categories for seed URL configuration
 * @returns {Promise} API response with list of supported categories
 */
export const getSupportedCategories = () => {
  return api.get('/news/seed-urls/config/supported-categories');
};

/**
 * Add seed URL
 * @param {Object} data - Seed URL data
 * @returns {Promise} API response
 */
export const addSeedUrl = (data) => {
  return api.post('/news/seed-urls', data);
};

/**
 * Update seed URL
 * @param {string} partnerId - Partner ID
 * @param {Object} data - Updated data
 * @returns {Promise} API response
 */
export const updateSeedUrl = (partnerId, data) => {
  return api.put(`/news/seed-urls/${partnerId}`, data);
};

/**
 * Delete seed URL
 * @param {string} partnerId - Partner ID
 * @returns {Promise} API response
 */
export const deleteSeedUrl = (partnerId) => {
  return api.delete(`/news/seed-urls/${partnerId}`);
};

/**
 * Get enrichment status
 * @returns {Promise} API response
 */
export const getEnrichmentStatus = () => {
  return api.get('/news/enrichment/status');
};

/**
 * Update news article
 * @param {string} articleId - Article ID
 * @param {Object} data - Updated article data
 * @returns {Promise} API response
 */
export const updateArticle = (articleId, data) => {
  return api.put(`/news/${articleId}`, data);
};

/**
 * Get enrichment configuration
 * @returns {Promise} API response
 */
export const getEnrichmentConfig = () => {
  return api.get('/news/enrichment/config');
};

/**
 * Update enrichment configuration
 * @param {Object} config - Configuration updates
 * @returns {Promise} API response
 */
export const updateEnrichmentConfig = (config) => {
  return api.put('/news/enrichment/config', config);
};

/**
 * Reset enrichment configuration to defaults
 * @returns {Promise} API response
 */
export const resetEnrichmentConfig = () => {
  return api.post('/news/enrichment/config/reset');
};

export default {
  getNews,
  getNewsById,
  getCategories,
  getFilters,
  getNewsStats,
  runNewsFetchJob,
  getSeedUrls,
  getSeedUrlById,
  getSupportedCategories,
  addSeedUrl,
  updateSeedUrl,
  deleteSeedUrl,
  getEnrichmentStatus,
  updateArticle,
  getEnrichmentConfig,
  updateEnrichmentConfig,
  resetEnrichmentConfig,
};

