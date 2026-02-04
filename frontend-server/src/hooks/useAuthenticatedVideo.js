import { useState, useEffect, useCallback } from 'react';

/**
 * Custom hook to fetch and manage authenticated video
 * Returns a blob URL that can be used in Video elements
 * 
 * @param {string} src - The video source URL
 * @returns {Object} { videoUrl, loading, error, refetch }
 */
export const useAuthenticatedVideo = (src) => {
  const [videoUrl, setVideoUrl] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchVideo = useCallback(async () => {
    if (!src) {
      setVideoUrl(null);
      setLoading(false);
      return;
    }

    // If src is not an API URL (e.g., blob:, data:, or external URL), use it directly
    const isApiUrl = (
      src.startsWith('/api/') ||
      src.includes('/api/video-library/') ||
      src.includes('/api/assets/download/') ||
      src.includes('/api/projects/export/')
    );

    if (!isApiUrl) {
      setVideoUrl(src);
      setLoading(false);
      return;
    }

    const token = localStorage.getItem('auth_token');
    if (!token) {
      console.error('No auth token found for authenticated video');
      setError(new Error('No auth token'));
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      console.log('🔐 Fetching authenticated video:', src.substring(0, 80));

      const response = await fetch(src, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch video: ${response.status} ${response.statusText}`);
      }

      const blob = await response.blob();
      const contentType = response.headers.get('Content-Type') || 'video/mp4';
      const videoBlob = new Blob([blob], { type: contentType });
      const url = URL.createObjectURL(videoBlob);
      
      console.log('✅ Created video blob URL');
      setVideoUrl(url);
      setLoading(false);
    } catch (err) {
      console.error('❌ Error fetching authenticated video:', err);
      setError(err);
      setLoading(false);
    }
  }, [src]);

  useEffect(() => {
    fetchVideo();

    // Cleanup blob URL when component unmounts or src changes
    return () => {
      if (videoUrl && videoUrl.startsWith('blob:')) {
        URL.revokeObjectURL(videoUrl);
      }
    };
  }, [src, fetchVideo]);

  return {
    videoUrl,
    loading,
    error,
    refetch: fetchVideo
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
    url.includes('/api/video-library/') ||
    url.includes('/api/assets/download/') ||
    url.includes('/api/projects/export/') ||
    url.includes('/api/image-library/')
  );
};

/**
 * Helper function to fetch authenticated video and return blob URL
 * @param {string} url - The video URL
 * @returns {Promise<string>} - Blob URL
 */
export const fetchAuthenticatedVideo = async (url) => {
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
    throw new Error(`Failed to fetch video: ${response.status} ${response.statusText}`);
  }

  const blob = await response.blob();
  const contentType = response.headers.get('Content-Type') || 'video/mp4';
  const videoBlob = new Blob([blob], { type: contentType });
  return URL.createObjectURL(videoBlob);
};

