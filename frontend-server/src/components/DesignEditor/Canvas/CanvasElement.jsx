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
        const textStyle = {
          fontSize: (element.fontSize || 16) * zoom,
          fontWeight: element.fontWeight,
          color: element.color,
          fontFamily: element.fontFamily,
          textAlign: element.textAlign || 'left',
          width: element.width ? element.width * zoom : 'auto',
          maxWidth: element.width ? element.width * zoom : 'none',
          lineHeight: element.lineHeight || 1.4,
          letterSpacing: element.letterSpacing,
          whiteSpace: 'pre-wrap',
          wordWrap: 'break-word',
          overflowWrap: 'break-word',
          overflow: 'hidden',
          cursor: 'move'
        };

        // Add text effects
        if (element.gradient) {
          textStyle.background = element.gradient;
          textStyle.WebkitBackgroundClip = 'text';
          textStyle.WebkitTextFillColor = 'transparent';
          textStyle.backgroundClip = 'text';
        }

        if (element.textShadow) {
          textStyle.textShadow = element.textShadow;
        }

        if (element.textStroke) {
          textStyle.WebkitTextStroke = element.textStroke;
        }

        return (
          <div style={textStyle}>
            {element.text}
          </div>
        );

      case 'bullets':
        return (
          <div
            style={{
              fontSize: (element.fontSize || 16) * zoom,
              fontWeight: element.fontWeight,
              color: element.color,
              fontFamily: element.fontFamily,
              width: element.width ? element.width * zoom : 'auto',
              maxWidth: element.width ? element.width * zoom : 'none',
              lineHeight: element.lineHeight || 1.5,
              cursor: 'move'
            }}
          >
            {element.bullets && element.bullets.map((bullet, index) => (
              <div
                key={index}
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  marginBottom: (element.spacing || 20) * zoom,
                  wordWrap: 'break-word',
                  overflowWrap: 'break-word'
                }}
              >
                <span style={{ marginRight: 10 * zoom, flexShrink: 0, fontSize: '1.2em' }}>
                  {element.bulletStyle || '•'}
                </span>
                <span style={{ flex: 1 }}>{bullet}</span>
              </div>
            ))}
          </div>
        );

      case 'image':
        return (
          <img
            src={element.src}
            alt="Canvas element"
            style={{
              width: element.width ? element.width * zoom : 'auto',
              height: element.height ? element.height * zoom : 'auto',
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
              width: element.width ? element.width * zoom : 'auto',
              height: element.height ? element.height * zoom : 'auto',
              backgroundColor: element.fill,
              border: `${(element.strokeWidth || 0) * zoom}px solid ${element.stroke || 'transparent'}`,
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
              fontSize: (element.fontSize || 16) * zoom,
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
        // Don't apply transform scale here - positions are already scaled by zoom
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

