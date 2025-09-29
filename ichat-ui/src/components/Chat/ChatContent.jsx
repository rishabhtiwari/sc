import React, { useRef, useEffect } from 'react';
import ChatHeader from './ChatHeader';
import ChatInput from './ChatInput';
import Message from './Message';
import TypingIndicator from './TypingIndicator';

const ChatContent = ({ messages, isTyping, onSend, connectionStatus }) => {
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  return (
    <div className="flex-1 flex flex-col h-screen">
      {/* Fixed Header */}
      <div className="flex-shrink-0">
        <ChatHeader connectionStatus={connectionStatus} />
      </div>

      {/* Scrollable Messages Area */}
      <div className="flex-1 overflow-y-auto min-h-0">
        {messages.map((message) => (
          <Message key={message.id} message={message} />
        ))}

        {isTyping && <TypingIndicator />}

        <div ref={messagesEndRef} />
      </div>

      {/* Fixed Input Area */}
      <div className="flex-shrink-0 border-t border-gray-200 bg-white">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <ChatInput onSend={onSend} disabled={connectionStatus === 'disconnected'} />
        </div>
      </div>
    </div>
  );
};

export default ChatContent;
