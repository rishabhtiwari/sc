#!/usr/bin/env python3
"""
iChat API Server - Main Application Entry Point
"""

import time
import random

from flask import Flask
from flask_cors import CORS

from routes.chat_routes import chat_bp
from routes.health_routes import health_bp
from config.app_config import AppConfig


def create_app():
    """
    Application factory pattern - creates and configures Flask app
    """
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(AppConfig)
    
    # Enable CORS for cross-origin requests
    CORS(app)
    
    # Register blueprints (routes)
    app.register_blueprint(chat_bp, url_prefix='/api')
    app.register_blueprint(health_bp, url_prefix='/api')
    
    # Root endpoint
    @app.route('/', methods=['GET'])
    def home():
        """
        Home endpoint with API information
        """
        from flask import jsonify
        return jsonify({
            "name": "iChat API Server",
            "version": "2.0.0",
            "status": "running",
            "endpoints": {
                "chat": "/api/chat (POST)",
                "health": "/api/health (GET)",
                "home": "/ (GET)"
            },
            "timestamp": int(time.time() * 1000)
        })
    
    return app


def main():
    """
    Main entry point for the application
    """
    try:
        print("🚀 Starting iChat API Server v2.0...")
        print("📍 Server will be available at: http://localhost:8080")
        print("🔗 Chat endpoint: http://localhost:8080/api/chat")
        print("❤️  Health check: http://localhost:8080/api/health")
        print("🛑 Press Ctrl+C to stop the server")
        print("=" * 50)
        
        app = create_app()
        app.run(
            host='0.0.0.0',
            port=8080,
            debug=True,
            use_reloader=False
        )
        
    except KeyboardInterrupt:
        print("\n👋 iChat API Server stopped")
    except Exception as e:
        print(f"❌ Failed to start server: {e}")


if __name__ == "__main__":
    main()
