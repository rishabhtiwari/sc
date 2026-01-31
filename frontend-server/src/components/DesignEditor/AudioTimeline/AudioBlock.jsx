import React, { useRef, useEffect, useState } from 'react';
import { useTimeline } from '../../common/Timeline';

/**
 * Audio Block Component
 * Renders a single audio track block with waveform visualization
 */
const AudioBlock = ({
  track,
  index,
  isSelected,
  onSelect,
  onUpdate,
  waveformData,
  volumeEnvelope,
  colors
}) => {
  const { timeToPixels, pixelsToTime, formatTime } = useTimeline();
  const canvasRef = useRef(null);
  const [isStretching, setIsStretching] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [stretchStart, setStretchStart] = useState(null);
  const [dragStart, setDragStart] = useState(null);

  const startTime = track.startTime || 0;
  const duration = track.duration || 0;
  const blockWidth = timeToPixels(duration);
  const leftPosition = timeToPixels(startTime);

  // Draw waveform on canvas
  useEffect(() => {
    if (canvasRef.current && waveformData) {
      const canvas = canvasRef.current;
      const ctx = canvas.getContext('2d');
      const width = canvas.width;
      const height = canvas.height;

      // Clear canvas
      ctx.clearRect(0, 0, width, height);

      // Draw waveform
      const barWidth = width / waveformData.length;
      waveformData.forEach((amplitude, i) => {
        const barHeight = amplitude * height * 0.8;
        const x = i * barWidth;
        const y = (height - barHeight) / 2;

        ctx.fillStyle = 'rgba(255, 255, 255, 0.6)';
        ctx.fillRect(x, y, Math.max(1, barWidth - 1), barHeight);
      });

      // Draw volume envelope line
      if (volumeEnvelope) {
        const volumeY = height * (1 - volumeEnvelope.volume / 100);
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.8)';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(0, volumeY);
        ctx.lineTo(width, volumeY);
        ctx.stroke();
      }
    }
  }, [waveformData, volumeEnvelope, blockWidth]);

  const handleStretchStart = (e, edge) => {
    e.stopPropagation();
    e.preventDefault();
    console.log('🎯 Audio stretch started:', track.id, edge);
    setIsStretching(true);
    setStretchStart({
      x: e.clientX,
      edge,
      initialStartTime: startTime,
      initialDuration: duration
    });
  };

  const handleDragStart = (e) => {
    // Don't drag if clicking on handles
    if (e.target.classList.contains('cursor-ew-resize')) {
      return;
    }

    e.stopPropagation();
    console.log('🎯 Audio drag started:', track.id);
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
        if (onUpdate) {
          onUpdate({ duration: newDuration });
        }
      } else if (stretchStart.edge === 'left') {
        const newStartTime = Math.max(0, stretchStart.initialStartTime + deltaTime);
        const newDuration = Math.max(1, stretchStart.initialDuration - deltaTime);
        if (onUpdate) {
          onUpdate({ startTime: newStartTime, duration: newDuration });
        }
      }
    } else if (isDragging && dragStart) {
      const deltaX = e.clientX - dragStart.x;
      const deltaTime = pixelsToTime(deltaX);
      const newStartTime = Math.max(0, dragStart.initialStartTime + deltaTime);

      if (onUpdate) {
        onUpdate({ startTime: newStartTime });
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
    <div
      className={`absolute top-0 h-16 border rounded shadow-sm cursor-move transition-all overflow-hidden ${
        isSelected
          ? `${colors.bg} border-2 ${colors.border} ring-2 ring-opacity-50`
          : `${colors.bg} ${colors.hover} border ${colors.border}`
      }`}
      style={{
        left: `${leftPosition}px`,
        width: `${blockWidth}px`,
        minWidth: '40px'
      }}
      title={`${track.name} (${formatTime(duration)})`}
      onClick={(e) => {
        e.stopPropagation();
        if (onSelect) onSelect();
      }}
      onMouseDown={handleDragStart}
    >
      {/* Waveform Canvas */}
      <canvas
        ref={canvasRef}
        width={Math.max(40, blockWidth)}
        height={64}
        className="absolute inset-0 pointer-events-none"
      />

      {/* Track Name */}
      <div className="absolute top-0 left-0 right-0 px-2 py-0.5 text-xs font-medium text-white truncate bg-black bg-opacity-30 backdrop-blur-sm">
        {track.name}
      </div>

      {/* Duration Label */}
      <div className="absolute bottom-0 right-0 px-2 py-0.5 text-xs font-medium text-white bg-black bg-opacity-30 backdrop-blur-sm rounded-tl">
        {formatTime(duration)}
      </div>

      {/* Left Stretch Handle */}
      <div
        className="absolute left-0 top-0 bottom-0 w-2 bg-white bg-opacity-50 cursor-ew-resize hover:bg-opacity-70 transition-colors z-20"
        onMouseDown={(e) => handleStretchStart(e, 'left')}
        onClick={(e) => e.stopPropagation()}
        title="Drag to adjust start time"
      />

      {/* Right Stretch Handle */}
      <div
        className="absolute right-0 top-0 bottom-0 w-2 bg-white bg-opacity-50 cursor-ew-resize hover:bg-opacity-70 transition-colors z-20"
        onMouseDown={(e) => handleStretchStart(e, 'right')}
        onClick={(e) => e.stopPropagation()}
        title="Drag to extend duration"
      />
    </div>
  );
};

export default AudioBlock;

