import React, { useState, useEffect } from 'react';

const TemplateEditor = ({ template, onSave, onCancel }) => {
  const [formData, setFormData] = useState({
    template_id: '',
    name: '',
    category: 'news',
    description: '',
    version: '1.0.0',
    aspect_ratio: '16:9',
    resolution: { width: 1920, height: 1080 },
    layers: [],
    effects: [],
    background_music: {
      enabled: false,
      source: 'background_music.wav',
      volume: 0.15,
      fade_in: 3.0,
      fade_out: 2.0
    },
    logo: {
      enabled: false,
      source: 'logo.png',
      position: 'top-right',
      scale: 0.12,
      opacity: 0.9,
      margin: 30
    },
    thumbnail: {
      source: '',
      auto_generate: true,
      timestamp: 2.0
    },
    variables: {},
    metadata: {
      tags: [],
      thumbnail: ''
    }
  });

  const [currentTab, setCurrentTab] = useState('basic');
  const [errors, setErrors] = useState({});
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [previewError, setPreviewError] = useState(null);

  useEffect(() => {
    if (template) {
      setFormData(template);
    }
  }, [template]);

  const handleBasicInfoChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleResolutionChange = () => {
    const resolutions = {
      '16:9': { width: 1920, height: 1080 },
      '9:16': { width: 1080, height: 1920 },
      '1:1': { width: 1080, height: 1080 }
    };
    setFormData(prev => ({
      ...prev,
      resolution: resolutions[prev.aspect_ratio] || { width: 1920, height: 1080 }
    }));
  };

  const handleAddLayer = () => {
    const newLayer = {
      id: `layer_${Date.now()}`,
      type: 'rectangle',
      position: { x: 0, y: 0 },
      size: { width: 100, height: 100 },
      fill: '#000000',
      z_index: formData.layers.length
    };
    setFormData(prev => ({
      ...prev,
      layers: [...prev.layers, newLayer]
    }));
  };

  const handleLayerChange = (index, field, value) => {
    setFormData(prev => ({
      ...prev,
      layers: prev.layers.map((layer, i) => 
        i === index ? { ...layer, [field]: value } : layer
      )
    }));
  };

  const handleRemoveLayer = (index) => {
    setFormData(prev => ({
      ...prev,
      layers: prev.layers.filter((_, i) => i !== index)
    }));
  };

  const handleAddVariable = () => {
    const varName = prompt('Enter variable name (e.g., brand_color):');
    if (varName && !formData.variables[varName]) {
      setFormData(prev => ({
        ...prev,
        variables: {
          ...prev.variables,
          [varName]: {
            type: 'text',
            required: false,
            description: ''
          }
        }
      }));
    }
  };

  const handleVariableChange = (varName, field, value) => {
    setFormData(prev => ({
      ...prev,
      variables: {
        ...prev.variables,
        [varName]: {
          ...prev.variables[varName],
          [field]: value
        }
      }
    }));
  };

  const handleRemoveVariable = (varName) => {
    setFormData(prev => {
      const newVars = { ...prev.variables };
      delete newVars[varName];
      return { ...prev, variables: newVars };
    });
  };

  const handleAddTag = () => {
    const tag = prompt('Enter tag:');
    if (tag && !formData.metadata.tags.includes(tag)) {
      setFormData(prev => ({
        ...prev,
        metadata: {
          ...prev.metadata,
          tags: [...prev.metadata.tags, tag]
        }
      }));
    }
  };

  const handleRemoveTag = (tag) => {
    setFormData(prev => ({
      ...prev,
      metadata: {
        ...prev.metadata,
        tags: prev.metadata.tags.filter(t => t !== tag)
      }
    }));
  };

  const validateForm = () => {
    const newErrors = {};
    if (!formData.template_id) newErrors.template_id = 'Template ID is required';
    if (!formData.name) newErrors.name = 'Name is required';
    if (!formData.category) newErrors.category = 'Category is required';
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = () => {
    if (validateForm()) {
      onSave(formData);
    }
  };

  const handleGeneratePreview = async () => {
    setPreviewLoading(true);
    setPreviewError(null);
    setPreviewUrl(null);

    try {
      const response = await fetch('http://localhost:8080/api/templates/preview', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        },
        body: JSON.stringify({
          template: formData,
          sample_data: {} // Use default sample data
        })
      });

      const data = await response.json();

      if (response.ok && data.status === 'success') {
        setPreviewUrl(data.preview_url || data.video_path);
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

  const tabs = [
    { id: 'basic', name: 'Basic Info', icon: '📝' },
    { id: 'effects', name: 'Effects', icon: '✨' },
    { id: 'music', name: 'Background Music', icon: '🎵' },
    { id: 'logo', name: 'Logo', icon: '🏷️' },
    { id: 'thumbnail', name: 'Thumbnail', icon: '🖼️' },
    { id: 'layers', name: 'Layers', icon: '🎨' },
    { id: 'variables', name: 'Variables', icon: '🔧' },
    { id: 'metadata', name: 'Metadata', icon: '📋' },
    { id: 'preview', name: 'Preview', icon: '▶️' }
  ];

  return (
    <div className="flex flex-col h-full">
      {/* Tabs */}
      <div className="border-b border-gray-200 bg-gray-50">
        <nav className="flex space-x-4 px-6 py-3">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setCurrentTab(tab.id)}
              className={`
                flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm transition-colors
                ${currentTab === tab.id
                  ? 'bg-white text-indigo-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
                }
              `}
            >
              <span>{tab.icon}</span>
              {tab.name}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content - Scrollable */}
      <div className="flex-1 overflow-y-auto p-6">
        {currentTab === 'basic' && <BasicInfoTab formData={formData} onChange={handleBasicInfoChange} onResolutionChange={handleResolutionChange} errors={errors} />}
        {currentTab === 'effects' && <EffectsTab effects={formData.effects} onChange={(effects) => setFormData(prev => ({ ...prev, effects }))} />}
        {currentTab === 'music' && <BackgroundMusicTab music={formData.background_music} onChange={(music) => setFormData(prev => ({ ...prev, background_music: music }))} />}
        {currentTab === 'logo' && <LogoTab logo={formData.logo} onChange={(logo) => setFormData(prev => ({ ...prev, logo }))} />}
        {currentTab === 'thumbnail' && <ThumbnailTab thumbnail={formData.thumbnail} onChange={(thumbnail) => setFormData(prev => ({ ...prev, thumbnail }))} />}
        {currentTab === 'layers' && <LayersTab layers={formData.layers} onAdd={handleAddLayer} onChange={handleLayerChange} onRemove={handleRemoveLayer} />}
        {currentTab === 'variables' && <VariablesTab variables={formData.variables} onAdd={handleAddVariable} onChange={handleVariableChange} onRemove={handleRemoveVariable} />}
        {currentTab === 'metadata' && <MetadataTab metadata={formData.metadata} onAddTag={handleAddTag} onRemoveTag={handleRemoveTag} onChange={(field, value) => setFormData(prev => ({ ...prev, metadata: { ...prev.metadata, [field]: value } }))} />}
        {currentTab === 'preview' && (
          <PreviewTab
            previewUrl={previewUrl}
            previewLoading={previewLoading}
            previewError={previewError}
            onGeneratePreview={handleGeneratePreview}
          />
        )}
      </div>

      {/* Footer Actions */}
      <div className="border-t border-gray-200 p-6 bg-gray-50 flex justify-end gap-3">
        <button
          onClick={onCancel}
          className="px-6 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 font-medium"
        >
          Cancel
        </button>
        <button
          onClick={handleSubmit}
          className="px-6 py-2 text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 font-medium"
        >
          Save Template
        </button>
      </div>
    </div>
  );
};

