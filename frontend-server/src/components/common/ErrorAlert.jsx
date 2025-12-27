import React from 'react';
import Button from './Button';

/**
 * Generic Error Alert Component
 * Displays error messages with dismiss functionality
 * 
 * @param {Object} props - Component props
 * @param {string} props.message - Error message to display
 * @param {string} props.title - Optional error title (default: "Error")
 * @param {Function} props.onDismiss - Callback when user dismisses the error
 * @param {string} props.variant - Alert variant (error, warning, info, success)
 * @param {boolean} props.dismissible - Whether the alert can be dismissed (default: true)
 */
const ErrorAlert = ({
  message,
  title = 'Error',
  onDismiss,
  variant = 'error',
  dismissible = true
}) => {
  if (!message) return null;

  const variantStyles = {
    error: {
      bg: 'bg-red-50',
      border: 'border-red-500',
      text: 'text-red-800',
      icon: '❌'
    },
    warning: {
      bg: 'bg-yellow-50',
      border: 'border-yellow-500',
      text: 'text-yellow-800',
      icon: '⚠️'
    },
    info: {
      bg: 'bg-blue-50',
      border: 'border-blue-500',
      text: 'text-blue-800',
      icon: 'ℹ️'
    },
    success: {
      bg: 'bg-green-50',
      border: 'border-green-500',
      text: 'text-green-800',
      icon: '✅'
    }
  };

  const styles = variantStyles[variant] || variantStyles.error;

  return (
    <div className={`${styles.bg} border-l-4 ${styles.border} p-4 rounded-lg mb-4`}>
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-3 flex-1">
          <span className="text-2xl flex-shrink-0">{styles.icon}</span>
          <div className="flex-1">
            <h3 className={`font-semibold ${styles.text} mb-1`}>{title}</h3>
            <p className={`text-sm ${styles.text}`}>{message}</p>
          </div>
        </div>
        {dismissible && onDismiss && (
          <button
            onClick={onDismiss}
            className={`ml-4 ${styles.text} hover:opacity-70 transition-opacity flex-shrink-0`}
            aria-label="Dismiss"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>
    </div>
  );
};

export default ErrorAlert;

