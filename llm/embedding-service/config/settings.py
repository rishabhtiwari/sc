"""
Configuration settings for Embedding Service

This module contains all configuration settings for the embedding service
including server settings, external service URLs, and processing parameters.
"""

import os
from typing import Dict, Any


class Config:
    """Configuration class for Embedding Service"""

    # Server Configuration
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 8085))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

    # File Upload Configuration
    MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE_MB', 50))
    MAX_CONTENT_LENGTH = MAX_FILE_SIZE_MB * 1024 * 1024  # Convert to bytes

    # Whitelisted file extensions (files allowed for embedding)
    WHITELISTED_EXTENSIONS = {
        # Programming languages
        'py', 'java', 'js', 'ts', 'jsx', 'tsx', 'c', 'cpp', 'cc', 'cxx', 'h', 'hpp', 'hxx',
        'cs', 'php', 'rb', 'go', 'rs', 'swift', 'kt', 'scala', 'clj', 'cljs', 'hs', 'ml', 'fs',
        'r', 'jl', 'dart', 'lua', 'perl', 'pl', 'sh', 'bash', 'zsh', 'fish', 'ps1', 'bat', 'cmd',
        # Web technologies
        'html', 'htm', 'css', 'scss', 'sass', 'less', 'vue', 'svelte', 'xml', 'xhtml', 'xsl', 'xslt',
        # Configuration and data files
        'json', 'yaml', 'yml', 'toml', 'ini', 'cfg', 'conf', 'config', 'properties', 'env',
        'dockerfile', 'makefile', 'cmake', 'gradle', 'maven', 'pom', 'sbt', 'build',
        # Documentation and text
        'md', 'markdown', 'rst', 'txt', 'text', 'log', 'readme', 'changelog', 'license',
        'tex', 'latex', 'bib', 'org', 'adoc', 'asciidoc',
        # Document formats
        'pdf', 'doc', 'docx', 'odt', 'rtf', 'pages',
        # Spreadsheets and presentations
        'xls', 'xlsx', 'ods', 'csv', 'tsv', 'ppt', 'pptx', 'odp', 'key',
        # Image formats
        'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'tif', 'webp', 'svg', 'ico',
        # Database and query files
        'sql', 'sqlite', 'db', 'dbf', 'mdb', 'accdb',
        # Other common development files
        'gitignore', 'gitattributes', 'editorconfig', 'log', 'txt', 'text'
                                                                    'tsconfig', 'jsconfig', 'package', 'composer',
        'requirements', 'pipfile', 'poetry',
        'cargo', 'gemfile', 'podfile', 'pubspec', 'mix', 'rebar', 'stack'
    }

    # External Services
    OCR_SERVICE_URL = os.getenv('OCR_SERVICE_URL', 'http://localhost:8082')
    VECTOR_DB_URL = os.getenv('VECTOR_DB_URL', 'http://localhost:8084')

    # OCR Service Endpoints
    OCR_EXTRACT_ENDPOINT = '/ocr/extract'
    OCR_HEALTH_ENDPOINT = '/health'

    # Vector DB Endpoints
    VECTOR_DB_DOCUMENTS_ENDPOINT = '/vector/documents'
    VECTOR_DB_SEARCH_ENDPOINT = '/vector/search'
    VECTOR_DB_HEALTH_ENDPOINT = '/health'
    VECTOR_DB_COLLECTIONS_ENDPOINT = '/vector/collections'

    # Text Processing Configuration
    CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', 1000))
    CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', 200))
    MIN_CHUNK_SIZE = int(os.getenv('MIN_CHUNK_SIZE', 100))
    MAX_CHUNKS_PER_DOCUMENT = int(os.getenv('MAX_CHUNKS_PER_DOCUMENT', 20))

    # Search Configuration
    DEFAULT_SEARCH_LIMIT = int(os.getenv('DEFAULT_SEARCH_LIMIT', 20))
    MIN_SIMILARITY_THRESHOLD = float(os.getenv('MIN_SIMILARITY_THRESHOLD', 0.4))
    DEFAULT_USE_HYBRID = os.getenv('DEFAULT_USE_HYBRID', 'true').lower() == 'true'

    # Processing Configuration
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', 300))  # 5 minutes
    OCR_TIMEOUT = int(os.getenv('OCR_TIMEOUT', 300))  # 5 minutes
    VECTOR_DB_TIMEOUT = int(os.getenv('VECTOR_DB_TIMEOUT', 300))  # 5 minutes

    # Document ID Configuration
    DOCUMENT_ID_PREFIX = os.getenv('DOCUMENT_ID_PREFIX', 'doc')
    DOCUMENT_ID_LENGTH = int(os.getenv('DOCUMENT_ID_LENGTH', 12))

    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = os.getenv('LOG_FORMAT',
                           '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Health Check Configuration
    HEALTH_CHECK_INTERVAL = int(os.getenv('HEALTH_CHECK_INTERVAL', 30))

    # Retry Configuration
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', 3))
    RETRY_DELAY = float(os.getenv('RETRY_DELAY', 1.0))

    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """Get all configuration as a dictionary"""
        return {
            'server': {
                'host': cls.HOST,
                'port': cls.PORT,
                'debug': cls.DEBUG
            },
            'file_upload': {
                'max_size_mb': cls.MAX_FILE_SIZE_MB,
                'whitelisted_extensions': list(cls.WHITELISTED_EXTENSIONS)
            },
            'external_services': {
                'ocr_service': cls.OCR_SERVICE_URL,
                'vector_db': cls.VECTOR_DB_URL
            },
            'text_processing': {
                'chunk_size': cls.CHUNK_SIZE,
                'chunk_overlap': cls.CHUNK_OVERLAP,
                'min_chunk_size': cls.MIN_CHUNK_SIZE,
                'max_chunks_per_document': cls.MAX_CHUNKS_PER_DOCUMENT
            },
            'search': {
                'default_limit': cls.DEFAULT_SEARCH_LIMIT,
                'min_similarity_threshold': cls.MIN_SIMILARITY_THRESHOLD,
                'default_use_hybrid': cls.DEFAULT_USE_HYBRID
            },
            'timeouts': {
                'request_timeout': cls.REQUEST_TIMEOUT,
                'ocr_timeout': cls.OCR_TIMEOUT,
                'vector_db_timeout': cls.VECTOR_DB_TIMEOUT
            }
        }

    @classmethod
    def is_allowed_file(cls, filename: str) -> bool:
        """Check if file extension is allowed (whitelisted)"""
        if not filename:
            return False
        if '.' not in filename:
            return False  # Files without extensions are not allowed in whitelist mode

        filename_lower = filename.lower()

        # Check compound extensions first (e.g., .tar.gz, .tar.bz2)
        for ext in cls.WHITELISTED_EXTENSIONS:
            if '.' in ext and filename_lower.endswith('.' + ext):
                return True

        # Check single extension
        extension = filename.rsplit('.', 1)[1].lower()
        return extension in cls.WHITELISTED_EXTENSIONS

    @classmethod
    def get_ocr_url(cls, endpoint: str = '') -> str:
        """Get full OCR service URL"""
        return f"{cls.OCR_SERVICE_URL}{endpoint}"

    @classmethod
    def get_vector_db_url(cls, endpoint: str = '') -> str:
        """Get full Vector DB URL"""
        return f"{cls.VECTOR_DB_URL}{endpoint}"
