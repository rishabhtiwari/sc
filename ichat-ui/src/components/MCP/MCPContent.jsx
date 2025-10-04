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
  const [syncStatus, setSyncStatus] = useState({});
  const [syncHistory, setSyncHistory] = useState([]);
  const [activeJobs, setActiveJobs] = useState({});
  const [githubSyncStatus, setGithubSyncStatus] = useState({});
  const [githubActiveJobs, setGithubActiveJobs] = useState({});

  useEffect(() => {
    console.log('MCPContent mounted, loading providers...');
    loadProviders();
    loadConnections();
    loadSyncHistory();
    loadActiveJobs();
    loadGithubActiveJobs();

    // Set up periodic polling for active jobs (every 30 seconds)
    const activeJobsInterval = setInterval(() => {
      loadActiveJobs();
      loadGithubActiveJobs();
    }, 30000);

    return () => {
      clearInterval(activeJobsInterval);
    };
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

  const handleTestConnection = async (providerId, connectionId) => {
    try {
      console.log(`🧪 Testing connection for provider: ${providerId}, connection: ${connectionId}`);

      if (providerId === 'remote_host') {
        // Test remote host connection
        const response = await apiService.testMCPProviderConnection(providerId, connectionId);

        if (response.status === 'success') {
          alert('Connection test successful! ✅');
          await loadConnections(); // Refresh to show updated status
        } else {
          alert(`Connection test failed: ${response.message || 'Unknown error'} ❌`);
        }
      } else {
        alert('Connection testing is currently only supported for remote host connections.');
      }
    } catch (error) {
      console.error('Failed to test connection:', error);
      alert(`Failed to test connection: ${error.message || 'Unknown error'} ❌`);
    }
  };

  const handleTestConnectionInWizard = async () => {
    try {
      console.log('🧪 Testing connection in wizard with config:', connectionConfig);

      // Validate required fields
      const requiredFields = selectedProvider.config_fields?.filter(field => {
        const selectedProtocol = connectionConfig.protocol;
        const isHttpProtocol = selectedProtocol === 'http' || selectedProtocol === 'https';
        const isFieldRequired = field.required && !(isHttpProtocol && (field.name === 'username' || field.name === 'password'));
        return isFieldRequired;
      }) || [];

      for (const field of requiredFields) {
        if (!connectionConfig[field.name]) {
          alert(`Please fill in the required field: ${field.label}`);
          return;
        }
      }

      // Create a temporary connection config for testing
      let testConfig = { ...connectionConfig };

      // Test the connection configuration via API server (which handles localhost conversion)
      const response = await fetch('http://localhost:8080/api/mcp/providers/remote_host/test-config', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(testConfig),
      });

      const result = await response.json();

      if (result.status === 'success') {
        alert('Connection test successful! ✅ You can now connect.');
      } else {
        alert(`Connection test failed: ${result.message || 'Unknown error'} ❌`);
      }
    } catch (error) {
      console.error('Failed to test connection in wizard:', error);
      alert(`Failed to test connection: ${error.message || 'Unknown error'} ❌`);
    }
  };

  const handleSyncConnection = async (connectionId) => {
    try {
      console.log(`🔄 Starting sync for connection: ${connectionId}`);

      // Set sync status to loading
      setSyncStatus(prev => ({
        ...prev,
        [connectionId]: { status: 'syncing', message: 'Starting sync...', progress: 0 }
      }));

      const response = await apiService.triggerSyncConnection(connectionId);

      if (response.status === 'success' && response.job_id) {
        // Update sync status with immediate job information from response
        const job = response.job || {};
        const message = job.status === 'pending'
          ? 'Preparing sync...'
          : job.status === 'running'
          ? `Processing ${job.processed_files || 0}/${job.total_files || 0} files...`
          : 'Starting sync...';

        setSyncStatus(prev => ({
          ...prev,
          [connectionId]: {
            status: 'syncing',
            message: message,
            progress: job.progress || 0,
            jobId: response.job_id
          }
        }));

        // Start polling job status
        pollJobStatus(connectionId, response.job_id);
      } else if (response.status === 'error' && response.error && response.error.includes('409')) {
        // Handle concurrent sync error - extract job_id if available
        const errorMatch = response.error.match(/job_id":"([^"]+)"/);
        if (errorMatch) {
          const existingJobId = errorMatch[1];
          console.log(`🔄 Sync already in progress, polling existing job: ${existingJobId}`);
          pollJobStatus(connectionId, existingJobId);
        } else {
          setSyncStatus(prev => ({
            ...prev,
            [connectionId]: { status: 'error', message: 'Sync already in progress' }
          }));
        }
      } else {
        setSyncStatus(prev => ({
          ...prev,
          [connectionId]: { status: 'error', message: response.message || response.error || 'Sync failed' }
        }));
      }
    } catch (error) {
      console.error('Failed to sync connection:', error);

      // Handle 409 error (sync already in progress)
      if (error.message && error.message.includes('409')) {
        setSyncStatus(prev => ({
          ...prev,
          [connectionId]: { status: 'error', message: 'Sync already in progress' }
        }));
      } else {
        setSyncStatus(prev => ({
          ...prev,
          [connectionId]: { status: 'error', message: error.message || 'Sync failed' }
        }));
      }
    }
  };

  const pollJobStatus = async (connectionId, jobId) => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await apiService.getJobStatus(jobId);

        if (response.status === 'success' && response.job) {
          const job = response.job;

          // Update sync status based on job status
          if (job.status === 'pending') {
            setSyncStatus(prev => ({
              ...prev,
              [connectionId]: {
                status: 'syncing',
                message: 'Preparing sync...',
                progress: 0,
                jobId: jobId
              }
            }));
          } else if (job.status === 'running') {
            setSyncStatus(prev => ({
              ...prev,
              [connectionId]: {
                status: 'syncing',
                message: `Processing ${job.processed_files || 0}/${job.total_files || 0} files...`,
                progress: job.progress || 0,
                jobId: jobId
              }
            }));
          } else if (job.status === 'completed') {
            setSyncStatus(prev => ({
              ...prev,
              [connectionId]: {
                status: 'success',
                message: `Sync completed: ${job.processed_files || 0} files processed`,
                progress: 100,
                jobId: jobId
              }
            }));

            // Load sync history to show updated results
            await loadSyncHistory();

            // Clear success status after 5 seconds
            setTimeout(() => {
              setSyncStatus(prev => ({
                ...prev,
                [connectionId]: null
              }));
            }, 5000);

            clearInterval(pollInterval);
          } else if (job.status === 'failed') {
            setSyncStatus(prev => ({
              ...prev,
              [connectionId]: {
                status: 'error',
                message: job.error_message || 'Sync failed',
                jobId: jobId
              }
            }));
            clearInterval(pollInterval);
          }
        }
      } catch (error) {
        console.error('Failed to poll job status:', error);
        // Don't clear interval on polling errors, just log them
      }
    }, 2000); // Poll every 2 seconds

    // Clear interval after 5 minutes to prevent infinite polling
    setTimeout(() => {
      clearInterval(pollInterval);
    }, 300000);
  };

  const handleSyncGithubRepository = async (repositoryId, displayName = null) => {
    try {
      console.log(`🔄 Starting sync for GitHub repository: ${repositoryId} (${displayName || repositoryId})`);

      // Use display name for sync status tracking, fall back to repository ID
      const statusKey = displayName || repositoryId;

      // Set sync status to loading
      setGithubSyncStatus(prev => ({
        ...prev,
        [statusKey]: { status: 'syncing', message: 'Starting sync...', progress: 0 }
      }));

      // Trigger sync using the repository ID directly (API service handles encoding)
      const response = await apiService.triggerGitHubRepositorySync(repositoryId);

      if (response.status === 'success' && response.job_id) {
        // Update sync status with immediate job information from response
        const job = response.job || {};
        const message = job.status === 'pending'
          ? 'Preparing sync...'
          : job.status === 'running'
          ? `Processing ${job.processed_files || 0}/${job.total_files || 0} files...`
          : 'Starting sync...';

        setGithubSyncStatus(prev => ({
          ...prev,
          [statusKey]: {
            status: 'syncing',
            message: message,
            progress: job.progress || 0,
            jobId: response.job_id
          }
        }));

        // Start polling job status
        pollGithubJobStatus(statusKey, response.job_id);
      } else if (response.status === 'error' && response.error && response.error.includes('409')) {
        // Handle concurrent sync error - extract job_id if available
        const errorMatch = response.error.match(/job_id":"([^"]+)"/);
        if (errorMatch) {
          const existingJobId = errorMatch[1];
          console.log(`🔄 GitHub sync already in progress, polling existing job: ${existingJobId}`);
          pollGithubJobStatus(statusKey, existingJobId);
        } else {
          setGithubSyncStatus(prev => ({
            ...prev,
            [statusKey]: { status: 'error', message: 'Sync already in progress' }
          }));
        }
      } else {
        setGithubSyncStatus(prev => ({
          ...prev,
          [statusKey]: { status: 'error', message: response.message || response.error || 'Sync failed' }
        }));
      }
    } catch (error) {
      console.error('Failed to sync GitHub repository:', error);

      // Handle 409 error (sync already in progress)
      if (error.message && error.message.includes('409')) {
        setGithubSyncStatus(prev => ({
          ...prev,
          [statusKey]: { status: 'error', message: 'Sync already in progress' }
        }));
      } else {
        setGithubSyncStatus(prev => ({
          ...prev,
          [statusKey]: { status: 'error', message: error.message || 'Sync failed' }
        }));
      }
    }
  };

  const pollGithubJobStatus = async (statusKey, jobId) => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await apiService.getGitHubJobStatus(jobId);

        if (response.status === 'success' && response.job) {
          const job = response.job;

          // Update sync status based on job status
          if (job.status === 'pending') {
            setGithubSyncStatus(prev => ({
              ...prev,
              [statusKey]: {
                status: 'syncing',
                message: 'Preparing sync...',
                progress: 0,
                jobId: jobId
              }
            }));
          } else if (job.status === 'running') {
            setGithubSyncStatus(prev => ({
              ...prev,
              [statusKey]: {
                status: 'syncing',
                message: `Processing ${job.processed_files || 0}/${job.total_files || 0} files...`,
                progress: job.progress || 0,
                jobId: jobId
              }
            }));
          } else if (job.status === 'completed') {
            setGithubSyncStatus(prev => ({
              ...prev,
              [statusKey]: {
                status: 'success',
                message: `Sync completed: ${job.processed_files || 0} files processed`,
                progress: 100,
                jobId: jobId
              }
            }));

            // Clear success status after 5 seconds
            setTimeout(() => {
              setGithubSyncStatus(prev => ({
                ...prev,
                [statusKey]: null
              }));
            }, 5000);

            clearInterval(pollInterval);
          } else if (job.status === 'failed') {
            setGithubSyncStatus(prev => ({
              ...prev,
              [statusKey]: {
                status: 'error',
                message: job.error_message || 'Sync failed',
                jobId: jobId
              }
            }));
            clearInterval(pollInterval);
          }
        }
      } catch (error) {
        console.error('Failed to poll GitHub job status:', error);
        // Don't clear interval on polling errors, just log them
      }
    }, 2000); // Poll every 2 seconds

    // Clear interval after 5 minutes to prevent infinite polling
    setTimeout(() => {
      clearInterval(pollInterval);
    }, 300000);
  };

  const loadSyncHistory = async () => {
    try {
      const response = await apiService.getSyncHistory({ limit: 10 });
      if (response.status === 'success') {
        setSyncHistory(response.history || []);
      }
    } catch (error) {
      console.warn('Failed to load sync history:', error);
    }
  };

  const loadActiveJobs = async () => {
    try {
      const response = await apiService.getActiveJobs();
      if (response.status === 'success' && response.jobs) {
        // Group active jobs by connection_id
        const jobsByConnection = {};
        const newSyncStatus = {};

        response.jobs.forEach(job => {
          if (!jobsByConnection[job.connection_id]) {
            jobsByConnection[job.connection_id] = [];
          }
          jobsByConnection[job.connection_id].push(job);

          // Initialize sync status for active jobs to maintain UI consistency
          if (job.status === 'running' || job.status === 'pending') {
            newSyncStatus[job.connection_id] = {
              status: 'syncing',
              message: job.status === 'pending'
                ? 'Preparing sync...'
                : `Processing ${job.processed_files || 0}/${job.total_files || 0} files...`,
              progress: job.progress || 0,
              jobId: job.id
            };
          }
        });

        setActiveJobs(jobsByConnection);

        // Update sync status for connections with active jobs
        setSyncStatus(prev => ({
          ...prev,
          ...newSyncStatus
        }));

        // Start polling for any active jobs found on page load
        Object.keys(newSyncStatus).forEach(connectionId => {
          const job = response.jobs.find(j => j.connection_id === connectionId && (j.status === 'running' || j.status === 'pending'));
          if (job) {
            console.log(`🔄 Found active job on page load, starting polling for connection ${connectionId}, job ${job.id}`);
            pollJobStatus(connectionId, job.id);
          }
        });
      }
    } catch (error) {
      console.error('Failed to load active jobs:', error);
    }
  };

  const loadGithubActiveJobs = async () => {
    try {
      const response = await apiService.getGitHubActiveJobs();

      if (response.status === 'success' && response.jobs) {
        // Get repository information to map IDs to display names
        const repoResponse = await apiService.getGitHubRepositories();
        const repositoryMap = {};

        if (repoResponse.status === 'success' && repoResponse.repositories) {
          repoResponse.repositories.forEach(repo => {
            repositoryMap[repo.id] = repo.full_name || repo.name;
          });
        }

        // Group active jobs by repository_id
        const jobsByRepository = {};
        const newGithubSyncStatus = {};

        response.jobs.forEach(job => {
          if (!jobsByRepository[job.repository_id]) {
            jobsByRepository[job.repository_id] = [];
          }
          jobsByRepository[job.repository_id].push(job);

          // Initialize sync status for active jobs to maintain UI consistency
          if (job.status === 'running' || job.status === 'pending') {
            // Use display_name from job metadata, or look up repository display name, or fall back to repository_id
            const statusKey = job.display_name || repositoryMap[job.repository_id] || job.repository_id;

            newGithubSyncStatus[statusKey] = {
              status: 'syncing',
              message: job.status === 'pending'
                ? 'Preparing sync...'
                : `Processing ${job.processed_files || 0}/${job.total_files || 0} files...`,
              progress: job.progress || 0,
              jobId: job.id
            };
          }
        });

        setGithubActiveJobs(jobsByRepository);

        // Update sync status for repositories with active jobs
        setGithubSyncStatus(prev => ({
          ...prev,
          ...newGithubSyncStatus
        }));

        // Start polling for any active jobs found on page load
        Object.keys(newGithubSyncStatus).forEach(statusKey => {
          const job = response.jobs.find(j => {
            const jobKey = j.display_name || repositoryMap[j.repository_id] || j.repository_id;
            return jobKey === statusKey && (j.status === 'running' || j.status === 'pending');
          });
          if (job) {
            console.log(`🔄 Found active GitHub job on page load, starting polling for repository ${statusKey}, job ${job.id}`);
            pollGithubJobStatus(statusKey, job.id);
          }
        });
      }
    } catch (error) {
      console.error('Failed to load GitHub active jobs:', error);
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
          <div className="flex items-center gap-2">
            {githubConnections.length > 0 && (
              <>
                <button
                  onClick={async () => {
                    try {
                      const response = await apiService.triggerGitHubSyncAll();
                      if (response.status === 'success') {
                        // Show immediate feedback with job information
                        const job = response.job || {};
                        const message = job.status === 'pending'
                          ? 'GitHub sync started - preparing...'
                          : job.status === 'running'
                          ? `GitHub sync running: ${job.processed_files || 0}/${job.total_files || 0} files`
                          : 'GitHub sync started successfully!';

                        alert(`✅ ${message}`);
                        await loadGithubActiveJobs();
                      }
                    } catch (error) {
                      alert(`❌ Failed to start GitHub sync: ${error.message}`);
                    }
                  }}
                  className="px-3 py-1.5 text-sm bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors flex items-center gap-2"
                  title="Sync all GitHub repositories"
                >
                  <i className="fas fa-sync-alt text-xs"></i>
                  Sync All
                </button>

                <button
                  onClick={async () => {
                    if (window.confirm('⚠️ This will cancel all active GitHub sync jobs. Are you sure?')) {
                      try {
                        const response = await apiService.emergencyCleanupGitHubJobs();
                        if (response.status === 'success') {
                          alert(`✅ GitHub cleanup completed! ${response.stale_count || 0} jobs cancelled.`);
                          await loadGithubActiveJobs();
                        }
                      } catch (error) {
                        alert(`❌ Failed to cleanup GitHub jobs: ${error.message}`);
                      }
                    }
                  }}
                  className="px-3 py-1.5 text-sm bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors flex items-center gap-2"
                  title="Cancel all active GitHub sync jobs"
                >
                  <i className="fas fa-broom text-xs"></i>
                  Cleanup Jobs
                </button>
              </>
            )}
            <button
              onClick={() => setSelectedProvider(githubProvider)}
              className="px-4 py-2 bg-gray-800 text-white rounded-md hover:bg-gray-900 transition-colors flex items-center gap-2"
            >
              <i className="fas fa-plus"></i>
              Add GitHub Account
            </button>
          </div>
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
                    <div className="space-y-2">
                      {connection.repositories.slice(0, 8).map((repo, index) => {
                        const repoDisplayName = repo.full_name || repo.name; // Use display name for sync status matching
                        const repoId = repo.id; // Keep internal ID for API calls
                        return (
                          <div key={index} className="flex items-center justify-between bg-gray-50 px-3 py-2 rounded-lg">
                            <div className="flex items-center gap-2">
                              <i className="fab fa-github text-gray-600"></i>
                              <div>
                                <span className="text-sm font-medium text-gray-800">
                                  {repo.name || repo.full_name || 'Repository'}
                                </span>
                                {repo.private && (
                                  <span className="ml-2 px-1.5 py-0.5 text-xs bg-yellow-100 text-yellow-800 rounded">
                                    Private
                                  </span>
                                )}
                              </div>
                            </div>

                            <div className="flex items-center gap-2">
                              {/* GitHub Sync Status */}
                              {githubSyncStatus[repoDisplayName] && !githubActiveJobs[repoId]?.length && (
                                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                                  githubSyncStatus[repoDisplayName].status === 'success'
                                    ? 'bg-green-100 text-green-800'
                                    : githubSyncStatus[repoDisplayName].status === 'error'
                                    ? 'bg-red-100 text-red-800'
                                    : 'bg-gray-100 text-gray-800'
                                }`}>
                                  {githubSyncStatus[repoDisplayName].status === 'success' ? 'Synced' :
                                   githubSyncStatus[repoDisplayName].status === 'error' ? 'Sync Failed' : 'Ready'}
                                </span>
                              )}

                              {/* GitHub Sync Button - only show when no active jobs and no syncing status */}
                              {(!githubActiveJobs[repoId] || githubActiveJobs[repoId].length === 0) &&
                               (!githubSyncStatus[repoDisplayName] || githubSyncStatus[repoDisplayName].status !== 'syncing') && (
                                <button
                                  onClick={() => handleSyncGithubRepository(repoId, repoDisplayName)}
                                  className="px-2 py-1 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors text-xs"
                                  title="Sync this repository"
                                >
                                  <i className="fas fa-sync-alt mr-1"></i>
                                  Sync
                                </button>
                              )}

                              {/* GitHub Syncing Status - show progress bar when syncing */}
                              {githubSyncStatus[repoDisplayName] && githubSyncStatus[repoDisplayName].status === 'syncing' && (
                                <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg px-3 py-2 shadow-sm min-w-[200px]">
                                  <div className="space-y-2">
                                    <div className="flex items-center justify-between">
                                      <span className="text-xs font-medium text-blue-800">Syncing...</span>
                                      <span className="text-xs font-bold text-blue-700 bg-blue-100 px-2 py-0.5 rounded-full">
                                        {githubSyncStatus[repoDisplayName].progress || 0}%
                                      </span>
                                    </div>
                                    <div className="w-full bg-gray-200 rounded-full h-1.5 overflow-hidden">
                                      <div
                                        className="bg-gradient-to-r from-blue-500 to-indigo-600 h-1.5 rounded-full transition-all duration-500 ease-out"
                                        style={{ width: `${githubSyncStatus[repoDisplayName].progress || 0}%` }}
                                      ></div>
                                    </div>
                                    <div className="text-xs text-blue-600">
                                      {githubSyncStatus[repoDisplayName].message || 'Processing...'}
                                    </div>
                                  </div>
                                </div>
                              )}

                              {/* Active GitHub Jobs */}
                              {githubActiveJobs[repoId] && githubActiveJobs[repoId].length > 0 && (
                                <div className="flex items-center gap-2">
                                  {githubActiveJobs[repoId].map(job => (
                                    <div key={job.id} className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg px-3 py-2 shadow-sm min-w-[200px]">
                                      <div className="space-y-2">
                                        <div className="flex items-center justify-between">
                                          <div className="flex items-center gap-2">
                                            <div className="relative">
                                              <i className="fas fa-sync-alt fa-spin text-blue-600 text-sm"></i>
                                              <div className="absolute -top-0.5 -right-0.5 w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse"></div>
                                            </div>
                                            <span className="font-semibold text-blue-800 text-sm">
                                              {job.status === 'pending' ? 'Preparing...' : 'Syncing'}
                                            </span>
                                          </div>
                                          <button
                                            onClick={async () => {
                                              if (window.confirm(`Cancel sync job for ${repo.name}?`)) {
                                                try {
                                                  const response = await apiService.cancelGitHubJob(job.id);
                                                  if (response.status === 'success') {
                                                    alert('✅ GitHub job cancelled successfully!');
                                                    await loadGithubActiveJobs();
                                                  }
                                                } catch (error) {
                                                  alert(`❌ Failed to cancel GitHub job: ${error.message}`);
                                                }
                                              }
                                            }}
                                            className="group px-3 py-1.5 bg-white border border-red-200 text-red-600 rounded-md hover:bg-red-50 hover:border-red-300 transition-all duration-200 text-xs font-medium shadow-sm"
                                            title="Cancel sync job"
                                          >
                                            <i className="fas fa-times mr-1 group-hover:scale-110 transition-transform"></i>
                                            Cancel
                                          </button>
                                        </div>

                                        {/* Compact Progress Bar */}
                                        <div className="space-y-1">
                                          <div className="flex justify-between items-center">
                                            <span className="text-xs font-medium text-gray-600">Progress</span>
                                            <span className="text-xs font-bold text-blue-700 bg-blue-100 px-2 py-0.5 rounded-full">
                                              {job.progress || 0}%
                                            </span>
                                          </div>
                                          <div className="w-full bg-gray-200 rounded-full h-1.5 overflow-hidden">
                                            <div
                                              className="bg-gradient-to-r from-blue-500 to-indigo-600 h-1.5 rounded-full transition-all duration-500 ease-out"
                                              style={{ width: `${job.progress || 0}%` }}
                                            ></div>
                                          </div>
                                        </div>

                                        {/* Files processed info */}
                                        <div className="text-xs text-blue-600 flex justify-between">
                                          <span>Files: {job.processed_files || 0}/{job.total_files || 0}</span>
                                        </div>

                                        {/* Status message */}
                                        {job.message && (
                                          <div className="mt-2 p-2 bg-white bg-opacity-60 rounded-md border border-blue-100">
                                            <div className="text-xs text-gray-700 truncate" title={job.message}>
                                              <i className="fas fa-info-circle text-blue-500 mr-1"></i>
                                              {job.message}
                                            </div>
                                          </div>
                                        )}
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          </div>
                        );
                      })}
                      {connection.repositories.length > 8 && (
                        <div className="text-sm text-gray-500 px-3 py-2 text-center">
                          +{connection.repositories.length - 8} more repositories...
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
          <div className="flex items-center gap-2">
            {remoteHostConnections.length > 0 && (
              <>
                <button
                  onClick={async () => {
                    try {
                      const response = await apiService.triggerSyncAll();
                      if (response.status === 'success') {
                        // Show immediate feedback with job information
                        const job = response.job || {};
                        const message = job.status === 'pending'
                          ? 'Sync started - preparing...'
                          : 'Sync started for all connections!';
                        alert(`${message} 🔄`);

                        // Refresh data immediately
                        await loadSyncHistory();
                        await loadActiveJobs();
                      }
                    } catch (error) {
                      alert(`Failed to start sync: ${error.message}`);
                    }
                  }}
                  className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors flex items-center gap-2"
                >
                  <i className="fas fa-sync-alt text-xs"></i>
                  Sync All
                </button>

                <button
                  onClick={async () => {
                    if (window.confirm('⚠️ This will cancel all active sync jobs. Are you sure?')) {
                      try {
                        const response = await apiService.emergencyCleanupJobs();
                        if (response.status === 'success') {
                          alert(`✅ Emergency cleanup completed! ${response.stale_count} jobs cancelled.`);
                          await loadSyncHistory();
                          await loadActiveJobs();
                        }
                      } catch (error) {
                        alert(`❌ Failed to cleanup jobs: ${error.message}`);
                      }
                    }
                  }}
                  className="px-3 py-1.5 text-sm bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors flex items-center gap-2"
                  title="Cancel all active sync jobs"
                >
                  <i className="fas fa-broom text-xs"></i>
                  Cleanup Jobs
                </button>
              </>
            )}
            <button
              onClick={() => setSelectedProvider(remoteHostProvider)}
              className="px-3 py-1.5 text-sm bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors flex items-center gap-2"
            >
              <i className="fas fa-plus text-xs"></i>
              Add Remote Host
            </button>
          </div>
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

                    {/* Sync Status - Simple status indicator only */}
                    {syncStatus[connection.id] && !activeJobs[connection.id]?.length && (
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        syncStatus[connection.id].status === 'success'
                          ? 'bg-green-100 text-green-800'
                          : syncStatus[connection.id].status === 'error'
                          ? 'bg-red-100 text-red-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        {syncStatus[connection.id].status === 'success' ? 'Synced' :
                         syncStatus[connection.id].status === 'error' ? 'Sync Failed' : 'Ready'}
                      </span>
                    )}

                    {/* Sync Button - only show when no active jobs */}
                    {(!activeJobs[connection.id] || activeJobs[connection.id].length === 0) && (
                      <button
                        onClick={() => handleSyncConnection(connection.id)}
                        className="px-3 py-1 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors text-sm"
                        title="Sync files from this connection"
                      >
                        <i className="fas fa-sync-alt mr-1"></i>
                        Sync
                      </button>
                    )}



                    {/* Active Jobs - Compact and elegant design */}
                    {activeJobs[connection.id] && activeJobs[connection.id].length > 0 && (
                      <div className="space-y-2">
                        {activeJobs[connection.id].map(job => (
                          <div key={job.id} className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-3 shadow-sm">
                            {/* Header with status and cancel button */}
                            <div className="flex items-center justify-between mb-3">
                              <div className="flex items-center gap-2">
                                <div className="relative">
                                  <i className="fas fa-sync-alt fa-spin text-blue-600 text-sm"></i>
                                  <div className="absolute -top-1 -right-1 w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                                </div>
                                <div>
                                  <span className="font-semibold text-blue-800 text-sm">
                                    {job.status === 'pending' ? 'Preparing...' : 'Syncing'}
                                  </span>
                                  <div className="text-xs text-blue-600">
                                    {job.processed_files || 0} of {job.total_files || 0} files
                                  </div>
                                </div>
                              </div>
                              <button
                                onClick={async () => {
                                  if (window.confirm(`Cancel sync job?`)) {
                                    try {
                                      const response = await apiService.cancelJob(job.id);
                                      if (response.status === 'success') {
                                        alert('✅ Job cancelled successfully!');
                                        await loadActiveJobs();
                                        await loadSyncHistory();
                                      }
                                    } catch (error) {
                                      alert(`❌ Failed to cancel job: ${error.message}`);
                                    }
                                  }
                                }}
                                className="group px-3 py-1.5 bg-white border border-red-200 text-red-600 rounded-md hover:bg-red-50 hover:border-red-300 transition-all duration-200 text-xs font-medium shadow-sm"
                                title="Cancel sync job"
                              >
                                <i className="fas fa-times mr-1 group-hover:scale-110 transition-transform"></i>
                                Cancel
                              </button>
                            </div>

                            {/* Compact Progress Bar */}
                            <div className="space-y-1">
                              <div className="flex justify-between items-center">
                                <span className="text-xs font-medium text-gray-600">Progress</span>
                                <span className="text-xs font-bold text-blue-700 bg-blue-100 px-2 py-0.5 rounded-full">
                                  {job.progress || 0}%
                                </span>
                              </div>
                              <div className="w-full bg-gray-200 rounded-full h-1.5 overflow-hidden">
                                <div
                                  className="bg-gradient-to-r from-blue-500 to-indigo-600 h-1.5 rounded-full transition-all duration-500 ease-out"
                                  style={{ width: `${job.progress || 0}%` }}
                                ></div>
                              </div>
                            </div>

                            {/* Status message */}
                            {job.message && (
                              <div className="mt-2 p-2 bg-white bg-opacity-60 rounded-md border border-blue-100">
                                <div className="text-xs text-gray-700 truncate" title={job.message}>
                                  <i className="fas fa-info-circle text-blue-500 mr-1"></i>
                                  {job.message}
                                </div>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}

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
                  {selectedProvider.config_fields?.map((field) => {
                    // Hide username and password fields for HTTP/HTTPS protocols
                    const selectedProtocol = connectionConfig.protocol;
                    const isHttpProtocol = selectedProtocol === 'http' || selectedProtocol === 'https';
                    const shouldHideField = isHttpProtocol && (field.name === 'username' || field.name === 'password');

                    if (shouldHideField) {
                      return null;
                    }

                    // Make username and password optional for HTTP/HTTPS
                    const isFieldRequired = field.required && !(isHttpProtocol && (field.name === 'username' || field.name === 'password'));

                    return (
                    <div key={field.name}>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        {field.label}
                        {isFieldRequired && <span className="text-red-500 ml-1">*</span>}
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
                    );
                  })}
                </div>

                <div className="flex gap-3 mt-6 justify-end">
                  <button
                    onClick={() => {
                      setSelectedProvider(null);
                      setConnectionConfig({});
                    }}
                    className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors"
                  >
                    Cancel
                  </button>
                  {selectedProvider.id === 'remote_host' && (
                    <button
                      onClick={() => handleTestConnectionInWizard()}
                      className="px-4 py-2 border border-blue-500 text-blue-500 rounded-md hover:bg-blue-50 transition-colors"
                    >
                      Test Connection
                    </button>
                  )}
                  <button
                    onClick={() => handleConnect(selectedProvider.id)}
                    className="px-6 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors"
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
