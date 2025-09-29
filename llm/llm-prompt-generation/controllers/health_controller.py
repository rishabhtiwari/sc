"""
Health controller for LLM service
"""
import time
from typing import Dict, Tuple, Any
from services.llm_service import LLMService
from config.settings import Config
from utils.logger import setup_logger


class HealthController:
    """Controller for health check endpoints"""
    
    def __init__(self):
        self.llm_service = LLMService()
        self.logger = setup_logger('health-controller')
    
    def health_check(self) -> Tuple[Dict[str, Any], int]:
        """
        Perform comprehensive health check
        
        Returns:
            Tuple of (response_dict, status_code)
        """
        try:
            health_result = self.llm_service.health_check()
            
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
            # Get actual model name from model instance if available
            actual_model_name = Config.MODEL_NAME
            if hasattr(self.llm_service, 'model_instance') and self.llm_service.model_instance:
                model_info = self.llm_service.model_instance.get_model_info()
                actual_model_name = model_info.get('model_name', Config.MODEL_NAME)

            return {
                "name": Config.SERVICE_NAME,
                "version": Config.SERVICE_VERSION,
                "description": Config.SERVICE_DESCRIPTION,
                "status": "running",
                "endpoints": {
                    "generate": "/llm/generate (POST)",
                    "chat": "/llm/chat (POST)",
                    "search": "/llm/search (POST)",
                    "health": "/health (GET)",
                    "status": "/status (GET)"
                },
                "model": {
                    "name": actual_model_name,
                    "max_length": Config.MAX_LENGTH,
                    "max_new_tokens": Config.MAX_NEW_TOKENS,
                    "temperature": Config.TEMPERATURE,
                    "use_gpu": Config.USE_GPU
                },
                "configuration": {
                    "max_context_length": Config.MAX_CONTEXT_LENGTH,
                    "max_context_chunks": Config.MAX_CONTEXT_CHUNKS,
                    "min_similarity_threshold": Config.MIN_SIMILARITY_THRESHOLD
                },
                "dependencies": {
                    "retriever_service": Config.RETRIEVER_SERVICE_URL
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
