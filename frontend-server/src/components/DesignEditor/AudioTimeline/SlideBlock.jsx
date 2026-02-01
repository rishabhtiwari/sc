import React, { useState, useEffect } from 'react';
import { useTimeline } from '../../common/Timeline';
import AuthenticatedImage from '../../common/AuthenticatedImage';

/**
 * Slide Block Component
 * Renders a single slide block on the timeline with thumbnails and stretch handles
 */
const SlideBlock = ({
  slide,
  index,
  startTime,
  duration,
  isSelected,
  onSelect,
  onUpdate,
  onTransitionClick,
  allSlides = [] // All slides for collision detection
}) => {
  const { timeToPixels, pixelsToTime, formatTime } = useTimeline();
  const [isStretching, setIsStretching] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [stretchStart, setStretchStart] = useState(null);
  const [dragStart, setDragStart] = useState(null);

  const blockWidth = timeToPixels(duration);
  const leftPosition = timeToPixels(startTime);

  // Calculate how many thumbnails to repeat across the block
  const thumbnailSize = 40;
  const thumbnailCount = Math.max(1, Math.floor(blockWidth / thumbnailSize));

  /**
   * Check if a new position would cause collision with other slides
   * @param {number} newStart - Proposed start time
   * @param {number} newDur - Proposed duration
   * @returns {boolean} - True if collision detected
   */
  const checkCollision = (newStart, newDur) => {
    const newEnd = newStart + newDur;

    return allSlides.some((otherSlide, otherIndex) => {
      // Don't check collision with self
      if (otherIndex === index) return false;

      const otherStart = otherSlide.startTime !== undefined ? otherSlide.startTime : 0;
      const otherDur = otherSlide.duration || 5;
      const otherEnd = otherStart + otherDur;

      // Check if ranges overlap
      return (newStart < otherEnd && newEnd > otherStart);
    });
  };

  const handleStretchStart = (e, edge) => {
    e.stopPropagation();
    e.preventDefault();
    console.log('🎯 Slide stretch started:', index, edge);
    setIsStretching(true);
    setStretchStart({
      x: e.clientX,
      edge,
      initialDuration: duration,
      initialStartTime: startTime
    });
  };

  const handleDragStart = (e) => {
    // Don't drag if clicking on handles
    if (e.target.classList.contains('cursor-ew-resize')) {
      return;
    }

    e.stopPropagation();
    console.log('🎯 Slide drag started:', index);
    setIsDragging(true);
    setDragStart({
      x: e.clientX,
      initialStartTime: startTime
    });
  };

  const handleMouseMove = (e) => {
    if (isStretching && stretchStart) {
      const deltaX = e.clientX - stretchStart.x;
      const deltaTime = pixelsToTime(deltaX);

      if (stretchStart.edge === 'right') {
        const newDuration = Math.max(1, stretchStart.initialDuration + deltaTime);

        // Check collision before updating
        if (!checkCollision(startTime, newDuration)) {
          console.log('🔧 Stretching slide right. New duration:', newDuration);
          if (onUpdate) {
            onUpdate({ duration: newDuration });
          }
        } else {
          console.log('⚠️ Collision detected - cannot stretch right');
        }
      } else if (stretchStart.edge === 'left') {
        const newDuration = Math.max(1, stretchStart.initialDuration - deltaTime);
        const newStartTime = Math.max(0, stretchStart.initialStartTime + deltaTime);

        // Check collision before updating
        if (!checkCollision(newStartTime, newDuration)) {
          console.log('🔧 Stretching slide left. New duration:', newDuration, 'New start:', newStartTime);
          if (onUpdate) {
            onUpdate({ duration: newDuration, startTime: newStartTime });
          }
        } else {
          console.log('⚠️ Collision detected - cannot stretch left');
        }
      }
    } else if (isDragging && dragStart) {
      const deltaX = e.clientX - dragStart.x;
      const deltaTime = pixelsToTime(deltaX);
      const newStartTime = Math.max(0, dragStart.initialStartTime + deltaTime);

      // Check collision before updating
      if (!checkCollision(newStartTime, duration)) {
        console.log('🔧 Dragging slide. New start time:', newStartTime);
        if (onUpdate) {
          onUpdate({ startTime: newStartTime });
        }
      } else {
        console.log('⚠️ Collision detected - cannot move to:', newStartTime);
      }
    }
  };

  const handleMouseUp = () => {
    setIsStretching(false);
    setIsDragging(false);
    setStretchStart(null);
    setDragStart(null);
  };

  useEffect(() => {
    if (isStretching || isDragging) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
      return () => {
        window.removeEventListener('mousemove', handleMouseMove);
        window.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isStretching, isDragging, stretchStart, dragStart]);

  return (
    <>
      {/* Slide Block */}
      <div
        className={`absolute top-0 h-20 border rounded shadow-sm transition-all overflow-hidden ${
          isSelected
            ? 'bg-purple-500 border-2 border-purple-300 ring-2 ring-purple-200'
            : 'bg-purple-600 hover:bg-purple-500 border border-purple-400'
        } ${isDragging ? 'cursor-grabbing' : 'cursor-grab'}`}
        style={{
          left: `${leftPosition}px`,
          width: `${blockWidth}px`,
          minWidth: '40px'
        }}
        title={`${slide.name || `Slide ${index + 1}`} (${formatTime(duration)})`}
        onMouseDown={handleDragStart}
        onClick={(e) => {
          e.stopPropagation();
          if (onSelect) onSelect();
        }}
      >
        {/* Repeating Thumbnails */}
        <div className="h-full flex items-center gap-0.5 px-1">
          {Array.from({ length: thumbnailCount }).map((_, thumbIdx) => (
            <div
              key={thumbIdx}
              className="flex-shrink-0 w-14 h-14 bg-purple-400 rounded border border-purple-300 flex items-center justify-center"
            >
              {slide.elements && slide.elements.length > 0 ? (
                slide.elements[0].type === 'image' ? (
                  <AuthenticatedImage
                    src={slide.elements[0].src}
                    alt=""
                    className="w-full h-full object-cover rounded"
                  />
                ) : (
                  <span>📄</span>
                )
              ) : (
                <span>📄</span>
              )}
            </div>
          ))}
        </div>

        {/* Slide Label */}
        <div className="absolute top-0 left-0 right-0 px-2 py-0.5 text-xs font-medium text-white truncate bg-black bg-opacity-30 backdrop-blur-sm">
          {slide.name || `Slide ${index + 1}`}
        </div>

        {/* Left Stretch Handle */}
        <div
          className="absolute left-0 top-0 bottom-0 w-2 bg-purple-400 cursor-ew-resize hover:bg-purple-300 transition-colors border-r border-purple-300 z-20"
          onMouseDown={(e) => handleStretchStart(e, 'left')}
          onClick={(e) => e.stopPropagation()}
          title="Drag to adjust start time"
        />

        {/* Right Stretch Handle */}
        <div
          className="absolute right-0 top-0 bottom-0 w-2 bg-purple-400 cursor-ew-resize hover:bg-purple-300 transition-colors border-l border-purple-300 z-20"
          onMouseDown={(e) => handleStretchStart(e, 'right')}
          onClick={(e) => e.stopPropagation()}
          title="Drag to extend duration"
        />
      </div>

      {/* Transition Icon Between Slides */}
      {onTransitionClick && (
        <div
          className="absolute top-0 h-20 w-8 flex items-center justify-center cursor-pointer z-10 group"
          style={{
            left: `${leftPosition + blockWidth - 16}px`
          }}
          onClick={(e) => {
            e.stopPropagation();
            onTransitionClick();
          }}
          title="Click to change transition"
        >
          <div className="w-6 h-6 bg-yellow-500 rounded-full flex items-center justify-center text-xs shadow-md group-hover:bg-yellow-400 transition-colors border-2 border-white">
            ⚡
          </div>
        </div>
      )}
    </>
  );
};

export default SlideBlock;

