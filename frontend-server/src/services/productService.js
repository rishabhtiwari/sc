import api from './api';

/**
 * Product Service - API calls for e-commerce product video operations
 */

/**
 * Get all products with optional filters
 * @param {Object} params - Query parameters
 * @param {string} params.status - Filter by video generation status
 * @param {string} params.category - Filter by product category
 * @param {number} params.page - Page number
 * @param {number} params.page_size - Items per page
 * @returns {Promise} API response
 */
export const getProducts = (params = {}) => {
  return api.get('/products', { params });
};

/**
 * Get a specific product by ID
 * @param {string} productId - Product ID
 * @returns {Promise} API response
 */
export const getProduct = (productId) => {
  return api.get(`/products/${productId}`);
};

/**
 * Create a new product
 * @param {Object} data - Product data
 * @param {string} data.product_name - Product name
 * @param {string} data.description - Product description
 * @param {string} data.category - Product category
 * @param {number} data.price - Product price
 * @param {string} data.currency - Currency code (default: USD)
 * @returns {Promise} API response
 */
export const createProduct = (data) => {
  return api.post('/products', data);
};

/**
 * Update a product
 * @param {string} productId - Product ID
 * @param {Object} data - Updated product data
 * @returns {Promise} API response
 */
export const updateProduct = (productId, data) => {
  return api.put(`/products/${productId}`, data);
};

/**
 * Delete a product
 * @param {string} productId - Product ID
 * @returns {Promise} API response
 */
export const deleteProduct = (productId) => {
  return api.delete(`/products/${productId}`);
};

/**
 * Generate AI summary for product description
 * @param {string} productId - Product ID
 * @param {Object} options - Generation options
 * @param {boolean} options.regenerate - Force regeneration even if summary exists
 * @returns {Promise} API response
 */
export const generateSummary = (productId, options = {}) => {
  return api.post(`/products/${productId}/generate-summary`, options);
};

/**
 * Upload media files for a product
 * @param {string} productId - Product ID
 * @param {FileList|Array} files - Files to upload
 * @returns {Promise} API response
 */
export const uploadMedia = (productId, files) => {
  const formData = new FormData();
  
  // Add all files to form data
  Array.from(files).forEach((file) => {
    formData.append('files', file);
  });
  
  return api.post(`/products/${productId}/media`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};

/**
 * Generate audio from AI summary
 * @param {string} productId - Product ID
 * @param {Object} options - Audio generation options
 * @param {string} options.voice - Voice to use (default: af_sky)
 * @param {string} options.model - TTS model (default: kokoro-82m)
 * @returns {Promise} API response
 */
export const generateAudio = (productId, options = {}) => {
  return api.post(`/products/${productId}/generate-audio`, options);
};

/**
 * Generate final product video
 * @param {string} productId - Product ID
 * @param {Object} options - Video generation options
 * @param {string} options.template_id - Template to use
 * @returns {Promise} API response
 */
export const generateVideo = (productId, options = {}) => {
  return api.post(`/products/${productId}/generate-video`, options);
};

/**
 * Get product statistics
 * @returns {Promise} API response
 */
export const getProductStats = () => {
  return api.get('/products/stats');
};

export default {
  getProducts,
  getProduct,
  createProduct,
  updateProduct,
  deleteProduct,
  generateSummary,
  uploadMedia,
  generateAudio,
  generateVideo,
  getProductStats,
};

