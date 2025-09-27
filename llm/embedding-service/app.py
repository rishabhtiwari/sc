#!/usr/bin/env python3
"""
Embedding Service - Document Processing and Vector Storage Service

This service handles document upload, OCR processing, text chunking,
and storage in vector database for RAG functionality.

Author: iChat System
Version: 1.0.0
"""

import os
import sys
import time
from flask import Flask, request, jsonify
from flask_cors import CORS


# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import Config
from services.embedding_service import EmbeddingService
from routes.embedding_routes import embedding_bp
from utils.logger import setup_logger

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# Setup logging
logger = setup_logger('embedding-service')

# Global service instance
embedding_service = None

def create_app():
    """Create and configure the Flask application"""
    global embedding_service
    
    try:
        logger.info("Starting Embedding Service...")
        logger.info(f"Configuration: {Config.get_config()}")
        
        # Initialize embedding service
        logger.info("Initializing Embedding Service...")
        embedding_service = EmbeddingService()
        
        if not embedding_service.initialize():
            logger.error("Failed to initialize embedding service")
            return None
            
        logger.info("Embedding service initialized successfully")
        
        # Register blueprints
        app.register_blueprint(embedding_bp)

        # Store service in app context
        app.embedding_service = embedding_service
        
        # Health check endpoint
        @app.route('/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            try:
                if embedding_service and embedding_service.is_healthy():
                    return jsonify({
                        "service": "Embedding Service",
                        "status": "healthy",
                        "version": "1.0.0",
                        "ocr_service": Config.OCR_SERVICE_URL,
                        "vector_db": Config.VECTOR_DB_URL,
                        "timestamp": int(time.time() * 1000)
                    }), 200
                else:
                    return jsonify({
                        "service": "Embedding Service",
                        "status": "unhealthy",
                        "error": "Service not properly initialized",
                        "timestamp": int(time.time() * 1000)
                    }), 503
            except Exception as e:
                logger.error(f"Health check failed: {str(e)}")
                return jsonify({
                    "service": "Embedding Service",
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": int(time.time() * 1000)
                }), 503
        
        # Error handlers
        @app.errorhandler(404)
        def not_found(error):
            return jsonify({
                "status": "error",
                "error": "Endpoint not found",
                "timestamp": int(time.time() * 1000)
            }), 404

        @app.errorhandler(413)
        def file_too_large(error):
            return jsonify({
                "status": "error",
                "error": "File too large",
                "max_size": f"{Config.MAX_FILE_SIZE_MB}MB",
                "timestamp": int(time.time() * 1000)
            }), 413
        
        @app.errorhandler(500)
        def internal_error(error):
            logger.error(f"Internal server error: {str(error)}")
            return jsonify({
                "status": "error",
                "error": "Internal server error",
                "timestamp": int(time.time() * 1000)
            }), 500
        
        return app
        
    except Exception as e:
        logger.error(f"Failed to create app: {str(e)}")
        return None

def get_embedding_service():
    """Get the global embedding service instance"""
    return embedding_service

if __name__ == '__main__':
    app = create_app()
    if app:
        logger.info(f"Starting Embedding Service on {Config.HOST}:{Config.PORT}")
        app.run(
            host=Config.HOST,
            port=Config.PORT,
            debug=Config.DEBUG
        )
    else:
        logger.error("Failed to start embedding service")
        sys.exit(1)
