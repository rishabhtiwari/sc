"""
Vector Database Service - ChromaDB-based vector storage and retrieval
"""

import os
import logging
from flask import Flask, jsonify
from flask_cors import CORS

from config.settings import Config
from services.vector_service import VectorService
from routes.vector_routes import vector_bp
from utils.logger import setup_logging

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Setup logging
setup_logging()
logger = logging.getLogger('vector-db')

# Load configuration
config = Config()

# Initialize vector service
vector_service = VectorService()

# Register blueprints
app.register_blueprint(vector_bp)

# Set vector service in routes
from routes.vector_routes import set_vector_service
set_vector_service(vector_service)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Check if vector service is healthy
        service_status = vector_service.health_check()
        
        if service_status['status'] == 'healthy':
            return jsonify({
                "status": "healthy",
                "service": "Vector Database Service",
                "version": "1.0.0",
                "database": "ChromaDB",
                "collections": service_status.get('collections', 0),
                "timestamp": service_status.get('timestamp')
            }), 200
        else:
            return jsonify({
                "status": "unhealthy",
                "service": "Vector Database Service",
                "error": service_status.get('error', 'Unknown error'),
                "timestamp": service_status.get('timestamp')
            }), 503
            
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            "status": "unhealthy",
            "service": "Vector Database Service",
            "error": str(e)
        }), 503

@app.route('/', methods=['GET'])
def root():
    """Root endpoint with service information"""
    return jsonify({
        "service": "Vector Database Service",
        "version": "1.0.0",
        "description": "ChromaDB-based vector storage and retrieval service",
        "endpoints": {
            "health": "/health",
            "collections": "/vector/collections",
            "documents": "/vector/documents",
            "search": "/vector/search",
            "embeddings": "/vector/embeddings"
        }
    })

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        "status": "error",
        "error": "Endpoint not found",
        "message": "The requested endpoint does not exist"
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({
        "status": "error",
        "error": "Internal server error",
        "message": "An unexpected error occurred"
    }), 500

if __name__ == '__main__':
    try:
        logger.info("Starting Vector Database Service...")
        logger.info(f"Configuration: {config.get_summary()}")
        
        # Initialize vector service
        if vector_service.initialize():
            logger.info("Vector service initialized successfully")
        else:
            logger.error("Failed to initialize vector service")
            exit(1)
        
        # Start Flask app
        app.run(
            host=config.HOST,
            port=config.PORT,
            debug=config.DEBUG
        )
        
    except Exception as e:
        logger.error(f"Failed to start Vector Database Service: {str(e)}")
        exit(1)
