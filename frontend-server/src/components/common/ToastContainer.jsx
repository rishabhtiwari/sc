import React from 'react';

/**
 * Toast Container Component
 * Displays toast notifications in a fixed position
 * 
 * @param {Object} props - Component props
 * @param {Array} props.toasts - Array of toast objects { id, message, type }
 * @param {Function} props.onDismiss - Callback when user dismisses a toast
 * @param {string} props.position - Position of toast container (top-right, top-left, bottom-right, bottom-left)
 */
const ToastContainer = ({
  toasts = [],
  onDismiss,
  position = 'top-right'
}) => {
  if (!toasts || toasts.length === 0) return null;

  const positionClasses = {
    'top-right': 'top-4 right-4',
    'top-left': 'top-4 left-4',
    'bottom-right': 'bottom-4 right-4',
    'bottom-left': 'bottom-4 left-4'
  };

  const typeStyles = {
    success: {
      bg: 'bg-green-50',
      border: 'border-green-500',
      text: 'text-green-800',
      icon: '✅'
    },
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
    }
  };

  return (
    <div className={`fixed ${positionClasses[position]} z-50 space-y-2 max-w-md`}>
      {toasts.map((toast) => {
        const styles = typeStyles[toast.type] || typeStyles.info;
        
        return (
          <div
            key={toast.id}
            className={`${styles.bg} border-l-4 ${styles.border} p-4 rounded-lg shadow-lg animate-slide-in-right`}
          >
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-start gap-3 flex-1">
                <span className="text-xl flex-shrink-0">{styles.icon}</span>
                <p className={`text-sm font-medium ${styles.text} flex-1`}>{toast.message}</p>
              </div>
              {onDismiss && (
                <button
                  onClick={() => onDismiss(toast.id)}
                  className={`${styles.text} hover:opacity-70 transition-opacity flex-shrink-0`}
                  aria-label="Dismiss"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default ToastContainer;

