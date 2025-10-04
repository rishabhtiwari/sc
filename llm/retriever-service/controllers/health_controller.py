"""
Health controller for retriever service
"""
import time
from typing import Dict, Tuple, Any
from services.retriever_service import RetrieverService
from config.settings import Config
from utils.logger import setup_logger


class HealthController:
    """Controller for health check endpoints"""
    
    def __init__(self):
        self.retriever_service = RetrieverService()
        self.logger = setup_logger('health-controller')
    
    def health_check(self) -> Tuple[Dict[str, Any], int]:
        """
        Perform comprehensive health check
        
        Returns:
            Tuple of (response_dict, status_code)
        """
        try:
            health_result = self.retriever_service.health_check()
            
            # Determine HTTP status code based on health
            status_code = 200 if health_result.get("status") == "healthy" else 503
            
            return health_result, status_code
            
        except Exception as e:
            self.logger.error(f"Health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": int(time.time() * 1000)
            }, 503
    
    def service_info(self) -> Tuple[Dict[str, Any], int]:
        """
        Get service information
        
        Returns:
            Tuple of (response_dict, status_code)
        """
        try:
            return {
                "name": Config.SERVICE_NAME,
                "version": Config.SERVICE_VERSION,
                "description": Config.SERVICE_DESCRIPTION,
                "status": "running",
                "endpoints": {
                    "search": "/retrieve/search (POST)",
                    "context": "/retrieve/context/{document_ids} (GET)",
                    "rag": "/retrieve/rag (POST)",
                    "health": "/health (GET)",
                    "status": "/status (GET)"
                },
                "configuration": {
                    "default_search_limit": Config.DEFAULT_SEARCH_LIMIT,
                    "max_search_limit": Config.MAX_SEARCH_LIMIT,
                    "min_similarity_threshold": Config.MIN_SIMILARITY_THRESHOLD,
                    "default_use_hybrid": Config.DEFAULT_USE_HYBRID,
                    "context_window_size": Config.CONTEXT_WINDOW_SIZE,
                    "max_context_chunks": Config.MAX_CONTEXT_CHUNKS
                },
                "dependencies": {
                    "embedding_service": Config.EMBEDDING_SERVICE_URL,
                    "vector_db": Config.VECTOR_DB_URL
                },
                "timestamp": int(time.time() * 1000)
            }, 200
            
        except Exception as e:
            self.logger.error(f"Error getting service info: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": int(time.time() * 1000)
            }, 500
