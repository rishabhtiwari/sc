"""
Configuration settings for GitHub Repository Syncer Job
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for GitHub Repository Syncer"""
    
    # Job Settings
    JOB_NAME = "github-repo-syncer"
    JOB_VERSION = "1.0.0"
    
    # Scheduling
    SYNC_FREQUENCY = os.getenv('SYNC_FREQUENCY', 'daily')  # daily, hourly, weekly
    SYNC_TIME = os.getenv('SYNC_TIME', '03:00')  # Time to run daily sync (24h format)
    
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
    MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE_MB', '10'))  # Max file size to sync (smaller for code files)
    BATCH_SIZE = int(os.getenv('BATCH_SIZE', '50'))  # Number of files to process in each batch
    
    # GitHub API Settings
    GITHUB_API_URL = 'https://api.github.com'
    GITHUB_RAW_URL = 'https://raw.githubusercontent.com'
    
    # Supported file extensions for code repositories
    SUPPORTED_EXTENSIONS = os.getenv('SUPPORTED_EXTENSIONS',
        # Programming languages
        '.py,.js,.ts,.jsx,.tsx,.java,.cpp,.c,.h,.hpp,.cs,.php,.rb,.go,.rs,.swift,.kt,.scala,'
        '.clj,.cljs,.hs,.ml,.fs,.erl,.ex,.exs,.lua,.pl,.r,.m,.sh,.bash,.zsh,.fish,'
        # Web technologies
        '.html,.htm,.css,.scss,.sass,.less,.vue,.svelte,.astro,'
        # Configuration and data
        '.json,.yaml,.yml,.xml,.toml,.ini,.cfg,.conf,.properties,.env,'
        # Documentation
        '.md,.rst,.txt,.adoc,.org,'
        # Database and query
        '.sql,.graphql,.gql,'
        # Build and deployment
        '.dockerfile,.docker-compose.yml,.makefile,.gradle,.maven,.sbt,.cargo.toml,'
        # Other common formats
        '.proto,.thrift,.avro'
    ).split(',')
    
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
        # Compiled/generated files
        '.class,.pyc,.pyo,.o,.obj,.lib,.a,.jar,'
        # IDE and editor files
        '.swp,.swo,.tmp,.temp,.bak,.backup,'
        # OS files
        '.DS_Store,.Thumbs.db,.desktop.ini'
    ).split(',')
    
    # Database
    DB_PATH = os.getenv('DB_PATH', './data/github_syncer.db')
    JOB_INSTANCES_DB_PATH = os.getenv('JOB_INSTANCES_DB_PATH', './data/job_instances.db')
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', './logs/github-repo-syncer.log')
    
    # Health check server
    HEALTH_CHECK_PORT = int(os.getenv('HEALTH_CHECK_PORT', '8092'))
    
    # Performance settings
    MAX_CONCURRENT_REPOS = int(os.getenv('MAX_CONCURRENT_REPOS', '3'))  # Max repositories to sync concurrently
    MAX_CONCURRENT_FILES = int(os.getenv('MAX_CONCURRENT_FILES', '10'))  # Max files to process concurrently per repo
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '30'))  # HTTP request timeout in seconds
    RETRY_ATTEMPTS = int(os.getenv('RETRY_ATTEMPTS', '3'))  # Number of retry attempts for failed requests
    RETRY_DELAY = int(os.getenv('RETRY_DELAY', '5'))  # Delay between retries in seconds
    
    # GitHub specific settings
    CLONE_DEPTH = int(os.getenv('CLONE_DEPTH', '1'))  # Git clone depth (1 for shallow clone)
    SKIP_BINARY_FILES = os.getenv('SKIP_BINARY_FILES', 'true').lower() == 'true'
    INCLUDE_HIDDEN_FILES = os.getenv('INCLUDE_HIDDEN_FILES', 'false').lower() == 'true'
    
    # Rate limiting
    GITHUB_API_RATE_LIMIT = int(os.getenv('GITHUB_API_RATE_LIMIT', '5000'))  # Requests per hour
    RATE_LIMIT_BUFFER = float(os.getenv('RATE_LIMIT_BUFFER', '0.1'))  # 10% buffer for rate limiting
    
    def validate(self):
        """Validate configuration settings"""
        errors = []
        
        # Validate required URLs
        required_urls = [
            ('MCP_SERVICE_URL', self.MCP_SERVICE_URL),
            ('API_SERVER_URL', self.API_SERVER_URL),
            ('EMBEDDING_SERVICE_URL', self.EMBEDDING_SERVICE_URL)
        ]
        
        for name, url in required_urls:
            if not url or not url.startswith('http'):
                errors.append(f"{name} must be a valid HTTP URL")
        
        # Validate numeric settings
        if self.MAX_FILE_SIZE_MB <= 0:
            errors.append("MAX_FILE_SIZE_MB must be positive")
            
        if self.BATCH_SIZE <= 0:
            errors.append("BATCH_SIZE must be positive")
            
        if self.HEALTH_CHECK_PORT <= 0 or self.HEALTH_CHECK_PORT > 65535:
            errors.append("HEALTH_CHECK_PORT must be between 1 and 65535")
            
        if self.MAX_CONCURRENT_REPOS <= 0:
            errors.append("MAX_CONCURRENT_REPOS must be positive")
            
        if self.MAX_CONCURRENT_FILES <= 0:
            errors.append("MAX_CONCURRENT_FILES must be positive")
        
        # Validate sync frequency
        valid_frequencies = ['daily', 'hourly', 'weekly']
        if self.SYNC_FREQUENCY not in valid_frequencies:
            errors.append(f"SYNC_FREQUENCY must be one of: {', '.join(valid_frequencies)}")
        
        # Validate sync time format (HH:MM)
        if self.SYNC_FREQUENCY in ['daily', 'weekly']:
            try:
                time_parts = self.SYNC_TIME.split(':')
                if len(time_parts) != 2:
                    raise ValueError()
                hour, minute = int(time_parts[0]), int(time_parts[1])
                if not (0 <= hour <= 23) or not (0 <= minute <= 59):
                    raise ValueError()
            except ValueError:
                errors.append("SYNC_TIME must be in HH:MM format (24-hour)")
        
        # Validate file extensions
        if not self.SUPPORTED_EXTENSIONS:
            errors.append("SUPPORTED_EXTENSIONS cannot be empty")
        
        # Create directories if they don't exist
        for path in [self.DB_PATH, self.JOB_INSTANCES_DB_PATH, self.LOG_FILE]:
            directory = os.path.dirname(path)
            if directory and not os.path.exists(directory):
                try:
                    os.makedirs(directory, exist_ok=True)
                except Exception as e:
                    errors.append(f"Cannot create directory {directory}: {str(e)}")
        
        if errors:
            raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")
        
        return True
    
    def get_github_headers(self, token: str = None):
        """Get headers for GitHub API requests"""
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': f'{self.JOB_NAME}/{self.JOB_VERSION}'
        }
        
        if token:
            headers['Authorization'] = f'token {token}'
            
        return headers
    
    def is_supported_file(self, filename: str) -> bool:
        """Check if file is supported for indexing"""
        if not filename:
            return False
            
        # Skip hidden files unless explicitly included
        if filename.startswith('.') and not self.INCLUDE_HIDDEN_FILES:
            return False
            
        # Get file extension
        _, ext = os.path.splitext(filename.lower())
        
        # Check if blacklisted
        if ext in self.BLACKLISTED_EXTENSIONS:
            return False
            
        # Check if supported (if no extension, allow if not blacklisted)
        if not ext:
            return True
            
        return ext in self.SUPPORTED_EXTENSIONS
    
    def __str__(self):
        """String representation of config (excluding sensitive data)"""
        return f"GitHubRepoSyncerConfig(version={self.JOB_VERSION}, frequency={self.SYNC_FREQUENCY})"
