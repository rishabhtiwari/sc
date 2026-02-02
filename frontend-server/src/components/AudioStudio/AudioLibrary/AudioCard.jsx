import React, { useState, useRef, useEffect } from 'react';

/**
 * Audio Card Component
 * Individual audio file card with playback and actions
 */
const AudioCard = ({ audio, onDelete, onAddToCanvas }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [showMenu, setShowMenu] = useState(false);
  const [audioUrl, setAudioUrl] = useState(null);
  const [loading, setLoading] = useState(true);
  const audioRef = useRef(null);

  // Fetch authenticated audio URL
  useEffect(() => {
    const fetchAudio = async () => {
      try {
        setLoading(true);
        const token = localStorage.getItem('auth_token');

        console.log('Fetching audio from:', audio.url);

        const response = await fetch(audio.url, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        console.log('Audio response status:', response.status);
        console.log('Audio response headers:', {
          contentType: response.headers.get('Content-Type'),
          contentLength: response.headers.get('Content-Length'),
          contentDisposition: response.headers.get('Content-Disposition'),
          allHeaders: Array.from(response.headers.entries())
        });

        if (response.ok) {
          const blob = await response.blob();
          console.log('Audio blob created:', {
            size: blob.size,
            type: blob.type
          });

          // Check if blob is actually audio
          if (!blob.type.startsWith('audio/')) {
            console.error('⚠️ Blob is not audio! Type:', blob.type);
            // Try to read blob as text to see what it contains
            const text = await blob.text();
            console.error('Blob content (first 500 chars):', text.substring(0, 500));
            return;
          }

          // Ensure blob has correct MIME type
          const audioBlob = new Blob([blob], { type: 'audio/wav' });
          console.log('Created audio blob with type:', audioBlob.type);
          const blobUrl = URL.createObjectURL(audioBlob);
          setAudioUrl(blobUrl);
          console.log('✅ Audio blob URL created:', blobUrl);
        } else {
          const errorText = await response.text();
          console.error('Failed to fetch audio:', response.status, errorText);
        }
      } catch (error) {
        console.error('Error fetching audio:', error);
      } finally {
        setLoading(false);
      }
    };

    if (audio.url) {
      fetchAudio();
    }

    // Cleanup blob URL on unmount
    return () => {
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
      }
    };
  }, [audio.url]);

  const togglePlayPause = () => {
    const audioElement = audioRef.current;
    if (!audioElement) {
      console.error('❌ Audio element not found');
      return;
    }

    console.log('🎵 Toggle play/pause. Current state:', { isPlaying, audioUrl, src: audioElement.src });

    if (isPlaying) {
      audioElement.pause();
    } else {
      audioElement.play().catch(err => {
        console.error('❌ Error playing audio:', err);
        console.error('Audio element details:', {
          src: audioElement.src,
          readyState: audioElement.readyState,
          networkState: audioElement.networkState,
          error: audioElement.error
        });
      });
    }
    setIsPlaying(!isPlaying);
  };

  const handleDownload = () => {
    const link = document.createElement('a');
    link.href = audio.url;
    link.download = `${audio.name}.wav`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    setShowMenu(false);
  };

  const handleDelete = () => {
    onDelete(audio);
    setShowMenu(false);
  };

  const formatDuration = (seconds) => {
    if (!seconds) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getTypeIcon = () => {
    switch (audio.type) {
      case 'voiceover':
        return '🎙️';
      case 'music':
        return '🎵';
      case 'sound_effect':
        return '🔊';
      default:
        return '🎵';
    }
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
      <audio
        ref={audioRef}
        src={audioUrl}
        onEnded={() => setIsPlaying(false)}
        onPause={() => setIsPlaying(false)}
        onPlay={() => setIsPlaying(true)}
      />

      <div className="flex items-start gap-3">
        {/* Play Button */}
        <button
          onClick={togglePlayPause}
          disabled={loading || !audioUrl}
          className="w-12 h-12 bg-blue-600 hover:bg-blue-700 text-white rounded-full flex items-center justify-center flex-shrink-0 transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
          title={loading ? 'Loading...' : isPlaying ? 'Pause' : 'Play'}
        >
          {loading ? (
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
          ) : isPlaying ? (
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z" />
            </svg>
          ) : (
            <svg className="w-5 h-5 ml-0.5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M8 5v14l11-7z" />
            </svg>
          )}
        </button>

        {/* Audio Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-1">
                <span className="text-sm">{getTypeIcon()}</span>
                <h4 className="text-sm font-medium text-gray-900 truncate">
                  {audio.name}
                </h4>
              </div>
              <p className="text-xs text-gray-500 mt-0.5">
                {formatDuration(audio.duration)}
                {audio.generation_config?.voice && (
                  <span className="ml-2">• {audio.generation_config.voice}</span>
                )}
              </p>
              <p className="text-xs text-gray-400 mt-0.5">
                {new Date(audio.created_at).toLocaleDateString()}
              </p>
            </div>

            {/* Menu Button */}
            <div className="relative">
              <button
                onClick={() => setShowMenu(!showMenu)}
                className="p-1 hover:bg-gray-100 rounded transition-colors"
              >
                <span className="text-gray-600">⋮</span>
              </button>

              {/* Dropdown Menu */}
              {showMenu && (
                <>
                  <div
                    className="fixed inset-0 z-10"
                    onClick={() => setShowMenu(false)}
                  />
                  <div className="absolute right-0 top-full mt-1 w-48 bg-white border border-gray-200 rounded-lg shadow-lg z-20">
                    {onAddToCanvas && (
                      <button
                        onClick={() => {
                          console.log('🎵 Open in Design Editor clicked:', {
                            title: audio.name,
                            audioUrl: audioUrl,
                            duration: audio.duration,
                            audio_id: audio.audio_id,
                            loading: loading
                          });

                          if (!audioUrl) {
                            console.error('❌ Audio URL not ready yet!');
                            return;
                          }

                          onAddToCanvas({
                            title: audio.name,
                            url: audioUrl,
                            audio_url: audioUrl,
                            duration: audio.duration,
                            audio_id: audio.audio_id,  // Include audio_id from library
                            libraryId: audio.audio_id,  // Also set as libraryId
                            assetId: audio.audio_id     // And as assetId for consistency
                          });
                          setShowMenu(false);
                        }}
                        disabled={!audioUrl || loading}
                        className="w-full px-4 py-2 text-left text-sm text-blue-600 hover:bg-blue-50 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <span>🎨</span>
                        <span>Open in Design Editor</span>
                      </button>
                    )}
                    <button
                      onClick={handleDownload}
                      className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100 flex items-center gap-2"
                    >
                      <span>⬇️</span>
                      <span>Download</span>
                    </button>
                    <button
                      onClick={handleDelete}
                      className="w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50 flex items-center gap-2"
                    >
                      <span>🗑️</span>
                      <span>Delete</span>
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AudioCard;

