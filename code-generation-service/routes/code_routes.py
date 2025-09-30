"""
Routes for code generation service endpoints
"""
from flask import Blueprint
from controllers.code_controller import CodeController

# Create blueprint
code_bp = Blueprint('code', __name__)

# Initialize controller
code_controller = CodeController()

# Repository connection endpoints
@code_bp.route('/code/connect', methods=['POST'])
def connect_repository():
    """Connect to a code repository"""
    return code_controller.connect_repository()

@code_bp.route('/code/repositories', methods=['GET'])
def get_repositories():
    """Get list of connected repositories"""
    return code_controller.get_repositories()

@code_bp.route('/code/repositories/<repository_id>', methods=['DELETE'])
def delete_repository(repository_id):
    """Delete a connected repository"""
    return code_controller.delete_repository(repository_id)

# GitHub OAuth endpoints
@code_bp.route('/code/auth/github/config', methods=['POST'])
def github_oauth_config():
    """Store GitHub OAuth configuration"""
    return code_controller.github_oauth_config()

@code_bp.route('/code/auth/github/login', methods=['GET'])
def github_oauth_login():
    """Initiate GitHub OAuth login flow"""
    return code_controller.github_oauth_login()

@code_bp.route('/code/auth/github/callback', methods=['GET'])
def github_oauth_callback():
    """Handle GitHub OAuth callback"""
    return code_controller.github_oauth_callback()

@code_bp.route('/code/auth/status', methods=['GET'])
def auth_status():
    """Check authentication status"""
    return code_controller.auth_status()

@code_bp.route('/code/auth/test', methods=['GET'])
def oauth_test_page():
    """Serve OAuth test page"""
    from flask import send_from_directory
    import os
    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')
    return send_from_directory(static_dir, 'oauth-test.html')

@code_bp.route('/code/analyze', methods=['POST'])
def analyze_repository():
    """Analyze a connected repository"""
    return code_controller.analyze_repository()

@code_bp.route('/code/files', methods=['GET'])
def list_repository_files():
    """List files in a connected repository"""
    return code_controller.list_repository_files()

@code_bp.route('/code/file', methods=['GET'])
def get_file_content():
    """Get content of a specific file from repository"""
    return code_controller.get_file_content()

@code_bp.route('/code/cleanup', methods=['POST'])
def cleanup_repository():
    """Clean up temporary repository files"""
    return code_controller.cleanup_repository()

# Code generation endpoints
@code_bp.route('/code/generate', methods=['POST'])
def generate_code():
    """Generate code based on repository context and requirements"""
    return code_controller.generate_code()
