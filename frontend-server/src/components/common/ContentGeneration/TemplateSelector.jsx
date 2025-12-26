import React, { useState, useEffect } from 'react';
import { Button, AuthenticatedImage, AuthenticatedVideo } from '../';
import { useTemplates } from '../../../hooks/useTemplates';
import { useToast } from '../../../hooks/useToast';

/**
 * Generic Template Selector Component
 * Handles template selection and variable configuration
 * 
 * @param {Object} props
 * @param {string} props.initialTemplateId - Initial selected template ID
 * @param {Object} props.initialVariables - Initial template variables
 * @param {Function} props.onTemplateSelected - Callback when template is selected
 * @param {Function} props.onVariablesChange - Callback when variables change
 * @param {boolean} props.showVariables - Show variable configuration
 * @param {boolean} props.showPreview - Show template preview
 * @param {string} props.filterCategory - Filter templates by category
 * @param {string} props.className - Additional CSS classes
 */
const TemplateSelector = ({
  initialTemplateId = null,
  initialVariables = {},
  onTemplateSelected,
  onVariablesChange,
  showVariables = true,
  showPreview = true,
  filterCategory = null,
  className = ''
}) => {
  const {
    templates,
    selectedTemplate,
    selectedTemplateDetails,
    loading,
    error,
    selectTemplate,
    getTemplateVariables
  } = useTemplates(initialTemplateId);

  const { showToast } = useToast();

  const [templateVariables, setTemplateVariables] = useState(initialVariables);
  const [expandedPreview, setExpandedPreview] = useState(false);

  // Update variables when template changes
  useEffect(() => {
    if (selectedTemplateDetails) {
      const variables = getTemplateVariables();
      
      // Initialize variables with default values
      const initializedVars = {};
      variables.forEach(variable => {
        initializedVars[variable.name] = initialVariables[variable.name] || variable.default || '';
      });
      
      setTemplateVariables(initializedVars);
    }
  }, [selectedTemplateDetails, getTemplateVariables, initialVariables]);

  /**
   * Handle template selection
   */
  const handleTemplateSelect = async (templateId) => {
    const template = await selectTemplate(templateId);
    
    if (template && onTemplateSelected) {
      onTemplateSelected(templateId, template);
    }
  };

  /**
   * Handle variable change
   */
  const handleVariableChange = (variableName, value) => {
    const newVariables = {
      ...templateVariables,
      [variableName]: value
    };
    
    setTemplateVariables(newVariables);
    
    if (onVariablesChange) {
      onVariablesChange(newVariables);
    }
  };

  // Filter templates by category if specified
  const filteredTemplates = filterCategory
    ? templates.filter(t => t.category === filterCategory)
    : templates;

  if (loading) {
    return (
      <div className="text-center py-8">
        <div className="animate-spin text-4xl mb-2">⚙️</div>
        <p className="text-gray-600">Loading templates...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8 text-red-600">
        <p>Error loading templates: {error}</p>
      </div>
    );
  }

  return (
    <div className={`template-selector ${className}`}>
      {/* Template Grid */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Select Template
        </label>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {filteredTemplates.map((template) => (
            <button
              key={template._id}
              onClick={() => handleTemplateSelect(template._id)}
              className={`border rounded-lg p-4 text-left transition-all ${
                selectedTemplate === template._id
                  ? 'border-indigo-500 bg-indigo-50 ring-2 ring-indigo-500'
                  : 'border-gray-300 hover:border-indigo-300'
              }`}
            >
              {/* Template Thumbnail */}
              {template.thumbnail_url && (
                <div className="mb-2 rounded overflow-hidden">
                  <AuthenticatedImage
                    src={template.thumbnail_url}
                    alt={template.name}
                    className="w-full h-32 object-cover"
                  />
                </div>
              )}
              
              {/* Template Info */}
              <h3 className="font-semibold text-gray-800">{template.name}</h3>
              <p className="text-sm text-gray-600 mt-1">{template.description}</p>
              
              {/* Template Metadata */}
              <div className="flex items-center gap-2 mt-2 text-xs text-gray-500">
                <span>{template.resolution || '1920x1080'}</span>
                <span>•</span>
                <span>{template.duration || '30'}s</span>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Template Variables */}
      {showVariables && selectedTemplateDetails && getTemplateVariables().length > 0 && (
        <div className="mt-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Template Variables
          </label>
          <div className="space-y-3">
            {getTemplateVariables().map((variable) => (
              <div key={variable.name}>
                <label className="block text-sm text-gray-600 mb-1">
                  {variable.label || variable.name}
                  {variable.required && <span className="text-red-500 ml-1">*</span>}
                </label>
                
                {variable.type === 'text' && (
                  <input
                    type="text"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    value={templateVariables[variable.name] || ''}
                    onChange={(e) => handleVariableChange(variable.name, e.target.value)}
                    placeholder={variable.placeholder || ''}
                  />
                )}
                
                {variable.type === 'textarea' && (
                  <textarea
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    rows="3"
                    value={templateVariables[variable.name] || ''}
                    onChange={(e) => handleVariableChange(variable.name, e.target.value)}
                    placeholder={variable.placeholder || ''}
                  />
                )}
                
                {variable.type === 'number' && (
                  <input
                    type="number"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    value={templateVariables[variable.name] || ''}
                    onChange={(e) => handleVariableChange(variable.name, e.target.value)}
                    placeholder={variable.placeholder || ''}
                  />
                )}
                
                {variable.description && (
                  <p className="text-xs text-gray-500 mt-1">{variable.description}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Template Preview */}
      {showPreview && selectedTemplateDetails && selectedTemplateDetails.preview_url && (
        <div className="mt-6">
          <div className="flex items-center justify-between mb-2">
            <label className="block text-sm font-medium text-gray-700">
              Template Preview
            </label>
            <Button
              size="sm"
              variant="outline"
              onClick={() => setExpandedPreview(!expandedPreview)}
            >
              {expandedPreview ? '🔽 Collapse' : '🔼 Expand'}
            </Button>
          </div>
          
          {expandedPreview && (
            <div className="border border-gray-300 rounded-lg overflow-hidden">
              <AuthenticatedVideo
                src={selectedTemplateDetails.preview_url}
                controls
                className="w-full"
              />
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default TemplateSelector;

