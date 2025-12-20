import React from 'react';

/**
 * Professional Button Component - Enterprise SaaS Style
 * Follows modern design principles with consistent sizing and minimal color variants
 *
 * @param {Object} props - Component props
 * @param {string} props.variant - Button variant (primary, secondary, ghost, text)
 * @param {boolean} props.disabled - Disabled state
 * @param {boolean} props.loading - Loading state
 * @param {string} props.icon - Icon emoji or SVG
 * @param {Function} props.onClick - Click handler
 * @param {string} props.className - Additional CSS classes
 * @param {React.ReactNode} props.children - Button content
 */
const Button = ({
  variant = 'primary',
  disabled = false,
  loading = false,
  icon,
  onClick,
  className = '',
  children,
  ...props
}) => {
  // Base classes - consistent for all buttons
  const baseClasses = 'inline-flex items-center justify-center gap-2 px-4 py-2 text-sm font-medium rounded-md transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed';

  // Minimal variant system - professional single-color approach
  const variantClasses = {
    // Primary - Main action button (blue)
    primary: 'bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white shadow-sm hover:shadow focus:ring-blue-500',

    // Secondary - Alternative action (outlined)
    secondary: 'bg-white hover:bg-neutral-50 active:bg-neutral-100 text-neutral-700 border border-neutral-300 hover:border-neutral-400 focus:ring-blue-500',

    // Ghost - Subtle action (transparent)
    ghost: 'bg-transparent hover:bg-neutral-100 active:bg-neutral-200 text-neutral-700 hover:text-neutral-900 focus:ring-blue-500',

    // Text - Minimal action (no background)
    text: 'bg-transparent hover:bg-neutral-50 active:bg-neutral-100 text-blue-600 hover:text-blue-700 focus:ring-blue-500',
  };

  const classes = `
    ${baseClasses}
    ${variantClasses[variant] || variantClasses.primary}
    ${className}
  `.trim();

  return (
    <button
      className={classes}
      onClick={onClick}
      disabled={disabled || loading}
      {...props}
    >
      {loading && (
        <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
      )}
      {!loading && icon && <span className="flex-shrink-0">{icon}</span>}
      {children && <span>{children}</span>}
    </button>
  );
};

export default Button;

