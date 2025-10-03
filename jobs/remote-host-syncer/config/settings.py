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

    # Blacklisted file extensions (files to skip during indexing)
    BLACKLISTED_EXTENSIONS = os.getenv('BLACKLISTED_EXTENSIONS',
        # Video files
        '.mp4,.avi,.mov,.wmv,.flv,.webm,.mkv,.m4v,.3gp,.mpg,.mpeg,.m2v,.divx,.xvid,'
        # Audio files
        '.mp3,.wav,.flac,.aac,.ogg,.wma,.m4a,.opus,.aiff,.au,'
        # Image files (large binary)
        '.jpg,.jpeg,.png,.gif,.bmp,.tiff,.tif,.webp,.ico,.svg,.psd,.ai,.eps,'
        # Archive files
        '.zip,.rar,.7z,.tar,.gz,.bz2,.xz,.tar.gz,.tar.bz2,.tar.xz,.tgz,.tbz2,.txz,'
        # Binary executables
        '.exe,.dll,.so,.dylib,.bin,.app,.deb,.rpm,.msi,.dmg,.pkg,.snap,'
        # Office/PDF files (binary)
        '.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.odt,.ods,.odp,'
        # Database files
        '.db,.sqlite,.sqlite3,.mdb,.accdb,'
        # Other binary formats
        '.iso,.img,.vdi,.vmdk,.qcow2,.vhd,.wim'
    ).split(',')

    # Remove any empty strings and strip whitespace
    BLACKLISTED_EXTENSIONS = [ext.strip() for ext in BLACKLISTED_EXTENSIONS if ext.strip()]
    
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
