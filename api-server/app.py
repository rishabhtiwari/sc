#!/usr/bin/env python3
"""
iChat API Server - Main Application Entry Point
"""

import time
import random
import logging
import sys

from flask import Flask
from flask_cors import CORS

from routes.chat_routes import chat_bp
from routes.health_routes import health_bp
from routes.document_routes import document_bp
from routes.llm_routes import llm_bp
from routes.mcp_routes import mcp_bp
from routes.syncer_routes import syncer_bp
from routes.github_syncer_routes import github_syncer_bp
from routes.news_routes import news_bp
from routes.prompt_routes import prompt_bp
from routes.voice_config_routes import voice_config_bp
from routes.video_config_routes import video_config_bp
from routes.frontend_routes import frontend_bp
from routes.websocket_routes import websocket_bp, init_socketio
from routes.auth_routes import auth_bp
from routes.dashboard_routes import dashboard_bp
from routes.monitoring_routes import monitoring_bp

from config.app_config import AppConfig


def create_app():
    """
    Application factory pattern - creates and configures Flask app
    """
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(AppConfig)

    # Configure logging
    log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO').upper())
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('logs/api-server.log', mode='a')
        ]
    )

    # Set Flask app logger level
    app.logger.setLevel(log_level)

    # Enable debug logging for our modules
    logging.getLogger('api-server').setLevel(log_level)

    app.logger.info(f"🔧 Logging configured at {app.config.get('LOG_LEVEL', 'INFO')} level")

    # Enable CORS for cross-origin requests with comprehensive localhost configuration
    CORS(app,
         origins=[
             'http://localhost:3001',
             'http://127.0.0.1:3001',
             'http://[::1]:3001',  # IPv6 localhost
             'http://0.0.0.0:3001',  # All interfaces
             'http://localhost:3002',  # News automation frontend (Express)
             'http://127.0.0.1:3002',
             'http://localhost:3003',  # News automation frontend (Nginx)
             'http://127.0.0.1:3003'
         ],
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
         allow_headers=['Content-Type', 'Authorization', 'Origin', 'Accept', 'Accept-Encoding', 'Cache-Control', 'X-Customer-ID', 'X-User-ID'],
         supports_credentials=True)

    # Register global JWT middleware to extract customer_id/user_id from JWT tokens
    # This ensures all backend services receive proper multi-tenant context
    from middleware.jwt_middleware import extract_and_inject_jwt_context
    app.before_request(extract_and_inject_jwt_context)
    app.logger.info("🔐 JWT middleware registered - will extract customer_id/user_id from tokens")
    
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
    from routes.github_syncer_routes import github_syncer_bp
    from routes.news_routes import news_bp
    from routes.prompt_routes import prompt_bp
    from routes.voice_config_routes import voice_config_bp
    from routes.video_config_routes import video_config_bp
    from routes.frontend_routes import frontend_bp
    from routes.websocket_routes import websocket_bp
    from routes.auth_routes import auth_bp
    from routes.dashboard_routes import dashboard_bp
    from routes.monitoring_routes import monitoring_bp
    # New service proxy routes
    from routes.image_routes import image_bp
    from routes.youtube_routes import youtube_bp
    from routes.video_routes import video_bp
    from routes.voice_routes import voice_bp
    from routes.template_routes import template_bp
    from routes.product_routes import product_bp
    from routes.audio_studio_routes import audio_studio_bp
    from routes.asset_routes import asset_bp
    from routes.prompt_template_routes import prompt_template_bp

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
    app.register_blueprint(github_syncer_bp, url_prefix='/api')
    app.register_blueprint(news_bp, url_prefix='/api')
    app.register_blueprint(prompt_bp, url_prefix='/api')
    app.register_blueprint(voice_config_bp, url_prefix='/api')
    app.register_blueprint(video_config_bp, url_prefix='/api')
    app.register_blueprint(frontend_bp, url_prefix='/api')
    app.register_blueprint(websocket_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(dashboard_bp, url_prefix='/api')
    app.register_blueprint(monitoring_bp, url_prefix='/api')
    # Register new service proxy routes
    app.register_blueprint(image_bp, url_prefix='/api')
    app.register_blueprint(youtube_bp, url_prefix='/api')
    app.register_blueprint(video_bp, url_prefix='/api')
    app.register_blueprint(voice_bp, url_prefix='/api')
    app.register_blueprint(template_bp, url_prefix='/api')
    app.register_blueprint(product_bp, url_prefix='/api')
    app.register_blueprint(audio_studio_bp, url_prefix='/api')
    app.register_blueprint(asset_bp, url_prefix='/api')
    app.register_blueprint(prompt_template_bp, url_prefix='/api')

    # Initialize Socket.IO for real-time updates
    socketio = init_socketio(app)
    app.socketio = socketio  # Store reference in app for access in routes

    
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
                "news": "/api/news/* (GET)",
                "prompts": "/api/llm/prompts/* (GET/POST/PUT/DELETE)",
                "voice": "/api/voice/* (GET/POST/PUT)",
                "frontend": "/api/frontend/* (Proxy to all services)",
                "websocket": "/api/websocket/* (WebSocket endpoints)",
                "auth": "/api/auth/* (Authentication)",
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
        print("📰 News API: http://localhost:8080/api/news")
        print("🔌 WebSocket: ws://localhost:8080/socket.io")
        print("🌐 Frontend Proxy: http://localhost:8080/api/frontend/*")
        print("❤️  Health check: http://localhost:8080/api/health")
        print("🛑 Press Ctrl+C to stop the server")
        print("=" * 50)

        app = create_app()

        # Use socketio.run() instead of app.run() to enable WebSocket support
        app.socketio.run(
            app,
            host='0.0.0.0',
            port=8080,
            debug=True,
            use_reloader=False,
            allow_unsafe_werkzeug=True  # Allow for development
        )

    except KeyboardInterrupt:
        print("\n👋 iChat API Server stopped")
    except Exception as e:
        print(f"❌ Failed to start server: {e}")


if __name__ == "__main__":
    main()
