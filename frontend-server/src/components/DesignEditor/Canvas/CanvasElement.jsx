import React, { useState, useRef } from 'react';

/**
 * Canvas Element Component
 * Renders different types of elements (text, image, shape, etc.)
 */
const CanvasElement = ({ element, isSelected, zoom, onSelect, onUpdate }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const elementRef = useRef(null);

  const handleMouseDown = (e) => {
    e.stopPropagation();
    onSelect();
    setIsDragging(true);
    setDragStart({
      x: e.clientX - (element.x || 0) * zoom,
      y: e.clientY - (element.y || 0) * zoom
    });
  };

  const handleMouseMove = (e) => {
    if (isDragging) {
      const newX = (e.clientX - dragStart.x) / zoom;
      const newY = (e.clientY - dragStart.y) / zoom;
      onUpdate({ x: newX, y: newY });
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  React.useEffect(() => {
    if (isDragging) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
      return () => {
        window.removeEventListener('mousemove', handleMouseMove);
        window.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isDragging, dragStart]);

  const renderElement = () => {
    switch (element.type) {
      case 'text':
        return (
          <div
            style={{
              fontSize: element.fontSize,
              fontWeight: element.fontWeight,
              color: element.color,
              fontFamily: element.fontFamily,
              whiteSpace: 'pre-wrap',
              cursor: 'move'
            }}
          >
            {element.text}
          </div>
        );

      case 'image':
        return (
          <img
            src={element.src}
            alt="Canvas element"
            style={{
              width: element.width,
              height: element.height,
              objectFit: 'cover',
              cursor: 'move'
            }}
            draggable={false}
          />
        );

      case 'shape':
        return (
          <div
            style={{
              width: element.width,
              height: element.height,
              backgroundColor: element.fill,
              border: `${element.strokeWidth}px solid ${element.stroke}`,
              borderRadius: element.shapeType === 'circle' ? '50%' : '0',
              cursor: 'move'
            }}
          />
        );

      case 'icon':
      case 'sticker':
        return (
          <div
            style={{
              fontSize: element.fontSize,
              color: element.color,
              cursor: 'move'
            }}
          >
            {element.icon || element.emoji}
          </div>
        );

      default:
        return <div>Unknown element type</div>;
    }
  };

  return (
    <div
      ref={elementRef}
      onMouseDown={handleMouseDown}
      className={`absolute ${isSelected ? 'ring-2 ring-blue-500' : ''}`}
      style={{
        left: (element.x || 0) * zoom,
        top: (element.y || 0) * zoom,
        transform: `scale(${zoom})`,
        transformOrigin: 'top left',
        cursor: isDragging ? 'grabbing' : 'grab'
      }}
    >
      {renderElement()}

      {/* Selection Handles */}
      {isSelected && (
        <>
          {/* Resize handles */}
          <div className="absolute -top-1 -left-1 w-3 h-3 bg-blue-500 rounded-full cursor-nwse-resize" />
          <div className="absolute -top-1 -right-1 w-3 h-3 bg-blue-500 rounded-full cursor-nesw-resize" />
          <div className="absolute -bottom-1 -left-1 w-3 h-3 bg-blue-500 rounded-full cursor-nesw-resize" />
          <div className="absolute -bottom-1 -right-1 w-3 h-3 bg-blue-500 rounded-full cursor-nwse-resize" />
        </>
      )}
    </div>
  );
};

export default CanvasElement;

