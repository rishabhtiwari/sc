import React from 'react';

/**
 * Upload Progress Component - Display upload progress with logs
 */
const UploadProgress = ({ progress, logs, visible }) => {
  if (!visible) return null;

  return (
    <div className="mt-6 space-y-4">
      {/* Progress Bar */}
      <div className="relative">
        <div className="w-full h-8 bg-gray-200 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-green-500 to-green-400 transition-all duration-300 flex items-center justify-center text-white font-bold text-sm"
            style={{ width: `${progress}%` }}
          >
            {progress}%
          </div>
        </div>
      </div>

      {/* Upload Logs */}
      {logs && logs.length > 0 && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 max-h-80 overflow-y-auto">
          <div className="space-y-1 font-mono text-xs">
            {logs.map((log, index) => (
              <div
                key={index}
                className={`p-2 rounded ${
                  log.type === 'success'
                    ? 'text-green-700 bg-green-50'
                    : log.type === 'error'
                    ? 'text-red-700 bg-red-50'
                    : 'text-blue-700 bg-blue-50'
                }`}
              >
                {log.message}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default UploadProgress;

