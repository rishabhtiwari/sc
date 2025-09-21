"""
Error handling middleware for OCR Service
"""

import time
import traceback
from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException
from utils.logger import get_logger


class ErrorHandler:
    """
    Global error handler for the Flask application
    """
    
    def __init__(self, app: Flask = None):
        self.logger = get_logger(__name__)
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """
        Initialize error handlers for Flask app
        
        Args:
            app: Flask application instance
        """
        app.register_error_handler(404, self.handle_not_found)
        app.register_error_handler(405, self.handle_method_not_allowed)
        app.register_error_handler(413, self.handle_payload_too_large)
        app.register_error_handler(500, self.handle_internal_error)
        app.register_error_handler(Exception, self.handle_generic_exception)
    
    def handle_not_found(self, error):
        """
        Handle 404 Not Found errors
        
        Args:
            error: Error object
            
        Returns:
            JSON error response
        """
        self.logger.warning(f"404 Not Found: {request.url}")
        
        return jsonify({
            "status": "error",
            "message": "Endpoint not found",
            "error_code": "NOT_FOUND",
            "available_endpoints": [
                "GET /",
                "GET /health",
                "GET /status",
                "GET /formats",
                "POST /convert"
            ],
            "timestamp": int(time.time() * 1000)
        }), 404
    
    def handle_method_not_allowed(self, error):
        """
        Handle 405 Method Not Allowed errors
        
        Args:
            error: Error object
            
        Returns:
            JSON error response
        """
        self.logger.warning(f"405 Method Not Allowed: {request.method} {request.url}")
        
        return jsonify({
            "status": "error",
            "message": f"Method {request.method} not allowed for this endpoint",
            "error_code": "METHOD_NOT_ALLOWED",
            "allowed_methods": error.valid_methods if hasattr(error, 'valid_methods') else [],
            "timestamp": int(time.time() * 1000)
        }), 405
    
    def handle_payload_too_large(self, error):
        """
        Handle 413 Payload Too Large errors
        
        Args:
            error: Error object
            
        Returns:
            JSON error response
        """
        self.logger.warning(f"413 Payload Too Large: {request.url}")
        
        return jsonify({
            "status": "error",
            "message": "File too large. Maximum size is 10MB",
            "error_code": "PAYLOAD_TOO_LARGE",
            "max_file_size": "10MB",
            "timestamp": int(time.time() * 1000)
        }), 413
    
    def handle_internal_error(self, error):
        """
        Handle 500 Internal Server Error
        
        Args:
            error: Error object
            
        Returns:
            JSON error response
        """
        self.logger.error(f"500 Internal Server Error: {str(error)}")
        self.logger.error(f"Traceback: {traceback.format_exc()}")
        
        return jsonify({
            "status": "error",
            "message": "Internal server error occurred",
            "error_code": "INTERNAL_ERROR",
            "timestamp": int(time.time() * 1000)
        }), 500
    
    def handle_generic_exception(self, error):
        """
        Handle generic exceptions
        
        Args:
            error: Error object
            
        Returns:
            JSON error response
        """
        # If it's an HTTP exception, let it be handled normally
        if isinstance(error, HTTPException):
            return error
        
        self.logger.error(f"Unhandled exception: {str(error)}")
        self.logger.error(f"Traceback: {traceback.format_exc()}")
        
        return jsonify({
            "status": "error",
            "message": "An unexpected error occurred",
            "error_code": "UNEXPECTED_ERROR",
            "timestamp": int(time.time() * 1000)
        }), 500
