import React, { useState, useEffect } from 'react';
import { Card, Button } from '../common';
import NewsSelector from './NewsSelector';
import { backgroundAudioService } from '../../services';

/**
 * Long Video Configuration Component - Configure and create compilation videos
 */
const LongVideoConfig = ({ initialConfig, onSave, onCancel, loading }) => {
  const [config, setConfig] = useState({
    categories: [],
    country: '',
    language: '',
    videoCount: 20,
    title: '',
    frequency: 'none',
    youtubeTitle: '',
    youtubeDescription: '',
    youtubeTags: [],
    backgroundAudioId: null,
  });

  const [availableCategories, setAvailableCategories] = useState([]);
  const [audioFiles, setAudioFiles] = useState([]);
  const [audioLoading, setAudioLoading] = useState(false);

  // Fetch available categories and audio files on mount
  useEffect(() => {
    fetchCategories();
    fetchAudioFiles();
  }, []);

  // Load initial config if editing
  useEffect(() => {
    if (initialConfig) {
      setConfig({
        categories: initialConfig.categories || [],
        country: initialConfig.country || '',
        language: initialConfig.language || '',
        videoCount: initialConfig.videoCount || 20,
        title: initialConfig.title || '',
        frequency: initialConfig.frequency || 'none',
        youtubeTitle: initialConfig.youtubeTitle || '',
        youtubeDescription: initialConfig.youtubeDescription || '',
        youtubeTags: initialConfig.youtubeTags || [],
        backgroundAudioId: initialConfig.backgroundAudioId || null,
      });
    }
  }, [initialConfig]);

  const fetchCategories = async () => {
    try {
      const response = await fetch('/api/news/categories');
      const data = await response.json();
      if (data.status === 'success') {
        // Ensure categories is always an array
        const categories = Array.isArray(data.categories) ? data.categories : [];
        setAvailableCategories(categories);
      } else {
        setAvailableCategories([]);
      }
    } catch (error) {
      console.error('Failed to fetch categories:', error);
      setAvailableCategories([]);
    }
  };

  const fetchAudioFiles = async () => {
    try {
      setAudioLoading(true);
      const response = await backgroundAudioService.getBackgroundAudioList();
      if (response.data.status === 'success') {
        setAudioFiles(response.data.audio_files || []);
      } else {
        setAudioFiles([]);
      }
    } catch (error) {
      console.error('Failed to fetch audio files:', error);
      setAudioFiles([]);
    } finally {
      setAudioLoading(false);
    }
  };

  const handleInputChange = (field, value) => {
    setConfig(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleCategoryToggle = (category) => {
    setConfig(prev => ({
      ...prev,
      categories: prev.categories.includes(category)
        ? prev.categories.filter(c => c !== category)
        : [...prev.categories, category]
    }));
  };

  const handleSave = () => {
    // Validate required fields
    if (!config.title || !config.title.trim()) {
      alert('Please enter a title for the video configuration');
      return;
    }

    if (config.videoCount < 1 || config.videoCount > 100) {
      alert('Video count must be between 1 and 100');
      return;
    }

    onSave(config);
  };

  const handleCancel = () => {
    onCancel();
  };

  const isConfigValid = () => {
    if (!config.title.trim()) return false;
    return config.videoCount > 0;
  };

  return (
    <div className="space-y-4">
      {/* Configuration Form */}
      <div className="space-y-4">
        {/* Title */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Video Title *
          </label>
          <input
            type="text"
            value={config.title}
            onChange={(e) => handleInputChange('title', e.target.value)}
            placeholder="e.g., Top 20 News Stories Today"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500"
          />
        </div>

        {/* Number of Videos */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Number of Videos
          </label>
          <input
            type="number"
            value={config.videoCount}
            onChange={(e) => handleInputChange('videoCount', parseInt(e.target.value) || 0)}
            min="1"
            max="50"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500"
          />
          <p className="text-xs text-gray-500 mt-1">
            Select between 1-50 videos. Use the Re-compute wizard to manually select specific articles.
          </p>
        </div>

        {/* Categories */}
        <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Categories (Optional)
            </label>
            <div className="flex flex-wrap gap-2">
              {availableCategories.map((category) => (
                <button
                  key={category}
                  onClick={() => handleCategoryToggle(category)}
                  className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                    config.categories.includes(category)
                      ? 'bg-red-600 text-white'
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                >
                  {category}
                </button>
              ))}
            </div>
            <p className="text-xs text-gray-500 mt-1">
              {config.categories.length === 0 
                ? 'All categories will be included' 
                : `${config.categories.length} category(ies) selected`}
            </p>
        </div>

        {/* Country */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Country (Optional)
          </label>
          <select
            value={config.country}
            onChange={(e) => handleInputChange('country', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500"
          >
            <option value="">All Countries</option>
            <option value="us">United States</option>
            <option value="in">India</option>
            <option value="gb">United Kingdom</option>
            <option value="ca">Canada</option>
            <option value="au">Australia</option>
          </select>
        </div>

        {/* Language */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Language (Optional)
          </label>
          <select
            value={config.language}
            onChange={(e) => handleInputChange('language', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500"
          >
            <option value="">All Languages</option>
            <option value="en">English</option>
            <option value="hi">Hindi</option>
            <option value="es">Spanish</option>
            <option value="fr">French</option>
            <option value="de">German</option>
          </select>
        </div>

        {/* Frequency */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Auto-Recompute Frequency
          </label>
          <select
            value={config.frequency}
            onChange={(e) => handleInputChange('frequency', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500"
          >
            <option value="none">None (Manual Only)</option>
            <option value="hourly">Hourly</option>
            <option value="daily">Daily</option>
            <option value="weekly">Weekly</option>
            <option value="monthly">Monthly</option>
          </select>
          <p className="mt-1 text-xs text-gray-500">
            Automatically recompute this video based on the selected frequency
          </p>
        </div>

        {/* Background Audio */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Background Audio (Optional)
          </label>
          <select
            value={config.backgroundAudioId || ''}
            onChange={(e) => handleInputChange('backgroundAudioId', e.target.value || null)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500"
            disabled={audioLoading}
          >
            <option value="">Default Background Music</option>
            {audioFiles.map((audio) => (
              <option key={audio.id} value={audio.id}>
                🎵 {audio.name} ({audio.size_mb} MB)
              </option>
            ))}
          </select>
          <p className="mt-1 text-xs text-gray-500">
            {audioLoading ? (
              'Loading audio files...'
            ) : audioFiles.length === 0 ? (
              <>Upload background audio files in the "Audio Library" tab to use custom music</>
            ) : (
              <>Select custom background audio or use default music. {audioFiles.length} audio file(s) available.</>
            )}
          </p>
        </div>

        {/* YouTube Metadata Section */}
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 space-y-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-lg">📺</span>
            <h3 className="text-sm font-semibold text-gray-900">YouTube Metadata (Optional)</h3>
          </div>
          <p className="text-xs text-gray-600 mb-3">
            Custom metadata for YouTube upload. Leave empty to auto-generate.
          </p>

          {/* YouTube Title */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              YouTube Title
            </label>
            <input
              type="text"
              value={config.youtubeTitle}
              onChange={(e) => handleInputChange('youtubeTitle', e.target.value)}
              placeholder="e.g., 📰 Top 20 News: This Morning's Headlines | 10 Dec 2025"
              maxLength={100}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-yellow-500"
            />
            <p className="text-xs text-gray-500 mt-1">
              {config.youtubeTitle.length}/100 characters. Leave empty to auto-generate.
            </p>
          </div>

          {/* YouTube Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              YouTube Description
            </label>
            <textarea
              value={config.youtubeDescription}
              onChange={(e) => handleInputChange('youtubeDescription', e.target.value)}
              placeholder="Enter custom YouTube description..."
              rows={4}
              maxLength={5000}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-yellow-500"
            />
            <p className="text-xs text-gray-500 mt-1">
              {config.youtubeDescription.length}/5000 characters. Leave empty to auto-generate.
            </p>
          </div>

          {/* YouTube Tags */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              YouTube Tags
            </label>
            <input
              type="text"
              value={config.youtubeTags.join(', ')}
              onChange={(e) => {
                const tags = e.target.value.split(',').map(t => t.trim()).filter(t => t);
                handleInputChange('youtubeTags', tags);
              }}
              placeholder="e.g., news, breaking news, latest news, india news"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-yellow-500"
            />
            <p className="text-xs text-gray-500 mt-1">
              {config.youtubeTags.length} tags. Separate with commas. Max 35 tags. Leave empty to auto-generate.
            </p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-3 pt-4">
          <Button
            variant="secondary"
            onClick={handleCancel}
            disabled={loading}
            className="flex-1"
          >
            Cancel
          </Button>
          <Button
            variant="primary"
            onClick={handleSave}
            loading={loading}
            disabled={!isConfigValid() || loading}
            className="flex-1"
          >
            {loading ? 'Saving...' : initialConfig ? 'Update Configuration' : 'Save Configuration'}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default LongVideoConfig;

