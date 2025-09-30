import React, { useState } from 'react';

const ChatInput = ({ onSend, onStop, disabled = false, canStop = false, isTyping = false }) => {
  const [input, setInput] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim() && !disabled && !isTyping) {
      onSend(input.trim());
      setInput('');
    }
  };

  const handleStop = (e) => {
    e.preventDefault();
    if (onStop && canStop) {
      onStop();
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!isTyping) {
        handleSubmit(e);
      }
    }
  };

  return (
    <div className="space-y-2">
      <form onSubmit={handleSubmit} className="flex gap-2">
        <div className="flex-1 relative">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={
              disabled
                ? "Connecting to server..."
                : isTyping
                  ? "Assistant is responding..."
                  : "Type your message..."
            }
            disabled={disabled || isTyping}
            className={`w-full p-3 ${canStop && isTyping ? 'pr-20' : 'pr-12'} rounded-xl border resize-none transition-colors ${
              disabled || isTyping
                ? 'bg-gray-100 border-gray-300 text-gray-400 cursor-not-allowed'
                : 'bg-white border-gray-300 text-gray-800 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100'
            }`}
            rows="1"
            style={{ minHeight: '48px', maxHeight: '120px' }}
          />

          {/* Stop button - appears next to send button when streaming */}
          {canStop && isTyping && (
            <button
              type="button"
              onClick={handleStop}
              className="absolute right-12 top-1/2 transform -translate-y-1/2 p-2 rounded-lg bg-red-500 hover:bg-red-600 text-white transition-colors"
              title="Stop generating"
            >
              <div className="w-3 h-3 bg-white rounded-sm"></div>
            </button>
          )}

          {/* Send button */}
          <button
            type="submit"
            disabled={!input.trim() || disabled || isTyping}
            className={`absolute right-2 top-1/2 transform -translate-y-1/2 p-2 rounded-lg transition-colors ${
              !input.trim() || disabled || isTyping
                ? 'text-gray-400 cursor-not-allowed'
                : 'text-blue-500 hover:bg-blue-50 hover:text-blue-600'
            }`}
          >
            <i className="fas fa-paper-plane"></i>
          </button>
        </div>
      </form>
    </div>
  );
};

export default ChatInput;
