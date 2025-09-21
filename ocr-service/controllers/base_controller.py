"""
Base Controller - Common functionality for all controllers
"""

import time
from flask import jsonify
from typing import Dict, Any, Tuple


class BaseController:
    """
    Base controller with common functionality
    """
    
    @staticmethod
    def success_response(data: Dict[str, Any], status_code: int = 200) -> Tuple[Dict, int]:
        """
        Create a standardized success response
        
        Args:
            data: Response data
            status_code: HTTP status code
            
        Returns:
            Tuple of (response_dict, status_code)
        """
        response = {
            "status": "success",
            "timestamp": int(time.time() * 1000),
            **data
        }
        return jsonify(response), status_code
    
    @staticmethod
    def error_response(message: str, status_code: int = 400, error_code: str = None) -> Tuple[Dict, int]:
        """
        Create a standardized error response
        
        Args:
            message: Error message
            status_code: HTTP status code
            error_code: Optional error code
            
        Returns:
            Tuple of (response_dict, status_code)
        """
        response = {
            "status": "error",
            "message": message,
            "timestamp": int(time.time() * 1000)
        }
        
        if error_code:
            response["error_code"] = error_code
            
        return jsonify(response), status_code
    
    @staticmethod
    def validation_error(errors: Dict[str, str]) -> Tuple[Dict, int]:
        """
        Create a validation error response
        
        Args:
            errors: Dictionary of field validation errors
            
        Returns:
            Tuple of (response_dict, status_code)
        """
        response = {
            "status": "validation_error",
            "message": "Validation failed",
            "errors": errors,
            "timestamp": int(time.time() * 1000)
        }
        return jsonify(response), 422
