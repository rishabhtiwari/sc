"""
Configuration settings for Code Generation Service
"""
import os
from typing import Dict, Any, List


class Config:
    """Configuration class for Code Generation Service"""
    
    # Service Information
    SERVICE_NAME = "Code Generation Service"
    SERVICE_VERSION = "1.0.0"
    SERVICE_DESCRIPTION = "Code repository connector and analysis service with LLM-powered code generation"
    
    # Server Configuration
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 8088))
    DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
    
    # CORS Configuration
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')
    
    # Gunicorn Configuration
    USE_GUNICORN = os.getenv('USE_GUNICORN', 'false').lower() == 'true'
    GUNICORN_WORKERS = int(os.getenv('GUNICORN_WORKERS', 2))
    
    # External LLM Services Configuration
    LLM_SERVICE_HOST = os.getenv('LLM_SERVICE_HOST', 'localhost')
    LLM_SERVICE_PORT = int(os.getenv('LLM_SERVICE_PORT', 8082))
    LLM_PROMPT_SERVICE_HOST = os.getenv('LLM_PROMPT_SERVICE_HOST', 'localhost')
    LLM_PROMPT_SERVICE_PORT = int(os.getenv('LLM_PROMPT_SERVICE_PORT', 8083))

    # Embedding Service Configuration
    EMBEDDING_SERVICE_HOST = os.getenv('EMBEDDING_SERVICE_HOST', 'ichat-embedding-service')
    EMBEDDING_SERVICE_PORT = int(os.getenv('EMBEDDING_SERVICE_PORT', 8085))

    # Service URLs
    @classmethod
    def get_llm_service_url(cls, endpoint: str = '') -> str:
        """Get LLM service URL with optional endpoint"""
        base_url = f"http://{cls.LLM_SERVICE_HOST}:{cls.LLM_SERVICE_PORT}"
        return f"{base_url}/{endpoint.lstrip('/')}" if endpoint else base_url

    @classmethod
    def get_llm_prompt_service_url(cls, endpoint: str = '') -> str:
        """Get LLM prompt service URL with optional endpoint"""
        base_url = f"http://{cls.LLM_PROMPT_SERVICE_HOST}:{cls.LLM_PROMPT_SERVICE_PORT}"
        return f"{base_url}/{endpoint.lstrip('/')}" if endpoint else base_url

    @classmethod
    def get_embedding_service_url(cls, endpoint: str = '') -> str:
        """Get embedding service URL with optional endpoint"""
        base_url = f"http://{cls.EMBEDDING_SERVICE_HOST}:{cls.EMBEDDING_SERVICE_PORT}"
        return f"{base_url}/{endpoint.lstrip('/')}" if endpoint else base_url
    
    # Code Repository Configuration
    SUPPORTED_REPO_TYPES = ['git', 'local', 'github', 'gitlab']
    MAX_REPO_SIZE_MB = int(os.getenv('MAX_REPO_SIZE_MB', 500))  # 500MB limit
    TEMP_REPO_DIR = os.getenv('TEMP_REPO_DIR', './temp/repositories')

    # GitHub OAuth Configuration
    GITHUB_CLIENT_ID = os.getenv('GITHUB_CLIENT_ID', '')
    GITHUB_CLIENT_SECRET = os.getenv('GITHUB_CLIENT_SECRET', '')
    GITHUB_REDIRECT_URI = os.getenv('GITHUB_REDIRECT_URI', 'http://localhost:8088/code/auth/github/callback')
    GITHUB_SCOPE = os.getenv('GITHUB_SCOPE', 'repo,read:user')  # repo access and user info

    # OAuth Session Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
    SESSION_TIMEOUT = int(os.getenv('SESSION_TIMEOUT', 3600))  # 1 hour
    
    # Code Analysis Configuration
    SUPPORTED_LANGUAGES = [
        'python', 'java', 'javascript', 'typescript', 'go', 'rust', 
        'cpp', 'c', 'csharp', 'php', 'ruby', 'swift', 'kotlin'
    ]
    MAX_FILE_SIZE_KB = int(os.getenv('MAX_FILE_SIZE_KB', 1024))  # 1MB per file
    ANALYSIS_TIMEOUT = int(os.getenv('ANALYSIS_TIMEOUT', 300))  # 5 minutes
    
    # Code Generation Configuration
    DEFAULT_GENERATION_TEMPERATURE = float(os.getenv('DEFAULT_GENERATION_TEMPERATURE', 0.2))
    DEFAULT_MAX_TOKENS = int(os.getenv('DEFAULT_MAX_TOKENS', 2048))
    CODE_GENERATION_TIMEOUT = int(os.getenv('CODE_GENERATION_TIMEOUT', 120))  # 2 minutes
    
    # File Extensions Mapping
    LANGUAGE_EXTENSIONS = {
        'python': ['.py', '.pyx', '.pyi'],
        'java': ['.java'],
        'javascript': ['.js', '.jsx', '.mjs'],
        'typescript': ['.ts', '.tsx'],
        'go': ['.go'],
        'rust': ['.rs'],
        'cpp': ['.cpp', '.cc', '.cxx', '.c++', '.hpp', '.hh', '.hxx', '.h++'],
        'c': ['.c', '.h'],
        'csharp': ['.cs'],
        'php': ['.php'],
        'ruby': ['.rb'],
        'swift': ['.swift'],
        'kotlin': ['.kt', '.kts']
    }
    
    # Ignore Patterns for Code Analysis
    IGNORE_PATTERNS = [
        '*.pyc', '*.pyo', '*.pyd', '__pycache__', '.git', '.svn', '.hg',
        'node_modules', '.npm', 'bower_components', 'dist', 'build',
        '*.class', '*.jar', '*.war', 'target', '.gradle', 'gradle',
        '*.o', '*.so', '*.dll', '*.exe', '.vscode', '.idea',
        '*.log', '*.tmp', '*.temp', '.DS_Store', 'Thumbs.db'
    ]
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FILE = os.getenv('LOG_FILE', 'logs/code-generation-service.log')
    
    # Request Timeouts
    HTTP_TIMEOUT = int(os.getenv('HTTP_TIMEOUT', 30))
    LLM_REQUEST_TIMEOUT = int(os.getenv('LLM_REQUEST_TIMEOUT', 120))
    
    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        config_dict = {}
        for key, value in cls.__dict__.items():
            if not key.startswith('_') and not callable(value):
                config_dict[key] = value
        return config_dict
    
    @classmethod
    def get_language_from_extension(cls, file_extension: str) -> str:
        """Get programming language from file extension"""
        file_extension = file_extension.lower()
        for language, extensions in cls.LANGUAGE_EXTENSIONS.items():
            if file_extension in extensions:
                return language
        return 'unknown'
    
    @classmethod
    def is_supported_file(cls, filename: str) -> bool:
        """Check if file is supported for analysis"""
        _, ext = os.path.splitext(filename)
        return cls.get_language_from_extension(ext) != 'unknown'
