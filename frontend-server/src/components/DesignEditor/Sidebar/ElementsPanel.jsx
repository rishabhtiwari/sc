import React from 'react';
import { useToast } from '../../../hooks/useToast';

/**
 * Elements Panel
 * Features: Shapes, Icons, Stickers, Lines
 */
const ElementsPanel = ({ onAddElement }) => {
  const { showToast } = useToast();

  const shapes = [
    { id: 'rectangle', name: 'Rectangle', icon: '▭', type: 'rect' },
    { id: 'circle', name: 'Circle', icon: '●', type: 'circle' },
    { id: 'triangle', name: 'Triangle', icon: '▲', type: 'triangle' },
    { id: 'star', name: 'Star', icon: '★', type: 'star' },
    { id: 'line', name: 'Line', icon: '─', type: 'line' },
    { id: 'arrow', name: 'Arrow', icon: '→', type: 'arrow' },
  ];

  const icons = [
    { id: 'heart', icon: '❤️', name: 'Heart' },
    { id: 'star', icon: '⭐', name: 'Star' },
    { id: 'fire', icon: '🔥', name: 'Fire' },
    { id: 'check', icon: '✓', name: 'Check' },
    { id: 'cross', icon: '✗', name: 'Cross' },
    { id: 'info', icon: 'ℹ️', name: 'Info' },
  ];

  const handleAddShape = (shape) => {
    onAddElement({
      type: 'shape',
      shapeType: shape.type,
      width: 150,
      height: 150,
      fill: '#3B82F6',
      stroke: '#1E40AF',
      strokeWidth: 2
    });
    showToast(`${shape.name} added to canvas`, 'success');
  };

  const handleAddIcon = (icon) => {
    onAddElement({
      type: 'icon',
      icon: icon.icon,
      fontSize: 48,
      color: '#000000'
    });
    showToast(`${icon.name} added to canvas`, 'success');
  };

  return (
    <div className="space-y-6">
      {/* Shapes */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-gray-900">Shapes</h3>
        <div className="grid grid-cols-3 gap-2">
          {shapes.map((shape) => (
            <button
              key={shape.id}
              onClick={() => handleAddShape(shape)}
              className="p-4 border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all text-center"
            >
              <div className="text-3xl mb-1">{shape.icon}</div>
              <div className="text-xs font-medium text-gray-700">{shape.name}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Icons */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-gray-900">Icons</h3>
        <div className="grid grid-cols-3 gap-2">
          {icons.map((icon) => (
            <button
              key={icon.id}
              onClick={() => handleAddIcon(icon)}
              className="p-4 border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all text-center"
            >
              <div className="text-3xl mb-1">{icon.icon}</div>
              <div className="text-xs font-medium text-gray-700">{icon.name}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Stickers */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-gray-900">Stickers</h3>
        <div className="grid grid-cols-4 gap-2">
          {['😀', '😍', '🎉', '🎨', '🚀', '💡', '🌟', '🔥'].map((emoji, index) => (
            <button
              key={index}
              onClick={() => {
                onAddElement({
                  type: 'sticker',
                  emoji,
                  fontSize: 64
                });
                showToast('Sticker added to canvas', 'success');
              }}
              className="p-3 border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all text-center text-2xl"
            >
              {emoji}
            </button>
          ))}
        </div>
      </div>

      {/* Frames & Borders */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-gray-900">Frames</h3>
        <div className="grid grid-cols-2 gap-2">
          <button className="p-4 border-2 border-gray-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all text-center">
            <div className="text-xs font-medium">Simple</div>
          </button>
          <button className="p-4 border-4 border-double border-gray-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all text-center">
            <div className="text-xs font-medium">Double</div>
          </button>
          <button className="p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all text-center">
            <div className="text-xs font-medium">Dashed</div>
          </button>
          <button className="p-4 border-2 border-dotted border-gray-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all text-center">
            <div className="text-xs font-medium">Dotted</div>
          </button>
        </div>
      </div>
    </div>
  );
};

export default ElementsPanel;

