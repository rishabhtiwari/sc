import React, { useState, useEffect } from 'react';
import apiService from '../../services/apiService';

// Helper function to get provider icon
const getProviderIcon = (providerId) => {
  const iconMap = {
    'github': 'fab fa-github',
    'database': 'fas fa-database',
    'document_upload': 'fas fa-file-upload',
    'remote_host': 'fas fa-server',
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
    'remote_host': 'text-purple-600',
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
  const [activeTab, setActiveTab] = useState('github');
  const [githubConnections, setGithubConnections] = useState([]);
  const [remoteHostConnections, setRemoteHostConnections] = useState([]);

  useEffect(() => {
    console.log('MCPContent mounted, loading providers...');
    loadProviders();
    loadConnections();
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
      console.log('Calling getMCPProviders...');

      const providersResponse = await apiService.getMCPProviders();
      console.log('MCP providers response:', providersResponse);

      // Handle both array and object response formats
      if (providersResponse && providersResponse.providers) {
        if (Array.isArray(providersResponse.providers)) {
          // Legacy array format
          setProviders(providersResponse.providers);
        } else if (typeof providersResponse.providers === 'object') {
          // New object format - convert to array with provider IDs
          const providersArray = Object.keys(providersResponse.providers).map(providerId => ({
            id: providerId,
            ...providersResponse.providers[providerId]
          }));
          console.log('Converted providers to array:', providersArray);
          setProviders(providersArray);
        } else {
          console.warn('MCP providers response format not recognized:', providersResponse);
          setProviders([]);
        }
      } else if (Array.isArray(providersResponse)) {
        // Direct array response
        setProviders(providersResponse);
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

  const loadConnections = async () => {
    try {
      console.log('Loading existing connections...');

      // Load GitHub connections (OAuth tokens)
      const tokensResponse = await apiService.getMCPTokens().catch(err => {
        console.warn('Failed to load tokens:', err);
        return { tokens: [] };
      });

      const githubTokens = tokensResponse.tokens?.filter(token =>
        token.provider === 'github' && !token.is_expired
      ) || [];

      // For each GitHub token, get repository resources
      const githubConns = [];
      for (const token of githubTokens) {
        try {
          const resourcesResponse = await apiService.getMCPProviderResources('github', token.token_id);
          if (resourcesResponse.resources) {
            githubConns.push({
              id: token.token_id,
              name: `GitHub Account`,
              connected: true,
              repositories: resourcesResponse.resources
            });
          }
        } catch (err) {
          console.warn('Failed to load GitHub resources for token:', token.token_id, err);
        }
      }
      setGithubConnections(githubConns);

      // Load Remote Host connections (stored connections)
      try {
        const remoteHostResponse = await apiService.getRemoteHostConnections();
        console.log('Remote host connections response:', remoteHostResponse);

        if (remoteHostResponse && remoteHostResponse.connections) {
          const remoteHostConns = remoteHostResponse.connections.map(conn => ({
            id: conn.id,
            name: conn.name,
            host: conn.host,
            protocol: conn.protocol,
            connected: conn.status === 'active' // Assuming 'active' means connected
          }));
          setRemoteHostConnections(remoteHostConns);
        } else {
          setRemoteHostConnections([]);
        }
      } catch (error) {
        console.warn('Failed to load remote host connections:', error);
        setRemoteHostConnections([]);
      }

    } catch (error) {
      console.error('Failed to load connections:', error);
    }
  };

  const handleConnect = async (providerId) => {
    try {
      console.log('🔌 handleConnect called for provider:', providerId);
      if (providerId === 'github') {
        console.log('🐙 Detected GitHub provider, starting OAuth flow...');
        // GitHub requires OAuth flow
        await handleGitHubConnect();
      } else if (providerId === 'remote_host') {
        console.log('🖥️ Detected Remote Host provider, using direct connection...');
        // Remote host requires direct connection via MCP service
        const response = await apiService.connectMCPProvider(providerId, connectionConfig);
        if (response.status === 'success') {
          await loadConnections(); // Refresh the connections
          setSelectedProvider(null);
          setConnectionConfig({});
          alert('Remote host connected successfully!');
        } else {
          alert(`Failed to connect remote host: ${response.message || 'Unknown error'}`);
        }
      } else {
        console.log('🔗 Using direct connection for provider:', providerId);
        // Direct connection for other providers
        const response = await apiService.connectMCPProvider(providerId, connectionConfig);
        if (response.status === 'success') {
          await loadConnections(); // Refresh the connections
          setSelectedProvider(null);
          setConnectionConfig({});
        }
      }
    } catch (error) {
      console.error('💥 Failed to connect provider:', error);
      alert(`Failed to connect provider: ${error.message || 'Unknown error'}`);
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
                await loadConnections(); // Refresh the connections
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

  const handleDisconnect = async (providerId, connectionId = null) => {
    try {
      if (providerId === 'github') {
        // For GitHub, revoke the specific OAuth token
        if (connectionId) {
          await apiService.revokeMCPToken(connectionId);
        } else {
          // Revoke all GitHub tokens
          const tokensResponse = await apiService.getMCPTokens();
          const githubTokens = tokensResponse.tokens?.filter(token => token.provider === 'github') || [];
          for (const token of githubTokens) {
            await apiService.revokeMCPToken(token.token_id);
          }
        }
      } else if (providerId === 'remote_host') {
        // For remote hosts, disconnect the specific connection
        if (connectionId) {
          await apiService.disconnectMCPProvider('remote_host', { connection_id: connectionId });
        } else {
          await apiService.disconnectMCPProvider(providerId);
        }
      } else {
        // For other providers, use the standard disconnect
        await apiService.disconnectMCPProvider(providerId);
      }
      await loadConnections(); // Refresh the connections
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

  const renderGitHubTab = () => {
    const githubProvider = providers.find(p => p.id === 'github');

    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <i className="fab fa-github text-2xl text-gray-800"></i>
            <div>
              <h3 className="text-lg font-semibold text-gray-800">GitHub Connections</h3>
              <p className="text-sm text-gray-500">Connect to GitHub repositories</p>
            </div>
          </div>
          <button
            onClick={() => setSelectedProvider(githubProvider)}
            className="px-4 py-2 bg-gray-800 text-white rounded-md hover:bg-gray-900 transition-colors flex items-center gap-2"
          >
            <i className="fas fa-plus"></i>
            Add GitHub Account
          </button>
        </div>

        {githubConnections.length === 0 ? (
          <div className="text-center py-12 border-2 border-dashed border-gray-200 rounded-lg">
            <div className="text-4xl text-gray-300 mb-4">
              <i className="fab fa-github"></i>
            </div>
            <h3 className="text-lg font-medium text-gray-800 mb-2">No GitHub Connections</h3>
            <p className="text-gray-500 mb-4">Connect your GitHub account to access repositories</p>
            <button
              onClick={() => setSelectedProvider(githubProvider)}
              className="px-4 py-2 bg-gray-800 text-white rounded-md hover:bg-gray-900 transition-colors"
            >
              Connect GitHub
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {githubConnections.map((connection) => (
              <div key={connection.id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <i className="fab fa-github text-xl text-gray-800"></i>
                    <div>
                      <h4 className="font-medium text-gray-800">{connection.name}</h4>
                      <p className="text-sm text-gray-500">
                        {connection.repositories?.length || 0} repositories available
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                      Connected
                    </span>
                    <button
                      onClick={() => handleDisconnect('github', connection.id)}
                      className="px-3 py-1 bg-red-500 text-white rounded-md hover:bg-red-600 transition-colors text-sm"
                    >
                      Disconnect
                    </button>
                  </div>
                </div>

                {connection.repositories && connection.repositories.length > 0 && (
                  <div className="border-t border-gray-100 pt-3">
                    <p className="text-sm font-medium text-gray-700 mb-2">Available Repositories:</p>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                      {connection.repositories.slice(0, 6).map((repo, index) => (
                        <div key={index} className="text-sm text-gray-600 bg-gray-50 px-2 py-1 rounded">
                          {repo.name || repo.full_name || 'Repository'}
                        </div>
                      ))}
                      {connection.repositories.length > 6 && (
                        <div className="text-sm text-gray-500 px-2 py-1">
                          +{connection.repositories.length - 6} more...
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  const renderRemoteHostTab = () => {
    const remoteHostProvider = providers.find(p => p.id === 'remote_host');

    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <i className="fas fa-server text-2xl text-purple-600"></i>
            <div>
              <h3 className="text-lg font-semibold text-gray-800">Remote Host Connections</h3>
              <p className="text-sm text-gray-500">Connect to remote servers via SSH, SFTP, FTP, HTTP</p>
            </div>
          </div>
          <button
            onClick={() => setSelectedProvider(remoteHostProvider)}
            className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors flex items-center gap-2"
          >
            <i className="fas fa-plus"></i>
            Add Remote Host
          </button>
        </div>

        {remoteHostConnections.length === 0 ? (
          <div className="text-center py-12 border-2 border-dashed border-gray-200 rounded-lg">
            <div className="text-4xl text-gray-300 mb-4">
              <i className="fas fa-server"></i>
            </div>
            <h3 className="text-lg font-medium text-gray-800 mb-2">No Remote Host Connections</h3>
            <p className="text-gray-500 mb-4">Connect to remote servers to access files and documents</p>
            <button
              onClick={() => setSelectedProvider(remoteHostProvider)}
              className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors"
            >
              Add Remote Host
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {remoteHostConnections.map((connection) => (
              <div key={connection.id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <i className="fas fa-server text-xl text-purple-600"></i>
                    <div>
                      <h4 className="font-medium text-gray-800">{connection.name}</h4>
                      <p className="text-sm text-gray-500">
                        {connection.protocol?.toUpperCase()} • {connection.host}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      connection.connected
                        ? 'bg-green-100 text-green-800'
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {connection.connected ? 'Connected' : 'Disconnected'}
                    </span>
                    <button
                      onClick={() => handleDisconnect('remote_host', connection.id)}
                      className="px-3 py-1 bg-red-500 text-white rounded-md hover:bg-red-600 transition-colors text-sm"
                    >
                      Remove
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

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

          {/* Tab Navigation */}
          <div className="flex border-b border-gray-200 mb-6">
            <button
              onClick={() => setActiveTab('github')}
              className={`px-4 py-2 font-medium text-sm border-b-2 transition-colors ${
                activeTab === 'github'
                  ? 'border-gray-800 text-gray-800'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              <i className="fab fa-github mr-2"></i>
              GitHub
            </button>
            <button
              onClick={() => setActiveTab('remote_host')}
              className={`px-4 py-2 font-medium text-sm border-b-2 transition-colors ${
                activeTab === 'remote_host'
                  ? 'border-purple-600 text-purple-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              <i className="fas fa-server mr-2"></i>
              Remote Hosts
            </button>
          </div>

          {/* Tab Content */}
          {activeTab === 'github' && renderGitHubTab()}
          {activeTab === 'remote_host' && renderRemoteHostTab()}

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
                      ) : field.type === 'textarea' ? (
                        <textarea
                          value={connectionConfig[field.name] || field.default || ''}
                          onChange={(e) => setConnectionConfig({
                            ...connectionConfig,
                            [field.name]: e.target.value
                          })}
                          placeholder={field.description}
                          rows={4}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
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
