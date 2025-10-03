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

    # Blacklisted file extensions (files to reject for embedding)
    BLACKLISTED_EXTENSIONS = {
        # Disk/VM images
        'iso', 'img', 'vdi', 'vmdk', 'qcow2', 'vhd', 'wim',
        # Binary executables
        'exe', 'dll', 'so', 'dylib', 'bin', 'app', 'deb', 'rpm', 'msi', 'dmg', 'pkg', 'snap', 'run',
        # Archive files
        'zip', 'rar', '7z', 'tar', 'gz', 'bz2', 'xz', 'tar.gz', 'tar.bz2', 'tar.xz', 'tgz', 'tbz2', 'txz',
        # Audio files
        'mp3', 'wav', 'flac', 'aac', 'ogg', 'wma', 'm4a', 'opus', 'aiff', 'au',
        # Video files
        'mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mkv', 'm4v', '3gp', 'mpg', 'mpeg', 'm2v', 'divx', 'xvid'
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
    MAX_CHUNKS_PER_DOCUMENT = int(os.getenv('MAX_CHUNKS_PER_DOCUMENT', 1000))
    
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
                'blacklisted_extensions': list(cls.BLACKLISTED_EXTENSIONS)
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
            'timeouts': {
                'request_timeout': cls.REQUEST_TIMEOUT,
                'ocr_timeout': cls.OCR_TIMEOUT,
                'vector_db_timeout': cls.VECTOR_DB_TIMEOUT
            }
        }
    
    @classmethod
    def is_allowed_file(cls, filename: str) -> bool:
        """Check if file extension is allowed (not blacklisted)"""
        if not filename:
            return False
        if '.' not in filename:
            return True  # Files without extensions are allowed

        filename_lower = filename.lower()

        # Check compound extensions first (e.g., .tar.gz, .tar.bz2)
        for ext in cls.BLACKLISTED_EXTENSIONS:
            if '.' in ext and filename_lower.endswith('.' + ext):
                return False

        # Check single extension
        extension = filename.rsplit('.', 1)[1].lower()
        return extension not in cls.BLACKLISTED_EXTENSIONS
    
    @classmethod
    def get_ocr_url(cls, endpoint: str = '') -> str:
        """Get full OCR service URL"""
        return f"{cls.OCR_SERVICE_URL}{endpoint}"
    
    @classmethod
    def get_vector_db_url(cls, endpoint: str = '') -> str:
        """Get full Vector DB URL"""
        return f"{cls.VECTOR_DB_URL}{endpoint}"
