import api from './api';

/**
 * Social Media Service
 * API calls for social media platform management (master apps and user credentials)
 */

// ==================== Master App Management ====================

/**
 * List all master apps for the customer
 * @param {Object} filters - { platform: 'instagram', active_only: true }
 * @returns {Promise} List of master apps
 */
export const listMasterApps = async (filters = {}) => {
  const params = new URLSearchParams();
  if (filters.platform) params.append('platform', filters.platform);
  if (filters.active_only) params.append('active_only', 'true');
  
  const response = await api.get(`/social-media/master-apps?${params.toString()}`);
  return response.data;
};

/**
 * Get a specific master app by ID
 * @param {string} appId - Master app ID
 * @returns {Promise} Master app details
 */
export const getMasterApp = async (appId) => {
  const response = await api.get(`/social-media/master-apps/${appId}`);
  return response.data;
};

/**
 * Create a new master app
 * @param {Object} appData - { platform, app_name, app_id, app_secret, redirect_uri, scopes, is_active }
 * @returns {Promise} Created master app
 */
export const createMasterApp = async (appData) => {
  const response = await api.post('/social-media/master-apps', appData);
  return response.data;
};

/**
 * Update an existing master app
 * @param {string} appId - Master app ID
 * @param {Object} appData - Updated fields
 * @returns {Promise} Updated master app
 */
export const updateMasterApp = async (appId, appData) => {
  const response = await api.put(`/social-media/master-apps/${appId}`, appData);
  return response.data;
};

/**
 * Delete a master app
 * @param {string} appId - Master app ID
 * @returns {Promise} Deletion result
 */
export const deleteMasterApp = async (appId) => {
  const response = await api.delete(`/social-media/master-apps/${appId}`);
  return response.data;
};

/**
 * Activate a master app (deactivates others for same platform)
 * @param {string} appId - Master app ID
 * @returns {Promise} Activation result
 */
export const activateMasterApp = async (appId) => {
  const response = await api.post(`/social-media/master-apps/${appId}/activate`);
  return response.data;
};

// ==================== Instagram Credentials ====================

/**
 * Get Instagram OAuth initiation URL
 * @returns {Promise} OAuth URL and master app info
 */
export const initiateInstagramOAuth = async () => {
  const response = await api.get('/social-media/instagram/oauth/initiate');
  return response.data;
};

/**
 * List user's Instagram credentials
 * @returns {Promise} List of Instagram credentials
 */
export const listInstagramCredentials = async () => {
  const response = await api.get('/social-media/instagram/credentials');
  return response.data;
};

/**
 * Delete an Instagram credential
 * @param {string} credentialId - Credential ID
 * @returns {Promise} Deletion result
 */
export const deleteInstagramCredential = async (credentialId) => {
  const response = await api.delete(`/social-media/instagram/credentials/${credentialId}`);
  return response.data;
};

// ==================== Platform Constants ====================

export const SOCIAL_PLATFORMS = {
  instagram: {
    id: 'instagram',
    name: 'Instagram',
    icon: '📸',
    color: 'from-purple-600 to-pink-600',
    defaultScopes: ['pages_show_list', 'instagram_basic', 'instagram_content_publish', 'pages_read_engagement'],
    description: 'Instagram Business & Creator accounts via Facebook Graph API'
  },
  tiktok: {
    id: 'tiktok',
    name: 'TikTok',
    icon: '🎵',
    color: 'from-black to-pink-500',
    defaultScopes: ['user.info.basic', 'video.list', 'video.upload'],
    description: 'TikTok for Developers API'
  },
  twitter: {
    id: 'twitter',
    name: 'Twitter',
    icon: '🐦',
    color: 'from-blue-400 to-blue-600',
    defaultScopes: ['tweet.read', 'tweet.write', 'users.read'],
    description: 'Twitter API v2'
  },
  linkedin: {
    id: 'linkedin',
    name: 'LinkedIn',
    icon: '💼',
    color: 'from-blue-600 to-blue-800',
    defaultScopes: ['r_liteprofile', 'w_member_social'],
    description: 'LinkedIn Marketing API'
  },
  facebook: {
    id: 'facebook',
    name: 'Facebook',
    icon: '👥',
    color: 'from-blue-500 to-blue-700',
    defaultScopes: ['pages_manage_posts', 'pages_read_engagement'],
    description: 'Facebook Graph API'
  },
  reddit: {
    id: 'reddit',
    name: 'Reddit',
    icon: '🤖',
    color: 'from-orange-500 to-red-600',
    defaultScopes: ['submit', 'read'],
    description: 'Reddit API'
  }
};

export default {
  listMasterApps,
  getMasterApp,
  createMasterApp,
  updateMasterApp,
  deleteMasterApp,
  activateMasterApp,
  initiateInstagramOAuth,
  listInstagramCredentials,
  deleteInstagramCredential,
  SOCIAL_PLATFORMS
};

