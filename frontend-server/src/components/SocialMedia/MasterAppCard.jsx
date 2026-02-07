import React from 'react';
import { Card } from '../common';

/**
 * Master App Card Component
 * Displays a single master app with status and actions
 */
const MasterAppCard = ({ masterApp, platform, onEdit, onDelete, onActivate }) => {
  const isActive = masterApp?.is_active;
  const isConfigured = !!masterApp;

  const handleActivate = () => {
    if (masterApp && !isActive) {
      onActivate(masterApp._id);
    }
  };

  if (!isConfigured) {
    // Not configured state
    return (
      <Card className="hover:shadow-lg transition-shadow">
        <div className="p-6 text-center">
          <div className="text-5xl mb-3">{platform.icon}</div>
          <h3 className="font-semibold text-gray-900 mb-2">{platform.name}</h3>
          <p className="text-sm text-gray-500 mb-4">Not Configured</p>
          <button
            onClick={() => onEdit(null, platform.id)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
          >
            Configure App
          </button>
        </div>
      </Card>
    );
  }

  return (
    <Card className={`hover:shadow-lg transition-shadow ${isActive ? 'ring-2 ring-green-500' : ''}`}>
      <div className="p-6">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className={`text-4xl`}>{platform.icon}</div>
            <div>
              <h3 className="font-semibold text-gray-900">{masterApp.app_name}</h3>
              <p className="text-xs text-gray-500">{platform.name}</p>
            </div>
          </div>
          
          {/* Status Badge */}
          {isActive ? (
            <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full flex items-center gap-1">
              <span className="w-1.5 h-1.5 bg-green-500 rounded-full"></span>
              Active
            </span>
          ) : (
            <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
              Inactive
            </span>
          )}
        </div>

        {/* App Details */}
        <div className="space-y-2 mb-4">
          <div className="flex items-center gap-2 text-sm">
            <span className="text-gray-500">App ID:</span>
            <code className="text-xs bg-gray-100 px-2 py-1 rounded">{masterApp.app_id}</code>
          </div>
          
          <div className="flex items-center gap-2 text-sm">
            <span className="text-gray-500">Created:</span>
            <span className="text-gray-700">
              {new Date(masterApp.created_at).toLocaleDateString()}
            </span>
          </div>

          {masterApp.metadata?.environment && (
            <div className="flex items-center gap-2 text-sm">
              <span className="text-gray-500">Environment:</span>
              <span className="text-gray-700 capitalize">{masterApp.metadata.environment}</span>
            </div>
          )}
        </div>

        {/* Scopes */}
        {masterApp.scopes && masterApp.scopes.length > 0 && (
          <div className="mb-4">
            <p className="text-xs text-gray-500 mb-2">Scopes:</p>
            <div className="flex flex-wrap gap-1">
              {masterApp.scopes.slice(0, 3).map((scope, idx) => (
                <span key={idx} className="px-2 py-0.5 bg-blue-50 text-blue-700 text-xs rounded">
                  {scope}
                </span>
              ))}
              {masterApp.scopes.length > 3 && (
                <span className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded">
                  +{masterApp.scopes.length - 3} more
                </span>
              )}
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center gap-2 pt-4 border-t">
          {!isActive && (
            <button
              onClick={handleActivate}
              className="flex-1 px-3 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm font-medium"
            >
              Activate
            </button>
          )}
          
          <button
            onClick={() => onEdit(masterApp)}
            className="flex-1 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
          >
            Edit
          </button>
          
          <button
            onClick={() => onDelete(masterApp)}
            className="px-3 py-2 bg-red-50 text-red-600 rounded-lg hover:bg-red-100 transition-colors text-sm font-medium"
            title="Delete"
          >
            🗑️
          </button>
        </div>
      </div>
    </Card>
  );
};

export default MasterAppCard;

