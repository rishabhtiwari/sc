import React, { useState, useEffect } from 'react';
import Button from '../Button';
import VariableManager from './VariableManager';
import OutputSchemaBuilder from './OutputSchemaBuilder';
import PromptPreview from './PromptPreview';
import AIPromptGenerator from './AIPromptGenerator';

/**
 * PromptBuilder - User-friendly prompt template builder
 *
 * Provides a visual interface for creating prompt templates without
 * requiring technical knowledge of prompts or JSON schemas.
 */
const PromptBuilder = ({ initialData = {}, onChange, isEditing = false, onFinish }) => {
  // When editing, start in manual mode; when creating new, start in AI mode
  const [mode, setMode] = useState(isEditing ? 'manual' : 'ai');
  const [activeTab, setActiveTab] = useState('basic'); // basic, variables, output, review, preview
  const [initialized, setInitialized] = useState(false); // Track if we've parsed initial data
  const [formData, setFormData] = useState({
    template_id: '',
    name: '',
    description: '',
    category: 'product_summary',

    // Prompt building blocks
    instruction: '',
    context_description: '',
    output_format_instruction: '',
    additional_instructions: '',

    // Variables
    variables: [],

    // Output schema (built from UI)
    output_fields: [],

    ...initialData
  });

  // Parse existing prompt_text back into component parts
  const parsePromptText = (promptText) => {
    if (!promptText) return {};

    const parsed = {
      instruction: '',
      context_description: '',
      output_format_instruction: '',
      additional_instructions: ''
    };

    // Extract Task section
    const taskMatch = promptText.match(/\*\*Task:\*\*\s*([^\n]*(?:\n(?!\*\*)[^\n]*)*)/);
    if (taskMatch) {
      parsed.instruction = taskMatch[1].trim();
    }

    // Extract Context section
    const contextMatch = promptText.match(/\*\*Context:\*\*\s*\n([^\n]*(?:\n(?!\*\*)[^\n]*)*)/);
    if (contextMatch) {
      parsed.context_description = contextMatch[1].trim();
    }

    // Extract Output Format section
    const outputFormatMatch = promptText.match(/\*\*Output Format:\*\*\s*\n([^\n]*(?:\n(?!\*\*)[^\n]*)*)/);
    if (outputFormatMatch) {
      parsed.output_format_instruction = outputFormatMatch[1].trim();
    }

    // Extract Additional Instructions section
    const additionalMatch = promptText.match(/\*\*Additional Instructions:\*\*\s*\n([^\n]*(?:\n(?!\*\*|Generate the JSON)[^\n]*)*)/);
    if (additionalMatch) {
      parsed.additional_instructions = additionalMatch[1].trim();
    }

    return parsed;
  };

  // When editing, parse the existing prompt_text and populate fields (only once)
  useEffect(() => {
    if (isEditing && initialData.prompt_text && !initialized) {
      const parsedPrompt = parsePromptText(initialData.prompt_text);
      setFormData(prev => ({
        ...prev,
        ...parsedPrompt,
        variables: initialData.variables || [],
        output_fields: parseOutputSchema(initialData.output_schema) || []
      }));
      setInitialized(true);
    }
  }, [isEditing, initialData.prompt_text, initialized]);

  // Convert form data to backend format (skip during initialization)
  useEffect(() => {
    // Only convert after initialization is complete
    if (!isEditing || initialized) {
      const backendData = convertToBackendFormat(formData);
      if (onChange) {
        onChange(backendData);
      }
    }
  }, [formData, initialized, isEditing]);

  const convertToBackendFormat = (data) => {
    // Build prompt_text from components
    let promptParts = [];

    if (data.instruction) {
      promptParts.push(`**Task:** ${data.instruction}`);
    }

    if (data.context_description) {
      promptParts.push(`\n**Context:**\n${data.context_description}`);
    }

    // Add variable placeholders
    if (data.variables && data.variables.length > 0) {
      promptParts.push('\n**Input Data:**');
      data.variables.forEach(v => {
        promptParts.push(`- ${v.description || v.name}: {${v.name}}`);
      });
    }

    if (data.output_format_instruction) {
      promptParts.push(`\n**Output Format:**\n${data.output_format_instruction}`);
    }

    if (data.additional_instructions) {
      promptParts.push(`\n**Additional Instructions:**\n${data.additional_instructions}`);
    }

    promptParts.push('\n\nGenerate the JSON response now:');

    const prompt_text = promptParts.join('\n');
    
    // Build output_schema from output_fields
    const output_schema = buildOutputSchema(data.output_fields);
    
    return {
      template_id: data.template_id,
      name: data.name,
      description: data.description,
      category: data.category,
      prompt_text,
      output_schema,
      variables: data.variables,
      is_active: true
    };
  };

  const buildOutputSchema = (fields) => {
    if (!fields || fields.length === 0) {
      return {
        type: 'object',
        properties: {
          content: { type: 'string' }
        }
      };
    }

    const properties = {};
    const required = [];

    fields.forEach(field => {
      if (field.required) {
        required.push(field.name);
      }

      if (field.type === 'text') {
        properties[field.name] = {
          type: 'string',
          ...(field.minLength && { minLength: parseInt(field.minLength) }),
          ...(field.maxLength && { maxLength: parseInt(field.maxLength) })
        };
      } else if (field.type === 'number') {
        properties[field.name] = {
          type: 'number',
          ...(field.min && { minimum: parseInt(field.min) }),
          ...(field.max && { maximum: parseInt(field.max) })
        };
      } else if (field.type === 'list') {
        properties[field.name] = {
          type: 'array',
          ...(field.minItems && { minItems: parseInt(field.minItems) }),
          ...(field.maxItems && { maxItems: parseInt(field.maxItems) }),
          items: field.itemSchema || { type: 'string' }
        };
      } else if (field.type === 'boolean') {
        properties[field.name] = { type: 'boolean' };
      }
    });

    return {
      type: 'object',
      ...(required.length > 0 && { required }),
      properties
    };
  };

  // Parse output_schema back to output_fields format for editing
  const parseOutputSchema = (schema) => {
    if (!schema || !schema.properties) {
      return [];
    }

    const fields = [];
    const required = schema.required || [];

    Object.entries(schema.properties).forEach(([name, prop]) => {
      const field = {
        name,
        required: required.includes(name),
        description: prop.description || ''
      };

      if (prop.type === 'string') {
        field.type = 'text';
        if (prop.minLength) field.minLength = prop.minLength;
        if (prop.maxLength) field.maxLength = prop.maxLength;
      } else if (prop.type === 'number') {
        field.type = 'number';
        if (prop.minimum !== undefined) field.min = prop.minimum;
        if (prop.maximum !== undefined) field.max = prop.maximum;
      } else if (prop.type === 'array') {
        field.type = 'list';
        if (prop.minItems) field.minItems = prop.minItems;
        if (prop.maxItems) field.maxItems = prop.maxItems;
        field.itemSchema = prop.items || { type: 'string' };
      } else if (prop.type === 'boolean') {
        field.type = 'boolean';
      }

      fields.push(field);
    });

    return fields;
  };

  const updateFormData = (updates) => {
    setFormData(prev => ({ ...prev, ...updates }));
  };

  const handleAIGenerate = (generatedData) => {
    // Populate form with AI-generated data
    // The backend sends: template_id, name, description, category, variables, output_fields, prompt_text, output_schema
    setFormData(prev => ({
      ...prev,
      template_id: generatedData.template_id || '',
      name: generatedData.name || '',
      description: generatedData.description || '',
      category: generatedData.category || 'product_summary',
      variables: generatedData.variables || [],
      output_fields: generatedData.output_fields || [],
      // Store the raw prompt_text for editing
      instruction: generatedData.prompt_text || '',
      context_description: '',
      output_format_instruction: '',
      additional_instructions: '',
    }));
    setMode('manual'); // Switch to manual mode for editing
    setActiveTab('preview'); // Show preview first so user can see what was generated
  };

  // AI Mode - Simple description-based generation
  if (mode === 'ai') {
    return (
      <div className="prompt-builder">
        <AIPromptGenerator
          onGenerate={handleAIGenerate}
          onCancel={() => setMode('manual')}
        />
      </div>
    );
  }

  // Manual Mode - Detailed form-based editing
  return (
    <div className="prompt-builder">
      {/* Success Message after AI Generation */}
      {formData.template_id && formData.template_id.startsWith('template_') && (
        <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex items-start">
            <span className="text-green-500 text-xl mr-3">✅</span>
            <div className="flex-1">
              <h4 className="text-sm font-semibold text-green-800 mb-1">
                AI Generated Template Ready!
              </h4>
              <p className="text-xs text-green-700">
                Review the generated template below. You can edit the prompt, add/remove input fields,
                modify output structure, and test with sample data in the Preview tab.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Mode Toggle */}
      <div className="mb-4 flex justify-between items-center">
        <div className="text-sm text-gray-600">
          <span className="font-medium">Edit Mode</span> - Customize your template
        </div>
        <Button
          variant="secondary"
          size="sm"
          onClick={() => setMode('ai')}
        >
          🤖 Generate New with AI
        </Button>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="flex space-x-4">
          {[
            { id: 'basic', label: '📝 Basic Info', icon: '📝' },
            { id: 'variables', label: '🔤 Input Fields', icon: '🔤' },
            { id: 'output', label: '📤 Output Structure', icon: '📤' },
            { id: 'review', label: '✅ Review', icon: '✅' },
            { id: 'preview', label: '🧪 Test Preview', icon: '🧪' }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2 font-medium text-sm border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="tab-content">
        {/* Basic Info Tab */}
        {activeTab === 'basic' && (
          <BasicInfoTab formData={formData} onChange={updateFormData} />
        )}

        {/* Variables Tab */}
        {activeTab === 'variables' && (
          <VariableManager
            variables={formData.variables}
            onChange={(variables) => updateFormData({ variables })}
          />
        )}

        {/* Output Schema Tab */}
        {activeTab === 'output' && (
          <OutputSchemaBuilder
            fields={formData.output_fields}
            onChange={(output_fields) => updateFormData({ output_fields })}
          />
        )}

        {/* Review Tab */}
        {activeTab === 'review' && (
          <ReviewTab
            data={convertToBackendFormat(formData)}
            onFinish={onFinish}
            onGoToPreview={() => setActiveTab('preview')}
          />
        )}

        {/* Preview Tab */}
        {activeTab === 'preview' && (
          <PromptPreview
            data={convertToBackendFormat(formData)}
            onFinish={onFinish}
          />
        )}
      </div>
    </div>
  );
};

/**
 * BasicInfoTab - Basic template information
 */
const BasicInfoTab = ({ formData, onChange }) => {
  return (
    <div className="space-y-6">
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
        <p className="text-sm text-blue-800">
          <strong>💡 Tip:</strong> Describe what you want the AI to do in simple terms.
          No technical knowledge required!
        </p>
      </div>

      {/* Template ID */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Template ID <span className="text-red-500">*</span>
          <span className="text-gray-500 text-xs ml-2">(Unique identifier, e.g., "my-product-video")</span>
        </label>
        <input
          type="text"
          value={formData.template_id}
          onChange={(e) => onChange({ template_id: e.target.value })}
          placeholder="e.g., ecommerce-product-video"
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          required
        />
      </div>

      {/* Template Name */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Template Name <span className="text-red-500">*</span>
          <span className="text-gray-500 text-xs ml-2">(Friendly name for display)</span>
        </label>
        <input
          type="text"
          value={formData.name}
          onChange={(e) => onChange({ name: e.target.value })}
          placeholder="e.g., E-commerce Product Video"
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          required
        />
      </div>

      {/* Description */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Description
          <span className="text-gray-500 text-xs ml-2">(What is this template for?)</span>
        </label>
        <textarea
          value={formData.description}
          onChange={(e) => onChange({ description: e.target.value })}
          placeholder="e.g., Creates engaging product videos for e-commerce platforms"
          rows={3}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {/* Category */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Category <span className="text-red-500">*</span>
        </label>
        <select
          value={formData.category}
          onChange={(e) => onChange({ category: e.target.value })}
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

      {/* Prompt Template */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Prompt Template <span className="text-red-500">*</span>
          <span className="text-gray-500 text-xs ml-2">(The instruction for the AI)</span>
        </label>
        <textarea
          value={formData.instruction}
          onChange={(e) => onChange({ instruction: e.target.value })}
          placeholder="e.g., Create an engaging product description for {product_name} that highlights its key features and benefits..."
          rows={10}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 font-mono text-sm"
          required
        />
        <p className="mt-2 text-xs text-gray-500">
          💡 Use {`{variable_name}`} to reference input fields. Edit this prompt to customize how the AI processes your data.
        </p>
      </div>
    </div>
  );
};

/**
 * ReviewTab - Review the complete template before saving
 */
const ReviewTab = ({ data, onFinish, onGoToPreview }) => {
  return (
    <div className="review-tab">
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
        <p className="text-sm text-blue-800">
          <strong>✅ Review Your Template</strong><br />
          Review all the details below. You can click <strong>Finish</strong> to save the template,
          or go to <strong>Test Preview</strong> to test it with sample data first.
        </p>
      </div>

      {/* Template Summary */}
      <div className="bg-white border border-gray-200 rounded-lg p-6 mb-6">
        <h3 className="text-lg font-semibold mb-4">📋 Template Information</h3>
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <span className="text-sm font-medium text-gray-600">Template ID:</span>
              <div className="mt-1 text-sm text-gray-800 font-mono bg-gray-50 px-3 py-2 rounded">
                {data.template_id || 'Not set'}
              </div>
            </div>
            <div>
              <span className="text-sm font-medium text-gray-600">Category:</span>
              <div className="mt-1 text-sm text-gray-800 bg-gray-50 px-3 py-2 rounded">
                {data.category || 'Not set'}
              </div>
            </div>
          </div>
          <div>
            <span className="text-sm font-medium text-gray-600">Name:</span>
            <div className="mt-1 text-sm text-gray-800 bg-gray-50 px-3 py-2 rounded">
              {data.name || 'Not set'}
            </div>
          </div>
          <div>
            <span className="text-sm font-medium text-gray-600">Description:</span>
            <div className="mt-1 text-sm text-gray-800 bg-gray-50 px-3 py-2 rounded">
              {data.description || 'Not set'}
            </div>
          </div>
        </div>
      </div>

      {/* Input Fields */}
      {data.variables && data.variables.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-lg p-6 mb-6">
          <h3 className="text-lg font-semibold mb-4">🔤 Input Fields ({data.variables.length})</h3>
          <div className="space-y-3">
            {data.variables.map((v, i) => (
              <div key={i} className="bg-gray-50 p-3 rounded border border-gray-200">
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-mono text-sm font-semibold text-blue-600">{`{${v.name}}`}</span>
                  <span className="text-xs px-2 py-0.5 bg-gray-200 rounded">{v.type}</span>
                  {v.required && <span className="text-xs px-2 py-0.5 bg-red-100 text-red-700 rounded">Required</span>}
                </div>
                <div className="text-sm text-gray-700">{v.description}</div>
                {v.default && (
                  <div className="text-xs text-gray-500 mt-1">Default: {v.default}</div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Output Fields */}
      {data.output_schema && data.output_schema.properties && (
        <div className="bg-white border border-gray-200 rounded-lg p-6 mb-6">
          <h3 className="text-lg font-semibold mb-4">
            📤 Output Fields ({Object.keys(data.output_schema.properties).length})
          </h3>
          <div className="space-y-3">
            {Object.entries(data.output_schema.properties).map(([name, schema]) => (
              <div key={name} className="bg-gray-50 p-3 rounded border border-gray-200">
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-semibold text-sm text-gray-800">{name}</span>
                  <span className="text-xs px-2 py-0.5 bg-gray-200 rounded">{schema.type}</span>
                  {data.output_schema.required?.includes(name) && (
                    <span className="text-xs px-2 py-0.5 bg-red-100 text-red-700 rounded">Required</span>
                  )}
                </div>
                {schema.description && (
                  <div className="text-sm text-gray-700">{schema.description}</div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Prompt Preview */}
      <div className="bg-white border border-gray-200 rounded-lg p-6 mb-6">
        <h3 className="text-lg font-semibold mb-4">📝 Prompt Template</h3>
        <div className="bg-gray-50 border border-gray-300 rounded-lg p-4 font-mono text-sm whitespace-pre-wrap max-h-96 overflow-y-auto">
          {data.prompt_text || 'No prompt defined'}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex justify-between items-center pt-4 border-t border-gray-200">
        <Button
          onClick={onGoToPreview}
          variant="secondary"
        >
          🧪 Test with Sample Data
        </Button>
        <Button
          onClick={onFinish}
          variant="primary"
        >
          ✅ Finish & Save Template
        </Button>
      </div>
    </div>
  );
};

export default PromptBuilder;

