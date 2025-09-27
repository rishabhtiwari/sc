"""
Vector Database Service Configuration
"""

import os
from typing import Dict, Any


class Config:
    """Configuration class for Vector Database Service"""
    
    # Server configuration
    HOST = '0.0.0.0'
    PORT = 8084
    DEBUG = False
    
    # ChromaDB configuration
    CHROMA_PERSIST_DIRECTORY = './data/chroma'
    CHROMA_COLLECTION_NAME = 'documents'
    
    # Embedding configuration
    EMBEDDING_MODEL = 'all-MiniLM-L6-v2'  # Sentence Transformers model
    EMBEDDING_DIMENSION = 384  # Dimension for all-MiniLM-L6-v2
    
    # Document processing
    DEFAULT_CHUNK_SIZE = 1000
    DEFAULT_CHUNK_OVERLAP = 200
    MAX_DOCUMENT_SIZE = 10 * 1024 * 1024  # 10MB
    
    # Search configuration
    DEFAULT_SEARCH_RESULTS = 5
    MAX_SEARCH_RESULTS = 50
    DEFAULT_SIMILARITY_THRESHOLD = 0.7
    
    # Performance settings
    BATCH_SIZE = 100
    MAX_CONCURRENT_REQUESTS = 10
    
    # Logging
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    @classmethod
    def get_chroma_config(cls) -> Dict[str, Any]:
        """Get ChromaDB configuration"""
        return {
            'persist_directory': cls.CHROMA_PERSIST_DIRECTORY,
            'collection_name': cls.CHROMA_COLLECTION_NAME
        }
    
    @classmethod
    def get_embedding_config(cls) -> Dict[str, Any]:
        """Get embedding configuration"""
        return {
            'model_name': cls.EMBEDDING_MODEL,
            'dimension': cls.EMBEDDING_DIMENSION
        }
    
    @classmethod
    def get_processing_config(cls) -> Dict[str, Any]:
        """Get document processing configuration"""
        return {
            'chunk_size': cls.DEFAULT_CHUNK_SIZE,
            'chunk_overlap': cls.DEFAULT_CHUNK_OVERLAP,
            'max_document_size': cls.MAX_DOCUMENT_SIZE,
            'batch_size': cls.BATCH_SIZE
        }
    
    @classmethod
    def get_search_config(cls) -> Dict[str, Any]:
        """Get search configuration"""
        return {
            'default_results': cls.DEFAULT_SEARCH_RESULTS,
            'max_results': cls.MAX_SEARCH_RESULTS,
            'similarity_threshold': cls.DEFAULT_SIMILARITY_THRESHOLD
        }
    
    @classmethod
    def get_summary(cls) -> Dict[str, Any]:
        """Get configuration summary"""
        return {
            'server': {
                'host': cls.HOST,
                'port': cls.PORT,
                'debug': cls.DEBUG
            },
            'database': {
                'type': 'ChromaDB',
                'persist_directory': cls.CHROMA_PERSIST_DIRECTORY,
                'collection': cls.CHROMA_COLLECTION_NAME
            },
            'embedding': {
                'model': cls.EMBEDDING_MODEL,
                'dimension': cls.EMBEDDING_DIMENSION
            },
            'processing': {
                'chunk_size': cls.DEFAULT_CHUNK_SIZE,
                'chunk_overlap': cls.DEFAULT_CHUNK_OVERLAP,
                'batch_size': cls.BATCH_SIZE
            }
        }
