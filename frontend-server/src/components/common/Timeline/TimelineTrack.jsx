import React from 'react';

/**
 * Timeline Track Component
 *
 * Represents a single track in the timeline (e.g., slides, audio, video).
 *
 * @param {Object} props
 * @param {string} props.type - Type of track ('slides', 'audio', 'video')
 * @param {number} props.height - Height of the track in pixels
 * @param {number} props.maxHeight - Maximum height before scrolling (optional)
 * @param {string} props.label - Optional label for the track
 * @param {string} props.className - Additional CSS classes
 * @param {React.ReactNode} props.children - Track content (blocks)
 */
const TimelineTrack = ({
  type = 'generic',
  height = 80,
  maxHeight,
  label,
  className = '',
  children
}) => {
  const getTrackStyles = () => {
    switch (type) {
      case 'slides':
        return 'bg-white border-b border-gray-200';
      case 'audio':
        return 'bg-gray-50 border-b border-gray-100';
      case 'video':
        return 'bg-blue-50 border-b border-blue-100';
      default:
        return 'bg-white border-b border-gray-200';
    }
  };

  // Determine if scrolling is needed
  const needsScroll = maxHeight && height > maxHeight;
  const finalHeight = needsScroll ? maxHeight : height;

  return (
    <div
      className={`relative ${getTrackStyles()} ${className} ${needsScroll ? 'overflow-y-auto' : ''}`}
      style={{
        height: `${finalHeight}px`,
        maxHeight: maxHeight ? `${maxHeight}px` : undefined
      }}
    >
      {label && (
        <div className="sticky top-0 left-0 px-2 py-1 text-xs font-semibold text-gray-600 bg-white bg-opacity-90 z-10 border-b border-gray-200">
          {label}
        </div>
      )}
      <div style={{ height: needsScroll ? `${height}px` : '100%' }}>
        {children}
      </div>
    </div>
  );
};

export default TimelineTrack;

