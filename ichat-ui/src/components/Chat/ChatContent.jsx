import React, { useRef, useEffect, useState } from 'react';
import ChatHeader from './ChatHeader';
import ChatInput from './ChatInput';
import Message from './Message';

const ChatContent = ({ messages, isTyping, onSend, onStop, connectionStatus, canStop }) => {
  const messagesEndRef = useRef(null);
  const messagesContainerRef = useRef(null);
  const [isUserScrolling, setIsUserScrolling] = useState(false);
  const [shouldAutoScroll, setShouldAutoScroll] = useState(true);

  const scrollToBottom = () => {
    if (shouldAutoScroll && !isUserScrolling) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const handleScroll = () => {
    if (!messagesContainerRef.current) return;

    const { scrollTop, scrollHeight, clientHeight } = messagesContainerRef.current;
    const isAtBottom = scrollHeight - scrollTop - clientHeight < 50; // 50px threshold

    setShouldAutoScroll(isAtBottom);

    // Detect if user is actively scrolling up
    if (!isAtBottom && !isUserScrolling) {
      setIsUserScrolling(true);
      // Reset user scrolling flag after a delay
      setTimeout(() => setIsUserScrolling(false), 1000);
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping, shouldAutoScroll]);

  return (
    <div className="flex-1 flex flex-col h-screen">
      {/* Fixed Header */}
      <div className="flex-shrink-0">
        <ChatHeader connectionStatus={connectionStatus} />
      </div>

      {/* Scrollable Messages Area */}
      <div
        ref={messagesContainerRef}
        className="flex-1 overflow-y-auto min-h-0"
        onScroll={handleScroll}
      >
        {messages.map((message) => (
          <Message key={message.id} message={message} />
        ))}

        <div ref={messagesEndRef} />
      </div>

      {/* Fixed Input Area */}
      <div className="flex-shrink-0 border-t border-gray-200 bg-white">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <ChatInput
            onSend={onSend}
            onStop={onStop}
            disabled={connectionStatus === 'disconnected'}
            canStop={canStop}
            isTyping={isTyping}
          />

          {/* Scroll to bottom button when user scrolled up */}
          {!shouldAutoScroll && (
            <div className="flex justify-center mt-2">
              <button
                onClick={() => {
                  setShouldAutoScroll(true);
                  setIsUserScrolling(false);
                  scrollToBottom();
                }}
                className="bg-blue-500 hover:bg-blue-600 text-white text-sm px-3 py-1 rounded-full shadow-lg transition-colors"
              >
                ↓ Scroll to bottom
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ChatContent;
