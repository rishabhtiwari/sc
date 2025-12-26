import React, { useState, useEffect, useCallback } from 'react';
import { Button } from '../';
import { useAudioGeneration } from '../../../hooks/useAudioGeneration';
import { useToast } from '../../../hooks/useToast';
import {
  AUDIO_MODELS,
  LANGUAGES,
  getAvailableVoices,
  getDefaultVoice,
  getDefaultModel
} from '../../../constants/audioModels';

/**
 * AudioGenerator Component
 * 
 * A comprehensive, reusable audio generation component that supports:
 * - Single text-to-speech conversion
 * - Section-based audio generation with individual controls
 * - Batch audio processing
 * - Voice preview and selection
 * - Speed/pitch adjustments per section
 * - Audio playback controls
 * 
 * @param {Object} props
 * @param {string} props.endpoint - API endpoint for audio generation
 * @param {string} props.text - Single text to convert (for simple mode)
 * @param {Array} props.sections - Array of sections for section-based generation
 * @param {string} props.initialAudioUrl - Initial audio URL
 * @param {Object} props.initialConfig - Initial audio config
 * @param {Function} props.onAudioGenerated - Callback when audio is generated
 * @param {Function} props.onSectionAudioGenerated - Callback for section audio
 * @param {Function} props.onConfigChange - Callback when config changes
 * @param {boolean} props.autoDetectLanguage - Auto-detect language
 * @param {boolean} props.showSectionControls - Show section-level controls
 * @param {boolean} props.showAdvancedOptions - Show advanced options
 * @param {boolean} props.allowBatchGeneration - Allow generating all sections at once
 * @param {string} props.mode - 'simple' or 'sections'
 * @param {string} props.className - Additional CSS classes
 */
