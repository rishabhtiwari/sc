#!/usr/bin/env python3
"""
OCR Service - Paddle OCR Document Converter
Restructured with proper MVC architecture
"""

from flask import Flask
from flask_cors import CORS

from config.ocr_config import OCRConfig
from controllers.ocr_controller import OCRController
from controllers.health_controller import HealthController
from middleware.error_handler import ErrorHandler
from middleware.request_logger import RequestLogger
from utils.logger import get_logger


def create_app():
    """
    Application factory pattern - creates and configures Flask app
    """
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(OCRConfig)

    # Enable CORS for cross-origin requests
    CORS(app)

    # Initialize middleware
    error_handler = ErrorHandler(app)
    request_logger = RequestLogger(app)

    # Initialize controllers
    ocr_controller = OCRController()
    health_controller = HealthController()

    # Register routes
    register_routes(app, ocr_controller, health_controller)

    return app


def register_routes(app: Flask, ocr_controller: OCRController, health_controller: HealthController):
    """
    Register all application routes

    Args:
        app: Flask application instance
        ocr_controller: OCR controller instance
        health_controller: Health controller instance
    """
    # Health and status endpoints
    app.add_url_rule('/', 'home', health_controller.service_info, methods=['GET'])
    app.add_url_rule('/health', 'health', health_controller.health_check, methods=['GET'])
    app.add_url_rule('/status', 'status', health_controller.detailed_status, methods=['GET'])

    # OCR endpoints
    app.add_url_rule('/convert', 'convert', ocr_controller.convert_document, methods=['POST'])
    app.add_url_rule('/formats', 'formats', ocr_controller.get_supported_formats, methods=['GET'])


def main():
    """
    Main entry point for the OCR service
    """
    logger = get_logger(__name__)

    try:
        logger.info("🚀 Starting Paddle OCR Document Converter...")
        logger.info("📍 Service will be available at: http://localhost:8081")
        logger.info("📄 Convert endpoint: http://localhost:8081/convert")
        logger.info("❤️  Health check: http://localhost:8081/health")
        logger.info("🛑 Press Ctrl+C to stop the service")
        logger.info("=" * 50)

        app = create_app()
        app.run(
            host='0.0.0.0',
            port=8081,
            debug=False,  # Disable debug in production
            use_reloader=False
        )

    except KeyboardInterrupt:
        logger.info("\n👋 OCR Service stopped")
    except Exception as e:
        logger.error(f"❌ Failed to start OCR service: {e}")


if __name__ == "__main__":
    main()
