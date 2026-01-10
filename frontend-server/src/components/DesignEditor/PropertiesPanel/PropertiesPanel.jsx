import React from 'react';

/**
 * Properties Panel - Edit selected element properties
 */
const PropertiesPanel = ({ element, onUpdate, onDelete }) => {
  if (!element) return null;

  const renderProperties = () => {
    switch (element.type) {
      case 'text':
        return (
          <div className="space-y-4">
            {/* Text Content */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Text</label>
              <textarea
                value={element.text}
                onChange={(e) => onUpdate({ text: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                rows={3}
              />
            </div>

            {/* Font Size */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Font Size: {element.fontSize}px
              </label>
              <input
                type="range"
                min="8"
                max="120"
                value={element.fontSize}
                onChange={(e) => onUpdate({ fontSize: parseInt(e.target.value) })}
                className="w-full"
              />
            </div>

            {/* Font Weight */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Font Weight</label>
              <select
                value={element.fontWeight}
                onChange={(e) => onUpdate({ fontWeight: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="normal">Normal</option>
                <option value="600">Semi Bold</option>
                <option value="bold">Bold</option>
              </select>
            </div>

            {/* Color */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Color</label>
              <input
                type="color"
                value={element.color}
                onChange={(e) => onUpdate({ color: e.target.value })}
                className="w-full h-10 rounded-lg cursor-pointer"
              />
            </div>
          </div>
        );

      case 'image':
        return (
          <div className="space-y-4">
            {/* Width */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Width: {element.width}px
              </label>
              <input
                type="range"
                min="50"
                max="1000"
                value={element.width}
                onChange={(e) => onUpdate({ width: parseInt(e.target.value) })}
                className="w-full"
              />
            </div>

            {/* Height */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Height: {element.height}px
              </label>
              <input
                type="range"
                min="50"
                max="1000"
                value={element.height}
                onChange={(e) => onUpdate({ height: parseInt(e.target.value) })}
                className="w-full"
              />
            </div>
          </div>
        );

      case 'shape':
        return (
          <div className="space-y-4">
            {/* Fill Color */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Fill Color</label>
              <input
                type="color"
                value={element.fill}
                onChange={(e) => onUpdate({ fill: e.target.value })}
                className="w-full h-10 rounded-lg cursor-pointer"
              />
            </div>

            {/* Stroke Color */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Stroke Color</label>
              <input
                type="color"
                value={element.stroke}
                onChange={(e) => onUpdate({ stroke: e.target.value })}
                className="w-full h-10 rounded-lg cursor-pointer"
              />
            </div>

            {/* Stroke Width */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Stroke Width: {element.strokeWidth}px
              </label>
              <input
                type="range"
                min="0"
                max="20"
                value={element.strokeWidth}
                onChange={(e) => onUpdate({ strokeWidth: parseInt(e.target.value) })}
                className="w-full"
              />
            </div>
          </div>
        );

      default:
        return <div className="text-sm text-gray-500">No properties available</div>;
    }
  };

  return (
    <div className="w-80 bg-white border-l border-gray-200 overflow-y-auto">
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900">Properties</h2>
        <p className="text-sm text-gray-500 mt-1 capitalize">{element.type} Element</p>
      </div>

      <div className="p-4">
        {renderProperties()}

        {/* Delete Button */}
        <button
          onClick={onDelete}
          className="w-full mt-6 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
        >
          Delete Element
        </button>
      </div>
    </div>
  );
};

export default PropertiesPanel;

