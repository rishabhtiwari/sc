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

  const handleEditTemplate = (template) => {
    setSelectedTemplate(template);
    setShowWizard(true);
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
              className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-lg hover:from-purple-700 hover:to-indigo-700 transition-all shadow-lg"
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
                    ? 'bg-indigo-100 text-indigo-700 border-2 border-indigo-300'
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
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
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
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
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
              try {
                await templateService.saveTemplate(templateData);
                setShowWizard(false);
                fetchTemplates();
              } catch (error) {
                console.error('Failed to save template:', error);
                alert('Failed to save template: ' + error.message);
              }
            }}
          />
        )}
      </div>
    </div>
  );
};

// Template Card Component
const TemplateCard = ({ template, onEdit }) => {
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

  return (
    <div className="bg-white rounded-lg border-2 border-gray-200 hover:border-indigo-300 transition-all hover:shadow-lg">
      {/* Thumbnail */}
      <div className="h-48 bg-gradient-to-br from-gray-100 to-gray-200 rounded-t-lg flex items-center justify-center">
        {template.thumbnail ? (
          <img src={template.thumbnail} alt={template.name} className="w-full h-full object-cover rounded-t-lg" />
        ) : (
          <div className="text-6xl">{categoryIcons[template.category] || '📋'}</div>
        )}
      </div>

      {/* Content */}
      <div className="p-4">
        <div className="flex items-start justify-between mb-2">
          <h3 className="text-lg font-semibold text-gray-900">{template.name}</h3>
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${categoryColors[template.category] || 'bg-gray-100 text-gray-800'}`}>
            {template.category}
          </span>
        </div>

        <p className="text-sm text-gray-600 mb-3 line-clamp-2">{template.description}</p>

        {/* Tags */}
        {template.tags && template.tags.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-3">
            {template.tags.slice(0, 3).map((tag, index) => (
              <span key={index} className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded">
                {tag}
              </span>
            ))}
          </div>
        )}

        {/* Footer */}
        <div className="flex items-center justify-between pt-3 border-t border-gray-200">
          <span className="text-xs text-gray-500">v{template.version}</span>
          <button
            onClick={onEdit}
            className="flex items-center gap-1 px-3 py-1.5 text-sm font-medium text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
            Edit
          </button>
        </div>
      </div>
    </div>
  );
};

export default TemplateManagementPage;

