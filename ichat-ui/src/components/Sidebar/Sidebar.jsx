import React, { useState } from 'react';

const Sidebar = ({ activeSection, setActiveSection }) => {
  const [isOpen, setIsOpen] = useState(true);

  const menuItems = [
    {
      id: 'chat',
      name: 'Chat',
      icon: 'fas fa-comments',
      description: 'AI Chat Assistant'
    },
    {
      id: 'mcp',
      name: 'MCP Connection',
      icon: 'fas fa-plug',
      description: 'Model Context Protocol'
    },
    {
      id: 'context',
      name: 'Context Setup',
      icon: 'fas fa-cog',
      description: 'Repository Context'
    }
  ];

  const toggleSidebar = () => {
    setIsOpen(!isOpen);
  };

  const handleItemClick = (itemId) => {
    setActiveSection(itemId);
  };

  return (
    <div className={`bg-white border-r border-gray-200 shadow-lg transition-all duration-300 flex flex-col h-full ${
      isOpen ? 'w-64' : 'w-16'
    }`}>
      {/* Fixed Header */}
      <div className="flex-shrink-0 p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          {isOpen && (
            <h2 className="text-lg font-semibold text-gray-800">iChat</h2>
          )}
          <button
            onClick={toggleSidebar}
            className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <i className={`fas ${isOpen ? 'fa-chevron-left' : 'fa-chevron-right'} text-gray-500`}></i>
          </button>
        </div>
      </div>

      {/* Scrollable Navigation */}
      <nav className="flex-1 p-2 overflow-y-auto">
        {menuItems.map((item) => (
          <button
            key={item.id}
            onClick={() => handleItemClick(item.id)}
            className={`w-full flex items-center gap-3 p-3 rounded-lg transition-colors mb-2 ${
              activeSection === item.id
                ? 'bg-blue-500 text-white shadow-md'
                : 'text-gray-600 hover:bg-gray-100 hover:text-gray-800'
            }`}
          >
            <i className={`${item.icon} text-lg`}></i>
            {isOpen && (
              <div className="flex-1 text-left">
                <div className="font-medium">{item.name}</div>
                <div className="text-xs opacity-75">{item.description}</div>
              </div>
            )}
          </button>
        ))}
      </nav>

      {/* Fixed Footer */}
      {isOpen && (
        <div className="flex-shrink-0 p-4 border-t border-gray-200">
          <div className="text-xs text-gray-500">
            <div>iChat Assistant v2.0</div>
            <div>Powered by AI</div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Sidebar;
