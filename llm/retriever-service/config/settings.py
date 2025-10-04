"""
Configuration settings for the Retriever Service
"""
import os
from typing import Dict, Any


class Config:
    """Configuration class for retriever service"""

    # Service Configuration
    SERVICE_NAME = "Retriever Service"
    SERVICE_VERSION = "1.0.0"
    SERVICE_DESCRIPTION = "Document retrieval and RAG service for iChat"

    # Server Configuration
    HOST = os.getenv('RETRIEVER_HOST', '0.0.0.0')
    PORT = int(os.getenv('RETRIEVER_PORT', 8086))
    DEBUG = os.getenv('RETRIEVER_DEBUG', 'false').lower() == 'true'

    # Environment
    ENVIRONMENT = os.getenv('RETRIEVER_ENV', 'development')

    # External Services
    EMBEDDING_SERVICE_URL = os.getenv('EMBEDDING_SERVICE_URL', 'http://localhost:8085')
    VECTOR_DB_URL = os.getenv('VECTOR_DB_URL', 'http://localhost:8084')

    # Embedding Service Endpoints
    EMBEDDING_SEARCH_ENDPOINT = '/embed/search'
    EMBEDDING_DOCUMENT_ENDPOINT = '/embed/document'
    EMBEDDING_HEALTH_ENDPOINT = '/health'

    # Vector DB Endpoints
    VECTOR_DB_SEARCH_ENDPOINT = '/vector/search'
    VECTOR_DB_DOCUMENTS_ENDPOINT = '/vector/documents'
    VECTOR_DB_HEALTH_ENDPOINT = '/health'

    # Retrieval Configuration
    DEFAULT_SEARCH_LIMIT = int(os.getenv('DEFAULT_SEARCH_LIMIT', 20))
    MAX_SEARCH_LIMIT = int(os.getenv('MAX_SEARCH_LIMIT', 20))
    MIN_SIMILARITY_THRESHOLD = float(os.getenv('MIN_SIMILARITY_THRESHOLD', 0.4))
    USE_HYBRID_SEARCH = os.getenv('USE_HYBRID_SEARCH', 'true').lower() == 'true'
    DEFAULT_USE_HYBRID = os.getenv('DEFAULT_USE_HYBRID', 'true').lower() == 'true'

    # RAG Configuration
    CONTEXT_WINDOW_SIZE = int(os.getenv('CONTEXT_WINDOW_SIZE', 4000))
    MAX_CONTEXT_CHUNKS = int(os.getenv('MAX_CONTEXT_CHUNKS', 20))
    CHUNK_OVERLAP_THRESHOLD = float(os.getenv('CHUNK_OVERLAP_THRESHOLD', 0.8))

    # Request Timeouts (seconds)
    EMBEDDING_TIMEOUT = int(os.getenv('EMBEDDING_TIMEOUT', 300))
    VECTOR_DB_TIMEOUT = int(os.getenv('VECTOR_DB_TIMEOUT', 300))

    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FILE = os.getenv('LOG_FILE', '/app/logs/retriever-service.log')

    # CORS Configuration
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')

    @classmethod
    def get_embedding_url(cls, endpoint: str) -> str:
        """Get full URL for embedding service endpoint"""
        return f"{cls.EMBEDDING_SERVICE_URL}{endpoint}"

    @classmethod
    def get_vector_db_url(cls, endpoint: str) -> str:
        """Get full URL for vector database endpoint"""
        return f"{cls.VECTOR_DB_URL}{endpoint}"

    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'service_name': cls.SERVICE_NAME,
            'service_version': cls.SERVICE_VERSION,
            'service_description': cls.SERVICE_DESCRIPTION,
            'host': cls.HOST,
            'port': cls.PORT,
            'debug': cls.DEBUG,
            'environment': cls.ENVIRONMENT,
            'embedding_service_url': cls.EMBEDDING_SERVICE_URL,
            'vector_db_url': cls.VECTOR_DB_URL,
            'default_search_limit': cls.DEFAULT_SEARCH_LIMIT,
            'max_search_limit': cls.MAX_SEARCH_LIMIT,
            'min_similarity_threshold': cls.MIN_SIMILARITY_THRESHOLD,
            'use_hybrid_search': cls.USE_HYBRID_SEARCH,
            'default_use_hybrid': cls.DEFAULT_USE_HYBRID,
            'context_window_size': cls.CONTEXT_WINDOW_SIZE,
            'max_context_chunks': cls.MAX_CONTEXT_CHUNKS,
            'log_level': cls.LOG_LEVEL
        }
