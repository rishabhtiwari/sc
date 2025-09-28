"""
Health Controller - Handles health check operations
"""

import time
import logging
from typing import Dict, Any, Tuple
from flask import jsonify

from services.mcp_client_service import MCPClientService


class HealthController:
    """Controller for handling health check requests"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.mcp_client_service = MCPClientService()
    
    def health_check(self) -> Tuple[Dict[str, Any], int]:
        """
        Handle GET /health requests
        
        Returns:
            Tuple[Dict, int]: Response data and HTTP status code
        """
        try:
            # Get basic service status
            connections = self.mcp_client_service.list_connections()
            active_connections = len([c for c in connections if c.get('status') == 'connected'])
            
            return jsonify({
                "status": "healthy",
                "service": "MCP Service",
                "version": "1.0.0",
                "active_connections": active_connections,
                "total_connections": len(connections),
                "timestamp": int(time.time() * 1000)
            }), 200
            
        except Exception as e:
            self.logger.error(f"❌ Health check failed: {str(e)}")
            return jsonify({
                "status": "unhealthy",
                "service": "MCP Service",
                "error": str(e),
                "timestamp": int(time.time() * 1000)
            }), 503
    
    def detailed_status(self) -> Tuple[Dict[str, Any], int]:
        """
        Handle GET /status requests
        
        Returns:
            Tuple[Dict, int]: Response data and HTTP status code
        """
        try:
            # Get detailed service status
            connections = self.mcp_client_service.list_connections()
            
            # Categorize connections by status
            connection_stats = {
                'connected': 0,
                'connecting': 0,
                'disconnected': 0,
                'error': 0
            }
            
            for conn in connections:
                status = conn.get('status', 'unknown')
                if status in connection_stats:
                    connection_stats[status] += 1
                else:
                    connection_stats['error'] += 1
            
            # Check system resources (basic check)
            import psutil
            memory_usage = psutil.virtual_memory().percent
            cpu_usage = psutil.cpu_percent(interval=1)
            
            return jsonify({
                "status": "healthy",
                "service_name": "MCP Service",
                "version": "1.0.0",
                "uptime": int(time.time() * 1000),  # Simplified uptime
                "connections": {
                    "total": len(connections),
                    "by_status": connection_stats,
                    "details": connections
                },
                "system": {
                    "memory_usage_percent": memory_usage,
                    "cpu_usage_percent": cpu_usage
                },
                "endpoints": {
                    "connect": "/mcp/connect (POST)",
                    "disconnect": "/mcp/disconnect (POST)",
                    "list": "/mcp/list (GET)",
                    "execute": "/mcp/execute (POST)",
                    "config": "/mcp/config (POST/GET/DELETE)"
                },
                "timestamp": int(time.time() * 1000)
            }), 200
            
        except Exception as e:
            self.logger.error(f"❌ Detailed status check failed: {str(e)}")
            return jsonify({
                "status": "error",
                "service_name": "MCP Service",
                "error": str(e),
                "timestamp": int(time.time() * 1000)
            }), 500
