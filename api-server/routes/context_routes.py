"""
Context Routes - API endpoints for context management (repositories and MCP resources)
"""

from flask import Blueprint, jsonify, request
from datetime import datetime
import time

from handlers.context_handler import ContextHandler

# Create context blueprint
context_bp = Blueprint('context', __name__)


@context_bp.route('/context/repositories', methods=['GET'])
def get_repositories():
    """
    GET /api/context/repositories - Get all connected repositories
    
    Returns:
        JSON response with repositories list
    """
    return ContextHandler.handle_get_repositories()


@context_bp.route('/context/repositories', methods=['POST'])
def add_repository():
    """
    POST /api/context/repositories - Add a new repository to context
    
    Expected JSON payload:
    {
        "name": "repository_name",
        "url": "https://github.com/user/repo.git",
        "branch": "main",
        "accessToken": "optional_access_token"
    }
    
    Returns:
        JSON response with operation result
    """
    return ContextHandler.handle_add_repository()


@context_bp.route('/context/repositories/<repo_id>', methods=['DELETE'])
def remove_repository(repo_id):
    """
    DELETE /api/context/repositories/<repo_id> - Remove repository from context
    
    Returns:
        JSON response with operation result
    """
    return ContextHandler.handle_remove_repository(repo_id)


@context_bp.route('/context/mcp-resources', methods=['GET'])
def get_mcp_resources():
    """
    GET /api/context/mcp-resources - Get all MCP resources in context
    
    Returns:
        JSON response with MCP resources list
    """
    return ContextHandler.handle_get_mcp_resources()


@context_bp.route('/context/mcp-resources', methods=['POST'])
def add_mcp_resource():
    """
    POST /api/context/mcp-resources - Add MCP resource to context
    
    Expected JSON payload:
    {
        "provider_id": "github",
        "token_id": "token_uuid",
        "resource_id": "resource_identifier",
        "resource_name": "Resource Name",
        "resource_type": "repository",
        "resource_data": {...}
    }
    
    Returns:
        JSON response with operation result
    """
    return ContextHandler.handle_add_mcp_resource()


@context_bp.route('/context/mcp-resources/<resource_id>', methods=['DELETE'])
def remove_mcp_resource(resource_id):
    """
    DELETE /api/context/mcp-resources/<resource_id> - Remove MCP resource from context
    
    Returns:
        JSON response with operation result
    """
    return ContextHandler.handle_remove_mcp_resource(resource_id)


# MCP Provider resource listing (proxied to MCP service)
@context_bp.route('/mcp/provider/<provider_id>/resources', methods=['GET'])
def get_provider_resources(provider_id):
    """
    GET /api/mcp/provider/<provider_id>/resources - Get resources from MCP provider
    
    Query parameters:
    - token_id: OAuth token ID for authentication
    
    Returns:
        JSON response with provider resources
    """
    return ContextHandler.handle_get_provider_resources(provider_id)
