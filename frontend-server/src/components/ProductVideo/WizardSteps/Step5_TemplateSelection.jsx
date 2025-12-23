import React, { useState, useEffect } from 'react';
import { Button } from '../../common';
import { templateService } from '../../../services';
import { useToast } from '../../../hooks/useToast';

/**
 * Step 5: Template Selection with User Templates & Variables
 */
const Step5_TemplateSelection = ({ formData, onComplete, onUpdate }) => {
  const [selectedTemplate, setSelectedTemplate] = useState(formData.template_id || null);
  const [templates, setTemplates] = useState([]);
  const [loadingTemplates, setLoadingTemplates] = useState(true);
  const [selectedTemplateDetails, setSelectedTemplateDetails] = useState(null);
  const [templateVariables, setTemplateVariables] = useState(formData.template_variables || {});
  const { showToast } = useToast();

  // Load templates from API (ecommerce category only)
  useEffect(() => {
    const fetchTemplates = async () => {
      try {
        setLoadingTemplates(true);
        const response = await templateService.listTemplates('ecommerce');

        if (response.status === 'success' && response.templates) {
          // Only show real templates from the API
          setTemplates(response.templates);
        } else {
          setTemplates([]);
        }
      } catch (error) {
        console.error('Error loading templates:', error);
        setTemplates([]);
      } finally {
        setLoadingTemplates(false);
      }
    };

    fetchTemplates();
  }, []);

  // Load selected template details when selection changes
  useEffect(() => {
    const loadTemplateDetails = async () => {
      if (!selectedTemplate) return;

      const template = templates.find(t => t.template_id === selectedTemplate);
      if (template) {
        setSelectedTemplateDetails(template);

        // Initialize template variables with defaults
        if (template.variables) {
          const initialVars = {};
          Object.entries(template.variables).forEach(([key, config]) => {
            if (config.default !== undefined) {
              initialVars[key] = templateVariables[key] || config.default;
            }
          });
          setTemplateVariables(initialVars);
        }
      }
    };

    loadTemplateDetails();
  }, [selectedTemplate, templates]);

  const handleTemplateSelect = (templateId) => {
    setSelectedTemplate(templateId);
    onUpdate({ template_id: templateId });
  };

  const handleVariableChange = (varName, value) => {
    const updatedVars = { ...templateVariables, [varName]: value };
    setTemplateVariables(updatedVars);
    onUpdate({ template_variables: updatedVars });
  };

  const handleNext = () => {
    // Validate required variables
    if (selectedTemplateDetails?.variables) {
      const missingVars = [];
      Object.entries(selectedTemplateDetails.variables).forEach(([key, config]) => {
        if (config.required && !templateVariables[key]) {
          missingVars.push(key);
        }
      });

      if (missingVars.length > 0) {
        showToast(`Please fill in required fields: ${missingVars.join(', ')}`, 'error');
        return;
      }
    }

    onComplete({
      template_id: selectedTemplate,
      template_variables: templateVariables
    });
  };

  const handleCreateTemplate = () => {
    // Open template management page in new tab
    window.open('/template-management', '_blank');
  };

  if (loadingTemplates) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading templates...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-xl font-semibold text-gray-900 mb-2">🎨 Template Selection</h3>
        <p className="text-gray-600">Choose a template for your product video</p>
      </div>

      {/* Template Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Existing Templates */}
        {templates.map((template) => (
          <button
            key={template.template_id}
            onClick={() => handleTemplateSelect(template.template_id)}
            className={`p-6 border-2 rounded-lg text-left transition-all ${
              selectedTemplate === template.template_id
                ? 'border-indigo-500 bg-indigo-50 shadow-lg'
                : 'border-gray-300 hover:border-indigo-300 hover:shadow-md'
            }`}
          >
            {/* Thumbnail or Preview */}
            {template.thumbnail ? (
              <div className="mb-4">
                <img
                  src={template.thumbnail}
                  alt={template.name}
                  className="w-full h-32 object-cover rounded-md"
                />
              </div>
            ) : (
              <div className="flex items-center justify-center mb-4">
                <div className="text-6xl">🎬</div>
              </div>
            )}

            {/* Template Info */}
            <div className="flex items-start justify-between mb-2">
              <h4 className="font-semibold text-gray-900 text-lg">
                {template.name}
              </h4>
              {selectedTemplate === template.template_id && (
                <span className="text-indigo-600 text-xl">✓</span>
              )}
            </div>
            <p className="text-sm text-gray-600 mb-4">{template.description || 'Custom template'}</p>

            {/* Selected Badge */}
            {selectedTemplate === template.template_id && (
              <div className="mt-4 bg-indigo-600 text-white text-center py-2 rounded-md font-medium">
                Selected
              </div>
            )}
          </button>
        ))}

        {/* Create Template Card */}
        <button
          onClick={handleCreateTemplate}
          className="p-6 border-2 border-dashed border-gray-300 rounded-lg text-center transition-all hover:border-indigo-400 hover:bg-indigo-50 hover:shadow-md"
        >
          <div className="flex flex-col items-center justify-center h-full min-h-[200px]">
            <div className="rounded-full bg-indigo-100 p-4 mb-4">
              <span className="text-4xl">➕</span>
            </div>
            <h4 className="font-semibold text-gray-900 text-lg mb-2">Create New Template</h4>
            <p className="text-sm text-gray-600">Design your own custom template</p>
          </div>
        </button>
      </div>

      {/* Template Variables Section */}
      {selectedTemplateDetails && selectedTemplateDetails.variables &&
       Object.keys(selectedTemplateDetails.variables).length > 0 && (
        <div className="bg-gradient-to-r from-purple-50 to-indigo-50 border-2 border-purple-200 rounded-lg p-6">
          <h4 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <span>⚙️</span>
            Template Variables
          </h4>
          <p className="text-sm text-gray-600 mb-4">
            Customize the template by providing values for these variables
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Object.entries(selectedTemplateDetails.variables).map(([varName, varConfig]) => (
              <div key={varName}>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {varConfig.description || varName}
                  {varConfig.required && <span className="text-red-500 ml-1">*</span>}
                </label>

                {varConfig.type === 'text' && (
                  <input
                    type="text"
                    value={templateVariables[varName] || ''}
                    onChange={(e) => handleVariableChange(varName, e.target.value)}
                    placeholder={varConfig.default || `Enter ${varName}`}
                    maxLength={varConfig.max_length}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  />
                )}

                {varConfig.type === 'color' && (
                  <div className="flex gap-2">
                    <input
                      type="color"
                      value={templateVariables[varName] || varConfig.default || '#000000'}
                      onChange={(e) => handleVariableChange(varName, e.target.value)}
                      className="h-10 w-20 border border-gray-300 rounded cursor-pointer"
                    />
                    <input
                      type="text"
                      value={templateVariables[varName] || varConfig.default || '#000000'}
                      onChange={(e) => handleVariableChange(varName, e.target.value)}
                      placeholder="#000000"
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>
                )}

                {varConfig.type === 'number' && (
                  <input
                    type="number"
                    value={templateVariables[varName] || ''}
                    onChange={(e) => handleVariableChange(varName, parseFloat(e.target.value))}
                    placeholder={varConfig.default?.toString() || '0'}
                    min={varConfig.min}
                    max={varConfig.max}
                    step={varConfig.step || 1}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                  />
                )}

                {varConfig.type === 'font' && (
                  <select
                    value={templateVariables[varName] || varConfig.default || ''}
                    onChange={(e) => handleVariableChange(varName, e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                  >
                    <option value="">Select font...</option>
                    <option value="Arial">Arial</option>
                    <option value="Arial-Bold">Arial Bold</option>
                    <option value="Helvetica">Helvetica</option>
                    <option value="Times-New-Roman">Times New Roman</option>
                    <option value="Georgia">Georgia</option>
                    <option value="Courier">Courier</option>
                  </select>
                )}

                {varConfig.description && (
                  <p className="text-xs text-gray-500 mt-1">{varConfig.description}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Template Preview Info */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="font-medium text-blue-900 mb-2">💡 Template Features:</h4>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• All templates are optimized for social media</li>
          <li>• Supports both 16:9 and 9:16 aspect ratios</li>
          <li>• Customizable colors and fonts</li>
          <li>• Professional animations and transitions</li>
        </ul>
      </div>

      <div className="flex justify-end">
        <Button variant="primary" onClick={handleNext}>
          Next: Preview & Generate →
        </Button>
      </div>
    </div>
  );
};

export default Step5_TemplateSelection;

