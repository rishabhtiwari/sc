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

export default {
  getStats,
  getNextImage,
  processImage,
  saveImage,
  skipImage,
  getCleanedImage,
};

