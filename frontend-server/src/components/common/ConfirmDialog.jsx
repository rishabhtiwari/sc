import React from 'react';

/**
 * Reusable Confirmation Dialog Component
 * @param {Object} props - Component props
 * @param {boolean} props.isOpen - Dialog open state
 * @param {Function} props.onClose - Close handler
 * @param {Function} props.onConfirm - Confirm handler
 * @param {string} props.title - Dialog title
 * @param {string} props.message - Main message content
 * @param {string} props.description - Optional subtitle/description
 * @param {string} props.warningMessage - Optional warning message to display
 * @param {string} props.confirmText - Text for confirm button (default: "Confirm")
 * @param {string} props.cancelText - Text for cancel button (default: "Cancel")
 * @param {string} props.variant - Dialog variant: 'danger', 'warning', 'info' (default: 'info')
 */
const ConfirmDialog = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  description,
  warningMessage,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  variant = 'info'
}) => {
  if (!isOpen) return null;

  // Variant-specific styling
  const variantStyles = {
    danger: {
      iconBg: 'bg-red-100',
      iconColor: 'text-red-600',
      buttonBg: 'bg-red-600 hover:bg-red-700',
      warningBg: 'bg-red-50 border-red-200',
      warningText: 'text-red-800'
    },
    warning: {
      iconBg: 'bg-yellow-100',
      iconColor: 'text-yellow-600',
      buttonBg: 'bg-yellow-600 hover:bg-yellow-700',
      warningBg: 'bg-yellow-50 border-yellow-200',
      warningText: 'text-yellow-800'
    },
    info: {
      iconBg: 'bg-blue-100',
      iconColor: 'text-blue-600',
      buttonBg: 'bg-blue-600 hover:bg-blue-700',
      warningBg: 'bg-blue-50 border-blue-200',
      warningText: 'text-blue-800'
    }
  };

  const styles = variantStyles[variant];

  // Icon based on variant
  const getIcon = () => {
    if (variant === 'danger') {
      return (
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      );
    } else if (variant === 'warning') {
      return (
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      );
    } else {
      return (
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      );
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
        {/* Header */}
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <div className={`flex-shrink-0 w-12 h-12 ${styles.iconBg} rounded-full flex items-center justify-center`}>
              <svg className={`w-6 h-6 ${styles.iconColor}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                {getIcon()}
              </svg>
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900">{title}</h2>
              {description && <p className="text-sm text-gray-600 mt-1">{description}</p>}
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          <p className="text-gray-700">{message}</p>
          
          {warningMessage && (
            <div className={`mt-4 p-4 ${styles.warningBg} border rounded-lg`}>
              <p className={`text-sm ${styles.warningText}`}>
                <strong>Warning:</strong> {warningMessage}
              </p>
            </div>
          )}
        </div>

        {/* Buttons */}
        <div className="flex gap-3 p-6 border-t border-gray-200">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
          >
            {cancelText}
          </button>
          <button
            onClick={onConfirm}
            className={`flex-1 px-4 py-2 ${styles.buttonBg} text-white rounded-lg transition-colors`}
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ConfirmDialog;

