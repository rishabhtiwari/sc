import React from 'react';

/**
 * Reusable Badge Component
 * @param {Object} props - Component props
 * @param {string} props.variant - Badge variant (success, error, warning, info, default)
 * @param {string} props.size - Badge size (sm, md, lg)
 * @param {React.ReactNode} props.children - Badge content
 */
const Badge = ({ variant = 'default', size = 'md', children }) => {
  const variantClasses = {
    success: 'bg-green-100 text-green-800',
    error: 'bg-red-100 text-red-800',
    warning: 'bg-orange-100 text-orange-800',
    info: 'bg-blue-100 text-blue-800',
    default: 'bg-gray-100 text-gray-800',
  };

  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-sm',
    lg: 'px-3 py-1.5 text-base',
  };

  return (
    <span
      className={`
        inline-flex items-center font-medium rounded-full
        ${variantClasses[variant]}
        ${sizeClasses[size]}
      `}
    >
      {children}
    </span>
  );
};

export default Badge;

