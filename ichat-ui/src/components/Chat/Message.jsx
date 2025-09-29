import React from 'react';

const Message = ({ message }) => {
  const isUser = message.sender === 'user';
  const isAssistant = message.sender === 'assistant';

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatMessage = (text) => {
    // Handle code blocks
    const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g;
    const inlineCodeRegex = /`([^`]+)`/g;
    
    let formattedText = text;
    
    // Replace code blocks
    formattedText = formattedText.replace(codeBlockRegex, (match, language, code) => {
      return `<div class="bg-gray-800 text-gray-100 p-4 rounded-lg my-2 overflow-x-auto">
        <div class="text-xs text-gray-400 mb-2">${language || 'code'}</div>
        <pre><code>${code.trim()}</code></pre>
      </div>`;
    });
    
    // Replace inline code
    formattedText = formattedText.replace(inlineCodeRegex, '<code class="bg-gray-100 text-gray-800 px-1 py-0.5 rounded text-sm">$1</code>');
    
    return formattedText;
  };

  if (isUser) {
    return (
      <div className="w-full bg-white border-b border-gray-100">
        <div className="max-w-4xl mx-auto px-4 py-6">
          <div className="flex gap-4">
            <div className="w-8 h-8 rounded-full bg-gradient-to-r from-blue-500 to-blue-600 flex items-center justify-center flex-shrink-0">
              <span className="text-white text-xs">👤</span>
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-gray-800 text-base leading-relaxed whitespace-pre-wrap">
                {message.text}
              </div>
              <div className="text-xs text-gray-500 mt-2">
                {formatTime(message.timestamp)}
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (isAssistant) {
    return (
      <div className="w-full bg-white border-b border-gray-100">
        <div className="max-w-4xl mx-auto px-4 py-6">
          <div className="flex gap-4">
            <div className="w-8 h-8 rounded-full bg-gradient-to-r from-green-500 to-emerald-600 flex items-center justify-center flex-shrink-0">
              <span className="text-white text-xs">🤖</span>
            </div>
            <div className="flex-1 min-w-0">
              <div 
                className="text-gray-800 text-base leading-relaxed whitespace-pre-wrap"
                dangerouslySetInnerHTML={{ __html: formatMessage(message.text) }}
              />
              <div className="text-xs text-gray-500 mt-2">
                {formatTime(message.timestamp)}
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return null;
};

export default Message;
