"""
Template Service - Flask Application
Video template management and resolution service
"""
import os
from flask import Flask, jsonify, request, g
from flask_cors import CORS
from pymongo import MongoClient

from config import Config
from utils import setup_logger
from services import TemplateManager, VariableResolver
from routes import template_bp, health_bp, init_routes


def create_app(config_class=Config):
    """Create and configure Flask application"""
    
    # Create Flask app
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Enable CORS
    CORS(app, origins=config_class.CORS_ORIGINS)
    
    # Setup logger
    logger = setup_logger(
        'template-service',
        log_file=config_class.LOG_FILE,
        level=config_class.LOG_LEVEL
    )
    
    logger.info(f"Starting {config_class.SERVICE_NAME} v{config_class.SERVICE_VERSION}")
    
    # Validate configuration
    try:
        config_class.validate()
        logger.info("Configuration validated successfully")
    except ValueError as e:
        logger.error(f"Configuration validation failed: {e}")
        # Create template directory if it doesn't exist
        os.makedirs(config_class.TEMPLATE_DIR, exist_ok=True)
        logger.info(f"Created template directory: {config_class.TEMPLATE_DIR}")
    
    # Initialize MongoDB connection
    try:
        mongo_client = MongoClient(config_class.MONGODB_URL)
        # Test connection
        mongo_client.admin.command('ping')
        logger.info(f"Connected to MongoDB: {config_class.MONGODB_HOST}")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise
    
    # Initialize services
    template_manager = TemplateManager(
        template_dir=config_class.TEMPLATE_DIR,
        db_client=mongo_client,
        logger=logger
    )
    
    variable_resolver = VariableResolver(logger=logger)
    
    # Initialize routes with dependencies
    init_routes(template_manager, variable_resolver, mongo_client, logger)

    # Register middleware to extract customer_id from request headers
    @app.before_request
    def extract_customer_context():
        """
        Extract customer_id and user_id from request headers
        These are injected by the API gateway's JWT middleware
        """
        # Skip for OPTIONS requests (CORS preflight)
        if request.method == 'OPTIONS':
            return

        # Extract from headers (injected by API gateway)
        g.customer_id = request.headers.get('X-Customer-ID')
        g.user_id = request.headers.get('X-User-ID')

        logger.debug(f"Request context: customer_id={g.customer_id}, user_id={g.user_id}, path={request.path}")

    # Register blueprints
    app.register_blueprint(health_bp, url_prefix='/api')
    app.register_blueprint(template_bp, url_prefix='/api')
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'status': 'error',
            'error': 'Not found'
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        return jsonify({
            'status': 'error',
            'error': 'Internal server error'
        }), 500
    
    # Root endpoint
    @app.route('/')
    def index():
        return jsonify({
            'service': config_class.SERVICE_NAME,
            'version': config_class.SERVICE_VERSION,
            'description': config_class.SERVICE_DESCRIPTION,
            'endpoints': {
                'health': '/api/health',
                'templates': '/api/templates',
                'resolve': '/api/templates/resolve'
            }
        })
    
    logger.info(f"{config_class.SERVICE_NAME} initialized successfully")
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )

