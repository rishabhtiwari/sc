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
  const [genderFilter, setGenderFilter] = useState('all'); // 'all', 'male', 'female'
  const [searchQuery, setSearchQuery] = useState('');

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

  // Filter voices based on gender filter and search query
  const getFilteredVoices = () => {
    const voices = getAvailableVoices();
    let filtered = voices.all;

    // Apply gender filter
    if (genderFilter === 'male') {
      filtered = voices.male;
    } else if (genderFilter === 'female') {
      filtered = voices.female;
    }

    // Apply search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(v =>
        (v.name || v.id).toLowerCase().includes(query) ||
        (v.accent && v.accent.toLowerCase().includes(query))
      );
    }

    return filtered;
  };

  const currentVoiceConfig = getCurrentVoiceConfig();
  const availableVoices = getAvailableVoices();
  const filteredVoices = getFilteredVoices();
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

      {/* Browse Voices */}
      <Card title="🎤 Browse Voices">
        {/* Filters */}
        <div className="mb-4 space-y-3">
          {/* Search */}
          <div>
            <input
              type="text"
              placeholder="Search voices by name or accent..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Gender Filter */}
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setGenderFilter('all')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                genderFilter === 'all'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              All ({availableVoices.all.length})
            </button>
            <button
              type="button"
              onClick={() => setGenderFilter('male')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                genderFilter === 'male'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              👨 Male ({availableVoices.male.length})
            </button>
            <button
              type="button"
              onClick={() => setGenderFilter('female')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                genderFilter === 'female'
                  ? 'bg-pink-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              👩 Female ({availableVoices.female.length})
            </button>
          </div>
        </div>

        {/* Voice Cards Grid */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
          {filteredVoices.map((voice) => {
            const isDefault = currentVoiceConfig.defaultVoice === voice.id;
            const isMaleVoice = (currentVoiceConfig.maleVoices || []).includes(voice.id);
            const isFemaleVoice = (currentVoiceConfig.femaleVoices || []).includes(voice.id);
            const genderIcon = voice.gender === 'male' ? '👨' : voice.gender === 'female' ? '👩' : '🎭';

            return (
              <div
                key={voice.id}
                className={`p-3 rounded-lg border-2 transition-all ${
                  isDefault
                    ? 'border-green-500 bg-green-50'
                    : 'border-gray-200 bg-white hover:border-gray-300'
                }`}
              >
                <div className="mb-2">
                  <div className="flex items-center gap-1 mb-1">
                    <span className="text-lg">{genderIcon}</span>
                    <h4 className="font-medium text-sm text-gray-900 truncate flex-1" title={voice.name || voice.id}>
                      {voice.name || voice.id}
                    </h4>
                  </div>
                  {voice.accent && voice.accent !== 'neutral' && (
                    <p className="text-xs text-gray-500 truncate" title={voice.accent}>
                      {voice.accent}
                    </p>
                  )}
                  <div className="flex gap-1 mt-1 flex-wrap">
                    {isDefault && (
                      <span className="inline-block px-2 py-0.5 bg-green-100 text-green-700 text-xs font-medium rounded">
                        ⭐ Default
                      </span>
                    )}
                    {isMaleVoice && (
                      <span className="inline-block px-2 py-0.5 bg-blue-100 text-blue-700 text-xs font-medium rounded">
                        👨 Male
                      </span>
                    )}
                    {isFemaleVoice && (
                      <span className="inline-block px-2 py-0.5 bg-pink-100 text-pink-700 text-xs font-medium rounded">
                        👩 Female
                      </span>
                    )}
                  </div>
                </div>

                <div className="space-y-1.5">
                  <Button
                    type="button"
                    variant="secondary"
                    size="sm"
                    onClick={() => handlePreview(voice.id)}
                    disabled={previewingVoice === voice.id}
                    className="w-full text-xs py-1.5"
                  >
                    {previewingVoice === voice.id ? (
                      <>
                        <Spinner size="sm" /> Playing...
                      </>
                    ) : (
                      '🔊 Preview'
                    )}
                  </Button>

                  <Button
                    type="button"
                    variant="primary"
                    size="sm"
                    onClick={() => handleVoiceConfigChange('defaultVoice', voice.id)}
                    className="w-full text-xs py-1.5"
                  >
                    {isDefault ? '⭐ Default' : 'Set Default'}
                  </Button>

                  {/* Add to Male/Female for alternation */}
                  {currentVoiceConfig.enableAlternation && voice.gender === 'male' && (
                    <Button
                      type="button"
                      variant={isMaleVoice ? 'primary' : 'secondary'}
                      size="sm"
                      onClick={() => handleVoiceSelection(voice.id, 'male')}
                      className="w-full text-xs py-1.5"
                    >
                      {isMaleVoice ? '✓ Male Voice' : '+ Add Male'}
                    </Button>
                  )}

                  {currentVoiceConfig.enableAlternation && voice.gender === 'female' && (
                    <Button
                      type="button"
                      variant={isFemaleVoice ? 'primary' : 'secondary'}
                      size="sm"
                      onClick={() => handleVoiceSelection(voice.id, 'female')}
                      className="w-full text-xs py-1.5"
                    >
                      {isFemaleVoice ? '✓ Female Voice' : '+ Add Female'}
                    </Button>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {filteredVoices.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            <p>No voices found matching your filters.</p>
          </div>
        )}
      </Card>

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



      {/* Automation Summary */}
      <Card title="📋 Automation Summary">
        <div className="space-y-4">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h4 className="font-semibold text-blue-900 mb-2">
              {selectedLanguage === 'en' ? '🇬🇧 English' : '🇮🇳 Hindi'} News Articles
            </h4>
            <div className="space-y-2 text-sm">
              <div className="flex items-start gap-2">
                <span className="text-blue-600 font-medium min-w-[120px]">Model:</span>
                <span className="text-gray-700">{formData.models[selectedLanguage]}</span>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-blue-600 font-medium min-w-[120px]">Default Voice:</span>
                <span className="text-gray-700">{currentVoiceConfig.defaultVoice || 'Not set'}</span>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-blue-600 font-medium min-w-[120px]">Alternation:</span>
                <span className={`font-semibold ${currentVoiceConfig.enableAlternation ? 'text-green-600' : 'text-gray-600'}`}>
                  {currentVoiceConfig.enableAlternation ? '✅ Enabled' : '❌ Disabled'}
                </span>
              </div>
              {currentVoiceConfig.enableAlternation && (
                <>
                  <div className="flex items-start gap-2">
                    <span className="text-blue-600 font-medium min-w-[120px]">Male Voices:</span>
                    <span className="text-gray-700">
                      {(currentVoiceConfig.maleVoices || []).length > 0
                        ? currentVoiceConfig.maleVoices.join(', ')
                        : 'None selected'}
                    </span>
                  </div>
                  <div className="flex items-start gap-2">
                    <span className="text-blue-600 font-medium min-w-[120px]">Female Voices:</span>
                    <span className="text-gray-700">
                      {(currentVoiceConfig.femaleVoices || []).length > 0
                        ? currentVoiceConfig.femaleVoices.join(', ')
                        : 'None selected'}
                    </span>
                  </div>
                  <div className="mt-3 p-3 bg-white rounded border border-blue-200">
                    <p className="text-xs text-gray-600">
                      <strong>How it works:</strong> When generating audio for news articles, the system will automatically
                      alternate between the first male voice and the first female voice from your selected lists.
                      This creates variety in your automated news narration.
                    </p>
                  </div>
                </>
              )}
              {!currentVoiceConfig.enableAlternation && (
                <div className="mt-3 p-3 bg-white rounded border border-blue-200">
                  <p className="text-xs text-gray-600">
                    <strong>How it works:</strong> All news articles will use the default voice: <strong>{currentVoiceConfig.defaultVoice}</strong>
                  </p>
                </div>
              )}
            </div>
          </div>
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

