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
  return api.post('/news/fetch/run');
};

/**
 * Get seed URLs with status
 * @returns {Promise} API response
 */
export const getSeedUrls = () => {
  return api.get('/news/seed-urls/status');
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

export default {
  getNews,
  getNewsById,
  getCategories,
  getFilters,
  getNewsStats,
  runNewsFetchJob,
  getSeedUrls,
  addSeedUrl,
  updateSeedUrl,
  deleteSeedUrl,
  getEnrichmentStatus,
};

