"""
LLM Prompt Generation Service Application
LLM-powered prompt generation and response service for iChat RAG
"""
import os
import sys
from flask import Flask, jsonify
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import Config
from routes.llm_routes import llm_bp
from utils.logger import setup_logger


def create_app() -> Flask:
    """
    Create and configure Flask application
    
    Returns:
        Configured Flask application
    """
    app = Flask(__name__)
    
    # Configure CORS
    CORS(app, origins=Config.CORS_ORIGINS)
    
    # Register blueprints
    app.register_blueprint(llm_bp)
    
    # Global error handlers
    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        """Handle HTTP exceptions"""
        return jsonify({
            "status": "error",
            "error": e.description,
            "code": e.code,
            "timestamp": int(__import__('time').time() * 1000)
        }), e.code
    
    @app.errorhandler(Exception)
    def handle_general_exception(e):
        """Handle general exceptions"""
        logger = setup_logger('app')
        logger.error(f"Unhandled exception: {str(e)}")
        
        return jsonify({
            "status": "error",
            "error": "Internal server error",
            "timestamp": int(__import__('time').time() * 1000)
        }), 500
    
    return app


def main():
    """Main application entry point"""
    # Setup logging
    logger = setup_logger('llm-service')
    
    try:
        logger.info("Starting LLM Prompt Generation Service")
        logger.info(f"Service: {Config.SERVICE_NAME} v{Config.SERVICE_VERSION}")
        logger.info(f"Environment: {Config.ENVIRONMENT}")
        logger.info(f"Host: {Config.HOST}:{Config.PORT}")
        logger.info(f"Debug: {Config.DEBUG}")
        
        # Create Flask app
        app = create_app()
        
        # Log configuration
        logger.info("Service Configuration:")
        for key, value in Config.to_dict().items():
            logger.info(f"  {key}: {value}")
        
        # Start the server
        logger.info("LLM Service is ready to accept requests")
        
        if Config.ENVIRONMENT == 'production':
            # Use Gunicorn in production
            import gunicorn.app.base
            
            class StandaloneApplication(gunicorn.app.base.BaseApplication):
                def __init__(self, app, options=None):
                    self.options = options or {}
                    self.application = app
                    super().__init__()
                
                def load_config(self):
                    for key, value in self.options.items():
                        self.cfg.set(key.lower(), value)
                
                def load(self):
                    return self.application
            
            options = {
                'bind': f'{Config.HOST}:{Config.PORT}',
                'workers': 1,  # Single worker for model loading
                'worker_class': 'sync',
                'timeout': 300,  # Longer timeout for LLM generation
                'keepalive': 2,
                'max_requests': 100,  # Lower for memory management
                'max_requests_jitter': 10,
                'preload_app': True,
                'access_log_format': '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s',
            }
            
            StandaloneApplication(app, options).run()
        else:
            # Use Flask development server
            app.run(
                host=Config.HOST,
                port=Config.PORT,
                debug=Config.DEBUG,
                threaded=True
            )
            
    except KeyboardInterrupt:
        logger.info("LLM Service stopped by user")
    except Exception as e:
        logger.error(f"Failed to start LLM Service: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
