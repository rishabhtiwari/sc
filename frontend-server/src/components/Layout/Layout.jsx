import React, { useState, useEffect, useRef } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';

const Layout = ({ children, user, onLogout }) => {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [expandedMenus, setExpandedMenus] = useState({ ecommerce: true }); // Track expanded menus
  const location = useLocation();
  const navigate = useNavigate();
  const userMenuRef = useRef(null);

  // Auto-collapse sidebar when navigating to Design Editor
  useEffect(() => {
    if (location.pathname === '/design-editor') {
      setSidebarOpen(false);
    }
  }, [location.pathname]);

  const navItems = [
    { path: '/', icon: '📊', label: 'Dashboard' },
    { path: '/news-fetcher', icon: '📰', label: 'News Fetcher' },
    { path: '/image-processing', icon: '🖼️', label: 'Image Processing' },
    { path: '/voice-llm', icon: '🎤', label: 'Audio Processing' },
    { path: '/audio-studio', icon: '🎙️', label: 'Audio Studio' },
    { path: '/text-studio', icon: '📝', label: 'Text Studio' },
    { path: '/design-editor', icon: '🎨', label: 'Design Editor' },
    { path: '/youtube', icon: '📺', label: 'Video Processing' },
    { path: '/ecommerce', icon: '🛒', label: 'E-commerce' },
    {
      id: 'templates',
      icon: '📋',
      label: 'Templates',
      subItems: [
        { path: '/templates/prompt', icon: '📝', label: 'Prompt Templates' },
        { path: '/templates/video', icon: '🎬', label: 'Video Templates' },
      ]
    },
    { path: '/workflow', icon: '🔄', label: 'Workflow Pipeline' },
    { path: '/monitoring', icon: '📈', label: 'Monitoring & Logs' },
    { path: '/settings', icon: '⚙️', label: 'Settings' },
  ];

  const toggleMenu = (menuId) => {
    setExpandedMenus(prev => ({
      ...prev,
      [menuId]: !prev[menuId]
    }));
  };

  // Close user menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target)) {
        setShowUserMenu(false);
      }
    };

    if (showUserMenu) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showUserMenu]);

  const isActive = (path) => {
    if (path === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  };

  const isMenuActive = (item) => {
    if (item.path) {
      return isActive(item.path);
    }
    if (item.subItems) {
      return item.subItems.some(subItem => isActive(subItem.path));
    }
    return false;
  };

  return (
    <div className="flex h-screen" style={{ backgroundColor: '#e8f0f7' }}>
      {/* Sidebar - Rubrik Style */}
      <aside
        className={`${
          sidebarOpen ? 'w-72' : 'w-20'
        } border-r border-neutral-200 transition-all duration-300 flex flex-col shadow-sm`}
        style={{ backgroundColor: '#f8fafc' }}
      >
        {/* Logo/Header */}
        <div className="h-16 px-4 flex items-center justify-between border-b border-neutral-200">
          {sidebarOpen && (
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-600 to-blue-700 rounded-lg flex items-center justify-center">
                <span className="text-white text-lg font-bold">N</span>
              </div>
              <div>
                <h1 className="text-base font-bold text-neutral-900">News Automation</h1>
                <p className="text-xs text-neutral-500">Platform</p>
              </div>
            </div>
          )}
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-2 rounded-lg hover:bg-neutral-100 text-neutral-600 transition-colors"
            title={sidebarOpen ? 'Collapse sidebar' : 'Expand sidebar'}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              {sidebarOpen ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" />
              )}
            </svg>
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {navItems.map((item, index) => {
            // Handle menu items with sub-items
            if (item.subItems) {
              const isExpanded = expandedMenus[item.id];
              const hasActiveSubItem = isMenuActive(item);

              return (
                <div key={item.id || index}>
                  <button
                    onClick={() => toggleMenu(item.id)}
                    className={`
                      w-full group flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all
                      ${hasActiveSubItem
                        ? 'bg-blue-50 text-blue-700 font-medium'
                        : 'text-neutral-700 hover:bg-neutral-100 hover:text-neutral-900'
                      }
                    `}
                    title={!sidebarOpen ? item.label : ''}
                  >
                    <span className={`text-xl ${hasActiveSubItem ? 'scale-110' : 'group-hover:scale-110'} transition-transform`}>
                      {item.icon}
                    </span>
                    {sidebarOpen && (
                      <>
                        <div className="flex-1 min-w-0 text-left">
                          <span className="block text-sm truncate">{item.label}</span>
                        </div>
                        <svg
                          className={`w-4 h-4 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                      </>
                    )}
                  </button>

                  {/* Sub-items */}
                  {sidebarOpen && isExpanded && (
                    <div className="ml-6 mt-1 space-y-1">
                      {item.subItems.map((subItem) => {
                        const subActive = isActive(subItem.path);
                        return (
                          <Link
                            key={subItem.path}
                            to={subItem.path}
                            className={`
                              group flex items-center gap-3 px-3 py-2 rounded-lg transition-all text-sm
                              ${subActive
                                ? 'bg-blue-50 text-blue-700 font-medium'
                                : 'text-neutral-600 hover:bg-neutral-100 hover:text-neutral-900'
                              }
                            `}
                          >
                            <span className="text-base">{subItem.icon}</span>
                            <span className="truncate">{subItem.label}</span>
                            {subActive && (
                              <div className="w-1.5 h-1.5 bg-blue-600 rounded-full ml-auto"></div>
                            )}
                          </Link>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            }

            // Handle regular menu items
            const active = isActive(item.path);
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`
                  group flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all
                  ${active
                    ? 'bg-blue-50 text-blue-700 font-medium'
                    : 'text-neutral-700 hover:bg-neutral-100 hover:text-neutral-900'
                  }
                `}
                title={!sidebarOpen ? item.label : ''}
              >
                <span className={`text-xl ${active ? 'scale-110' : 'group-hover:scale-110'} transition-transform`}>
                  {item.icon}
                </span>
                {sidebarOpen && (
                  <div className="flex-1 min-w-0">
                    <span className="block text-sm truncate">{item.label}</span>
                  </div>
                )}
                {sidebarOpen && active && (
                  <div className="w-1.5 h-1.5 bg-blue-600 rounded-full"></div>
                )}
              </Link>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-neutral-200">
          {sidebarOpen ? (
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-xs text-neutral-500">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <span>All systems operational</span>
              </div>
              <div className="text-xs text-neutral-400">
                <p>Version 1.0.0</p>
                <p className="mt-0.5">© 2024 News Automation</p>
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-2">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <div className="text-center text-xs text-neutral-400">v1.0</div>
            </div>
          )}
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto" style={{ backgroundColor: '#e8f0f7' }}>
        {/* Top Bar - Rubrik Style */}
        <header className="border-b border-neutral-200 sticky top-0 z-10 backdrop-blur-sm" style={{ backgroundColor: 'rgba(248, 250, 252, 0.95)' }}>
          <div className="px-6 py-3.5 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div>
                <h2 className="text-lg font-semibold text-neutral-900">
                  {navItems.find((item) => isActive(item.path))?.label || 'Dashboard'}
                </h2>
                <p className="text-xs text-neutral-500 mt-0.5">
                  Manage your news automation workflow
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              {/* Health Status Indicator */}
              <div className="flex items-center gap-2 px-3 py-1.5 bg-green-50 border border-green-200 rounded-lg">
                <div className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-xs text-green-700 font-medium">Online</span>
              </div>

              {/* Notifications */}
              <button className="p-2 rounded-lg hover:bg-neutral-100 text-neutral-600 transition-colors relative">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                </svg>
                <span className="absolute top-1 right-1 w-2 h-2 bg-blue-600 rounded-full"></span>
              </button>

              {/* User Menu */}
              {user && (
                <div className="relative" ref={userMenuRef}>
                  <button
                    onClick={() => setShowUserMenu(!showUserMenu)}
                    className="flex items-center gap-2.5 px-3 py-1.5 bg-neutral-50 hover:bg-neutral-100 border border-neutral-200 rounded-lg transition-colors"
                  >
                    <div className="w-7 h-7 bg-gradient-to-br from-blue-600 to-blue-700 rounded-full flex items-center justify-center text-white text-sm font-semibold">
                      {user.first_name?.charAt(0).toUpperCase() || user.email?.charAt(0).toUpperCase() || 'U'}
                    </div>
                    <div className="text-left">
                      <p className="text-xs font-semibold text-neutral-900">
                        {user.first_name && user.last_name ? `${user.first_name} ${user.last_name}` : user.email}
                      </p>
                      <p className="text-xs text-neutral-500">{user.customer_name || 'Customer'}</p>
                    </div>
                    <svg
                      className={`w-4 h-4 text-neutral-500 transition-transform ${showUserMenu ? 'rotate-180' : ''}`}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>

                  {/* Dropdown Menu - Rubrik Style */}
                  {showUserMenu && (
                    <div className="absolute right-0 mt-2 w-72 bg-white rounded-xl shadow-xl border border-neutral-200 overflow-hidden z-50">
                      <div className="px-4 py-3 bg-gradient-to-r from-blue-50 to-blue-100 border-b border-blue-200">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-blue-700 rounded-full flex items-center justify-center text-white text-base font-bold">
                            {user.first_name?.charAt(0).toUpperCase() || user.email?.charAt(0).toUpperCase() || 'U'}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-semibold text-neutral-900 truncate">
                              {user.first_name && user.last_name ? `${user.first_name} ${user.last_name}` : 'User'}
                            </p>
                            <p className="text-xs text-neutral-600 truncate">{user.email}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2 mt-2.5">
                          <span className="inline-flex items-center px-2 py-1 text-xs font-medium rounded-md bg-blue-600 text-white">
                            {user.role_name || 'User'}
                          </span>
                          {user.customer_name && (
                            <span className="inline-flex items-center px-2 py-1 text-xs font-medium rounded-md bg-white text-neutral-700 border border-neutral-300">
                              {user.customer_name}
                            </span>
                          )}
                        </div>
                      </div>

                      <div className="py-1">
                        <Link
                          to="/settings"
                          onClick={() => setShowUserMenu(false)}
                          className="w-full text-left px-4 py-2.5 text-sm text-neutral-700 hover:bg-neutral-50 transition-colors flex items-center gap-3 group"
                        >
                          <svg className="w-4 h-4 text-neutral-500 group-hover:text-blue-600 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                          </svg>
                          <span className="group-hover:text-neutral-900">Settings</span>
                        </Link>

                        <div className="my-1 border-t border-neutral-200"></div>

                        <button
                          onClick={() => {
                            setShowUserMenu(false);
                            onLogout();
                            navigate('/login');
                          }}
                          className="w-full text-left px-4 py-2.5 text-sm text-red-600 hover:bg-red-50 transition-colors flex items-center gap-3 group"
                        >
                          <svg className="w-4 h-4 group-hover:text-red-700 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                          </svg>
                          <span className="group-hover:text-red-700">Logout</span>
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </header>

        {/* Page Content */}
        <div className="p-6">
          {/* Debug indicator - remove after confirming */}
          <div style={{
            position: 'fixed',
            bottom: '10px',
            right: '10px',
            backgroundColor: '#f0f4f8',
            border: '2px solid #2563eb',
            padding: '8px 12px',
            borderRadius: '8px',
            fontSize: '11px',
            fontWeight: 'bold',
            color: '#2563eb',
            zIndex: 9999,
            boxShadow: '0 2px 8px rgba(0,0,0,0.15)'
          }}>
            ✓ Blue BG Active
          </div>
          {children}
        </div>
      </main>
    </div>
  );
};

export default Layout;

