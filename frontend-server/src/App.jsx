import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout/Layout';
import Login from './components/Auth/Login';
import Dashboard from './pages/Dashboard';
import NewsFetcherPage from './pages/NewsFetcherPage';
import ImageCleaningPage from './pages/ImageCleaningPage';
import VoiceLLMPage from './pages/VoiceLLMPage';
import YouTubePage from './pages/YouTubePage';
import Workflow from './pages/Workflow';
import Monitoring from './pages/Monitoring';
import api from './services/api';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Check authentication on mount
  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('auth_token');
      const storedUser = localStorage.getItem('user');

      if (token && storedUser) {
        try {
          // Set authorization header
          api.defaults.headers.common['Authorization'] = `Bearer ${token}`;

          // Verify token with server
          const response = await api.get('/auth/verify');

          if (response.data.valid) {
            setIsAuthenticated(true);
            setUser(JSON.parse(storedUser));
          } else {
            // Token invalid, clear storage
            handleLogout();
          }
        } catch (error) {
          console.error('Auth verification failed:', error);
          handleLogout();
        }
      }

      setLoading(false);
    };

    checkAuth();
  }, []);

  const handleLoginSuccess = (userData) => {
    setIsAuthenticated(true);
    setUser(userData);
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
    setUser(null);
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user');
    delete api.defaults.headers.common['Authorization'];
  };

  // Show loading spinner while checking auth
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <Router>
      <Routes>
        {/* Login Route - accessible without authentication */}
        <Route
          path="/login"
          element={
            isAuthenticated ? (
              <Navigate to="/" replace />
            ) : (
              <Login onLoginSuccess={handleLoginSuccess} />
            )
          }
        />

        {/* Protected Routes - require authentication */}
        <Route
          path="/*"
          element={
            isAuthenticated ? (
              <Layout user={user} onLogout={handleLogout}>
                <Routes>
                  <Route path="/" element={<Dashboard />} />
                  <Route path="/news-fetcher" element={<NewsFetcherPage />} />
                  <Route path="/image-cleaning" element={<ImageCleaningPage />} />
                  <Route path="/voice-llm" element={<VoiceLLMPage />} />
                  <Route path="/youtube" element={<YouTubePage />} />
                  <Route path="/workflow" element={<Workflow />} />
                  <Route path="/monitoring" element={<Monitoring />} />
                </Routes>
              </Layout>
            ) : (
              <Navigate to="/login" replace />
            )
          }
        />
      </Routes>
    </Router>
  );
}

export default App;