// Basic Info Tab
const BasicInfoTab = ({ formData, onChange, onResolutionChange, errors }) => (
  <div className="space-y-6">
    <div className="grid grid-cols-2 gap-6">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Template ID <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          value={formData.template_id}
          onChange={(e) => onChange('template_id', e.target.value)}
          className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 ${errors.template_id ? 'border-red-500' : 'border-gray-300'}`}
          placeholder="e.g., modern_news_v1"
        />
        {errors.template_id && <p className="text-red-500 text-sm mt-1">{errors.template_id}</p>}
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Name <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          value={formData.name}
          onChange={(e) => onChange('name', e.target.value)}
          className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 ${errors.name ? 'border-red-500' : 'border-gray-300'}`}
          placeholder="e.g., Modern News"
        />
        {errors.name && <p className="text-red-500 text-sm mt-1">{errors.name}</p>}
      </div>
    </div>

    <div className="grid grid-cols-2 gap-6">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Category <span className="text-red-500">*</span>
        </label>
        <select
          value={formData.category}
          onChange={(e) => onChange('category', e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
        >
          <option value="news">News Videos</option>
          <option value="shorts">YouTube Shorts</option>
          <option value="ecommerce">E-commerce</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Version</label>
        <input
          type="text"
          value={formData.version}
          onChange={(e) => onChange('version', e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
          placeholder="1.0.0"
        />
      </div>
    </div>

    <div>
      <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
      <textarea
        value={formData.description}
        onChange={(e) => onChange('description', e.target.value)}
        rows={3}
        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
        placeholder="Describe this template..."
      />
    </div>

    <div className="grid grid-cols-2 gap-6">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Aspect Ratio</label>
        <select
          value={formData.aspect_ratio}
          onChange={(e) => {
            onChange('aspect_ratio', e.target.value);
            onResolutionChange();
          }}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
        >
          <option value="16:9">16:9 (Landscape)</option>
          <option value="9:16">9:16 (Portrait)</option>
          <option value="1:1">1:1 (Square)</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Resolution</label>
        <div className="flex items-center gap-2">
          <input
            type="number"
            value={formData.resolution.width}
            onChange={(e) => onChange('resolution', { ...formData.resolution, width: parseInt(e.target.value) })}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
          />
          <span className="text-gray-500">×</span>
          <input
            type="number"
            value={formData.resolution.height}
            onChange={(e) => onChange('resolution', { ...formData.resolution, height: parseInt(e.target.value) })}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
          />
        </div>
      </div>
    </div>
  </div>
);

// Layers Tab
const LayersTab = ({ layers, onAdd, onChange, onRemove }) => (
  <div className="space-y-4">
    <div className="flex justify-between items-center mb-4">
      <h3 className="text-lg font-semibold text-gray-900">Template Layers</h3>
      <button
        onClick={onAdd}
        className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
        </svg>
        Add Layer
      </button>
    </div>

    {layers.length === 0 ? (
      <div className="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
        <div className="text-gray-400 text-4xl mb-2">🎨</div>
        <p className="text-gray-600">No layers yet. Click "Add Layer" to start building your template.</p>
      </div>
    ) : (
      <div className="space-y-4">
        {layers.map((layer, index) => (
          <div key={layer.id} className="bg-white border-2 border-gray-200 rounded-lg p-4">
            <div className="flex justify-between items-start mb-4">
              <div className="flex items-center gap-2">
                <span className="text-lg font-semibold text-gray-700">Layer {index + 1}</span>
                <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded">{layer.type}</span>
              </div>
              <button
                onClick={() => onRemove(index)}
                className="text-red-600 hover:text-red-800"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Layer ID</label>
                <input
                  type="text"
                  value={layer.id}
                  onChange={(e) => onChange(index, 'id', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
                <select
                  value={layer.type}
                  onChange={(e) => onChange(index, 'type', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                >
                  <option value="image">Image</option>
                  <option value="rectangle">Rectangle</option>
                  <option value="text">Text</option>
                  <option value="video">Video</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Z-Index</label>
                <input
                  type="number"
                  value={layer.z_index}
                  onChange={(e) => onChange(index, 'z_index', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                />
              </div>

              {layer.type === 'rectangle' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Fill Color</label>
                  <input
                    type="color"
                    value={layer.fill || '#000000'}
                    onChange={(e) => onChange(index, 'fill', e.target.value)}
                    className="w-full h-10 border border-gray-300 rounded-lg"
                  />
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    )}
  </div>
);

// Variables Tab
const VariablesTab = ({ variables, onAdd, onChange, onRemove }) => {
  const variableEntries = Object.entries(variables);

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Template Variables</h3>
        <button
          onClick={onAdd}
          className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Add Variable
        </button>
      </div>

      {variableEntries.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
          <div className="text-gray-400 text-4xl mb-2">🔧</div>
          <p className="text-gray-600">No variables defined. Add variables to make your template customizable.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {variableEntries.map(([varName, varConfig]) => (
            <div key={varName} className="bg-white border-2 border-gray-200 rounded-lg p-4">
              <div className="flex justify-between items-start mb-4">
                <div className="flex items-center gap-2">
                  <code className="text-sm font-mono bg-gray-100 px-2 py-1 rounded">{`{{${varName}}}`}</code>
                </div>
                <button
                  onClick={() => onRemove(varName)}
                  className="text-red-600 hover:text-red-800"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
                  <select
                    value={varConfig.type}
                    onChange={(e) => onChange(varName, 'type', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                  >
                    <option value="text">Text</option>
                    <option value="color">Color</option>
                    <option value="image">Image</option>
                    <option value="number">Number</option>
                    <option value="url">URL</option>
                  </select>
                </div>

                <div className="flex items-center">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={varConfig.required || false}
                      onChange={(e) => onChange(varName, 'required', e.target.checked)}
                      className="w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                    />
                    <span className="text-sm font-medium text-gray-700">Required</span>
                  </label>
                </div>

                <div className="col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                  <input
                    type="text"
                    value={varConfig.description || ''}
                    onChange={(e) => onChange(varName, 'description', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                    placeholder="Describe this variable..."
                  />
                </div>

                {varConfig.type === 'text' && (
                  <div className="col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">Default Value</label>
                    <input
                      type="text"
                      value={varConfig.default || ''}
                      onChange={(e) => onChange(varName, 'default', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                      placeholder="Default value..."
                    />
                  </div>
                )}

                {varConfig.type === 'color' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Default Color</label>
                    <input
                      type="color"
                      value={varConfig.default || '#000000'}
                      onChange={(e) => onChange(varName, 'default', e.target.value)}
                      className="w-full h-10 border border-gray-300 rounded-lg"
                    />
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// Metadata Tab
const MetadataTab = ({ metadata, onAddTag, onRemoveTag, onChange }) => (
  <div className="space-y-6">
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-2">Thumbnail URL</label>
      <input
        type="text"
        value={metadata.thumbnail || ''}
        onChange={(e) => onChange('thumbnail', e.target.value)}
        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
        placeholder="https://example.com/thumbnail.jpg"
      />
    </div>

    <div>
      <div className="flex justify-between items-center mb-2">
        <label className="block text-sm font-medium text-gray-700">Tags</label>
        <button
          onClick={onAddTag}
          className="text-sm text-indigo-600 hover:text-indigo-800 font-medium"
        >
          + Add Tag
        </button>
      </div>
      <div className="flex flex-wrap gap-2">
        {metadata.tags && metadata.tags.length > 0 ? (
          metadata.tags.map((tag, index) => (
            <span
              key={index}
              className="inline-flex items-center gap-1 px-3 py-1 bg-indigo-100 text-indigo-800 rounded-full text-sm"
            >
              {tag}
              <button
                onClick={() => onRemoveTag(tag)}
                className="hover:text-indigo-900"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </span>
          ))
        ) : (
          <p className="text-gray-500 text-sm">No tags added yet</p>
        )}
      </div>
    </div>
  </div>
);

// Effects Tab
const EffectsTab = ({ effects, onChange }) => {
  const availableEffects = [
    { type: 'ken_burns', name: 'Ken Burns (Zoom & Pan)', description: 'Adds cinematic zoom and pan motion to images' },
    { type: 'fade_text', name: 'Fade Text', description: 'Fade in/out transitions for text' },
    { type: 'transition', name: 'Transition', description: 'Crossfade, slide, wipe transitions between clips' },
    { type: 'bottom_banner', name: 'Bottom Banner', description: 'Two-tier bottom banner with scrolling ticker' }
  ];

  const handleAddEffect = () => {
    const newEffect = {
      type: 'ken_burns',
      target: 'background',
      params: {}
    };
    onChange([...effects, newEffect]);
  };

  const handleEffectChange = (index, field, value) => {
    const newEffects = [...effects];
    newEffects[index] = { ...newEffects[index], [field]: value };
    onChange(newEffects);
  };

  const handleRemoveEffect = (index) => {
    onChange(effects.filter((_, i) => i !== index));
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold text-gray-900">Video Effects</h3>
        <button
          onClick={handleAddEffect}
          className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 font-medium text-sm"
        >
          + Add Effect
        </button>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="font-medium text-blue-900 mb-2">Available Effects:</h4>
        <ul className="space-y-1 text-sm text-blue-800">
          {availableEffects.map(effect => (
            <li key={effect.type}>
              <strong>{effect.name}:</strong> {effect.description}
            </li>
          ))}
        </ul>
      </div>

      {effects && effects.length > 0 ? (
        <div className="space-y-4">
          {effects.map((effect, index) => (
            <div key={index} className="border border-gray-300 rounded-lg p-4 bg-white">
              <div className="flex justify-between items-start mb-4">
                <h4 className="font-medium text-gray-900">Effect #{index + 1}</h4>
                <button
                  onClick={() => handleRemoveEffect(index)}
                  className="text-red-600 hover:text-red-800"
                >
                  Remove
                </button>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Effect Type</label>
                  <select
                    value={effect.type}
                    onChange={(e) => handleEffectChange(index, 'type', e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                  >
                    {availableEffects.map(e => (
                      <option key={e.type} value={e.type}>{e.name}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Target Layer ID</label>
                  <input
                    type="text"
                    value={effect.target || ''}
                    onChange={(e) => handleEffectChange(index, 'target', e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                    placeholder="e.g., background, title_text"
                  />
                </div>
              </div>

              <div className="mt-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">Parameters (JSON)</label>
                <textarea
                  value={JSON.stringify(effect.params || {}, null, 2)}
                  onChange={(e) => {
                    try {
                      const params = JSON.parse(e.target.value);
                      handleEffectChange(index, 'params', params);
                    } catch (err) {
                      // Invalid JSON, ignore
                    }
                  }}
                  rows={4}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 font-mono text-sm"
                  placeholder='{"zoom_start": 1.0, "zoom_end": 1.2}'
                />
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-gray-500 text-center py-8">No effects added yet. Click "Add Effect" to get started.</p>
      )}
    </div>
  );
};

// Background Music Tab
const BackgroundMusicTab = ({ music, onChange }) => {
  const handleChange = (field, value) => {
    onChange({ ...music, [field]: value });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <input
          type="checkbox"
          id="music-enabled"
          checked={music.enabled}
          onChange={(e) => handleChange('enabled', e.target.checked)}
          className="w-5 h-5 text-indigo-600 rounded focus:ring-indigo-500"
        />
        <label htmlFor="music-enabled" className="text-lg font-semibold text-gray-900">
          Enable Background Music
        </label>
      </div>

      {music.enabled && (
        <>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Music File</label>
            <input
              type="text"
              value={music.source || ''}
              onChange={(e) => handleChange('source', e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
              placeholder="background_music.wav or {{music_file}}"
            />
            <p className="text-sm text-gray-500 mt-1">
              Use a filename from assets directory or a variable like {'{'}{'{'} music_file {'}'}{'}'}
            </p>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Volume</label>
              <input
                type="number"
                min="0"
                max="1"
                step="0.05"
                value={music.volume}
                onChange={(e) => handleChange('volume', parseFloat(e.target.value))}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
              />
              <p className="text-xs text-gray-500 mt-1">0.0 - 1.0 (default: 0.15)</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Fade In (seconds)</label>
              <input
                type="number"
                min="0"
                step="0.5"
                value={music.fade_in}
                onChange={(e) => handleChange('fade_in', parseFloat(e.target.value))}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Fade Out (seconds)</label>
              <input
                type="number"
                min="0"
                step="0.5"
                value={music.fade_out}
                onChange={(e) => handleChange('fade_out', parseFloat(e.target.value))}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>
        </>
      )}
    </div>
  );
};

// Logo Tab
const LogoTab = ({ logo, onChange }) => {
  const handleChange = (field, value) => {
    onChange({ ...logo, [field]: value });
  };

  const positions = [
    { value: 'top-left', label: 'Top Left' },
    { value: 'top-right', label: 'Top Right' },
    { value: 'bottom-left', label: 'Bottom Left' },
    { value: 'bottom-right', label: 'Bottom Right' },
    { value: 'center', label: 'Center' }
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <input
          type="checkbox"
          id="logo-enabled"
          checked={logo.enabled}
          onChange={(e) => handleChange('enabled', e.target.checked)}
          className="w-5 h-5 text-indigo-600 rounded focus:ring-indigo-500"
        />
        <label htmlFor="logo-enabled" className="text-lg font-semibold text-gray-900">
          Enable Logo Watermark
        </label>
      </div>

      {logo.enabled && (
        <>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Logo File</label>
            <input
              type="text"
              value={logo.source || ''}
              onChange={(e) => handleChange('source', e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
              placeholder="logo.png or {{logo_path}}"
            />
            <p className="text-sm text-gray-500 mt-1">
              Use a filename from assets directory or a variable like {'{'}{'{'} logo_path {'}'}{'}'}
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Position</label>
              <select
                value={logo.position}
                onChange={(e) => handleChange('position', e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
              >
                {positions.map(pos => (
                  <option key={pos.value} value={pos.value}>{pos.label}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Margin (pixels)</label>
              <input
                type="number"
                min="0"
                value={logo.margin}
                onChange={(e) => handleChange('margin', parseInt(e.target.value))}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Scale</label>
              <input
                type="number"
                min="0.01"
                max="1"
                step="0.01"
                value={logo.scale}
                onChange={(e) => handleChange('scale', parseFloat(e.target.value))}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
              />
              <p className="text-xs text-gray-500 mt-1">Relative to video width (0.12 = 12%)</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Opacity</label>
              <input
                type="number"
                min="0"
                max="1"
                step="0.1"
                value={logo.opacity}
                onChange={(e) => handleChange('opacity', parseFloat(e.target.value))}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
              />
              <p className="text-xs text-gray-500 mt-1">0.0 (transparent) - 1.0 (opaque)</p>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

// Thumbnail Tab
const ThumbnailTab = ({ thumbnail, onChange }) => {
  const handleChange = (field, value) => {
    onChange({ ...thumbnail, [field]: value });
  };

  return (
    <div className="space-y-6">
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="font-medium text-blue-900 mb-2">📸 Thumbnail Configuration</h4>
        <p className="text-sm text-blue-800">
          Configure how video thumbnails are generated. You can either provide a custom thumbnail image or auto-generate one from the video.
        </p>
      </div>

      <div className="flex items-center gap-3">
        <input
          type="checkbox"
          id="auto-generate"
          checked={thumbnail.auto_generate}
          onChange={(e) => handleChange('auto_generate', e.target.checked)}
          className="w-5 h-5 text-indigo-600 rounded focus:ring-indigo-500"
        />
        <label htmlFor="auto-generate" className="text-lg font-semibold text-gray-900">
          Auto-Generate Thumbnail
        </label>
      </div>

      {thumbnail.auto_generate ? (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Timestamp (seconds)</label>
          <input
            type="number"
            min="0"
            step="0.5"
            value={thumbnail.timestamp}
            onChange={(e) => handleChange('timestamp', parseFloat(e.target.value))}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
          />
          <p className="text-sm text-gray-500 mt-1">
            Extract thumbnail from video at this timestamp (default: 2.0 seconds)
          </p>
        </div>
      ) : (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Custom Thumbnail Image</label>
          <input
            type="text"
            value={thumbnail.source || ''}
            onChange={(e) => handleChange('source', e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
            placeholder="thumbnail.jpg or {{thumbnail_image}}"
          />
          <p className="text-sm text-gray-500 mt-1">
            Use a filename from assets directory or a variable like {'{'}{'{'} thumbnail_image {'}'}{'}'}
          </p>
        </div>
      )}
    </div>
  );
};

// Preview Tab
const PreviewTab = ({ previewUrl, previewLoading, previewError, onGeneratePreview }) => {
  return (
    <div className="space-y-6">
      <div className="bg-gradient-to-r from-purple-50 to-indigo-50 border border-purple-200 rounded-lg p-6">
        <h4 className="font-medium text-purple-900 mb-2 flex items-center gap-2">
          <span className="text-2xl">▶️</span>
          Live Template Preview
        </h4>
        <p className="text-sm text-purple-800 mb-4">
          Generate a preview video with sample data to see how your template looks. This helps you test effects, layouts, and styling before saving.
        </p>
        <button
          onClick={onGeneratePreview}
          disabled={previewLoading}
          className={`
            px-6 py-3 rounded-lg font-medium text-white transition-all
            ${previewLoading
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 shadow-lg hover:shadow-xl'
            }
          `}
        >
          {previewLoading ? (
            <span className="flex items-center gap-2">
              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              Generating Preview... (this may take 1-2 minutes)
            </span>
          ) : (
            <span className="flex items-center gap-2">
              <span>🎬</span>
              Generate Preview Video
            </span>
          )}
        </button>
      </div>

      {previewError && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <h5 className="font-medium text-red-900 mb-1">❌ Preview Generation Failed</h5>
          <p className="text-sm text-red-800">{previewError}</p>
        </div>
      )}

      {previewUrl && (
        <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-lg">
          <h5 className="font-medium text-gray-900 mb-4 flex items-center gap-2">
            <span>✅</span>
            Preview Ready
          </h5>
          <div className="aspect-video bg-black rounded-lg overflow-hidden">
            <video
              src={previewUrl}
              controls
              className="w-full h-full"
              autoPlay
            >
              Your browser does not support the video tag.
            </video>
          </div>
          <div className="mt-4 flex gap-3">
            <a
              href={previewUrl}
              download
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium"
            >
              📥 Download Preview
            </a>
            <button
              onClick={onGeneratePreview}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 font-medium"
            >
              🔄 Regenerate
            </button>
          </div>
        </div>
      )}

      {!previewUrl && !previewLoading && !previewError && (
        <div className="bg-gray-50 border-2 border-dashed border-gray-300 rounded-lg p-12 text-center">
          <div className="text-6xl mb-4">🎥</div>
          <h5 className="text-lg font-medium text-gray-900 mb-2">No Preview Yet</h5>
          <p className="text-gray-600">
            Click "Generate Preview Video" above to see your template in action with sample data.
          </p>
        </div>
      )}
    </div>
  );
};

export default TemplateEditor;

