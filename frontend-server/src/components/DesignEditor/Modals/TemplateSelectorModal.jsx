import React, { useState } from 'react';
import { getAllTemplates } from '../../../constants/slideTemplates';

/**
 * Template Selector Modal
 * Allows users to choose a slide template
 */
const TemplateSelectorModal = ({ isOpen, onClose, onSelectTemplate, text }) => {
  const [selectedTemplate, setSelectedTemplate] = useState('content');
  const templates = getAllTemplates();

  if (!isOpen) return null;

  const handleApply = () => {
    onSelectTemplate(selectedTemplate);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 bg-black bg-opacity-50 flex items-center justify-center">
      <div className="bg-white rounded-lg shadow-2xl w-[900px] max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-6 py-4 flex-shrink-0 rounded-t-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-3xl">🎨</span>
              <div>
                <h2 className="text-2xl font-bold">Choose Slide Template</h2>
                <p className="text-sm text-blue-100 mt-1">
                  Select a template to format your text into professional slides
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="text-white hover:text-gray-200 text-2xl font-bold transition-colors"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 flex-1 overflow-y-auto">
          {/* Template Grid */}
          <div className="grid grid-cols-3 gap-4 mb-6">
            {templates.map((template) => (
              <button
                key={template.id}
                onClick={() => setSelectedTemplate(template.id)}
                className={`
                  p-4 border-2 rounded-lg transition-all text-left
                  ${selectedTemplate === template.id
                    ? 'border-blue-600 bg-blue-50 shadow-lg'
                    : 'border-gray-200 hover:border-blue-300 hover:shadow-md'
                  }
                `}
              >
                {/* Template Icon */}
                <div className="text-4xl mb-3 text-center">{template.icon}</div>
                
                {/* Template Name */}
                <div className="font-semibold text-gray-900 mb-1 text-center">
                  {template.name}
                </div>
                
                {/* Template Description */}
                <div className="text-xs text-gray-600 text-center">
                  {template.description}
                </div>

                {/* Selected Indicator */}
                {selectedTemplate === template.id && (
                  <div className="mt-3 flex items-center justify-center gap-1 text-blue-600 text-sm font-medium">
                    <span>✓</span>
                    <span>Selected</span>
                  </div>
                )}
              </button>
            ))}
          </div>

          {/* Preview Section */}
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
            <h3 className="text-sm font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <span>👁️</span>
              Preview
            </h3>
            <div className="bg-white border-2 border-gray-300 rounded-lg p-8 min-h-[200px] flex items-center justify-center">
              {selectedTemplate === 'title' && (
                <div className="text-center">
                  <div className="text-4xl font-bold text-gray-900 mb-2">
                    Your Title Here
                  </div>
                  <div className="text-lg text-gray-600">Subtitle text</div>
                </div>
              )}
              {selectedTemplate === 'content' && (
                <div className="w-full">
                  <div className="text-3xl font-bold text-gray-900 mb-4">
                    Slide Title
                  </div>
                  <div className="text-base text-gray-700 leading-relaxed">
                    Your content text will appear here with proper formatting and spacing.
                  </div>
                </div>
              )}
              {selectedTemplate === 'bullets' && (
                <div className="w-full">
                  <div className="text-3xl font-bold text-gray-900 mb-4">
                    Key Points
                  </div>
                  <ul className="space-y-2 text-gray-700">
                    <li className="flex items-start gap-2">
                      <span className="text-blue-600">•</span>
                      <span>First bullet point</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-blue-600">•</span>
                      <span>Second bullet point</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-blue-600">•</span>
                      <span>Third bullet point</span>
                    </li>
                  </ul>
                </div>
              )}
              {selectedTemplate === 'quote' && (
                <div className="text-center">
                  <div className="text-2xl italic text-gray-800 mb-3">
                    "Your inspiring quote will appear here in beautiful typography"
                  </div>
                  <div className="text-sm text-gray-600">— Author Name</div>
                </div>
              )}
              {selectedTemplate === 'twoColumn' && (
                <div className="w-full">
                  <div className="text-3xl font-bold text-gray-900 mb-4 text-center">
                    Comparison
                  </div>
                  <div className="grid grid-cols-2 gap-6">
                    <div className="text-gray-700">
                      <div className="font-semibold mb-2">Left Column</div>
                      <div className="text-sm">Content for left side</div>
                    </div>
                    <div className="text-gray-700">
                      <div className="font-semibold mb-2">Right Column</div>
                      <div className="text-sm">Content for right side</div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="bg-gray-50 border-t border-gray-200 px-6 py-4 flex justify-between items-center">
          <div className="text-sm text-gray-600">
            💡 Tip: You can change the template later for individual slides
          </div>
          <div className="flex gap-3">
            <button
              onClick={onClose}
              className="px-5 py-2 text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleApply}
              className="px-5 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-md hover:from-blue-700 hover:to-purple-700 transition-colors font-medium"
            >
              Create Slides
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TemplateSelectorModal;

