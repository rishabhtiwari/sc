import React from 'react';

/**
 * Reusable Spinner Component
 * @param {Object} props - Component props
 * @param {string} props.size - Spinner size (sm, md, lg)
 * @param {string} props.color - Spinner color
 * @param {string} props.message - Loading message
 */
const Spinner = ({ size = 'md', color = 'blue', message }) => {
  const sizeClasses = {
    sm: 'h-6 w-6',
    md: 'h-12 w-12',
    lg: 'h-16 w-16',
  };

  const colorClasses = {
    blue: 'border-blue-600',
    green: 'border-green-600',
    red: 'border-red-600',
    gray: 'border-gray-600',
  };

  return (
    <div className="flex flex-col items-center justify-center">
      <div
        className={`
          animate-spin rounded-full border-b-2
          ${sizeClasses[size]}
          ${colorClasses[color]}
        `}
      ></div>
      {message && <p className="mt-4 text-gray-600">{message}</p>}
    </div>
  );
};

export default Spinner;

