import React, { useState, useRef } from 'react';
import { useAuthenticatedAudio } from '../../../hooks/useAuthenticatedAudio';

/**
 * Audio Card Component
 * Individual audio file card with playback and actions
 */
const AudioCard = ({ audio, onDelete, onAddToCanvas }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [showMenu, setShowMenu] = useState(false);
  const audioRef = useRef(null);

  // Use the centralized authenticated audio hook
  const { blobUrl: audioUrl, loading, error } = useAuthenticatedAudio(audio.url);

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
          disabled={loading || !audioUrl || error}
          className="w-12 h-12 bg-blue-600 hover:bg-blue-700 text-white rounded-full flex items-center justify-center flex-shrink-0 transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
          title={loading ? 'Loading...' : error ? 'Failed to load audio' : isPlaying ? 'Pause' : 'Play'}
        >
          {loading ? (
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
          ) : error ? (
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z" />
            </svg>
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

