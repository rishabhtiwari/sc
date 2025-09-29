import React from 'react';

const ChatHeader = ({ connectionStatus }) => {
  const getStatusColor = () => {
    switch (connectionStatus) {
      case 'connected': return 'text-green-400';
      case 'disconnected': return 'text-red-400';
      case 'checking': return 'text-yellow-400';
      default: return 'text-gray-500';
    }
  };

  const getStatusText = () => {
    switch (connectionStatus) {
      case 'connected': return 'Connected to API';
      case 'disconnected': return 'API Disconnected';
      case 'checking': return 'Checking connection...';
      default: return 'Unknown status';
    }
  };

  const getStatusIcon = () => {
    switch (connectionStatus) {
      case 'connected': return 'fa-circle';
      case 'disconnected': return 'fa-times-circle';
      case 'checking': return 'fa-clock';
      default: return 'fa-question-circle';
    }
  };

  return (
    <div className="bg-white border-b border-gray-200 shadow-sm">
      <div className="max-w-4xl mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-full bg-gradient-to-r from-blue-500 to-purple-600 flex items-center justify-center">
              <i className="fas fa-robot text-white text-lg"></i>
            </div>
            <div>
              <h1 className="text-xl font-semibold text-gray-800">iChat Assistant</h1>
              <p className="text-sm text-gray-500">Your AI-powered chat companion</p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <i className={`fas ${getStatusIcon()} ${getStatusColor()}`}></i>
            <span className={`text-sm font-medium ${getStatusColor()}`}>
              {getStatusText()}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatHeader;
