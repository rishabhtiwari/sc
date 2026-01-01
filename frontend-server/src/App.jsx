import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout/Layout';
import Login from './components/Auth/Login';
import LoginPage from './pages/LoginPage';
import CustomerRegistrationPage from './pages/CustomerRegistrationPage';
import Dashboard from './pages/Dashboard';
import NewsFetcherPage from './pages/NewsFetcherPage';
import ImageProcessingPage from './pages/ImageProcessingPage';
import AudioProcessingPage from './pages/AudioProcessingPage';
import YouTubePage from './pages/YouTubePage';
import Workflow from './pages/Workflow';
import Monitoring from './pages/Monitoring';
import SettingsPage from './pages/SettingsPage';
import TemplateManagementPage from './pages/TemplateManagementPage';
import PromptTemplateManagementPage from './pages/PromptTemplateManagementPage';
import ProductVideoPage from './pages/ProductVideoPage';
import EcommercePage from './pages/EcommercePage';
import AudioStudioPage from './pages/AudioStudioPage';
import AudioLibraryPage from './pages/AudioLibraryPage';
import VoicePreviewPage from './pages/VoicePreviewPage';
import { isAuthenticated as checkAuth, verifyToken } from './services/authService';
import api from './services/api';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Check authentication on mount
  useEffect(() => {
    const checkAuthStatus = async () => {
      const token = localStorage.getItem('auth_token');
      const storedUser = localStorage.getItem('user_info');

      if (token && storedUser) {
        try {
          // Verify token with server
          const response = await verifyToken();

          if (response.valid) {
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

    checkAuthStatus();
  }, []);

  const handleLoginSuccess = (userData) => {
    setIsAuthenticated(true);
    setUser(userData);
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
    setUser(null);
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_info');
  };

  // Show loading spinner while checking auth
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: '#e8f0f7' }}>
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
              <LoginPage />
            )
          }
        />

        {/* Registration Route - accessible without authentication */}
        <Route
          path="/register"
          element={
            isAuthenticated ? (
              <Navigate to="/" replace />
            ) : (
              <CustomerRegistrationPage />
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
                  <Route path="/dashboard" element={<Dashboard />} />
                  <Route path="/news-fetcher" element={<NewsFetcherPage />} />
                  <Route path="/image-processing" element={<ImageProcessingPage />} />
                  <Route path="/voice-llm" element={<AudioProcessingPage />} />
                  <Route path="/audio-studio" element={<AudioStudioPage />} />
                  <Route path="/audio-studio/library" element={<AudioLibraryPage />} />
                  <Route path="/audio-studio/voice-preview" element={<VoicePreviewPage />} />
                  <Route path="/youtube" element={<YouTubePage />} />
                  <Route path="/ecommerce" element={<EcommercePage />} />
                  <Route path="/workflow" element={<Workflow />} />
                  <Route path="/monitoring" element={<Monitoring />} />
                  <Route path="/templates/video" element={<TemplateManagementPage />} />
                  <Route path="/templates/prompt" element={<PromptTemplateManagementPage />} />
                  {/* Legacy routes for backward compatibility */}
                  <Route path="/templates" element={<Navigate to="/templates/video" replace />} />
                  <Route path="/prompt-templates" element={<Navigate to="/templates/prompt" replace />} />
                  <Route path="/settings" element={<SettingsPage />} />
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

