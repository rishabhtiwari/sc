import React from 'react';
import { useToast } from '../../../hooks/useToast';

/**
 * Text Panel
 * Features: Add text, Headings, Subheadings, Body text
 */
const TextPanel = ({ onAddElement }) => {
  const { showToast } = useToast();

  const textPresets = [
    {
      id: 'heading',
      name: 'Heading',
      text: 'Add a heading',
      fontSize: 48,
      fontWeight: 'bold',
      color: '#000000'
    },
    {
      id: 'subheading',
      name: 'Subheading',
      text: 'Add a subheading',
      fontSize: 32,
      fontWeight: '600',
      color: '#374151'
    },
    {
      id: 'body',
      name: 'Body Text',
      text: 'Add body text',
      fontSize: 16,
      fontWeight: 'normal',
      color: '#6B7280'
    },
    {
      id: 'caption',
      name: 'Caption',
      text: 'Add a caption',
      fontSize: 12,
      fontWeight: 'normal',
      color: '#9CA3AF'
    }
  ];

  const handleAddText = (preset) => {
    onAddElement({
      type: 'text',
      text: preset.text,
      fontSize: preset.fontSize,
      fontWeight: preset.fontWeight,
      color: preset.color,
      fontFamily: 'Arial, sans-serif'
    });
    showToast(`${preset.name} added to canvas`, 'success');
  };

  return (
    <div className="space-y-6">
      {/* Text Presets */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-gray-900">Text Styles</h3>
        <div className="space-y-2">
          {textPresets.map((preset) => (
            <button
              key={preset.id}
              onClick={() => handleAddText(preset)}
              className="w-full p-4 border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all text-left"
            >
              <div
                style={{
                  fontSize: `${Math.min(preset.fontSize / 2, 24)}px`,
                  fontWeight: preset.fontWeight,
                  color: preset.color
                }}
              >
                {preset.text}
              </div>
              <div className="text-xs text-gray-500 mt-1">{preset.name}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Font Combinations */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-gray-900">Font Combinations</h3>
        <div className="space-y-2">
          <button className="w-full p-4 border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all text-left">
            <div className="font-bold text-lg">Modern Sans</div>
            <div className="text-sm text-gray-600">Clean and professional</div>
          </button>
          <button className="w-full p-4 border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all text-left">
            <div className="font-serif text-lg font-bold">Classic Serif</div>
            <div className="text-sm text-gray-600">Elegant and timeless</div>
          </button>
          <button className="w-full p-4 border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all text-left">
            <div className="font-mono text-lg font-bold">Tech Mono</div>
            <div className="text-sm text-gray-600">Modern and technical</div>
          </button>
        </div>
      </div>

      {/* Text Effects */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-gray-900">Text Effects</h3>
        <div className="grid grid-cols-2 gap-2">
          <button className="p-3 border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all text-center">
            <div className="text-2xl mb-1">🌈</div>
            <div className="text-xs font-medium">Gradient</div>
          </button>
          <button className="p-3 border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all text-center">
            <div className="text-2xl mb-1">💫</div>
            <div className="text-xs font-medium">Shadow</div>
          </button>
          <button className="p-3 border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all text-center">
            <div className="text-2xl mb-1">✨</div>
            <div className="text-xs font-medium">Glow</div>
          </button>
          <button className="p-3 border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all text-center">
            <div className="text-2xl mb-1">🎨</div>
            <div className="text-xs font-medium">Outline</div>
          </button>
        </div>
      </div>

      {/* Tips */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="text-sm font-semibold text-blue-900 mb-2">💡 Tips</h4>
        <ul className="text-xs text-blue-800 space-y-1">
          <li>• Double-click text to edit</li>
          <li>• Use consistent fonts for better design</li>
          <li>• Adjust spacing for readability</li>
        </ul>
      </div>
    </div>
  );
};

export default TextPanel;

