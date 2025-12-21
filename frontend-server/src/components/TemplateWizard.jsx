import React, { useState, useEffect } from 'react';

const TemplateWizard = ({ template, onClose, onSave }) => {
  // Generate unique template ID
  const generateTemplateId = (name, category) => {
    const timestamp = Date.now();
    const sanitizedName = name.toLowerCase().replace(/[^a-z0-9]/g, '_') || 'template';
    return `${category}_${sanitizedName}_${timestamp}`;
  };

  // Default template configuration
  const getDefaultConfig = () => ({
    template_id: generateTemplateId('', 'news'),
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
      source: '',
      text: {
        enabled: false,
        title: '',
        subtitle: '',
        position: 'top-left',
        font_size: 88,
        title_color: '#FFFFFF',
        subtitle_color: '#FFFFFF',
        background_color: '#003399',
        background_opacity: 0.9
      }
    },
    layers: [],
    variables: {}
  });

  // Deep merge helper function
  const deepMerge = (target, source) => {
    const result = { ...target };
    for (const key in source) {
      if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
        result[key] = deepMerge(target[key] || {}, source[key]);
      } else {
        result[key] = source[key];
      }
    }
    return result;
  };

  // Template configuration state - initialize from template prop if editing
  const [config, setConfig] = useState(() => {
    if (template) {
      // Editing existing template - deep merge with defaults to ensure all fields exist
      console.log('🔧 Initializing wizard with template:', template);
      return deepMerge(getDefaultConfig(), template);
    }
    // Creating new template - use defaults
    console.log('🆕 Initializing wizard for new template');
    return getDefaultConfig();
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

  // Save state
  const [saveError, setSaveError] = useState(null);
  const [saveLoading, setSaveLoading] = useState(false);

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
  const updateConfig = (updates, autoRefreshPreview = false) => {
    const newConfig = { ...config, ...updates };

    // Add to history
    const newHistory = history.slice(0, historyIndex + 1);
    newHistory.push(newConfig);
    setHistory(newHistory);
    setHistoryIndex(newHistory.length - 1);

    setConfig(newConfig);

    // Auto-refresh preview for certain changes (like aspect ratio or effects)
    if (autoRefreshPreview) {
      // Use setTimeout to ensure state is updated first, and pass the new config
      setTimeout(() => {
        // Use is_initial=false to generate a new preview with effects applied
        generatePreviewWithConfig(newConfig, false);
      }, 100);
    }
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

  // Generate preview video with specific config
  const generatePreviewWithConfig = async (templateConfig, isInitial = false) => {
    console.log('generatePreviewWithConfig called:', { isInitial, background_music: templateConfig.background_music });
    setPreviewLoading(true);
    setPreviewError(null);

    try {
      const requestBody = {
        template: templateConfig,
        sample_data: {},
        is_initial: isInitial
      };
      console.log('Sending preview request:', requestBody);

      const response = await fetch('http://localhost:8080/api/templates/preview', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        },
        body: JSON.stringify(requestBody)
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

  // Generate preview video with current config
  const generatePreview = async (isInitial = false) => {
    return generatePreviewWithConfig(config, isInitial);
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
    // Clear previous errors
    setSaveError(null);

    // Validate required fields
    if (!config.name) {
      setSaveError('Please enter a template name');
      return;
    }

    try {
      setSaveLoading(true);

      // Cleanup temp preview before saving
      if (previewUrl && !isInitialPreview) {
        await cleanupPreview(previewUrl);
      }

      // Call the onSave callback
      await onSave(config);
    } catch (error) {
      setSaveError(error.message || 'Failed to save template');
    } finally {
      setSaveLoading(false);
    }
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
    { id: 'layers', name: 'Layers', icon: '🎨' },
    { id: 'effects', name: 'Effects', icon: '✨' },
    { id: 'music', name: 'Background Music', icon: '🎵' },
    { id: 'logo', name: 'Logo', icon: '🏷️' },
    { id: 'thumbnail', name: 'Thumbnail', icon: '🖼️' },
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
                  onClick={() => {
                    console.log('Refresh Preview clicked, config:', config);
                    generatePreview(false);
                  }}
                  disabled={previewLoading}
                  className={`px-4 py-2 rounded-lg font-medium text-white ${
                    previewLoading
                      ? 'bg-gray-400 cursor-not-allowed'
                      : 'bg-blue-600 hover:bg-blue-700'
                  }`}
                >
                  {previewLoading ? '⏳ Generating...' : '🔄 Refresh Preview'}
                </button>
              </div>
            </div>

            <div className="flex-1 p-6 flex items-center justify-center overflow-auto">
              {previewLoading && (
                <div className="text-center">
                  <div className="inline-block animate-spin rounded-full h-16 w-16 border-4 border-blue-600 border-t-transparent mb-4"></div>
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
                  <div className={`bg-black rounded-lg overflow-hidden shadow-2xl ${
                    config.aspect_ratio === '16:9' ? 'aspect-video' :
                    config.aspect_ratio === '9:16' ? 'aspect-[9/16]' :
                    config.aspect_ratio === '1:1' ? 'aspect-square' :
                    config.aspect_ratio === '4:5' ? 'aspect-[4/5]' :
                    'aspect-video'
                  }`}>
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
                        ? 'bg-blue-600 text-white shadow-md'
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
                <ThumbnailSection config={config} updateConfig={updateConfig} previewUrl={previewUrl} />
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
          <div className="flex flex-col items-end gap-3">
            {/* Error Message */}
            {saveError && (
              <div className="w-full bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-start gap-2">
                <span className="text-xl">⚠️</span>
                <div className="flex-1">
                  <p className="font-medium">Failed to save template</p>
                  <p className="text-sm mt-1">{saveError}</p>
                </div>
                <button
                  onClick={() => setSaveError(null)}
                  className="text-red-400 hover:text-red-600"
                >
                  ✕
                </button>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex gap-3">
              <button
                onClick={handleClose}
                disabled={saveLoading}
                className="px-6 py-3 border border-gray-300 rounded-lg font-medium text-gray-700 hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={saveLoading}
                className="px-6 py-3 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-lg font-medium hover:from-purple-700 hover:to-indigo-700 shadow-lg disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {saveLoading ? (
                  <>
                    <span className="animate-spin">⏳</span>
                    Saving...
                  </>
                ) : (
                  <>💾 Save Template</>
                )}
              </button>
            </div>
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
      <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
      <textarea
        value={config.description || ''}
        onChange={(e) => updateConfig({ description: e.target.value })}
        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
        placeholder="Brief description of this template..."
        rows="3"
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
            onClick={() => updateConfig({ aspect_ratio: ratio }, true)}
            className={`px-4 py-3 rounded-lg font-medium border-2 transition-all ${
              config.aspect_ratio === ratio
                ? 'border-blue-600 bg-blue-50 text-blue-900'
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
  // Available effects with their metadata
  const availableEffects = [
    {
      type: 'ken_burns',
      name: 'Ken Burns (Zoom & Pan)',
      icon: '🎬',
      description: 'Adds cinematic zoom and pan motion to images',
      defaultParams: { zoom_start: 1.0, zoom_end: 1.2, pan_style: 'zoom_center', easing: 'ease_in_out' }
    },
    {
      type: 'transition',
      name: 'Transition',
      icon: '🔄',
      description: 'Crossfade, slide, wipe transitions between clips',
      defaultParams: { transition_type: 'crossfade', duration: 1.0 }
    },
    {
      type: 'bottom_banner',
      name: 'Bottom Banner',
      icon: '📰',
      description: 'Two-tier bottom banner with scrolling ticker',
      defaultParams: { height: 120, background_color: '#1a1a1a', opacity: 0.9 }
    }
  ];

  // Check if an effect is enabled
  const isEffectEnabled = (effectType) => {
    return config.effects.some(e => e.type === effectType);
  };

  // Get effect configuration
  const getEffectConfig = (effectType) => {
    return config.effects.find(e => e.type === effectType);
  };

  // Toggle effect on/off
  const toggleEffect = (effectType, effectMetadata) => {
    if (isEffectEnabled(effectType)) {
      // Remove effect
      const newEffects = config.effects.filter(e => e.type !== effectType);
      updateConfig({ effects: newEffects }, true); // Auto-refresh preview
    } else {
      // Add effect with default params
      const newEffect = {
        type: effectType,
        target_layer_id: '',
        params: effectMetadata.defaultParams
      };
      updateConfig({ effects: [...config.effects, newEffect] }, true); // Auto-refresh preview
    }
  };

  // Update effect parameters
  const updateEffectParams = (effectType, paramUpdates) => {
    const newEffects = config.effects.map(effect => {
      if (effect.type === effectType) {
        return {
          ...effect,
          params: { ...effect.params, ...paramUpdates }
        };
      }
      return effect;
    });
    updateConfig({ effects: newEffects }, true); // Auto-refresh preview
  };

  return (
    <div className="space-y-6">
      <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
        <h4 className="font-medium text-purple-900 mb-2">✨ Video Effects</h4>
        <p className="text-sm text-purple-800">
          Select effects to apply to your video. Changes will update the preview automatically.
        </p>
      </div>

      {availableEffects.map((effectMeta) => {
        const enabled = isEffectEnabled(effectMeta.type);
        const effectConfig = getEffectConfig(effectMeta.type);

        return (
          <div key={effectMeta.type} className="border border-gray-300 rounded-lg p-4 bg-white">
            {/* Effect Header with Checkbox */}
            <div className="flex items-start gap-3 mb-3">
              <input
                type="checkbox"
                id={`effect-${effectMeta.type}`}
                checked={enabled}
                onChange={() => toggleEffect(effectMeta.type, effectMeta)}
                className="w-5 h-5 text-blue-600 rounded mt-1"
              />
              <div className="flex-1">
                <label htmlFor={`effect-${effectMeta.type}`} className="flex items-center gap-2 cursor-pointer">
                  <span className="text-2xl">{effectMeta.icon}</span>
                  <div>
                    <div className="font-semibold text-gray-900">{effectMeta.name}</div>
                    <div className="text-sm text-gray-600">{effectMeta.description}</div>
                  </div>
                </label>
              </div>
            </div>

            {/* Effect Configuration (shown when enabled) */}
            {enabled && effectConfig && (
              <div className="ml-8 mt-4 space-y-3 border-t border-gray-200 pt-4">
                {/* Ken Burns Parameters */}
                {effectMeta.type === 'ken_burns' && (
                  <>
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Zoom Start</label>
                        <input
                          type="number"
                          step="0.1"
                          min="0.5"
                          max="2.0"
                          value={effectConfig.params.zoom_start || 1.0}
                          onChange={(e) => updateEffectParams(effectMeta.type, { zoom_start: parseFloat(e.target.value) })}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Zoom End</label>
                        <input
                          type="number"
                          step="0.1"
                          min="0.5"
                          max="2.0"
                          value={effectConfig.params.zoom_end || 1.2}
                          onChange={(e) => updateEffectParams(effectMeta.type, { zoom_end: parseFloat(e.target.value) })}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                        />
                      </div>
                    </div>
                  </>
                )}

                {/* Transition Parameters */}
                {effectMeta.type === 'transition' && (
                  <>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Transition Type</label>
                      <select
                        value={effectConfig.params.transition_type || 'crossfade'}
                        onChange={(e) => updateEffectParams(effectMeta.type, { transition_type: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                      >
                        <option value="crossfade">Crossfade</option>
                        <option value="fade_black">Fade to Black</option>
                        <option value="slide_left">Slide Left</option>
                        <option value="slide_right">Slide Right</option>
                        <option value="slide_up">Slide Up</option>
                        <option value="slide_down">Slide Down</option>
                        <option value="wipe_horizontal">Wipe Horizontal</option>
                        <option value="wipe_vertical">Wipe Vertical</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Duration (seconds)</label>
                      <input
                        type="number"
                        step="0.1"
                        min="0.1"
                        max="3"
                        value={effectConfig.params.duration || 1.0}
                        onChange={(e) => updateEffectParams(effectMeta.type, { duration: parseFloat(e.target.value) })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                      />
                    </div>
                  </>
                )}

                {/* Bottom Banner Parameters */}
                {effectMeta.type === 'bottom_banner' && (
                  <>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Static Heading Text
                        <span className="text-xs text-gray-500 ml-2">(Top tier - centered)</span>
                      </label>
                      <input
                        type="text"
                        value={effectConfig.params.heading || '{{banner_heading}}'}
                        onChange={(e) => updateEffectParams(effectMeta.type, { heading: e.target.value })}
                        placeholder="{{banner_heading}}"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                      />
                      <p className="text-xs text-gray-500 mt-1">
                        💡 Use <code className="bg-gray-100 px-1 rounded">{'{{banner_heading}}'}</code> for dynamic text
                      </p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Scrolling Ticker Text
                        <span className="text-xs text-gray-500 ml-2">(Bottom tier - scrolling)</span>
                      </label>
                      <input
                        type="text"
                        value={effectConfig.params.ticker || '{{banner_ticker}}'}
                        onChange={(e) => updateEffectParams(effectMeta.type, { ticker: e.target.value })}
                        placeholder="{{banner_ticker}}"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                      />
                      <p className="text-xs text-gray-500 mt-1">
                        💡 Use <code className="bg-gray-100 px-1 rounded">{'{{banner_ticker}}'}</code> for dynamic text
                      </p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Banner Height (px)</label>
                      <input
                        type="number"
                        step="10"
                        min="60"
                        max="200"
                        value={effectConfig.params.height || 120}
                        onChange={(e) => updateEffectParams(effectMeta.type, { height: parseInt(e.target.value) })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Background Color</label>
                      <div className="flex gap-2">
                        <input
                          type="color"
                          value={effectConfig.params.background_color || '#1a1a1a'}
                          onChange={(e) => updateEffectParams(effectMeta.type, { background_color: e.target.value })}
                          className="h-10 w-20 border border-gray-300 rounded-lg cursor-pointer"
                        />
                        <input
                          type="text"
                          value={effectConfig.params.background_color || '#1a1a1a'}
                          onChange={(e) => updateEffectParams(effectMeta.type, { background_color: e.target.value })}
                          placeholder="#1a1a1a"
                          className="flex-1 px-3 py-2 border border-gray-300 rounded-lg font-mono text-sm"
                        />
                      </div>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Opacity</label>
                      <input
                        type="number"
                        step="0.1"
                        min="0"
                        max="1"
                        value={effectConfig.params.opacity || 0.9}
                        onChange={(e) => updateEffectParams(effectMeta.type, { opacity: parseFloat(e.target.value) })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                      />
                    </div>
                  </>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};

const MusicSection = ({ config, updateConfig }) => {
  const [uploading, setUploading] = React.useState(false);
  const [uploadError, setUploadError] = React.useState('');
  const fileInputRef = React.useRef(null);

  const updateMusic = (updates) => {
    console.log('updateMusic called with:', updates);
    console.log('Current background_music config:', config.background_music);
    const newMusicConfig = { ...config.background_music, ...updates };
    console.log('New background_music config:', newMusicConfig);
    updateConfig({ background_music: newMusicConfig });
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validate file type
    const allowedTypes = ['audio/mpeg', 'audio/wav', 'audio/mp4', 'audio/aac', 'audio/ogg', 'audio/flac'];
    const allowedExtensions = ['.mp3', '.wav', '.m4a', '.aac', '.ogg', '.flac'];
    const fileExt = '.' + file.name.split('.').pop().toLowerCase();

    if (!allowedTypes.includes(file.type) && !allowedExtensions.includes(fileExt)) {
      setUploadError('Invalid file type. Please upload an audio file (MP3, WAV, M4A, AAC, OGG, FLAC)');
      return;
    }

    // Validate file size (max 50MB)
    if (file.size > 50 * 1024 * 1024) {
      setUploadError('File too large. Maximum size is 50MB');
      return;
    }

    setUploading(true);
    setUploadError('');

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('http://localhost:8080/api/templates/upload/audio', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        },
        body: formData
      });

      const data = await response.json();

      if (data.status === 'success') {
        console.log('Audio uploaded successfully:', data.filename);
        updateMusic({ source: data.filename });
        setUploadError('');
        console.log('Background music config updated, source:', data.filename);
      } else {
        setUploadError(data.error || 'Upload failed');
      }
    } catch (error) {
      console.error('Upload error:', error);
      setUploadError('Upload failed: ' + error.message);
    } finally {
      setUploading(false);
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
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
          className="w-5 h-5 text-blue-600 rounded"
        />
        <label htmlFor="music-enabled" className="text-lg font-semibold text-gray-900">
          Enable Background Music
        </label>
      </div>

      {config.background_music.enabled && (
        <>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Music File</label>
            <div className="flex gap-2">
              <input
                type="text"
                value={config.background_music.source}
                onChange={(e) => updateMusic({ source: e.target.value })}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg"
                placeholder="music.mp3 or {{music_file}}"
              />
              <input
                ref={fileInputRef}
                type="file"
                accept=".mp3,.wav,.m4a,.aac,.ogg,.flac,audio/*"
                onChange={handleFileUpload}
                className="hidden"
              />
              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={uploading}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {uploading ? (
                  <>
                    <span className="animate-spin">⏳</span>
                    Uploading...
                  </>
                ) : (
                  <>
                    📁 Upload
                  </>
                )}
              </button>
            </div>
            {uploadError && (
              <p className="text-sm text-red-600 mt-1">{uploadError}</p>
            )}
            {config.background_music.source && !uploadError && (
              <p className="text-sm text-green-600 mt-1">✓ {config.background_music.source}</p>
            )}
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
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Fade In (seconds)
                <span className="ml-2 text-xs text-gray-500" title="Audio gradually increases from 0% to full volume">ℹ️</span>
              </label>
              <input
                type="number"
                min="0"
                step="0.5"
                value={config.background_music.fade_in}
                onChange={(e) => updateMusic({ fade_in: parseFloat(e.target.value) })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                placeholder="e.g., 2.0"
              />
              <p className="text-xs text-gray-500 mt-1">Audio starts silent, gradually increases to full volume</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Fade Out (seconds)
                <span className="ml-2 text-xs text-gray-500" title="Audio gradually decreases from full volume to 0%">ℹ️</span>
              </label>
              <input
                type="number"
                min="0"
                step="0.5"
                value={config.background_music.fade_out}
                onChange={(e) => updateMusic({ fade_out: parseFloat(e.target.value) })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                placeholder="e.g., 3.0"
              />
              <p className="text-xs text-gray-500 mt-1">Audio gradually decreases to silent at the end</p>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

const LogoSection = ({ config, updateConfig }) => {
  const [logoUploading, setLogoUploading] = React.useState(false);
  const [logoUploadError, setLogoUploadError] = React.useState('');
  const logoFileInputRef = React.useRef(null);

  const updateLogo = (updates) => {
    updateConfig({ logo: { ...config.logo, ...updates } });
  };

  const handleLogoUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Validate file type
    const validTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/svg+xml'];
    if (!validTypes.includes(file.type)) {
      setLogoUploadError('Please upload a valid image file (PNG, JPG, GIF, or SVG)');
      return;
    }

    // Validate file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
      setLogoUploadError('File size must be less than 5MB');
      return;
    }

    setLogoUploading(true);
    setLogoUploadError('');

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('http://localhost:8080/api/templates/upload/logo', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        },
        body: formData
      });

      const data = await response.json();

      if (data.status === 'success') {
        updateLogo({ source: data.filename });
        setLogoUploadError('');
      } else {
        setLogoUploadError(data.error || 'Upload failed');
      }
    } catch (error) {
      console.error('Logo upload error:', error);
      setLogoUploadError('Failed to upload logo');
    } finally {
      setLogoUploading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <input
          type="checkbox"
          id="logo-enabled"
          checked={config.logo.enabled}
          onChange={(e) => updateLogo({ enabled: e.target.checked })}
          className="w-5 h-5 text-blue-600 rounded"
        />
        <label htmlFor="logo-enabled" className="text-lg font-semibold text-gray-900">
          Enable Logo Watermark
        </label>
      </div>

      {config.logo.enabled && (
        <>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Logo Image</label>
            <div className="flex gap-2">
              <input
                type="text"
                value={config.logo.source}
                onChange={(e) => updateLogo({ source: e.target.value })}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg"
                placeholder="logo.png or {{logo_path}}"
              />
              <input
                ref={logoFileInputRef}
                type="file"
                accept="image/png,image/jpeg,image/jpg,image/gif,image/svg+xml"
                onChange={handleLogoUpload}
                className="hidden"
              />
              <button
                onClick={() => logoFileInputRef.current?.click()}
                disabled={logoUploading}
                className={`px-4 py-2 rounded-lg font-medium text-white ${
                  logoUploading
                    ? 'bg-gray-400 cursor-not-allowed'
                    : 'bg-blue-600 hover:bg-blue-700'
                }`}
              >
                {logoUploading ? '⏳ Uploading...' : '📁 Upload'}
              </button>
            </div>
            {logoUploadError && (
              <p className="text-sm text-red-600 mt-1">{logoUploadError}</p>
            )}
            {config.logo.source && !logoUploadError && (
              <p className="text-sm text-green-600 mt-1">✓ {config.logo.source}</p>
            )}
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
                      ? 'border-blue-600 bg-blue-50 text-blue-900'
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

const ThumbnailSection = ({ config, updateConfig, previewUrl }) => {
  const [thumbnailUrl, setThumbnailUrl] = React.useState(null);
  const [thumbnailLoading, setThumbnailLoading] = React.useState(false);
  const [thumbnailError, setThumbnailError] = React.useState('');

  const updateThumbnail = (updates) => {
    updateConfig({ thumbnail: { ...config.thumbnail, ...updates } });
  };

  const generateThumbnail = async () => {
    if (!previewUrl) {
      setThumbnailError('Please generate a video preview first');
      return;
    }

    if (!config.thumbnail.auto_generate) {
      setThumbnailError('Auto-generate must be enabled to preview thumbnail');
      return;
    }

    setThumbnailLoading(true);
    setThumbnailError('');

    try {
      // Extract path from full URL if needed
      let videoPath = previewUrl;
      if (videoPath.startsWith('http://')) {
        const url = new URL(videoPath);
        videoPath = url.pathname; // Extract just the path part
      }

      console.log('🖼️ Generating thumbnail from video:', videoPath);

      const response = await fetch('http://localhost:8080/api/templates/preview/thumbnail', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        },
        body: JSON.stringify({
          video_path: videoPath,
          timestamp: config.thumbnail.timestamp || 2.0,
          aspect_ratio: config.aspect_ratio || '16:9',
          text: config.thumbnail.text?.enabled ? config.thumbnail.text : null,
          variables: config.variables || {}
        })
      });

      const data = await response.json();

      if (data.status === 'success') {
        // Add cache buster to force reload
        setThumbnailUrl(`http://localhost:8080${data.thumbnail_url}?t=${Date.now()}`);
        setThumbnailError('');
      } else {
        setThumbnailError(data.error || 'Failed to generate thumbnail');
      }
    } catch (error) {
      console.error('Thumbnail generation error:', error);
      setThumbnailError('Failed to generate thumbnail');
    } finally {
      setThumbnailLoading(false);
    }
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
          className="w-5 h-5 text-blue-600 rounded"
        />
        <label htmlFor="auto-thumbnail" className="text-lg font-semibold text-gray-900">
          Auto-Generate Thumbnail
        </label>
      </div>

      {config.thumbnail.auto_generate ? (
        <>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Timestamp (seconds)
              <span className="ml-2 text-xs text-gray-500">
                ℹ️ Frame to extract from video
              </span>
            </label>
            <input
              type="number"
              min="0"
              step="0.5"
              value={config.thumbnail.timestamp}
              onChange={(e) => updateThumbnail({ timestamp: parseFloat(e.target.value) })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg"
              placeholder="e.g., 2.0"
            />
            <p className="text-xs text-gray-500 mt-1">
              The system will extract a frame at this timestamp to use as the video thumbnail
            </p>
          </div>

          {/* Text Overlay Configuration */}
          <div className="border-t pt-4 mt-4">
            <div className="flex items-center gap-3 mb-3">
              <input
                type="checkbox"
                id="thumbnail-text-enabled"
                checked={config.thumbnail.text?.enabled || false}
                onChange={(e) => updateThumbnail({
                  text: {
                    ...(config.thumbnail.text || {}),
                    enabled: e.target.checked,
                    // Set default values when enabling
                    ...(e.target.checked && !config.thumbnail.text?.title && {
                      title: '{{title}}',
                      subtitle: '{{date}}'
                    })
                  }
                })}
                className="w-5 h-5 text-blue-600 rounded"
              />
              <label htmlFor="thumbnail-text-enabled" className="text-sm font-semibold text-gray-900">
                📝 Add Text Overlay to Thumbnail
              </label>
            </div>

            {config.thumbnail.text?.enabled && (
              <div className="space-y-4 ml-8">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Title Text
                    <span className="ml-2 text-xs text-gray-500">Main heading on thumbnail</span>
                  </label>
                  <input
                    type="text"
                    value={config.thumbnail.text.title || ''}
                    onChange={(e) => updateThumbnail({
                      text: { ...config.thumbnail.text, title: e.target.value }
                    })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                    placeholder="e.g., TOP 20 NEWS or {{title}}"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Subtitle Text
                    <span className="ml-2 text-xs text-gray-500">Optional secondary text</span>
                  </label>
                  <input
                    type="text"
                    value={config.thumbnail.text.subtitle || ''}
                    onChange={(e) => updateThumbnail({
                      text: { ...config.thumbnail.text, subtitle: e.target.value }
                    })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                    placeholder="e.g., Current date or {{date}}"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Position</label>
                    <select
                      value={config.thumbnail.text.position || 'top-left'}
                      onChange={(e) => updateThumbnail({
                        text: { ...config.thumbnail.text, position: e.target.value }
                      })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                    >
                      <option value="top-left">Top Left</option>
                      <option value="top-right">Top Right</option>
                      <option value="bottom-left">Bottom Left</option>
                      <option value="bottom-right">Bottom Right</option>
                      <option value="center">Center</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Font Size</label>
                    <input
                      type="number"
                      min="20"
                      max="150"
                      value={config.thumbnail.text.font_size || 88}
                      onChange={(e) => updateThumbnail({
                        text: { ...config.thumbnail.text, font_size: parseInt(e.target.value) }
                      })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Title Color</label>
                    <input
                      type="color"
                      value={config.thumbnail.text.title_color || '#FFFFFF'}
                      onChange={(e) => updateThumbnail({
                        text: { ...config.thumbnail.text, title_color: e.target.value }
                      })}
                      className="w-full h-10 border border-gray-300 rounded-lg"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Subtitle Color</label>
                    <input
                      type="color"
                      value={config.thumbnail.text.subtitle_color || '#FFFFFF'}
                      onChange={(e) => updateThumbnail({
                        text: { ...config.thumbnail.text, subtitle_color: e.target.value }
                      })}
                      className="w-full h-10 border border-gray-300 rounded-lg"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Background Color</label>
                    <input
                      type="color"
                      value={config.thumbnail.text.background_color || '#003399'}
                      onChange={(e) => updateThumbnail({
                        text: { ...config.thumbnail.text, background_color: e.target.value }
                      })}
                      className="w-full h-10 border border-gray-300 rounded-lg"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Background Opacity</label>
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.1"
                      value={config.thumbnail.text.background_opacity || 0.9}
                      onChange={(e) => updateThumbnail({
                        text: { ...config.thumbnail.text, background_opacity: parseFloat(e.target.value) }
                      })}
                      className="w-full"
                    />
                    <span className="text-xs text-gray-500">{config.thumbnail.text.background_opacity || 0.9}</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          <div>
            <button
              onClick={generateThumbnail}
              disabled={thumbnailLoading || !previewUrl}
              className={`w-full px-4 py-2 rounded-lg font-medium text-white ${
                thumbnailLoading || !previewUrl
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-pink-600 hover:bg-pink-700'
              }`}
            >
              {thumbnailLoading ? '⏳ Generating Thumbnail...' : '🖼️ Generate Thumbnail Preview'}
            </button>
            {!previewUrl && (
              <p className="text-xs text-amber-600 mt-1">
                ⚠️ Generate a video preview first to see thumbnail
              </p>
            )}
          </div>

          {thumbnailError && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3">
              <p className="text-sm text-red-800">{thumbnailError}</p>
            </div>
          )}

          {thumbnailUrl && (
            <div className="border border-gray-300 rounded-lg p-4 bg-gray-50">
              <h5 className="text-sm font-medium text-gray-700 mb-2">Thumbnail Preview:</h5>
              <img
                src={thumbnailUrl}
                alt="Thumbnail preview"
                className="w-full rounded-lg shadow-md"
              />
              <p className="text-xs text-gray-500 mt-2">
                ✓ Extracted at {config.thumbnail.timestamp}s
              </p>
            </div>
          )}
        </>
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
          <p className="text-xs text-gray-500 mt-1">
            Provide a custom thumbnail image path or use a variable
          </p>
        </div>
      )}
    </div>
  );
};

const LayersSection = ({ config, updateConfig }) => {
  const [selectedLayerId, setSelectedLayerId] = React.useState(null);
  const [layerError, setLayerError] = React.useState(null);
  const layers = config.layers || [];

  // Check if video or image layer already exists
  const hasVideoLayer = layers.some(layer => layer.type === 'video');
  const hasImageLayer = layers.some(layer => layer.type === 'image');

  const addLayer = (type) => {
    // Clear previous errors
    setLayerError(null);

    // Prevent adding image layer if video layer exists
    if (type === 'image' && hasVideoLayer) {
      setLayerError('Cannot add image overlay when a video layer exists. Video and image overlays cannot be used together.');
      return;
    }

    // Prevent adding video layer if image layer exists
    if (type === 'video' && hasImageLayer) {
      setLayerError('Cannot add video layer when an image overlay exists. Video and image overlays cannot be used together.');
      return;
    }

    const newLayer = {
      id: `layer_${Date.now()}`,
      type: type,
      source: '',
      z_index: layers.length,
      position: { x: 0.5, y: 0.5 },
      size: { width: type === 'video' || type === 'image' ? 1.0 : 0.5, height: type === 'video' || type === 'image' ? 1.0 : 0.3 },
      duration: null,
      start_time: 0,
      opacity: 1.0,
      // Type-specific properties
      ...(type === 'text' && {
        content: '{{overlay_text}}',
        font: {
          family: 'Arial',
          size: 48,
          color: '#FFFFFF',
          weight: 'bold'
        },
        fade: {
          enabled: false,
          fade_in_duration: 0.5,
          fade_out_duration: 0.5,
          fade_type: 'both'
        }
      }),
      ...(type === 'shape' && {
        shape_type: 'rectangle',
        fill_color: '#3B82F6',
        stroke_color: '#1E40AF',
        stroke_width: 2
      })
    };

    updateConfig({ layers: [...layers, newLayer] }, true);
    setSelectedLayerId(newLayer.id);
  };

  const updateLayer = (layerId, updates) => {
    const updatedLayers = layers.map(layer =>
      layer.id === layerId ? { ...layer, ...updates } : layer
    );
    updateConfig({ layers: updatedLayers }, true);
  };

  const deleteLayer = (layerId) => {
    const updatedLayers = layers.filter(layer => layer.id !== layerId);
    updateConfig({ layers: updatedLayers }, true);
    if (selectedLayerId === layerId) {
      setSelectedLayerId(null);
    }
  };

  const moveLayer = (layerId, direction) => {
    const index = layers.findIndex(l => l.id === layerId);
    if (index === -1) return;

    const newLayers = [...layers];
    const targetIndex = direction === 'up' ? index - 1 : index + 1;

    if (targetIndex < 0 || targetIndex >= newLayers.length) return;

    // Swap layers
    [newLayers[index], newLayers[targetIndex]] = [newLayers[targetIndex], newLayers[index]];

    // Update z_index
    newLayers.forEach((layer, idx) => {
      layer.z_index = idx;
    });

    updateConfig({ layers: newLayers }, true);
  };

  const selectedLayer = layers.find(l => l.id === selectedLayerId);

  return (
    <div className="space-y-6">
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="font-medium text-blue-900 mb-2">🎨 Layers</h4>
        <p className="text-sm text-blue-800">
          Build your video by stacking layers. Each layer can be a background video, image, text, or shape.
        </p>
      </div>

      {/* Layer Error Message */}
      {layerError && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-start gap-2">
          <span className="text-xl">⚠️</span>
          <div className="flex-1">
            <p className="text-sm">{layerError}</p>
          </div>
          <button
            onClick={() => setLayerError(null)}
            className="text-red-400 hover:text-red-600"
          >
            ✕
          </button>
        </div>
      )}

      {/* Add Layer Buttons */}
      <div>
        <h5 className="text-sm font-medium text-gray-700 mb-3">Add New Layer:</h5>
        <div className="grid grid-cols-2 gap-3">
          {/* Background Video Button */}
          <div className="relative group">
            <button
              onClick={() => addLayer('video')}
              disabled={hasImageLayer}
              className={`w-full px-4 py-3 rounded-lg font-medium text-sm ${
                hasImageLayer
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : 'bg-purple-600 text-white hover:bg-purple-700'
              }`}
            >
              🎥 Background Video
            </button>
            {hasImageLayer && (
              <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-10">
                Cannot add video layer when image overlay exists
                <div className="absolute top-full left-1/2 transform -translate-x-1/2 -mt-1 border-4 border-transparent border-t-gray-900"></div>
              </div>
            )}
          </div>

          {/* Image Overlay Button */}
          <div className="relative group">
            <button
              onClick={() => addLayer('image')}
              disabled={hasVideoLayer}
              className={`w-full px-4 py-3 rounded-lg font-medium text-sm ${
                hasVideoLayer
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              }`}
            >
              🖼️ Image Overlay
            </button>
            {hasVideoLayer && (
              <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-10">
                Cannot add image overlay when video layer exists
                <div className="absolute top-full left-1/2 transform -translate-x-1/2 -mt-1 border-4 border-transparent border-t-gray-900"></div>
              </div>
            )}
          </div>

          {/* Text Overlay Button */}
          <button
            onClick={() => addLayer('text')}
            className="px-4 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium text-sm"
          >
            📝 Text Overlay
          </button>

          {/* Shape/Graphics Button */}
          <button
            onClick={() => addLayer('shape')}
            className="px-4 py-3 bg-orange-600 text-white rounded-lg hover:bg-orange-700 font-medium text-sm"
          >
            ⬛ Shape/Graphics
          </button>
        </div>
      </div>

      {/* Layer List */}
      {layers.length > 0 && (
        <div>
          <h5 className="text-sm font-medium text-gray-700 mb-3">Layers (bottom to top):</h5>
          <div className="space-y-2">
            {layers.map((layer, index) => (
              <div
                key={layer.id}
                onClick={() => setSelectedLayerId(layer.id)}
                className={`p-3 border rounded-lg cursor-pointer transition-all ${
                  selectedLayerId === layer.id
                    ? 'border-blue-500 bg-blue-50 shadow-md'
                    : 'border-gray-300 bg-white hover:border-gray-400'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">
                      {layer.type === 'video' && '🎥'}
                      {layer.type === 'image' && '🖼️'}
                      {layer.type === 'text' && '📝'}
                      {layer.type === 'shape' && '⬛'}
                    </span>
                    <div>
                      <div className="font-medium text-gray-900">
                        {layer.type.charAt(0).toUpperCase() + layer.type.slice(1)} Layer
                      </div>
                      <div className="text-xs text-gray-500">
                        z-index: {layer.z_index} | opacity: {(layer.opacity * 100).toFixed(0)}%
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={(e) => { e.stopPropagation(); moveLayer(layer.id, 'up'); }}
                      disabled={index === layers.length - 1}
                      className="px-2 py-1 text-gray-600 hover:text-gray-900 disabled:opacity-30"
                      title="Move up"
                    >
                      ↑
                    </button>
                    <button
                      onClick={(e) => { e.stopPropagation(); moveLayer(layer.id, 'down'); }}
                      disabled={index === 0}
                      className="px-2 py-1 text-gray-600 hover:text-gray-900 disabled:opacity-30"
                      title="Move down"
                    >
                      ↓
                    </button>
                    <button
                      onClick={(e) => { e.stopPropagation(); deleteLayer(layer.id); }}
                      className="px-2 py-1 text-red-600 hover:text-red-900"
                      title="Delete layer"
                    >
                      🗑️
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Layer Editor */}
      {selectedLayer && (
        <div className="border-t pt-6">
          <h5 className="text-lg font-semibold text-gray-900 mb-4">
            Edit {selectedLayer.type.charAt(0).toUpperCase() + selectedLayer.type.slice(1)} Layer
          </h5>
          <LayerEditor layer={selectedLayer} updateLayer={updateLayer} />
        </div>
      )}

      {layers.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          <div className="text-4xl mb-2">🎨</div>
          <p>No layers yet. Add your first layer above!</p>
        </div>
      )}
    </div>
  );
};

const LayerEditor = ({ layer, updateLayer }) => {
  const [uploadingFile, setUploadingFile] = React.useState(false);

  const handleFileUpload = async (e, fieldName) => {
    const file = e.target.files[0];
    if (!file) return;

    // Validate file type based on layer type
    const validTypes = {
      video: ['video/mp4', 'video/webm', 'video/ogg'],
      image: ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/svg+xml']
    };

    if (layer.type === 'video' || layer.type === 'image') {
      if (!validTypes[layer.type].includes(file.type)) {
        alert(`Invalid file type. Please upload a ${layer.type} file.`);
        return;
      }
    }

    // Max file size: 50MB for videos, 5MB for images
    const maxSize = layer.type === 'video' ? 50 * 1024 * 1024 : 5 * 1024 * 1024;
    if (file.size > maxSize) {
      alert(`File too large. Maximum size is ${layer.type === 'video' ? '50MB' : '5MB'}.`);
      return;
    }

    setUploadingFile(true);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const endpoint = layer.type === 'video'
        ? 'http://localhost:8080/api/templates/upload/video'
        : 'http://localhost:8080/api/templates/upload/image';

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        },
        body: formData
      });

      const data = await response.json();

      if (data.status === 'success') {
        updateLayer(layer.id, { [fieldName]: data.filename });
      } else {
        alert(`Upload failed: ${data.error || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Upload error:', error);
      alert('Upload failed. Please try again.');
    } finally {
      setUploadingFile(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Common Properties */}
      <div className="grid grid-cols-2 gap-4">
        {/* Source */}
        {(layer.type === 'video' || layer.type === 'image') && (
          <div className="col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {layer.type === 'video' ? 'Video File' : 'Image File'}
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={layer.source}
                onChange={(e) => updateLayer(layer.id, { source: e.target.value })}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm"
                placeholder={`filename.${layer.type === 'video' ? 'mp4' : 'png'} or {{variable}}`}
              />
              <label className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 cursor-pointer text-sm font-medium">
                {uploadingFile ? '⏳' : '📁'} Upload
                <input
                  type="file"
                  accept={layer.type === 'video' ? 'video/*' : 'image/*'}
                  onChange={(e) => handleFileUpload(e, 'source')}
                  className="hidden"
                  disabled={uploadingFile}
                />
              </label>
            </div>
          </div>
        )}

        {/* Text Content */}
        {layer.type === 'text' && (
          <div className="col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-2">Text Content</label>
            <textarea
              value={layer.content}
              onChange={(e) => updateLayer(layer.id, { content: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
              rows="3"
              placeholder="Enter text or use {{variable}}"
            />
          </div>
        )}

        {/* Position */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Position X (0-1)
            <span className="ml-2 text-xs text-gray-500">0=left, 0.5=center, 1=right</span>
          </label>
          <input
            type="number"
            min="0"
            max="1"
            step="0.05"
            value={layer.position.x}
            onChange={(e) => updateLayer(layer.id, { position: { ...layer.position, x: parseFloat(e.target.value) } })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Position Y (0-1)
            <span className="ml-2 text-xs text-gray-500">0=top, 0.5=middle, 1=bottom</span>
          </label>
          <input
            type="number"
            min="0"
            max="1"
            step="0.05"
            value={layer.position.y}
            onChange={(e) => updateLayer(layer.id, { position: { ...layer.position, y: parseFloat(e.target.value) } })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
          />
        </div>

        {/* Size */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Width (0-1)
            <span className="ml-2 text-xs text-gray-500">Relative to video width</span>
          </label>
          <input
            type="number"
            min="0.1"
            max="1"
            step="0.05"
            value={layer.size.width}
            onChange={(e) => updateLayer(layer.id, { size: { ...layer.size, width: parseFloat(e.target.value) } })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Height (0-1)
            <span className="ml-2 text-xs text-gray-500">Relative to video height</span>
          </label>
          <input
            type="number"
            min="0.1"
            max="1"
            step="0.05"
            value={layer.size.height}
            onChange={(e) => updateLayer(layer.id, { size: { ...layer.size, height: parseFloat(e.target.value) } })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
          />
        </div>

        {/* Timing */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Start Time (seconds)
          </label>
          <input
            type="number"
            min="0"
            step="0.5"
            value={layer.start_time}
            onChange={(e) => updateLayer(layer.id, { start_time: parseFloat(e.target.value) })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Duration (seconds)
            <span className="ml-2 text-xs text-gray-500">Leave empty for auto</span>
          </label>
          <input
            type="number"
            min="0"
            step="0.5"
            value={layer.duration || ''}
            onChange={(e) => updateLayer(layer.id, { duration: e.target.value ? parseFloat(e.target.value) : null })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
            placeholder="auto"
          />
        </div>

        {/* Opacity */}
        <div className="col-span-2">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Opacity: {(layer.opacity * 100).toFixed(0)}%
          </label>
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={layer.opacity}
            onChange={(e) => updateLayer(layer.id, { opacity: parseFloat(e.target.value) })}
            className="w-full"
          />
        </div>
      </div>

      {/* Text-specific properties */}
      {layer.type === 'text' && layer.font && (
        <>
          <div className="border-t pt-4 mt-4">
            <h6 className="text-sm font-semibold text-gray-900 mb-3">Text Styling</h6>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Font Family</label>
                <select
                  value={layer.font.family}
                  onChange={(e) => updateLayer(layer.id, { font: { ...layer.font, family: e.target.value } })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                >
                  <option value="Arial">Arial</option>
                  <option value="Helvetica">Helvetica</option>
                  <option value="Times New Roman">Times New Roman</option>
                  <option value="Courier New">Courier New</option>
                  <option value="Georgia">Georgia</option>
                  <option value="Verdana">Verdana</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Font Size (px)</label>
                <input
                  type="number"
                  min="12"
                  max="200"
                  value={layer.font.size}
                  onChange={(e) => updateLayer(layer.id, { font: { ...layer.font, size: parseInt(e.target.value) } })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Font Color</label>
                <input
                  type="color"
                  value={layer.font.color}
                  onChange={(e) => updateLayer(layer.id, { font: { ...layer.font, color: e.target.value } })}
                  className="w-full h-10 border border-gray-300 rounded-lg"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Font Weight</label>
                <select
                  value={layer.font.weight}
                  onChange={(e) => updateLayer(layer.id, { font: { ...layer.font, weight: e.target.value } })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                >
                  <option value="normal">Normal</option>
                  <option value="bold">Bold</option>
                </select>
              </div>
            </div>
          </div>

          {/* Fade Animation Controls */}
          <div className="border-t pt-4 mt-4">
            <div className="flex items-center gap-3 mb-3">
              <input
                type="checkbox"
                id={`fade-${layer.id}`}
                checked={layer.fade?.enabled || false}
                onChange={(e) => updateLayer(layer.id, {
                  fade: {
                    ...(layer.fade || {}),
                    enabled: e.target.checked,
                    fade_in_duration: layer.fade?.fade_in_duration || 0.5,
                    fade_out_duration: layer.fade?.fade_out_duration || 0.5,
                    fade_type: layer.fade?.fade_type || 'both'
                  }
                })}
                className="w-5 h-5 text-blue-600 rounded"
              />
              <label htmlFor={`fade-${layer.id}`} className="text-sm font-semibold text-gray-900">
                ✨ Enable Fade Animation
              </label>
            </div>

            {layer.fade?.enabled && (
              <div className="grid grid-cols-2 gap-4 ml-8">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Fade In (seconds)
                    <span className="ml-2 text-xs text-gray-500">Duration of fade in</span>
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    max="5"
                    value={layer.fade.fade_in_duration}
                    onChange={(e) => updateLayer(layer.id, {
                      fade: { ...layer.fade, fade_in_duration: parseFloat(e.target.value) }
                    })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Fade Out (seconds)
                    <span className="ml-2 text-xs text-gray-500">Duration of fade out</span>
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    max="5"
                    value={layer.fade.fade_out_duration}
                    onChange={(e) => updateLayer(layer.id, {
                      fade: { ...layer.fade, fade_out_duration: parseFloat(e.target.value) }
                    })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                  />
                </div>

                <div className="col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-2">Fade Type</label>
                  <select
                    value={layer.fade.fade_type}
                    onChange={(e) => updateLayer(layer.id, {
                      fade: { ...layer.fade, fade_type: e.target.value }
                    })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                  >
                    <option value="in">Fade In Only</option>
                    <option value="out">Fade Out Only</option>
                    <option value="both">Both Fade In & Out</option>
                  </select>
                </div>
              </div>
            )}
          </div>
        </>
      )}

      {/* Shape-specific properties */}
      {layer.type === 'shape' && (
        <div className="border-t pt-4 mt-4">
          <h6 className="text-sm font-semibold text-gray-900 mb-3">Shape Styling</h6>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Shape Type</label>
              <select
                value={layer.shape_type}
                onChange={(e) => updateLayer(layer.id, { shape_type: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
              >
                <option value="rectangle">Rectangle</option>
                <option value="circle">Circle</option>
                <option value="line">Line</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Fill Color</label>
              <input
                type="color"
                value={layer.fill_color}
                onChange={(e) => updateLayer(layer.id, { fill_color: e.target.value })}
                className="w-full h-10 border border-gray-300 rounded-lg"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Stroke Color</label>
              <input
                type="color"
                value={layer.stroke_color}
                onChange={(e) => updateLayer(layer.id, { stroke_color: e.target.value })}
                className="w-full h-10 border border-gray-300 rounded-lg"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Stroke Width (px)</label>
              <input
                type="number"
                min="0"
                max="20"
                value={layer.stroke_width}
                onChange={(e) => updateLayer(layer.id, { stroke_width: parseInt(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const VariablesSection = ({ config, updateConfig }) => {
  const variables = config.variables || {};

  // Predefined list of common variables
  const predefinedVariables = [
    {
      name: 'title',
      type: 'text',
      description: 'Main title text for video and thumbnail',
      defaultValue: 'Breaking News',
      category: 'Text Content'
    },
    {
      name: 'overlay_text',
      type: 'text',
      description: 'Text for overlay on video',
      defaultValue: 'Sample Overlay Text',
      category: 'Text Content'
    },
    {
      name: 'date',
      type: 'text',
      description: 'Date text for video and thumbnail',
      defaultValue: new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' }),
      category: 'Text Content'
    },
    {
      name: 'banner_heading',
      type: 'text',
      description: 'Static heading text for bottom banner',
      defaultValue: 'BREAKING NEWS',
      category: 'Text Content'
    },
    {
      name: 'banner_ticker',
      type: 'text',
      description: 'Scrolling ticker text for bottom banner',
      defaultValue: 'Sample News Ticker • Latest Updates • Breaking Stories • ',
      category: 'Text Content'
    }
  ];

  const toggleVariable = (varName, enabled) => {
    if (enabled) {
      // Find the predefined variable config
      const predefined = predefinedVariables.find(v => v.name === varName);
      updateConfig({
        variables: {
          ...variables,
          [varName]: {
            type: predefined.type,
            required: false,
            default: predefined.defaultValue,
            description: predefined.description
          }
        }
      });
    } else {
      // Remove the variable
      const newVars = { ...variables };
      delete newVars[varName];
      updateConfig({ variables: newVars });
    }
  };

  const updateVariable = (varName, updates) => {
    updateConfig({
      variables: {
        ...variables,
        [varName]: {
          ...variables[varName],
          ...updates
        }
      }
    });
  };

  // Group variables by category
  const categories = [...new Set(predefinedVariables.map(v => v.category))];
  const groupedVariables = categories.map(category => ({
    category,
    variables: predefinedVariables.filter(v => v.category === category)
  }));

  return (
    <div className="space-y-6">
      <div className="bg-teal-50 border border-teal-200 rounded-lg p-4">
        <h4 className="font-medium text-teal-900 mb-2">🔧 Template Variables</h4>
        <p className="text-sm text-teal-800 mb-2">
          Select which variables you want to use in your template. These will be filled with actual values when generating videos.
        </p>
        <p className="text-xs text-teal-700">
          💡 Use variables with <code className="bg-teal-100 px-1 rounded">{'{{variable_name}}'}</code> syntax in text layers and thumbnail text.
        </p>
      </div>

      {/* Available Variables by Category */}
      {groupedVariables.map(({ category, variables: categoryVars }) => (
        <div key={category} className="space-y-3">
          <h5 className="text-md font-semibold text-gray-800 border-b pb-2">
            {category}
          </h5>

          <div className="space-y-2">
            {categoryVars.map((predefinedVar) => {
              const isEnabled = variables.hasOwnProperty(predefinedVar.name);
              const varConfig = variables[predefinedVar.name] || {};

              return (
                <div
                  key={predefinedVar.name}
                  className={`border-2 rounded-lg p-4 transition-all ${
                    isEnabled
                      ? 'border-teal-300 bg-teal-50'
                      : 'border-gray-200 bg-white'
                  }`}
                >
                  {/* Variable Header with Checkbox */}
                  <div className="flex items-start gap-3 mb-3">
                    <input
                      type="checkbox"
                      id={`var-${predefinedVar.name}`}
                      checked={isEnabled}
                      onChange={(e) => toggleVariable(predefinedVar.name, e.target.checked)}
                      className="w-5 h-5 text-teal-600 rounded mt-1"
                    />
                    <div className="flex-1">
                      <label
                        htmlFor={`var-${predefinedVar.name}`}
                        className="flex items-center gap-2 cursor-pointer"
                      >
                        <code className="text-sm font-mono bg-gray-100 px-2 py-1 rounded text-gray-800">
                          {'{{' + predefinedVar.name + '}}'}
                        </code>
                        <span className={`text-xs px-2 py-1 rounded ${
                          predefinedVar.type === 'text' ? 'bg-blue-100 text-blue-800' :
                          predefinedVar.type === 'color' ? 'bg-purple-100 text-purple-800' :
                          predefinedVar.type === 'image' ? 'bg-green-100 text-green-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {predefinedVar.type}
                        </span>
                      </label>
                      <p className="text-xs text-gray-600 mt-1">
                        {predefinedVar.description}
                      </p>
                    </div>
                  </div>

                  {/* Variable Configuration (shown when enabled) */}
                  {isEnabled && (
                    <div className="ml-8 space-y-3 pt-3 border-t border-teal-200">
                      <div className="grid grid-cols-2 gap-4">
                        <div className="flex items-center">
                          <input
                            type="checkbox"
                            id={`required-${predefinedVar.name}`}
                            checked={varConfig.required || false}
                            onChange={(e) => updateVariable(predefinedVar.name, { required: e.target.checked })}
                            className="w-4 h-4 text-teal-600 rounded mr-2"
                          />
                          <label htmlFor={`required-${predefinedVar.name}`} className="text-sm font-medium text-gray-700">
                            Required
                          </label>
                        </div>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Default Value
                          <span className="ml-2 text-xs text-gray-500">(Used when no value is provided during video generation)</span>
                        </label>
                        {predefinedVar.type === 'color' ? (
                          <div className="flex items-center gap-2">
                            <input
                              type="color"
                              value={varConfig.default || predefinedVar.defaultValue}
                              onChange={(e) => updateVariable(predefinedVar.name, { default: e.target.value })}
                              className="h-10 w-20 border border-gray-300 rounded-lg"
                            />
                            <input
                              type="text"
                              value={varConfig.default || predefinedVar.defaultValue}
                              onChange={(e) => updateVariable(predefinedVar.name, { default: e.target.value })}
                              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm font-mono"
                              placeholder="#000000"
                            />
                          </div>
                        ) : (
                          <input
                            type={predefinedVar.type === 'number' ? 'number' : 'text'}
                            value={varConfig.default || predefinedVar.defaultValue}
                            onChange={(e) => updateVariable(predefinedVar.name, { default: e.target.value })}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                            placeholder={`Default ${predefinedVar.type} value`}
                          />
                        )}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      ))}

      {/* Usage Guide */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h5 className="font-medium text-blue-900 mb-2">📝 How to Use Variables</h5>
        <div className="text-sm text-blue-800 space-y-2">
          <p>
            <strong>1. Enable Variables:</strong> Check the variables you want to use in your template.
          </p>
          <p>
            <strong>2. Use in Template:</strong> Add <code className="bg-blue-100 px-1 rounded">{'{{variable_name}}'}</code> in text layers or thumbnail text.
          </p>
          <p>
            <strong>3. During Video Generation:</strong> Provide actual values for these variables when creating videos.
          </p>
          <p className="text-xs text-blue-700 mt-2 pt-2 border-t border-blue-200">
            <strong>Example:</strong> Enable <code className="bg-blue-100 px-1 rounded">title</code> variable,
            use <code className="bg-blue-100 px-1 rounded">{'{{title}}'}</code> in a text layer,
            then provide "Breaking News" as the value when generating the video.
          </p>
        </div>
      </div>

      {/* Summary of Enabled Variables */}
      {Object.keys(variables).length > 0 && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <h5 className="font-medium text-green-900 mb-2">
            ✅ Enabled Variables ({Object.keys(variables).length})
          </h5>
          <div className="flex flex-wrap gap-2">
            {Object.keys(variables).map(varName => (
              <code key={varName} className="text-xs font-mono bg-green-100 px-2 py-1 rounded text-green-800">
                {'{{' + varName + '}}'}
              </code>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default TemplateWizard;

