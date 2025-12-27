import React, { useState } from 'react';
import Button from '../Button';
import Spinner from '../Spinner';
import api from '../../../services/api';

/**
 * AIPromptGenerator - AI-powered prompt template generator
 *
 * User describes what they want in natural language, and AI generates:
 * - Complete prompt template
 * - Input variables
 * - Output schema
 * - Sample preview
 */
const AIPromptGenerator = ({ onGenerate, onCancel }) => {
  const [description, setDescription] = useState('');
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState('');

  const handleGenerate = async () => {
    if (!description.trim()) {
      setError('Please describe what you want the AI to do');
      return;
    }

    setGenerating(true);
    setError('');

    try {
      const response = await api.post('/prompt-templates/generate', {
        description: description.trim(),
      });

      if (response.data.status === 'success' && response.data.data) {
        onGenerate(response.data.data);
      } else {
        throw new Error('Invalid response from server');
      }
    } catch (err) {
      console.error('Error generating prompt:', err);
      const errorMessage = err.response?.data?.message || err.message || 'Failed to generate prompt template. Please try again.';
      setError(errorMessage);
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <div className="text-4xl mb-3">🤖</div>
        <h3 className="text-xl font-semibold text-gray-800 mb-2">
          AI-Powered Prompt Generator
        </h3>
        <p className="text-sm text-gray-600">
          Simply describe what you want the AI to do, and we'll generate a complete prompt template for you
        </p>
      </div>

      {/* Description Input */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Describe what you need in simple terms <span className="text-red-500">*</span>
        </label>
        <textarea
          value={description}
          onChange={(e) => {
            setDescription(e.target.value);
            setError('');
          }}
          placeholder="Example: I want to create product pitch for e-commerce products"
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
          rows={6}
          disabled={generating}
        />
        <p className="mt-2 text-xs text-gray-500">
          💡 Just describe what you want - the AI will figure out the inputs, outputs, and prompt structure
        </p>
      </div>

      {/* Error Message */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-start">
            <span className="text-red-500 mr-2">⚠️</span>
            <p className="text-sm text-red-700">{error}</p>
          </div>
        </div>
      )}

      {/* Examples */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="text-sm font-semibold text-blue-800 mb-2">📝 Example Descriptions:</h4>
        <ul className="text-xs text-blue-700 space-y-2">
          <li>• "I want to create product pitch for e-commerce products"</li>
          <li>• "Generate social media posts from news articles"</li>
          <li>• "Create video scripts for product demos"</li>
          <li>• "Summarize long articles into key points"</li>
        </ul>
        <p className="text-xs text-blue-600 mt-3">
          The AI will automatically determine what inputs are needed and what outputs to generate. You can edit everything after generation!
        </p>
      </div>

      {/* Action Buttons */}
      <div className="flex justify-end space-x-3 pt-4 border-t">
        <Button
          variant="secondary"
          onClick={onCancel}
          disabled={generating}
        >
          Cancel
        </Button>
        <Button
          variant="primary"
          onClick={handleGenerate}
          disabled={generating || !description.trim()}
        >
          {generating ? (
            <>
              <Spinner size="sm" className="mr-2" />
              Generating...
            </>
          ) : (
            <>
              ✨ Generate Prompt Template
            </>
          )}
        </Button>
      </div>
    </div>
  );
};

export default AIPromptGenerator;

