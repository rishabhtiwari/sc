"""
MCP Service Configuration
"""

import os


class MCPConfig:
    """
    MCP Service configuration class
    """
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'mcp-secret-key-change-in-production'
    DEBUG = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    
    # Server settings
    HOST = os.environ.get('FLASK_HOST', '0.0.0.0')
    PORT = int(os.environ.get('FLASK_PORT', 8089))
    
    # API settings
    API_VERSION = "1.0.0"
    API_TITLE = "iChat MCP Service"
    
    # MCP settings
    MAX_CONNECTIONS = int(os.environ.get('MAX_MCP_CONNECTIONS', 10))
    CONNECTION_TIMEOUT = int(os.environ.get('MCP_CONNECTION_TIMEOUT', 30))
    EXECUTION_TIMEOUT = int(os.environ.get('MCP_EXECUTION_TIMEOUT', 60))
    
    # Note: LLM integration is handled by the iChat API server, not MCP service
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    # Security settings
    ALLOWED_MCP_PROTOCOLS = os.environ.get('ALLOWED_MCP_PROTOCOLS', 'stdio,sse,websocket').split(',')
    ENABLE_MCP_VALIDATION = os.environ.get('ENABLE_MCP_VALIDATION', 'true').lower() == 'true'
    
    # Storage settings
    MCP_CONFIG_STORAGE_PATH = os.environ.get('MCP_CONFIG_STORAGE_PATH', '/app/data/mcp_configs')
    MCP_TEMP_PATH = os.environ.get('MCP_TEMP_PATH', '/app/temp')

    # Database configuration
    DATABASE_PATH = os.path.join(MCP_CONFIG_STORAGE_PATH, 'tokens.db')
    ENCRYPTION_KEY_PATH = os.path.join(MCP_CONFIG_STORAGE_PATH, 'encryption.key')

    # GitHub OAuth settings
    GITHUB_CLIENT_ID = os.environ.get('GITHUB_CLIENT_ID', '')
    GITHUB_CLIENT_SECRET = os.environ.get('GITHUB_CLIENT_SECRET', '')
    GITHUB_REDIRECT_URI = os.environ.get('GITHUB_REDIRECT_URI', 'http://localhost:8080/api/mcp/oauth/github/callback')

    # OAuth settings
    OAUTH_STATE_EXPIRY = int(os.environ.get('OAUTH_STATE_EXPIRY', 600))  # 10 minutes

    # Supported MCP providers
    SUPPORTED_MCP_PROVIDERS = {
        'github': {
            'name': 'GitHub',
            'description': 'Connect to GitHub repositories and perform Git operations',
            'oauth_required': True,
            'enabled': True,
            'config_fields': [
                {
                    'name': 'client_id',
                    'label': 'GitHub Client ID',
                    'type': 'text',
                    'required': True,
                    'description': 'OAuth App Client ID from GitHub Developer Settings'
                },
                {
                    'name': 'client_secret',
                    'label': 'GitHub Client Secret',
                    'type': 'password',
                    'required': True,
                    'description': 'OAuth App Client Secret from GitHub Developer Settings'
                },
                {
                    'name': 'redirect_uri',
                    'label': 'Redirect URI',
                    'type': 'text',
                    'required': True,
                    'default': 'http://localhost:8080/api/mcp/oauth/github/callback',
                    'description': 'OAuth redirect URI (must match GitHub App settings)'
                },
                {
                    'name': 'scope',
                    'label': 'OAuth Scopes',
                    'type': 'text',
                    'required': False,
                    'default': 'repo,read:user',
                    'description': 'Comma-separated list of OAuth scopes'
                }
            ]
        },
        # Future providers can be added here
        'gitlab': {
            'name': 'GitLab',
            'description': 'Connect to GitLab repositories (Coming Soon)',
            'oauth_required': True,
            'enabled': False
        },
        'filesystem': {
            'name': 'File System',
            'description': 'Access local file system (Coming Soon)',
            'oauth_required': False,
            'enabled': False
        }
    }

    # LLM service URL method removed - handled by iChat API server

    @classmethod
    def get_supported_providers(cls) -> dict:
        """Get supported MCP providers"""
        return {k: v for k, v in cls.SUPPORTED_MCP_PROVIDERS.items()
                if v.get('enabled', True)}

    @classmethod
    def get_provider_config(cls, provider: str) -> dict:
        """Get configuration for a specific provider"""
        return cls.SUPPORTED_MCP_PROVIDERS.get(provider, {})


class DevelopmentConfig(MCPConfig):
    """
    Development configuration
    """
    DEBUG = True
    LOG_LEVEL = 'DEBUG'


class ProductionConfig(MCPConfig):
    """
    Production configuration
    """
    DEBUG = False
    LOG_LEVEL = 'INFO'


class TestingConfig(MCPConfig):
    """
    Testing configuration
    """
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
    CONNECTION_TIMEOUT = 5
    EXECUTION_TIMEOUT = 10


# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
