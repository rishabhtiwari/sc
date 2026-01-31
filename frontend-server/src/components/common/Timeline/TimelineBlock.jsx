import React, { useState, useEffect } from 'react';
import { useTimeline } from './TimelineContext';

/**
 * Timeline Block Component
 * 
 * Represents a draggable and stretchable block on the timeline.
 * 
 * @param {Object} props
 * @param {number} props.startTime - Start time in seconds
 * @param {number} props.duration - Duration in seconds
 * @param {Function} props.onStretch - Callback when block is stretched: (edge, newDuration, newStartTime) => {}
 * @param {Function} props.onDrag - Callback when block is dragged: (newStartTime) => {}
 * @param {Function} props.onClick - Callback when block is clicked
 * @param {boolean} props.stretchable - Whether block can be stretched (default: true)
 * @param {boolean} props.draggable - Whether block can be dragged (default: true)
 * @param {string} props.className - Additional CSS classes
 * @param {React.ReactNode} props.children - Block content
 */
const TimelineBlock = ({
  startTime = 0,
  duration = 5,
  onStretch,
  onDrag,
  onClick,
  stretchable = true,
  draggable = true,
  className = '',
  children
}) => {
  const { timeToPixels, pixelsToTime, availableWidth } = useTimeline();
  
  const [isDragging, setIsDragging] = useState(false);
  const [isStretching, setIsStretching] = useState(false);
  const [dragStart, setDragStart] = useState(null);
  const [stretchStart, setStretchStart] = useState(null);

  // Calculate position and width
  const leftPosition = timeToPixels(startTime);
  const blockWidth = timeToPixels(duration);

  // Ensure block stays within boundaries
  const clampedLeft = Math.max(0, Math.min(leftPosition, availableWidth));
  const clampedWidth = Math.max(20, Math.min(blockWidth, availableWidth - clampedLeft));

  // Handle stretch start
  const handleStretchStart = (e, edge) => {
    if (!stretchable) return;
    
    e.stopPropagation();
    e.preventDefault();
    
    console.log('🎯 Stretch started:', edge, 'startTime:', startTime, 'duration:', duration);
    
    setIsStretching(true);
    setStretchStart({
      x: e.clientX,
      startTime,
      duration,
      edge
    });
  };

  // Handle drag start
  const handleDragStart = (e) => {
    if (!draggable) return;
    
    // Don't drag if clicking on handles
    if (e.target.classList.contains('cursor-ew-resize')) {
      return;
    }
    
    e.stopPropagation();
    
    console.log('🎯 Drag started:', 'startTime:', startTime);
    
    setIsDragging(true);
    setDragStart({
      x: e.clientX,
      startTime
    });
  };

  // Handle mouse move
  const handleMouseMove = (e) => {
    if (isDragging && dragStart && onDrag) {
      const deltaX = e.clientX - dragStart.x;
      const deltaTime = pixelsToTime(deltaX);
      const newStartTime = Math.max(0, dragStart.startTime + deltaTime);
      
      onDrag(newStartTime);
    } else if (isStretching && stretchStart && onStretch) {
      const deltaX = e.clientX - stretchStart.x;
      const deltaTime = pixelsToTime(deltaX);

      if (stretchStart.edge === 'right') {
        const newDuration = Math.max(1, stretchStart.duration + deltaTime);
        console.log('🔧 Stretching right. New duration:', newDuration);
        onStretch('right', newDuration, stretchStart.startTime);
      } else if (stretchStart.edge === 'left') {
        const newStartTime = Math.max(0, stretchStart.startTime + deltaTime);
        const newDuration = Math.max(1, stretchStart.duration - deltaTime);
        console.log('🔧 Stretching left. New duration:', newDuration, 'New start:', newStartTime);
        onStretch('left', newDuration, newStartTime);
      }
    }
  };

  // Handle mouse up
  const handleMouseUp = () => {
    setIsDragging(false);
    setIsStretching(false);
    setDragStart(null);
    setStretchStart(null);
  };

  // Add mouse event listeners
  useEffect(() => {
    if (isDragging || isStretching) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
      return () => {
        window.removeEventListener('mousemove', handleMouseMove);
        window.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isDragging, isStretching, dragStart, stretchStart]);

  return (
    <div
      className={`absolute top-0 h-full rounded shadow-sm transition-all ${
        draggable ? 'cursor-move' : ''
      } ${className}`}
      style={{
        left: `${clampedLeft}px`,
        width: `${clampedWidth}px`,
        minWidth: '20px'
      }}
      onMouseDown={handleDragStart}
      onClick={(e) => {
        e.stopPropagation();
        if (onClick) onClick();
      }}
    >
      {children}

      {/* Left Stretch Handle */}
      {stretchable && (
        <div
          className="absolute left-0 top-0 bottom-0 w-2 bg-purple-400 cursor-ew-resize hover:bg-purple-300 transition-colors border-r border-purple-300 z-20"
          onMouseDown={(e) => handleStretchStart(e, 'left')}
          onClick={(e) => e.stopPropagation()}
          title="Drag to adjust start time"
        />
      )}

      {/* Right Stretch Handle */}
      {stretchable && (
        <div
          className="absolute right-0 top-0 bottom-0 w-2 bg-purple-400 cursor-ew-resize hover:bg-purple-300 transition-colors border-l border-purple-300 z-20"
          onMouseDown={(e) => handleStretchStart(e, 'right')}
          onClick={(e) => e.stopPropagation()}
          title="Drag to extend duration"
        />
      )}
    </div>
  );
};

export default TimelineBlock;

