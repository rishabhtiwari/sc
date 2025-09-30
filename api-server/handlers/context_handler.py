"""
Context Handler - Handle context management requests (repositories and MCP resources)
"""

from flask import request, jsonify, current_app
import time
import uuid
import requests
from typing import Dict, Any, List

from controllers.context_controller import ContextController


class ContextHandler:
    """Handler for context management operations"""

    @staticmethod
    def handle_get_repositories():
        """
        Handle GET /api/context/repositories requests
        Get all connected repositories
        
        Returns:
            Flask Response: JSON response with repositories
        """
        try:
            result = ContextController.get_repositories()
            return jsonify(result), 200
            
        except Exception as e:
            current_app.logger.error(f"❌ Error getting repositories: {str(e)}")
            return jsonify({
                "error": f"Failed to get repositories: {str(e)}",
                "status": "error",
                "timestamp": int(time.time() * 1000)
            }), 500

    @staticmethod
    def handle_add_repository():
        """
        Handle POST /api/context/repositories requests
        Add a new repository to context
        
        Returns:
            Flask Response: JSON response with operation result
        """
        try:
            data = request.get_json()
            if not data:
                return jsonify({
                    "error": "Request body is required",
                    "status": "error"
                }), 400

            # Validate required fields
            required_fields = ['name', 'url']
            for field in required_fields:
                if field not in data:
                    return jsonify({
                        "error": f"Missing required field: {field}",
                        "status": "error"
                    }), 400

            result = ContextController.add_repository(data)
            return jsonify(result), 200
            
        except Exception as e:
            current_app.logger.error(f"❌ Error adding repository: {str(e)}")
            return jsonify({
                "error": f"Failed to add repository: {str(e)}",
                "status": "error",
                "timestamp": int(time.time() * 1000)
            }), 500

    @staticmethod
    def handle_remove_repository(repo_id: str):
        """
        Handle DELETE /api/context/repositories/<repo_id> requests
        Remove repository from context
        
        Args:
            repo_id: Repository ID to remove
            
        Returns:
            Flask Response: JSON response with operation result
        """
        try:
            result = ContextController.remove_repository(repo_id)
            return jsonify(result), 200
            
        except Exception as e:
            current_app.logger.error(f"❌ Error removing repository: {str(e)}")
            return jsonify({
                "error": f"Failed to remove repository: {str(e)}",
                "status": "error",
                "timestamp": int(time.time() * 1000)
            }), 500

    @staticmethod
    def handle_get_mcp_resources():
        """
        Handle GET /api/context/mcp-resources requests
        Get all MCP resources in context
        
        Returns:
            Flask Response: JSON response with MCP resources
        """
        try:
            result = ContextController.get_mcp_resources()
            return jsonify(result), 200
            
        except Exception as e:
            current_app.logger.error(f"❌ Error getting MCP resources: {str(e)}")
            return jsonify({
                "error": f"Failed to get MCP resources: {str(e)}",
                "status": "error",
                "timestamp": int(time.time() * 1000)
            }), 500

    @staticmethod
    def handle_add_mcp_resource():
        """
        Handle POST /api/context/mcp-resources requests
        Add MCP resource to context
        
        Returns:
            Flask Response: JSON response with operation result
        """
        try:
            data = request.get_json()
            if not data:
                return jsonify({
                    "error": "Request body is required",
                    "status": "error"
                }), 400

            # Validate required fields
            required_fields = ['provider_id', 'token_id', 'resource_id', 'resource_name', 'resource_type']
            for field in required_fields:
                if field not in data:
                    return jsonify({
                        "error": f"Missing required field: {field}",
                        "status": "error"
                    }), 400

            result = ContextController.add_mcp_resource(data)
            return jsonify(result), 200
            
        except Exception as e:
            current_app.logger.error(f"❌ Error adding MCP resource: {str(e)}")
            return jsonify({
                "error": f"Failed to add MCP resource: {str(e)}",
                "status": "error",
                "timestamp": int(time.time() * 1000)
            }), 500

    @staticmethod
    def handle_remove_mcp_resource(resource_id: str):
        """
        Handle DELETE /api/context/mcp-resources/<resource_id> requests
        Remove MCP resource from context
        
        Args:
            resource_id: MCP resource ID to remove
            
        Returns:
            Flask Response: JSON response with operation result
        """
        try:
            result = ContextController.remove_mcp_resource(resource_id)
            return jsonify(result), 200
            
        except Exception as e:
            current_app.logger.error(f"❌ Error removing MCP resource: {str(e)}")
            return jsonify({
                "error": f"Failed to remove MCP resource: {str(e)}",
                "status": "error",
                "timestamp": int(time.time() * 1000)
            }), 500

    @staticmethod
    def handle_get_provider_resources(provider_id: str):
        """
        Handle GET /api/mcp/provider/<provider_id>/resources requests
        Get resources from MCP provider (proxy to MCP service)
        
        Args:
            provider_id: MCP provider ID
            
        Returns:
            Flask Response: JSON response with provider resources
        """
        try:
            token_id = request.args.get('token_id')
            if not token_id:
                return jsonify({
                    "error": "token_id query parameter is required",
                    "status": "error"
                }), 400

            # Proxy request to MCP service
            mcp_service_url = current_app.config.get('MCP_SERVICE_URL', 'http://localhost:8089')
            
            response = requests.get(
                f"{mcp_service_url}/provider/{provider_id}/resources",
                params={'token_id': token_id},
                timeout=30
            )
            
            if response.status_code == 200:
                return jsonify(response.json()), 200
            else:
                return jsonify({
                    "error": f"MCP service error: {response.status_code}",
                    "details": response.text,
                    "status": "error"
                }), response.status_code
            
        except requests.RequestException as e:
            current_app.logger.error(f"❌ Error calling MCP service: {str(e)}")
            return jsonify({
                "error": f"Failed to connect to MCP service: {str(e)}",
                "status": "error",
                "timestamp": int(time.time() * 1000)
            }), 500
        except Exception as e:
            current_app.logger.error(f"❌ Error getting provider resources: {str(e)}")
            return jsonify({
                "error": f"Failed to get provider resources: {str(e)}",
                "status": "error",
                "timestamp": int(time.time() * 1000)
            }), 500
