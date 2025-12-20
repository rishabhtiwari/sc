import React from 'react';

/**
 * Reusable Card Component - Rubrik Style
 * @param {Object} props - Component props
 * @param {string} props.title - Card title
 * @param {string} props.subtitle - Card subtitle
 * @param {React.ReactNode} props.actions - Action buttons/elements
 * @param {string} props.className - Additional CSS classes
 * @param {boolean} props.hover - Enable hover effect
 * @param {boolean} props.noPadding - Remove padding from content area
 * @param {React.ReactNode} props.children - Card content
 */
const Card = ({
  title,
  subtitle,
  actions,
  className = '',
  hover = false,
  noPadding = false,
  children
}) => {
  return (
    <div
      className={`
        rounded-lg border border-neutral-200 overflow-hidden
        ${hover ? 'card-hover cursor-pointer' : 'shadow-sm'}
        ${className}
      `}
      style={{ backgroundColor: '#ffffff' }}
    >
      {(title || subtitle || actions) && (
        <div className="px-5 py-4 border-b border-neutral-200" style={{ backgroundColor: '#f8fafc' }}>
          <div className="flex items-center justify-between">
            <div className="flex-1 min-w-0">
              {title && (
                <h3 className="text-base font-semibold text-neutral-900 truncate">
                  {title}
                </h3>
              )}
              {subtitle && (
                <p className="text-sm text-neutral-600 mt-0.5 truncate">
                  {subtitle}
                </p>
              )}
            </div>
            {actions && (
              <div className="flex items-center gap-2 ml-4">
                {actions}
              </div>
            )}
          </div>
        </div>
      )}
      <div className={noPadding ? '' : 'p-5'}>
        {children}
      </div>
    </div>
  );
};

export default Card;

