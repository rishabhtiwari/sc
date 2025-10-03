#!/usr/bin/env python3
"""
MCP Service - Model Context Protocol Integration Service
"""

import os
import sys
import logging
from flask import Flask, request
from flask_cors import CORS

from routes.mcp_routes import mcp_bp
from routes.health_routes import health_bp
from routes.remote_host_mcp_routes import remote_host_mcp_bp
from config.settings import MCPConfig

def create_app():
    """
    Application factory pattern - creates and configures Flask app
    """
    print("Creating Flask app...")
    sys.stdout.flush()
    app = Flask(__name__)
    print("Flask app created")
    sys.stdout.flush()
    
    # Load configuration
    app.config.from_object(MCPConfig)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, app.config.get('LOG_LEVEL', 'INFO')),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Enable CORS for cross-origin requests
    CORS(app)
    
    # Register blueprints (routes)
    print("=" * 50)
    print("REGISTERING BLUEPRINTS...")
    print("=" * 50)
    sys.stdout.flush()
    try:
        app.register_blueprint(mcp_bp, url_prefix='/')
        print("✓ Registered mcp_bp")
        app.register_blueprint(health_bp, url_prefix='/')
        print("✓ Registered health_bp")
        app.register_blueprint(remote_host_mcp_bp, url_prefix='/mcp')
        print("✓ Registered remote_host_mcp_bp")
        print("=" * 50)
        print("ALL BLUEPRINTS REGISTERED SUCCESSFULLY")
        print("=" * 50)
    except Exception as e:
        print(f"❌ ERROR REGISTERING BLUEPRINTS: {e}")
        import traceback
        traceback.print_exc()

    # Add request logging
    @app.before_request
    def log_request():
        print(f"REQUEST: {request.method} {request.path}")
    
    # Root endpoint
    @app.route('/', methods=['GET'])
    def home():
        """
        Home endpoint with service information
        """
        from flask import jsonify
        import time
        return jsonify({
            "name": "iChat MCP Service",
            "version": "1.0.0",
            "status": "running",
            "description": "Model Context Protocol Integration Service",
            "endpoints": {
                "connect": "/mcp/connect (POST)",
                "list": "/mcp/list (GET)",
                "disconnect": "/mcp/disconnect (POST)",
                "execute": "/mcp/execute (POST)",
                "health": "/health (GET)",
                "status": "/status (GET)"
            },
            "timestamp": int(time.time() * 1000)
        })
    
    return app


def main():
    """
    Main entry point for the application
    """
    try:
        print("🚀 Starting iChat MCP Service v1.0...")
        print("📍 Server will be available at: http://localhost:8089")
        print("🔗 MCP endpoints: http://localhost:8089/mcp/*")
        print("❤️  Health check: http://localhost:8089/health")
        print("🛑 Press Ctrl+C to stop the server")
        print("=" * 50)
        
        print("Calling create_app()...")
        app = create_app()
        print("App created successfully")
        app.run(
            host=os.getenv('FLASK_HOST', '0.0.0.0'),
            port=int(os.getenv('FLASK_PORT', 8089)),
            debug=os.getenv('FLASK_DEBUG', 'false').lower() == 'true',
            use_reloader=False
        )
        
    except KeyboardInterrupt:
        print("\n👋 iChat MCP Service stopped")
    except Exception as e:
        print(f"❌ Failed to start server: {e}")


if __name__ == "__main__":
    main()
