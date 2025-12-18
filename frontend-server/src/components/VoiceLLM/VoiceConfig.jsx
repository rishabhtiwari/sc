import React, { useState, useEffect } from 'react';
import { Card, Button, Spinner } from '../common';
import { getAvailableModels } from '../../services/voiceService';

/**
 * Voice Configuration Component - Configure voice settings with model selection
 */
const VoiceConfig = ({ config, onSave, onPreview, loading }) => {
  const [availableModels, setAvailableModels] = useState(null);
  const [selectedLanguage, setSelectedLanguage] = useState(config?.language || 'en');

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
        enableAlternation: false,  // MMS Hindi only has one voice
        maleVoices: [],
        femaleVoices: [],
      },
    },
  });

  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewAudio, setPreviewAudio] = useState(null);

  // Fetch available models on mount
  useEffect(() => {
    const fetchModels = async () => {
      try {
        const response = await getAvailableModels();
        setAvailableModels(response.models);
      } catch (error) {
        console.error('Failed to fetch available models:', error);
      }
    };
    fetchModels();
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

  // Update model for a language
  const handleModelChange = (language, modelId) => {
    setFormData((prev) => ({
      ...prev,
      models: {
        ...prev.models,
        [language]: modelId,
      },
    }));
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
    setPreviewLoading(true);
    try {
      console.log('🎵 Starting preview for voice:', voiceId);

      // Use language-appropriate preview text
      const previewTexts = {
        en: 'This is a preview of the selected voice for news narration.',
        hi: 'यह समाचार वाचन के लिए चयनित आवाज का पूर्वावलोकन है।'
      };

      // Determine language from voice ID (hi_ prefix = Hindi, else English)
      const language = voiceId.startsWith('hi_') ? 'hi' : 'en';
      const previewText = previewTexts[language];

      let audioUrl;
      try {
        audioUrl = await onPreview(voiceId, previewText);
      } catch (err) {
        // Check if error is due to model loading
        if (err.model_loading) {
          alert(`⏳ ${err.message}\n\nThe TTS model is being downloaded and initialized. This happens only on first use and may take 2-5 minutes. Please wait and try again.`);
          return;
        }
        throw err;
      }

      console.log('✅ Preview API returned audio URL:', audioUrl);
      setPreviewAudio(audioUrl);

      // Fetch the audio file with authentication headers
      // The audioUrl is a relative path like /api/voice/preview/audio/kokoro_123.wav
      const token = localStorage.getItem('token');
      console.log('🔑 Token exists:', !!token);

      console.log('📥 Fetching audio from:', audioUrl);
      const response = await fetch(audioUrl, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      console.log('📡 Response status:', response.status, response.statusText);
      console.log('📡 Response headers:', {
        contentType: response.headers.get('Content-Type'),
        contentLength: response.headers.get('Content-Length')
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch audio: ${response.status} ${response.statusText}`);
      }

      // Create a blob URL from the response
      const blob = await response.blob();
      console.log('📦 Blob created:', { size: blob.size, type: blob.type });

      const blobUrl = URL.createObjectURL(blob);
      console.log('🔗 Blob URL created:', blobUrl);

      // Play audio using the blob URL
      const audio = new Audio(blobUrl);
      console.log('🔊 Audio element created, attempting to play...');

      audio.play().then(() => {
        console.log('✅ Audio playback started successfully');
      }).catch(err => {
        console.error('❌ Failed to play audio:', err);
        console.error('Error details:', {
          name: err.name,
          message: err.message,
          stack: err.stack
        });
        alert('Failed to play audio preview. Please check browser console for details.');
      });

      // Clean up blob URL after audio finishes or errors
      audio.onended = () => {
        console.log('🏁 Audio playback ended');
        URL.revokeObjectURL(blobUrl);
      };
      audio.onerror = (e) => {
        console.error('❌ Audio element error:', e);
        console.error('Audio error details:', {
          error: audio.error,
          networkState: audio.networkState,
          readyState: audio.readyState
        });
        URL.revokeObjectURL(blobUrl);
      };

    } catch (error) {
      console.error('❌ Preview failed:', error);
      console.error('Error stack:', error.stack);
      alert(`Preview failed: ${error.message || 'Unknown error'}`);
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave(formData);
  };

  // Get available voices for selected model
  const getAvailableVoices = () => {
    if (!availableModels) return { male: [], female: [] };
    const modelId = formData.models[selectedLanguage];
    const model = availableModels[modelId];
    if (!model) return { male: [], female: [] };
    return model.voices;
  };

  const currentVoiceConfig = getCurrentVoiceConfig();
  const availableVoices = getAvailableVoices();

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
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
              <option value="en">English</option>
              <option value="hi">Hindi</option>
            </select>
          </div>
        </div>
      </Card>

      {/* Language Tabs for Configuration */}
      <Card title="Voice Configuration by Language">
        <div className="mb-4">
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
              English
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
              Hindi
            </button>
          </div>
        </div>

        {/* Model Selection for Current Language */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            TTS Model for {selectedLanguage === 'en' ? 'English' : 'Hindi'}
          </label>
          <select
            value={formData.models[selectedLanguage] || ''}
            onChange={(e) => handleModelChange(selectedLanguage, e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            {availableModels &&
              Object.values(availableModels)
                .filter((model) => model.languages.includes(selectedLanguage))
                .map((model) => (
                  <option key={model.id} value={model.id}>
                    {model.name} - {model.description}
                  </option>
                ))}
          </select>
        </div>

        {/* Voice Alternation for Current Language */}
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
        <Card title="Male Voices">
          <div className="space-y-3">
            {availableVoices.male.map((voice) => (
              <div
                key={voice.id}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    checked={(currentVoiceConfig.maleVoices || []).includes(voice.id)}
                    onChange={() => handleVoiceSelection(voice.id, 'male')}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
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

      {/* Female Voices */}
      {availableVoices.female && availableVoices.female.length > 0 && (
        <Card title="Female Voices">
          <div className="space-y-3">
            {availableVoices.female.map((voice) => (
              <div
                key={voice.id}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    checked={(currentVoiceConfig.femaleVoices || []).includes(voice.id)}
                    onChange={() => handleVoiceSelection(voice.id, 'female')}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
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

