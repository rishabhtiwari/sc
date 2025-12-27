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
 * @param {Function} props.onTemplateSelect - Callback when template is selected (templateId, templateData)
 * @param {boolean} props.showCustomPrompt - Show custom prompt option
 * @param {string} props.customPrompt - Custom prompt text
 * @param {Function} props.onCustomPromptChange - Callback when custom prompt changes
 * @param {string} props.className - Additional CSS classes
 */
const PromptTemplateSelector = ({
  category = 'product_summary',
  selectedTemplateId = null,
  onTemplateSelect,
  showCustomPrompt = true,
  customPrompt = '',
  onCustomPromptChange,
  className = ''
}) => {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [useCustom, setUseCustom] = useState(false);
  const { showToast } = useToast();

  // Fetch templates on mount
  useEffect(() => {
    fetchTemplates();
  }, [category]);

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
          onTemplateSelect?.(defaultTemplate.template_id, defaultTemplate);
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
    onTemplateSelect?.(templateId, template);
  };

  const handleCustomToggle = () => {
    setUseCustom(!useCustom);
    if (!useCustom) {
      // Switching to custom mode
      onTemplateSelect?.(null, null);
    } else {
      // Switching back to template mode
      if (selectedTemplateId) {
        const template = templates.find(t => t.template_id === selectedTemplateId);
        onTemplateSelect?.(selectedTemplateId, template);
      }
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
          {selectedTemplateId && templates.find(t => t.template_id === selectedTemplateId) && (
            <p className="mt-2 text-sm text-gray-600">
              {templates.find(t => t.template_id === selectedTemplateId).description}
            </p>
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

