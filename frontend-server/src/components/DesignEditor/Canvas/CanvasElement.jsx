import React, { useState, useRef } from 'react';
import AuthenticatedVideo from '../../common/AuthenticatedVideo';

/**
 * Canvas Element Component
 * Renders different types of elements (text, image, shape, etc.)
 */
const CanvasElement = ({ element, isSelected, zoom, onSelect, onUpdate, onEditingChange }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [isResizing, setIsResizing] = useState(false);
  const [resizeHandle, setResizeHandle] = useState(null);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [isEditing, setIsEditing] = useState(false);
  const [editText, setEditText] = useState(element.text || '');
  const elementRef = useRef(null);

  // Notify parent when editing state changes
  React.useEffect(() => {
    if (onEditingChange) {
      onEditingChange(isEditing);
    }
  }, [isEditing, onEditingChange]);

  const handleMouseDown = (e) => {
    e.stopPropagation();
    onSelect();

    // Check if clicking on a resize handle
    if (e.target.dataset.resizeHandle) {
      setIsResizing(true);
      setResizeHandle(e.target.dataset.resizeHandle);
      setDragStart({
        x: e.clientX,
        y: e.clientY,
        width: element.width || 200,
        height: element.height || 100
      });
      return;
    }

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
    } else if (isResizing) {
      const deltaX = (e.clientX - dragStart.x) / zoom;
      const deltaY = (e.clientY - dragStart.y) / zoom;

      let newWidth = dragStart.width;
      let newHeight = dragStart.height;

      if (resizeHandle.includes('e')) {
        newWidth = Math.max(50, dragStart.width + deltaX);
      }
      if (resizeHandle.includes('w')) {
        newWidth = Math.max(50, dragStart.width - deltaX);
      }
      if (resizeHandle.includes('s')) {
        newHeight = Math.max(30, dragStart.height + deltaY);
      }
      if (resizeHandle.includes('n')) {
        newHeight = Math.max(30, dragStart.height - deltaY);
      }

      onUpdate({ width: newWidth, height: newHeight });
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
    setIsResizing(false);
    setResizeHandle(null);
  };

  const handleDoubleClick = (e) => {
    if (element.type === 'text') {
      e.stopPropagation();
      setIsEditing(true);
      setEditText(element.text || '');
    }
  };

  const handleTextChange = (e) => {
    setEditText(e.target.value);
  };

  const handleTextBlur = () => {
    setIsEditing(false);
    if (editText !== element.text) {
      onUpdate({ text: editText });
    }
  };

  const handleTextKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleTextBlur();
    } else if (e.key === 'Escape') {
      setIsEditing(false);
      setEditText(element.text || '');
    }
  };

  React.useEffect(() => {
    if (isDragging || isResizing) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
      return () => {
        window.removeEventListener('mousemove', handleMouseMove);
        window.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isDragging, isResizing, dragStart, resizeHandle]);

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
          minWidth: element.width ? element.width * zoom : '100px',
          maxWidth: element.width ? element.width * zoom : 'none',
          lineHeight: element.lineHeight || 1.4,
          letterSpacing: element.letterSpacing,
          whiteSpace: 'pre-wrap',
          wordWrap: 'break-word',
          overflowWrap: 'break-word',
          overflow: 'visible',
          cursor: isEditing ? 'text' : 'move',
          padding: '4px'
        };

        // Add text effects
        if (element.gradient && !isEditing) {
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

        if (isEditing) {
          return (
            <textarea
              value={editText}
              onChange={handleTextChange}
              onBlur={handleTextBlur}
              onKeyDown={handleTextKeyDown}
              autoFocus
              style={{
                ...textStyle,
                border: '2px solid #3b82f6',
                borderRadius: '4px',
                outline: 'none',
                resize: 'none',
                background: 'white'
              }}
            />
          );
        }

        return (
          <div
            style={textStyle}
            onDoubleClick={handleDoubleClick}
          >
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
        // Build filter string for image effects
        const filters = [];
        if (element.brightness !== undefined && element.brightness !== 100) {
          filters.push(`brightness(${element.brightness}%)`);
        }
        if (element.contrast !== undefined && element.contrast !== 100) {
          filters.push(`contrast(${element.contrast}%)`);
        }
        if (element.saturation !== undefined && element.saturation !== 100) {
          filters.push(`saturate(${element.saturation}%)`);
        }
        if (element.blur !== undefined && element.blur > 0) {
          filters.push(`blur(${element.blur}px)`);
        }

        const imageStyle = {
          width: element.width ? element.width * zoom : 'auto',
          height: element.height ? element.height * zoom : 'auto',
          objectFit: 'cover',
          cursor: 'move',
          opacity: element.opacity !== undefined ? element.opacity : 1,
          transform: `
            rotate(${element.rotation || 0}deg)
            scaleX(${element.flipX ? -1 : 1})
            scaleY(${element.flipY ? -1 : 1})
          `.trim(),
          borderRadius: element.borderRadius ? `${element.borderRadius * zoom}px` : '0',
          border: element.borderWidth ? `${element.borderWidth * zoom}px solid ${element.borderColor || '#000'}` : 'none',
          filter: filters.length > 0 ? filters.join(' ') : 'none'
        };

        return (
          <img
            src={element.src}
            alt="Canvas element"
            style={imageStyle}
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

      case 'video':
        const videoStyle = {
          width: element.width ? element.width * zoom : 'auto',
          height: element.height ? element.height * zoom : 'auto',
          objectFit: 'cover',
          cursor: 'move',
          opacity: element.opacity !== undefined ? element.opacity : 1,
          transform: `
            rotate(${element.rotation || 0}deg)
            scaleX(${element.flipX ? -1 : 1})
            scaleY(${element.flipY ? -1 : 1})
          `.trim(),
          borderRadius: element.borderRadius ? `${element.borderRadius * zoom}px` : '0',
          border: element.borderWidth ? `${element.borderWidth * zoom}px solid ${element.borderColor || '#000'}` : 'none',
          pointerEvents: 'none', // Prevent video from capturing mouse events
        };

        console.log('🎬 Rendering video element:', element.id, 'src:', element.src?.substring(0, 50));

        // Check if this is an API URL that needs authentication
        const isApiUrl = element.src && element.src.startsWith('/api/assets/download/');

        if (isApiUrl) {
          // Use AuthenticatedVideo for API URLs
          return (
            <AuthenticatedVideo
              key={element.id}
              src={element.src}
              style={videoStyle}
              muted={element.muted !== undefined ? element.muted : true}
              loop={element.loop !== undefined ? element.loop : false}
              playsInline
              preload="auto"
              data-video-element-id={element.id}
            />
          );
        } else {
          // Use regular video tag for blob URLs and local files
          return (
            <video
              key={element.id}
              src={element.src}
              style={videoStyle}
              muted={element.muted !== undefined ? element.muted : true}
              loop={element.loop !== undefined ? element.loop : false}
              playsInline
              preload="auto"
              data-video-element-id={element.id}
              onLoadedMetadata={(e) => {
                console.log('🎬 Video onLoadedMetadata:', element.id, 'duration:', e.target.duration, 'readyState:', e.target.readyState, 'src valid:', !!e.target.src);
              }}
              onCanPlay={(e) => {
                console.log('🎬 Video onCanPlay:', element.id);
              }}
              onPlay={(e) => {
                console.log('✅ Video onPlay event:', element.id);
              }}
              onPause={(e) => {
                console.log('⏸️ Video onPause event:', element.id);
              }}
              onError={(e) => {
                console.error('❌ Video onError:', element.id, 'error:', e.target.error);
              }}
            />
          );
        }

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
        cursor: isDragging ? 'grabbing' : (isEditing ? 'text' : 'grab')
      }}
    >
      {renderElement()}

      {/* Selection Handles */}
      {isSelected && !isEditing && (
        <>
          {/* Resize handles - corner handles */}
          <div
            data-resize-handle="nw"
            onMouseDown={handleMouseDown}
            className="absolute -top-1 -left-1 w-3 h-3 bg-blue-500 rounded-full cursor-nwse-resize z-10"
          />
          <div
            data-resize-handle="ne"
            onMouseDown={handleMouseDown}
            className="absolute -top-1 -right-1 w-3 h-3 bg-blue-500 rounded-full cursor-nesw-resize z-10"
          />
          <div
            data-resize-handle="sw"
            onMouseDown={handleMouseDown}
            className="absolute -bottom-1 -left-1 w-3 h-3 bg-blue-500 rounded-full cursor-nesw-resize z-10"
          />
          <div
            data-resize-handle="se"
            onMouseDown={handleMouseDown}
            className="absolute -bottom-1 -right-1 w-3 h-3 bg-blue-500 rounded-full cursor-nwse-resize z-10"
          />

          {/* Edge handles for width/height only */}
          <div
            data-resize-handle="e"
            onMouseDown={handleMouseDown}
            className="absolute top-1/2 -right-1 w-3 h-3 bg-blue-500 rounded-full cursor-ew-resize z-10 -translate-y-1/2"
          />
          <div
            data-resize-handle="w"
            onMouseDown={handleMouseDown}
            className="absolute top-1/2 -left-1 w-3 h-3 bg-blue-500 rounded-full cursor-ew-resize z-10 -translate-y-1/2"
          />
        </>
      )}
    </div>
  );
};

export default CanvasElement;

