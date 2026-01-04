import React, { useState, useEffect } from 'react';
import { Button } from '../';
import { useAudioGeneration } from '../../../hooks/useAudioGeneration';
import { useToast } from '../../../hooks/useToast';
import api from '../../../services/api';

/**
 * Generic Audio Selector Component
 * Handles TTS generation with model/voice selection
 * 
 * @param {Object} props
 * @param {string} props.endpoint - API endpoint for audio generation
 * @param {string} props.text - Text to convert to speech
 * @param {string} props.initialAudioUrl - Initial audio URL
 * @param {Object} props.initialConfig - Initial audio config (model, language, voice)
 * @param {Function} props.onAudioGenerated - Callback when audio is generated
 * @param {Function} props.onConfigChange - Callback when config changes
 * @param {boolean} props.autoDetectLanguage - Auto-detect language from text
 * @param {boolean} props.showAdvancedOptions - Show advanced options (section speeds, etc.)
 * @param {string} props.className - Additional CSS classes
 */
const AudioSelector = ({
  endpoint,
  text = '',
  initialAudioUrl = null,
  initialConfig = {},
  onAudioGenerated,
  onConfigChange,
  autoDetectLanguage = true,
  showAdvancedOptions = false,
  className = ''
}) => {
  const {
    generating,
    audioUrl,
    generate,
    previewVoice,
    detectLanguage,
    setAudioUrl
  } = useAudioGeneration();

  const { showToast } = useToast();

  // API-driven TTS configuration (models, voices, etc.)
  const [ttsConfig, setTtsConfig] = useState(null);
  const [loadingConfig, setLoadingConfig] = useState(true);

  const [selectedModel, setSelectedModel] = useState(initialConfig.model || null);
  const [selectedLanguage, setSelectedLanguage] = useState(initialConfig.language || 'en');
  const [selectedVoice, setSelectedVoice] = useState(initialConfig.voice || null);
  const [previewingVoice, setPreviewingVoice] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);

  // Fetch audio configuration from API
  useEffect(() => {
    const fetchAudioConfig = async () => {
      try {
        const response = await api.get('/audio-studio/config');
        const config = response.data;
        setTtsConfig(config);

        // Set defaults from API if not already set
        if (!selectedModel && config.default_model) {
          setSelectedModel(config.default_model);

          // Set default voice for the default model
          const defaultModelConfig = config.models[config.default_model];
          if (defaultModelConfig && defaultModelConfig.default_voice && !selectedVoice) {
            setSelectedVoice(defaultModelConfig.default_voice);
          }
        }
      } catch (error) {
        console.error('Failed to fetch audio config:', error);
        showToast('Failed to load audio configuration', 'error');
      } finally {
        setLoadingConfig(false);
      }
    };

    fetchAudioConfig();
  }, []);

  // Auto-detect language on mount or when text changes
  useEffect(() => {
    if (autoDetectLanguage && text) {
      const detected = detectLanguage(text);
      setSelectedLanguage(detected);
    }
  }, [text, autoDetectLanguage, detectLanguage]);

  // Update voice when model changes
  useEffect(() => {
    if (ttsConfig && selectedModel) {
      const modelConfig = ttsConfig.models[selectedModel];
      if (modelConfig && modelConfig.default_voice) {
        setSelectedVoice(modelConfig.default_voice);
      }
    }
  }, [selectedModel, ttsConfig]);

  // Set initial audio URL
  useEffect(() => {
    if (initialAudioUrl) {
      setAudioUrl(initialAudioUrl);
    }
  }, [initialAudioUrl, setAudioUrl]);

  // Set initial config
  useEffect(() => {
    if (initialConfig.model || initialConfig.language || initialConfig.voice) {
      setAudioConfig(initialConfig);
      setSelectedModel(initialConfig.model || 'kokoro-82m');
      setSelectedLanguage(initialConfig.language || 'en');
      setSelectedVoice(initialConfig.voice || 'am_adam');
    }
  }, [initialConfig, setAudioConfig]);

  /**
   * Handle audio generation
   */
  const handleGenerate = async () => {
    if (!text) {
      showToast('No text provided for audio generation', 'error');
      return;
    }

    const result = await generate({
      endpoint,
      text,
      model: selectedModel,
      language: selectedLanguage,
      voice: selectedVoice,
      onSuccess: (url, data) => {
        showToast('Audio generated successfully', 'success');
        
        if (onAudioGenerated) {
          onAudioGenerated(url, {
            model: selectedModel,
            language: selectedLanguage,
            voice: selectedVoice
          }, data);
        }
      },
      onError: (error) => {
        showToast(error, 'error');
      }
    });

    return result;
  };

  /**
   * Handle voice preview
   */
  const handlePreviewVoice = async (voice) => {
    setPreviewingVoice(voice);

    await previewVoice({
      voice,
      model: selectedModel,
      language: selectedLanguage,
      sampleText: 'Hello, this is a voice preview. How does this sound?',
      onSuccess: (url) => {
        // Play the preview audio
        const audio = new Audio(url);
        audio.play();
        setPreviewingVoice(null);
      },
      onError: (error) => {
        showToast(error, 'error');
        setPreviewingVoice(null);
      }
    });
  };

  /**
   * Handle config change
   */
  const handleConfigChange = (field, value) => {
    const newConfig = {
      model: selectedModel,
      language: selectedLanguage,
      voice: selectedVoice,
      [field]: value
    };

    if (field === 'model') setSelectedModel(value);
    if (field === 'language') setSelectedLanguage(value);
    if (field === 'voice') setSelectedVoice(value);

    if (onConfigChange) {
      onConfigChange(newConfig);
    }
  };

  // Get available voices for selected model
  const availableVoices = ttsConfig && selectedModel
    ? ttsConfig.models[selectedModel]?.voices || []
    : [];

  // Show loading state
  if (loadingConfig) {
    return (
      <div className={`audio-selector ${className}`}>
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
          <span className="ml-3 text-gray-600">Loading audio configuration...</span>
        </div>
      </div>
    );
  }

  // Show error state if config failed to load
  if (!ttsConfig) {
    return (
      <div className={`audio-selector ${className}`}>
        <div className="text-center py-8 text-red-600">
          Failed to load audio configuration. Please refresh the page.
        </div>
      </div>
    );
  }

  return (
    <div className={`audio-selector ${className}`}>
      {/* Audio Configuration */}
      <div className="space-y-4">
        {/* Model Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            TTS Model
            {ttsConfig.gpu_enabled && (
              <span className="ml-2 text-xs text-green-600 font-semibold">🎮 GPU Enabled</span>
            )}
          </label>
          <select
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            value={selectedModel || ''}
            onChange={(e) => handleConfigChange('model', e.target.value)}
          >
            {Object.entries(ttsConfig.models).map(([key, model]) => (
              <option key={key} value={key}>
                {model.name} - {model.language}
                {model.supports_emotions && ' 🎭'}
                {model.supports_music && ' 🎵'}
              </option>
            ))}
          </select>
        </div>

        {/* Voice/Speaker Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Voice / Speaker
            {availableVoices.length > 0 && (
              <span className="ml-2 text-xs text-gray-500">
                ({availableVoices.length} available)
              </span>
            )}
          </label>
          {availableVoices.length > 0 ? (
            <div className="grid grid-cols-2 gap-2 max-h-48 overflow-y-auto">
              {availableVoices.map((voice) => (
                <button
                  key={voice}
                  onClick={() => handleConfigChange('voice', voice)}
                  className={`px-3 py-2 border rounded-lg text-xs ${
                    selectedVoice === voice
                      ? 'border-indigo-500 bg-indigo-50 text-indigo-700 font-semibold'
                      : 'border-gray-300 hover:border-indigo-300'
                  }`}
                >
                  {voice}
                </button>
              ))}
            </div>
          ) : (
            <div className="text-sm text-gray-500 italic py-2">
              No voices available for this model
            </div>
          )}
        </div>

        {/* Generate Button */}
        <Button
          variant="primary"
          onClick={handleGenerate}
          loading={generating}
          disabled={generating || !text}
          className="w-full"
        >
          {audioUrl ? '🔄 Regenerate Audio' : '🎵 Generate Audio'}
        </Button>

        {/* Audio Player */}
        {audioUrl && (
          <div className="border border-gray-300 rounded-lg p-4">
            <audio
              controls
              src={audioUrl}
              className="w-full"
              onPlay={() => setIsPlaying(true)}
              onPause={() => setIsPlaying(false)}
              onEnded={() => setIsPlaying(false)}
            />
          </div>
        )}
      </div>
    </div>
  );
};

export default AudioSelector;

