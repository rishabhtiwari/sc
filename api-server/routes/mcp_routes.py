"""
MCP Routes - API endpoints for MCP (Model Context Protocol) integration
"""

from flask import Blueprint, jsonify
from datetime import datetime

from handlers.mcp_handler import MCPHandler

# Create MCP blueprint
mcp_bp = Blueprint('mcp', __name__)


@mcp_bp.route('/mcp/connect', methods=['POST'])
def connect_mcp():
    """
    POST /api/mcp/connect - Connect to an MCP server
    
    Expected JSON payload:
    {
        "name": "server_name",
        "command": ["python", "-m", "mcp_server"],
        "args": ["--option", "value"],
        "env": {"KEY": "value"},
        "protocol": "stdio",
        "config_id": "optional_stored_config_id"
    }
    
    Returns:
        JSON response with connection result
    """
    return MCPHandler.handle_mcp_connect()


@mcp_bp.route('/mcp/disconnect', methods=['POST'])
def disconnect_mcp():
    """
    POST /api/mcp/disconnect - Disconnect from an MCP server
    
    Expected JSON payload:
    {
        "connection_id": "connection_uuid"
    }
    
    Returns:
        JSON response with disconnection result
    """
    return MCPHandler.handle_mcp_disconnect()


@mcp_bp.route('/mcp/list', methods=['GET'])
def list_mcp_connections():
    """
    GET /api/mcp/list - List all active MCP connections
    
    Returns:
        JSON response with list of connections
    """
    return MCPHandler.handle_list_connections()


@mcp_bp.route('/mcp/status/<connection_id>', methods=['GET'])
def get_mcp_status(connection_id):
    """
    GET /api/mcp/status/<connection_id> - Get status of specific MCP connection
    
    Returns:
        JSON response with connection status
    """
    return MCPHandler.handle_connection_status(connection_id)


@mcp_bp.route('/mcp/execute', methods=['POST'])
def execute_mcp_tool():
    """
    POST /api/mcp/execute - Execute a tool through MCP
    
    Expected JSON payload:
    {
        "connection_id": "connection_uuid",
        "tool_name": "tool_name",
        "arguments": {"arg1": "value1", "arg2": "value2"}
    }
    
    Returns:
        JSON response with execution result
    """
    return MCPHandler.handle_tool_execution()


@mcp_bp.route('/mcp/tools/<connection_id>', methods=['GET'])
def list_mcp_tools(connection_id):
    """
    GET /api/mcp/tools/<connection_id> - List available tools for MCP connection
    
    Returns:
        JSON response with available tools
    """
    return MCPHandler.handle_list_tools(connection_id)


@mcp_bp.route('/mcp/resources/<connection_id>', methods=['GET'])
def list_mcp_resources(connection_id):
    """
    GET /api/mcp/resources/<connection_id> - List available resources for MCP connection
    
    Returns:
        JSON response with available resources
    """
    return MCPHandler.handle_list_resources(connection_id)


@mcp_bp.route('/mcp/config', methods=['POST'])
def store_mcp_config():
    """
    POST /api/mcp/config - Store MCP configuration for later use
    
    Expected JSON payload:
    {
        "name": "config_name",
        "description": "Configuration description",
        "command": ["python", "-m", "mcp_server"],
        "args": ["--option", "value"],
        "env": {"KEY": "value"},
        "protocol": "stdio"
    }
    
    Returns:
        JSON response with storage result
    """
    return MCPHandler.handle_store_config()


@mcp_bp.route('/mcp/config/<config_id>', methods=['GET'])
def get_mcp_config(config_id):
    """
    GET /api/mcp/config/<config_id> - Get stored MCP configuration
    
    Returns:
        JSON response with configuration data
    """
    return MCPHandler.handle_get_config(config_id)


@mcp_bp.route('/mcp/config/<config_id>', methods=['DELETE'])
def delete_mcp_config(config_id):
    """
    DELETE /api/mcp/config/<config_id> - Delete stored MCP configuration
    
    Returns:
        JSON response with deletion result
    """
    return MCPHandler.handle_delete_config(config_id)


@mcp_bp.route('/mcp/configs', methods=['GET'])
def list_mcp_configs():
    """
    GET /api/mcp/configs - List all stored MCP configurations
    
    Returns:
        JSON response with list of configurations
    """
    return MCPHandler.handle_list_configs()


@mcp_bp.route('/mcp/test', methods=['GET'])
def mcp_test():
    """
    GET /api/mcp/test - Test MCP service connectivity
    
    Returns:
        JSON response confirming MCP service is working
    """
    return MCPHandler.handle_mcp_test()


@mcp_bp.route('/mcp/suggest', methods=['POST'])
def suggest_mcp_connections():
    """
    POST /api/mcp/suggest - Get MCP connection suggestions based on requirements
    
    Expected JSON payload:
    {
        "requirements": "User description of what they need"
    }
    
    Returns:
        JSON response with connection suggestions
    """
    return MCPHandler.handle_connection_suggestions()


@mcp_bp.route('/mcp/route', methods=['POST'])
def route_mcp_request():
    """
    POST /api/mcp/route - Route request to appropriate MCP connection

    Expected JSON payload:
    {
        "query": "User's natural language query"
    }

    Returns:
        JSON response with routing decision
    """
    return MCPHandler.handle_request_routing()


# New GitHub OAuth and Provider Management Routes

