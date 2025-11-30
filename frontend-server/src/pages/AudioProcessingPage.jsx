import React, { useState, useEffect } from 'react';
import { Card, Button } from '../components/common';
import { VoiceConfig, AudioGallery } from '../components/VoiceLLM';
import { voiceService } from '../services';
import { useToast } from '../hooks/useToast';

/**
 * Audio Processing Page - Voice Configuration and Audio Gallery
 */
const AudioProcessingPage = () => {
  const [activeTab, setActiveTab] = useState('voice'); // voice, gallery
  const [voiceConfig, setVoiceConfig] = useState(null);
  const [loading, setLoading] = useState(false);
  const { showToast } = useToast();

  // Load data on mount
  useEffect(() => {
    if (activeTab === 'voice') {
      loadVoiceConfig();
    }
  }, [activeTab]);

  const loadVoiceConfig = async () => {
    setLoading(true);
    try {
      const data = await voiceService.getConfig();
      setVoiceConfig(data);
    } catch (error) {
      showToast('Failed to load voice configuration', 'error');
      console.error('Error loading voice config:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadAudioGalleryData = async (page, statusFilter) => {
    try {
      const response = await voiceService.getAudioList(page, statusFilter, 20);
      console.log('Audio Gallery Response:', response);
      // Backend returns { status: 'success', data: { audio_files: [...], pagination: {...} } }
      // voiceService.getAudioList already returns response.data, so we need response.data
      if (response.status === 'success' && response.data) {
        return response.data;
      }
      return { audio_files: [], pagination: {} };
    } catch (error) {
      showToast('Failed to load audio files', 'error');
      console.error('Error loading audio files:', error);
      throw error;
    }
  };

  const loadAudioStats = async () => {
    try {
      const response = await voiceService.getAudioStats();
      console.log('Audio Stats Response:', response);
      // Backend returns { status: 'success', data: { total, pending, generated, coverage_percentage } }
      if (response.status === 'success' && response.data) {
        return response.data;
      }
      return { total: 0, pending: 0, generated: 0 };
    } catch (error) {
      showToast('Failed to load audio stats', 'error');
      console.error('Error loading audio stats:', error);
      throw error;
    }
  };

  const handleSaveVoiceConfig = async (configData) => {
    setLoading(true);
    try {
      await voiceService.updateConfig(configData);
      showToast('Voice configuration saved successfully', 'success');
      loadVoiceConfig();
    } catch (error) {
      showToast('Failed to save voice configuration', 'error');
      console.error('Error saving voice config:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleVoicePreview = async (voiceId, text) => {
    try {
      const audioUrl = await voiceService.preview(voiceId, text);
      return audioUrl;
    } catch (error) {
      showToast('Failed to preview voice', 'error');
      throw error;
    }
  };

  const tabs = [
    { id: 'voice', label: 'Voice Configuration', icon: '🎙️' },
    { id: 'gallery', label: 'Audio Gallery', icon: '🎵' },
  ];

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Audio Processing</h1>
          <p className="text-gray-600 mt-2">
            Configure voice settings and manage audio files for news automation
          </p>
        </div>

        {/* Tabs */}
        <div className="mb-6 border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`
                  py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2
                  ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }
                `}
              >
                <span>{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Content */}
        <div>
          {activeTab === 'voice' && (
            <div>
              {/* Voice Configuration */}
              <div className="mb-6">
                <h2 className="text-xl font-semibold text-gray-900">Voice Settings</h2>
                <p className="text-sm text-gray-600 mt-1">
                  Configure voice settings for audio generation
                </p>
              </div>

              {voiceConfig ? (
                <VoiceConfig
                  config={voiceConfig}
                  onSave={handleSaveVoiceConfig}
                  onPreview={handleVoicePreview}
                  loading={loading}
                />
              ) : (
                <Card>
                  <div className="text-center py-8">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                    <p className="text-gray-600 mt-4">Loading voice configuration...</p>
                  </div>
                </Card>
              )}
            </div>
          )}

          {activeTab === 'gallery' && (
            <div>
              {/* Audio Gallery */}
              <div className="mb-6">
                <h2 className="text-xl font-semibold text-gray-900">Audio Gallery</h2>
                <p className="text-sm text-gray-600 mt-1">
                  Browse and play generated audio files
                </p>
              </div>

              <AudioGallery
                onLoadData={loadAudioGalleryData}
                onLoadStats={loadAudioStats}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AudioProcessingPage;

