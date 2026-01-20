import api from './api';

/**
 * Image Service - API calls for image/watermark operations
 */

/**
 * Get statistics for image cleaning
 * @returns {Promise} API response
 */
export const getStats = () => {
  return api.get('/image/stats');
};

/**
 * List all images with pagination and filtering
 * @param {Object} params - Query parameters
 * @param {number} params.page - Page number (default: 1)
 * @param {number} params.limit - Items per page (default: 20)
 * @param {string} params.status - Status filter: 'all', 'pending', 'cleaned', 'skipped' (default: 'all')
 * @returns {Promise} API response
 */
export const listImages = (params = {}) => {
  return api.get('/image/images', { params });
};

/**
 * Get next pending image for cleaning
 * @returns {Promise} API response
 */
export const getNextImage = () => {
  return api.get('/image/next');
};

/**
 * Process image to remove watermark
 * @param {Object} data - Image and mask data
 * @param {string} data.doc_id - Document ID
 * @param {string} data.image_data - Base64 image data
 * @param {string} data.mask_data - Base64 mask data
 * @returns {Promise} API response
 */
export const processImage = (data) => {
  return api.post('/image/process', data);
};

/**
 * Save cleaned image and mark as done
 * @param {Object} data - Image data
 * @param {string} data.doc_id - Document ID
 * @param {string} data.image_data - Base64 image data
 * @returns {Promise} API response
 */
export const saveImage = (data) => {
  return api.post('/image/save', data);
};

/**
 * Replace image URL for an article
 * @param {Object} data - Replacement data
 * @param {string} data.doc_id - Document ID
 * @param {string} data.image_url - New image URL
 * @returns {Promise} API response
 */
export const replaceImage = (data) => {
  return api.post('/image/replace-image', data);
};

/**
 * Skip image (mark as skipped)
 * @param {string} docId - Document ID
 * @returns {Promise} API response
 */
export const skipImage = (docId) => {
  return api.post('/image/skip', { doc_id: docId });
};

/**
 * Get cleaned image by document ID
 * @param {string} docId - Document ID
 * @returns {Promise} API response
 */
export const getCleanedImage = (docId) => {
  return api.get(`/image/cleaned/${docId}`, {
    responseType: 'blob',
  });
};

/**
 * Get image cleaning configuration
 * @returns {Promise} API response with config { auto_mark_cleaned: boolean }
 */
export const getImageConfig = () => {
  return api.get('/image/config');
};

/**
 * Update image cleaning configuration
 * @param {Object} config - Configuration object
 * @param {boolean} config.auto_mark_cleaned - Whether to auto-mark images as cleaned
 * @returns {Promise} API response
 */
export const updateImageConfig = (config) => {
  return api.put('/image/config', config);
};

export default {
  getStats,
  listImages,
  getNextImage,
  processImage,
  saveImage,
  replaceImage,
  skipImage,
  getCleanedImage,
  getImageConfig,
  updateImageConfig,
};

