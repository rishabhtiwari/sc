"""
Configuration settings for Remote Host Syncer Job
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for Remote Host Syncer"""
    
    # Job Settings
    JOB_NAME = "remote-host-syncer"
    JOB_VERSION = "1.0.0"
    
    # Scheduling
    SYNC_FREQUENCY = os.getenv('SYNC_FREQUENCY', 'daily')  # daily, hourly, weekly
    SYNC_TIME = os.getenv('SYNC_TIME', '02:00')  # Time to run daily sync (24h format)
    
    # Service URLs
    MCP_SERVICE_URL = os.getenv('MCP_SERVICE_URL', 'http://localhost:8089')
    API_SERVER_URL = os.getenv('API_SERVER_URL', 'http://localhost:8080')
    EMBEDDING_SERVICE_URL = os.getenv('EMBEDDING_SERVICE_URL', 'http://localhost:8085')
    
    # Docker networking - use service names when running in Docker
    if os.getenv('DOCKER_ENV', 'false').lower() == 'true':
        MCP_SERVICE_URL = 'http://ichat-mcp-service:8089'
        API_SERVER_URL = 'http://ichat-api-server:8080'
        EMBEDDING_SERVICE_URL = 'http://ichat-embedding-service:8085'
    
    # Sync Settings
    MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE_MB', '50'))  # Max file size to sync

    # File filtering is now handled by embedding service whitelist
    # Remote host syncer will send all files and let embedding service filter
    
    # Batch Processing
    BATCH_SIZE = int(os.getenv('BATCH_SIZE', '20'))  # Files to process in one batch (reduced for better cancellation responsiveness)
    MAX_CONCURRENT_CONNECTIONS = int(os.getenv('MAX_CONCURRENT_CONNECTIONS', '3'))
    
    # Retry Settings
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
    RETRY_DELAY_SECONDS = int(os.getenv('RETRY_DELAY_SECONDS', '5'))
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/remote-host-syncer.log')
    
    # Health Check
    HEALTH_CHECK_PORT = int(os.getenv('HEALTH_CHECK_PORT', '8091'))
    
    # Database (for tracking sync state)
    DB_PATH = os.getenv('DB_PATH', 'data/syncer.db')
    
    # Security
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', 'default-key-change-in-production')
    
    @classmethod
    def validate(cls):
        """Validate configuration"""
        required_vars = [
            'MCP_SERVICE_URL',
            'API_SERVER_URL', 
            'EMBEDDING_SERVICE_URL'
        ]
        
        missing = []
        for var in required_vars:
            if not getattr(cls, var):
                missing.append(var)
        
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")
        
        return True
