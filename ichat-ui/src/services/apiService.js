class ApiService {
  constructor() {
    this.baseURL = process.env.NODE_ENV === 'production' 
      ? 'http://localhost:8080/api' 
      : 'http://localhost:8080/api';
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;

    const defaultOptions = {
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      ...options,
    };

    try {
      const response = await fetch(url, defaultOptions);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  async checkHealth() {
    try {
      const response = await this.request('/health');
      return response;
    } catch (error) {
      console.error('Health check failed:', error);
      return { status: 'error', error: error.message };
    }
  }

  async sendChatMessage(message, options = {}) {
    const payload = {
      message: message.trim(),
      timestamp: Date.now(),
      client: 'ichat-ui',
      use_rag: options.useRag || false,
      session_id: options.sessionId || `web-session-${Date.now()}`,
      conversation_id: options.conversationId || null,
      ...options
    };

    return this.request('/chat', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  /**
   * Stream chat message with real-time response
   * @param {string} message - The message to send
   * @param {Object} options - Options for the request
   * @param {Function} onChunk - Callback for each streaming chunk
   * @param {Function} onComplete - Callback when streaming is complete
   * @param {Function} onError - Callback for errors
   */
  async streamChatMessage(message, options = {}, onChunk, onComplete, onError) {
    const payload = {
      message: message.trim(),
      timestamp: Date.now(),
      client: 'ichat-ui',
      use_rag: options.useRag !== false, // Default to true for streaming
      session_id: options.sessionId || `web-session-${Date.now()}`,
      conversation_id: options.conversationId || null,
      ...options
    };

    const url = `${this.baseURL}/chat/stream`;

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
        },
        body: JSON.stringify(payload),
        signal: options.signal, // Support abort signal
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();

        if (done) {
          if (onComplete) onComplete();
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');

        // Keep the last incomplete line in the buffer
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.substring(6));
              if (onChunk) onChunk(data);
            } catch (e) {
              console.error('Error parsing streaming data:', e);
            }
          }
        }
      }
    } catch (error) {
      console.error('Streaming request failed:', error);
      if (onError) onError(error);
      throw error;
    }
  }

  async uploadDocument(file, options = {}) {
    const formData = new FormData();
    formData.append('file', file);
    
    Object.keys(options).forEach(key => {
      formData.append(key, options[key]);
    });

    return this.request('/documents/upload', {
      method: 'POST',
      body: formData,
      headers: {
        // Remove Content-Type to let browser set it with boundary
      },
    });
  }

  async getDocuments() {
    return this.request('/documents');
  }

  async deleteDocument(documentId) {
    return this.request(`/documents/${documentId}`, {
      method: 'DELETE',
    });
  }

  // MCP Service methods
  async getMCPProviders() {
    // Get available MCP provider types for connection
    return this.request('/mcp/providers');
  }

  async getMCPConnectedProviders() {
    // Get connected MCP providers via OAuth tokens
    return this.request('/mcp/tokens');
  }

  // Deprecated - use the method below with token_id
  async getMCPProviderResourcesOld(providerId) {
    return this.request(`/mcp/providers/${providerId}/resources`);
  }

  async connectMCPProvider(providerId, config) {
    return this.request(`/mcp/providers/${providerId}/connect`, {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  async disconnectMCPProvider(providerId, data = null) {
    return this.request(`/mcp/providers/${providerId}/disconnect`, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async testMCPProviderConnection(providerId, connectionId) {
    return this.request(`/mcp/providers/${providerId}/connections/${connectionId}/test`, {
      method: 'POST',
    });
  }

  async getRemoteHostConnections() {
    return this.request('/mcp/providers/remote_host/connections');
  }

  async configureMCPProvider(providerId, config) {
    return this.request(`/mcp/provider/${providerId}/config`, {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  async startMCPProviderAuth(providerId, data) {
    return this.request(`/mcp/provider/${providerId}/auth`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getMCPTokens() {
    return this.request('/mcp/tokens');
  }

  async revokeMCPToken(tokenId) {
    return this.request(`/mcp/token/${tokenId}/revoke`, {
      method: 'POST',
    });
  }

  // Context/Repository methods
  async getRepositories() {
    return this.request('/context/repositories');
  }

  async addRepository(repoConfig) {
    return this.request('/context/repositories', {
      method: 'POST',
      body: JSON.stringify(repoConfig),
    });
  }

  async removeRepository(repoId) {
    return this.request(`/context/repositories/${repoId}`, {
      method: 'DELETE',
    });
  }

  // Code Generation Service methods (proxied through api-server)
  async connectRepository(repoConfig) {
    return this.request('/code/connect', {
      method: 'POST',
      body: JSON.stringify(repoConfig),
    });
  }

  async analyzeRepository(repositoryId, language) {
    return this.request('/code/analyze', {
      method: 'POST',
      body: JSON.stringify({
        repository_id: repositoryId,
        language: language
      }),
    });
  }

  async getRepositoryFiles(repositoryId) {
    return this.request(`/code/files?repository_id=${repositoryId}`);
  }

  async cleanupRepository(repositoryId) {
    return this.request('/code/cleanup', {
      method: 'POST',
      body: JSON.stringify({ repository_id: repositoryId }),
    });
  }

  // MCP Provider Resource methods
  async getMCPProviderResources(providerId, tokenId) {
    return this.request(`/mcp/provider/${providerId}/resources?token_id=${tokenId}`);
  }

  async addMCPResourceToContext(providerId, tokenId, resourceData) {
    // Extract the actual resource data - it might be nested under resource_data
    const actualResource = resourceData.resource_data || resourceData;

    console.log('🔍 addMCPResourceToContext called with:', {
      providerId,
      tokenId,
      resourceData,
      actualResource,
      clone_url: actualResource.clone_url,
      default_branch: actualResource.default_branch
    });

    const requestBody = {
      type: 'git',
      url: actualResource.clone_url,
      branch: actualResource.default_branch || 'main',
      session_id: tokenId,
      credentials: {
        username: '',
        token: ''
      }
    };

    console.log('📤 Sending request body:', requestBody);

    return this.request('/code/connect', {
      method: 'POST',
      body: JSON.stringify(requestBody),
    });
  }

  async getConnectedRepositories() {
    return this.request('/code/repositories');
  }

  async getMCPResources() {
    // For now, MCP resources are stored as repositories with MCP provider info
    // In the future, this might be a separate endpoint
    return this.request('/code/repositories');
  }

  async getMCPContextResources() {
    return this.request('/code/repositories');
  }

  async removeMCPResourceFromContext(resourceId) {
    return this.request(`/code/repositories/${resourceId}`, {
      method: 'DELETE',
    });
  }
}

export default new ApiService();
