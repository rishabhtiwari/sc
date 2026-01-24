import React from 'react';

/**
 * Text Panel - Add text elements to slides
 */
const TextPanel = ({ onAddElement }) => {
  const textPresets = [
    { id: 'heading', name: 'Heading', text: 'Add a heading', fontSize: 48, fontWeight: 'bold', color: '#000000' },
    { id: 'subheading', name: 'Subheading', text: 'Add a subheading', fontSize: 32, fontWeight: '600', color: '#374151' },
    { id: 'body', name: 'Body Text', text: 'Add body text', fontSize: 16, fontWeight: 'normal', color: '#6B7280' },
    { id: 'caption', name: 'Caption', text: 'Add a caption', fontSize: 12, fontWeight: 'normal', color: '#9CA3AF' }
  ];

  const handleAddText = (preset) => {
    onAddElement({
      type: 'text',
      text: preset.text,
      fontSize: preset.fontSize,
      fontWeight: preset.fontWeight,
      color: preset.color,
      fontFamily: preset.fontFamily || 'Arial, sans-serif',
      gradient: preset.gradient,
      textShadow: preset.textShadow,
      textStroke: preset.textStroke
    });
  };

  return (
    <div className="space-y-4">
      {/* Add Text Elements */}
      <div>
        <h3 className="text-sm font-semibold text-gray-900 mb-3">✏️ Add Text</h3>
        <div className="grid grid-cols-2 gap-2">
          {textPresets.map((preset) => (
            <button
              key={preset.id}
              onClick={() => handleAddText(preset)}
              className="p-3 border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all text-left"
            >
              <div style={{ fontSize: `${Math.min(preset.fontSize / 2, 20)}px`, fontWeight: preset.fontWeight, color: preset.color }}>
                {preset.text}
              </div>
              <div className="text-xs text-gray-500 mt-1">{preset.name}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Text Effects */}
      <div>
        <h3 className="text-sm font-semibold text-gray-900 mb-3">🎨 Text Effects</h3>
        <div className="grid grid-cols-2 gap-2">
          <button 
            onClick={() => handleAddText({ text: 'Gradient Text', fontSize: 48, fontWeight: 'bold', color: '#667eea', gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' })} 
            className="p-3 border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all text-center"
          >
            <div className="text-2xl mb-1">🌈</div>
            <div className="text-xs font-medium">Gradient</div>
          </button>
          <button 
            onClick={() => handleAddText({ text: 'Shadow Text', fontSize: 48, fontWeight: 'bold', color: '#1f2937', textShadow: '2px 2px 4px rgba(0,0,0,0.3)' })} 
            className="p-3 border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all text-center"
          >
            <div className="text-2xl mb-1">💫</div>
            <div className="text-xs font-medium">Shadow</div>
          </button>
          <button 
            onClick={() => handleAddText({ text: 'Glow Text', fontSize: 48, fontWeight: 'bold', color: '#ffffff', textShadow: '0 0 10px #667eea, 0 0 20px #667eea' })} 
            className="p-3 border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all text-center"
          >
            <div className="text-2xl mb-1">✨</div>
            <div className="text-xs font-medium">Glow</div>
          </button>
          <button 
            onClick={() => handleAddText({ text: 'Outline Text', fontSize: 48, fontWeight: 'bold', color: 'transparent', textStroke: '2px #1f2937' })} 
            className="p-3 border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all text-center"
          >
            <div className="text-2xl mb-1">🎨</div>
            <div className="text-xs font-medium">Outline</div>
          </button>
        </div>
      </div>

      {/* Font Styles */}
      <div>
        <h3 className="text-sm font-semibold text-gray-900 mb-3">🔤 Font Styles</h3>
        <div className="space-y-2">
          <button 
            onClick={() => handleAddText({ text: 'Modern Sans', fontSize: 32, fontWeight: '600', color: '#1f2937', fontFamily: 'Inter, -apple-system, sans-serif' })} 
            className="w-full p-3 border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all text-left"
          >
            <div className="font-semibold text-base">Modern Sans</div>
            <div className="text-xs text-gray-500">Clean and professional</div>
          </button>
          <button 
            onClick={() => handleAddText({ text: 'Classic Serif', fontSize: 32, fontWeight: '600', color: '#1f2937', fontFamily: 'Georgia, serif' })} 
            className="w-full p-3 border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all text-left"
          >
            <div className="font-serif font-semibold text-base">Classic Serif</div>
            <div className="text-xs text-gray-500">Elegant and timeless</div>
          </button>
          <button 
            onClick={() => handleAddText({ text: 'Tech Mono', fontSize: 28, fontWeight: '500', color: '#1f2937', fontFamily: 'Monaco, monospace' })} 
            className="w-full p-3 border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all text-left"
          >
            <div className="font-mono font-medium text-base">Tech Mono</div>
            <div className="text-xs text-gray-500">Modern and technical</div>
          </button>
        </div>
      </div>

      {/* Info Box */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="text-sm font-semibold text-blue-900 mb-2">💡 Tips</h4>
        <ul className="text-xs text-blue-800 space-y-1">
          <li>• Click any text style to add it to your slide</li>
          <li>• Apply effects like gradient, shadow, and glow</li>
          <li>• Double-click text on canvas to edit</li>
          <li>• Drag text elements to reposition them</li>
        </ul>
      </div>
    </div>
  );
};

export default TextPanel;

