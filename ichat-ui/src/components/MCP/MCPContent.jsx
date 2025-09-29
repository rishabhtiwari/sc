import React, { useState, useEffect } from 'react';
import apiService from '../../services/apiService';

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

  const loadProviders = async () => {
    try {
      setLoading(true);
      setError(null);
      console.log('Calling getMCPProviders...');
      const response = await apiService.getMCPProviders();
      console.log('MCP providers response:', response);

      // Ensure we always have an array
      if (response && Array.isArray(response.providers)) {
        setProviders(response.providers);
      } else if (Array.isArray(response)) {
        setProviders(response);
      } else {
        console.warn('MCP providers response is not an array:', response);
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
      const response = await apiService.connectMCPProvider(providerId, connectionConfig);
      if (response.status === 'success') {
        await loadProviders(); // Refresh the list
        setSelectedProvider(null);
        setConnectionConfig({});
      }
    } catch (error) {
      console.error('Failed to connect provider:', error);
    }
  };

  const handleDisconnect = async (providerId) => {
    try {
      const response = await apiService.disconnectMCPProvider(providerId);
      if (response.status === 'success') {
        await loadProviders(); // Refresh the list
      }
    } catch (error) {
      console.error('Failed to disconnect provider:', error);
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
                <div key={provider.id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <i className={`${provider.icon || 'fas fa-plug'} text-xl text-gray-600`}></i>
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
        </div>
      </div>
    </div>
  );
};

export default MCPContent;
