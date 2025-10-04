"""
Routes for MCP service endpoints
"""
from flask import Blueprint
from controllers.mcp_controller import MCPController

# Create blueprint
mcp_bp = Blueprint('mcp', __name__)

# Initialize controller
mcp_controller = MCPController()

# MCP connection endpoints
@mcp_bp.route('/mcp/connect', methods=['POST'])
def connect_mcp():
    """Connect to an MCP server"""
    return mcp_controller.connect_mcp()

@mcp_bp.route('/mcp/disconnect', methods=['POST'])
def disconnect_mcp():
    """Disconnect from an MCP server"""
    return mcp_controller.disconnect_mcp()

@mcp_bp.route('/mcp/list', methods=['GET'])
def list_mcp_connections():
    """List all active MCP connections"""
    return mcp_controller.list_connections()

@mcp_bp.route('/mcp/status/<connection_id>', methods=['GET'])
def get_mcp_status(connection_id):
    """Get status of a specific MCP connection"""
    return mcp_controller.get_connection_status(connection_id)

# MCP execution endpoints
@mcp_bp.route('/mcp/execute', methods=['POST'])
def execute_mcp_tool():
    """Execute a tool through MCP"""
    return mcp_controller.execute_tool()

@mcp_bp.route('/mcp/tools/<connection_id>', methods=['GET'])
def list_mcp_tools(connection_id):
    """List available tools for an MCP connection"""
    return mcp_controller.list_tools(connection_id)

@mcp_bp.route('/mcp/resources/<connection_id>', methods=['GET'])
def list_mcp_resources(connection_id):
    """List available resources for an MCP connection"""
    return mcp_controller.list_resources(connection_id)

# MCP configuration endpoints
@mcp_bp.route('/mcp/config', methods=['POST'])
def store_mcp_config():
    """Store MCP configuration for later use"""
    return mcp_controller.store_config()

@mcp_bp.route('/mcp/config/<config_id>', methods=['GET'])
def get_mcp_config(config_id):
    """Get stored MCP configuration"""
    return mcp_controller.get_config(config_id)

@mcp_bp.route('/mcp/config/<config_id>', methods=['DELETE'])
def delete_mcp_config(config_id):
    """Delete stored MCP configuration"""
    return mcp_controller.delete_config(config_id)

@mcp_bp.route('/mcp/configs', methods=['GET'])
def list_mcp_configs():
    """List all stored MCP configurations"""
    return mcp_controller.list_configs()

# Provider Management Routes

@mcp_bp.route('/providers', methods=['GET'])
def get_providers():
    """Get list of supported MCP providers"""
    return mcp_controller.get_providers()

@mcp_bp.route('/provider/<provider>/config', methods=['POST'])
def configure_provider(provider):
    """Configure an MCP provider"""
    return mcp_controller.configure_provider(provider)

@mcp_bp.route('/provider/<provider>/auth', methods=['POST'])
def start_provider_auth(provider):
    """Start OAuth authentication"""
    return mcp_controller.start_provider_auth(provider)

@mcp_bp.route('/oauth/<provider>/callback', methods=['GET'])
def oauth_callback(provider):
    """Handle OAuth callback"""
    return mcp_controller.handle_oauth_callback(provider)

@mcp_bp.route('/connections', methods=['GET'])
def list_connections():
    """List all MCP connections"""
    return mcp_controller.list_connections()

@mcp_bp.route('/connection/<connection_id>/status', methods=['GET'])
def get_connection_status(connection_id):
    """Get connection status"""
    return mcp_controller.get_connection_status(connection_id)

@mcp_bp.route('/connection/<connection_id>/disconnect', methods=['POST'])
def disconnect_connection(connection_id):
    """Disconnect connection"""
    return mcp_controller.disconnect_connection(connection_id)

@mcp_bp.route('/connection/<connection_id>/tools', methods=['GET'])
def list_connection_tools(connection_id):
    """List tools for connection"""
    return mcp_controller.list_tools(connection_id)

@mcp_bp.route('/connection/<connection_id>/execute', methods=['POST'])
def execute_connection_tool(connection_id):
    """Execute tool"""
    return mcp_controller.execute_tool(connection_id)

@mcp_bp.route('/connection/<connection_id>/resources', methods=['GET'])
def list_connection_resources(connection_id):
    """List resources for connection"""
    return mcp_controller.list_resources(connection_id)



@mcp_bp.route('/test', methods=['GET'])
def test_service():
    """Test MCP service"""
    return mcp_controller.test_service()

# GitHub-specific routes
@mcp_bp.route('/github/tokens', methods=['GET'])
def github_tokens():
    """List GitHub OAuth tokens"""
    return mcp_controller.list_tokens()

@mcp_bp.route('/github/token/<token_id>', methods=['GET'])
def github_token(token_id):
    """Get specific GitHub OAuth token"""
    return mcp_controller.get_token(token_id)

@mcp_bp.route('/github/token/<token_id>/revoke', methods=['POST'])
def revoke_github_token(token_id):
    """Revoke GitHub OAuth token"""
    return mcp_controller.revoke_token(token_id)

@mcp_bp.route('/github/repositories', methods=['GET'])
def github_repositories():
    """List GitHub repositories"""
    return mcp_controller.github_repositories()

@mcp_bp.route('/github/repository/<owner>/<repo>', methods=['GET'])
def github_repository_details(owner, repo):
    """Get repository details"""
    return mcp_controller.github_repository_details(owner, repo)

@mcp_bp.route('/provider/<provider_id>/resources', methods=['GET'])
def get_provider_resources(provider_id):
    """Get resources from MCP provider"""
    return mcp_controller.get_provider_resources(provider_id)

@mcp_bp.route('/github/repository/<owner>/<repo>/clone', methods=['POST'])
def github_repository_clone(owner, repo):
    """Clone repository"""
    return mcp_controller.github_repository_clone(owner, repo)

# MCP test page
@mcp_bp.route('/mcp/test', methods=['GET'])
def mcp_test_page():
    """Serve MCP test page"""
    from flask import send_from_directory
    import os
    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')
    return send_from_directory(static_dir, 'mcp-test.html')
