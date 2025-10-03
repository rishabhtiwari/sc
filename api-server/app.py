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
from routes.document_routes import document_bp
from routes.llm_routes import llm_bp
from routes.mcp_routes import mcp_bp
from routes.syncer_routes import syncer_bp

from config.app_config import AppConfig


def create_app():
    """
    Application factory pattern - creates and configures Flask app
    """
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(AppConfig)
    
    # Enable CORS for cross-origin requests with comprehensive localhost configuration
    CORS(app,
         origins=[
             'http://localhost:3001',
             'http://127.0.0.1:3001',
             'http://[::1]:3001',  # IPv6 localhost
             'http://0.0.0.0:3001'  # All interfaces
         ],
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
         allow_headers=['Content-Type', 'Authorization', 'Origin', 'Accept', 'Accept-Encoding', 'Cache-Control'],
         supports_credentials=True)
    
    # Import blueprints
    from routes.chat_routes import chat_bp
    from routes.health_routes import health_bp
    from routes.document_routes import document_bp
    from routes.llm_routes import llm_bp
    from routes.mcp_routes import mcp_bp
    from routes.context_routes import context_bp
    from routes.customer_context_routes import customer_context_bp
    from routes.code_routes import code_bp
    from routes.syncer_routes import syncer_bp

    # Register blueprints (routes)
    app.register_blueprint(chat_bp, url_prefix='/api')
    app.register_blueprint(health_bp, url_prefix='/api')
    app.register_blueprint(document_bp, url_prefix='/api')
    app.register_blueprint(llm_bp, url_prefix='/api')
    app.register_blueprint(mcp_bp, url_prefix='/api')
    app.register_blueprint(context_bp, url_prefix='/api')
    app.register_blueprint(customer_context_bp, url_prefix='/api')
    app.register_blueprint(code_bp, url_prefix='/api')
    app.register_blueprint(syncer_bp, url_prefix='/api')

    
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
                "documents": "/api/documents/* (GET/POST)",
                "llm": "/api/llm/* (GET/POST)",
                "mcp": "/api/mcp/* (GET/POST)",
                "context": "/api/context/* (GET/POST/DELETE)",
                "code": "/api/code/* (GET/POST)",
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
        print("📄 Document processing: http://localhost:8080/api/documents")
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
