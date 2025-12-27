import React, { useState, useEffect } from 'react';
import { Button, Spinner } from '../index';
import { useToast } from '../../../hooks/useToast';
import api from '../../../services/api';

/**
 * Generic Prompt Template Selector Component
 *
 * Allows users to select from available prompt templates or use custom prompts.
 * Can be used with any content generation workflow (products, articles, social posts, etc.)
 *
 * @param {Object} props
 * @param {string} props.category - Template category filter (e.g., 'product_summary', 'article_summary')
 * @param {string} props.selectedTemplateId - Currently selected template ID
 * @param {Function} props.onTemplateSelect - Callback when template is selected (templateId, templateData, templateVariables)
 * @param {boolean} props.showCustomPrompt - Show custom prompt option
 * @param {string} props.customPrompt - Custom prompt text
 * @param {Function} props.onCustomPromptChange - Callback when custom prompt changes
 * @param {Object} props.contextData - Context data from the product/content (e.g., product_name, description, price)
 * @param {Object} props.initialTemplateVariables - Initial template variables (for editing existing content)
 * @param {string} props.className - Additional CSS classes
 */
const PromptTemplateSelector = ({
  category = 'product_summary',
  selectedTemplateId = null,
  onTemplateSelect,
  showCustomPrompt = true,
  customPrompt = '',
  onCustomPromptChange,
  contextData = {},
  initialTemplateVariables = {},
  className = ''
}) => {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [useCustom, setUseCustom] = useState(false);
  const [templateVariables, setTemplateVariables] = useState(initialTemplateVariables);
  const [selectedTemplateData, setSelectedTemplateData] = useState(null);
  const [isInitialized, setIsInitialized] = useState(false);
  const { showToast } = useToast();

  // Fetch templates on mount
  useEffect(() => {
    fetchTemplates();
  }, [category]);

  // Load selected template data when templates are fetched and selectedTemplateId is provided
  useEffect(() => {
    if (selectedTemplateId && templates.length > 0 && !selectedTemplateData) {
      const template = templates.find(t => t.template_id === selectedTemplateId);
      if (template) {
        console.log('📋 Loading template data for editing:', template);
        setSelectedTemplateData(template);
      }
    }
  }, [selectedTemplateId, templates]);

  // Auto-populate template variables from context data when template changes
  // Priority: initialTemplateVariables > contextData > default values
  useEffect(() => {
    if (selectedTemplateData && selectedTemplateData.variables) {
      const autoPopulatedVars = {};

      selectedTemplateData.variables.forEach(variable => {
        // Priority 1: Use initial template variables (for editing)
        if (initialTemplateVariables[variable.name] !== undefined &&
            initialTemplateVariables[variable.name] !== null &&
            initialTemplateVariables[variable.name] !== '' &&
            !isInitialized) {
          autoPopulatedVars[variable.name] = initialTemplateVariables[variable.name];
        }
        // Priority 2: Try to auto-populate from contextData
        else if (contextData[variable.name] !== undefined &&
                 contextData[variable.name] !== null &&
                 contextData[variable.name] !== '') {
          autoPopulatedVars[variable.name] = contextData[variable.name];
        }
        // Priority 3: Use default value from template
        else if (variable.default) {
          autoPopulatedVars[variable.name] = variable.default;
        }
        // Priority 4: Empty string
        else {
          autoPopulatedVars[variable.name] = '';
        }
      });

      setTemplateVariables(autoPopulatedVars);
      setIsInitialized(true);

      // Notify parent component about auto-populated variables
      if (onTemplateSelect && selectedTemplateData.template_id) {
        onTemplateSelect(selectedTemplateData.template_id, selectedTemplateData, autoPopulatedVars);
      }
    }
  }, [selectedTemplateData]); // Only run when template changes, not when contextData or initialTemplateVariables change

  const fetchTemplates = async () => {
    try {
      setLoading(true);
      const response = await api.get('/prompt-templates', {
        params: { category, is_active: true }
      });

      if (response.data.status === 'success') {
        setTemplates(response.data.templates || []);

        // Auto-select first template if none selected
        if (!selectedTemplateId && response.data.templates.length > 0) {
          const defaultTemplate = response.data.templates.find(t => t.is_system_default)
            || response.data.templates[0];
          setSelectedTemplateData(defaultTemplate);
          onTemplateSelect?.(defaultTemplate.template_id, defaultTemplate, {});
        }
      }
    } catch (error) {
      console.error('Error fetching templates:', error);
      showToast('Failed to load prompt templates', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleTemplateChange = (e) => {
    const templateId = e.target.value;
    const template = templates.find(t => t.template_id === templateId);
    setSelectedTemplateData(template);
    // Note: Don't call onTemplateSelect here - the useEffect will handle it
    // after auto-populating variables from contextData
  };

  const handleVariableChange = (varName, value) => {
    const updatedVars = { ...templateVariables, [varName]: value };
    setTemplateVariables(updatedVars);

    // Notify parent component about the change
    onTemplateSelect?.(selectedTemplateId, selectedTemplateData, updatedVars);
  };

  /**
   * Validate all required template variables are filled
   * @returns {Object} { isValid: boolean, missingVars: Array }
   */
  const validateTemplateVariables = () => {
    if (!selectedTemplateData || !selectedTemplateData.variables) {
      return { isValid: true, missingVars: [] };
    }

    const requiredVars = selectedTemplateData.variables.filter(v => v.required);
    const missingVars = requiredVars.filter(v => {
      const value = templateVariables[v.name];
      // Check for empty string, null, undefined, or empty array
      if (value === null || value === undefined || value === '') {
        return true;
      }
      if (typeof value === 'string' && value.trim() === '') {
        return true;
      }
      if (Array.isArray(value) && value.length === 0) {
        return true;
      }
      return false;
    });

    return {
      isValid: missingVars.length === 0,
      missingVars: missingVars.map(v => v.description || v.name)
    };
  };

  const handleCustomToggle = () => {
    setUseCustom(!useCustom);
    if (!useCustom) {
      // Switching to custom mode
      onTemplateSelect?.(null, null, {});
    } else {
      // Switching back to template mode
      if (selectedTemplateId) {
        const template = templates.find(t => t.template_id === selectedTemplateId);
        onTemplateSelect?.(selectedTemplateId, template, templateVariables);
      }
    }
  };

  const getInputType = (varType) => {
    switch (varType) {
      case 'number':
        return 'number';
      case 'url':
        return 'url';
      case 'long_text':
        return 'textarea';
      default:
        return 'text';
    }
  };

  if (loading) {
    return (
      <div className={`flex items-center justify-center p-4 ${className}`}>
        <Spinner size="sm" />
        <span className="ml-2 text-gray-600">Loading templates...</span>
      </div>
    );
  }

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Template Selection Mode Toggle */}
      {showCustomPrompt && (
        <div className="flex items-center space-x-4">
          <label className="flex items-center cursor-pointer">
            <input
              type="radio"
              checked={!useCustom}
              onChange={() => handleCustomToggle()}
              className="mr-2"
            />
            <span className="text-sm font-medium text-gray-700">Use Template</span>
          </label>
          <label className="flex items-center cursor-pointer">
            <input
              type="radio"
              checked={useCustom}
              onChange={() => handleCustomToggle()}
              className="mr-2"
            />
            <span className="text-sm font-medium text-gray-700">Custom Prompt</span>
          </label>
        </div>
      )}

      {/* Template Selector */}
      {!useCustom && (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Prompt Template
            </label>
            <select
              value={selectedTemplateId || ''}
              onChange={handleTemplateChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">-- Select a template --</option>
              {templates.map((template) => (
                <option key={template.template_id} value={template.template_id}>
                  {template.name}
                  {template.is_system_default && ' (Default)'}
                </option>
              ))}
            </select>

            {/* Template Description */}
            {selectedTemplateData && (
              <p className="mt-2 text-sm text-gray-600">
                {selectedTemplateData.description}
              </p>
            )}
          </div>

          {/* Template Variables */}
          {selectedTemplateData && selectedTemplateData.variables && selectedTemplateData.variables.length > 0 && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h4 className="text-sm font-semibold text-blue-900 mb-3">📝 Template Parameters</h4>
              <div className="space-y-3">
                {selectedTemplateData.variables.map((variable) => {
                  const inputType = getInputType(variable.type);
                  const value = templateVariables[variable.name] || '';
                  const isAutoPopulated = contextData[variable.name] !== undefined &&
                                         contextData[variable.name] !== null &&
                                         contextData[variable.name] !== '';

                  return (
                    <div key={variable.name}>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        {variable.description || variable.name}
                        {variable.required && <span className="text-red-500 ml-1">*</span>}
                        {isAutoPopulated && (
                          <span className="ml-2 text-xs text-green-600 font-normal">
                            ✓ Auto-filled
                          </span>
                        )}
                      </label>

                      {inputType === 'textarea' ? (
                        <textarea
                          value={value}
                          onChange={(e) => handleVariableChange(variable.name, e.target.value)}
                          placeholder={variable.default || `Enter ${variable.description || variable.name}`}
                          rows={3}
                          className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm ${
                            isAutoPopulated ? 'bg-green-50 border-green-300' : 'border-gray-300'
                          }`}
                        />
                      ) : (
                        <input
                          type={inputType}
                          value={value}
                          onChange={(e) => handleVariableChange(variable.name, e.target.value)}
                          placeholder={variable.default || `Enter ${variable.description || variable.name}`}
                          className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm ${
                            isAutoPopulated ? 'bg-green-50 border-green-300' : 'border-gray-300'
                          }`}
                        />
                      )}

                      {variable.description && (
                        <p className="mt-1 text-xs text-gray-500">{variable.description}</p>
                      )}
                    </div>
                  );
                })}
              </div>

              <div className="mt-3 text-xs text-blue-700">
                <p>💡 <strong>Tip:</strong> Fields marked with ✓ are auto-filled from your product information. You can edit them if needed.</p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Custom Prompt Input */}
      {useCustom && showCustomPrompt && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Custom Prompt
          </label>
          <textarea
            value={customPrompt}
            onChange={(e) => onCustomPromptChange?.(e.target.value)}
            placeholder="Enter your custom prompt here..."
            rows={6}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
          />
        </div>
      )}
    </div>
  );
};

export default PromptTemplateSelector;

