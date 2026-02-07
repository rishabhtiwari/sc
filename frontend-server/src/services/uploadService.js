import api from './api';

/**
 * Upload Service
 * Generic service for uploading content to various social media platforms
 */

// ==================== Platform Account Management ====================

/**
 * Get connected accounts for a platform
 * @param {string} platform - Platform name (youtube, instagram, tiktok, etc.)
 * @returns {Promise} List of connected accounts
 */
export const getConnectedAccounts = async (platform) => {
  switch (platform) {
    case 'youtube':
      const response = await api.get('/youtube/credentials');
      return response.data.credentials || [];
    
    case 'instagram':
      const igResponse = await api.get('/social-media/instagram/credentials');
      return igResponse.data.credentials || [];
    
    // Add more platforms as needed
    default:
      throw new Error(`Platform ${platform} not supported`);
  }
};

// ==================== YouTube Upload ====================

/**
 * Upload video to YouTube
 * @param {Object} params - Upload parameters
 * @param {string} params.videoUrl - URL or path to video file
 * @param {string} params.title - Video title
 * @param {string} params.description - Video description
 * @param {Array} params.tags - Video tags
 * @param {string} params.categoryId - YouTube category ID
 * @param {string} params.privacyStatus - Privacy status (public, private, unlisted)
 * @param {string} params.credentialId - YouTube credential ID to use
 * @returns {Promise} Upload result
 */
export const uploadToYouTube = async (params) => {
  const {
    videoUrl,
    title,
    description,
    tags = [],
    categoryId = '22', // People & Blogs
    privacyStatus = 'public',
    credentialId
  } = params;

  const response = await api.post('/youtube/upload', {
    video_url: videoUrl,
    title,
    description,
    tags,
    category_id: categoryId,
    privacy_status: privacyStatus,
    credential_id: credentialId
  });

  return response.data;
};

// ==================== Instagram Upload ====================

/**
 * Upload content to Instagram
 * @param {Object} params - Upload parameters
 * @param {string} params.mediaUrl - URL to media file
 * @param {string} params.caption - Post caption
 * @param {string} params.mediaType - Media type (IMAGE, VIDEO, REELS)
 * @param {string} params.credentialId - Instagram credential ID to use
 * @returns {Promise} Upload result
 */
export const uploadToInstagram = async (params) => {
  const {
    mediaUrl,
    caption,
    mediaType = 'VIDEO',
    credentialId
  } = params;

  const response = await api.post('/social-media/instagram/upload', {
    media_url: mediaUrl,
    caption,
    media_type: mediaType,
    credential_id: credentialId
  });

  return response.data;
};

// ==================== Generic Upload Function ====================

/**
 * Upload content to any platform
 * @param {string} platform - Platform name
 * @param {Object} params - Platform-specific upload parameters
 * @returns {Promise} Upload result
 */
export const uploadToPlatform = async (platform, params) => {
  switch (platform) {
    case 'youtube':
      return uploadToYouTube(params);
    
    case 'instagram':
      return uploadToInstagram(params);
    
    // Add more platforms as needed
    default:
      throw new Error(`Platform ${platform} not supported`);
  }
};

// ==================== Platform Configuration ====================

export const PLATFORMS = {
  youtube: {
    id: 'youtube',
    name: 'YouTube',
    icon: '📺',
    color: 'from-red-500 to-red-600',
    supportedFormats: ['video/mp4', 'video/webm', 'video/mov'],
    maxFileSize: 128 * 1024 * 1024 * 1024, // 128GB
    fields: ['title', 'description', 'tags', 'category', 'privacy']
  },
  instagram: {
    id: 'instagram',
    name: 'Instagram',
    icon: '📸',
    color: 'from-purple-600 to-pink-600',
    supportedFormats: ['video/mp4', 'image/jpeg', 'image/png'],
    maxFileSize: 100 * 1024 * 1024, // 100MB
    fields: ['caption', 'mediaType']
  },
  tiktok: {
    id: 'tiktok',
    name: 'TikTok',
    icon: '🎵',
    color: 'from-black to-pink-500',
    supportedFormats: ['video/mp4'],
    maxFileSize: 287 * 1024 * 1024, // 287MB
    fields: ['caption', 'privacy']
  }
};

export default {
  getConnectedAccounts,
  uploadToYouTube,
  uploadToInstagram,
  uploadToPlatform,
  PLATFORMS
};

