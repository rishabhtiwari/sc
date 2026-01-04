import React, { useState, useRef } from 'react';
import api from '../../../services/api';

/**
 * Voice Preview Card Component
 * Enhanced card for voice preview page with larger layout
 * Supports preview caching to avoid regenerating the same audio
 */
const VoicePreviewCard = ({ voice, modelId, language, sampleText }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [cachedAudioUrl, setCachedAudioUrl] = useState(null);
  const audioRef = useRef(null);

  // Use provided sample text or fallback to default
  const previewText = sampleText || (language === 'hi'
    ? `नमस्ते! मैं ${voice.name} हूं। यह आवाज़ का पूर्वावलोकन है।`
    : `Hello! I'm ${voice.name}. This is a voice preview.`);

  const handlePreview = async () => {
    // Stop if already playing
    if (isPlaying && audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      setIsPlaying(false);
      return;
    }

    try {
      setIsLoading(true);

      // Call preview endpoint - backend handles all caching logic
      console.log('Requesting preview...');
      const response = await api.post('/audio/preview', {
        text: previewText,
        model: modelId,
        voice: voice.id,
        language: language
      });

      console.log('Preview response:', response.data);

      if (response.data.status === 'success' && response.data.audioUrl) {
        const audioUrl = response.data.audioUrl;
        const isCached = response.data.cached;

        // Update cached state if this was from cache
        if (isCached && !cachedAudioUrl) {
          setCachedAudioUrl(audioUrl);
          console.log('✅ Using cached preview');
        } else if (!isCached) {
          setCachedAudioUrl(audioUrl);
          console.log('✅ Preview generated and cached');
        }

        // Play the audio
        const token = localStorage.getItem('auth_token');
        if (!token) {
          console.error('No auth token found');
          setIsLoading(false);
          return;
        }

        // Construct full URL for the audio
        const fullAudioUrl = audioUrl.startsWith('http')
          ? audioUrl
          : `http://localhost:3002${audioUrl}`;

        console.log('Fetching audio from:', fullAudioUrl);

        // Fetch audio with authentication
        const audioResponse = await fetch(fullAudioUrl, {
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
        audioRef.current = audio;

        audio.onended = () => {
          setIsPlaying(false);
          URL.revokeObjectURL(blobUrl);
        };

        audio.onerror = (e) => {
          console.error('Audio playback error:', e);
          setIsPlaying(false);
          setIsLoading(false);
          URL.revokeObjectURL(blobUrl);
        };

        audio.oncanplay = () => {
          setIsLoading(false);
        };

        await audio.play();
        setIsPlaying(true);
      } else {
        console.error('Invalid response format:', response.data);
        setIsLoading(false);
      }
    } catch (error) {
      console.error('Preview error:', error);
      setIsLoading(false);
      setIsPlaying(false);
    }
  };

  // Get icon based on gender
  const getVoiceIcon = () => {
    if (voice.gender === 'male') return '👨';
    if (voice.gender === 'female') return '👩';
    return '🎤';
  };

  // Get accent/region badge
  const getAccentBadge = () => {
    if (voice.id.startsWith('am_')) return '🇺🇸 American';
    if (voice.id.startsWith('bm_')) return '🇬🇧 British';
    if (voice.id.startsWith('af_')) return '🇺🇸 American';
    if (voice.id.startsWith('bf_')) return '🇬🇧 British';
    return '🌍 Default';
  };

  return (
    <div className="bg-white rounded-xl shadow-md hover:shadow-xl transition-all duration-300 overflow-hidden border border-gray-200">
      {/* Header with Icon */}
      <div className="bg-gradient-to-br from-blue-500 to-purple-600 p-6 text-center">
        <div className="text-6xl mb-2">{getVoiceIcon()}</div>
        <h3 className="text-xl font-bold text-white">{voice.name}</h3>
        <div className="mt-2 inline-block px-3 py-1 bg-white/20 backdrop-blur-sm rounded-full text-white text-xs font-medium">
          {getAccentBadge()}
        </div>
      </div>

      {/* Content */}
      <div className="p-6">
        {/* Description */}
        <p className="text-gray-600 text-sm mb-4 min-h-[40px]">
          {voice.description}
        </p>

        {/* Characteristics */}
        <div className="space-y-2 mb-4">
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-500">Gender:</span>
            <span className="font-medium text-gray-900 capitalize">{voice.gender || 'Unknown'}</span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-500">Language:</span>
            <span className="font-medium text-gray-900">{language === 'en' ? 'English' : language === 'hi' ? 'Hindi' : language.toUpperCase()}</span>
          </div>
          {cachedAudioUrl && (
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-500">Status:</span>
              <span className="font-medium text-green-600 flex items-center gap-1">
                <span>✓</span>
                <span>Cached</span>
              </span>
            </div>
          )}
        </div>

        {/* Preview Button */}
        <button
          onClick={handlePreview}
          disabled={isLoading}
          className={`
            w-full py-3 rounded-lg font-semibold transition-all duration-300
            ${isPlaying
              ? 'bg-red-500 hover:bg-red-600 text-white'
              : isLoading
              ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-700 text-white'
            }
          `}
        >
          {isLoading ? (
            <span className="flex items-center justify-center gap-2">
              <span className="animate-spin">⏳</span>
              <span>Loading...</span>
            </span>
          ) : isPlaying ? (
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

        {/* Sample Text Preview */}
        <div className="mt-4 p-3 bg-gray-50 rounded-lg">
          <p className="text-xs text-gray-500 mb-1">Sample Text:</p>
          <p className="text-xs text-gray-700 italic line-clamp-2">
            "{previewText.substring(0, 100)}..."
          </p>
        </div>
      </div>
    </div>
  );
};

export default VoicePreviewCard;