@mcp_bp.route('/mcp/providers', methods=['GET'])
def get_mcp_providers():
    """
    GET /api/mcp/providers - Get list of supported MCP providers

    Returns:
        JSON response with supported providers and their configuration requirements
    """
    return MCPHandler.handle_get_providers()


@mcp_bp.route('/mcp/provider/<provider>/config', methods=['POST'])
def configure_mcp_provider(provider):
    """
    POST /api/mcp/provider/<provider>/config - Configure an MCP provider

    For GitHub:
    {
        "client_id": "your_github_client_id",
        "client_secret": "your_github_client_secret",
        "redirect_uri": "http://localhost:8080/api/mcp/oauth/github/callback",
        "scope": "repo,read:user"
    }

    Returns:
        JSON response with configuration result
    """
    return MCPHandler.handle_configure_provider(provider)


@mcp_bp.route('/mcp/provider/<provider>/auth', methods=['POST'])
def start_mcp_auth(provider):
    """
    POST /api/mcp/provider/<provider>/auth - Start OAuth authentication for provider

    Expected JSON payload:
    {
        "config_id": "configuration_id_from_configure_step"
    }

    Returns:
        JSON response with authorization URL
    """
    return MCPHandler.handle_start_auth(provider)


@mcp_bp.route('/mcp/oauth/<provider>/callback', methods=['GET'])
def handle_oauth_callback(provider):
    """
    GET /api/mcp/oauth/<provider>/callback - Handle OAuth callback

    Query parameters:
        code: Authorization code from provider
        state: State parameter for CSRF protection

    Returns:
        JSON response with authentication result
    """
    return MCPHandler.handle_oauth_callback(provider)


@mcp_bp.route('/mcp/tokens', methods=['GET'])
def list_oauth_tokens():
    """
    GET /api/mcp/tokens - List all stored OAuth tokens

    Returns:
        JSON response with list of tokens (without sensitive data)
    """
    return MCPHandler.handle_list_tokens()


@mcp_bp.route('/mcp/token/<token_id>/revoke', methods=['POST'])
def revoke_oauth_token(token_id):
    """
    POST /api/mcp/token/<token_id>/revoke - Revoke an OAuth token

    Returns:
        JSON response with revocation result
    """
    return MCPHandler.handle_revoke_token(token_id)


@mcp_bp.route('/mcp/github/repositories', methods=['GET'])
def list_github_repositories():
    """
    GET /api/mcp/github/repositories - List GitHub repositories for authenticated user

    Query parameters:
        token_id: OAuth token ID
        type: Repository type (all, owner, member) - default: owner
        sort: Sort by (created, updated, pushed, full_name) - default: updated
        per_page: Results per page (1-100) - default: 30

    Returns:
        JSON response with repositories list
    """
    return MCPHandler.handle_github_repositories()


@mcp_bp.route('/mcp/github/repository/<owner>/<repo>', methods=['GET'])
def get_github_repository(owner, repo):
    """
    GET /api/mcp/github/repository/<owner>/<repo> - Get GitHub repository details

    Query parameters:
        token_id: OAuth token ID

    Returns:
        JSON response with repository details
    """
    return MCPHandler.handle_github_repository_details(owner, repo)


@mcp_bp.route('/mcp/github/repository/<owner>/<repo>/clone', methods=['POST'])
def clone_github_repository(owner, repo):
    """
    POST /api/mcp/github/repository/<owner>/<repo>/clone - Clone GitHub repository

    Expected JSON payload:
    {
        "token_id": "oauth_token_id",
        "branch": "main"  // optional
    }

    Returns:
        JSON response with clone result
    """
    return MCPHandler.handle_github_repository_clone(owner, repo)


@mcp_bp.route('/mcp/provider/<provider_id>/resources', methods=['GET'])
def get_mcp_provider_resources(provider_id):
    """
    GET /api/mcp/provider/<provider_id>/resources - Get resources from MCP provider

    Query parameters:
        token_id: OAuth token ID for the provider

    Returns:
        JSON response with provider resources
    """
    return MCPHandler.handle_get_provider_resources(provider_id)


@mcp_bp.route('/mcp/providers/<provider_id>/connect', methods=['POST'])
def connect_mcp_provider(provider_id):
    """
    POST /api/mcp/providers/<provider_id>/connect - Connect to MCP provider

    For remote_host provider:
    {
        "name": "My Server",
        "protocol": "ssh",
        "host": "example.com",
        "port": 22,
        "username": "user",
        "password": "pass",
        "private_key": "...",
        "base_path": "/"
    }

    Returns:
        JSON response with connection result
    """
    return MCPHandler.handle_connect_provider(provider_id)


@mcp_bp.route('/mcp/providers/<provider_id>/disconnect', methods=['POST'])
def disconnect_mcp_provider(provider_id):
    """
    POST /api/mcp/providers/<provider_id>/disconnect - Disconnect from MCP provider

    Expected JSON payload:
    {
        "connection_id": "connection_uuid"
    }

    Returns:
        JSON response with disconnection result
    """
    return MCPHandler.handle_disconnect_provider(provider_id)


@mcp_bp.route('/mcp/providers/<provider_id>/connections', methods=['GET'])
def get_provider_connections(provider_id):
    """
    GET /api/mcp/providers/<provider_id>/connections - Get connections for a specific MCP provider

    Args:
        provider_id: The ID of the provider to get connections for

    Returns:
        JSON response with provider connections
    """
    return MCPHandler.handle_get_provider_connections(provider_id)
