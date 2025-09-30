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

  const formatMessage = (text, isStreaming = false) => {
    // Handle code blocks - both complete and partial (for streaming)
    const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g;
    const inlineCodeRegex = /`([^`]+)`/g;
    const partialCodeBlockRegex = /```(\w+)?\n([\s\S]*)$/; // For streaming partial blocks

    let formattedText = text;

    // Replace complete code blocks first
    formattedText = formattedText.replace(codeBlockRegex, (match, language, code) => {
      return `<div class="bg-gray-800 text-gray-100 p-4 rounded-lg my-2 overflow-x-auto">
        <div class="text-xs text-gray-400 mb-2">${language || 'code'}</div>
        <pre><code>${code.trim()}</code></pre>
      </div>`;
    });

    // Handle partial code blocks during streaming
    if (isStreaming) {
      formattedText = formattedText.replace(partialCodeBlockRegex, (match, language, code) => {
        return `<div class="bg-gray-800 text-gray-100 p-4 rounded-lg my-2 overflow-x-auto">
          <div class="text-xs text-gray-400 mb-2">${language || 'code'}</div>
          <pre><code>${code}</code></pre>
        </div>`;
      });
    }

    // Replace inline code (only if not inside a code block)
    if (!formattedText.includes('<div class="bg-gray-800')) {
      formattedText = formattedText.replace(inlineCodeRegex, '<code class="bg-gray-100 text-gray-800 px-1 py-0.5 rounded text-sm">$1</code>');
    }

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
              <div className="text-gray-800 text-base leading-relaxed whitespace-pre-wrap">
                <span
                  dangerouslySetInnerHTML={{ __html: formatMessage(message.text, message.isStreaming) }}
                />
                {message.isStreaming && (
                  <span className="inline-block w-2 h-5 bg-gray-400 ml-1 animate-pulse"></span>
                )}
              </div>
              <div className="text-xs text-gray-500 mt-2 flex items-center gap-2">
                {formatTime(message.timestamp)}
                {message.isStreaming && (
                  <span className="text-blue-500 text-xs flex items-center gap-1">
                    <div className="flex gap-1">
                      <div className="w-1 h-1 bg-blue-500 rounded-full animate-bounce"></div>
                      <div className="w-1 h-1 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-1 h-1 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                    Assistant is typing...
                  </span>
                )}
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
