import React, { useRef, useEffect, useState } from 'react';
import CanvasElement from './CanvasElement';

/**
 * Canvas Component - Main design area
 * Features: Drag & drop, resize, rotate elements
 */
const Canvas = ({ elements, selectedElement, onSelectElement, onUpdateElement, onDeleteElement, background }) => {
  const canvasRef = useRef(null);
  const [canvasSize, setCanvasSize] = useState({ width: 1920, height: 1080 });
  const [zoom, setZoom] = useState(0.5);

  // Generate background style
  const getBackgroundStyle = () => {
    if (!background) return { backgroundColor: '#ffffff' };

    if (background.type === 'gradient') {
      const angle = background.angle || 135;
      const colors = background.colors || ['#667eea', '#764ba2'];
      return {
        background: `linear-gradient(${angle}deg, ${colors.join(', ')})`
      };
    } else if (background.type === 'solid') {
      return { backgroundColor: background.color || '#ffffff' };
    }

    return { backgroundColor: '#ffffff' };
  };

  // Canvas presets
  const presets = [
    { name: 'Instagram Post', width: 1080, height: 1080 },
    { name: 'Instagram Story', width: 1080, height: 1920 },
    { name: 'YouTube Thumbnail', width: 1280, height: 720 },
    { name: 'Facebook Post', width: 1200, height: 630 },
    { name: 'Twitter Post', width: 1200, height: 675 },
    { name: 'Custom', width: 1920, height: 1080 },
  ];

  const handleCanvasClick = (e) => {
    // Deselect if clicking on canvas background
    if (e.target === canvasRef.current) {
      onSelectElement(null);
    }
  };

  const handleKeyDown = (e) => {
    // Delete selected element on Delete/Backspace
    if ((e.key === 'Delete' || e.key === 'Backspace') && selectedElement) {
      onDeleteElement(selectedElement.id);
    }
  };

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedElement]);

  return (
    <div className="flex-1 flex flex-col bg-gray-100">
      {/* Canvas Toolbar */}
      <div className="bg-white border-b border-gray-200 px-4 py-2 flex items-center justify-between">
        <div className="flex items-center gap-4">
          {/* Canvas Size Selector */}
          <select
            value={`${canvasSize.width}x${canvasSize.height}`}
            onChange={(e) => {
              const [width, height] = e.target.value.split('x').map(Number);
              setCanvasSize({ width, height });
            }}
            className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            {presets.map((preset) => (
              <option key={preset.name} value={`${preset.width}x${preset.height}`}>
                {preset.name} ({preset.width}×{preset.height})
              </option>
            ))}
          </select>

          {/* Zoom Controls */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setZoom(Math.max(0.1, zoom - 0.1))}
              className="px-2 py-1 border border-gray-300 rounded hover:bg-gray-50"
            >
              −
            </button>
            <span className="text-sm font-medium text-gray-700 min-w-[60px] text-center">
              {Math.round(zoom * 100)}%
            </span>
            <button
              onClick={() => setZoom(Math.min(2, zoom + 0.1))}
              className="px-2 py-1 border border-gray-300 rounded hover:bg-gray-50"
            >
              +
            </button>
          </div>
        </div>

        {/* Canvas Actions */}
        <div className="flex items-center gap-2">
          <button className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-50">
            Undo
          </button>
          <button className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-50">
            Redo
          </button>
        </div>
      </div>

      {/* Canvas Area */}
      <div className="flex-1 overflow-auto p-8 flex items-center justify-center">
        <div
          ref={canvasRef}
          onClick={handleCanvasClick}
          className="shadow-2xl relative"
          style={{
            width: canvasSize.width * zoom,
            height: canvasSize.height * zoom,
            transform: `scale(1)`,
            transformOrigin: 'center',
            ...getBackgroundStyle()
          }}
        >
          {/* Render Elements */}
          {elements.map((element) => (
            <CanvasElement
              key={element.id}
              element={element}
              isSelected={selectedElement?.id === element.id}
              zoom={zoom}
              onSelect={() => onSelectElement(element)}
              onUpdate={(updates) => onUpdateElement(element.id, updates)}
            />
          ))}

          {/* Empty State */}
          {elements.length === 0 && (
            <div className="absolute inset-0 flex items-center justify-center text-gray-400">
              <div className="text-center">
                <div className="text-6xl mb-4">🎨</div>
                <div className="text-lg font-medium">Start creating</div>
                <div className="text-sm mt-2">Add elements from the sidebar</div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Canvas;

