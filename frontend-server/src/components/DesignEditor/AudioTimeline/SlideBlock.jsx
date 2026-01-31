import React, { useState, useEffect } from 'react';
import { useTimeline } from '../../common/Timeline';

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
  onTransitionClick
}) => {
  const { timeToPixels, pixelsToTime, formatTime } = useTimeline();
  const [isStretching, setIsStretching] = useState(false);
  const [stretchStart, setStretchStart] = useState(null);

  const blockWidth = timeToPixels(duration);
  const leftPosition = timeToPixels(startTime);

  // Calculate how many thumbnails to repeat across the block
  const thumbnailSize = 40;
  const thumbnailCount = Math.max(1, Math.floor(blockWidth / thumbnailSize));

  const handleStretchStart = (e, edge) => {
    e.stopPropagation();
    e.preventDefault();
    console.log('🎯 Slide stretch started:', index, edge);
    setIsStretching(true);
    setStretchStart({
      x: e.clientX,
      edge,
      initialDuration: duration
    });
  };

  const handleMouseMove = (e) => {
    if (!isStretching || !stretchStart) return;

    const deltaX = e.clientX - stretchStart.x;
    const deltaTime = pixelsToTime(deltaX);

    if (stretchStart.edge === 'right') {
      const newDuration = Math.max(1, stretchStart.initialDuration + deltaTime);
      console.log('🔧 Stretching slide right. New duration:', newDuration);
      if (onUpdate) {
        onUpdate({ duration: newDuration });
      }
    } else if (stretchStart.edge === 'left') {
      const newDuration = Math.max(1, stretchStart.initialDuration - deltaTime);
      console.log('🔧 Stretching slide left. New duration:', newDuration);
      if (onUpdate) {
        onUpdate({ duration: newDuration });
      }
    }
  };

  const handleMouseUp = () => {
    setIsStretching(false);
    setStretchStart(null);
  };

  useEffect(() => {
    if (isStretching) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
      return () => {
        window.removeEventListener('mousemove', handleMouseMove);
        window.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isStretching, stretchStart]);

  return (
    <>
      {/* Slide Block */}
      <div
        className={`absolute top-0 h-12 border rounded shadow-sm transition-all overflow-hidden ${
          isSelected
            ? 'bg-purple-500 border-2 border-purple-300 ring-2 ring-purple-200'
            : 'bg-purple-600 hover:bg-purple-500 border border-purple-400'
        }`}
        style={{
          left: `${leftPosition}px`,
          width: `${blockWidth}px`,
          minWidth: '40px'
        }}
        title={`${slide.name || `Slide ${index + 1}`} (${formatTime(duration)})`}
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
              className="flex-shrink-0 w-9 h-9 bg-purple-400 rounded border border-purple-300 flex items-center justify-center"
            >
              {slide.elements && slide.elements.length > 0 ? (
                slide.elements[0].type === 'image' ? (
                  <img
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
          className="absolute top-0 h-12 w-8 flex items-center justify-center cursor-pointer z-10 group"
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

