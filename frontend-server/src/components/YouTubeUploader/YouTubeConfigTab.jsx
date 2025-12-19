import React, { useState, useEffect } from 'react';
import { Card, Button } from '../common';

/**
 * YouTube Platform Configuration Tab
 * Configure YouTube-specific settings for video uploads
 */
const YouTubeConfigTab = ({ config, onChange, onSave, onCancel, loading }) => {
  const [youtubeConfig, setYoutubeConfig] = useState({
    enabled: true,
    title: '',
    description: '',
    tags: [],
    ...config
  });

  useEffect(() => {
    if (config) {
      setYoutubeConfig({
        enabled: true,
        title: '',
        description: '',
        tags: [],
        ...config
      });
    }
  }, [config]);

  const handleInputChange = (field, value) => {
    const updated = {
      ...youtubeConfig,
      [field]: value
    };
    setYoutubeConfig(updated);
    onChange(updated);
  };

  return (
    <div className="space-y-4">
      <Card>
        <div className="space-y-4">
          {/* Enable YouTube Upload */}
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div>
              <h4 className="text-sm font-medium text-gray-900">Enable YouTube Upload</h4>
              <p className="text-sm text-gray-500 mt-1">
                Automatically upload videos to YouTube when generated
              </p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={youtubeConfig.enabled !== false}
                onChange={(e) => handleInputChange('enabled', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-red-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-red-600"></div>
            </label>
          </div>

          {/* YouTube Metadata */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 space-y-4">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-lg">📺</span>
              <h3 className="text-sm font-semibold text-gray-900">YouTube Metadata</h3>
            </div>
            <p className="text-xs text-gray-600 mb-3">
              Custom metadata for YouTube upload. Leave empty to auto-generate based on video content.
            </p>

            {/* YouTube Title */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                YouTube Title (Optional)
              </label>
              <input
                type="text"
                value={youtubeConfig.title}
                onChange={(e) => handleInputChange('title', e.target.value)}
                placeholder="e.g., 📰 Top 20 News: This Morning's Headlines | 10 Dec 2025"
                maxLength={100}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-yellow-500"
              />
              <p className="text-xs text-gray-500 mt-1">
                {youtubeConfig.title.length}/100 characters. Leave empty to auto-generate.
              </p>
            </div>

            {/* YouTube Description */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                YouTube Description (Optional)
              </label>
              <textarea
                value={youtubeConfig.description}
                onChange={(e) => handleInputChange('description', e.target.value)}
                placeholder="Enter custom YouTube description..."
                rows={6}
                maxLength={5000}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-yellow-500"
              />
              <p className="text-xs text-gray-500 mt-1">
                {youtubeConfig.description.length}/5000 characters. Leave empty to auto-generate.
              </p>
            </div>

            {/* YouTube Tags */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                YouTube Tags (Optional)
              </label>
              <input
                type="text"
                value={youtubeConfig.tags.join(', ')}
                onChange={(e) => {
                  const tags = e.target.value.split(',').map(t => t.trim()).filter(t => t);
                  handleInputChange('tags', tags);
                }}
                placeholder="e.g., news, breaking news, latest news, india news"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-yellow-500"
              />
              <p className="text-xs text-gray-500 mt-1">
                {youtubeConfig.tags.length} tags. Separate with commas. Max 35 tags. Leave empty to auto-generate.
              </p>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3 pt-4">
            <Button
              variant="secondary"
              onClick={onCancel}
              disabled={loading}
              className="flex-1"
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={onSave}
              loading={loading}
              disabled={loading}
              className="flex-1"
            >
              {loading ? 'Saving...' : 'Save Configuration'}
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default YouTubeConfigTab;

