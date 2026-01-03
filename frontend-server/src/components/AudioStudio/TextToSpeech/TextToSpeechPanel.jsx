import React, { useState, useRef, useEffect } from 'react';
import { Button } from '../../common';
import { useToast } from '../../../hooks/useToast';
import { useAudioGeneration } from '../../../hooks/useAudioGeneration';
import { useAudioLibrary } from '../../../hooks/useAudioLibrary';
import AudioMessageBubble from './AudioMessageBubble';
import api from '../../../services/api';

/**
 * Text-to-Speech Panel Component - Chat-like Interface
 * API-driven chat-style UI for generating voiceovers
 */
const TextToSpeechPanel = ({ onAudioGenerated }) => {
  const { showToast } = useToast();
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  // API-driven TTS configuration
  const [ttsConfig, setTtsConfig] = useState(null);
  const [loadingConfig, setLoadingConfig] = useState(true);

  // State
  const [text, setText] = useState('');
  const [selectedModel, setSelectedModel] = useState(null);
  const [selectedVoice, setSelectedVoice] = useState(null);
  const [selectedLanguage, setSelectedLanguage] = useState('en'); // Default to English
  const [speed, setSpeed] = useState(1.0);
  const [audioMessages, setAudioMessages] = useState([]);
  const [showVoiceSelector, setShowVoiceSelector] = useState(false);

  // Custom hooks
  const { generating, generateAudio } = useAudioGeneration();
  const { saveToLibrary, saving } = useAudioLibrary();

  // Fetch TTS configuration from API
  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const response = await api.get('/audio-studio/config');
        const config = response.data;
        setTtsConfig(config);

        // Set defaults from API
        if (config.default_model) {
          setSelectedModel(config.default_model);
          const defaultModelConfig = config.models[config.default_model];
          if (defaultModelConfig?.default_voice) {
            setSelectedVoice(defaultModelConfig.default_voice);
          }
        }
      } catch (error) {
        console.error('Failed to fetch TTS config:', error);
        showToast('Failed to load audio configuration', 'error');
      } finally {
        setLoadingConfig(false);
      }
    };
    fetchConfig();
  }, []);

  // Get available voices for current model
  const allVoices = selectedModel && ttsConfig
    ? (ttsConfig.models[selectedModel]?.voices || []).map(voiceId => ({
        id: voiceId,
        name: voiceId,
        description: `${ttsConfig.models[selectedModel]?.name} voice`,
        category: 'default'
      }))
    : [];

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [audioMessages]);

  // Handle model change
  const handleModelChange = (modelKey) => {
    setSelectedModel(modelKey);
    const modelConfig = ttsConfig.models[modelKey];
    if (modelConfig?.default_voice) {
      setSelectedVoice(modelConfig.default_voice);
    }
    showToast(`Model changed to ${modelConfig?.name}`, 'success');
  };

  // Handle voice selection
  const handleVoiceSelect = (voiceId) => {
    setSelectedVoice(voiceId);
    setShowVoiceSelector(false);
    showToast(`Voice changed to ${voiceId}`, 'success');
  };

  // Handle audio generation
  const handleGenerate = async () => {
    if (!text.trim()) {
      showToast('Please enter some text to generate audio', 'error');
      return;
    }

    if (text.length > 5000) {
      showToast('Text is too long. Maximum 5000 characters allowed.', 'error');
      return;
    }

    const userText = text.trim();
    setText(''); // Clear input immediately

    try {
      const result = await generateAudio({
        text: userText,
        model: selectedModel,
        voice: selectedVoice,
        language: selectedLanguage,
        speed: speed
      });

      if (result.success) {
        const newMessage = {
          id: Date.now(),
          text: userText,
          audioUrl: result.audio_url,
          duration: result.audio_info?.duration || 0,
          voice: selectedVoice,
          voiceName: selectedVoice,
          model: selectedModel,
          speed: speed,
          timestamp: new Date().toISOString()
        };

        setAudioMessages(prev => [...prev, newMessage]);
        showToast('Audio generated successfully!', 'success');

        // Notify parent to refresh library
        if (onAudioGenerated) {
          onAudioGenerated();
        }
      }
    } catch (error) {
      showToast(error.message || 'Failed to generate audio', 'error');
      setText(userText); // Restore text on error
    }
  };

  // Handle save to library
  const handleSaveToLibrary = async (message) => {
    try {
      await saveToLibrary({
        audioUrl: message.audioUrl,
        text: message.text,
        voice: message.voice,
        metadata: {
          model: message.model,
          speed: message.speed,
          duration: message.duration
        }
      });
      showToast('Saved to Audio Library!', 'success');
      if (onAudioGenerated) {
        onAudioGenerated();
      }
    } catch (error) {
      showToast('Failed to save to library', 'error');
    }
  };

  // Handle Enter key press
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleGenerate();
    }
  };

  // Get selected voice info
  const selectedVoiceInfo = allVoices.find(v => v.id === selectedVoice);

  return (
    <div className="flex flex-col h-full bg-gray-50 overflow-hidden">
      {/* Header with Info */}
      <div className="bg-white border-b border-gray-200 px-6 py-4 flex-shrink-0">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">💬 Text-to-Speech Chat</h2>
            <p className="text-sm text-gray-600">Type your text and generate audio instantly</p>
          </div>
          <button
            onClick={() => window.open('/audio-studio/voice-preview', '_blank')}
            className="px-4 py-2 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 transition-colors text-sm font-medium"
          >
            🎭 Browse All Voices
          </button>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 min-h-0 overflow-y-auto px-6 py-4 space-y-4">
        {audioMessages.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <div className="text-6xl mb-4">🎙️</div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Start Creating Voiceovers
              </h3>
              <p className="text-gray-600 max-w-md">
                Type your text below, select a voice and language, then press Enter or click Generate to create professional voiceovers.
              </p>
            </div>
          </div>
        ) : (
          <>
            {audioMessages.map((message) => (
              <AudioMessageBubble
                key={message.id}
                message={message}
                onSaveToLibrary={() => handleSaveToLibrary(message)}
                saving={saving}
              />
            ))}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input Bar - Fixed at Bottom */}
      <div className="bg-white border-t border-gray-200 px-6 py-4 flex-shrink-0 relative">
        {/* Voice Selector Dropdown - Positioned as overlay */}
        {showVoiceSelector && (
          <div className="absolute bottom-full left-6 right-6 mb-2 p-4 bg-white rounded-lg border border-gray-200 shadow-lg max-h-80 overflow-y-auto z-10">
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-semibold text-gray-900">Select Voice</h4>
              <button
                onClick={() => setShowVoiceSelector(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
            <div className="grid grid-cols-2 gap-2">
              {allVoices.map((voice) => (
                <button
                  key={voice.id}
                  onClick={() => handleVoiceSelect(voice.id)}
                  className={`
                    p-3 rounded-lg text-left transition-all
                    ${selectedVoice === voice.id
                      ? 'bg-blue-100 border-2 border-blue-500'
                      : 'bg-white border border-gray-200 hover:border-blue-300'
                    }
                  `}
                >
                  <div className="flex items-center gap-2">
                    <span className="text-xl">
                      {voice.category === 'male' ? '👨' : voice.category === 'female' ? '👩' : '🎤'}
                    </span>
                    <div>
                      <div className="font-medium text-sm">{voice.name}</div>
                      <div className="text-xs text-gray-600">{voice.description}</div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Controls Row */}
        <div className="flex flex-wrap items-center gap-3 mb-3">
          {loadingConfig ? (
            <div className="text-sm text-gray-600">Loading configuration...</div>
          ) : !ttsConfig ? (
            <div className="text-sm text-red-600">Failed to load configuration</div>
          ) : (
            <>
              {/* Model Selector */}
              <div className="flex items-center gap-2">
                <label className="text-sm font-medium text-gray-700 whitespace-nowrap">
                  Model:
                  {ttsConfig.gpu_enabled && (
                    <span className="ml-2 text-xs text-green-600 font-semibold">🎮 GPU</span>
                  )}
                </label>
                <select
                  value={selectedModel || ''}
                  onChange={(e) => handleModelChange(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
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
            </>
          )}

          {!loadingConfig && ttsConfig && (
            <>
              {/* Voice Selector Button */}
              <button
                onClick={() => setShowVoiceSelector(!showVoiceSelector)}
                className="flex items-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors text-sm font-medium whitespace-nowrap"
                disabled={!selectedModel}
              >
                <span>🎤</span>
                <span className="max-w-[150px] truncate">{selectedVoice || 'Select Voice'}</span>
                <span className="text-xs text-gray-600">▼</span>
              </button>

              {/* Language Selector - Show only for multi-lingual models */}
              {selectedModel && ttsConfig.models[selectedModel]?.supported_languages?.length > 0 && (
                <div className="flex items-center gap-2">
                  <label className="text-sm font-medium text-gray-700 whitespace-nowrap">
                    🌍 Language:
                  </label>
                  <select
                    value={selectedLanguage}
                    onChange={(e) => setSelectedLanguage(e.target.value)}
                    className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                  >
                    {ttsConfig.models[selectedModel].supported_languages.map((langCode, index) => (
                      <option key={langCode} value={langCode}>
                        {ttsConfig.models[selectedModel].supported_language_names[index]}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {/* Speed Control */}
              <div className="flex items-center gap-2">
                <label className="text-sm font-medium text-gray-700 whitespace-nowrap">Speed:</label>
                <input
                  type="range"
                  min="0.5"
                  max="2.0"
                  step="0.1"
                  value={speed}
                  onChange={(e) => setSpeed(parseFloat(e.target.value))}
                  className="w-20"
                />
                <span className="text-sm text-gray-600 w-12 whitespace-nowrap">{speed}x</span>
              </div>
            </>
          )}

          {/* Character Count */}
          <div className="ml-auto text-sm text-gray-600 whitespace-nowrap">
            {text.length} / 5000
          </div>
        </div>

        {/* Text Input Row */}
        <div className="flex items-end gap-3">
          <div className="flex-1 relative min-w-0">
            <textarea
              ref={textareaRef}
              value={text}
              onChange={(e) => setText(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your text here... (Press Enter to generate, Shift+Enter for new line)"
              className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none break-words"
              rows={2}
              maxLength={5000}
              style={{ wordBreak: 'break-word', overflowWrap: 'break-word' }}
            />
            {text.length > 0 && (
              <button
                onClick={() => setText('')}
                className="absolute right-3 top-3 text-gray-400 hover:text-gray-600"
                title="Clear text"
              >
                ✕
              </button>
            )}
          </div>

          <Button
            onClick={handleGenerate}
            disabled={generating || !text.trim()}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 whitespace-nowrap"
          >
            {generating ? (
              <>
                <span className="animate-spin">⏳</span>
                <span>Generating...</span>
              </>
            ) : (
              <>
                <span>🎙️</span>
                <span>Generate</span>
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default TextToSpeechPanel;

