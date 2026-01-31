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
    position: true,
    transform: true,
    effects: true,
    border: true,
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
      case 'audio':
        return (
          <div className="space-y-1">
            {/* Audio Info Section */}
            <div className="bg-white border-b border-gray-100">
              <SectionHeader
                title="Audio Info"
                icon="🎵"
                section="content"
                isExpanded={expandedSections.content}
              />
              {expandedSections.content && (
                <div className="p-4 space-y-3">
                  <div>
                    <label className="text-xs font-medium text-gray-600 uppercase tracking-wide block mb-2">Track Name</label>
                    <input
                      type="text"
                      value={element.name || ''}
                      onChange={(e) => onUpdate({ name: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-200 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                      placeholder="Audio track name"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-medium text-gray-600 uppercase tracking-wide block mb-2">Type</label>
                    <select
                      value={element.audioType || 'music'}
                      onChange={(e) => onUpdate({ audioType: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-200 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                    >
                      <option value="music">🎵 Music</option>
                      <option value="voiceover">🎤 Voiceover</option>
                      <option value="sfx">🔊 Sound Effect</option>
                    </select>
                  </div>
                  <div className="text-xs text-gray-500 space-y-1">
                    <div>Duration: {element.duration?.toFixed(2)}s</div>
                    <div>Start Time: {element.startTime?.toFixed(2)}s</div>
                  </div>
                </div>
              )}
            </div>

            {/* Volume Section */}
            <div className="bg-white border-b border-gray-100">
              <SectionHeader
                title="Volume"
                icon="🔊"
                section="color"
                isExpanded={expandedSections.color}
              />
              {expandedSections.color && (
                <div className="p-4 space-y-4">
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <label className="text-xs font-medium text-gray-600 uppercase tracking-wide">Volume</label>
                      <span className="text-xs font-semibold text-gray-700">{element.volume || 100}%</span>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={element.volume || 100}
                      onChange={(e) => onUpdate({ volume: parseInt(e.target.value) })}
                      className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                    />
                  </div>
                </div>
              )}
            </div>

            {/* Fade Effects Section */}
            <div className="bg-white border-b border-gray-100">
              <SectionHeader
                title="Fade Effects"
                icon="🌊"
                section="effects"
                isExpanded={expandedSections.effects}
              />
              {expandedSections.effects && (
                <div className="p-4 space-y-4">
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <label className="text-xs font-medium text-gray-600 uppercase tracking-wide">Fade In</label>
                      <span className="text-xs font-semibold text-gray-700">{element.fadeIn || 0}s</span>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="5"
                      step="0.1"
                      value={element.fadeIn || 0}
                      onChange={(e) => onUpdate({ fadeIn: parseFloat(e.target.value) })}
                      className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                    />
                  </div>
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <label className="text-xs font-medium text-gray-600 uppercase tracking-wide">Fade Out</label>
                      <span className="text-xs font-semibold text-gray-700">{element.fadeOut || 0}s</span>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="5"
                      step="0.1"
                      value={element.fadeOut || 0}
                      onChange={(e) => onUpdate({ fadeOut: parseFloat(e.target.value) })}
                      className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                    />
                  </div>
                </div>
              )}
            </div>

            {/* Delete Section */}
            <div className="bg-white border-b border-gray-100">
              <div className="p-4">
                <button
                  onClick={onDelete}
                  className="w-full px-4 py-2.5 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors font-medium text-sm flex items-center justify-center gap-2"
                >
                  <span>🗑️</span>
                  Delete Audio Track
                </button>
              </div>
            </div>
          </div>
        );

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
                    <select
                      value={element.fontWeight || 'normal'}
                      onChange={(e) => onUpdate({ fontWeight: e.target.value })}
                      className="w-full px-3 py-2 bg-white border border-gray-200 rounded-md text-sm text-gray-700 focus:ring-2 focus:ring-blue-500 focus:border-transparent cursor-pointer"
                    >
                      <option value="normal">Normal</option>
                      <option value="600">Semi Bold</option>
                      <option value="bold">Bold</option>
                    </select>
                  </div>

                  {/* Text Alignment */}
                  <div>
                    <label className="block text-xs font-medium text-gray-600 uppercase tracking-wide mb-2">Align</label>
                    <select
                      value={element.textAlign || 'left'}
                      onChange={(e) => onUpdate({ textAlign: e.target.value })}
                      className="w-full px-3 py-2 bg-white border border-gray-200 rounded-md text-sm text-gray-700 focus:ring-2 focus:ring-blue-500 focus:border-transparent cursor-pointer"
                    >
                      <option value="left">⬅️ Left</option>
                      <option value="center">↔️ Center</option>
                      <option value="right">➡️ Right</option>
                    </select>
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
            {/* Position Section */}
            <div className="bg-white border-b border-gray-100">
              <SectionHeader
                title="Position"
                icon="📍"
                section="position"
                isExpanded={expandedSections.position}
              />
              {expandedSections.position && (
                <div className="p-4 space-y-4">
                  {/* X Position */}
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <label className="text-xs font-medium text-gray-600 uppercase tracking-wide">X Position</label>
                      <span className="text-xs font-bold text-blue-600 bg-blue-50 px-2 py-1 rounded">{Math.round(element.x || 0)}px</span>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="1920"
                      value={element.x || 0}
                      onChange={(e) => onUpdate({ x: parseInt(e.target.value) })}
                      className="w-full h-1.5 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                    />
                  </div>

                  {/* Y Position */}
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <label className="text-xs font-medium text-gray-600 uppercase tracking-wide">Y Position</label>
                      <span className="text-xs font-bold text-blue-600 bg-blue-50 px-2 py-1 rounded">{Math.round(element.y || 0)}px</span>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="1080"
                      value={element.y || 0}
                      onChange={(e) => onUpdate({ y: parseInt(e.target.value) })}
                      className="w-full h-1.5 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                    />
                  </div>
                </div>
              )}
            </div>

            {/* Dimensions Section */}
            <div className="bg-white border-b border-gray-100">
              <SectionHeader
                title="Size"
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

            {/* Transform Section */}
            <div className="bg-white border-b border-gray-100">
              <SectionHeader
                title="Transform"
                icon="🔄"
                section="transform"
                isExpanded={expandedSections.transform}
              />
              {expandedSections.transform && (
                <div className="p-4 space-y-4">
                  {/* Rotation */}
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <label className="text-xs font-medium text-gray-600 uppercase tracking-wide">Rotation</label>
                      <span className="text-xs font-bold text-blue-600 bg-blue-50 px-2 py-1 rounded">{element.rotation || 0}°</span>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="360"
                      value={element.rotation || 0}
                      onChange={(e) => onUpdate({ rotation: parseInt(e.target.value) })}
                      className="w-full h-1.5 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                    />
                  </div>

                  {/* Opacity */}
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <label className="text-xs font-medium text-gray-600 uppercase tracking-wide">Opacity</label>
                      <span className="text-xs font-bold text-blue-600 bg-blue-50 px-2 py-1 rounded">{Math.round((element.opacity || 1) * 100)}%</span>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={(element.opacity || 1) * 100}
                      onChange={(e) => onUpdate({ opacity: parseInt(e.target.value) / 100 })}
                      className="w-full h-1.5 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                    />
                  </div>

                  {/* Flip Controls */}
                  <div>
                    <label className="block text-xs font-medium text-gray-600 uppercase tracking-wide mb-2">Flip</label>
                    <div className="grid grid-cols-2 gap-2">
                      <button
                        onClick={() => onUpdate({ flipX: !(element.flipX || false) })}
                        className={`px-3 py-2 rounded text-xs transition-all ${
                          element.flipX
                            ? 'bg-blue-600 text-white shadow-sm'
                            : 'bg-gray-50 border border-gray-200 text-gray-700 hover:border-blue-400'
                        }`}
                      >
                        ↔️ Horizontal
                      </button>
                      <button
                        onClick={() => onUpdate({ flipY: !(element.flipY || false) })}
                        className={`px-3 py-2 rounded text-xs transition-all ${
                          element.flipY
                            ? 'bg-blue-600 text-white shadow-sm'
                            : 'bg-gray-50 border border-gray-200 text-gray-700 hover:border-blue-400'
                        }`}
                      >
                        ↕️ Vertical
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Border Section */}
            <div className="bg-white border-b border-gray-100">
              <SectionHeader
                title="Border"
                icon="⬜"
                section="border"
                isExpanded={expandedSections.border}
              />
              {expandedSections.border && (
                <div className="p-4 space-y-4">
                  {/* Border Width */}
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <label className="text-xs font-medium text-gray-600 uppercase tracking-wide">Border Width</label>
                      <span className="text-xs font-bold text-blue-600 bg-blue-50 px-2 py-1 rounded">{element.borderWidth || 0}px</span>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="20"
                      value={element.borderWidth || 0}
                      onChange={(e) => onUpdate({ borderWidth: parseInt(e.target.value) })}
                      className="w-full h-1.5 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                    />
                  </div>

                  {/* Border Color */}
                  {(element.borderWidth || 0) > 0 && (
                    <div>
                      <label className="block text-xs font-medium text-gray-600 uppercase tracking-wide mb-2">Border Color</label>
                      <div className="flex items-center gap-3">
                        <input
                          type="color"
                          value={element.borderColor || '#000000'}
                          onChange={(e) => onUpdate({ borderColor: e.target.value })}
                          className="w-12 h-12 rounded-md cursor-pointer border border-gray-200"
                        />
                        <div className="flex-1">
                          <div className="text-xs text-gray-500 font-mono bg-gray-50 px-2 py-1 rounded">{element.borderColor || '#000000'}</div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Corner Radius */}
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <label className="text-xs font-medium text-gray-600 uppercase tracking-wide">Corner Radius</label>
                      <span className="text-xs font-bold text-blue-600 bg-blue-50 px-2 py-1 rounded">{element.borderRadius || 0}px</span>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={element.borderRadius || 0}
                      onChange={(e) => onUpdate({ borderRadius: parseInt(e.target.value) })}
                      className="w-full h-1.5 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                    />
                  </div>
                </div>
              )}
            </div>

            {/* Effects Section */}
            <div className="bg-white border-b border-gray-100">
              <SectionHeader
                title="Effects"
                icon="✨"
                section="effects"
                isExpanded={expandedSections.effects}
              />
              {expandedSections.effects && (
                <div className="p-4 space-y-4">
                  {/* Brightness */}
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <label className="text-xs font-medium text-gray-600 uppercase tracking-wide">Brightness</label>
                      <span className="text-xs font-bold text-blue-600 bg-blue-50 px-2 py-1 rounded">{element.brightness || 100}%</span>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="200"
                      value={element.brightness || 100}
                      onChange={(e) => onUpdate({ brightness: parseInt(e.target.value) })}
                      className="w-full h-1.5 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                    />
                  </div>

                  {/* Contrast */}
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <label className="text-xs font-medium text-gray-600 uppercase tracking-wide">Contrast</label>
                      <span className="text-xs font-bold text-blue-600 bg-blue-50 px-2 py-1 rounded">{element.contrast || 100}%</span>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="200"
                      value={element.contrast || 100}
                      onChange={(e) => onUpdate({ contrast: parseInt(e.target.value) })}
                      className="w-full h-1.5 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                    />
                  </div>

                  {/* Saturation */}
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <label className="text-xs font-medium text-gray-600 uppercase tracking-wide">Saturation</label>
                      <span className="text-xs font-bold text-blue-600 bg-blue-50 px-2 py-1 rounded">{element.saturation || 100}%</span>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="200"
                      value={element.saturation || 100}
                      onChange={(e) => onUpdate({ saturation: parseInt(e.target.value) })}
                      className="w-full h-1.5 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                    />
                  </div>

                  {/* Blur */}
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <label className="text-xs font-medium text-gray-600 uppercase tracking-wide">Blur</label>
                      <span className="text-xs font-bold text-blue-600 bg-blue-50 px-2 py-1 rounded">{element.blur || 0}px</span>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="20"
                      value={element.blur || 0}
                      onChange={(e) => onUpdate({ blur: parseInt(e.target.value) })}
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
    </div>
  );
};

export default PropertiesPanel;

