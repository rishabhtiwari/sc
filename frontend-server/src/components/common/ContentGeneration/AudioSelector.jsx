import React, { useState, useEffect } from 'react';
import { Button } from '../';
import { useAudioGeneration } from '../../../hooks/useAudioGeneration';
import { useToast } from '../../../hooks/useToast';

/**
 * Voice configuration options
 */
const VOICE_MODELS = {
  'kokoro-82m': {
    name: 'Kokoro 82M',
    languages: {
      en: ['am_adam', 'am_michael', 'af_bella', 'af_sarah'],
      zh: ['zh_male', 'zh_female'],
      ja: ['ja_male', 'ja_female'],
      ko: ['ko_male', 'ko_female']
    }
  },
  'mms-tts': {
    name: 'MMS TTS',
    languages: {
      en: ['eng'],
      zh: ['cmn'],
      ja: ['jpn'],
      ko: ['kor'],
      ar: ['ara'],
      hi: ['hin']
    }
  }
};

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
    audioConfig,
    generate,
    previewVoice,
    detectLanguage,
    setAudioUrl,
    setAudioConfig
  } = useAudioGeneration();

  const { showToast } = useToast();

  const [selectedModel, setSelectedModel] = useState(initialConfig.model || 'kokoro-82m');
  const [selectedLanguage, setSelectedLanguage] = useState(initialConfig.language || 'en');
  const [selectedVoice, setSelectedVoice] = useState(initialConfig.voice || 'am_adam');
  const [previewingVoice, setPreviewingVoice] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);

  // Auto-detect language on mount or when text changes
  useEffect(() => {
    if (autoDetectLanguage && text) {
      const detected = detectLanguage(text);
      setSelectedLanguage(detected);
    }
  }, [text, autoDetectLanguage, detectLanguage]);

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

  // Get available voices for selected model and language
  const availableVoices = VOICE_MODELS[selectedModel]?.languages[selectedLanguage] || [];

  return (
    <div className={`audio-selector ${className}`}>
      {/* Audio Configuration */}
      <div className="space-y-4">
        {/* Model Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            TTS Model
          </label>
          <select
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            value={selectedModel}
            onChange={(e) => handleConfigChange('model', e.target.value)}
          >
            {Object.entries(VOICE_MODELS).map(([key, model]) => (
              <option key={key} value={key}>{model.name}</option>
            ))}
          </select>
        </div>

        {/* Language Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Language
          </label>
          <select
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            value={selectedLanguage}
            onChange={(e) => handleConfigChange('language', e.target.value)}
          >
            {Object.keys(VOICE_MODELS[selectedModel]?.languages || {}).map((lang) => (
              <option key={lang} value={lang}>{lang.toUpperCase()}</option>
            ))}
          </select>
        </div>

        {/* Voice Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Voice
          </label>
          <div className="grid grid-cols-2 gap-2">
            {availableVoices.map((voice) => (
              <button
                key={voice}
                onClick={() => handleConfigChange('voice', voice)}
                className={`px-4 py-2 border rounded-lg text-sm ${
                  selectedVoice === voice
                    ? 'border-indigo-500 bg-indigo-50 text-indigo-700'
                    : 'border-gray-300 hover:border-indigo-300'
                }`}
              >
                {voice}
              </button>
            ))}
          </div>
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

