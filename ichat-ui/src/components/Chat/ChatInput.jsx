import React, { useState } from 'react';

const ChatInput = ({ onSend, disabled = false }) => {
  const [input, setInput] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim() && !disabled) {
      onSend(input.trim());
      setInput('');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <div className="flex-1 relative">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder={disabled ? "Connecting to server..." : "Type your message..."}
          disabled={disabled}
          className={`w-full p-3 pr-12 rounded-xl border resize-none transition-colors ${
            disabled
              ? 'bg-gray-100 border-gray-300 text-gray-400 cursor-not-allowed'
              : 'bg-white border-gray-300 text-gray-800 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100'
          }`}
          rows="1"
          style={{ minHeight: '48px', maxHeight: '120px' }}
        />
        <button
          type="submit"
          disabled={!input.trim() || disabled}
          className={`absolute right-2 top-1/2 transform -translate-y-1/2 p-2 rounded-lg transition-colors ${
            !input.trim() || disabled
              ? 'text-gray-400 cursor-not-allowed'
              : 'text-blue-500 hover:bg-blue-50 hover:text-blue-600'
          }`}
        >
          <i className="fas fa-paper-plane"></i>
        </button>
      </div>
    </form>
  );
};

export default ChatInput;
