"""
Health Controller - Handles health and status endpoints
"""

import time
from typing import Dict, Any, Tuple

from .base_controller import BaseController
from services.ocr_service import OCRService
from utils.system_info import SystemInfo
from utils.logger import get_logger


class HealthController(BaseController):
    """
    Controller for health and status operations
    """
    
    def __init__(self):
        self.ocr_service = OCRService()
        self.system_info = SystemInfo()
        self.logger = get_logger(__name__)
    
    def health_check(self) -> Tuple[Dict, int]:
        """
        Basic health check endpoint
        
        Returns:
            Tuple of (response_dict, status_code)
        """
        try:
            # Test OCR service
            ocr_status = self.ocr_service.health_check()
            
            data = {
                "message": "OCR service is operational" if ocr_status else "OCR service unavailable",
                "ocr_engine": "PaddleOCR",
                "version": "1.0.0",
                "supported_languages": ["en", "ch", "fr", "german", "korean", "japan"]
            }
            
            status_code = 200 if ocr_status else 503
            response_status = "success" if ocr_status else "unhealthy"
            
            response = {
                "status": response_status,
                "timestamp": int(time.time() * 1000),
                **data
            }
            
            return response, status_code
            
        except Exception as e:
            self.logger.error(f"Health check failed: {str(e)}")
            return self.error_response(f"Health check failed: {str(e)}", 500)
    
    def detailed_status(self) -> Tuple[Dict, int]:
        """
        Get detailed service status including system metrics
        
        Returns:
            Tuple of (response_dict, status_code)
        """
        try:
            system_metrics = self.system_info.get_system_metrics()
            
            data = {
                "service": {
                    "name": "Paddle OCR Document Converter",
                    "version": "1.0.0",
                    "uptime": self.system_info.get_uptime()
                },
                "system": system_metrics,
                "ocr_engine": {
                    "name": "PaddleOCR",
                    "version": "2.7.0.3",
                    "status": "ready" if self.ocr_service.health_check() else "unavailable"
                }
            }
            
            return self.success_response(data)
            
        except Exception as e:
            self.logger.error(f"Failed to get detailed status: {str(e)}")
            return self.error_response(f"Failed to get status: {str(e)}", 500)
    
    def service_info(self) -> Tuple[Dict, int]:
        """
        Get basic service information
        
        Returns:
            Tuple of (response_dict, status_code)
        """
        data = {
            "name": "Paddle OCR Document Converter",
            "version": "1.0.0",
            "status": "running",
            "endpoints": {
                "extract": "/ocr/extract (POST)",
                "convert": "/ocr/convert (POST)",
                "health": "/health (GET)",
                "status": "/status (GET)",
                "formats": "/formats (GET)"
            },
            "supported_formats": [
                "PDF", "PNG", "JPG", "JPEG", "BMP", "TIFF", "DOCX", "TXT"
            ]
        }
        
        return self.success_response(data)
