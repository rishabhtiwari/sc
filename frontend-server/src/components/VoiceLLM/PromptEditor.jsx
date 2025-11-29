import React, { useState } from 'react';
import { Card, Button, Input } from '../common';

/**
 * Prompt Editor Component - Edit LLM prompts with template variables
 */
const PromptEditor = ({ prompt, onSave, onCancel, loading }) => {
  const [formData, setFormData] = useState({
    name: prompt?.name || '',
    type: prompt?.type || 'summary',
    template: prompt?.template || '',
    description: prompt?.description || '',
    maxTokens: prompt?.maxTokens || 150,
    temperature: prompt?.temperature || 0.7,
    variables: prompt?.variables || [],
  });

  const [errors, setErrors] = useState({});

  const promptTypes = [
    { value: 'summary', label: 'News Summary' },
    { value: 'title', label: 'Title Generation' },
    { value: 'description', label: 'Description Generation' },
    { value: 'tags', label: 'Tags Generation' },
  ];

  const templateVariables = [
    { name: '{{title}}', description: 'Article title' },
    { name: '{{content}}', description: 'Article content/description' },
    { name: '{{summary}}', description: 'Short summary' },
    { name: '{{category}}', description: 'Article category' },
    { name: '{{source}}', description: 'Source name' },
    { name: '{{language}}', description: 'Article language' },
  ];

  const handleChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    // Clear error for this field
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: null }));
    }
  };

  const validate = () => {
    const newErrors = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    }

    if (!formData.template.trim()) {
      newErrors.template = 'Template is required';
    }

    if (formData.maxTokens < 1 || formData.maxTokens > 4000) {
      newErrors.maxTokens = 'Max tokens must be between 1 and 4000';
    }

    if (formData.temperature < 0 || formData.temperature > 2) {
      newErrors.temperature = 'Temperature must be between 0 and 2';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (validate()) {
      onSave(formData);
    }
  };

  const insertVariable = (variable) => {
    const textarea = document.getElementById('template-textarea');
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const text = formData.template;
    const newText = text.substring(0, start) + variable + text.substring(end);
    
    setFormData((prev) => ({ ...prev, template: newText }));
    
    // Set cursor position after inserted variable
    setTimeout(() => {
      textarea.focus();
      textarea.setSelectionRange(start + variable.length, start + variable.length);
    }, 0);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Basic Info */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Input
          label="Prompt Name"
          value={formData.name}
          onChange={(e) => handleChange('name', e.target.value)}
          error={errors.name}
          placeholder="e.g., News Summary Prompt"
          required
        />

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Prompt Type
          </label>
          <select
            value={formData.type}
            onChange={(e) => handleChange('type', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            {promptTypes.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Description */}
      <Input
        label="Description"
        value={formData.description}
        onChange={(e) => handleChange('description', e.target.value)}
        placeholder="Brief description of this prompt's purpose"
      />

      {/* Template Variables Reference */}
      <Card title="Available Template Variables" className="bg-blue-50">
        <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
          {templateVariables.map((variable) => (
            <button
              key={variable.name}
              type="button"
              onClick={() => insertVariable(variable.name)}
              className="text-left px-3 py-2 bg-white border border-blue-200 rounded-lg hover:bg-blue-100 hover:border-blue-300 transition-colors"
              title={`Click to insert: ${variable.description}`}
            >
              <code className="text-sm font-mono text-blue-700">{variable.name}</code>
              <p className="text-xs text-gray-600 mt-1">{variable.description}</p>
            </button>
          ))}
        </div>
      </Card>

      {/* Template */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Prompt Template *
        </label>
        <textarea
          id="template-textarea"
          value={formData.template}
          onChange={(e) => handleChange('template', e.target.value)}
          rows={8}
          className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm ${
            errors.template ? 'border-red-500' : 'border-gray-300'
          }`}
          placeholder="Enter your prompt template here. Use {{variable}} syntax for dynamic values."
        />
        {errors.template && (
          <p className="mt-1 text-sm text-red-600">{errors.template}</p>
        )}
        <p className="mt-1 text-sm text-gray-500">
          Use template variables like {`{{title}}`} to insert dynamic content
        </p>
      </div>

      {/* Generation Parameters */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Input
          label="Max Tokens"
          type="number"
          value={formData.maxTokens}
          onChange={(e) => handleChange('maxTokens', parseInt(e.target.value))}
          error={errors.maxTokens}
          min={1}
          max={4000}
          required
        />

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Temperature: {formData.temperature}
          </label>
          <input
            type="range"
            min="0"
            max="2"
            step="0.1"
            value={formData.temperature}
            onChange={(e) => handleChange('temperature', parseFloat(e.target.value))}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
          />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>Focused (0)</span>
            <span>Balanced (1)</span>
            <span>Creative (2)</span>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex justify-end gap-3 pt-4 border-t">
        <Button variant="secondary" onClick={onCancel} type="button">
          Cancel
        </Button>
        <Button variant="primary" type="submit" loading={loading}>
          Save Prompt
        </Button>
      </div>
    </form>
  );
};

export default PromptEditor;

