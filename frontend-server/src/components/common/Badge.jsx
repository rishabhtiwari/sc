import React from 'react';

/**
 * Reusable Badge Component - Rubrik Style
 * @param {Object} props - Component props
 * @param {string} props.variant - Badge variant (success, error, warning, info, default, primary)
 * @param {string} props.size - Badge size (xs, sm, md, lg)
 * @param {boolean} props.dot - Show dot indicator
 * @param {React.ReactNode} props.children - Badge content
 */
const Badge = ({
  variant = 'default',
  size = 'md',
  dot = false,
  children
}) => {
  const variantClasses = {
    success: 'bg-green-100 text-green-800 border-green-200',
    error: 'bg-red-100 text-red-800 border-red-200',
    warning: 'bg-orange-100 text-orange-800 border-orange-200',
    info: 'bg-blue-100 text-blue-800 border-blue-200',
    primary: 'bg-blue-600 text-white border-blue-700',
    default: 'bg-neutral-100 text-neutral-800 border-neutral-200',
  };

  const dotColors = {
    success: 'bg-green-500',
    error: 'bg-red-500',
    warning: 'bg-orange-500',
    info: 'bg-blue-500',
    primary: 'bg-white',
    default: 'bg-neutral-500',
  };

  const sizeClasses = {
    xs: 'px-1.5 py-0.5 text-xs',
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-sm',
    lg: 'px-3 py-1.5 text-sm',
  };

  return (
    <span
      className={`
        inline-flex items-center gap-1.5 font-medium rounded-md border
        ${variantClasses[variant]}
        ${sizeClasses[size]}
      `}
    >
      {dot && (
        <span className={`w-1.5 h-1.5 rounded-full ${dotColors[variant]}`}></span>
      )}
      {children}
    </span>
  );
};

export default Badge;

