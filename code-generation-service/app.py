"""
Code Generation Service Application
Code repository connector and analysis service that uses existing LLM services for code generation
"""
import os
import sys
from flask import Flask, jsonify
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import Config
from routes.code_routes import code_bp
from routes.health_routes import health_bp
from routes.repository_routes import repository_bp
from utils.logger import setup_logger


def create_app() -> Flask:
    """
    Create and configure Flask application
    
    Returns:
        Configured Flask application
    """
    app = Flask(__name__)

    # Configure Flask app
    app.secret_key = Config.SECRET_KEY

    # Configure CORS
    CORS(app, origins=Config.CORS_ORIGINS)
    
    # Register blueprints
    app.register_blueprint(code_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(repository_bp)
    
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
    def handle_exception(e):
        """Handle general exceptions"""
        return jsonify({
            "status": "error",
            "error": "Internal server error",
            "message": str(e),
            "timestamp": int(__import__('time').time() * 1000)
        }), 500

    return app


class StandaloneApplication:
    """Gunicorn application wrapper"""
    
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app

    def load_config(self):
        config = {key: value for key, value in self.options.items()
                  if key in self.cfg.settings and value is not None}
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application


def main():
    """Main entry point"""
    logger = setup_logger('code-generation-service')
    
    try:
        logger.info("Starting Code Generation Service")
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
        logger.info("Code Generation Service is ready to accept requests")
        
        if Config.USE_GUNICORN:
            # Use Gunicorn for production
            try:
                from gunicorn.app.base import BaseApplication
                
                class StandaloneApplication(BaseApplication):
                    def __init__(self, app, options=None):
                        self.options = options or {}
                        self.application = app
                        super().__init__()

                    def load_config(self):
                        config = {key: value for key, value in self.options.items()
                                  if key in self.cfg.settings and value is not None}
                        for key, value in config.items():
                            self.cfg.set(key.lower(), value)

                    def load(self):
                        return self.application
                
                options = {
                    'bind': f'{Config.HOST}:{Config.PORT}',
                    'workers': Config.GUNICORN_WORKERS,
                    'worker_class': 'sync',
                    'timeout': 300,  # Longer timeout for code generation
                    'keepalive': 2,
                    'max_requests': 100,
                    'max_requests_jitter': 10,
                    'preload_app': True,
                    'access_log_format': '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s',
                }
                
                StandaloneApplication(app, options).run()
            except ImportError:
                logger.warning("Gunicorn not available, falling back to Flask dev server")
                app.run(
                    host=Config.HOST,
                    port=Config.PORT,
                    debug=Config.DEBUG,
                    threaded=True
                )
        else:
            # Use Flask development server
            app.run(
                host=Config.HOST,
                port=Config.PORT,
                debug=Config.DEBUG,
                threaded=True
            )
            
    except KeyboardInterrupt:
        logger.info("Code Generation Service stopped by user")
    except Exception as e:
        logger.error(f"Failed to start Code Generation Service: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
