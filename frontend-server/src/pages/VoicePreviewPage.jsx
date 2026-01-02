import React, { useState, useEffect } from 'react';
import { Card } from '../components/common';
import VoicePreviewCard from '../components/AudioStudio/TextToSpeech/VoicePreviewCard';
import api from '../services/api';

/**
 * Voice Preview Page
 * Dedicated page for browsing and previewing all available voices
 * Fetches configuration from API instead of using hardcoded values
 */
const VoicePreviewPage = () => {
  const [ttsConfig, setTtsConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedModel, setSelectedModel] = useState(null);
  const [filter, setFilter] = useState('all'); // all, male, female

  // Fetch TTS configuration from API
  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const response = await api.get('/audio-studio/config');
        const config = response.data;
        setTtsConfig(config);
        // Set default model
        if (config.default_model) {
          setSelectedModel(config.default_model);
        }
      } catch (error) {
        console.error('Failed to fetch TTS config:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchConfig();
  }, []);

  // Get all voices for selected model
  const allVoices = selectedModel && ttsConfig
    ? (ttsConfig.models[selectedModel]?.voices || []).map(voiceId => ({
        id: voiceId,
        name: voiceId,
        description: `${ttsConfig.models[selectedModel]?.name} voice`,
        category: 'default' // Bark doesn't have male/female categories
      }))
    : [];

  // Filter voices (for now, just return all since Bark doesn't have gender categories)
  const filteredVoices = allVoices;

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading voice configuration...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (!ttsConfig) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-6xl mb-4">⚠️</div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Failed to Load Configuration</h2>
          <p className="text-gray-600 mb-4">Could not fetch TTS configuration from server</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                🎭 Voice Gallery
                {ttsConfig.gpu_enabled && (
                  <span className="ml-3 text-sm text-green-600 font-semibold">🎮 GPU Enabled</span>
                )}
              </h1>
              <p className="text-gray-600 mt-2">
                Browse and preview all available voices for text-to-speech
              </p>
            </div>
            <button
              onClick={() => window.close()}
              className="px-4 py-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
            >
              ✕ Close
            </button>
          </div>
        </div>
      </div>

      {/* Model Selector */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center gap-4">
            {/* Model Selection */}
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium text-gray-700">Model:</label>
              <div className="flex gap-2">
                {Object.entries(ttsConfig.models).map(([modelKey, model]) => (
                  <button
                    key={modelKey}
                    onClick={() => setSelectedModel(modelKey)}
                    className={`
                      px-4 py-2 rounded-lg font-medium transition-colors text-sm
                      ${selectedModel === modelKey
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      }
                    `}
                  >
                    {model.name} - {model.language}
                    {model.supports_emotions && ' 🎭'}
                    {model.supports_music && ' 🎵'}
                  </button>
                ))}
              </div>
            </div>

            {/* Voice Count */}
            <div className="ml-auto">
              <span className="text-sm text-gray-600">
                {allVoices.length} {allVoices.length === 1 ? 'voice' : 'voices'} available
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Voice Grid */}
      <div className="px-6 py-8">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {filteredVoices.map((voice) => (
              <VoicePreviewCard
                key={voice.id}
                voice={voice}
                modelId={selectedModel}
                language={ttsConfig.models[selectedModel]?.language || 'en'}
              />
            ))}
          </div>

          {/* Empty State */}
          {filteredVoices.length === 0 && (
            <div className="text-center py-16">
              <div className="text-6xl mb-4">🔍</div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                No voices found
              </h3>
              <p className="text-gray-600">
                Try selecting a different model
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default VoicePreviewPage;

