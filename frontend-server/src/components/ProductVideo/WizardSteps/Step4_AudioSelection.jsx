import React, { useState, useEffect, useImperativeHandle, forwardRef } from 'react';
import { Button } from '../../common';
import { productService } from '../../../services';
import { useToast } from '../../../hooks/useToast';
import api from '../../../services/api';
import {
  AUDIO_MODELS,
  LANGUAGES,
  getAvailableVoices,
  detectLanguage,
  getDefaultVoice,
  getDefaultModel
} from '../../../constants/audioModels';

/**
 * Step 4: Audio Selection
 */

const Step4_AudioSelection = forwardRef(({ formData, onComplete }, ref) => {
  // Auto-detect language from product description
  const detectedLanguage = detectLanguage(formData.description || formData.ai_summary?.full_text || '');

  const [audioType, setAudioType] = useState(formData.audio?.type || 'generated');
  const [selectedModel, setSelectedModel] = useState(formData.audio?.model || formData.audio_config?.model || 'kokoro-82m');
  const [selectedLanguage, setSelectedLanguage] = useState(formData.audio?.language || formData.audio_config?.language || detectedLanguage);
  const [selectedVoice, setSelectedVoice] = useState(formData.audio?.voice || formData.audio_config?.voice || 'am_adam');
  const [audioUrl, setAudioUrl] = useState(formData.audio?.url || formData.audio_url || null);
  const [generating, setGenerating] = useState(false);
  const [previewingVoice, setPreviewingVoice] = useState(null);
  const [previewAudioUrl, setPreviewAudioUrl] = useState(null);
  const [sectionSpeeds, setSectionSpeeds] = useState(formData.audio?.sectionPitches || {}); // Keep backend key name for compatibility
  const [playingProductAudio, setPlayingProductAudio] = useState(false);
  const [productAudioRef, setProductAudioRef] = useState(null); // Reference to playing audio element
  const [sections, setSections] = useState([]); // Sections from backend
  const [loadingSections, setLoadingSections] = useState(false);
  const [loadingExistingAudio, setLoadingExistingAudio] = useState(false);
  const [showAdvancedOptions, setShowAdvancedOptions] = useState(false); // Toggle for advanced speed controls
  const { showToast } = useToast();

  // Load sections from backend on component mount
  useEffect(() => {
    const loadSections = async () => {
      if (!formData.product_id) return;

      setLoadingSections(true);
      try {
        const response = await productService.getAudioSections(formData.product_id);
        if (response.data.status === 'success') {
          setSections(response.data.sections);
          console.log('✅ Loaded sections from backend:', response.data.sections);
        }
      } catch (error) {
        console.error('Error loading sections:', error);
        // Fallback to empty sections - component will still work
        setSections([]);
      } finally {
        setLoadingSections(false);
      }
    };

    loadSections();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [formData.product_id]);

  // Load existing audio on component mount
  useEffect(() => {
    const loadExistingAudio = async () => {
      // If formData already has audio_url from the product, use it directly
      if (formData.audio_url && formData.product_id) {
        console.log('✅ Found existing audio URL in formData:', formData.audio_url);
        setAudioUrl(formData.audio_url);
        return;
      }

      // Otherwise, try to fetch the product to get the latest audio_url
      if (!audioUrl && formData.product_id) {
        setLoadingExistingAudio(true);
        try {
          const response = await productService.getProduct(formData.product_id);
          if (response.data.status === 'success' && response.data.product.audio_url) {
            const existingAudioUrl = response.data.product.audio_url;
            setAudioUrl(existingAudioUrl);
            console.log('✅ Loaded existing audio from API:', existingAudioUrl);
          }
        } catch (error) {
          console.error('Error loading existing audio:', error);
        } finally {
          setLoadingExistingAudio(false);
        }
      }
    };

    loadExistingAudio();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Only run once on mount

  // Check if voice configuration has changed (requires regeneration)
  const hasVoiceConfigChanged = () => {
    if (!formData.audio_config) return false;

    return (
      formData.audio_config.voice !== selectedVoice ||
      formData.audio_config.model !== selectedModel ||
      formData.audio_config.language !== selectedLanguage
    );
  };

  // Check if audio needs to be generated
  const needsGeneration = !audioUrl || hasVoiceConfigChanged();

  // Handle language change - update model accordingly
  useEffect(() => {
    const defaultModel = getDefaultModel(selectedLanguage);
    const defaultVoice = getDefaultVoice(selectedLanguage);

    if (selectedModel !== defaultModel) {
      setSelectedModel(defaultModel);
      setSelectedVoice(defaultVoice);
    }
  }, [selectedLanguage, selectedModel]);

  // Preview voice with sample text (lightweight)
  const handlePreviewVoice = async (voiceId) => {
    try {
      setPreviewingVoice(voiceId);

      // Use sample text for preview (lightweight and fast)
      const previewText = selectedLanguage === 'en'
        ? "Hello! This is a preview of how this voice sounds. Perfect for your product videos!"
        : "नमस्ते! यह आवाज़ का पूर्वावलोकन है।";

      console.log('🎵 Previewing voice:', voiceId);

      const response = await api.post('/audio/preview', {
        text: previewText,
        model: selectedModel,
        voice: voiceId,
        language: selectedLanguage
      });

      if (response.data.audioUrl) {
        console.log('✅ Preview audio URL received:', response.data.audioUrl);

        // Fetch the audio file with authentication
        const token = localStorage.getItem('auth_token');
        const audioResponse = await fetch(response.data.audioUrl, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (!audioResponse.ok) {
          throw new Error(`Failed to fetch audio: ${audioResponse.status}`);
        }

        // Create blob URL and play
        const blob = await audioResponse.blob();
        const blobUrl = URL.createObjectURL(blob);
        setPreviewAudioUrl(blobUrl);

        // Auto-play preview
        const audio = new Audio(blobUrl);
        audio.play().then(() => {
          console.log('✅ Audio playback started');
        }).catch(err => {
          console.error('❌ Failed to play audio:', err);
          showToast('Failed to play audio preview', 'error');
        });

        // Clean up blob URL after audio ends
        audio.onended = () => {
          URL.revokeObjectURL(blobUrl);
        };
      }
    } catch (error) {
      console.error('Error previewing voice:', error);
      showToast('Failed to preview voice', 'error');
    } finally {
      setPreviewingVoice(null);
    }
  };

  // Play the generated product audio
  const handlePlayProductAudio = async () => {
    if (!audioUrl) {
      showToast('No audio generated yet', 'error');
      return;
    }

    try {
      setPlayingProductAudio(true);
      console.log('🔊 Playing product audio:', audioUrl);

      // Fetch the audio file with authentication
      const token = localStorage.getItem('auth_token');
      const audioResponse = await fetch(audioUrl, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!audioResponse.ok) {
        throw new Error(`Failed to fetch audio: ${audioResponse.status}`);
      }

      // Create blob URL and play
      const blob = await audioResponse.blob();
      const blobUrl = URL.createObjectURL(blob);

      // Auto-play product audio
      const audio = new Audio(blobUrl);
      setProductAudioRef(audio); // Store reference for stop functionality

      audio.play().then(() => {
        console.log('✅ Product audio playback started');
        showToast('Playing product audio...', 'info');
      }).catch(err => {
        console.error('❌ Failed to play audio:', err);
        showToast('Failed to play audio', 'error');
        setPlayingProductAudio(false);
        setProductAudioRef(null);
      });

      // Clean up blob URL after audio ends
      audio.onended = () => {
        URL.revokeObjectURL(blobUrl);
        setPlayingProductAudio(false);
        setProductAudioRef(null);
      };
    } catch (error) {
      console.error('Error playing product audio:', error);
      showToast('Failed to play product audio', 'error');
      setPlayingProductAudio(false);
      setProductAudioRef(null);
    }
  };

  // Stop the playing product audio
  const handleStopProductAudio = () => {
    if (productAudioRef) {
      productAudioRef.pause();
      productAudioRef.currentTime = 0;
      setPlayingProductAudio(false);
      setProductAudioRef(null);
      showToast('Audio stopped', 'info');
    }
  };

  const handleGenerateAudio = async () => {
    if (!formData.product_id) {
      showToast('⚠️ Product ID not found. Please save the product first.', 'error', 5000);
      return;
    }

    // Validate voice selection
    if (!selectedVoice) {
      showToast('⚠️ Please select a voice before generating audio', 'error', 5000);
      return;
    }

    try {
      setGenerating(true);

      // Merge smart defaults with user overrides
      const finalSpeeds = {};
      sections.forEach(section => {
        // Use user override if exists, otherwise use smart default from backend
        finalSpeeds[section.title] = sectionSpeeds[section.title] !== undefined
          ? sectionSpeeds[section.title]
          : section.defaultSpeed;
      });

      const response = await productService.generateAudio(formData.product_id, {
        voice: selectedVoice,
        model: selectedModel,
        language: selectedLanguage,
        sectionPitches: finalSpeeds  // Backend expects 'sectionPitches' key
      });

      if (response.data.status === 'success') {
        // Backend returns section_audio_urls array - use first one or combined URL
        const generatedAudioUrl = response.data.audio_url || response.data.section_audio_urls?.[0];

        if (generatedAudioUrl) {
          setAudioUrl(generatedAudioUrl);
          showToast('✅ Audio generated successfully! Click "Play Product Audio" to listen.', 'success');

          // Reload product data to get updated sections with audio_config.duration
          try {
            const productResponse = await productService.getProduct(formData.product_id);
            if (productResponse.data?.product?.ai_summary?.sections) {
              const updatedSections = productResponse.data.product.ai_summary.sections;
              console.log('🔄 Reloaded sections with updated durations:', updatedSections);

              // Update sections in parent formData
              if (onFormDataChange) {
                onFormDataChange({
                  ai_summary: { sections: updatedSections }
                });
              }
            }
          } catch (error) {
            console.error('⚠️ Failed to reload product data:', error);
            // Non-critical error, don't show to user
          }
        } else {
          showToast('⚠️ Audio generated but no URL returned', 'warning', 5000);
        }
      } else {
        throw new Error(response.data.message || 'Audio generation failed');
      }
    } catch (error) {
      console.error('❌ Error generating audio:', error);

      // Provide more specific error messages
      let errorMessage = 'Failed to generate audio. Please try again.';

      if (error.response) {
        const status = error.response.status;
        const data = error.response.data;

        if (status === 401) {
          errorMessage = '🔒 Session expired. Please log in again.';
        } else if (status === 404) {
          errorMessage = '❌ Product not found. Please refresh and try again.';
        } else if (status === 500) {
          errorMessage = '⚠️ Server error. Please try again later.';
        } else if (data?.message) {
          errorMessage = `❌ ${data.message}`;
        }
      } else if (error.request) {
        errorMessage = '🌐 Network error. Please check your connection.';
      } else if (error.message) {
        errorMessage = `❌ ${error.message}`;
      }

      showToast(errorMessage, 'error', 6000);
    } finally {
      setGenerating(false);
    }
  };

  // Expose handleNext to parent via ref
  useImperativeHandle(ref, () => ({
    handleNext
  }));

  const handleNext = () => {
    // Validate audio is generated or uploaded
    if (!audioUrl) {
      showToast('⚠️ Please generate or upload audio before proceeding', 'error', 5000);
      return;
    }

    // Validate voice selection for generated audio
    if (audioType === 'generated' && !selectedVoice) {
      showToast('⚠️ Please select a voice for audio generation', 'error', 5000);
      return;
    }

    onComplete({
      audio: {
        type: audioType,
        url: audioUrl,
        voice: selectedVoice,
        model: selectedModel,
        language: selectedLanguage,
        sectionPitches: sectionSpeeds  // Backend expects 'sectionPitches' key
      },
      audio_url: audioUrl,  // Also pass audio_url at top level for video generation
      audio_config: {
        voice: selectedVoice,
        model: selectedModel,
        language: selectedLanguage,
        sectionPitches: sectionSpeeds
      }
    });
  };

  // No longer needed - sections come from backend with smart defaults already applied

  const handleSpeedChange = (sectionTitle, speed) => {
    setSectionSpeeds(prev => ({
      ...prev,
      [sectionTitle]: parseFloat(speed)
    }));
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-xl font-semibold text-gray-900 mb-2">🎵 Audio Configuration</h3>
        <p className="text-gray-600">Configure voice settings for your product video</p>
      </div>

      {/* Loading Existing Audio Indicator */}
      {loadingExistingAudio && (
        <div className="bg-blue-50 border-2 border-blue-300 rounded-lg p-4">
          <div className="flex items-center gap-3">
            <div className="animate-spin text-2xl">⏳</div>
            <div>
              <h4 className="font-semibold text-blue-900">Loading Existing Audio...</h4>
              <p className="text-sm text-blue-700">Fetching previously generated audio</p>
            </div>
          </div>
        </div>
      )}

      {/* Audio Type Selection */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <button
          onClick={() => setAudioType('generated')}
          className={`p-4 border-2 rounded-lg text-left transition-all ${
            audioType === 'generated'
              ? 'border-indigo-500 bg-indigo-50'
              : 'border-gray-300 hover:border-indigo-300'
          }`}
        >
          <div className="text-3xl mb-2">🤖</div>
          <h4 className="font-semibold text-gray-900 mb-1">Generate from AI Summary</h4>
          <p className="text-sm text-gray-600">Use text-to-speech to create voiceover</p>
        </button>

        <button
          onClick={() => setAudioType('uploaded')}
          className={`p-4 border-2 rounded-lg text-left transition-all ${
            audioType === 'uploaded'
              ? 'border-indigo-500 bg-indigo-50'
              : 'border-gray-300 hover:border-indigo-300'
          }`}
        >
          <div className="text-3xl mb-2">📤</div>
          <h4 className="font-semibold text-gray-900 mb-1">Upload Custom Audio</h4>
          <p className="text-sm text-gray-600">Use your own audio file</p>
        </button>
      </div>

      {/* Generated Audio Options */}
      {audioType === 'generated' && (
        <div className="space-y-6">
          {/* Auto-detected Language Info */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <div className="flex items-center gap-2 text-sm text-blue-800">
              <span className="text-lg">🌍</span>
              <span>
                <strong>Language Auto-detected:</strong> {LANGUAGES.find(l => l.id === selectedLanguage)?.name || 'English'}
              </span>
            </div>
          </div>

          {/* Step 1: Voice/Speaker Selection with Preview */}
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <label className="block text-sm font-semibold text-gray-900 mb-3">
              1️⃣ Select Speaker & Preview
            </label>
            <div className="space-y-4">
              {Object.entries(AUDIO_MODELS[selectedModel]?.voices || {}).map(([category, voiceList]) => (
                <div key={category}>
                  <h6 className="text-xs font-semibold text-gray-500 uppercase mb-2">
                    {category === 'male' ? '👨 Male Voices' : category === 'female' ? '👩 Female Voices' : '🎤 Voices'}
                  </h6>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {voiceList.map((voice) => (
                      <div
                        key={voice.id}
                        className={`p-3 border-2 rounded-lg transition-all ${
                          selectedVoice === voice.id
                            ? 'border-indigo-500 bg-indigo-50'
                            : 'border-gray-300'
                        }`}
                      >
                        <div className="flex items-start justify-between">
                          <button
                            onClick={() => setSelectedVoice(voice.id)}
                            className="flex-1 text-left"
                          >
                            <h5 className="font-medium text-gray-900">{voice.name}</h5>
                            <p className="text-xs text-gray-600">{voice.description}</p>
                          </button>
                          <button
                            onClick={() => handlePreviewVoice(voice.id)}
                            disabled={previewingVoice === voice.id}
                            className="ml-2 p-2 text-indigo-600 hover:bg-indigo-100 rounded-lg transition-colors disabled:opacity-50"
                            title="Preview voice"
                          >
                            {previewingVoice === voice.id ? (
                              <span className="animate-spin">⏳</span>
                            ) : (
                              <span>▶️</span>
                            )}
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>



          {/* Step 2: Section-based Speed Configuration (Collapsible Advanced Options) */}
          {sections.length > 0 && (
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <label className="block text-sm font-semibold text-gray-900 mb-3">
                2️⃣ Customize Narration Speed (Optional)
              </label>
              {/* Collapsible Header */}
              <button
                onClick={() => setShowAdvancedOptions(!showAdvancedOptions)}
                className="w-full flex items-center justify-between text-left hover:bg-gray-50 rounded-lg p-2 transition-colors"
              >
                <div className="flex items-center gap-2">
                  <span className="text-lg">{showAdvancedOptions ? '🔽' : '▶️'}</span>
                  <span className="text-sm font-semibold text-gray-900">
                    Advanced: Customize Narration Speed per Section
                  </span>
                </div>
                <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                  {showAdvancedOptions ? 'Hide' : 'Show'}
                </span>
              </button>

              {/* Smart Defaults Info (Always Visible) - Dynamic based on actual sections */}
              <div className="mt-3 bg-gradient-to-r from-purple-50 to-indigo-50 border border-purple-200 rounded-lg p-3">
                <p className="text-xs font-semibold text-purple-900 mb-2">
                  ✨ Smart Speed Defaults Applied:
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-x-4 gap-y-1 text-xs text-gray-700">
                  {sections.map((section, index) => {
                    // Get emoji based on section title or index
                    const getSectionEmoji = (title, idx) => {
                      const titleLower = title.toLowerCase();
                      if (titleLower.includes('hook') || titleLower.includes('opening')) return '⚡';
                      if (titleLower.includes('introduction') || titleLower.includes('intro')) return '👋';
                      if (titleLower.includes('feature') || titleLower.includes('benefit')) return '📋';
                      if (titleLower.includes('proof') || titleLower.includes('trust') || titleLower.includes('testimonial')) return '✅';
                      if (titleLower.includes('action') || titleLower.includes('cta') || titleLower.includes('call')) return '🎯';
                      if (titleLower.includes('conclusion') || titleLower.includes('closing')) return '🎯';
                      // Default emojis based on position
                      if (idx === 0) return '⚡';
                      if (idx === sections.length - 1) return '🎯';
                      return '📝';
                    };

                    return (
                      <div key={index} className="flex items-center gap-2">
                        <span className="font-medium">
                          {getSectionEmoji(section.title, index)} {section.title}:
                        </span>
                        <span className="text-gray-600">{section.defaultSpeed}x</span>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Expandable Speed Controls */}
              {showAdvancedOptions && (
                <div className="mt-4 space-y-3 animate-fadeIn">
                  <p className="text-xs text-gray-600 mb-3">
                    💡 Adjust the narration speed for each section below. Smart defaults create a natural narrative arc.
                  </p>

                  {sections.map((section, index) => {
                    const currentSpeed = sectionSpeeds[section.title] !== undefined
                      ? sectionSpeeds[section.title]
                      : section.defaultSpeed;

                    return (
                      <div key={index} className="bg-gray-50 rounded-lg p-3 border border-gray-200">
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex-1">
                            <div className="text-sm font-semibold text-gray-900">{section.title}</div>
                            <div className="text-xs text-gray-600 mt-1">{section.description}</div>
                          </div>
                          <div className={`text-sm font-bold px-2 py-1 rounded ${
                            currentSpeed !== section.defaultSpeed
                              ? 'bg-indigo-100 text-indigo-700'
                              : 'bg-gray-100 text-gray-700'
                          }`}>
                            {currentSpeed.toFixed(2)}x
                          </div>
                        </div>

                        <div className="flex items-center gap-2">
                          <span className="text-xs text-gray-500 w-12">Slower</span>
                          <input
                            type="range"
                            min="0.85"
                            max="1.15"
                            step="0.05"
                            value={currentSpeed}
                            onChange={(e) => handleSpeedChange(section.title, e.target.value)}
                            className="flex-1"
                          />
                          <span className="text-xs text-gray-500 w-12 text-right">Faster</span>
                          {currentSpeed !== section.defaultSpeed && (
                            <button
                              onClick={() => {
                                const newSpeeds = { ...sectionSpeeds };
                                delete newSpeeds[section.title];
                                setSectionSpeeds(newSpeeds);
                              }}
                              className="text-xs text-indigo-600 hover:text-indigo-800 font-medium ml-2"
                              title="Reset to smart default"
                            >
                              Reset
                            </button>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {/* Voice Configuration Change Warning */}
          {hasVoiceConfigChanged() && audioUrl && (
            <div className="bg-yellow-50 border-2 border-yellow-400 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <span className="text-2xl">⚠️</span>
                <div className="flex-1">
                  <h4 className="font-semibold text-yellow-900 mb-1">Voice Configuration Changed</h4>
                  <p className="text-sm text-yellow-800 mb-3">
                    You've changed the voice settings. The audio needs to be regenerated with the new voice.
                  </p>
                  <div className="text-xs text-yellow-700">
                    <div>Previous: {formData.audio_config?.voice} ({formData.audio_config?.model})</div>
                    <div>New: {selectedVoice} ({selectedModel})</div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Generate/Regenerate and Play Audio Buttons - Side by Side */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {/* Regenerate Audio Button */}
            <Button
              variant="primary"
              onClick={handleGenerateAudio}
              loading={generating}
              disabled={generating}
              className="w-full"
            >
              {generating ? 'Generating Audio...' : needsGeneration ? '🎙️ Generate Audio' : '🔄 Regenerate Audio'}
            </Button>

            {/* Play/Stop Product Audio Button */}
            {playingProductAudio ? (
              <Button
                variant="danger"
                onClick={handleStopProductAudio}
                className="w-full"
              >
                ⏹️ Stop Audio
              </Button>
            ) : (
              <Button
                variant="secondary"
                onClick={handlePlayProductAudio}
                disabled={!audioUrl || hasVoiceConfigChanged()}
                className="w-full"
                title={!audioUrl ? 'Generate audio first to enable playback' : hasVoiceConfigChanged() ? 'Regenerate audio with new settings to enable playback' : 'Play generated audio'}
              >
                ▶️ Play Audio
              </Button>
            )}
          </div>

          {/* Audio Preview - Success Message - Below Play Button */}
          {audioUrl && !hasVoiceConfigChanged() && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-3">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-lg">✅</span>
                <h4 className="text-sm font-semibold text-green-900">Audio Generated Successfully!</h4>
              </div>

              <div className="flex items-center gap-3 text-xs text-gray-700">
                <div className="flex items-center gap-1">
                  <span>🎤</span>
                  <span className="font-medium">{AUDIO_MODELS[selectedModel]?.name}</span>
                </div>
                <div className="flex items-center gap-1">
                  <span>🗣️</span>
                  <span className="font-medium">
                    {getAvailableVoices(selectedModel).find(v => v.id === selectedVoice)?.name || selectedVoice}
                  </span>
                </div>
                <div className="flex items-center gap-1">
                  <span>{LANGUAGES.find(l => l.id === selectedLanguage)?.flag}</span>
                  <span className="font-medium">{LANGUAGES.find(l => l.id === selectedLanguage)?.name}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Upload Audio Option */}
      {audioType === 'uploaded' && (
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
          <div className="text-6xl mb-4">🎵</div>
          <h4 className="text-lg font-semibold text-gray-900 mb-2">Upload Audio File</h4>
          <p className="text-gray-600 mb-4">MP3, WAV, or M4A format</p>
          <Button variant="primary">Browse Files</Button>
          <p className="text-sm text-gray-500 mt-4">Coming soon...</p>
        </div>
      )}
    </div>
  );
});

Step4_AudioSelection.displayName = 'Step4_AudioSelection';

export default Step4_AudioSelection;

