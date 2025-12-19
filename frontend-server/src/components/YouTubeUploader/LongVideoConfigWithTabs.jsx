import React, { useState } from 'react';
import { Card } from '../common';
import LongVideoConfig from './LongVideoConfig';
import YouTubeConfigTab from './YouTubeConfigTab';

/**
 * Long Video Configuration with Platform Tabs
 * Allows configuration for different platforms (YouTube, etc.)
 */
const LongVideoConfigWithTabs = ({ initialConfig, onSave, onCancel, loading }) => {
  const [activeTab, setActiveTab] = useState('general');
  const [config, setConfig] = useState(initialConfig || {
    categories: [],
    country: '',
    language: '',
    videoCount: 20,
    title: '',
    frequency: 'none',
    backgroundAudioId: null,
    platforms: {
      youtube: {
        enabled: true,
        title: '',
        description: '',
        tags: [],
      }
    }
  });

  const tabs = [
    { id: 'general', label: 'General Settings', icon: '⚙️' },
    { id: 'youtube', label: 'YouTube', icon: '📺' },
  ];

  const handleGeneralConfigChange = (generalConfig) => {
    setConfig(prev => ({
      ...prev,
      ...generalConfig,
    }));
  };

  const handleYouTubeConfigChange = (youtubeConfig) => {
    setConfig(prev => ({
      ...prev,
      platforms: {
        ...prev.platforms,
        youtube: youtubeConfig,
      }
    }));
  };

  const handleSave = () => {
    onSave(config);
  };

  return (
    <div className="space-y-4">
      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="flex gap-2">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-3 font-medium text-sm transition-colors border-b-2 ${
                activeTab === tab.id
                  ? 'border-red-600 text-red-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="mt-4">
        {activeTab === 'general' && (
          <LongVideoConfig
            initialConfig={config}
            onSave={handleSave}
            onCancel={onCancel}
            loading={loading}
            onChange={handleGeneralConfigChange}
            hideYouTubeMetadata={true}
          />
        )}

        {activeTab === 'youtube' && (
          <YouTubeConfigTab
            config={config.platforms?.youtube || {}}
            onChange={handleYouTubeConfigChange}
            onSave={handleSave}
            onCancel={onCancel}
            loading={loading}
          />
        )}
      </div>
    </div>
  );
};

export default LongVideoConfigWithTabs;

