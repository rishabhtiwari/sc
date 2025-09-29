import React from 'react';

const TypingIndicator = () => {
  return (
    <div className="w-full bg-white border-b border-gray-100">
      <div className="max-w-4xl mx-auto px-4 py-6">
        <div className="flex gap-4">
          <div className="w-8 h-8 rounded-full bg-gradient-to-r from-green-500 to-emerald-600 flex items-center justify-center flex-shrink-0">
            <i className="fas fa-robot text-white text-xs"></i>
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <div className="flex gap-1">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
              </div>
              <span className="text-sm text-gray-500">Assistant is typing...</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TypingIndicator;
