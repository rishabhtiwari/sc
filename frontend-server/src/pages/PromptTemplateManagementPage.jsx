import React, { useState, useEffect } from 'react';
import { Button, Card, Table, Modal, Input, Spinner, ErrorAlert, ToastContainer, ConfirmDialog } from '../components/common';
import { useToast } from '../hooks/useToast';
import api from '../services/api';
import PromptBuilder from '../components/common/PromptBuilder/PromptBuilder';

/**
 * Prompt Template Management Page
 * Allows users to view, create, edit, and manage prompt templates
 */
const PromptTemplateManagementPage = () => {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [showViewModal, setShowViewModal] = useState(false);
  const [viewingTemplate, setViewingTemplate] = useState(null);
  const [editingTemplate, setEditingTemplate] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [formError, setFormError] = useState(null);
  const [useSimpleMode, setUseSimpleMode] = useState(true); // Toggle between simple and advanced mode
  const [viewMode, setViewMode] = useState('card'); // 'card' or 'table'
  const [deleteDialog, setDeleteDialog] = useState({ isOpen: false, template: null });
  const [formData, setFormData] = useState({
    template_id: '',
    name: '',
    description: '',
    category: 'product_summary',
    prompt_text: '',
    output_schema: {
      type: 'object',
      properties: {
        content: { type: 'string' }
      }
    },
    is_active: true
  });
  const { toasts, showToast, hideToast } = useToast();

  // Category definitions
  const categories = {
    all: { label: 'All Templates', icon: '📋', color: 'gray' },
    ecommerce: { label: 'E-commerce', icon: '🛒', color: 'blue' },
    social_media: { label: 'Social Media', icon: '📱', color: 'purple' },
    news: { label: 'News & Media', icon: '📰', color: 'red' },
    marketing: { label: 'Marketing', icon: '📢', color: 'green' },
    product_summary: { label: 'Product Summary', icon: '📦', color: 'orange' },
    section_content: { label: 'Section Content', icon: '📄', color: 'indigo' },
    custom: { label: 'Custom', icon: '⚙️', color: 'gray' },
  };

  useEffect(() => {
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    try {
      setLoading(true);
      const response = await api.get('/prompt-templates');
      if (response.data.status === 'success') {
        setTemplates(response.data.templates || []);
      }
    } catch (error) {
      console.error('Error fetching templates:', error);
      showToast('Failed to load templates', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingTemplate(null);
    setFormError(null);
    setFormData({
      template_id: '',
      name: '',
      description: '',
      category: 'product_summary',
      prompt_text: '',
      output_schema: {
        type: 'object',
        properties: {
          content: { type: 'string' }
        }
      },
      is_active: true
    });
    setShowModal(true);
  };

  const handleView = (template) => {
    setViewingTemplate(template);
    setShowViewModal(true);
  };

  const handleEdit = (template) => {
    setEditingTemplate(template);
    setFormError(null);
    setFormData({
      template_id: template.template_id,
      name: template.name,
      description: template.description,
      category: template.category,
      prompt_text: template.prompt_text,
      output_schema: template.output_schema || {
        type: 'object',
        properties: {
          content: { type: 'string' }
        }
      },
      variables: template.variables || [],
      is_active: template.is_active
    });
    setShowModal(true);
  };

  const handleSave = async () => {
    // Clear previous errors
    setFormError(null);

    // Validate form
    if (!formData.template_id || !formData.template_id.trim()) {
      setFormError('Template ID is required');
      return;
    }
    if (!formData.name || !formData.name.trim()) {
      setFormError('Template name is required');
      return;
    }
    if (!formData.description || !formData.description.trim()) {
      setFormError('Description is required');
      return;
    }
    if (!formData.prompt_text || !formData.prompt_text.trim()) {
      setFormError('Prompt text is required');
      return;
    }
    if (!formData.output_schema) {
      setFormError('Output schema is required');
      return;
    }

    // Validate output_schema is valid JSON
    try {
      if (typeof formData.output_schema === 'string') {
        JSON.parse(formData.output_schema);
      }
    } catch (e) {
      setFormError('Output schema must be valid JSON');
      return;
    }

    try {
      // Prepare data for submission
      const submitData = {
        ...formData,
        output_schema: typeof formData.output_schema === 'string'
          ? JSON.parse(formData.output_schema)
          : formData.output_schema
      };

      if (editingTemplate) {
        // Update existing template
        await api.put(`/prompt-templates/${editingTemplate.template_id}`, submitData);
        showToast('Template updated successfully', 'success');
      } else {
        // Create new template
        await api.post('/prompt-templates', submitData);
        showToast('Template created successfully', 'success');
      }
      setShowModal(false);
      setFormError(null);
      fetchTemplates();
    } catch (error) {
      console.error('Error saving template:', error);
      const errorMessage = error.response?.data?.message || 'Failed to save template';
      setFormError(errorMessage);
      showToast(errorMessage, 'error');
    }
  };

  const handleDelete = (template) => {
    setDeleteDialog({ isOpen: true, template });
  };

  const confirmDelete = async () => {
    const template = deleteDialog.template;
    setDeleteDialog({ isOpen: false, template: null });

    try {
      await api.delete(`/prompt-templates/${template.template_id}`);
      showToast('Template deleted successfully', 'success');
      fetchTemplates();
    } catch (error) {
      console.error('Error deleting template:', error);
      showToast(error.response?.data?.message || 'Failed to delete template', 'error');
    }
  };

  // Filter templates by category
  const filteredTemplates = selectedCategory === 'all'
    ? templates
    : templates.filter(t => t.category === selectedCategory);

  // Group templates by category for display
  const templatesByCategory = templates.reduce((acc, template) => {
    const cat = template.category || 'custom';
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(template);
    return acc;
  }, {});

  const columns = [
    { key: 'name', label: 'Name' },
    { key: 'category', label: 'Category' },
    { key: 'description', label: 'Description' },
    {
      key: 'is_system_default',
      label: 'Type',
      render: (value) => (
        <span className={`px-2 py-1 rounded text-xs ${value ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-800'}`}>
          {value ? 'System' : 'Custom'}
        </span>
      )
    },
    {
      key: 'is_active',
      label: 'Status',
      render: (value) => (
        <span className={`px-2 py-1 rounded text-xs ${value ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
          {value ? 'Active' : 'Inactive'}
        </span>
      )
    },
    {
      key: 'actions',
      label: 'Actions',
      render: (_, template) => (
        <div className="flex gap-2">
          <Button
            size="sm"
            variant="outline"
            onClick={() => handleView(template)}
          >
            View
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => handleEdit(template)}
            disabled={template.is_system_default}
          >
            Edit
          </Button>
          <Button
            size="sm"
            variant="danger"
            onClick={() => handleDelete(template)}
            disabled={template.is_system_default}
          >
            Delete
          </Button>
        </div>
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
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Prompt Template Management</h1>
        <p className="text-gray-600 mt-2">Manage AI prompt templates for content generation across different use cases</p>
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
            <Button variant="primary" onClick={handleCreate}>
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
                <div className="text-6xl mb-4">📋</div>
                <p className="text-lg font-medium">No {selectedCategory === 'all' ? '' : categories[selectedCategory]?.label.toLowerCase()} templates found</p>
                <p className="text-sm mt-2">Create your first template to get started!</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {filteredTemplates.map((template) => {
                  const categoryInfo = categories[template.category] || categories.custom;
                  return (
                    <div
                      key={template.template_id}
                      className="bg-white border-2 border-gray-200 rounded-lg p-5 hover:shadow-lg hover:border-gray-300 transition-all duration-200"
                    >
                      {/* Header */}
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center gap-2">
                          <span className="text-2xl">{categoryInfo.icon}</span>
                          <div>
                            <h3 className="font-semibold text-gray-900 text-lg leading-tight">
                              {template.name}
                            </h3>
                            <span className={`inline-block mt-1 px-2 py-0.5 rounded text-xs font-medium bg-${categoryInfo.color}-100 text-${categoryInfo.color}-700`}>
                              {categoryInfo.label}
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Description */}
                      <p className="text-sm text-gray-600 mb-4 line-clamp-2 min-h-[40px]">
                        {template.description || 'No description provided'}
                      </p>

                      {/* Metadata */}
                      <div className="flex items-center gap-2 mb-4 text-xs">
                        <span className={`px-2 py-1 rounded ${template.is_system_default ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-800'}`}>
                          {template.is_system_default ? '🔒 System' : '✏️ Custom'}
                        </span>
                        <span className={`px-2 py-1 rounded ${template.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                          {template.is_active ? '✓ Active' : '✗ Inactive'}
                        </span>
                      </div>

                      {/* Variables & Output Info */}
                      <div className="flex items-center gap-4 mb-4 text-xs text-gray-500 border-t border-gray-100 pt-3">
                        <div className="flex items-center gap-1">
                          <span>📥</span>
                          <span>{template.variables?.length || 0} inputs</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <span>📤</span>
                          <span>{template.output_schema?.properties ? Object.keys(template.output_schema.properties).length : 0} outputs</span>
                        </div>
                      </div>

                      {/* Actions */}
                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleView(template)}
                          className="flex-1"
                        >
                          👁️ View
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleEdit(template)}
                          disabled={template.is_system_default}
                          className="flex-1"
                        >
                          ✏️ Edit
                        </Button>
                        <Button
                          size="sm"
                          variant="danger"
                          onClick={() => handleDelete(template)}
                          disabled={template.is_system_default}
                        >
                          🗑️
                        </Button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </Card>

      {/* View Modal (Read-only) */}
      <Modal
        isOpen={showViewModal}
        onClose={() => setShowViewModal(false)}
        title="View Template"
        size="lg"
      >
        {viewingTemplate && (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Template ID</label>
              <div className="px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-gray-900">
                {viewingTemplate.template_id}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
              <div className="px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-gray-900">
                {viewingTemplate.name}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
              <div className="px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-gray-900">
                {viewingTemplate.description}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
              <div className="px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-gray-900">
                {viewingTemplate.category}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
              <div className="px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg">
                <span className={`px-2 py-1 rounded text-xs ${viewingTemplate.is_system_default ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-800'}`}>
                  {viewingTemplate.is_system_default ? 'System Default' : 'Custom'}
                </span>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Prompt Text
              </label>
              <div className="px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg font-mono text-sm text-gray-900 whitespace-pre-wrap max-h-96 overflow-y-auto">
                {viewingTemplate.prompt_text}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Output Schema
              </label>
              <div className="px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg font-mono text-sm text-gray-900 whitespace-pre-wrap max-h-64 overflow-y-auto">
                {JSON.stringify(viewingTemplate.output_schema, null, 2)}
              </div>
            </div>

            {viewingTemplate.variables && viewingTemplate.variables.length > 0 && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Variables</label>
                <div className="px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg">
                  <div className="flex flex-wrap gap-2">
                    {viewingTemplate.variables.map((variable, idx) => (
                      <span key={idx} className="px-2 py-1 bg-blue-50 text-blue-700 rounded text-xs font-mono">
                        {'{' + variable + '}'}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
              <div className="px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg">
                <span className={`px-2 py-1 rounded text-xs ${viewingTemplate.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                  {viewingTemplate.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-4">
              <Button variant="outline" onClick={() => setShowViewModal(false)}>
                Close
              </Button>
              {!viewingTemplate.is_system_default && (
                <Button variant="primary" onClick={() => {
                  setShowViewModal(false);
                  handleEdit(viewingTemplate);
                }}>
                  Edit Template
                </Button>
              )}
            </div>
          </div>
        )}
      </Modal>

      {/* Create/Edit Modal */}
      <Modal
        isOpen={showModal}
        onClose={() => {
          setShowModal(false);
          setFormError(null);
        }}
        title={editingTemplate ? 'Edit Template' : 'Create Template'}
        size="xl"
      >
        <div className="space-y-4">
          {/* Error Alert */}
          {formError && (
            <ErrorAlert
              message={formError}
              title="Validation Error"
              variant="error"
              onDismiss={() => setFormError(null)}
            />
          )}

          {/* Mode Toggle */}
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg border border-gray-200">
            <div>
              <h4 className="font-semibold text-gray-800">
                {useSimpleMode ? '🎨 Simple Mode' : '🔧 Advanced Mode'}
              </h4>
              <p className="text-xs text-gray-600 mt-1">
                {useSimpleMode
                  ? 'User-friendly form builder - no technical knowledge required'
                  : 'Direct prompt and JSON schema editing for advanced users'
                }
              </p>
            </div>
            <button
              onClick={() => setUseSimpleMode(!useSimpleMode)}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
            >
              Switch to {useSimpleMode ? 'Advanced' : 'Simple'} Mode
            </button>
          </div>

          {/* Simple Mode - PromptBuilder */}
          {useSimpleMode ? (
            <PromptBuilder
              initialData={formData}
              onChange={(data) => setFormData(data)}
              isEditing={!!editingTemplate}
              onFinish={handleSave}
            />
          ) : (
            /* Advanced Mode - Raw Editing */
            <div className="space-y-4">
              <Input
                label="Template ID"
                value={formData.template_id}
                onChange={(e) => setFormData({ ...formData, template_id: e.target.value })}
                placeholder="e.g., my_custom_template_v1"
                disabled={!!editingTemplate}
                required
              />

              <Input
                label="Name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="e.g., My Custom Template"
                required
              />

              <Input
                label="Description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Brief description of the template"
                required
              />

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Category
                </label>
                <select
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="ecommerce">🛒 E-commerce</option>
                  <option value="social_media">📱 Social Media</option>
                  <option value="news">📰 News & Media</option>
                  <option value="marketing">📢 Marketing</option>
                  <option value="product_summary">📦 Product Summary</option>
                  <option value="section_content">📄 Section Content</option>
                  <option value="custom">⚙️ Custom</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Prompt Text
                  <span className="text-gray-500 text-xs ml-2">
                    (Use placeholders like {'{product_name}'}, {'{description}'}, etc.)
                  </span>
                </label>
                <textarea
                  value={formData.prompt_text}
                  onChange={(e) => setFormData({ ...formData, prompt_text: e.target.value })}
                  placeholder="Enter your prompt template here..."
                  rows={12}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Output Schema (JSON Schema)
                  <span className="text-gray-500 text-xs ml-2">
                    (Defines the structure of LLM output)
                  </span>
                </label>
                <textarea
                  value={typeof formData.output_schema === 'string' ? formData.output_schema : JSON.stringify(formData.output_schema, null, 2)}
                  onChange={(e) => setFormData({ ...formData, output_schema: e.target.value })}
                  placeholder='{"type": "object", "properties": {"content": {"type": "string"}}}'
                  rows={8}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                  required
                />
                <p className="mt-1 text-xs text-gray-500">
                  Example: {`{"type": "object", "required": ["title", "content"], "properties": {"title": {"type": "string"}, "content": {"type": "string"}}}`}
                </p>
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  checked={formData.is_active}
                  onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  className="mr-2"
                />
                <label className="text-sm font-medium text-gray-700">Active</label>
              </div>
            </div>
          )}

          {/* Only show Save/Cancel buttons in Advanced Mode */}
          {!useSimpleMode && (
            <div className="flex justify-end gap-2 pt-4 border-t border-gray-200">
              <Button variant="outline" onClick={() => {
                setShowModal(false);
                setFormError(null);
              }}>
                Cancel
              </Button>
              <Button variant="primary" onClick={handleSave}>
                {editingTemplate ? 'Update' : 'Create'}
              </Button>
            </div>
          )}
        </div>
      </Modal>

      {/* Toast Notifications */}
      <ToastContainer toasts={toasts} onDismiss={hideToast} position="top-right" />

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={deleteDialog.isOpen}
        onClose={() => setDeleteDialog({ isOpen: false, template: null })}
        onConfirm={confirmDelete}
        title="Delete Template"
        description="This action cannot be undone"
        message={
          deleteDialog.template
            ? `Are you sure you want to delete "${deleteDialog.template.name}"?`
            : ''
        }
        warningMessage="This will permanently delete the template. This action cannot be undone."
        confirmText="Delete Template"
        cancelText="Cancel"
        variant="danger"
      />
    </div>
  );
};

export default PromptTemplateManagementPage;

