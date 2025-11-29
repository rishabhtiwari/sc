import React, { useState, useEffect } from 'react';
import { Card, Button, Spinner } from '../common';

/**
 * Voice Configuration Component - Configure voice settings
 */
const VoiceConfig = ({ config, onSave, onPreview, loading }) => {
  const [formData, setFormData] = useState({
    defaultVoice: config?.defaultVoice || 'am_adam',
    enableAlternation: config?.enableAlternation !== false,
    language: config?.language || 'en',
    maleVoices: config?.maleVoices || ['am_adam', 'am_michael'],
    femaleVoices: config?.femaleVoices || ['af_bella', 'af_sarah'],
  });

  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewAudio, setPreviewAudio] = useState(null);

  // Available voices for English (Kokoro-82M)
  const englishVoices = {
    male: [
      { id: 'am_adam', name: 'Adam (American Male)', gender: 'male' },
      { id: 'am_michael', name: 'Michael (American Male)', gender: 'male' },
      { id: 'bm_george', name: 'George (British Male)', gender: 'male' },
      { id: 'bm_lewis', name: 'Lewis (British Male)', gender: 'male' },
    ],
    female: [
      { id: 'af_bella', name: 'Bella (American Female)', gender: 'female' },
      { id: 'af_nicole', name: 'Nicole (American Female)', gender: 'female' },
      { id: 'af_sarah', name: 'Sarah (American Female)', gender: 'female' },
      { id: 'af_sky', name: 'Sky (American Female)', gender: 'female' },
      { id: 'bf_emma', name: 'Emma (British Female)', gender: 'female' },
      { id: 'bf_isabella', name: 'Isabella (British Female)', gender: 'female' },
    ],
  };

  // Available languages
  const languages = [
    { code: 'en', name: 'English', model: 'kokoro-82m' },
    { code: 'hi', name: 'Hindi', model: 'mms-tts-hin' },
  ];

  const handleChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleVoiceSelection = (voiceId, gender) => {
    const field = gender === 'male' ? 'maleVoices' : 'femaleVoices';
    const currentVoices = formData[field];
    
    if (currentVoices.includes(voiceId)) {
      // Remove voice
      handleChange(field, currentVoices.filter((v) => v !== voiceId));
    } else {
      // Add voice
      handleChange(field, [...currentVoices, voiceId]);
    }
  };

  const handlePreview = async (voiceId) => {
    setPreviewLoading(true);
    try {
      const audioUrl = await onPreview(voiceId, 'This is a preview of the selected voice for news narration.');
      setPreviewAudio(audioUrl);
      
      // Play audio
      const audio = new Audio(audioUrl);
      audio.play();
    } catch (error) {
      console.error('Preview failed:', error);
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave(formData);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Language Selection */}
      <Card title="Language Settings">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Default Language
            </label>
            <select
              value={formData.language}
              onChange={(e) => handleChange('language', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              {languages.map((lang) => (
                <option key={lang.code} value={lang.code}>
                  {lang.name} ({lang.model})
                </option>
              ))}
            </select>
          </div>
        </div>
      </Card>

      {/* Voice Alternation */}
      <Card title="Voice Alternation">
        <div className="flex items-center justify-between">
          <div>
            <h4 className="text-sm font-medium text-gray-900">Enable Voice Alternation</h4>
            <p className="text-sm text-gray-500 mt-1">
              Automatically alternate between male and female voices for consecutive news articles
            </p>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={formData.enableAlternation}
              onChange={(e) => handleChange('enableAlternation', e.target.checked)}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
          </label>
        </div>
      </Card>

      {/* Voice Selection - Only for English */}
      {formData.language === 'en' && (
        <>
          {/* Male Voices */}
          <Card title="Male Voices">
            <div className="space-y-3">
              {englishVoices.male.map((voice) => (
                <div
                  key={voice.id}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      checked={formData.maleVoices.includes(voice.id)}
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

          {/* Female Voices */}
          <Card title="Female Voices">
            <div className="space-y-3">
              {englishVoices.female.map((voice) => (
                <div
                  key={voice.id}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      checked={formData.femaleVoices.includes(voice.id)}
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

          {/* Default Voice */}
          <Card title="Default Voice">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Default Voice
              </label>
              <select
                value={formData.defaultVoice}
                onChange={(e) => handleChange('defaultVoice', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <optgroup label="Male Voices">
                  {englishVoices.male.map((voice) => (
                    <option key={voice.id} value={voice.id}>
                      {voice.name}
                    </option>
                  ))}
                </optgroup>
                <optgroup label="Female Voices">
                  {englishVoices.female.map((voice) => (
                    <option key={voice.id} value={voice.id}>
                      {voice.name}
                    </option>
                  ))}
                </optgroup>
              </select>
            </div>
          </Card>
        </>
      )}

      {/* Hindi Voice Info */}
      {formData.language === 'hi' && (
        <Card title="Hindi Voice" className="bg-blue-50">
          <p className="text-sm text-gray-700">
            Hindi language uses the MMS-TTS-HIN model. Voice selection and alternation are not available for Hindi.
          </p>
        </Card>
      )}

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