const AudioGenerator = ({
  endpoint,
  text = '',
  sections = [],
  initialAudioUrl = null,
  initialConfig = {},
  onAudioGenerated,
  onSectionAudioGenerated,
  onConfigChange,
  autoDetectLanguage = true,
  showSectionControls = true,
  showAdvancedOptions = false,
  allowBatchGeneration = true,
  mode = 'simple', // 'simple' or 'sections'
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

  // Audio configuration state
  const [selectedModel, setSelectedModel] = useState(initialConfig.model || 'kokoro-82m');
  const [selectedLanguage, setSelectedLanguage] = useState(initialConfig.language || 'en');
  const [selectedVoice, setSelectedVoice] = useState(initialConfig.voice || 'am_adam');
  
  // Section-specific state
  const [sectionSpeeds, setSectionSpeeds] = useState({});
  const [sectionAudioUrls, setSectionAudioUrls] = useState({});
  const [generatingSections, setGeneratingSections] = useState({});
  
  // UI state
  const [previewingVoice, setPreviewingVoice] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [expandedSections, setExpandedSections] = useState({});
  const [showVoicePreview, setShowVoicePreview] = useState(false);

  // Auto-detect language on mount or when text changes
  useEffect(() => {
    if (autoDetectLanguage && (text || sections.length > 0)) {
      const textToDetect = text || sections.map(s => s.content).join(' ');
      const detected = detectLanguage(textToDetect);
      setSelectedLanguage(detected);
    }
  }, [text, sections, autoDetectLanguage, detectLanguage]);

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
   * Handle audio generation for simple mode
   */
  const handleGenerateSimple = async () => {
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
   * Handle audio generation for a specific section
   */
  const handleGenerateSection = async (sectionIndex) => {
    const section = sections[sectionIndex];
    if (!section || !section.content) {
      showToast('No content in this section', 'error');
      return;
    }

    setGeneratingSections(prev => ({ ...prev, [sectionIndex]: true }));

    const speed = sectionSpeeds[section.title] || 1.0;

    const result = await generate({
      endpoint,
      text: section.content,
      model: selectedModel,
      language: selectedLanguage,
      voice: selectedVoice,
      sectionSpeeds: { [section.title]: speed },
      onSuccess: (url, data) => {
        showToast(`Audio generated for "${section.title}"`, 'success');

        setSectionAudioUrls(prev => ({ ...prev, [sectionIndex]: url }));

        if (onSectionAudioGenerated) {
          onSectionAudioGenerated(sectionIndex, url, {
            model: selectedModel,
            language: selectedLanguage,
            voice: selectedVoice,
            speed
          }, data);
        }
      },
      onError: (error) => {
        showToast(error, 'error');
      }
    });

    setGeneratingSections(prev => ({ ...prev, [sectionIndex]: false }));
    return result;
  };

  /**
   * Handle batch generation for all sections
   */
  const handleGenerateAllSections = async () => {
    if (sections.length === 0) {
      showToast('No sections to generate audio for', 'error');
      return;
    }

    showToast(`Generating audio for ${sections.length} sections...`, 'info');

    // Generate audio for each section sequentially
    for (let i = 0; i < sections.length; i++) {
      await handleGenerateSection(i);
    }

    showToast('All section audio generated successfully', 'success');
  };

  /**
   * Handle voice preview
   */
  const handlePreviewVoice = async (voiceId) => {
    setPreviewingVoice(voiceId);

    await previewVoice({
      voice: voiceId,
      model: selectedModel,
      language: selectedLanguage,
      sampleText: 'Hello, this is a voice preview. How does this sound?',
      onSuccess: (url) => {
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
  const handleConfigChange = useCallback((field, value) => {
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
  }, [selectedModel, selectedLanguage, selectedVoice, onConfigChange]);

  /**
   * Handle section speed change
   */
  const handleSectionSpeedChange = (sectionTitle, speed) => {
    setSectionSpeeds(prev => ({ ...prev, [sectionTitle]: speed }));
  };

  /**
   * Toggle section expansion
   */
  const toggleSection = (index) => {
    setExpandedSections(prev => ({ ...prev, [index]: !prev[index] }));
  };

  // Get available voices for selected model
  const availableVoices = getAvailableVoices(selectedModel);

  // Get supported languages for selected model
  const supportedLanguages = AUDIO_MODELS[selectedModel]?.languages || [];

  return (
    <div className={`audio-generator space-y-6 ${className}`}>
      {/* Audio Configuration Panel */}
      <div className="bg-white border border-gray-200 rounded-lg p-6 space-y-4">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">🎙️ Audio Configuration</h3>

        {/* Model Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            TTS Model
          </label>
          <select
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            value={selectedModel}
            onChange={(e) => handleConfigChange('model', e.target.value)}
          >
            {Object.entries(AUDIO_MODELS).map(([key, model]) => (
              <option key={key} value={key}>
                {model.name} - {model.description}
              </option>
            ))}
          </select>
        </div>

        {/* Language Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Language
          </label>
          <select
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            value={selectedLanguage}
            onChange={(e) => handleConfigChange('language', e.target.value)}
          >
            {LANGUAGES.filter(lang => supportedLanguages.includes(lang.id)).map((lang) => (
              <option key={lang.id} value={lang.id}>
                {lang.flag} {lang.name}
              </option>
            ))}
          </select>
        </div>

        {/* Voice Selection */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="block text-sm font-medium text-gray-700">
              Voice
            </label>
            <button
              onClick={() => setShowVoicePreview(!showVoicePreview)}
              className="text-sm text-indigo-600 hover:text-indigo-700"
            >
              {showVoicePreview ? 'Hide' : 'Show'} Preview
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {availableVoices.map((voice) => (
              <div
                key={voice.id}
                className={`border rounded-lg p-3 cursor-pointer transition-all ${
                  selectedVoice === voice.id
                    ? 'border-indigo-500 bg-indigo-50 ring-2 ring-indigo-500'
                    : 'border-gray-300 hover:border-indigo-300'
                }`}
                onClick={() => handleConfigChange('voice', voice.id)}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-semibold text-gray-900">
                      {voice.gender === 'male' ? '👨' : voice.gender === 'female' ? '👩' : '🎭'} {voice.name}
                    </div>
                    <div className="text-xs text-gray-600">{voice.description}</div>
                  </div>

                  {showVoicePreview && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handlePreviewVoice(voice.id);
                      }}
                      disabled={previewingVoice === voice.id}
                      className="px-2 py-1 text-xs bg-indigo-100 text-indigo-700 rounded hover:bg-indigo-200 disabled:opacity-50"
                    >
                      {previewingVoice === voice.id ? '⏳' : '▶️'}
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Simple Mode - Single Audio Generation */}
      {mode === 'simple' && (
        <div className="space-y-4">
          <Button
            variant="primary"
            onClick={handleGenerateSimple}
            loading={generating}
            disabled={generating || !text}
            className="w-full"
          >
            {audioUrl ? '🔄 Regenerate Audio' : '🎵 Generate Audio'}
          </Button>

          {/* Audio Player */}
          {audioUrl && (
            <div className="border border-gray-300 rounded-lg p-4 bg-gray-50">
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
      )}

      {/* Sections Mode - Section-based Audio Generation */}
      {mode === 'sections' && sections.length > 0 && (
        <div className="space-y-4">
          {/* Batch Generation Button */}
          {allowBatchGeneration && (
            <Button
              variant="primary"
              onClick={handleGenerateAllSections}
              loading={generating}
              disabled={generating}
              className="w-full"
            >
              🎵 Generate Audio for All Sections ({sections.length})
            </Button>
          )}

          {/* Section List */}
          <div className="space-y-3">
            {sections.map((section, index) => (
              <div
                key={index}
                className="border border-gray-200 rounded-lg overflow-hidden"
              >
                {/* Section Header */}
                <div
                  className="flex items-center justify-between p-4 bg-gray-50 cursor-pointer hover:bg-gray-100"
                  onClick={() => toggleSection(index)}
                >
                  <div className="flex items-center gap-3">
                    <span className="text-lg">
                      {expandedSections[index] ? '▼' : '▶️'}
                    </span>
                    <div>
                      <h4 className="font-semibold text-gray-900">{section.title}</h4>
                      <p className="text-sm text-gray-600">
                        {section.content?.length || 0} characters
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    {sectionAudioUrls[index] && (
                      <span className="text-green-600 text-sm">✓ Generated</span>
                    )}
                  </div>
                </div>

                {/* Section Details (Expanded) */}
                {expandedSections[index] && (
                  <div className="p-4 space-y-4 border-t border-gray-200">
                    {/* Section Content Preview */}
                    <div className="text-sm text-gray-700 bg-white p-3 rounded border border-gray-200 max-h-32 overflow-y-auto">
                      {section.content}
                    </div>

                    {/* Speed Control */}
                    {showSectionControls && (
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Speed: {sectionSpeeds[section.title] || 1.0}x
                        </label>
                        <input
                          type="range"
                          min="0.5"
                          max="2.0"
                          step="0.1"
                          value={sectionSpeeds[section.title] || 1.0}
                          onChange={(e) => handleSectionSpeedChange(section.title, parseFloat(e.target.value))}
                          className="w-full"
                        />
                        <div className="flex justify-between text-xs text-gray-500 mt-1">
                          <span>0.5x (Slow)</span>
                          <span>1.0x (Normal)</span>
                          <span>2.0x (Fast)</span>
                        </div>
                      </div>
                    )}

                    {/* Generate Button for Section */}
                    <Button
                      variant="secondary"
                      onClick={() => handleGenerateSection(index)}
                      loading={generatingSections[index]}
                      disabled={generatingSections[index]}
                      className="w-full"
                    >
                      {sectionAudioUrls[index] ? '🔄 Regenerate' : '🎵 Generate'} Audio
                    </Button>

                    {/* Section Audio Player */}
                    {sectionAudioUrls[index] && (
                      <div className="border border-gray-300 rounded-lg p-3 bg-gray-50">
                        <audio
                          controls
                          src={sectionAudioUrls[index]}
                          className="w-full"
                        />
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Combined Audio Player (if available) */}
      {mode === 'sections' && audioUrl && (
        <div className="border border-indigo-200 rounded-lg p-4 bg-indigo-50">
          <h4 className="font-semibold text-gray-900 mb-3">🎧 Combined Audio</h4>
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
  );
};

export default AudioGenerator;


