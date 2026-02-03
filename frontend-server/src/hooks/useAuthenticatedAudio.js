import { useState, useEffect, useCallback } from 'react';

/**
 * Custom hook to fetch and manage authenticated audio
 * Returns a blob URL that can be used in Audio elements
 * 
 * @param {string} src - The audio source URL
 * @returns {Object} { blobUrl, loading, error, refetch }
 */
export const useAuthenticatedAudio = (src) => {
  const [blobUrl, setBlobUrl] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchAudio = useCallback(async () => {
    if (!src) {
      setBlobUrl(null);
      setLoading(false);
      return;
    }

    // If src is not an API URL (e.g., blob:, data:, or external URL), use it directly
    const isApiUrl = (
      src.startsWith('/api/') ||
      src.includes('/api/audio-studio/') ||
      src.includes('/api/assets/download/')
    );

    if (!isApiUrl) {
      setBlobUrl(src);
      setLoading(false);
      return;
    }

    const token = localStorage.getItem('auth_token');
    if (!token) {
      console.error('No auth token found for authenticated audio');
      setError(new Error('No auth token'));
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      console.log('🔐 Fetching authenticated audio:', src.substring(0, 80));

      const response = await fetch(src, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch audio: ${response.status} ${response.statusText}`);
      }

      const blob = await response.blob();
      const contentType = response.headers.get('Content-Type') || 'audio/mpeg';
      const audioBlob = new Blob([blob], { type: contentType });
      const url = URL.createObjectURL(audioBlob);
      
      console.log('✅ Created audio blob URL');
      setBlobUrl(url);
      setLoading(false);
    } catch (err) {
      console.error('❌ Error fetching authenticated audio:', err);
      setError(err);
      setLoading(false);
    }
  }, [src]);

  useEffect(() => {
    fetchAudio();

    // Cleanup blob URL when component unmounts or src changes
    return () => {
      if (blobUrl && blobUrl.startsWith('blob:')) {
        URL.revokeObjectURL(blobUrl);
      }
    };
  }, [src, fetchAudio]);

  return {
    blobUrl,
    loading,
    error,
    refetch: fetchAudio
  };
};

/**
 * Helper function to check if a URL needs authentication
 * @param {string} url - The URL to check
 * @returns {boolean} - True if URL needs authentication
 */
export const needsAuthentication = (url) => {
  if (!url) return false;
  
  return (
    url.startsWith('/api/') ||
    url.includes('/api/audio-studio/') ||
    url.includes('/api/assets/download/') ||
    url.includes('/api/video-library/') ||
    url.includes('/api/image-library/')
  );
};

/**
 * Helper function to fetch authenticated audio and return blob URL
 * @param {string} url - The audio URL
 * @returns {Promise<string>} - Blob URL
 */
export const fetchAuthenticatedAudio = async (url) => {
  if (!needsAuthentication(url)) {
    return url;
  }

  const token = localStorage.getItem('auth_token');
  if (!token) {
    throw new Error('No auth token found');
  }

  const response = await fetch(url, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch audio: ${response.status} ${response.statusText}`);
  }

  const blob = await response.blob();
  const contentType = response.headers.get('Content-Type') || 'audio/mpeg';
  const audioBlob = new Blob([blob], { type: contentType });
  return URL.createObjectURL(audioBlob);
};

