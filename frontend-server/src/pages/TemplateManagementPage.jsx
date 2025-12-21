import React, { useState, useEffect } from 'react';
import { templateService } from '../services/templateService';
import TemplateWizard from '../components/TemplateWizard';

const TemplateManagementPage = () => {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [showWizard, setShowWizard] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState(null);

  const categories = [
    { id: 'all', name: 'All Templates', icon: '📋' },
    { id: 'news', name: 'News Videos', icon: '📰' },
    { id: 'shorts', name: 'YouTube Shorts', icon: '📱' },
    { id: 'ecommerce', name: 'E-commerce', icon: '🛍️' }
  ];

  useEffect(() => {
    fetchTemplates();
  }, [selectedCategory]);

  const fetchTemplates = async () => {
    try {
      setLoading(true);
      setError(null);
      const category = selectedCategory === 'all' ? null : selectedCategory;
      const data = await templateService.listTemplates(category);
      setTemplates(data.templates || []);
    } catch (err) {
      setError(err.message || 'Failed to load templates');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTemplate = () => {
    setSelectedTemplate(null);
    setShowWizard(true);
  };

  const handleEditTemplate = async (template) => {
    try {
      // Fetch full template details from API
      console.log('📥 Fetching template details for:', template.template_id);
      const fullTemplate = await templateService.getTemplate(template.template_id);
      console.log('✅ Loaded full template:', fullTemplate);
      setSelectedTemplate(fullTemplate.template || fullTemplate);
      setShowWizard(true);
    } catch (err) {
      console.error('❌ Failed to load template:', err);
      alert(`Failed to load template: ${err.message}`);
    }
  };

  const handleDeleteTemplate = async (templateId) => {
    if (!window.confirm('Are you sure you want to delete this template?')) {
      return;
    }

    try {
      await templateService.deleteTemplate(templateId);
      fetchTemplates();
    } catch (err) {
      alert(`Failed to delete template: ${err.message}`);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Template Management</h1>
              <p className="text-gray-600 mt-2">Create and manage video templates for your content</p>
            </div>
            <button
              onClick={handleCreateTemplate}
              className="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all shadow-lg"
            >
              <span className="text-xl">🎬</span>
              Create Template
            </button>
          </div>
        </div>

        {/* Category Filter */}
        <div className="mb-6">
          <div className="flex gap-2">
            {categories.map((category) => (
              <button
                key={category.id}
                onClick={() => setSelectedCategory(category.id)}
                className={`
                  flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors
                  ${selectedCategory === category.id
                    ? 'bg-blue-100 text-blue-700 border-2 border-blue-300'
                    : 'bg-white text-gray-700 border-2 border-gray-200 hover:border-gray-300'
                  }
                `}
              >
                <span className="text-xl">{category.icon}</span>
                {category.name}
              </button>
            ))}
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-center gap-2 text-red-800">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              {error}
            </div>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        )}

        {/* Templates Grid */}
        {!loading && templates.length === 0 && (
          <div className="text-center py-12">
            <div className="text-gray-400 text-6xl mb-4">📋</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No templates found</h3>
            <p className="text-gray-600 mb-4">Get started by creating your first template</p>
            <button
              onClick={handleCreateTemplate}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Create Template
            </button>
          </div>
        )}

        {!loading && templates.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {templates.map((template) => (
              <TemplateCard
                key={template.template_id}
                template={template}
                onEdit={() => handleEditTemplate(template)}
                onDelete={() => handleDeleteTemplate(template.template_id)}
              />
            ))}
          </div>
        )}

        {/* Template Wizard */}
        {showWizard && (
          <TemplateWizard
            template={selectedTemplate}
            onClose={() => setShowWizard(false)}
            onSave={async (templateData) => {
              // Save template - errors will be handled by the wizard
              await templateService.saveTemplate(templateData);
              setShowWizard(false);
              fetchTemplates();
            }}
          />
        )}
      </div>
    </div>
  );
};

