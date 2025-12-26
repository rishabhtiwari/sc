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
 * @param {Array} mediaUrls - Array of media URLs or file objects
 * @returns {Promise} API response
 */
export const uploadMedia = (productId, mediaUrls) => {
  console.log('🔧 uploadMedia called with:', { productId, mediaUrls });
  console.log('🔧 mediaUrls type:', typeof mediaUrls);
  console.log('🔧 mediaUrls is array:', Array.isArray(mediaUrls));

  // Priority 1: If mediaUrls is an array of File objects (actual files to upload)
  if (Array.isArray(mediaUrls) && mediaUrls.length > 0 && mediaUrls.every(item => item instanceof File)) {
    console.log('🔧 Detected array of File objects, using FormData');
    const formData = new FormData();

    mediaUrls.forEach((file, index) => {
      console.log(`🔧 Appending file ${index}:`, file.name, file.type, file.size);
      formData.append('files', file);
    });

    return api.post(`/products/${productId}/upload-media`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  }

  // Priority 2: If mediaUrls is an array of URL strings, send directly
  if (Array.isArray(mediaUrls) && mediaUrls.every(item => typeof item === 'string')) {
    console.log('🔧 Detected URL strings, sending as JSON');
    return api.post(`/products/${productId}/upload-media`, {
      media_urls: mediaUrls
    });
  }

  // Priority 3: If mediaUrls is an array of objects with url property (URL-only entries)
  if (Array.isArray(mediaUrls) && mediaUrls.every(item => item && typeof item === 'object' && item.url && !item.file)) {
    console.log('🔧 Detected objects with url property (no file), sending as JSON');
    return api.post(`/products/${productId}/upload-media`, {
      media_urls: mediaUrls.map(item => item.url)
    });
  }

  // Priority 4: If mediaUrls is an array of objects with file property (File instances)
  if (Array.isArray(mediaUrls) && mediaUrls.length > 0 && mediaUrls.every(item => item && item.file instanceof File)) {
    console.log('🔧 Detected objects with File instances, extracting files and using FormData');
    const formData = new FormData();

    mediaUrls.forEach((item, index) => {
      console.log(`🔧 Appending file ${index}:`, item.file.name, item.file.type, item.file.size);
      formData.append('files', item.file);
    });

    return api.post(`/products/${productId}/upload-media`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  }

  // If we get here, something unexpected happened
  console.error('🔧 Unexpected mediaUrls format:', mediaUrls);
  console.error('🔧 First item:', mediaUrls[0]);
  console.error('🔧 First item has file?:', mediaUrls[0]?.file);
  console.error('🔧 First item file is File?:', mediaUrls[0]?.file instanceof File);
  throw new Error('Invalid media format. Expected File objects, URL strings, or URL objects.');
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
 * Delete a media file (image or video) from a product
 * @param {string} productId - Product ID
 * @param {string} filename - Filename to delete
 * @param {string} type - Media type ('images' or 'videos')
 * @returns {Promise} API response
 */
export const deleteMedia = (productId, filename, type = 'videos') => {
  return api.delete(`/ecommerce/public/product/${productId}/${type}/${filename}`);
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
  deleteMedia,
  generateAudio,
  generateVideo,
  getProductStats,
};

