import React, { useState } from 'react';

/**
 * Properties Panel - Edit selected element properties
 * Veed.io-inspired professional design with collapsible sections
 */
const PropertiesPanel = ({ element, onUpdate, onDelete }) => {
  const [expandedSections, setExpandedSections] = useState({
    content: true,
    typography: true,
    color: true,
    dimensions: true,
    stroke: true
  });

  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  if (!element) {
    return (
      <div className="w-80 bg-gray-50 border-l border-gray-200 flex items-center justify-center p-8">
        <div className="text-center">
          <div className="text-5xl mb-3 opacity-40">✨</div>
          <h3 className="text-sm font-semibold text-gray-700 mb-1">No element selected</h3>
          <p className="text-xs text-gray-500">Select an element to edit</p>
        </div>
      </div>
    );
  }

  // Collapsible Section Header Component
  const SectionHeader = ({ title, icon, section, isExpanded }) => (
    <button
      onClick={() => toggleSection(section)}
      className="w-full flex items-center justify-between px-4 py-3 hover:bg-gray-50 transition-colors border-b border-gray-100"
    >
      <div className="flex items-center gap-2">
        <span className="text-base">{icon}</span>
        <span className="text-sm font-semibold text-gray-800">{title}</span>
      </div>
      <svg
        className={`w-4 h-4 text-gray-500 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
      </svg>
    </button>
  );

  const renderProperties = () => {
    switch (element.type) {
      case 'text':
        return (
          <div className="space-y-1">
            {/* Text Content Section */}
            <div className="bg-white border-b border-gray-100">
              <SectionHeader
                title="Content"
                icon="✏️"
                section="content"
                isExpanded={expandedSections.content}
              />
              {expandedSections.content && (
                <div className="p-4 space-y-3">
                  <textarea
                    value={element.text}
                    onChange={(e) => onUpdate({ text: e.target.value })}
                    className="w-full px-3 py-2.5 border border-gray-200 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none text-sm"
                    rows={3}
                    placeholder="Enter text..."
                  />
                  <p className="text-xs text-gray-500">💡 Double-click on canvas to edit</p>
                </div>
              )}
            </div>

            {/* Typography Section */}
            <div className="bg-white border-b border-gray-100">
              <SectionHeader
                title="Typography"
                icon="🔤"
                section="typography"
                isExpanded={expandedSections.typography}
              />
              {expandedSections.typography && (
                <div className="p-4 space-y-4">
                  {/* Font Size */}
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <label className="text-xs font-medium text-gray-600 uppercase tracking-wide">Font Size</label>
                      <span className="text-xs font-bold text-blue-600 bg-blue-50 px-2 py-1 rounded">{element.fontSize}px</span>
                    </div>
                    <input
                      type="range"
                      min="8"
                      max="120"
                      value={element.fontSize}
                      onChange={(e) => onUpdate({ fontSize: parseInt(e.target.value) })}
                      className="w-full h-1.5 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                    />
                  </div>

                  {/* Font Weight */}
                  <div>
                    <label className="block text-xs font-medium text-gray-600 uppercase tracking-wide mb-2">Weight</label>
                    <div className="grid grid-cols-3 gap-1.5">
                      {[
                        { value: 'normal', label: 'Normal', weight: 'font-normal' },
                        { value: '600', label: 'Semi', weight: 'font-semibold' },
                        { value: 'bold', label: 'Bold', weight: 'font-bold' }
                      ].map(({ value, label, weight }) => (
                        <button
                          key={value}
                          onClick={() => onUpdate({ fontWeight: value })}
                          className={`px-2 py-2 rounded text-xs ${weight} transition-all ${
                            element.fontWeight === value
                              ? 'bg-blue-600 text-white shadow-sm'
                              : 'bg-gray-50 border border-gray-200 text-gray-700 hover:border-blue-400'
                          }`}
                        >
                          {label}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Text Alignment */}
                  <div>
                    <label className="block text-xs font-medium text-gray-600 uppercase tracking-wide mb-2">Align</label>
                    <div className="grid grid-cols-3 gap-1.5">
                      {[
                        { value: 'left', icon: '⬅️', label: 'Left' },
                        { value: 'center', icon: '↔️', label: 'Center' },
                        { value: 'right', icon: '➡️', label: 'Right' }
                      ].map(({ value, icon, label }) => (
                        <button
                          key={value}
                          onClick={() => onUpdate({ textAlign: value })}
                          className={`px-2 py-2 rounded text-xs transition-all ${
                            (element.textAlign || 'left') === value
                              ? 'bg-blue-600 text-white shadow-sm'
                              : 'bg-gray-50 border border-gray-200 text-gray-700 hover:border-blue-400'
                          }`}
                        >
                          <span className="mr-1">{icon}</span>
                          {label}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Color Section */}
            <div className="bg-white border-b border-gray-100">
              <SectionHeader
                title="Color"
                icon="🎨"
                section="color"
                isExpanded={expandedSections.color}
              />
              {expandedSections.color && (
                <div className="p-4">
                  <div className="flex items-center gap-3">
                    <input
                      type="color"
                      value={element.color}
                      onChange={(e) => onUpdate({ color: e.target.value })}
                      className="w-12 h-12 rounded-md cursor-pointer border border-gray-200"
                    />
                    <div className="flex-1">
                      <div className="text-xs font-medium text-gray-600 mb-1">Text Color</div>
                      <div className="text-xs text-gray-500 font-mono bg-gray-50 px-2 py-1 rounded">{element.color}</div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        );

      case 'image':
        return (
          <div className="space-y-1">
            {/* Dimensions Section */}
            <div className="bg-white border-b border-gray-100">
              <SectionHeader
                title="Dimensions"
                icon="📐"
                section="dimensions"
                isExpanded={expandedSections.dimensions}
              />
              {expandedSections.dimensions && (
                <div className="p-4 space-y-4">
                  {/* Width */}
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <label className="text-xs font-medium text-gray-600 uppercase tracking-wide">Width</label>
                      <span className="text-xs font-bold text-blue-600 bg-blue-50 px-2 py-1 rounded">{element.width}px</span>
                    </div>
                    <input
                      type="range"
                      min="50"
                      max="1000"
                      value={element.width}
                      onChange={(e) => onUpdate({ width: parseInt(e.target.value) })}
                      className="w-full h-1.5 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                    />
                  </div>

                  {/* Height */}
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <label className="text-xs font-medium text-gray-600 uppercase tracking-wide">Height</label>
                      <span className="text-xs font-bold text-blue-600 bg-blue-50 px-2 py-1 rounded">{element.height}px</span>
                    </div>
                    <input
                      type="range"
                      min="50"
                      max="1000"
                      value={element.height}
                      onChange={(e) => onUpdate({ height: parseInt(e.target.value) })}
                      className="w-full h-1.5 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                    />
                  </div>
                </div>
              )}
            </div>
          </div>
        );

      case 'shape':
        return (
          <div className="space-y-1">
            {/* Colors Section */}
            <div className="bg-white border-b border-gray-100">
              <SectionHeader
                title="Colors"
                icon="🎨"
                section="color"
                isExpanded={expandedSections.color}
              />
              {expandedSections.color && (
                <div className="p-4 space-y-4">
                  {/* Fill Color */}
                  <div>
                    <label className="block text-xs font-medium text-gray-600 uppercase tracking-wide mb-2">Fill Color</label>
                    <div className="flex items-center gap-3">
                      <input
                        type="color"
                        value={element.fill}
                        onChange={(e) => onUpdate({ fill: e.target.value })}
                        className="w-12 h-12 rounded-md cursor-pointer border border-gray-200"
                      />
                      <div className="flex-1">
                        <div className="text-xs text-gray-500 font-mono bg-gray-50 px-2 py-1 rounded">{element.fill}</div>
                      </div>
                    </div>
                  </div>

                  {/* Stroke Color */}
                  <div>
                    <label className="block text-xs font-medium text-gray-600 uppercase tracking-wide mb-2">Stroke Color</label>
                    <div className="flex items-center gap-3">
                      <input
                        type="color"
                        value={element.stroke}
                        onChange={(e) => onUpdate({ stroke: e.target.value })}
                        className="w-12 h-12 rounded-md cursor-pointer border border-gray-200"
                      />
                      <div className="flex-1">
                        <div className="text-xs text-gray-500 font-mono bg-gray-50 px-2 py-1 rounded">{element.stroke}</div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Stroke Width */}
            <div className="bg-white border-b border-gray-100">
              <SectionHeader
                title="Stroke"
                icon="✏️"
                section="stroke"
                isExpanded={expandedSections.stroke}
              />
              {expandedSections.stroke && (
                <div className="p-4">
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-xs font-medium text-gray-600 uppercase tracking-wide">Stroke Width</label>
                    <span className="text-xs font-bold text-blue-600 bg-blue-50 px-2 py-1 rounded">{element.strokeWidth}px</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="20"
                    value={element.strokeWidth}
                    onChange={(e) => onUpdate({ strokeWidth: parseInt(e.target.value) })}
                    className="w-full h-1.5 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                  />
                </div>
              )}
            </div>
          </div>
        );

      default:
        return (
          <div className="text-center py-12 px-4">
            <div className="text-4xl mb-3 opacity-40">🔧</div>
            <div className="text-sm text-gray-500">No properties available</div>
          </div>
        );
    }
  };

  return (
    <div className="w-80 bg-gray-50 border-l border-gray-200 flex flex-col h-full">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-4 py-3 flex-shrink-0">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm font-bold text-gray-900">Properties</h2>
            <p className="text-xs text-gray-500 mt-0.5 capitalize">{element.type} Element</p>
          </div>
          <div className="w-8 h-8 bg-blue-50 rounded-md flex items-center justify-center">
            <span className="text-lg">
              {element.type === 'text' ? '📝' : element.type === 'image' ? '🖼️' : '⬜'}
            </span>
          </div>
        </div>
      </div>

      {/* Properties Content - Scrollable */}
      <div className="flex-1 overflow-y-auto">
        {renderProperties()}
      </div>

      {/* Footer Actions */}
      <div className="border-t border-gray-200 p-3 flex-shrink-0 bg-white">
        <button
          onClick={onDelete}
          className="w-full px-4 py-2.5 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors font-medium text-sm flex items-center justify-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
          Delete Element
        </button>
      </div>
    </div>
  );
};

export default PropertiesPanel;