// Template Card Component
const TemplateCard = ({ template, onEdit, onDelete }) => {
  const [showPreview, setShowPreview] = React.useState(false);
  const [previewUrl, setPreviewUrl] = React.useState(null);
  const [loadingPreview, setLoadingPreview] = React.useState(false);
  const videoRef = React.useRef(null);

  const categoryColors = {
    news: 'bg-blue-100 text-blue-800',
    shorts: 'bg-purple-100 text-purple-800',
    ecommerce: 'bg-green-100 text-green-800'
  };

  const categoryIcons = {
    news: '📰',
    shorts: '📱',
    ecommerce: '🛍️'
  };

  const handlePreviewClick = async () => {
    if (showPreview) {
      // Close preview
      setShowPreview(false);
      if (videoRef.current) {
        videoRef.current.pause();
      }
      return;
    }

    // Generate preview if not already loaded
    if (!previewUrl) {
      try {
        setLoadingPreview(true);
        const token = localStorage.getItem('auth_token');

        console.log('🎬 Generating preview for template:', template.template_id);

        // Fetch full template details first (list only returns basic fields)
        console.log('📥 Fetching full template details...');
        const fullTemplate = await templateService.getTemplate(template.template_id);
        const templateData = fullTemplate.template || fullTemplate;

        console.log('✅ Full template loaded:', {
          layers: templateData.layers?.length || 0,
          effects: templateData.effects?.length || 0,
          background_music: templateData.background_music?.enabled || false,
          logo: templateData.logo?.enabled || false
        });

        const response = await fetch('http://localhost:8080/api/templates/preview', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(token && { 'Authorization': `Bearer ${token}` })
          },
          body: JSON.stringify({
            template: templateData,
            is_initial: false  // Generate with all template settings applied
          })
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.error || 'Failed to generate preview');
        }

        const data = await response.json();
        console.log('✅ Preview generated:', data);
        const fullPreviewUrl = `http://localhost:8080${data.preview_url}`;
        setPreviewUrl(fullPreviewUrl);
        setShowPreview(true);
      } catch (err) {
        console.error('❌ Failed to load preview:', err);
        alert(`Failed to load preview video: ${err.message}`);
      } finally {
        setLoadingPreview(false);
      }
    } else {
      setShowPreview(true);
    }
  };

  // Auto-play when preview is shown
  React.useEffect(() => {
    if (showPreview && videoRef.current) {
      videoRef.current.play();
    }
  }, [showPreview]);

  return (
    <div className="group bg-white rounded-xl shadow-sm hover:shadow-xl transition-all duration-300 overflow-hidden border border-gray-200 hover:border-blue-400">
      {/* Thumbnail/Preview */}
      <div className="relative h-56 bg-gradient-to-br from-blue-50 via-blue-100 to-blue-50 flex items-center justify-center overflow-hidden">
        {showPreview && previewUrl ? (
          <video
            ref={videoRef}
            src={previewUrl}
            className="w-full h-full object-contain bg-black"
            controls
            loop
          />
        ) : template.thumbnail?.source ? (
          <img
            src={`http://localhost:8080/api/templates/files/${template.thumbnail.source}`}
            alt={template.name}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          />
        ) : (
          <div className="text-7xl opacity-40 group-hover:opacity-60 transition-opacity">
            {categoryIcons[template.category] || '📋'}
          </div>
        )}

        {/* Category badge - top left */}
        <div className="absolute top-3 left-3">
          <span className={`px-3 py-1.5 rounded-lg text-xs font-semibold shadow-md backdrop-blur-sm ${categoryColors[template.category] || 'bg-gray-100 text-gray-800'}`}>
            {categoryIcons[template.category]} {template.category.toUpperCase()}
          </span>
        </div>

        {/* Play button overlay */}
        {!showPreview && (
          <button
            onClick={handlePreviewClick}
            disabled={loadingPreview}
            className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-0 group-hover:bg-opacity-40 transition-all duration-300"
          >
            <div className="w-20 h-20 bg-white rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all duration-300 shadow-2xl transform group-hover:scale-110">
              {loadingPreview ? (
                <svg className="animate-spin h-10 w-10 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              ) : (
                <svg className="w-10 h-10 text-blue-600 ml-1" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M8 5v14l11-7z" />
                </svg>
              )}
            </div>
          </button>
        )}

        {/* Close preview button */}
        {showPreview && (
          <button
            onClick={handlePreviewClick}
            className="absolute top-3 right-3 w-10 h-10 bg-red-600 rounded-full flex items-center justify-center hover:bg-red-700 transition-colors shadow-lg z-10 hover:scale-110 transform"
          >
            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>

      {/* Content */}
      <div className="p-5">
        {/* Title */}
        <h3 className="text-xl font-bold text-gray-900 mb-2 group-hover:text-blue-600 transition-colors">
          {template.name}
        </h3>

        {/* Description */}
        <p className="text-sm text-gray-600 mb-4 line-clamp-2 leading-relaxed">
          {template.description || 'No description available'}
        </p>

        {/* Tags */}
        {template.tags && template.tags.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-4">
            {template.tags.slice(0, 3).map((tag, index) => (
              <span key={index} className="px-2.5 py-1 bg-blue-50 text-blue-700 text-xs font-medium rounded-md border border-blue-100">
                #{tag}
              </span>
            ))}
            {template.tags.length > 3 && (
              <span className="px-2.5 py-1 bg-gray-50 text-gray-500 text-xs font-medium rounded-md">
                +{template.tags.length - 3} more
              </span>
            )}
          </div>
        )}

        {/* Footer */}
        <div className="flex items-center justify-between pt-4 border-t border-gray-100">
          <div className="flex items-center gap-2">
            <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs font-semibold rounded">
              v{template.version}
            </span>
            <span className="text-xs text-gray-400">
              ID: {template.template_id.split('_')[0]}
            </span>
          </div>
          <div className="flex gap-2">
            <button
              onClick={onEdit}
              className="flex items-center gap-1.5 px-4 py-2 text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-all shadow-sm hover:shadow-md transform hover:-translate-y-0.5"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
              Edit
            </button>
            <button
              onClick={onDelete}
              className="flex items-center gap-1.5 px-4 py-2 text-sm font-semibold text-red-600 bg-red-50 hover:bg-red-100 rounded-lg transition-all border border-red-200 hover:border-red-300 transform hover:-translate-y-0.5"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
              Delete
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TemplateManagementPage;

