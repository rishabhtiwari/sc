import React, { useState } from 'react';
import Button from '../Button';
import api from '../../../services/api';

/**
 * PromptPreview - Preview the generated prompt and schema
 *
 * Shows users what the final prompt will look like and allows
 * testing with sample data and getting LLM response.
 */
const PromptPreview = ({ data, onFinish }) => {
  const [showRawPrompt, setShowRawPrompt] = useState(false);
  const [showRawSchema, setShowRawSchema] = useState(false);
  const [sampleData, setSampleData] = useState({});
  const [isGenerating, setIsGenerating] = useState(false);
  const [llmResponse, setLlmResponse] = useState(null);
  const [llmError, setLlmError] = useState(null);

  // Generate sample data for variables
  const generateSampleData = () => {
    const samples = {};
    if (data.variables) {
      data.variables.forEach(v => {
        if (v.default) {
          samples[v.name] = v.default;
        } else if (v.type === 'text' || v.type === 'long_text') {
          samples[v.name] = `Sample ${v.description || v.name}`;
        } else if (v.type === 'number') {
          samples[v.name] = '100';
        } else if (v.type === 'url') {
          samples[v.name] = 'https://example.com';
        } else if (v.type === 'list') {
          samples[v.name] = 'Item 1, Item 2, Item 3';
        } else {
          samples[v.name] = `{${v.name}}`;
        }
      });
    }
    setSampleData(samples);
  };

  // Format prompt with sample data and include output schema
  const getFormattedPrompt = () => {
    let prompt = data.prompt_text || '';

    // Replace variable placeholders with sample data
    Object.keys(sampleData).forEach(key => {
      prompt = prompt.replace(new RegExp(`\\{${key}\\}`, 'g'), sampleData[key]);
    });

    // Add output schema to the prompt so LLM knows what structure to follow
    if (data.output_schema) {
      // Insert schema before "Generate the JSON response now:"
      const schemaInstruction = `\n**Required Output Schema:**\nYou MUST generate a JSON response that exactly matches this schema:\n\`\`\`json\n${JSON.stringify(data.output_schema, null, 2)}\n\`\`\`\n`;

      // Find the position to insert (before "Generate the JSON response now:")
      const generateIndex = prompt.indexOf('Generate the JSON response now:');
      if (generateIndex !== -1) {
        prompt = prompt.slice(0, generateIndex) + schemaInstruction + '\n' + prompt.slice(generateIndex);
      } else {
        // If not found, append at the end
        prompt += schemaInstruction;
      }
    }

    return prompt;
  };

  // Test the prompt with LLM
  const testPromptWithLLM = async () => {
    setIsGenerating(true);
    setLlmError(null);
    setLlmResponse(null);

    try {
      // Format the prompt with sample data
      const formattedPrompt = getFormattedPrompt();

      // Call LLM service via API proxy
      const response = await api.post('/llm/generate', {
        query: formattedPrompt,
        use_rag: false,
        detect_code: false
      });

      const result = response.data;

      if (result.status === 'success') {
        // Response can be in result.response or result.data.response
        const responseText = result.response || result.data?.response || 'No response generated';
        setLlmResponse(responseText);
      } else {
        setLlmError(result.error || 'Failed to generate response from LLM');
      }
    } catch (error) {
      console.error('Error testing prompt with LLM:', error);
      const errorMessage = error.response?.data?.error || error.message || 'Failed to test prompt';
      setLlmError(errorMessage);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="prompt-preview">
      <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 mb-6">
        <p className="text-sm text-purple-800">
          <strong>🧪 Test Preview Mode</strong><br />
          Test your template with sample data to see how the LLM will respond.
          Fill in sample values, click "Test Prompt with LLM", and review the output.
        </p>
      </div>

      {/* Prompt Testing Section */}
      <div className="bg-white border border-gray-200 rounded-lg p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">📝 Prompt Preview & Testing</h3>
          <div className="flex gap-2">
            <Button
              onClick={generateSampleData}
              variant="secondary"
              size="sm"
            >
              🎲 Fill Sample Data
            </Button>
            <Button
              onClick={() => setShowRawPrompt(!showRawPrompt)}
              variant="secondary"
              size="sm"
            >
              {showRawPrompt ? '👁️ Show Formatted' : '🔧 Show Raw'}
            </Button>
          </div>
        </div>

        {/* Sample Data Inputs */}
        {Object.keys(sampleData).length > 0 && (
          <div className="mb-4 p-4 bg-gray-50 rounded-lg">
            <h4 className="text-sm font-semibold mb-3">Sample Input Data:</h4>
            <div className="space-y-2">
              {Object.entries(sampleData).map(([key, value]) => (
                <div key={key} className="flex items-center gap-2">
                  <label className="text-xs font-mono text-gray-600 w-32">{key}:</label>
                  <input
                    type="text"
                    value={value}
                    onChange={(e) => setSampleData({ ...sampleData, [key]: e.target.value })}
                    className="flex-1 px-2 py-1 text-sm border border-gray-300 rounded"
                  />
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Prompt Display */}
        <div className="bg-gray-50 border border-gray-300 rounded-lg p-4 font-mono text-sm whitespace-pre-wrap mb-4">
          {showRawPrompt ? data.prompt_text : getFormattedPrompt()}
        </div>

        {/* Test Button */}
        <div className="flex justify-end">
          <Button
            onClick={testPromptWithLLM}
            variant="primary"
            disabled={isGenerating || Object.keys(sampleData).length === 0}
          >
            {isGenerating ? '⏳ Testing with LLM...' : '🧪 Test Prompt with LLM'}
          </Button>
        </div>

        {/* LLM Response */}
        {llmResponse && (
          <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
            <h4 className="text-sm font-semibold text-green-800 mb-2">✅ LLM Response:</h4>
            <div className="bg-white border border-green-300 rounded p-3 font-mono text-sm whitespace-pre-wrap">
              {llmResponse}
            </div>
          </div>
        )}

        {/* LLM Error */}
        {llmError && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <h4 className="text-sm font-semibold text-red-800 mb-2">❌ Error:</h4>
            <div className="text-sm text-red-700">{llmError}</div>
          </div>
        )}
      </div>

      {/* Schema Preview */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">📊 Output Schema</h3>
          <Button
            onClick={() => setShowRawSchema(!showRawSchema)}
            variant="secondary"
            size="sm"
          >
            {showRawSchema ? '📋 Show Summary' : '🔧 Show JSON'}
          </Button>
        </div>

        {showRawSchema ? (
          <div className="bg-gray-50 border border-gray-300 rounded-lg p-4 font-mono text-xs whitespace-pre-wrap overflow-x-auto">
            {JSON.stringify(data.output_schema, null, 2)}
          </div>
        ) : (
          <div className="space-y-2">
            {data.output_schema && data.output_schema.properties ? (
              Object.entries(data.output_schema.properties).map(([name, schema]) => (
                <div key={name} className="p-3 bg-gray-50 rounded border border-gray-200">
                  <div className="font-semibold text-sm text-gray-800 mb-1">{name}</div>
                  <div className="text-xs text-gray-600">
                    Type: {schema.type}
                    {schema.minLength && ` • Min: ${schema.minLength} chars`}
                    {schema.maxLength && ` • Max: ${schema.maxLength} chars`}
                    {schema.minItems && ` • Min: ${schema.minItems} items`}
                    {schema.maxItems && ` • Max: ${schema.maxItems} items`}
                    {schema.minimum !== undefined && ` • Min: ${schema.minimum}`}
                    {schema.maximum !== undefined && ` • Max: ${schema.maximum}`}
                  </div>
                </div>
              ))
            ) : (
              <p className="text-sm text-gray-500">No output schema defined</p>
            )}
          </div>
        )}
      </div>

      {/* Finish Button */}
      {onFinish && (
        <div className="mt-6 pt-6 border-t border-gray-200 flex justify-end">
          <Button
            onClick={onFinish}
            variant="primary"
            size="lg"
          >
            ✅ Finish & Save Template
          </Button>
        </div>
      )}
    </div>
  );
};

export default PromptPreview;

