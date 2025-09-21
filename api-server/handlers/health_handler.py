"""
Health Handler - HTTP request/response handling for health endpoints
"""

import time

from flask import jsonify

from controllers.health_controller import HealthController


class HealthHandler:
    """
    Handler for health-related HTTP requests
    """

    @staticmethod
    def handle_health_check():
        """
        Handle GET /api/health requests
        
        Returns:
            Flask Response: JSON response with health status
        """
        try:
            health_data = HealthController.get_health_status()

            # Determine HTTP status code based on health status
            status_code = 200 if health_data.get('status') == 'healthy' else 503

            return jsonify(health_data), status_code

        except Exception as e:
            print(f"❌ Error in health check: {str(e)}")
            return jsonify({
                "status": "unhealthy",
                "message": f"Health check failed: {str(e)}",
                "timestamp": int(time.time() * 1000),
                "error": str(e)
            }), 503

    @staticmethod
    def handle_detailed_status():
        """
        Handle GET /api/status requests - detailed system status
        
        Returns:
            Flask Response: JSON response with detailed status
        """
        try:
            status_data = HealthController.get_detailed_status()

            # Determine HTTP status code
            status_code = 200 if status_data.get('status') == 'healthy' else 503

            return jsonify(status_data), status_code

        except Exception as e:
            print(f"❌ Error getting detailed status: {str(e)}")
            return jsonify({
                "status": "error",
                "message": f"Failed to get system status: {str(e)}",
                "timestamp": int(time.time() * 1000),
                "error": str(e)
            }), 500

    @staticmethod
    def handle_ping():
        """
        Handle GET /api/ping requests - simple connectivity test
        
        Returns:
            Flask Response: Simple pong response
        """
        try:
            return jsonify({
                "status": "success",
                "message": "pong",
                "timestamp": int(time.time() * 1000),
                "server": "iChat API Server"
            }), 200

        except Exception as e:
            print(f"❌ Error in ping handler: {str(e)}")
            return jsonify({
                "status": "error",
                "message": f"Ping failed: {str(e)}",
                "timestamp": int(time.time() * 1000)
            }), 500
