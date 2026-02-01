import React, { useState, useEffect } from 'react';

/**
 * AuthenticatedVideo Component
 * Fetches videos with JWT authentication and displays them using blob URLs
 * This is necessary because <video> tags don't send Authorization headers
 */
const AuthenticatedVideo = ({ 
  src, 
  className = '', 
  fallback = null,
  onError = null,
  controls = false,
  preload = 'metadata',
  onMouseEnter = null,
  onMouseLeave = null,
  ...props 
}) => {
  const [blobUrl, setBlobUrl] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    console.log('🎬 [AuthenticatedVideo] useEffect triggered');
    console.log('  - src:', src);
    console.log('  - current blobUrl:', blobUrl);

    // If no src, don't try to load anything
    if (!src) {
      console.log('🎬 [AuthenticatedVideo] No src provided, skipping load');
      setLoading(false);
      setError(true);
      return;
    }

    // If src is not an API URL (e.g., blob:, data:, or external URL), use it directly
    // Check for both relative /api/ and absolute http://localhost:8080/api/ URLs
    const isApiUrl = src && (
      src.startsWith('/api/') ||
      src.includes('/api/ecommerce/') ||
      src.includes('/api/assets/download/')
    );
    console.log('  - isApiUrl:', isApiUrl);

    if (!isApiUrl) {
      console.log('🎬 [AuthenticatedVideo] Using src directly (not an API URL)');
      setBlobUrl(src);
      setLoading(false);
      return;
    }

    const abortController = new AbortController();

    const fetchAuthenticatedVideo = async () => {
      const token = localStorage.getItem('auth_token');
      if (!token) {
        console.error('🎬 [AuthenticatedVideo] ❌ No auth token found for authenticated video');
        setError(true);
        setLoading(false);
        if (onError) onError(new Error('No auth token'));
        return;
      }

      try {
        setLoading(true);
        setError(false);

        console.log('🎬 [AuthenticatedVideo] 🔐 Fetching authenticated video:', src);
        console.log('🎬 [AuthenticatedVideo] 🔑 Using token:', token.substring(0, 20) + '...');

        const response = await fetch(src, {
          headers: {
            'Authorization': `Bearer ${token}`
          },
          signal: abortController.signal
        });

        console.log('🎬 [AuthenticatedVideo] 📥 Video fetch response:', response.status, response.statusText);

        if (!response.ok) {
          // If 404, the video was deleted - don't show error, just show placeholder
          if (response.status === 404) {
            console.warn('🎬 [AuthenticatedVideo] ⚠️ Video not found (404) - may have been deleted');
            setError(true);
            setLoading(false);
            return;
          }
          throw new Error(`Failed to fetch video: ${response.status} ${response.statusText}`);
        }

        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        console.log('🎬 [AuthenticatedVideo] ✅ Created blob URL for video:', url);
        console.log('🎬 [AuthenticatedVideo] Original src:', src);
        setBlobUrl(url);
        setLoading(false);
      } catch (err) {
        // Ignore abort errors
        if (err.name === 'AbortError') {
          console.log('🎬 [AuthenticatedVideo] ⏹️ Fetch aborted');
          return;
        }
        console.error('🎬 [AuthenticatedVideo] ❌ Error fetching authenticated video:', err);
        setError(true);
        setLoading(false);
        if (onError) onError(err);
      }
    };

    fetchAuthenticatedVideo();

    // Cleanup blob URL and abort fetch when component unmounts or src changes
    return () => {
      console.log('🎬 [AuthenticatedVideo] 🧹 Cleanup function called');
      console.log('  - Aborting fetch if in progress');
      abortController.abort();
      console.log('  - Current blobUrl to cleanup:', blobUrl);
      console.log('  - Is blob URL?', blobUrl?.startsWith('blob:'));
      if (blobUrl && blobUrl.startsWith('blob:')) {
        console.log('🎬 [AuthenticatedVideo] 🗑️ Revoking blob URL:', blobUrl);
        URL.revokeObjectURL(blobUrl);
        console.log('🎬 [AuthenticatedVideo] ✅ Blob URL revoked');
      } else {
        console.log('🎬 [AuthenticatedVideo] ⏭️ No blob URL to revoke');
      }
    };
  }, [src]);

  if (loading) {
    return (
      <div className={`bg-gray-900 animate-pulse ${className}`} {...props}>
        <div className="w-full h-full flex items-center justify-center text-gray-400">
          <div className="text-center">
            <span className="text-4xl">⏳</span>
            <p className="text-xs mt-2">Loading video...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    if (fallback) {
      return fallback;
    }
    return (
      <div className={`bg-gray-900 ${className}`} {...props}>
        <div className="w-full h-full flex items-center justify-center text-gray-400">
          <div className="text-center">
            <span className="text-4xl">❌</span>
            <p className="text-xs mt-2">Failed to load video</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <video
      src={blobUrl}
      className={className}
      controls={controls}
      preload={preload}
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
      onError={(e) => {
        console.error('Video playback error:', e);
        setError(true);
        if (onError) onError(e);
      }}
      {...props}
    />
  );
};

export default AuthenticatedVideo;

