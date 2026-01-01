import React, { useState } from 'react';
import api from '../../../services/api';

/**
 * Voice Card Component
 * Individual voice card with preview functionality
 */
const VoiceCard = ({ voice, isSelected, onSelect }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [audioElement, setAudioElement] = useState(null);

  // Handle voice preview
  const handlePreview = async (e) => {
    e.stopPropagation(); // Prevent card selection

    // Stop if already playing
    if (isPlaying && audioElement) {
      audioElement.pause();
      audioElement.currentTime = 0;
      setIsPlaying(false);
      return;
    }

    try {
      setIsPlaying(true);

      // Generate preview audio
      const response = await api.post('/audio/preview', {
        text: `Hello! I'm ${voice.name}. ${voice.description}`,
        model: 'kokoro-82m',
        voice: voice.id,
        language: 'en'
      });

      if (response.data.status === 'success' && response.data.audioUrl) {
        // Fetch the audio file with authentication
        const token = localStorage.getItem('auth_token');
        if (!token) {
          console.error('No auth token found');
          setIsPlaying(false);
          return;
        }

        // Construct full URL for the audio
        const audioUrl = response.data.audioUrl.startsWith('http')
          ? response.data.audioUrl
          : `http://localhost:3002${response.data.audioUrl}`;

        // Fetch audio with authentication
        const audioResponse = await fetch(audioUrl, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (!audioResponse.ok) {
          throw new Error(`Failed to fetch audio: ${audioResponse.status}`);
        }

        // Create blob URL from the audio data
        const blob = await audioResponse.blob();
        const blobUrl = URL.createObjectURL(blob);

        const audio = new Audio(blobUrl);
        setAudioElement(audio);

        audio.onended = () => {
          setIsPlaying(false);
          // Clean up blob URL
          URL.revokeObjectURL(blobUrl);
        };

        audio.onerror = (e) => {
          console.error('Audio playback error:', e);
          setIsPlaying(false);
          // Clean up blob URL
          URL.revokeObjectURL(blobUrl);
        };

        await audio.play();
      } else {
        setIsPlaying(false);
      }
    } catch (error) {
      console.error('Preview error:', error);
      setIsPlaying(false);
    }
  };

  // Get icon based on category
  const getVoiceIcon = () => {
    if (voice.category === 'male') return '👨';
    if (voice.category === 'female') return '👩';
    return '🎤';
  };

  return (
    <div
      onClick={onSelect}
      className={`
        relative p-4 rounded-lg border-2 cursor-pointer transition-all
        ${isSelected
          ? 'border-blue-600 bg-blue-50 shadow-md'
          : 'border-gray-200 bg-white hover:border-blue-300 hover:shadow-sm'
        }
      `}
    >
      {/* Selected Indicator */}
      {isSelected && (
        <div className="absolute top-2 right-2">
          <div className="w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center">
            <span className="text-white text-xs">✓</span>
          </div>
        </div>
      )}

      {/* Voice Info */}
      <div className="flex items-start gap-3">
        <div className="text-3xl">{getVoiceIcon()}</div>
        <div className="flex-1">
          <h4 className="font-semibold text-gray-900">{voice.name}</h4>
          <p className="text-xs text-gray-600 mt-1">{voice.description}</p>
        </div>
      </div>

      {/* Preview Button */}
      <button
        onClick={handlePreview}
        className={`
          mt-3 w-full px-3 py-2 rounded-md text-sm font-medium transition-colors
          ${isPlaying
            ? 'bg-red-100 text-red-700 hover:bg-red-200'
            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }
        `}
      >
        {isPlaying ? (
          <span className="flex items-center justify-center gap-2">
            <span>⏸️</span>
            <span>Stop Preview</span>
          </span>
        ) : (
          <span className="flex items-center justify-center gap-2">
            <span>▶️</span>
            <span>Preview Voice</span>
          </span>
        )}
      </button>
    </div>
  );
};

export default VoiceCard;

