import React, { useState, useEffect } from 'react';
import { templateService } from '../services/templateService';
import TemplateWizard from '../components/TemplateWizard';
import { Card, Button, Table, Spinner, Modal } from '../components/common';
import ConfirmDialog from '../components/common/ConfirmDialog';

const TemplateManagementPage = () => {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [showWizard, setShowWizard] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [viewMode, setViewMode] = useState('card'); // 'card' or 'table'
  const [deleteDialog, setDeleteDialog] = useState({ isOpen: false, template: null });

  const categories = {
    all: { label: 'All Templates', icon: '📋', color: 'gray' },
    news: { label: 'News Videos', icon: '📰', color: 'blue' },
    shorts: { label: 'YouTube Shorts', icon: '📱', color: 'purple' },
    ecommerce: { label: 'E-commerce', icon: '🛍️', color: 'green' },
    social: { label: 'Social Media', icon: '📱', color: 'pink' }
  };

  useEffect(() => {
    fetchTemplates();
  }, []); // Only fetch once on mount

  const fetchTemplates = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await templateService.listTemplates(null); // Fetch all templates
      setTemplates(data.templates || []);
    } catch (err) {
      setError(err.message || 'Failed to load templates');
    } finally {
      setLoading(false);
    }
  };

  // Group templates by category
  const templatesByCategory = templates.reduce((acc, template) => {
    const cat = template.category || 'ecommerce';
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(template);
    return acc;
  }, {});

  // Filter templates based on selected category
  const filteredTemplates = selectedCategory === 'all'
    ? templates
    : templates.filter(t => t.category === selectedCategory);

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

  const handleDeleteTemplate = (template) => {
    setDeleteDialog({ isOpen: true, template });
  };

  const confirmDelete = async () => {
    const template = deleteDialog.template;
    setDeleteDialog({ isOpen: false, template: null });

    try {
      await templateService.deleteTemplate(template.template_id);
      fetchTemplates();
    } catch (err) {
      alert(`Failed to delete template: ${err.message}`);
    }
  };

  // Table columns configuration
  const columns = [
    {
      key: 'name',
      label: 'Name',
      render: (value, template) => (
        <div className="flex items-center gap-2">
          <span className="text-xl">{categories[template.category]?.icon || '🎬'}</span>
          <span className="font-medium">{value}</span>
        </div>
      )
    },
    {
      key: 'category',
      label: 'Category',
      render: (value) => {
        const cat = categories[value] || categories.ecommerce;
        return (
          <span className={`px-2 py-1 rounded text-xs font-medium bg-${cat.color}-100 text-${cat.color}-700`}>
            {cat.label}
          </span>
        );
      }
    },
    { key: 'description', label: 'Description' },
    {
      key: 'info',
      label: 'Info',
      render: (_, template) => (
        <div className="flex items-center gap-3 text-xs text-gray-500">
          <span>🎬 {template.layer_count || 0} layers</span>
          <span>✨ {template.effect_count || 0} effects</span>
        </div>
      )
    },
    {
      key: 'actions',
      label: 'Actions',
      render: (_, template) => (
        <TableRowActions
          template={template}
          onEdit={() => handleEditTemplate(template)}
          onDelete={() => handleDeleteTemplate(template)}
        />
      )
    }
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Video Template Management</h1>
        <p className="text-gray-600 mt-2">Create and manage video templates for your content</p>
      </div>

      {/* Category Filter Tabs */}
      <div className="mb-6 bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <div className="flex items-center gap-2 flex-wrap">
          {Object.entries(categories).map(([key, cat]) => (
            <button
              key={key}
              onClick={() => setSelectedCategory(key)}
              className={`
                flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm transition-all
                ${selectedCategory === key
                  ? `bg-${cat.color}-100 text-${cat.color}-700 border-2 border-${cat.color}-300`
                  : 'bg-gray-50 text-gray-600 border-2 border-transparent hover:bg-gray-100'
                }
              `}
            >
              <span className="text-lg">{cat.icon}</span>
              <span>{cat.label}</span>
              <span className={`
                ml-1 px-2 py-0.5 rounded-full text-xs font-semibold
                ${selectedCategory === key ? `bg-${cat.color}-200` : 'bg-gray-200'}
              `}>
                {key === 'all' ? templates.length : (templatesByCategory[key]?.length || 0)}
              </span>
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

      <Card>
        <div className="flex justify-between items-center mb-4">
          <div>
            <h2 className="text-xl font-semibold">
              {selectedCategory === 'all' ? 'All Templates' : categories[selectedCategory]?.label}
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              {filteredTemplates.length} template{filteredTemplates.length !== 1 ? 's' : ''} found
            </p>
          </div>
          <div className="flex items-center gap-3">
            {/* View Mode Toggle */}
            <div className="flex items-center gap-2 bg-gray-100 rounded-lg p-1">
              <button
                onClick={() => setViewMode('card')}
                className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all ${
                  viewMode === 'card'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
                title="Card View"
              >
                <span className="flex items-center gap-1">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
                  </svg>
                  Cards
                </span>
              </button>
              <button
                onClick={() => setViewMode('table')}
                className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all ${
                  viewMode === 'table'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
                title="Table View"
              >
                <span className="flex items-center gap-1">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                  Table
                </span>
              </button>
            </div>
            <Button variant="primary" onClick={handleCreateTemplate}>
              + Create Template
            </Button>
          </div>
        </div>

        {/* Table View */}
        {viewMode === 'table' && (
          <Table
            columns={columns}
            data={filteredTemplates}
            emptyMessage={`No ${selectedCategory === 'all' ? '' : categories[selectedCategory]?.label.toLowerCase()} templates found. Create your first template!`}
          />
        )}

        {/* Card View */}
        {viewMode === 'card' && (
          <div>
            {filteredTemplates.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <div className="text-6xl mb-4">🎬</div>
                <p className="text-lg font-medium">No {selectedCategory === 'all' ? '' : categories[selectedCategory]?.label.toLowerCase()} templates found</p>
                <p className="text-sm mt-2">Create your first template to get started!</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {filteredTemplates.map((template) => (
                  <VideoTemplateCard
                    key={template.template_id}
                    template={template}
                    categories={categories}
                    onEdit={() => handleEditTemplate(template)}
                    onDelete={() => handleDeleteTemplate(template)}
                  />
                ))}
              </div>
            )}
          </div>
        )}
      </Card>

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

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={deleteDialog.isOpen}
        onClose={() => setDeleteDialog({ isOpen: false, template: null })}
        onConfirm={confirmDelete}
        title="Delete Video Template"
        message={`Are you sure you want to delete "${deleteDialog.template?.name}"?`}
        description="This action cannot be undone. The template will be permanently removed."
        confirmText="Delete"
        cancelText="Cancel"
        variant="danger"
      />
    </div>
  );
};

// Table Row Actions Component (with Preview and Recompute)
const TableRowActions = ({ template, onEdit, onDelete }) => {
  const [showPreview, setShowPreview] = React.useState(false);
  const [previewUrl, setPreviewUrl] = React.useState(null);
  const [loadingPreview, setLoadingPreview] = React.useState(false);
  const [recomputing, setRecomputing] = React.useState(false);

  const handlePreview = async () => {
    try {
      setLoadingPreview(true);
      const token = localStorage.getItem('auth_token');
      const fullTemplate = await templateService.getTemplate(template.template_id);
      const templateData = fullTemplate.template || fullTemplate;

      const response = await fetch('http://localhost:8080/api/templates/preview', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { 'Authorization': `Bearer ${token}` })
        },
        body: JSON.stringify({
          template: templateData,
          is_initial: false
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to generate preview');
      }

      const data = await response.json();
      const fullPreviewUrl = `http://localhost:8080${data.preview_url}`;
      setPreviewUrl(fullPreviewUrl);
      setShowPreview(true);
    } catch (err) {
      console.error('❌ Failed to load preview:', err);
      alert(`Failed to load preview video: ${err.message}`);
    } finally {
      setLoadingPreview(false);
    }
  };

  const handleRecompute = async () => {
    try {
      setRecomputing(true);
      const token = localStorage.getItem('auth_token');
      const fullTemplate = await templateService.getTemplate(template.template_id);
      const templateData = fullTemplate.template || fullTemplate;

      const response = await fetch('http://localhost:8080/api/templates/preview', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { 'Authorization': `Bearer ${token}` })
        },
        body: JSON.stringify({
          template: templateData,
          is_initial: false
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to recompute preview');
      }

      const data = await response.json();
      const fullPreviewUrl = `http://localhost:8080${data.preview_url}`;
      setPreviewUrl(fullPreviewUrl);
      setShowPreview(true);
    } catch (err) {
      console.error('❌ Failed to recompute preview:', err);
      alert(`Failed to recompute preview: ${err.message}`);
    } finally {
      setRecomputing(false);
    }
  };

  return (
    <>
      <div className="flex gap-1.5">
        <Button
          size="sm"
          onClick={handlePreview}
          disabled={loadingPreview}
          className="px-2 py-1"
        >
          {loadingPreview ? '⏳' : 'Preview'}
        </Button>
        <Button
          size="sm"
          onClick={handleRecompute}
          disabled={recomputing}
          className="px-2 py-1"
        >
          {recomputing ? '⏳' : 'Recompute'}
        </Button>
        <Button
          size="sm"
          onClick={onEdit}
          className="px-2 py-1"
        >
          Edit
        </Button>
        <Button
          size="sm"
          variant="danger"
          onClick={onDelete}
          className="px-2 py-1"
        >
          🗑️
        </Button>
      </div>

      {/* Preview Modal */}
      {showPreview && previewUrl && (
        <div
          className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50"
          onClick={() => setShowPreview(false)}
        >
          <div className="relative max-w-4xl w-full mx-4" onClick={(e) => e.stopPropagation()}>
            <button
              onClick={() => setShowPreview(false)}
              className="absolute -top-10 right-0 text-white hover:text-gray-300 text-2xl font-bold"
            >
              ✕
            </button>
            <video
              src={previewUrl}
              className="w-full rounded-lg shadow-2xl"
              controls
              autoPlay
              loop
            />
          </div>
        </div>
      )}
    </>
  );
};

// Video Template Card Component (matching Prompt Template card style)
const VideoTemplateCard = ({ template, categories, onEdit, onDelete }) => {
  const [showPreview, setShowPreview] = React.useState(false);
  const [previewUrl, setPreviewUrl] = React.useState(null);
  const [loadingPreview, setLoadingPreview] = React.useState(false);
  const [recomputing, setRecomputing] = React.useState(false);
  const videoRef = React.useRef(null);

  const categoryInfo = categories[template.category] || categories.ecommerce;

  // Get layer and effect counts from template (provided by backend)
  const layerCount = template.layer_count || 0;
  const effectCount = template.effect_count || 0;

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

  const handleRecompute = async () => {
    try {
      setRecomputing(true);
      const token = localStorage.getItem('auth_token');

      console.log('🔄 Recomputing preview for template:', template.template_id);

      // Fetch full template details
      const fullTemplate = await templateService.getTemplate(template.template_id);
      const templateData = fullTemplate.template || fullTemplate;

      const response = await fetch('http://localhost:8080/api/templates/preview', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { 'Authorization': `Bearer ${token}` })
        },
        body: JSON.stringify({
          template: templateData,
          is_initial: false
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to recompute preview');
      }

      const data = await response.json();
      console.log('✅ Preview recomputed:', data);
      const fullPreviewUrl = `http://localhost:8080${data.preview_url}`;
      setPreviewUrl(fullPreviewUrl);
      setShowPreview(true);

      // Auto-play the video
      setTimeout(() => {
        if (videoRef.current) {
          videoRef.current.play();
        }
      }, 100);
    } catch (err) {
      console.error('❌ Failed to recompute preview:', err);
      alert(`Failed to recompute preview: ${err.message}`);
    } finally {
      setRecomputing(false);
    }
  };

  // Auto-play when preview is shown
  React.useEffect(() => {
    if (showPreview && videoRef.current) {
      videoRef.current.play();
    }
  }, [showPreview]);

  return (
    <div className="bg-white border-2 border-gray-200 rounded-lg overflow-hidden hover:shadow-lg hover:border-gray-300 transition-all duration-200">
      {/* Preview/Thumbnail Section - More Compact */}
      <div className="relative h-32 bg-gradient-to-br from-blue-50 via-blue-100 to-blue-50 flex items-center justify-center overflow-hidden">
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
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="text-4xl opacity-40">
            {categoryInfo.icon}
          </div>
        )}

        {/* Category badge - top left - More Compact */}
        <div className="absolute top-1.5 left-1.5">
          <span className={`px-1.5 py-0.5 rounded text-xs font-semibold shadow-md backdrop-blur-sm bg-${categoryInfo.color}-100 text-${categoryInfo.color}-700`}>
            {categoryInfo.icon} {categoryInfo.label}
          </span>
        </div>

        {/* Preview/Close button - center overlay - More Compact */}
        {!showPreview && (
          <button
            onClick={handlePreviewClick}
            disabled={loadingPreview}
            className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-0 hover:bg-opacity-40 transition-all duration-300 group"
          >
            <div className="w-12 h-12 bg-white rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all duration-300 shadow-2xl transform group-hover:scale-110">
              {loadingPreview ? (
                <svg className="animate-spin h-6 w-6 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              ) : (
                <svg className="w-6 h-6 text-blue-600 ml-0.5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M8 5v14l11-7z" />
                </svg>
              )}
            </div>
          </button>
        )}

        {/* Close preview button - More Compact */}
        {showPreview && (
          <button
            onClick={handlePreviewClick}
            className="absolute top-1.5 right-1.5 w-7 h-7 bg-red-600 rounded-full flex items-center justify-center hover:bg-red-700 transition-colors shadow-lg z-10 hover:scale-110 transform"
          >
            <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>

      {/* Content Section - More Compact */}
      <div className="p-3">
        {/* Header - More Compact */}
        <div className="flex items-start justify-between mb-2">
          <div className="flex items-center gap-1.5">
            <span className="text-xl">{categoryInfo.icon}</span>
            <div>
              <h3 className="font-semibold text-gray-900 text-base leading-tight">
                {template.name}
              </h3>
            </div>
          </div>
        </div>

        {/* Description - More Compact */}
        <p className="text-xs text-gray-600 mb-2 line-clamp-2 min-h-[32px]">
          {template.description || 'No description provided'}
        </p>

        {/* Template Info - More Compact */}
        <div className="flex items-center gap-3 mb-2 text-xs text-gray-500 border-t border-gray-100 pt-2">
          <div className="flex items-center gap-1">
            <span>🎬</span>
            <span>{layerCount} layer{layerCount !== 1 ? 's' : ''}</span>
          </div>
          <div className="flex items-center gap-1">
            <span>✨</span>
            <span>{effectCount} effect{effectCount !== 1 ? 's' : ''}</span>
          </div>
        </div>

        {/* Actions - All in one line - More Compact */}
        <div className="flex gap-1.5">
          <Button
            size="sm"
            onClick={handlePreviewClick}
            disabled={loadingPreview}
            className="flex-1 text-xs py-1"
          >
            {loadingPreview ? '⏳' : 'Preview'}
          </Button>
          <Button
            size="sm"
            onClick={handleRecompute}
            disabled={recomputing}
            className="flex-1 text-xs py-1"
          >
            {recomputing ? '⏳' : 'Recompute'}
          </Button>
          <Button
            size="sm"
            onClick={onEdit}
            className="flex-1 text-xs py-1"
          >
            Edit
          </Button>
          <Button
            size="sm"
            variant="danger"
            onClick={onDelete}
            className="px-2 text-xs py-1"
          >
            🗑️
          </Button>
        </div>
      </div>
    </div>
  );
};



export default TemplateManagementPage;

