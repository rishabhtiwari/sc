import React, { useState } from 'react';
import { Card, Button, Input, Spinner } from '../common';

/**
 * Prompt Tester Component - Test prompts with sample data
 */
const PromptTester = ({ prompt, onClose, onTest }) => {
  const [sampleData, setSampleData] = useState({
    title: 'Breaking: Major Tech Company Announces New AI Product',
    content: 'In a groundbreaking announcement today, a leading technology company unveiled its latest artificial intelligence product. The new AI system promises to revolutionize how businesses handle customer service and data analysis. Industry experts are calling it a game-changer that could reshape the competitive landscape.',
    summary: 'Tech company launches revolutionary AI product for business automation',
    category: 'Technology',
    source: 'Tech News Daily',
    language: 'en',
  });

  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleTest = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const testResult = await onTest(prompt, sampleData);
      setResult(testResult);
    } catch (err) {
      setError(err.message || 'Failed to test prompt');
    } finally {
      setLoading(false);
    }
  };

  const renderProcessedTemplate = () => {
    let processed = prompt.template;
    Object.keys(sampleData).forEach((key) => {
      const regex = new RegExp(`{{${key}}}`, 'g');
      processed = processed.replace(regex, sampleData[key]);
    });
    return processed;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Test Prompt</h2>
          <p className="text-gray-600 mt-1">{prompt.name}</p>
        </div>
        <Button variant="secondary" onClick={onClose}>
          Close
        </Button>
      </div>

      {/* Sample Data Input */}
      <Card title="Sample Data">
        <div className="space-y-4">
          <Input
            label="Title"
            value={sampleData.title}
            onChange={(e) => setSampleData({ ...sampleData, title: e.target.value })}
          />
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Content
            </label>
            <textarea
              value={sampleData.content}
              onChange={(e) => setSampleData({ ...sampleData, content: e.target.value })}
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Category"
              value={sampleData.category}
              onChange={(e) => setSampleData({ ...sampleData, category: e.target.value })}
            />
            <Input
              label="Source"
              value={sampleData.source}
              onChange={(e) => setSampleData({ ...sampleData, source: e.target.value })}
            />
          </div>
        </div>
      </Card>

      {/* Before: Processed Template */}
      <Card title="Before: Processed Template">
        <pre className="bg-gray-50 p-4 rounded-lg text-sm font-mono whitespace-pre-wrap overflow-x-auto">
          {renderProcessedTemplate()}
        </pre>
      </Card>

      {/* Test Button */}
      <div className="flex justify-center">
        <Button
          variant="primary"
          onClick={handleTest}
          loading={loading}
          disabled={loading}
          className="px-8"
        >
          {loading ? 'Testing...' : 'Run Test'}
        </Button>
      </div>

      {/* Error */}
      {error && (
        <Card className="bg-red-50 border-red-200">
          <div className="flex items-start gap-3">
            <svg
              className="h-5 w-5 text-red-600 mt-0.5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <div>
              <h3 className="text-sm font-medium text-red-800">Test Failed</h3>
              <p className="text-sm text-red-700 mt-1">{error}</p>
            </div>
          </div>
        </Card>
      )}

      {/* After: LLM Output */}
      {result && (
        <>
          <Card title="After: LLM Output" className="bg-green-50 border-green-200">
            <div className="bg-white p-4 rounded-lg">
              <pre className="text-sm whitespace-pre-wrap">{result.output}</pre>
            </div>
          </Card>

          {/* Statistics */}
          <Card title="Statistics">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-blue-50 p-4 rounded-lg">
                <p className="text-sm text-gray-600">Tokens Used</p>
                <p className="text-2xl font-bold text-blue-600">
                  {result.tokensUsed || 'N/A'}
                </p>
              </div>
              <div className="bg-green-50 p-4 rounded-lg">
                <p className="text-sm text-gray-600">Response Time</p>
                <p className="text-2xl font-bold text-green-600">
                  {result.responseTime ? `${result.responseTime}ms` : 'N/A'}
                </p>
              </div>
              <div className="bg-purple-50 p-4 rounded-lg">
                <p className="text-sm text-gray-600">Estimated Cost</p>
                <p className="text-2xl font-bold text-purple-600">
                  {result.estimatedCost ? `$${result.estimatedCost}` : 'N/A'}
                </p>
              </div>
              <div className="bg-orange-50 p-4 rounded-lg">
                <p className="text-sm text-gray-600">Model</p>
                <p className="text-lg font-bold text-orange-600">
                  {result.model || 'N/A'}
                </p>
              </div>
            </div>
          </Card>

          {/* Comparison */}
          <Card title="Comparison">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2">Input Length</h4>
                <p className="text-lg">{renderProcessedTemplate().length} characters</p>
              </div>
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2">Output Length</h4>
                <p className="text-lg">{result.output?.length || 0} characters</p>
              </div>
            </div>
          </Card>
        </>
      )}
    </div>
  );
};

export default PromptTester;

