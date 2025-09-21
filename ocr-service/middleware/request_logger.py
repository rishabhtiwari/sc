"""
Request logging middleware for OCR Service
"""

import time
from flask import Flask, request, g
from utils.logger import get_logger


class RequestLogger:
    """
    Request logging middleware
    """
    
    def __init__(self, app: Flask = None):
        self.logger = get_logger(__name__)
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """
        Initialize request logging for Flask app
        
        Args:
            app: Flask application instance
        """
        app.before_request(self.before_request)
        app.after_request(self.after_request)
    
    def before_request(self):
        """
        Log request start and store start time
        """
        g.start_time = time.time()
        
        # Log request details
        self.logger.info(f"Request started: {request.method} {request.path}")
        
        # Log additional details for POST requests
        if request.method == 'POST':
            content_length = request.content_length or 0
            self.logger.info(f"Content-Length: {content_length} bytes")
            
            if request.files:
                for file_key, file in request.files.items():
                    self.logger.info(f"File upload: {file_key} = {file.filename}")
    
    def after_request(self, response):
        """
        Log request completion and duration
        
        Args:
            response: Flask response object
            
        Returns:
            Response object
        """
        # Calculate request duration
        duration = time.time() - g.get('start_time', time.time())
        
        # Log response details
        self.logger.info(
            f"Request completed: {request.method} {request.path} "
            f"- Status: {response.status_code} "
            f"- Duration: {duration:.3f}s"
        )
        
        # Add custom headers
        response.headers['X-Response-Time'] = f"{duration:.3f}s"
        response.headers['X-Request-ID'] = self._generate_request_id()
        
        return response
    
    def _generate_request_id(self) -> str:
        """
        Generate a simple request ID
        
        Returns:
            Request ID string
        """
        return f"{int(time.time() * 1000)}-{hash(request.path) % 10000}"
