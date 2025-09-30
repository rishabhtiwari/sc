import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar/Sidebar';
import ChatContent from './components/Chat/ChatContent';
import MCPContent from './components/MCP/MCPContent';
import ContextContent from './components/Context/ContextContent';
import { useChat } from './hooks/useChat';

const App = () => {
  const {
    messages,
    isTyping,
    connectionStatus,
    handleSend,
    stopStream,
    checkConnection,
    canStop
  } = useChat();

  const [activeSection, setActiveSection] = useState('chat');

  useEffect(() => {
    checkConnection();
    const interval = setInterval(checkConnection, 30000);
    return () => clearInterval(interval);
  }, [checkConnection]);

  const renderContent = () => {
    switch (activeSection) {
      case 'chat':
        return (
          <ChatContent
            messages={messages}
            isTyping={isTyping}
            onSend={handleSend}
            onStop={stopStream}
            connectionStatus={connectionStatus}
            canStop={canStop}
          />
        );
      case 'mcp':
        return <MCPContent />;
      case 'context':
        return <ContextContent />;
      default:
        return (
          <ChatContent
            messages={messages}
            isTyping={isTyping}
            onSend={handleSend}
            onStop={stopStream}
            connectionStatus={connectionStatus}
            canStop={canStop}
          />
        );
    }
  };

  return (
    <div className="h-screen bg-gray-50 text-gray-800 flex overflow-hidden">
      <Sidebar
        activeSection={activeSection}
        setActiveSection={setActiveSection}
      />
      {renderContent()}
    </div>
  );
};

export default App;
