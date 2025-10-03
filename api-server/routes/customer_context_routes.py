"""
Customer Context Routes - API endpoints for customer-persistent context management
"""

import time
from flask import Blueprint, request, jsonify
from controllers.customer_context_controller import CustomerContextController

# Create blueprint
customer_context_bp = Blueprint('customer_context', __name__)


@customer_context_bp.route('/context/customer/<customer_id>', methods=['GET'])
def get_customer_context(customer_id):
    """
    GET /api/context/customer/<customer_id> - Get all context resources for a customer
    
    Returns:
        JSON response with customer's context resources grouped by type
    """
    try:
        result = CustomerContextController.get_all_context_resources(customer_id)
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": f"Failed to get customer context: {str(e)}",
            "timestamp": int(time.time() * 1000)
        }), 500


@customer_context_bp.route('/context/customer/<customer_id>/github-repository', methods=['POST'])
def add_github_repository_to_context(customer_id):
    """
    POST /api/context/customer/<customer_id>/github-repository - Add GitHub repository to customer context
    
    Expected JSON payload:
    {
        "name": "repository-name",
        "full_name": "owner/repository-name",
        "clone_url": "https://github.com/owner/repo.git",
        "html_url": "https://github.com/owner/repo",
        "default_branch": "main",
        "description": "Repository description",
        "language": "Python",
        "stars": 123,
        "private": false,
        "token_id": "github_token_uuid"
    }
    
    Returns:
        JSON response with operation result
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "status": "error",
                "error": "Request body is required"
            }), 400

        # Validate required fields
        required_fields = ['clone_url']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "status": "error",
                    "error": f"Missing required field: {field}"
                }), 400

        result = CustomerContextController.add_github_repository(data, customer_id)
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": f"Failed to add GitHub repository: {str(e)}",
            "timestamp": int(time.time() * 1000)
        }), 500


@customer_context_bp.route('/context/customer/<customer_id>/remote-host', methods=['POST'])
def add_remote_host_to_context(customer_id):
    """
    POST /api/context/customer/<customer_id>/remote-host - Add remote host to customer context
    
    Expected JSON payload:
    {
        "name": "My Server",
        "protocol": "ssh",
        "host": "example.com",
        "port": 22,
        "username": "user",
        "base_path": "/home/user",
        "connection_id": "remote_host_connection_uuid",
        "token_id": "remote_host_token_uuid"
    }
    
    Returns:
        JSON response with operation result
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "status": "error",
                "error": "Request body is required"
            }), 400

        # Validate required fields
        required_fields = ['name', 'protocol', 'host']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "status": "error",
                    "error": f"Missing required field: {field}"
                }), 400

        result = CustomerContextController.add_remote_host(data, customer_id)
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": f"Failed to add remote host: {str(e)}",
            "timestamp": int(time.time() * 1000)
        }), 500


@customer_context_bp.route('/context/customer/<customer_id>/resource/<resource_id>', methods=['DELETE'])
def remove_customer_context_resource(customer_id, resource_id):
    """
    DELETE /api/context/customer/<customer_id>/resource/<resource_id> - Remove a resource from customer context

    Returns:
        JSON response with operation result
    """
    try:
        result = CustomerContextController.remove_context_resource(resource_id, customer_id)
        return jsonify(result), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "error": f"Failed to remove resource: {str(e)}",
            "timestamp": int(time.time() * 1000)
        }), 500


@customer_context_bp.route('/context/customer/<customer_id>/resource/<resource_id>', methods=['DELETE'])
def remove_resource_from_context(customer_id, resource_id):
    """
    DELETE /api/context/customer/<customer_id>/resource/<resource_id> - Remove resource from customer context
    
    Returns:
        JSON response with operation result
    """
    try:
        result = CustomerContextController.remove_context_resource(resource_id, customer_id)
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": f"Failed to remove resource: {str(e)}",
            "timestamp": int(time.time() * 1000)
        }), 500


# MCP Integration Routes - Auto-add resources to context when MCP connections are made

@customer_context_bp.route('/mcp/github/connect-to-context', methods=['POST'])
def connect_github_to_context():
    """
    POST /api/mcp/github/connect-to-context - Connect GitHub repository and add to customer context
    
    Expected JSON payload:
    {
        "customer_id": "customer_uuid",
        "token_id": "github_token_uuid",
        "repository_data": {
            "name": "repository-name",
            "full_name": "owner/repository-name",
            "clone_url": "https://github.com/owner/repo.git",
            "html_url": "https://github.com/owner/repo",
            "default_branch": "main",
            "description": "Repository description",
            "language": "Python",
            "stars": 123,
            "private": false
        }
    }
    
    Returns:
        JSON response with operation result
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "status": "error",
                "error": "Request body is required"
            }), 400

        customer_id = data.get("customer_id", "default")
        repository_data = data.get("repository_data", {})
        repository_data["token_id"] = data.get("token_id")

        result = CustomerContextController.add_github_repository(repository_data, customer_id)
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": f"Failed to connect GitHub to context: {str(e)}",
            "timestamp": int(time.time() * 1000)
        }), 500


@customer_context_bp.route('/mcp/remote-host/connect-to-context', methods=['POST'])
def connect_remote_host_to_context():
    """
    POST /api/mcp/remote-host/connect-to-context - Connect remote host and add to customer context
    
    Expected JSON payload:
    {
        "customer_id": "customer_uuid",
        "token_id": "remote_host_token_uuid",
        "host_data": {
            "name": "My Server",
            "protocol": "ssh",
            "host": "example.com",
            "port": 22,
            "username": "user",
            "base_path": "/home/user",
            "connection_id": "remote_host_connection_uuid"
        }
    }
    
    Returns:
        JSON response with operation result
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "status": "error",
                "error": "Request body is required"
            }), 400

        customer_id = data.get("customer_id", "default")
        host_data = data.get("host_data", {})
        host_data["token_id"] = data.get("token_id")

        result = CustomerContextController.add_remote_host(host_data, customer_id)
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": f"Failed to connect remote host to context: {str(e)}",
            "timestamp": int(time.time() * 1000)
        }), 500


# Legacy compatibility routes (for existing UI)

@customer_context_bp.route('/context/repositories', methods=['GET'])
def get_repositories_legacy():
    """
    GET /api/context/repositories - Get repositories for default customer (legacy compatibility)
    """
    customer_id = request.args.get('customer_id', 'default')
    result = CustomerContextController.get_all_context_resources(customer_id)
    
    if result["status"] == "success":
        # Return only repositories for legacy compatibility
        return jsonify({
            "status": "success",
            "repositories": result["resources"]["repositories"],
            "count": len(result["resources"]["repositories"]),
            "timestamp": result["timestamp"]
        }), 200
    else:
        return jsonify(result), 500


@customer_context_bp.route('/context/mcp-resources', methods=['GET'])
def get_mcp_resources_legacy():
    """
    GET /api/context/mcp-resources - Get MCP resources for default customer (legacy compatibility)
    """
    customer_id = request.args.get('customer_id', 'default')
    result = CustomerContextController.get_all_context_resources(customer_id)
    
    if result["status"] == "success":
        # Return remote hosts and other MCP resources for legacy compatibility
        mcp_resources = result["resources"]["remote_hosts"] + result["resources"]["documents"]
        return jsonify({
            "status": "success",
            "resources": mcp_resources,
            "count": len(mcp_resources),
            "timestamp": result["timestamp"]
        }), 200
    else:
        return jsonify(result), 500
