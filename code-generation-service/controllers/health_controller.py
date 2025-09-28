"""
Health Controller
Handles health check and service status endpoints
"""
import time
import requests
from flask import jsonify
from typing import Dict, Tuple, Any

from config.settings import Config
from utils.logger import setup_logger


class HealthController:
    """Controller for health check and service status"""
    
    def __init__(self):
        self.logger = setup_logger('health-controller')
    
    def health_check(self) -> Tuple[Dict[str, Any], int]:
        """
        Basic health check endpoint
        
        Returns:
            Tuple of (response_dict, status_code)
        """
        try:
            return {
                "status": "healthy",
                "service": Config.SERVICE_NAME,
                "version": Config.SERVICE_VERSION,
                "timestamp": int(time.time() * 1000)
            }, 200
        except Exception as e:
            self.logger.error(f"Health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": int(time.time() * 1000)
            }, 503
    
    def service_status(self) -> Tuple[Dict[str, Any], int]:
        """
        Detailed service status including dependencies
        
        Returns:
            Tuple of (response_dict, status_code)
        """
        try:
            # Check external dependencies
            llm_service_status = self._check_llm_service()
            llm_prompt_service_status = self._check_llm_prompt_service()
            
            overall_status = "healthy"
            if not llm_service_status["available"] and not llm_prompt_service_status["available"]:
                overall_status = "degraded"
            
            return {
                "status": overall_status,
                "service": {
                    "name": Config.SERVICE_NAME,
                    "version": Config.SERVICE_VERSION,
                    "description": Config.SERVICE_DESCRIPTION,
                    "environment": Config.ENVIRONMENT
                },
                "dependencies": {
                    "llm_service": llm_service_status,
                    "llm_prompt_service": llm_prompt_service_status
                },
                "configuration": {
                    "supported_repo_types": Config.SUPPORTED_REPO_TYPES,
                    "supported_languages": Config.SUPPORTED_LANGUAGES,
                    "max_repo_size_mb": Config.MAX_REPO_SIZE_MB,
                    "max_file_size_kb": Config.MAX_FILE_SIZE_KB
                },
                "endpoints": {
                    "connect": "/code/connect (POST)",
                    "analyze": "/code/analyze (POST)",
                    "generate": "/code/generate (POST)",
                    "files": "/code/files (GET)",
                    "file_content": "/code/file (GET)",
                    "cleanup": "/code/cleanup (POST)",
                    "health": "/health (GET)",
                    "status": "/status (GET)"
                },
                "timestamp": int(time.time() * 1000)
            }, 200
            
        except Exception as e:
            self.logger.error(f"Status check failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": int(time.time() * 1000)
            }, 500
    
    def _check_llm_service(self) -> Dict[str, Any]:
        """Check LLM service availability"""
        try:
            url = Config.get_llm_service_url('health')
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                return {
                    "available": True,
                    "status": "healthy",
                    "url": url,
                    "response_time_ms": response.elapsed.total_seconds() * 1000
                }
            else:
                return {
                    "available": False,
                    "status": "unhealthy",
                    "url": url,
                    "error": f"HTTP {response.status_code}"
                }
                
        except requests.exceptions.RequestException as e:
            return {
                "available": False,
                "status": "unreachable",
                "url": Config.get_llm_service_url('health'),
                "error": str(e)
            }
        except Exception as e:
            return {
                "available": False,
                "status": "error",
                "error": str(e)
            }
    
    def _check_llm_prompt_service(self) -> Dict[str, Any]:
        """Check LLM prompt service availability"""
        try:
            url = Config.get_llm_prompt_service_url('health')
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                return {
                    "available": True,
                    "status": "healthy",
                    "url": url,
                    "response_time_ms": response.elapsed.total_seconds() * 1000
                }
            else:
                return {
                    "available": False,
                    "status": "unhealthy",
                    "url": url,
                    "error": f"HTTP {response.status_code}"
                }
                
        except requests.exceptions.RequestException as e:
            return {
                "available": False,
                "status": "unreachable",
                "url": Config.get_llm_prompt_service_url('health'),
                "error": str(e)
            }
        except Exception as e:
            return {
                "available": False,
                "status": "error",
                "error": str(e)
            }
