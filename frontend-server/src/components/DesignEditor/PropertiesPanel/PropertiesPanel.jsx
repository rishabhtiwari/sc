import React from 'react';

/**
 * Properties Panel - Edit selected element properties
 * Professional design with organized sections
 */
const PropertiesPanel = ({ element, onUpdate, onDelete }) => {
  if (!element) {
    return (
      <div className="w-80 bg-white border-l border-gray-200 flex items-center justify-center p-8">
        <div className="text-center">
          <div className="text-6xl mb-4">👆</div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No Selection</h3>
          <p className="text-sm text-gray-500">Click on an element to edit its properties</p>
        </div>
      </div>
    );
  }

  const renderProperties = () => {
    switch (element.type) {
      case 'text':
        return (
          <div className="space-y-6">
            {/* Text Content Section */}
            <div className="bg-gray-50 rounded-lg p-4">
              <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wide mb-2">
                ✏️ Text Content
              </label>
              <textarea
                value={element.text}
                onChange={(e) => onUpdate({ text: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none text-sm"
                rows={4}
                placeholder="Enter text..."
              />
              <p className="text-xs text-gray-500 mt-2">💡 Tip: Double-click text on canvas to edit directly</p>
            </div>

            {/* Typography Section */}
            <div className="bg-gray-50 rounded-lg p-4">
              <h4 className="text-xs font-semibold text-gray-700 uppercase tracking-wide mb-3">
                🔤 Typography
              </h4>

              {/* Font Size */}
              <div className="mb-4">
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm font-medium text-gray-700">Font Size</label>
                  <span className="text-sm font-semibold text-blue-600">{element.fontSize}px</span>
                </div>
                <input
                  type="range"
                  min="8"
                  max="120"
                  value={element.fontSize}
                  onChange={(e) => onUpdate({ fontSize: parseInt(e.target.value) })}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                />
              </div>

              {/* Font Weight */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">Font Weight</label>
                <div className="grid grid-cols-3 gap-2">
                  <button
                    onClick={() => onUpdate({ fontWeight: 'normal' })}
                    className={`px-3 py-2 rounded-lg text-sm font-normal transition-all ${
                      element.fontWeight === 'normal'
                        ? 'bg-blue-600 text-white'
                        : 'bg-white border border-gray-300 text-gray-700 hover:border-blue-500'
                    }`}
                  >
                    Normal
                  </button>
                  <button
                    onClick={() => onUpdate({ fontWeight: '600' })}
                    className={`px-3 py-2 rounded-lg text-sm font-semibold transition-all ${
                      element.fontWeight === '600'
                        ? 'bg-blue-600 text-white'
                        : 'bg-white border border-gray-300 text-gray-700 hover:border-blue-500'
                    }`}
                  >
                    Semi
                  </button>
                  <button
                    onClick={() => onUpdate({ fontWeight: 'bold' })}
                    className={`px-3 py-2 rounded-lg text-sm font-bold transition-all ${
                      element.fontWeight === 'bold'
                        ? 'bg-blue-600 text-white'
                        : 'bg-white border border-gray-300 text-gray-700 hover:border-blue-500'
                    }`}
                  >
                    Bold
                  </button>
                </div>
              </div>

              {/* Text Alignment */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Text Align</label>
                <div className="grid grid-cols-3 gap-2">
                  <button
                    onClick={() => onUpdate({ textAlign: 'left' })}
                    className={`px-3 py-2 rounded-lg text-sm transition-all ${
                      (element.textAlign || 'left') === 'left'
                        ? 'bg-blue-600 text-white'
                        : 'bg-white border border-gray-300 text-gray-700 hover:border-blue-500'
                    }`}
                  >
                    ⬅️ Left
                  </button>
                  <button
                    onClick={() => onUpdate({ textAlign: 'center' })}
                    className={`px-3 py-2 rounded-lg text-sm transition-all ${
                      element.textAlign === 'center'
                        ? 'bg-blue-600 text-white'
                        : 'bg-white border border-gray-300 text-gray-700 hover:border-blue-500'
                    }`}
                  >
                    ↔️ Center
                  </button>
                  <button
                    onClick={() => onUpdate({ textAlign: 'right' })}
                    className={`px-3 py-2 rounded-lg text-sm transition-all ${
                      element.textAlign === 'right'
                        ? 'bg-blue-600 text-white'
                        : 'bg-white border border-gray-300 text-gray-700 hover:border-blue-500'
                    }`}
                  >
                    ➡️ Right
                  </button>
                </div>
              </div>
            </div>

            {/* Color Section */}
            <div className="bg-gray-50 rounded-lg p-4">
              <h4 className="text-xs font-semibold text-gray-700 uppercase tracking-wide mb-3">
                🎨 Color
              </h4>
              <div className="flex items-center gap-3">
                <input
                  type="color"
                  value={element.color}
                  onChange={(e) => onUpdate({ color: e.target.value })}
                  className="w-16 h-16 rounded-lg cursor-pointer border-2 border-gray-300"
                />
                <div className="flex-1">
                  <div className="text-sm font-medium text-gray-700 mb-1">Text Color</div>
                  <div className="text-xs text-gray-500 font-mono">{element.color}</div>
                </div>
              </div>
            </div>
          </div>
        );

      case 'image':
        return (
          <div className="space-y-6">
            {/* Dimensions Section */}
            <div className="bg-gray-50 rounded-lg p-4">
              <h4 className="text-xs font-semibold text-gray-700 uppercase tracking-wide mb-3">
                📐 Dimensions
              </h4>

              {/* Width */}
              <div className="mb-4">
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm font-medium text-gray-700">Width</label>
                  <span className="text-sm font-semibold text-blue-600">{element.width}px</span>
                </div>
                <input
                  type="range"
                  min="50"
                  max="1000"
                  value={element.width}
                  onChange={(e) => onUpdate({ width: parseInt(e.target.value) })}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                />
              </div>

              {/* Height */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm font-medium text-gray-700">Height</label>
                  <span className="text-sm font-semibold text-blue-600">{element.height}px</span>
                </div>
                <input
                  type="range"
                  min="50"
                  max="1000"
                  value={element.height}
                  onChange={(e) => onUpdate({ height: parseInt(e.target.value) })}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                />
              </div>
            </div>
          </div>
        );

      case 'shape':
        return (
          <div className="space-y-6">
            {/* Colors Section */}
            <div className="bg-gray-50 rounded-lg p-4">
              <h4 className="text-xs font-semibold text-gray-700 uppercase tracking-wide mb-3">
                🎨 Colors
              </h4>

              {/* Fill Color */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">Fill Color</label>
                <div className="flex items-center gap-3">
                  <input
                    type="color"
                    value={element.fill}
                    onChange={(e) => onUpdate({ fill: e.target.value })}
                    className="w-16 h-16 rounded-lg cursor-pointer border-2 border-gray-300"
                  />
                  <div className="text-xs text-gray-500 font-mono">{element.fill}</div>
                </div>
              </div>

              {/* Stroke Color */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Stroke Color</label>
                <div className="flex items-center gap-3">
                  <input
                    type="color"
                    value={element.stroke}
                    onChange={(e) => onUpdate({ stroke: e.target.value })}
                    className="w-16 h-16 rounded-lg cursor-pointer border-2 border-gray-300"
                  />
                  <div className="text-xs text-gray-500 font-mono">{element.stroke}</div>
                </div>
              </div>
            </div>

            {/* Stroke Width */}
            <div className="bg-gray-50 rounded-lg p-4">
              <h4 className="text-xs font-semibold text-gray-700 uppercase tracking-wide mb-3">
                ✏️ Stroke
              </h4>
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-medium text-gray-700">Stroke Width</label>
                <span className="text-sm font-semibold text-blue-600">{element.strokeWidth}px</span>
              </div>
              <input
                type="range"
                min="0"
                max="20"
                value={element.strokeWidth}
                onChange={(e) => onUpdate({ strokeWidth: parseInt(e.target.value) })}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
              />
            </div>
          </div>
        );

      default:
        return (
          <div className="text-center py-8">
            <div className="text-4xl mb-2">🔧</div>
            <div className="text-sm text-gray-500">No properties available for this element</div>
          </div>
        );
    }
  };

  return (
    <div className="w-80 bg-white border-l border-gray-200 overflow-y-auto flex flex-col">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 px-6 py-4 flex-shrink-0">
        <h2 className="text-lg font-bold text-white">Properties</h2>
        <p className="text-sm text-blue-100 mt-1 capitalize">{element.type} Element</p>
      </div>

      {/* Properties Content */}
      <div className="flex-1 p-6 overflow-y-auto">
        {renderProperties()}
      </div>

      {/* Footer Actions */}
      <div className="border-t border-gray-200 p-4 flex-shrink-0 bg-gray-50">
        <button
          onClick={onDelete}
          className="w-full px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium text-sm flex items-center justify-center gap-2 shadow-sm"
        >
          <span>🗑️</span>
          Delete Element
        </button>
      </div>
    </div>
  );
};

export default PropertiesPanel;

