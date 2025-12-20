import React, { useState, useEffect } from 'react';

const TemplateWizard = ({ onClose, onSave }) => {
  // Template configuration state
  const [config, setConfig] = useState({
    name: '',
    category: 'news',
    aspect_ratio: '16:9',
    effects: [],
    background_music: {
      enabled: false,
      source: '',
      volume: 0.3,
      fade_in: 2.0,
      fade_out: 2.0
    },
    logo: {
      enabled: false,
      source: '',
      position: 'top-right',
      scale: 0.15,
      opacity: 0.8,
      margin: { x: 20, y: 20 }
    },
    thumbnail: {
      auto_generate: true,
      timestamp: 2.0,
      source: ''
    },
    layers: [],
    variables: {}
  });

  // Configuration history for undo/redo
  const [history, setHistory] = useState([]);
  const [historyIndex, setHistoryIndex] = useState(-1);

  // Preview state
  const [previewUrl, setPreviewUrl] = useState(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState(null);
  const [autoPreview, setAutoPreview] = useState(false);
  const [isInitialPreview, setIsInitialPreview] = useState(true);

  // Active configuration section
  const [activeSection, setActiveSection] = useState('basic');

  // Initialize with default sample video
  useEffect(() => {
    generatePreview(true);
  }, []);

  // Cleanup temp videos on unmount
  useEffect(() => {
    return () => {
      // Cleanup temp preview videos when wizard closes
      if (previewUrl && !isInitialPreview) {
        cleanupPreview(previewUrl);
      }
    };
  }, [previewUrl, isInitialPreview]);

  // Auto-preview when config changes (if enabled)
  useEffect(() => {
    if (autoPreview && historyIndex >= 0) {
      const timeoutId = setTimeout(() => {
        generatePreview();
      }, 1000); // Debounce 1 second
      return () => clearTimeout(timeoutId);
    }
  }, [config, autoPreview]);

  // Update configuration and add to history
  const updateConfig = (updates) => {
    const newConfig = { ...config, ...updates };
    
    // Add to history
    const newHistory = history.slice(0, historyIndex + 1);
    newHistory.push(newConfig);
    setHistory(newHistory);
    setHistoryIndex(newHistory.length - 1);
    
    setConfig(newConfig);
  };

  // Undo configuration change
  const undo = () => {
    if (historyIndex > 0) {
      setHistoryIndex(historyIndex - 1);
      setConfig(history[historyIndex - 1]);
    }
  };

  // Redo configuration change
  const redo = () => {
    if (historyIndex < history.length - 1) {
      setHistoryIndex(historyIndex + 1);
      setConfig(history[historyIndex + 1]);
    }
  };

  // Generate preview video
  const generatePreview = async (isInitial = false) => {
    setPreviewLoading(true);
    setPreviewError(null);

    try {
      const response = await fetch('http://localhost:8080/api/templates/preview', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        },
        body: JSON.stringify({
          template: config,
          sample_data: {},
          is_initial: isInitial
        })
      });

      const data = await response.json();

      if (response.ok && data.status === 'success') {
        // Cleanup old preview if it was a temp file
        if (previewUrl && !isInitialPreview) {
          cleanupPreview(previewUrl);
        }

        // Construct full URL for video preview
        const videoPath = data.preview_url || data.video_path;
        const fullVideoUrl = videoPath.startsWith('http')
          ? videoPath
          : `http://localhost:8080${videoPath}`;

        console.log('Setting preview URL:', fullVideoUrl);
        setPreviewUrl(fullVideoUrl);
        setIsInitialPreview(isInitial);
      } else {
        setPreviewError(data.error || 'Failed to generate preview');
      }
    } catch (error) {
      console.error('Preview generation error:', error);
      setPreviewError('Failed to connect to preview service');
    } finally {
      setPreviewLoading(false);
    }
  };

  // Cleanup preview video
  const cleanupPreview = async (videoUrl) => {
    try {
      await fetch('http://localhost:8080/api/templates/preview/cleanup', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        },
        body: JSON.stringify({
          preview_url: videoUrl
        })
      });
    } catch (error) {
      console.error('Cleanup error:', error);
    }
  };

  // Save template
  const handleSave = async () => {
    if (!config.name) {
      alert('Please enter a template name');
      return;
    }

    // Cleanup temp preview before saving
    if (previewUrl && !isInitialPreview) {
      await cleanupPreview(previewUrl);
    }

    onSave(config);
  };

  // Handle close
  const handleClose = async () => {
    // Cleanup temp preview before closing
    if (previewUrl && !isInitialPreview) {
      await cleanupPreview(previewUrl);
    }
    onClose();
  };

  const sections = [
    { id: 'basic', name: 'Basic Info', icon: '📝' },
    { id: 'effects', name: 'Effects', icon: '✨' },
    { id: 'music', name: 'Background Music', icon: '🎵' },
    { id: 'logo', name: 'Logo', icon: '🏷️' },
    { id: 'thumbnail', name: 'Thumbnail', icon: '🖼️' },
    { id: 'layers', name: 'Layers', icon: '🎨' },
    { id: 'variables', name: 'Variables', icon: '🔧' }
  ];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full h-full max-w-7xl max-h-[95vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">🎬 Template Creation Wizard</h2>
            <p className="text-sm text-gray-600 mt-1">Configure your template and see live preview</p>
          </div>
          <div className="flex items-center gap-3">
            {/* Undo/Redo buttons */}
            <button
              onClick={undo}
              disabled={historyIndex <= 0}
              className={`px-3 py-2 rounded-lg font-medium ${
                historyIndex <= 0
                  ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
              title="Undo (Ctrl+Z)"
            >
              ↶ Undo
            </button>
            <button
              onClick={redo}
              disabled={historyIndex >= history.length - 1}
              className={`px-3 py-2 rounded-lg font-medium ${
                historyIndex >= history.length - 1
                  ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
              title="Redo (Ctrl+Y)"
            >
              ↷ Redo
            </button>

            {/* Auto-preview toggle */}
            <label className="flex items-center gap-2 px-3 py-2 bg-purple-50 rounded-lg cursor-pointer">
              <input
                type="checkbox"
                checked={autoPreview}
                onChange={(e) => setAutoPreview(e.target.checked)}
                className="w-4 h-4 text-purple-600 rounded"
              />
              <span className="text-sm font-medium text-purple-900">Auto Preview</span>
            </label>

            <button
              onClick={handleClose}
              className="px-4 py-2 text-gray-600 hover:text-gray-900 font-medium"
            >
              ✕ Close
            </button>
          </div>
        </div>

        {/* Main Content - Split Screen */}
        <div className="flex-1 flex overflow-hidden">
          {/* Left Side - Video Preview */}
          <div className="w-1/2 border-r border-gray-200 flex flex-col bg-gray-50">
            <div className="p-4 border-b border-gray-200 bg-white">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900">📹 Live Preview</h3>
                <button
                  onClick={generatePreview}
                  disabled={previewLoading}
                  className={`px-4 py-2 rounded-lg font-medium text-white ${
                    previewLoading
                      ? 'bg-gray-400 cursor-not-allowed'
                      : 'bg-indigo-600 hover:bg-indigo-700'
                  }`}
                >
                  {previewLoading ? '⏳ Generating...' : '🔄 Refresh Preview'}
                </button>
              </div>
            </div>

            <div className="flex-1 p-6 flex items-center justify-center overflow-auto">
              {previewLoading && (
                <div className="text-center">
                  <div className="inline-block animate-spin rounded-full h-16 w-16 border-4 border-indigo-600 border-t-transparent mb-4"></div>
                  <p className="text-gray-600 font-medium">Generating preview...</p>
                  <p className="text-sm text-gray-500 mt-2">This may take 1-2 minutes</p>
                </div>
              )}

              {previewError && !previewLoading && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md">
                  <h4 className="font-medium text-red-900 mb-2">❌ Preview Failed</h4>
                  <p className="text-sm text-red-800">{previewError}</p>
                  <button
                    onClick={generatePreview}
                    className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
                  >
                    Try Again
                  </button>
                </div>
              )}

              {previewUrl && !previewLoading && (
                <div className="w-full max-w-3xl">
                  <div className="aspect-video bg-black rounded-lg overflow-hidden shadow-2xl">
                    <video
                      key={previewUrl}
                      src={previewUrl}
                      controls
                      autoPlay
                      className="w-full h-full"
                      onError={(e) => {
                        console.error('Video load error:', e);
                        console.error('Video src:', previewUrl);
                        console.error('Video error details:', e.target.error);
                        setPreviewError('Failed to load video. Please check the console for details.');
                      }}
                      onLoadStart={() => console.log('Video loading started:', previewUrl)}
                      onCanPlay={() => console.log('Video can play:', previewUrl)}
                    >
                      Your browser does not support the video tag.
                    </video>
                  </div>
                  <div className="mt-4 flex gap-3 justify-center">
                    <a
                      href={previewUrl}
                      download
                      className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium"
                    >
                      📥 Download
                    </a>
                  </div>
                </div>
              )}

              {!previewUrl && !previewLoading && !previewError && (
                <div className="text-center">
                  <div className="text-6xl mb-4">🎥</div>
                  <h4 className="text-lg font-medium text-gray-900 mb-2">No Preview Yet</h4>
                  <p className="text-gray-600 mb-4">Click "Refresh Preview" to generate a sample video</p>
                </div>
              )}
            </div>
          </div>

          {/* Right Side - Configuration Panel */}
          <div className="w-1/2 flex flex-col bg-white">
            {/* Section Tabs */}
            <div className="border-b border-gray-200 bg-gray-50 px-4 py-3 overflow-x-auto">
              <div className="flex gap-2">
                {sections.map((section) => (
                  <button
                    key={section.id}
                    onClick={() => setActiveSection(section.id)}
                    className={`px-4 py-2 rounded-lg font-medium whitespace-nowrap transition-colors ${
                      activeSection === section.id
                        ? 'bg-indigo-600 text-white shadow-md'
                        : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-200'
                    }`}
                  >
                    <span className="mr-2">{section.icon}</span>
                    {section.name}
                  </button>
                ))}
              </div>
            </div>

            {/* Configuration Content */}
            <div className="flex-1 overflow-auto p-6">
              {activeSection === 'basic' && (
                <BasicInfoSection config={config} updateConfig={updateConfig} />
              )}
              {activeSection === 'effects' && (
                <EffectsSection config={config} updateConfig={updateConfig} />
              )}
              {activeSection === 'music' && (
                <MusicSection config={config} updateConfig={updateConfig} />
              )}
              {activeSection === 'logo' && (
                <LogoSection config={config} updateConfig={updateConfig} />
              )}
              {activeSection === 'thumbnail' && (
                <ThumbnailSection config={config} updateConfig={updateConfig} />
              )}
              {activeSection === 'layers' && (
                <LayersSection config={config} updateConfig={updateConfig} />
              )}
              {activeSection === 'variables' && (
                <VariablesSection config={config} updateConfig={updateConfig} />
              )}
            </div>
          </div>
        </div>

        {/* Footer - Action Buttons */}
        <div className="border-t border-gray-200 p-6 bg-gray-50 flex items-center justify-between">
          <div className="text-sm text-gray-600">
            {historyIndex >= 0 && (
              <span>
                {historyIndex + 1} change{historyIndex !== 0 ? 's' : ''} made
              </span>
            )}
          </div>
          <div className="flex gap-3">
            <button
              onClick={handleClose}
              className="px-6 py-3 border border-gray-300 rounded-lg font-medium text-gray-700 hover:bg-gray-100"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              className="px-6 py-3 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-lg font-medium hover:from-purple-700 hover:to-indigo-700 shadow-lg"
            >
              💾 Save Template
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Configuration Sections Components

const BasicInfoSection = ({ config, updateConfig }) => (
  <div className="space-y-6">
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
      <h4 className="font-medium text-blue-900 mb-2">📝 Basic Information</h4>
      <p className="text-sm text-blue-800">
        Set the basic details for your template including name, category, and aspect ratio.
      </p>
    </div>

    <div>
      <label className="block text-sm font-medium text-gray-700 mb-2">Template Name *</label>
      <input
        type="text"
        value={config.name}
        onChange={(e) => updateConfig({ name: e.target.value })}
        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
        placeholder="e.g., Breaking News Template"
      />
    </div>

    <div>
      <label className="block text-sm font-medium text-gray-700 mb-2">Category</label>
      <select
        value={config.category}
        onChange={(e) => updateConfig({ category: e.target.value })}
        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
      >
        <option value="news">News</option>
        <option value="shorts">Shorts</option>
        <option value="ecommerce">E-commerce</option>
        <option value="social">Social Media</option>
      </select>
    </div>

    <div>
      <label className="block text-sm font-medium text-gray-700 mb-2">Aspect Ratio</label>
      <div className="grid grid-cols-3 gap-3">
        {['16:9', '9:16', '1:1', '4:5'].map((ratio) => (
          <button
            key={ratio}
            onClick={() => updateConfig({ aspect_ratio: ratio })}
            className={`px-4 py-3 rounded-lg font-medium border-2 transition-all ${
              config.aspect_ratio === ratio
                ? 'border-indigo-600 bg-indigo-50 text-indigo-900'
                : 'border-gray-300 bg-white text-gray-700 hover:border-gray-400'
            }`}
          >
            {ratio}
          </button>
        ))}
      </div>
    </div>
  </div>
);

const EffectsSection = ({ config, updateConfig }) => {
  const addEffect = () => {
    const newEffect = {
      type: 'ken_burns',
      target_layer_id: 'background',
      params: { zoom_start: 1.0, zoom_end: 1.2, easing: 'ease_in_out' }
    };
    updateConfig({ effects: [...config.effects, newEffect] });
  };

  const removeEffect = (index) => {
    const newEffects = config.effects.filter((_, i) => i !== index);
    updateConfig({ effects: newEffects });
  };

  const updateEffect = (index, updates) => {
    const newEffects = [...config.effects];
    newEffects[index] = { ...newEffects[index], ...updates };
    updateConfig({ effects: newEffects });
  };

  return (
    <div className="space-y-6">
      <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
        <h4 className="font-medium text-purple-900 mb-2">✨ Video Effects</h4>
        <p className="text-sm text-purple-800">
          Add visual effects like Ken Burns (zoom & pan), transitions, and more.
        </p>
      </div>

      <button
        onClick={addEffect}
        className="w-full px-4 py-3 border-2 border-dashed border-indigo-300 rounded-lg text-indigo-600 font-medium hover:bg-indigo-50"
      >
        + Add Effect
      </button>

      {config.effects.map((effect, index) => (
        <div key={index} className="border border-gray-300 rounded-lg p-4 bg-gray-50">
          <div className="flex items-center justify-between mb-3">
            <h5 className="font-medium text-gray-900">Effect #{index + 1}</h5>
            <button
              onClick={() => removeEffect(index)}
              className="text-red-600 hover:text-red-800 font-medium"
            >
              🗑️ Remove
            </button>
          </div>

          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Effect Type</label>
              <select
                value={effect.type}
                onChange={(e) => updateEffect(index, { type: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              >
                <option value="ken_burns">Ken Burns (Zoom & Pan)</option>
                <option value="fade_text">Fade Text</option>
                <option value="transition">Transition</option>
                <option value="bottom_banner">Bottom Banner</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Target Layer ID</label>
              <input
                type="text"
                value={effect.target_layer_id}
                onChange={(e) => updateEffect(index, { target_layer_id: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                placeholder="e.g., background"
              />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

const MusicSection = ({ config, updateConfig }) => {
  const updateMusic = (updates) => {
    updateConfig({ background_music: { ...config.background_music, ...updates } });
  };

  return (
    <div className="space-y-6">
      <div className="bg-green-50 border border-green-200 rounded-lg p-4">
        <h4 className="font-medium text-green-900 mb-2">🎵 Background Music</h4>
        <p className="text-sm text-green-800">
          Add background music to your videos with volume and fade controls.
        </p>
      </div>

      <div className="flex items-center gap-3">
        <input
          type="checkbox"
          id="music-enabled"
          checked={config.background_music.enabled}
          onChange={(e) => updateMusic({ enabled: e.target.checked })}
          className="w-5 h-5 text-indigo-600 rounded"
        />
        <label htmlFor="music-enabled" className="text-lg font-semibold text-gray-900">
          Enable Background Music
        </label>
      </div>

      {config.background_music.enabled && (
        <>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Music File</label>
            <input
              type="text"
              value={config.background_music.source}
              onChange={(e) => updateMusic({ source: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg"
              placeholder="music.mp3 or {{music_file}}"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Volume: {config.background_music.volume}
            </label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={config.background_music.volume}
              onChange={(e) => updateMusic({ volume: parseFloat(e.target.value) })}
              className="w-full"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Fade In (seconds)</label>
              <input
                type="number"
                min="0"
                step="0.5"
                value={config.background_music.fade_in}
                onChange={(e) => updateMusic({ fade_in: parseFloat(e.target.value) })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Fade Out (seconds)</label>
              <input
                type="number"
                min="0"
                step="0.5"
                value={config.background_music.fade_out}
                onChange={(e) => updateMusic({ fade_out: parseFloat(e.target.value) })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg"
              />
            </div>
          </div>
        </>
      )}
    </div>
  );
};

const LogoSection = ({ config, updateConfig }) => {
  const updateLogo = (updates) => {
    updateConfig({ logo: { ...config.logo, ...updates } });
  };

  return (
    <div className="space-y-6">
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <h4 className="font-medium text-yellow-900 mb-2">🏷️ Logo Watermark</h4>
        <p className="text-sm text-yellow-800">
          Add your logo as a watermark with customizable position and opacity.
        </p>
      </div>

      <div className="flex items-center gap-3">
        <input
          type="checkbox"
          id="logo-enabled"
          checked={config.logo.enabled}
          onChange={(e) => updateLogo({ enabled: e.target.checked })}
          className="w-5 h-5 text-indigo-600 rounded"
        />
        <label htmlFor="logo-enabled" className="text-lg font-semibold text-gray-900">
          Enable Logo Watermark
        </label>
      </div>

      {config.logo.enabled && (
        <>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Logo Image</label>
            <input
              type="text"
              value={config.logo.source}
              onChange={(e) => updateLogo({ source: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg"
              placeholder="logo.png or {{logo_path}}"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Position</label>
            <div className="grid grid-cols-2 gap-3">
              {['top-left', 'top-right', 'bottom-left', 'bottom-right'].map((pos) => (
                <button
                  key={pos}
                  onClick={() => updateLogo({ position: pos })}
                  className={`px-4 py-2 rounded-lg font-medium border-2 ${
                    config.logo.position === pos
                      ? 'border-indigo-600 bg-indigo-50 text-indigo-900'
                      : 'border-gray-300 bg-white text-gray-700 hover:border-gray-400'
                  }`}
                >
                  {pos}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Scale: {config.logo.scale}
            </label>
            <input
              type="range"
              min="0.05"
              max="0.5"
              step="0.05"
              value={config.logo.scale}
              onChange={(e) => updateLogo({ scale: parseFloat(e.target.value) })}
              className="w-full"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Opacity: {config.logo.opacity}
            </label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={config.logo.opacity}
              onChange={(e) => updateLogo({ opacity: parseFloat(e.target.value) })}
              className="w-full"
            />
          </div>
        </>
      )}
    </div>
  );
};

const ThumbnailSection = ({ config, updateConfig }) => {
  const updateThumbnail = (updates) => {
    updateConfig({ thumbnail: { ...config.thumbnail, ...updates } });
  };

  return (
    <div className="space-y-6">
      <div className="bg-pink-50 border border-pink-200 rounded-lg p-4">
        <h4 className="font-medium text-pink-900 mb-2">🖼️ Thumbnail</h4>
        <p className="text-sm text-pink-800">
          Configure how video thumbnails are generated.
        </p>
      </div>

      <div className="flex items-center gap-3">
        <input
          type="checkbox"
          id="auto-thumbnail"
          checked={config.thumbnail.auto_generate}
          onChange={(e) => updateThumbnail({ auto_generate: e.target.checked })}
          className="w-5 h-5 text-indigo-600 rounded"
        />
        <label htmlFor="auto-thumbnail" className="text-lg font-semibold text-gray-900">
          Auto-Generate Thumbnail
        </label>
      </div>

      {config.thumbnail.auto_generate ? (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Timestamp (seconds)</label>
          <input
            type="number"
            min="0"
            step="0.5"
            value={config.thumbnail.timestamp}
            onChange={(e) => updateThumbnail({ timestamp: parseFloat(e.target.value) })}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg"
          />
        </div>
      ) : (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Custom Thumbnail</label>
          <input
            type="text"
            value={config.thumbnail.source}
            onChange={(e) => updateThumbnail({ source: e.target.value })}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg"
            placeholder="thumbnail.jpg or {{thumbnail_image}}"
          />
        </div>
      )}
    </div>
  );
};

const LayersSection = ({ config, updateConfig }) => (
  <div className="space-y-6">
    <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4">
      <h4 className="font-medium text-indigo-900 mb-2">🎨 Layers</h4>
      <p className="text-sm text-indigo-800">
        Layers will be configured in the advanced editor. Use this wizard for basic settings.
      </p>
    </div>
    <p className="text-gray-600">Layer configuration coming soon...</p>
  </div>
);

const VariablesSection = ({ config, updateConfig }) => (
  <div className="space-y-6">
    <div className="bg-teal-50 border border-teal-200 rounded-lg p-4">
      <h4 className="font-medium text-teal-900 mb-2">🔧 Variables</h4>
      <p className="text-sm text-teal-800">
        Variables will be configured in the advanced editor. Use this wizard for basic settings.
      </p>
    </div>
    <p className="text-gray-600">Variable configuration coming soon...</p>
  </div>
);

export default TemplateWizard;

