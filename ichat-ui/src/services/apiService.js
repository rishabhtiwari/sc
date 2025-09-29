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
    return this.request('/mcp/providers');
  }

  async connectMCPProvider(providerId, config) {
    return this.request(`/mcp/providers/${providerId}/connect`, {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  async disconnectMCPProvider(providerId) {
    return this.request(`/mcp/providers/${providerId}/disconnect`, {
      method: 'POST',
    });
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
}

export default new ApiService();
