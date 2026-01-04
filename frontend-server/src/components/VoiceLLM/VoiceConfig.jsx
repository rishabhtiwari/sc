import React, { useState, useEffect } from 'react';
import { Card, Button, Spinner } from '../common';
import api from '../../services/api';

/**
 * Voice Configuration Component - Configure voice settings for automation
 * Automatically detects GPU/CPU mode and shows appropriate voices
 */
const VoiceConfig = ({ config, onSave, onPreview, loading }) => {
  const [audioConfig, setAudioConfig] = useState(null);
  const [selectedLanguage, setSelectedLanguage] = useState(config?.language || 'en');
  const [previewingVoice, setPreviewingVoice] = useState(null);

  // Initialize form data from config (new nested structure)
  const [formData, setFormData] = useState({
    language: config?.language || 'en',
    models: config?.models || { en: 'kokoro-82m', hi: 'mms-tts-hin' },
    voices: config?.voices || {
      en: {
        defaultVoice: 'am_adam',
        enableAlternation: true,
        maleVoices: ['am_adam', 'am_michael'],
        femaleVoices: ['af_bella', 'af_sarah'],
      },
      hi: {
        defaultVoice: 'hi_default',
        enableAlternation: false,
        maleVoices: [],
        femaleVoices: [],
      },
    },
  });

  // Fetch audio generation service configuration on mount
  useEffect(() => {
    const fetchAudioConfig = async () => {
      try {
        const response = await api.get('/audio-studio/config');
        setAudioConfig(response.data);
        console.log('Audio config loaded:', response.data);
      } catch (error) {
        console.error('Failed to fetch audio config:', error);
      }
    };
    fetchAudioConfig();
  }, []);

  // Update form data when config changes
  useEffect(() => {
    if (config) {
      setFormData({
        language: config.language || 'en',
        models: config.models || { en: 'kokoro-82m', hi: 'mms-tts-hin' },
        voices: config.voices || formData.voices,
      });
      setSelectedLanguage(config.language || 'en');
    }
  }, [config]);

  // Get current language voice config
  const getCurrentVoiceConfig = () => {
    return formData.voices[selectedLanguage] || {};
  };

  // Update voice config for current language
  const handleVoiceConfigChange = (field, value) => {
    setFormData((prev) => ({
      ...prev,
      voices: {
        ...prev.voices,
        [selectedLanguage]: {
          ...prev.voices[selectedLanguage],
          [field]: value,
        },
      },
    }));
  };

  const handleVoiceSelection = (voiceId, gender) => {
    const field = gender === 'male' ? 'maleVoices' : 'femaleVoices';
    const currentVoices = getCurrentVoiceConfig()[field] || [];

    if (currentVoices.includes(voiceId)) {
      // Remove voice
      handleVoiceConfigChange(field, currentVoices.filter((v) => v !== voiceId));
    } else {
      // Add voice
      handleVoiceConfigChange(field, [...currentVoices, voiceId]);
    }
  };

  const handlePreview = async (voiceId) => {
    setPreviewingVoice(voiceId);
    try {
      console.log('🎵 Starting preview for voice:', voiceId);

      // Use language-appropriate preview text
      const previewTexts = {
        en: 'This is a preview of the selected voice for news narration.',
        hi: 'यह समाचार वाचन के लिए चयनित आवाज का पूर्वावलोकन है।'
      };

      const previewText = previewTexts[selectedLanguage] || previewTexts.en;

      // Use the audio generation service's preview endpoint with caching
      const response = await api.post('/audio/preview', {
        text: previewText,
        model: formData.models[selectedLanguage],
        voice: voiceId,
        language: selectedLanguage
      });

      const audioUrl = response.data.audio_url || response.data.audioUrl;
      console.log('✅ Preview audio URL:', audioUrl);

      // If it's a presigned URL (starts with http), use it directly
      if (audioUrl.startsWith('http')) {
        const audio = new Audio(audioUrl);
        audio.play();
      } else {
        // Otherwise, fetch through proxy with auth
        const token = localStorage.getItem('auth_token');
        const audioResponse = await fetch(audioUrl, {
          headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!audioResponse.ok) {
          throw new Error(`Failed to fetch audio: ${audioResponse.status}`);
        }

        const blob = await audioResponse.blob();
        const blobUrl = URL.createObjectURL(blob);
        const audio = new Audio(blobUrl);

        audio.play();
        audio.onended = () => URL.revokeObjectURL(blobUrl);
        audio.onerror = () => URL.revokeObjectURL(blobUrl);
      }

    } catch (error) {
      console.error('❌ Preview failed:', error);

      // Check if error is due to model loading
      if (error.response?.status === 503 || error.response?.data?.model_loading) {
        alert(`⏳ The TTS model is loading. This may take a few minutes on first use. Please try again in a moment.`);
      } else {
        alert(`Preview failed: ${error.message || 'Unknown error'}`);
      }
    } finally {
      setPreviewingVoice(null);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave(formData);
  };

  // Get available voices from audio config
  const getAvailableVoices = () => {
    if (!audioConfig) return { male: [], female: [], all: [] };

    const modelId = formData.models[selectedLanguage];
    const model = audioConfig.models?.[modelId];

    if (!model) return { male: [], female: [], all: [] };

    // Check if model has voicesWithMetadata (Coqui XTTS)
    if (model.voicesWithMetadata && Array.isArray(model.voicesWithMetadata)) {
      const male = model.voicesWithMetadata.filter(v => v.gender === 'male');
      const female = model.voicesWithMetadata.filter(v => v.gender === 'female');
      return { male, female, all: model.voicesWithMetadata };
    }

    // Fallback to structured voices (Kokoro, MMS)
    if (model.voices) {
      const male = (model.voices.male || []).map(v => ({
        id: v.id || v,
        name: v.name || v.id || v,
        gender: 'male'
      }));
      const female = (model.voices.female || []).map(v => ({
        id: v.id || v,
        name: v.name || v.id || v,
        gender: 'female'
      }));
      const defaultVoices = (model.voices.default || []).map(v => ({
        id: v.id || v,
        name: v.name || v.id || v,
        gender: 'unknown'
      }));

      return {
        male,
        female,
        default: defaultVoices,
        all: [...male, ...female, ...defaultVoices]
      };
    }

    return { male: [], female: [], all: [] };
  };

  const currentVoiceConfig = getCurrentVoiceConfig();
  const availableVoices = getAvailableVoices();
  const isGpuMode = audioConfig?.gpu_enabled || false;

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* System Info Banner */}
      {audioConfig && (
        <div className={`p-4 rounded-lg ${isGpuMode ? 'bg-green-50 border border-green-200' : 'bg-blue-50 border border-blue-200'}`}>
          <div className="flex items-center gap-2">
            <span className="text-2xl">{isGpuMode ? '🎮' : '💻'}</span>
            <div>
              <h4 className="font-semibold text-gray-900">
                {isGpuMode ? 'GPU Mode Active' : 'CPU Mode Active'}
              </h4>
              <p className="text-sm text-gray-600">
                {isGpuMode
                  ? `Using ${audioConfig.default_model} - Universal multi-lingual model with ${availableVoices.all.length} speakers`
                  : `Using language-specific models - ${availableVoices.all.length} voices available`
                }
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Primary Language Selection */}
      <Card title="Primary Language">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Default Language for News Articles
            </label>
            <select
              value={formData.language}
              onChange={(e) => {
                setFormData((prev) => ({ ...prev, language: e.target.value }));
                setSelectedLanguage(e.target.value);
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="en">🇬🇧 English</option>
              <option value="hi">🇮🇳 Hindi</option>
            </select>
          </div>
        </div>
      </Card>

      {/* Language Tabs for Configuration */}
      <Card title="Voice Configuration by Language">
        <div className="mb-6">
          <div className="flex gap-2 border-b">
            <button
              type="button"
              onClick={() => setSelectedLanguage('en')}
              className={`px-4 py-2 font-medium text-sm transition-colors ${
                selectedLanguage === 'en'
                  ? 'border-b-2 border-blue-600 text-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              🇬🇧 English
            </button>
            <button
              type="button"
              onClick={() => setSelectedLanguage('hi')}
              className={`px-4 py-2 font-medium text-sm transition-colors ${
                selectedLanguage === 'hi'
                  ? 'border-b-2 border-blue-600 text-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              🇮🇳 Hindi
            </button>
          </div>
        </div>

        {/* Voice Alternation Toggle */}
        <div className="flex items-center justify-between mb-6 p-4 bg-gray-50 rounded-lg">
          <div>
            <h4 className="text-sm font-medium text-gray-900">Enable Voice Alternation</h4>
            <p className="text-sm text-gray-500 mt-1">
              Automatically alternate between male and female voices for {selectedLanguage === 'en' ? 'English' : 'Hindi'} articles
            </p>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={currentVoiceConfig.enableAlternation !== false}
              onChange={(e) => handleVoiceConfigChange('enableAlternation', e.target.checked)}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
          </label>
        </div>
      </Card>

      {/* Male Voices */}
      {availableVoices.male && availableVoices.male.length > 0 && (
        <Card title={`👨 Male Voices (${availableVoices.male.length})`}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {availableVoices.male.map((voice) => {
              const isSelected = (currentVoiceConfig.maleVoices || []).includes(voice.id);
              return (
                <div
                  key={voice.id}
                  className={`p-4 rounded-lg border-2 transition-all cursor-pointer ${
                    isSelected
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 bg-white hover:border-gray-300'
                  }`}
                  onClick={() => handleVoiceSelection(voice.id, 'male')}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <h4 className="font-semibold text-gray-900">{voice.name || voice.id}</h4>
                      {voice.accent && (
                        <p className="text-xs text-gray-500 mt-1">Accent: {voice.accent}</p>
                      )}
                      {voice.description && (
                        <p className="text-xs text-gray-600 mt-1">{voice.description}</p>
                      )}
                    </div>
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => {}}
                      className="h-5 w-5 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                  </div>
                  <Button
                    type="button"
                    variant="secondary"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      handlePreview(voice.id);
                    }}
                    disabled={previewingVoice === voice.id}
                    className="w-full"
                  >
                    {previewingVoice === voice.id ? (
                      <>
                        <Spinner size="sm" /> Playing...
                      </>
                    ) : (
                      '🔊 Preview'
                    )}
                  </Button>
                </div>
              );
            })}
          </div>
        </Card>
      )}

      {/* Female Voices */}
      {availableVoices.female && availableVoices.female.length > 0 && (
        <Card title={`👩 Female Voices (${availableVoices.female.length})`}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {availableVoices.female.map((voice) => {
              const isSelected = (currentVoiceConfig.femaleVoices || []).includes(voice.id);
              return (
                <div
                  key={voice.id}
                  className={`p-4 rounded-lg border-2 transition-all cursor-pointer ${
                    isSelected
                      ? 'border-pink-500 bg-pink-50'
                      : 'border-gray-200 bg-white hover:border-gray-300'
                  }`}
                  onClick={() => handleVoiceSelection(voice.id, 'female')}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <h4 className="font-semibold text-gray-900">{voice.name || voice.id}</h4>
                      {voice.accent && (
                        <p className="text-xs text-gray-500 mt-1">Accent: {voice.accent}</p>
                      )}
                      {voice.description && (
                        <p className="text-xs text-gray-600 mt-1">{voice.description}</p>
                      )}
                    </div>
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => {}}
                      className="h-5 w-5 text-pink-600 focus:ring-pink-500 border-gray-300 rounded"
                    />
                  </div>
                  <Button
                    type="button"
                    variant="secondary"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      handlePreview(voice.id);
                    }}
                    disabled={previewingVoice === voice.id}
                    className="w-full"
                  >
                    {previewingVoice === voice.id ? (
                      <>
                        <Spinner size="sm" /> Playing...
                      </>
                    ) : (
                      '🔊 Preview'
                    )}
                  </Button>
                </div>
              );
            })}
          </div>
        </Card>
      )}

      {/* Default Voices (for models with single voice like Hindi MMS) */}
      {availableVoices.default && availableVoices.default.length > 0 && (
        <Card title="Available Voice">
          <div className="space-y-3">
            <p className="text-sm text-gray-600 mb-3">
              This model only supports a single voice. Voice alternation is not available.
            </p>
            {availableVoices.default.map((voice) => (
              <div
                key={voice.id}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div>
                    <p className="text-sm font-medium text-gray-900">{voice.name}</p>
                    <p className="text-xs text-gray-500">ID: {voice.id}</p>
                  </div>
                </div>
                <Button
                  type="button"
                  variant="secondary"
                  size="sm"
                  onClick={() => handlePreview(voice.id)}
                  disabled={previewLoading}
                >
                  {previewLoading ? <Spinner size="sm" /> : 'Preview'}
                </Button>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Default Voice Selection */}
      <Card title="Default Voice">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select Default Voice for {selectedLanguage === 'en' ? 'English' : 'Hindi'}
          </label>
          <select
            value={currentVoiceConfig.defaultVoice || ''}
            onChange={(e) => handleVoiceConfigChange('defaultVoice', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            {availableVoices.default && availableVoices.default.length > 0 && (
              <optgroup label="Default Voice">
                {availableVoices.default.map((voice) => (
                  <option key={voice.id} value={voice.id}>
                    {voice.name}
                  </option>
                ))}
              </optgroup>
            )}
            {availableVoices.male && availableVoices.male.length > 0 && (
              <optgroup label="Male Voices">
                {availableVoices.male.map((voice) => (
                  <option key={voice.id} value={voice.id}>
                    {voice.name}
                  </option>
                ))}
              </optgroup>
            )}
            {availableVoices.female && availableVoices.female.length > 0 && (
              <optgroup label="Female Voices">
                {availableVoices.female.map((voice) => (
                  <option key={voice.id} value={voice.id}>
                    {voice.name}
                  </option>
                ))}
              </optgroup>
            )}
          </select>
        </div>
      </Card>

      {/* Actions */}
      <div className="flex justify-end gap-3 pt-4 border-t">
        <Button variant="primary" type="submit" loading={loading}>
          Save Configuration
        </Button>
      </div>
    </form>
  );
};

export default VoiceConfig;

