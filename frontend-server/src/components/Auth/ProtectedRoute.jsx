import React from 'react';
import { Navigate } from 'react-router-dom';
import { hasPermission, hasAnyPermission } from '../../services/authService';

/**
 * ProtectedRoute component
 * Wraps routes that require specific permissions
 */
const ProtectedRoute = ({ 
  children, 
  permission, 
  permissions, 
  requireAll = false,
  fallback = null 
}) => {
  // Check if user has required permission(s)
  let hasAccess = true;

  if (permission) {
    // Single permission check
    hasAccess = hasPermission(permission);
  } else if (permissions && permissions.length > 0) {
    // Multiple permissions check
    if (requireAll) {
      // User must have ALL permissions
      hasAccess = permissions.every(p => hasPermission(p));
    } else {
      // User must have ANY permission
      hasAccess = hasAnyPermission(permissions);
    }
  }

  if (!hasAccess) {
    // Show fallback or redirect
    if (fallback) {
      return fallback;
    }
    
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8 text-center">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Access Denied</h2>
          <p className="text-gray-600 mb-6">
            You don't have permission to access this page. Please contact your administrator if you believe this is an error.
          </p>
          <button
            onClick={() => window.history.back()}
            className="bg-indigo-600 text-white px-6 py-2 rounded-lg hover:bg-indigo-700"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  return children;
};

export default ProtectedRoute;

