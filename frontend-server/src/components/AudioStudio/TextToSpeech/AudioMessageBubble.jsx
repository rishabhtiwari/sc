import React, { useState, useRef, useEffect } from 'react';
import { Button } from '../../common';

/**
 * Audio Message Bubble Component
 * Displays a chat-style message with generated audio
 */
const AudioMessageBubble = ({ message, onSaveToLibrary, saving }) => {
  const audioRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(message.duration || 0);
  const [blobUrl, setBlobUrl] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  // Fetch authenticated audio and create blob URL
  useEffect(() => {
    const fetchAuthenticatedAudio = async () => {
      try {
        setLoading(true);
        setError(false);

        // Get auth token
        const token = localStorage.getItem('auth_token');
        if (!token) {
          console.error('No auth token found');
          setError(true);
          setLoading(false);
          return;
        }

        // Convert relative path to proxy URL
        let audioUrl = message.audioUrl;
        if (audioUrl && !audioUrl.startsWith('http') && !audioUrl.startsWith('blob:')) {
          // Remove leading slash if present
          const path = audioUrl.startsWith('/') ? audioUrl.substring(1) : audioUrl;
          audioUrl = `http://localhost:3002/api/audio/proxy/${path}`;
        }

        console.log('Fetching authenticated audio from:', audioUrl);

        // Fetch audio with authentication
        const response = await fetch(audioUrl, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (!response.ok) {
          throw new Error(`Failed to fetch audio: ${response.status}`);
        }

        // Create blob URL
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        console.log('Created blob URL for audio:', url);
        setBlobUrl(url);
        setLoading(false);
      } catch (err) {
        console.error('Error fetching authenticated audio:', err);
        setError(true);
        setLoading(false);
      }
    };

    if (message.audioUrl) {
      fetchAuthenticatedAudio();
    }

    // Cleanup blob URL on unmount
    return () => {
      if (blobUrl) {
        URL.revokeObjectURL(blobUrl);
      }
    };
  }, [message.audioUrl]);

  // Setup audio event listeners
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio || !blobUrl) return;

    const handleTimeUpdate = () => setCurrentTime(audio.currentTime);
    const handleLoadedMetadata = () => setDuration(audio.duration);
    const handleEnded = () => setIsPlaying(false);

    audio.addEventListener('timeupdate', handleTimeUpdate);
    audio.addEventListener('loadedmetadata', handleLoadedMetadata);
    audio.addEventListener('ended', handleEnded);

    return () => {
      audio.removeEventListener('timeupdate', handleTimeUpdate);
      audio.removeEventListener('loadedmetadata', handleLoadedMetadata);
      audio.removeEventListener('ended', handleEnded);
    };
  }, [blobUrl]);

  const togglePlayPause = () => {
    const audio = audioRef.current;
    if (!audio) return;

    if (isPlaying) {
      audio.pause();
    } else {
      audio.play();
    }
    setIsPlaying(!isPlaying);
  };

  const handleSeek = (e) => {
    const audio = audioRef.current;
    if (!audio) return;

    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const percentage = x / rect.width;
    audio.currentTime = percentage * duration;
  };

  const formatTime = (seconds) => {
    if (!seconds || isNaN(seconds)) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const progress = duration > 0 ? (currentTime / duration) * 100 : 0;

  return (
    <div className="flex justify-end">
      <div className="max-w-2xl w-full">
        {/* Message Bubble */}
        <div className="bg-blue-600 text-white rounded-lg p-4 shadow-md">
          {/* Text Content */}
          <div className="mb-3">
            <p className="text-sm leading-relaxed">{message.text}</p>
          </div>

          {/* Audio Player */}
          <div className="bg-white/10 rounded-lg p-3 backdrop-blur-sm">
            {blobUrl && <audio ref={audioRef} src={blobUrl} preload="metadata" />}

            {loading ? (
              <div className="flex items-center justify-center py-4">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
                <span className="ml-3 text-sm">Loading audio...</span>
              </div>
            ) : error ? (
              <div className="flex items-center justify-center py-4 text-red-200">
                <span className="text-sm">❌ Failed to load audio</span>
              </div>
            ) : (
              <>
                {/* Play/Pause Button and Progress */}
                <div className="flex items-center gap-3">
                  <button
                    onClick={togglePlayPause}
                    className="w-10 h-10 flex items-center justify-center bg-white text-blue-600 rounded-full hover:bg-blue-50 transition-colors flex-shrink-0"
                  >
                    {isPlaying ? (
                      <span className="text-lg">⏸️</span>
                    ) : (
                      <span className="text-lg">▶️</span>
                    )}
                  </button>

                  {/* Progress Bar */}
                  <div className="flex-1">
                    <div
                      onClick={handleSeek}
                      className="h-2 bg-white/20 rounded-full cursor-pointer relative"
                    >
                      <div
                        className="h-full bg-white rounded-full transition-all"
                        style={{ width: `${progress}%` }}
                      />
                    </div>
                    <div className="flex justify-between text-xs mt-1 text-white/80">
                      <span>{formatTime(currentTime)}</span>
                      <span>{formatTime(duration)}</span>
                    </div>
                  </div>
                </div>
              </>
            )}
          </div>

          {/* Metadata */}
          <div className="mt-3 flex items-center justify-between text-xs text-white/80">
            <div className="flex items-center gap-3">
              <span>🎤 {message.voiceName}</span>
              <span>⚡ {message.speed}x</span>
            </div>
            <span>{new Date(message.timestamp).toLocaleTimeString()}</span>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-end gap-2 mt-2">
          {blobUrl && (
            <a
              href={blobUrl}
              download={`voiceover-${Date.now()}.wav`}
              className="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
            >
              📥 Download
            </a>
          )}
          <button
            onClick={onSaveToLibrary}
            disabled={saving || loading}
            className="px-3 py-1.5 text-sm text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-lg transition-colors disabled:opacity-50"
          >
            {saving ? '💾 Saving...' : '💾 Save to Library'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default AudioMessageBubble;

