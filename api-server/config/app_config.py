"""
Application Configuration
"""

import os


class AppConfig:
    """
    Base configuration class
    """
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    # Server settings
    HOST = os.environ.get('FLASK_HOST', '0.0.0.0')
    PORT = int(os.environ.get('FLASK_PORT', 8080))
    
    # API settings
    API_VERSION = "2.0.0"
    API_TITLE = "iChat API Server"
    
    # Chat settings
    CHAT_RESPONSE_DELAY = float(os.environ.get('CHAT_RESPONSE_DELAY', 0.5))
    MAX_MESSAGE_LENGTH = int(os.environ.get('MAX_MESSAGE_LENGTH', 100000))  # Increased to 100k characters
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

    # MCP Service integration
    MCP_SERVICE_HOST = os.environ.get('MCP_SERVICE_HOST', 'localhost')
    MCP_SERVICE_PORT = int(os.environ.get('MCP_SERVICE_PORT', 8089))

    # Code Generation Service integration (for backward compatibility)
    CODE_GENERATION_SERVICE_HOST = os.environ.get('CODE_GENERATION_SERVICE_HOST', 'localhost')
    CODE_GENERATION_SERVICE_PORT = int(os.environ.get('CODE_GENERATION_SERVICE_PORT', 8088))

    # LLM Service integration
    LLM_SERVICE_HOST = os.environ.get('LLM_SERVICE_HOST', 'localhost')
    LLM_SERVICE_PORT = int(os.environ.get('LLM_SERVICE_PORT', 8087))
    LLM_SERVICE_URL = os.environ.get('LLM_SERVICE_URL', 'http://localhost:8083')

    # Remote Host Syncer Service integration
    SYNCER_SERVICE_HOST = os.environ.get('SYNCER_SERVICE_HOST', 'job-remote-host-syncer')
    SYNCER_SERVICE_PORT = int(os.environ.get('SYNCER_SERVICE_PORT', 8091))


class DevelopmentConfig(AppConfig):
    """
    Development configuration
    """
    DEBUG = True
    TESTING = False


class ProductionConfig(AppConfig):
    """
    Production configuration
    """
    DEBUG = False
    TESTING = False
    CHAT_RESPONSE_DELAY = 0.1  # Faster responses in production


class TestingConfig(AppConfig):
    """
    Testing configuration
    """
    DEBUG = True
    TESTING = True
    CHAT_RESPONSE_DELAY = 0.0  # No delay in tests


# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
