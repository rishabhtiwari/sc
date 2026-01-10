import React, { useState } from 'react';
import { useToast } from '../../../hooks/useToast';

/**
 * AI Tools Panel
 * Features: Image Generation, Background Removal, Image Enhancement, etc.
 */
const AIToolsPanel = ({ onAddElement }) => {
  const [generating, setGenerating] = useState(false);
  const [prompt, setPrompt] = useState('');
  const { showToast } = useToast();

  const aiTools = [
    {
      id: 'generate-image',
      name: 'Generate Image',
      icon: '🎨',
      description: 'Create images with AI',
      action: 'generate'
    },
    {
      id: 'remove-background',
      name: 'Remove Background',
      icon: '✂️',
      description: 'Remove image background',
      action: 'remove-bg'
    },
    {
      id: 'enhance-image',
      name: 'Enhance Image',
      icon: '✨',
      description: 'Improve image quality',
      action: 'enhance'
    },
    {
      id: 'generate-text',
      name: 'AI Text',
      icon: '📝',
      description: 'Generate text with AI',
      action: 'generate-text'
    }
  ];

  const handleGenerateImage = async () => {
    if (!prompt.trim()) {
      showToast('Please enter a prompt', 'error');
      return;
    }

    setGenerating(true);
    try {
      // TODO: Integrate with your AI image generation API
      showToast('AI image generation coming soon!', 'info');
      
      // Example: Add generated image to canvas
      // const response = await api.post('/api/ai/generate-image', { prompt });
      // onAddElement({
      //   type: 'image',
      //   src: response.data.image_url,
      //   width: 400,
      //   height: 400
      // });
    } catch (error) {
      showToast('Failed to generate image', 'error');
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* AI Image Generation */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-gray-900">Generate Image with AI</h3>
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Describe the image you want to create..."
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
          rows={4}
        />
        <button
          onClick={handleGenerateImage}
          disabled={generating}
          className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {generating ? 'Generating...' : 'Generate Image'}
        </button>
      </div>

      {/* AI Tools Grid */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-gray-900">AI Tools</h3>
        <div className="grid grid-cols-2 gap-3">
          {aiTools.map((tool) => (
            <button
              key={tool.id}
              onClick={() => showToast(`${tool.name} coming soon!`, 'info')}
              className="p-4 border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all text-left"
            >
              <div className="text-2xl mb-2">{tool.icon}</div>
              <div className="text-sm font-medium text-gray-900">{tool.name}</div>
              <div className="text-xs text-gray-500 mt-1">{tool.description}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Quick Tips */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="text-sm font-semibold text-blue-900 mb-2">💡 Tips</h4>
        <ul className="text-xs text-blue-800 space-y-1">
          <li>• Be specific in your prompts for better results</li>
          <li>• Try different styles: realistic, cartoon, 3D</li>
          <li>• Use AI tools to enhance your designs</li>
        </ul>
      </div>
    </div>
  );
};

export default AIToolsPanel;

