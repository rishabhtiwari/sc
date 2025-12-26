import React, { useState, useEffect } from 'react';

/**
 * AuthenticatedImage Component
 * Fetches images with JWT authentication and displays them using blob URLs
 * This is necessary because <img> tags don't send Authorization headers
 */
const AuthenticatedImage = ({ 
  src, 
  alt, 
  className = '', 
  fallback = null,
  onError = null,
  ...props 
}) => {
  const [blobUrl, setBlobUrl] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    // If src is not an API URL (e.g., blob:, data:, or external URL), use it directly
    // Check for both relative /api/ and absolute http://localhost:8080/api/ URLs
    const isApiUrl = src && (src.includes('/api/ecommerce/') || src.startsWith('/api/'));

    if (!src || !isApiUrl) {
      setBlobUrl(src);
      setLoading(false);
      return;
    }

    const fetchAuthenticatedImage = async () => {
      const token = localStorage.getItem('auth_token');
      if (!token) {
        console.error('No auth token found for authenticated image');
        setError(true);
        setLoading(false);
        if (onError) onError(new Error('No auth token'));
        return;
      }

      try {
        setLoading(true);
        setError(false);

        console.log('🔐 Fetching authenticated image:', src);
        console.log('🔑 Using token:', token.substring(0, 20) + '...');

        const response = await fetch(src, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        console.log('📥 Image fetch response:', response.status, response.statusText);

        if (!response.ok) {
          throw new Error(`Failed to fetch image: ${response.status} ${response.statusText}`);
        }

        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        console.log('✅ Created blob URL:', url);
        setBlobUrl(url);
        setLoading(false);
      } catch (err) {
        console.error('❌ Error fetching authenticated image:', err);
        setError(true);
        setLoading(false);
        if (onError) onError(err);
      }
    };

    fetchAuthenticatedImage();

    // Cleanup blob URL when component unmounts or src changes
    return () => {
      if (blobUrl && blobUrl.startsWith('blob:')) {
        URL.revokeObjectURL(blobUrl);
      }
    };
  }, [src]);

  if (loading) {
    return (
      <div className={`bg-gray-100 animate-pulse ${className}`} {...props}>
        <div className="w-full h-full flex items-center justify-center text-gray-400">
          <span className="text-2xl">⏳</span>
        </div>
      </div>
    );
  }

  if (error) {
    if (fallback) {
      return fallback;
    }
    return (
      <div className={`bg-gray-100 ${className}`} {...props}>
        <div className="w-full h-full flex items-center justify-center text-gray-400">
          <span className="text-2xl">❌</span>
        </div>
      </div>
    );
  }

  return (
    <img
      src={blobUrl}
      alt={alt}
      className={className}
      onError={(e) => {
        console.error('Image load error:', e);
        setError(true);
        if (onError) onError(e);
      }}
      {...props}
    />
  );
};

export default AuthenticatedImage;

