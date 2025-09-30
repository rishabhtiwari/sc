import React, { useState, useEffect } from 'react';
import apiService from '../../services/apiService';

const ContextContent = () => {
  const [connectedRepos, setConnectedRepos] = useState([]);
  const [mcpResources, setMcpResources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('current'); // 'current' or 'mcp'
  
  // MCP Provider states
  const [mcpProviders, setMcpProviders] = useState([]);
  const [selectedProvider, setSelectedProvider] = useState(null);
  const [providerResources, setProviderResources] = useState([]);
  const [loadingResources, setLoadingResources] = useState(false);
  const [showConfigureModal, setShowConfigureModal] = useState(false);
  const [connectingResources, setConnectingResources] = useState(new Set());
  const [connectedResources, setConnectedResources] = useState(new Set());

  useEffect(() => {
    loadData();
  }, []);

  // Load data when switching to current context tab
  useEffect(() => {
    if (activeTab === 'current') {
      console.log('🔄 Current Context tab activated - loading data...');
      loadData();
    }
  }, [activeTab]);

  const loadData = async () => {
    try {
      console.log('🚀 Starting to load context data...');
      setLoading(true);
      await Promise.all([
        loadConnectedRepos(),
        loadMCPResources(),
        loadMCPProviders()
      ]);
      console.log('✅ Context data loading completed');
    } catch (error) {
      console.error('❌ Failed to load context data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadConnectedRepos = async () => {
    try {
      console.log('🔄 Loading connected repositories...');
      const response = await apiService.getConnectedRepositories();
      console.log('📦 Connected repositories response:', response);
      if (response.status === 'success' && response.repositories) {
        // Filter for manual resources (those without MCP provider info)
        // Also exclude repositories with git_ prefix which are MCP resources
        const manualResources = response.repositories.filter(resource =>
          !resource.provider_id && !resource.token_id &&
          !(resource.repository_id && resource.repository_id.startsWith('git_'))
        );
        console.log('📋 Manual resources found:', manualResources);
        setConnectedRepos(manualResources);
      } else {
        console.log('⚠️ No repositories found or invalid response');
        setConnectedRepos([]);
      }
    } catch (error) {
      console.error('❌ Failed to load connected repositories:', error);
      setConnectedRepos([]);
    }
  };

  const loadMCPResources = async () => {
    try {
      console.log('🔄 Loading MCP resources...');
      const response = await apiService.getMCPResources();
      console.log('📦 MCP resources response:', response);
      if (response.status === 'success' && response.repositories) {
        // Filter for MCP resources (those with MCP provider info or git_ prefix)
        const mcpResources = response.repositories.filter(resource =>
          resource.provider_id || resource.token_id ||
          (resource.repository_id && resource.repository_id.startsWith('git_'))
        ).map(resource => ({
          id: resource.repository_id || resource.id,
          resource_name: getRepositoryDisplayName(resource),
          resource_type: resource.type || 'repository',
          provider_id: resource.provider_id || 'unknown',
          created_at: resource.created_at,
          ...resource
        }));
        console.log('📋 MCP resources found:', mcpResources);
        setMcpResources(mcpResources);
      } else {
        console.log('⚠️ No MCP resources found or invalid response');
        setMcpResources([]);
      }
    } catch (error) {
      console.error('❌ Failed to load MCP resources:', error);
      setMcpResources([]);
    }
  };

  const loadMCPProviders = async () => {
    try {
      console.log('🔄 Loading connected MCP providers...');
      const response = await apiService.getMCPConnectedProviders();
      console.log('📦 Connected MCP providers response:', response);

      if (response.status === 'success' && response.tokens && Array.isArray(response.tokens)) {
        console.log('📋 Connected OAuth tokens found:', response.tokens);

        // Transform tokens to provider format for UI
        const providers = response.tokens.map(token => ({
          id: token.token_id,
          name: token.user_login ? `${token.provider} (${token.user_login})` : `${token.provider} Provider`,
          type: token.provider,
          status: 'connected',
          description: `Connected ${token.provider} provider${token.user_login ? ` for ${token.user_login}` : ''}`,
          created_at: new Date(token.created_at * 1000).toISOString(),
          token_id: token.token_id,
          user_login: token.user_login,
          scope: token.scope
        }));

        console.log('📋 Transformed providers for UI:', providers);
        setMcpProviders(providers);
      } else {
        console.log('⚠️ No connected MCP providers found or invalid response');
        setMcpProviders([]);
      }
    } catch (error) {
      console.error('❌ Failed to load connected MCP providers:', error);
      setMcpProviders([]);
    }
  };

  const handleCloseConfigureModal = () => {
    setShowConfigureModal(false);
    setSelectedProvider(null);
    setProviderResources([]);
    setConnectingResources(new Set());
    // Keep connectedResources state to remember connected status
  };

  const handleConfigureContext = async (provider) => {
    setSelectedProvider(provider);
    setLoadingResources(true);
    setShowConfigureModal(true);

    try {
      // Load available resources for this provider
      // Use provider type (e.g., 'github') and token_id for the API call
      const response = await apiService.getMCPProviderResources(provider.type, provider.token_id);
      console.log('📦 Provider resources response:', response);

      if (response.status === 'success' && response.resources) {
        setProviderResources(response.resources);

        // Get fresh context data directly from API instead of relying on state
        console.log('🔄 Getting fresh context data for comparison...');
        const [connectedReposResponse, mcpResourcesResponse] = await Promise.all([
          apiService.getConnectedRepositories(),
          apiService.getMCPResources()
        ]);

        console.log('📦 Fresh connected repos:', connectedReposResponse);
        console.log('📦 Fresh MCP resources:', mcpResourcesResponse);

        // Check which resources are already connected by comparing with fresh context data
        const connectedRepoUrls = new Set();

        // Check connected repositories - normalize URLs
        if (connectedReposResponse.status === 'success' && connectedReposResponse.repositories) {
          const manualResources = connectedReposResponse.repositories.filter(resource =>
            !resource.provider_id && !resource.token_id &&
            !(resource.repository_id && resource.repository_id.startsWith('git_'))
          );
          manualResources.forEach(repo => {
            if (repo.url) {
              connectedRepoUrls.add(normalizeUrl(repo.url));
            }
          });
        }

        // Check MCP resources - normalize URLs
        if (mcpResourcesResponse.status === 'success' && mcpResourcesResponse.repositories) {
          const mcpResources = mcpResourcesResponse.repositories.filter(resource =>
            resource.provider_id || resource.token_id ||
            (resource.repository_id && resource.repository_id.startsWith('git_'))
          );
          mcpResources.forEach(resource => {
            if (resource.url) {
              connectedRepoUrls.add(normalizeUrl(resource.url));
            }
          });
        }

        console.log('🔗 Connected repo URLs (normalized):', Array.from(connectedRepoUrls));

        // Mark resources as connected if they're already in context
        const connectedResourceIds = new Set();
        response.resources.forEach(resource => {
          const resourceUrl = resource.clone_url || resource.url;
          if (resourceUrl) {
            const normalizedResourceUrl = normalizeUrl(resourceUrl);
            console.log(`🔍 Checking resource: ${resource.name} (${normalizedResourceUrl})`);
            if (connectedRepoUrls.has(normalizedResourceUrl)) {
              console.log(`✅ Resource already connected: ${resource.name}`);
              connectedResourceIds.add(resource.id);
            }
          }
        });

        console.log('🎯 Connected resource IDs:', Array.from(connectedResourceIds));
        setConnectedResources(connectedResourceIds);
      } else {
        setProviderResources([]);
        setConnectedResources(new Set());
      }
    } catch (error) {
      console.error('Failed to load provider resources:', error);
      setProviderResources([]);
      setConnectedResources(new Set());
    } finally {
      setLoadingResources(false);
    }
  };

  const handleAddResourceToContext = async (resource) => {
    // Add resource to connecting state
    setConnectingResources(prev => new Set([...prev, resource.id]));

    try {
      console.log('🔄 Adding resource to context:', resource);
      console.log('🔄 Selected provider:', selectedProvider);

      const response = await apiService.addMCPResourceToContext(
        selectedProvider.type, // provider type (e.g., 'github')
        selectedProvider.token_id, // token ID
        {
          resource_id: resource.id,
          resource_type: resource.type,
          resource_name: resource.name,
          clone_url: resource.clone_url,
          default_branch: resource.default_branch
        }
      );

      console.log('📦 Add resource response:', response);

      if (response.status === 'success') {
        // Mark resource as connected
        setConnectedResources(prev => new Set([...prev, resource.id]));

        // Refresh data
        await loadData();

        // Optional: Close modal after successful connection
        // setShowConfigureModal(false);
      }
    } catch (error) {
      console.error('Failed to add resource to context:', error);
    } finally {
      // Remove resource from connecting state
      setConnectingResources(prev => {
        const newSet = new Set(prev);
        newSet.delete(resource.id);
        return newSet;
      });
    }
  };

  const handleRemoveFromContext = async (resourceId, isManual = false) => {
    try {
      if (isManual) {
        await apiService.removeRepository(resourceId);
      } else {
        await apiService.removeMCPResourceFromContext(resourceId);
      }
      await loadData();
    } catch (error) {
      console.error('Failed to remove resource from context:', error);
    }
  };

  const getRepositoryDisplayName = (repo) => {
    if (repo.name && repo.name.trim()) {
      return repo.name;
    }
    if (repo.url) {
      const urlParts = repo.url.split('/');
      const repoName = urlParts[urlParts.length - 1].replace('.git', '');
      return repoName || 'Unknown Repository';
    }
    return 'Unknown Repository';
  };

  // Helper function to normalize URLs for comparison
  const normalizeUrl = (url) => {
    if (!url) return '';
    // Remove trailing slashes, convert to lowercase, remove .git suffix
    return url.toLowerCase().replace(/\/+$/, '').replace(/\.git$/, '');
  };

  const getResourceIcon = (resourceType) => {
    switch (resourceType) {
      case 'repository':
        return 'fas fa-code-branch';
      case 'database':
        return 'fas fa-database';
      case 'document':
        return 'fas fa-file-alt';
      case 'api':
        return 'fas fa-plug';
      case 'folder':
        return 'fas fa-folder';
      default:
        return 'fas fa-cube';
    }
  };

  const getProviderIcon = (providerType) => {
    switch (providerType) {
      case 'github':
        return 'fab fa-github';
      case 'database':
        return 'fas fa-database';
      case 'document':
        return 'fas fa-file-alt';
      default:
        return 'fas fa-plug';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2 text-gray-600">Loading context data...</span>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Context Management</h2>
        <p className="text-gray-600">
          Manage your RAG context resources and configure MCP providers for enhanced AI conversations.
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="flex border-b border-gray-200 mb-6">
        <button
          onClick={() => setActiveTab('current')}
          className={`px-4 py-2 font-medium text-sm border-b-2 transition-colors ${
            activeTab === 'current'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <i className="fas fa-list mr-2"></i>
          Current Context
        </button>
        <button
          onClick={() => setActiveTab('mcp')}
          className={`px-4 py-2 font-medium text-sm border-b-2 transition-colors ${
            activeTab === 'mcp'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <i className="fas fa-plug mr-2"></i>
          MCP Providers
        </button>
      </div>

      {/* Current Context Tab */}
      {activeTab === 'current' && (
        <div>
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Current Context Overview</h3>
            <p className="text-gray-600 mb-6">All resources currently available for RAG context, grouped by resource type</p>

            {(() => {
              // Combine all resources from both manual and MCP sources
              const allResources = [
                ...(Array.isArray(connectedRepos) ? connectedRepos : []).map(resource => ({
                  ...resource,
                  id: resource.repository_id || resource.id,
                  resource_name: getRepositoryDisplayName(resource),
                  resource_type: resource.type || 'repository',
                  source: 'manual',
                  provider_id: null
                })),
                ...(Array.isArray(mcpResources) ? mcpResources : []).map(resource => ({
                  ...resource,
                  resource_type: resource.resource_type || 'repository',
                  source: 'mcp'
                }))
              ];

              // Group all resources by type
              const groupedByType = allResources.reduce((groups, resource) => {
                const type = resource.resource_type || 'repository';
                if (!groups[type]) groups[type] = [];
                groups[type].push(resource);
                return groups;
              }, {});

              if (Object.keys(groupedByType).length === 0) {
                return (
                  <div className="text-center py-12">
                    <div className="text-gray-400 text-lg mb-2">No context resources connected</div>
                    <p className="text-gray-500 text-sm">
                      Add repositories, documents, databases, or other resources to provide context for your conversations.
                    </p>
                  </div>
                );
              }

              return (
                <div className="space-y-8">
                  {Object.entries(groupedByType).map(([type, resources]) => (
                    <div key={type} className="mb-8">
                      <div className="flex items-center gap-2 mb-4">
                        <i className={`${getResourceIcon(type)} text-blue-600`}></i>
                        <h4 className="text-lg font-medium text-gray-800 capitalize">
                          {type}s ({resources.length})
                        </h4>
                      </div>
                      <div className="grid gap-3">
                        {resources.map((resource) => (
                          <div key={resource.id} className="border border-gray-200 rounded-lg p-4 bg-white">
                            <div className="flex items-center justify-between">
                              <div className="flex items-center gap-3">
                                <i className={`${getResourceIcon(resource.resource_type)} text-lg text-gray-600`}></i>
                                <div>
                                  <h5 className="font-medium text-gray-800">{resource.resource_name}</h5>
                                  <p className="text-sm text-gray-500">
                                    {resource.url || resource.path || 'No URL/Path'}
                                  </p>
                                  <div className="flex items-center gap-4 text-xs text-gray-400 mt-1">
                                    {resource.branch && <span>Branch: {resource.branch}</span>}
                                    {resource.info?.total_files && <span>Files: {resource.info.total_files}</span>}
                                    {resource.status && <span>Status: {resource.status}</span>}
                                    {resource.provider_id && <span>Provider: {resource.provider_id}</span>}
                                    <span>Added: {new Date(resource.created_at).toLocaleDateString()}</span>
                                  </div>
                                </div>
                              </div>
                              <div className="flex items-center gap-2">
                                <span className={`px-2 py-1 text-xs rounded-full ${
                                  resource.source === 'mcp' 
                                    ? 'bg-green-100 text-green-800' 
                                    : 'bg-blue-100 text-blue-800'
                                }`}>
                                  {resource.source === 'mcp' ? 'MCP' : 'Manual'}
                                </span>
                                <button
                                  onClick={() => handleRemoveFromContext(resource.id, resource.source === 'manual')}
                                  className="px-3 py-1 bg-red-500 text-white rounded-md hover:bg-red-600 transition-colors text-sm"
                                >
                                  Remove
                                </button>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}

                  {/* Summary */}
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <i className="fas fa-info-circle text-blue-600"></i>
                      <h4 className="font-medium text-blue-800">Context Summary</h4>
                    </div>
                    <p className="text-blue-700 text-sm">
                      Total: {allResources.length} resources available for RAG context
                      {Object.entries(groupedByType).map(([type, resources]) => 
                        ` • ${resources.length} ${type}${resources.length !== 1 ? 's' : ''}`
                      ).join('')}
                    </p>
                  </div>
                </div>
              );
            })()}
          </div>
        </div>
      )}

      {/* MCP Providers Tab */}
      {activeTab === 'mcp' && (
        <div>
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">MCP Providers</h3>
            <p className="text-gray-600 mb-6">Configure context resources from your connected MCP providers. Each provider gives you access to different types of resources like repositories, databases, and documents.</p>

            {!Array.isArray(mcpProviders) || mcpProviders.length === 0 ? (
              <div className="text-center py-12">
                <div className="text-gray-400 text-lg mb-2">No MCP providers connected</div>
                <p className="text-gray-500 text-sm mb-4">
                  You need to connect MCP providers first to configure context resources. Go to the MCP page to connect providers like GitHub, databases, and document sources.
                </p>
                <div className="text-xs text-gray-400">
                  <i className="fas fa-info-circle mr-1"></i>
                  MCP providers are connected through the main MCP configuration page
                </div>
              </div>
            ) : (
              <div className="grid gap-4">
                {(Array.isArray(mcpProviders) ? mcpProviders : []).map((provider) => (
                  <div key={provider.id} className="border border-gray-200 rounded-lg p-6 bg-white">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                          <i className={`${getProviderIcon(provider.type)} text-xl text-blue-600`}></i>
                        </div>
                        <div>
                          <h4 className="text-lg font-medium text-gray-800">{provider.name}</h4>
                          <p className="text-sm text-gray-500">{provider.description || `Access ${provider.type} resources for context`}</p>
                          <div className="flex items-center gap-4 text-xs text-gray-400 mt-2">
                            <span className={`px-2 py-1 rounded text-xs font-medium ${
                              provider.status === 'connected'
                                ? 'bg-green-100 text-green-800'
                                : 'bg-gray-100 text-gray-600'
                            }`}>
                              {provider.status}
                            </span>
                            <span>Type: {provider.type}</span>
                            <span>Connected: {new Date(provider.created_at).toLocaleDateString()}</span>
                          </div>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleConfigureContext(provider)}
                          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                        >
                          <i className="fas fa-cog mr-2"></i>
                          Configure Context
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Configure Context Modal */}
      {showConfigureModal && selectedProvider && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-4xl mx-4 max-h-[80vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <div>
                <h3 className="text-xl font-semibold text-gray-800">Configure Context - {selectedProvider.name}</h3>
                <p className="text-gray-600">Select resources to add to your RAG context</p>
              </div>
              <button
                onClick={handleCloseConfigureModal}
                className="text-gray-400 hover:text-gray-600"
              >
                <i className="fas fa-times text-xl"></i>
              </button>
            </div>

            {loadingResources ? (
              <div className="text-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                <p className="text-gray-600 mt-2">Loading available resources...</p>
              </div>
            ) : providerResources.length === 0 ? (
              <div className="text-center py-12">
                <div className="text-gray-400 text-lg mb-2">No resources available</div>
                <p className="text-gray-500 text-sm">
                  This provider doesn't have any resources available for context configuration.
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="mb-4">
                  <h4 className="font-medium text-gray-800 mb-2">Available Resources ({providerResources.length})</h4>
                  <p className="text-sm text-gray-600">Click "Add to Context" to include a resource in your RAG context</p>
                </div>

                <div className="grid gap-3 max-h-96 overflow-y-auto">
                  {providerResources.map((resource) => (
                    <div key={resource.id} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <i className={`${getResourceIcon(resource.type)} text-lg text-gray-600`}></i>
                          <div>
                            <h5 className="font-medium text-gray-800">{resource.name}</h5>
                            <p className="text-sm text-gray-500">{resource.description || resource.url}</p>
                            <div className="flex items-center gap-4 text-xs text-gray-400 mt-1">
                              <span>Type: {resource.type}</span>
                              {resource.default_branch && <span>Branch: {resource.default_branch}</span>}
                              {resource.size && <span>Size: {resource.size}</span>}
                              {resource.updated_at && <span>Updated: {new Date(resource.updated_at).toLocaleDateString()}</span>}
                            </div>
                          </div>
                        </div>
                        {(() => {
                          const isConnecting = connectingResources.has(resource.id);
                          const isConnected = connectedResources.has(resource.id);

                          if (isConnected) {
                            return (
                              <button
                                disabled
                                className="px-4 py-2 bg-green-100 text-green-800 border border-green-200 rounded-lg cursor-not-allowed"
                              >
                                <i className="fas fa-check mr-2"></i>
                                Connected
                              </button>
                            );
                          }

                          if (isConnecting) {
                            return (
                              <button
                                disabled
                                className="px-4 py-2 bg-blue-100 text-blue-800 border border-blue-200 rounded-lg cursor-not-allowed"
                              >
                                <i className="fas fa-spinner fa-spin mr-2"></i>
                                Connecting...
                              </button>
                            );
                          }

                          return (
                            <button
                              onClick={() => handleAddResourceToContext(resource)}
                              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                            >
                              <i className="fas fa-plus mr-2"></i>
                              Add to Context
                            </button>
                          );
                        })()}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="flex justify-end gap-3 mt-6 pt-4 border-t border-gray-200">
              <button
                onClick={handleCloseConfigureModal}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ContextContent;
