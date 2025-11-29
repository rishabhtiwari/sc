import React from 'react';

/**
 * ProgressBar Component
 * Displays a progress bar with percentage and optional message
 * 
 * @param {number} progress - Progress percentage (0-100)
 * @param {string} status - Status ('running', 'completed', 'error', 'idle')
 * @param {string} message - Optional message to display
 * @param {boolean} showPercentage - Show percentage text (default: true)
 * @param {string} size - Size ('sm', 'md', 'lg') (default: 'md')
 */
const ProgressBar = ({ 
  progress = 0, 
  status = 'idle',
  message = '',
  showPercentage = true,
  size = 'md'
}) => {
  // Ensure progress is between 0 and 100
  const normalizedProgress = Math.min(Math.max(progress, 0), 100);

  // Size classes
  const sizeClasses = {
    sm: 'h-2',
    md: 'h-4',
    lg: 'h-6'
  };

  // Status colors
  const statusColors = {
    idle: 'bg-gray-300',
    running: 'bg-blue-500',
    completed: 'bg-green-500',
    error: 'bg-red-500'
  };

  // Animation classes
  const animationClass = status === 'running' ? 'animate-pulse' : '';

  return (
    <div className="w-full">
      {/* Message */}
      {message && (
        <div className="mb-2 flex items-center justify-between">
          <span className="text-sm text-gray-700">{message}</span>
          {showPercentage && (
            <span className="text-sm font-semibold text-gray-900">
              {normalizedProgress}%
            </span>
          )}
        </div>
      )}

      {/* Progress bar container */}
      <div className={`w-full bg-gray-200 rounded-full overflow-hidden ${sizeClasses[size]}`}>
        {/* Progress bar fill */}
        <div
          className={`${statusColors[status]} ${sizeClasses[size]} rounded-full transition-all duration-300 ease-out ${animationClass}`}
          style={{ width: `${normalizedProgress}%` }}
        >
          {/* Shimmer effect for running status */}
          {status === 'running' && (
            <div className="h-full w-full bg-gradient-to-r from-transparent via-white to-transparent opacity-30 animate-shimmer"></div>
          )}
        </div>
      </div>

      {/* Percentage below bar (if message is not shown) */}
      {!message && showPercentage && (
        <div className="mt-1 text-right">
          <span className="text-xs text-gray-600">{normalizedProgress}%</span>
        </div>
      )}
    </div>
  );
};

export default ProgressBar;

