import React, { useState, useEffect } from 'react';
import apiService from '../../services/apiService';

// Helper function to get provider icon
const getProviderIcon = (providerId) => {
  const iconMap = {
    'github': 'fab fa-github',
    'database': 'fas fa-database',
    'document_upload': 'fas fa-file-upload',
    'gitlab': 'fab fa-gitlab',
    'filesystem': 'fas fa-folder-open'
  };
  return iconMap[providerId] || 'fas fa-plug';
};

// Helper function to get provider color theme
const getProviderColor = (providerId) => {
  const colorMap = {
    'github': 'text-gray-800',
    'database': 'text-blue-600',
    'document_upload': 'text-green-600',
    'gitlab': 'text-orange-600',
    'filesystem': 'text-purple-600'
  };
  return colorMap[providerId] || 'text-gray-600';
};

const MCPContent = () => {
  const [providers, setProviders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedProvider, setSelectedProvider] = useState(null);
  const [connectionConfig, setConnectionConfig] = useState({});
  const [error, setError] = useState(null);

  useEffect(() => {
    console.log('MCPContent mounted, loading providers...');
    loadProviders();
  }, []);

  // Initialize connectionConfig with default values when provider is selected
  useEffect(() => {
    if (selectedProvider && selectedProvider.config_fields) {
      const defaultConfig = {};
      selectedProvider.config_fields.forEach(field => {
        if (field.default) {
          defaultConfig[field.name] = field.default;
        }
      });
      console.log('🔧 Initializing connection config with defaults:', defaultConfig);
      setConnectionConfig(defaultConfig);
    }
  }, [selectedProvider]);

  const loadProviders = async () => {
    try {
      setLoading(true);
      setError(null);
      console.log('Calling getMCPProviders and getMCPTokens...');

      // Load both providers and tokens to determine connection status
      const [providersResponse, tokensResponse] = await Promise.all([
        apiService.getMCPProviders(),
        apiService.getMCPTokens().catch(err => {
          console.warn('Failed to load tokens:', err);
          return { tokens: [] };
        })
      ]);

      console.log('MCP providers response:', providersResponse);
      console.log('MCP tokens response:', tokensResponse);

      // Get list of connected providers from tokens
      const connectedProviders = new Set();
      if (tokensResponse && tokensResponse.tokens) {
        tokensResponse.tokens.forEach(token => {
          if (!token.is_expired) {
            connectedProviders.add(token.provider);
          }
        });
      }
      console.log('Connected providers from tokens:', Array.from(connectedProviders));

      // Handle both array and object response formats
      if (providersResponse && providersResponse.providers) {
        if (Array.isArray(providersResponse.providers)) {
          // Legacy array format
          const providersArray = providersResponse.providers.map(provider => ({
            ...provider,
            connected: connectedProviders.has(provider.id)
          }));
          setProviders(providersArray);
        } else if (typeof providersResponse.providers === 'object') {
          // New object format - convert to array with provider IDs
          const providersArray = Object.keys(providersResponse.providers).map(providerId => ({
            id: providerId,
            ...providersResponse.providers[providerId],
            connected: connectedProviders.has(providerId)
          }));
          console.log('Converted providers to array:', providersArray);
          setProviders(providersArray);
        } else {
          console.warn('MCP providers response format not recognized:', providersResponse);
          setProviders([]);
        }
      } else if (Array.isArray(providersResponse)) {
        // Direct array response
        const providersArray = providersResponse.map(provider => ({
          ...provider,
          connected: connectedProviders.has(provider.id)
        }));
        setProviders(providersArray);
      } else {
        console.warn('MCP providers response is not valid:', providersResponse);
        setProviders([]);
      }
    } catch (error) {
      console.error('Failed to load MCP providers:', error);
      setError(error.message || 'Failed to load MCP providers');
      setProviders([]); // Ensure providers is always an array
    } finally {
      setLoading(false);
    }
  };

  const handleConnect = async (providerId) => {
    try {
      console.log('🔌 handleConnect called for provider:', providerId);
      if (providerId === 'github') {
        console.log('🐙 Detected GitHub provider, starting OAuth flow...');
        // GitHub requires OAuth flow
        await handleGitHubConnect();
      } else {
        console.log('🔗 Using direct connection for provider:', providerId);
        // Direct connection for other providers
        const response = await apiService.connectMCPProvider(providerId, connectionConfig);
        if (response.status === 'success') {
          await loadProviders(); // Refresh the list
          setSelectedProvider(null);
          setConnectionConfig({});
        }
      }
    } catch (error) {
      console.error('💥 Failed to connect provider:', error);
    }
  };

  const handleGitHubConnect = async () => {
    try {
      console.log('🔄 Starting GitHub OAuth flow...');
      console.log('📝 Connection config:', connectionConfig);

      // First configure OAuth settings
      console.log('⚙️ Configuring GitHub provider...');
      const configResponse = await apiService.configureMCPProvider('github', connectionConfig);
      console.log('✅ Config response:', configResponse);

      if (configResponse.status === 'success') {
        // Then start OAuth flow
        console.log('🚀 Starting OAuth authentication...');
        const authResponse = await apiService.startMCPProviderAuth('github', {
          config_id: configResponse.config_id
        });
        console.log('🔐 Auth response:', authResponse);

        if (authResponse.status === 'success' && authResponse.auth_url) {
          console.log('🌐 Opening OAuth URL:', authResponse.auth_url);
          // Open OAuth URL in new window
          window.open(authResponse.auth_url, 'github-oauth', 'width=600,height=700');

          // Listen for OAuth completion
          console.log('👂 Starting to listen for OAuth completion...');
          const checkAuth = setInterval(async () => {
            try {
              const tokensResponse = await apiService.getMCPTokens();
              const githubToken = tokensResponse.tokens?.find(token => token.provider === 'github');
              if (githubToken) {
                console.log('🎉 GitHub token found! OAuth completed successfully');
                clearInterval(checkAuth);
                await loadProviders(); // Refresh the list
                setSelectedProvider(null);
                setConnectionConfig({});
                alert('GitHub connected successfully!');
              }
            } catch (error) {
              console.log('⏳ Still waiting for OAuth completion...');
            }
          }, 2000);

          // Stop checking after 5 minutes
          setTimeout(() => {
            console.log('⏰ OAuth timeout reached, stopping check');
            clearInterval(checkAuth);
          }, 300000);
        } else {
          console.error('❌ Auth response missing auth_url:', authResponse);
          alert('Failed to get OAuth URL. Please try again.');
        }
      } else {
        console.error('❌ Config response failed:', configResponse);
        alert('Failed to configure GitHub provider. Please check your settings.');
      }
    } catch (error) {
      console.error('💥 Failed to connect GitHub:', error);
      alert('Failed to connect GitHub. Please check your configuration.');
    }
  };

  const handleDisconnect = async (providerId) => {
    try {
      if (providerId === 'github') {
        // For GitHub, revoke the OAuth token
        const tokensResponse = await apiService.getMCPTokens();
        const githubToken = tokensResponse.tokens?.find(token => token.provider === 'github');
        if (githubToken) {
          await apiService.revokeMCPToken(githubToken.token_id);
        }
      } else {
        // For other providers, use the standard disconnect
        await apiService.disconnectMCPProvider(providerId);
      }
      await loadProviders(); // Refresh the list
    } catch (error) {
      console.error('Failed to disconnect provider:', error);
      alert('Failed to disconnect provider. Please try again.');
    }
  };

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-500">Loading MCP providers...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-500 text-4xl mb-4">⚠️</div>
          <h3 className="text-lg font-medium text-gray-800 mb-2">Error Loading MCP Providers</h3>
          <p className="text-gray-500 mb-4">{error}</p>
          <button
            onClick={loadProviders}
            className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 p-6 bg-gray-50">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-full bg-gradient-to-r from-purple-500 to-pink-600 flex items-center justify-center">
              <i className="fas fa-plug text-white"></i>
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-800">MCP Connection</h2>
              <p className="text-gray-600">Model Context Protocol providers</p>
            </div>
          </div>

          {!Array.isArray(providers) || providers.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-4xl text-gray-300 mb-4">🔌</div>
              <h3 className="text-lg font-medium text-gray-800 mb-2">No MCP Providers Available</h3>
              <p className="text-gray-500">MCP providers will appear here when configured.</p>
            </div>
          ) : (
            <div className="grid gap-4">
              {providers.map((provider) => (
                <div key={provider.id} className="border border-gray-200 rounded-lg p-4 hover:border-gray-300 transition-colors">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <i className={`${getProviderIcon(provider.id)} text-2xl ${getProviderColor(provider.id)}`}></i>
                      <div>
                        <h3 className="font-medium text-gray-800">{provider.name}</h3>
                        <p className="text-sm text-gray-500">{provider.description}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        provider.connected 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        {provider.connected ? 'Connected' : 'Disconnected'}
                      </span>
                      {provider.connected ? (
                        <button
                          onClick={() => handleDisconnect(provider.id)}
                          className="px-3 py-1 bg-red-500 text-white rounded-md hover:bg-red-600 transition-colors"
                        >
                          Disconnect
                        </button>
                      ) : (
                        <button
                          onClick={() => setSelectedProvider(provider)}
                          className="px-3 py-1 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors"
                        >
                          Connect
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Configuration Modal */}
          {selectedProvider && (
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
              <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
                <div className="flex items-center gap-3 mb-4">
                  <i className={`${getProviderIcon(selectedProvider.id)} text-2xl ${getProviderColor(selectedProvider.id)}`}></i>
                  <h3 className="text-lg font-semibold text-gray-800">Connect {selectedProvider.name}</h3>
                </div>

                <div className="space-y-4">
                  {selectedProvider.config_fields?.map((field) => (
                    <div key={field.name}>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        {field.label}
                        {field.required && <span className="text-red-500 ml-1">*</span>}
                      </label>
                      {field.type === 'select' ? (
                        <select
                          value={connectionConfig[field.name] || field.default || ''}
                          onChange={(e) => setConnectionConfig({
                            ...connectionConfig,
                            [field.name]: e.target.value
                          })}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                          <option value="">Select {field.label}</option>
                          {field.options?.map((option) => (
                            <option key={option} value={option}>{option}</option>
                          ))}
                        </select>
                      ) : field.type === 'checkbox' ? (
                        <label className="flex items-center">
                          <input
                            type="checkbox"
                            checked={connectionConfig[field.name] === 'true' || connectionConfig[field.name] === true}
                            onChange={(e) => setConnectionConfig({
                              ...connectionConfig,
                              [field.name]: e.target.checked
                            })}
                            className="mr-2"
                          />
                          {field.description}
                        </label>
                      ) : (
                        <input
                          type={field.type === 'password' ? 'password' : field.type === 'number' ? 'number' : 'text'}
                          value={connectionConfig[field.name] || field.default || ''}
                          onChange={(e) => setConnectionConfig({
                            ...connectionConfig,
                            [field.name]: e.target.value
                          })}
                          placeholder={field.description}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      )}
                    </div>
                  ))}
                </div>

                <div className="flex gap-3 mt-6">
                  <button
                    onClick={() => {
                      setSelectedProvider(null);
                      setConnectionConfig({});
                    }}
                    className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={() => handleConnect(selectedProvider.id)}
                    className="flex-1 px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors"
                  >
                    {selectedProvider.id === 'github' ? 'Connect with OAuth' : 'Connect'}
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MCPContent;
