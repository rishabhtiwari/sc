/**
 * Audio utility functions for handling authenticated audio streams
 */

/**
 * Check if a URL is an audio library stream URL that requires authentication
 * @param {string} url - The URL to check
 * @returns {boolean} - True if it's a library stream URL
 */
export const isLibraryStreamUrl = (url) => {
  if (!url) return false;
  return url.includes('/api/audio-studio/library/') && url.includes('/stream');
};

/**
 * Fetch authenticated audio and convert to blob URL
 * @param {string} url - The audio library stream URL
 * @returns {Promise<string>} - Blob URL for the audio
 */
export const fetchAuthenticatedAudio = async (url) => {
  try {
    const token = localStorage.getItem('auth_token');
    if (!token) {
      throw new Error('No authentication token found');
    }

    console.log('🔐 Fetching authenticated audio:', url);

    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch audio: ${response.status} ${response.statusText}`);
    }

    const blob = await response.blob();
    
    // Determine MIME type from response or default to audio/mpeg
    const contentType = response.headers.get('Content-Type') || 'audio/mpeg';
    const audioBlob = new Blob([blob], { type: contentType });
    
    const blobUrl = URL.createObjectURL(audioBlob);
    console.log('✅ Created authenticated blob URL:', blobUrl);
    
    return blobUrl;
  } catch (error) {
    console.error('❌ Error fetching authenticated audio:', error);
    throw error;
  }
};

/**
 * Process audio URL - convert library URLs to authenticated blob URLs
 * @param {string} url - The audio URL (could be blob, library stream, or other)
 * @returns {Promise<string>} - Processed URL (blob URL if library stream, original otherwise)
 */
export const processAudioUrl = async (url) => {
  if (isLibraryStreamUrl(url)) {
    return await fetchAuthenticatedAudio(url);
  }
  return url;
};

/**
 * Cleanup blob URL
 * @param {string} url - The blob URL to revoke
 */
export const cleanupBlobUrl = (url) => {
  if (url && url.startsWith('blob:')) {
    URL.revokeObjectURL(url);
  }
};

