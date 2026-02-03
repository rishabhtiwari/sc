import React, { useState, useEffect, useRef, forwardRef, useImperativeHandle } from 'react';

/**
 * AuthenticatedAudio Component
 * Fetches audio with JWT authentication and provides an audio element using blob URLs
 * This is necessary because <audio> tags don't send Authorization headers
 * 
 * Usage:
 * <AuthenticatedAudio 
 *   src="/api/audio-studio/library/123/stream"
 *   onLoadedMetadata={(audio) => console.log('Duration:', audio.duration)}
 *   onError={(error) => console.error(error)}
 * />
 */
const AuthenticatedAudio = forwardRef(({ 
  src, 
  volume = 1.0,
  loop = false,
  autoPlay = false,
  onLoadedMetadata = null,
  onEnded = null,
  onPause = null,
  onPlay = null,
  onError = null,
  onTimeUpdate = null,
  className = '',
  controls = false,
  ...props 
}, ref) => {
  const [blobUrl, setBlobUrl] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const audioRef = useRef(null);

  // Expose audio element methods to parent via ref
  useImperativeHandle(ref, () => ({
    get audio() {
      return audioRef.current;
    },
    play: () => audioRef.current?.play(),
    pause: () => audioRef.current?.pause(),
    get currentTime() {
      return audioRef.current?.currentTime || 0;
    },
    set currentTime(time) {
      if (audioRef.current) {
        audioRef.current.currentTime = time;
      }
    },
    get duration() {
      return audioRef.current?.duration || 0;
    },
    get paused() {
      return audioRef.current?.paused ?? true;
    },
    get volume() {
      return audioRef.current?.volume || 0;
    },
    set volume(vol) {
      if (audioRef.current) {
        audioRef.current.volume = vol;
      }
    }
  }));

  useEffect(() => {
    // If src is not an API URL (e.g., blob:, data:, or external URL), use it directly
    const isApiUrl = src && (
      src.startsWith('/api/') ||
      src.includes('/api/audio-studio/') ||
      src.includes('/api/assets/download/')
    );

    if (!src || !isApiUrl) {
      setBlobUrl(src);
      setLoading(false);
      return;
    }

    const fetchAuthenticatedAudio = async () => {
      const token = localStorage.getItem('auth_token');
      if (!token) {
        console.error('No auth token found for authenticated audio');
        setError(true);
        setLoading(false);
        if (onError) onError(new Error('No auth token'));
        return;
      }

      try {
        setLoading(true);
        setError(false);

        console.log('🔐 Fetching authenticated audio:', src.substring(0, 80));

        const response = await fetch(src, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        console.log('📥 Audio fetch response:', response.status, response.statusText);

        if (!response.ok) {
          throw new Error(`Failed to fetch audio: ${response.status} ${response.statusText}`);
        }

        const blob = await response.blob();
        const contentType = response.headers.get('Content-Type') || 'audio/mpeg';
        const audioBlob = new Blob([blob], { type: contentType });
        const url = URL.createObjectURL(audioBlob);
        console.log('✅ Created audio blob URL:', url);
        setBlobUrl(url);
        setLoading(false);
      } catch (err) {
        console.error('❌ Error fetching authenticated audio:', err);
        setError(true);
        setLoading(false);
        if (onError) onError(err);
      }
    };

    fetchAuthenticatedAudio();

    // Cleanup blob URL when component unmounts or src changes
    return () => {
      if (blobUrl && blobUrl.startsWith('blob:')) {
        URL.revokeObjectURL(blobUrl);
      }
    };
  }, [src]);

  // Update audio properties when they change
  useEffect(() => {
    if (audioRef.current && !loading && !error) {
      audioRef.current.volume = volume;
      audioRef.current.loop = loop;
    }
  }, [volume, loop, loading, error]);

  if (loading) {
    return null; // Audio is loading, no visual representation needed
  }

  if (error) {
    return null; // Audio failed to load, no visual representation needed
  }

  return (
    <audio
      ref={audioRef}
      src={blobUrl}
      className={className}
      controls={controls}
      autoPlay={autoPlay}
      onLoadedMetadata={(e) => {
        console.log('🎵 Audio metadata loaded, duration:', e.target.duration);
        if (onLoadedMetadata) onLoadedMetadata(e.target);
      }}
      onEnded={onEnded}
      onPause={onPause}
      onPlay={onPlay}
      onTimeUpdate={onTimeUpdate}
      onError={(e) => {
        console.error('Audio load error:', e);
        setError(true);
        if (onError) onError(e);
      }}
      {...props}
    />
  );
});

AuthenticatedAudio.displayName = 'AuthenticatedAudio';

export default AuthenticatedAudio;

