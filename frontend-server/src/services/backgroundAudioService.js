/**
 * Background Audio Service - API calls for managing background audio library
 */

import api from './api';

/**
 * Get all background audio files
 * @returns {Promise} API response with audio files list
 */
export const getBackgroundAudioList = () => {
  return api.get('/videos/background-audio');
};

/**
 * Upload a new background audio file
 * @param {File} file - Audio file to upload
 * @param {Function} onProgress - Progress callback (optional)
 * @returns {Promise} API response
 */
export const uploadBackgroundAudio = (file, onProgress = null) => {
  const formData = new FormData();
  formData.append('file', file);

  const config = {};
  if (onProgress) {
    config.onUploadProgress = (progressEvent) => {
      const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
      onProgress(percentCompleted);
    };
  }

  return api.post('/videos/background-audio', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    ...config,
  });
};

/**
 * Delete a background audio file
 * @param {string} audioId - Audio file ID (filename)
 * @returns {Promise} API response
 */
export const deleteBackgroundAudio = (audioId) => {
  return api.delete(`/videos/background-audio/${audioId}`);
};

/**
 * Get download URL for a background audio file
 * @param {string} audioId - Audio file ID (filename)
 * @returns {string} Download URL
 */
export const getBackgroundAudioDownloadUrl = (audioId) => {
  // Get the base URL from the api instance
  const baseURL = api.defaults.baseURL || '';
  return `${baseURL}/videos/background-audio/${audioId}/download`;
};

export default {
  getBackgroundAudioList,
  uploadBackgroundAudio,
  deleteBackgroundAudio,
  getBackgroundAudioDownloadUrl,
};

