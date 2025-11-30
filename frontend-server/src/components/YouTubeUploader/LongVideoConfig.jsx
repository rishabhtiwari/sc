import React, { useState, useEffect } from 'react';
import { Card, Button } from '../common';

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
  });

  const [availableCategories, setAvailableCategories] = useState([]);

  // Fetch available categories on mount
  useEffect(() => {
    fetchCategories();
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
    return config.title.trim() !== '' && config.videoCount > 0;
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
            <p className="text-xs text-gray-500 mt-1">Select between 1-50 videos</p>
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

