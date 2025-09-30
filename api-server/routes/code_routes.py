"""
Code Routes - API endpoints that proxy to code-generation-service
"""

from flask import Blueprint, jsonify, request
import requests
import time

# Create code blueprint
code_bp = Blueprint('code', __name__)

# Code generation service URL
from config.app_config import AppConfig
CODE_SERVICE_URL = f'http://{AppConfig.CODE_GENERATION_SERVICE_HOST}:{AppConfig.CODE_GENERATION_SERVICE_PORT}'


@code_bp.route('/code/connect', methods=['POST'])
def connect_repository():
    """
    POST /api/code/connect - Connect to a code repository
    Proxy to code-generation-service
    
    Expected JSON payload:
    {
        "type": "git|github|local",
        "url": "repository_url",
        "branch": "main",
        "credentials": {
            "username": "username",
            "token": "access_token"
        }
    }
    
    Returns:
        JSON response with connection result
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "error": "Request body is required",
                "status": "error"
            }), 400

        # Transform UI request format to code-generation-service format
        if 'provider_id' in data and 'token_id' in data:
            # This is a request from the UI with MCP provider data
            transformed_data = {
                "type": "github",  # Assume GitHub for MCP provider
                "url": data.get('repository_url'),
                "branch": data.get('branch', 'main'),
                "session_id": data.get('token_id')  # Use token_id as session_id
            }
        else:
            # This is a direct API call, use as-is
            transformed_data = data

        # Proxy request to code-generation-service
        response = requests.post(
            f"{CODE_SERVICE_URL}/code/connect",
            json=transformed_data,
            timeout=60  # Repository cloning can take time
        )
        
        return jsonify(response.json()), response.status_code
        
    except requests.RequestException as e:
        return jsonify({
            "error": f"Failed to connect to code generation service: {str(e)}",
            "status": "error",
            "timestamp": int(time.time() * 1000)
        }), 500
    except Exception as e:
        return jsonify({
            "error": f"Failed to connect repository: {str(e)}",
            "status": "error",
            "timestamp": int(time.time() * 1000)
        }), 500


@code_bp.route('/code/repositories', methods=['GET'])
def get_repositories():
    """
    GET /api/code/repositories - Get list of connected repositories
    Proxy to code-generation-service

    Returns:
        JSON response with repositories list
    """
    try:
        # Proxy request to code-generation-service
        response = requests.get(
            f"{CODE_SERVICE_URL}/code/repositories",
            timeout=30
        )

        return jsonify(response.json()), response.status_code

    except requests.RequestException as e:
        return jsonify({
            "error": f"Failed to connect to code generation service: {str(e)}",
            "status": "error",
            "timestamp": int(time.time() * 1000)
        }), 500
    except Exception as e:
        return jsonify({
            "error": f"Failed to get repositories: {str(e)}",
            "status": "error",
            "timestamp": int(time.time() * 1000)
        }), 500


@code_bp.route('/code/repositories/<repository_id>', methods=['DELETE'])
def delete_repository(repository_id):
    """
    DELETE /api/code/repositories/<repository_id> - Delete a connected repository
    Proxy to code-generation-service

    Returns:
        JSON response with deletion result
    """
    try:
        # Proxy request to code-generation-service
        response = requests.delete(
            f"{CODE_SERVICE_URL}/code/repositories/{repository_id}",
            timeout=30
        )

        return jsonify(response.json()), response.status_code

    except requests.RequestException as e:
        return jsonify({
            "error": f"Failed to connect to code generation service: {str(e)}",
            "status": "error",
            "timestamp": int(time.time() * 1000)
        }), 500
    except Exception as e:
        return jsonify({
            "error": f"Failed to delete repository: {str(e)}",
            "status": "error",
            "timestamp": int(time.time() * 1000)
        }), 500


@code_bp.route('/code/analyze', methods=['POST'])
def analyze_repository():
    """
    POST /api/code/analyze - Analyze a connected repository
    Proxy to code-generation-service
    
    Expected JSON payload:
    {
        "repository_id": "repo_id",
        "language": "python"
    }
    
    Returns:
        JSON response with analysis result
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "error": "Request body is required",
                "status": "error"
            }), 400

        # Proxy request to code-generation-service
        response = requests.post(
            f"{CODE_SERVICE_URL}/code/analyze",
            json=data,
            timeout=120  # Analysis can take time
        )
        
        return jsonify(response.json()), response.status_code
        
    except requests.RequestException as e:
        return jsonify({
            "error": f"Failed to connect to code generation service: {str(e)}",
            "status": "error",
            "timestamp": int(time.time() * 1000)
        }), 500
    except Exception as e:
        return jsonify({
            "error": f"Failed to analyze repository: {str(e)}",
            "status": "error",
            "timestamp": int(time.time() * 1000)
        }), 500


@code_bp.route('/code/files', methods=['GET'])
def list_repository_files():
    """
    GET /api/code/files - List files in a connected repository
    Proxy to code-generation-service
    
    Query parameters:
    - repository_id: Repository ID
    
    Returns:
        JSON response with files list
    """
    try:
        # Forward query parameters
        params = dict(request.args)
        
        # Proxy request to code-generation-service
        response = requests.get(
            f"{CODE_SERVICE_URL}/code/files",
            params=params,
            timeout=30
        )
        
        return jsonify(response.json()), response.status_code
        
    except requests.RequestException as e:
        return jsonify({
            "error": f"Failed to connect to code generation service: {str(e)}",
            "status": "error",
            "timestamp": int(time.time() * 1000)
        }), 500
    except Exception as e:
        return jsonify({
            "error": f"Failed to list repository files: {str(e)}",
            "status": "error",
            "timestamp": int(time.time() * 1000)
        }), 500


@code_bp.route('/code/file', methods=['GET'])
def get_file_content():
    """
    GET /api/code/file - Get content of a specific file
    Proxy to code-generation-service
    
    Query parameters:
    - repository_id: Repository ID
    - file_path: Path to file
    
    Returns:
        JSON response with file content
    """
    try:
        # Forward query parameters
        params = dict(request.args)
        
        # Proxy request to code-generation-service
        response = requests.get(
            f"{CODE_SERVICE_URL}/code/file",
            params=params,
            timeout=30
        )
        
        return jsonify(response.json()), response.status_code
        
    except requests.RequestException as e:
        return jsonify({
            "error": f"Failed to connect to code generation service: {str(e)}",
            "status": "error",
            "timestamp": int(time.time() * 1000)
        }), 500
    except Exception as e:
        return jsonify({
            "error": f"Failed to get file content: {str(e)}",
            "status": "error",
            "timestamp": int(time.time() * 1000)
        }), 500


@code_bp.route('/code/cleanup', methods=['POST'])
def cleanup_repository():
    """
    POST /api/code/cleanup - Clean up temporary repository files
    Proxy to code-generation-service
    
    Expected JSON payload:
    {
        "repository_id": "repo_id"
    }
    
    Returns:
        JSON response with cleanup result
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "error": "Request body is required",
                "status": "error"
            }), 400

        # Proxy request to code-generation-service
        response = requests.post(
            f"{CODE_SERVICE_URL}/code/cleanup",
            json=data,
            timeout=30
        )
        
        return jsonify(response.json()), response.status_code
        
    except requests.RequestException as e:
        return jsonify({
            "error": f"Failed to connect to code generation service: {str(e)}",
            "status": "error",
            "timestamp": int(time.time() * 1000)
        }), 500
    except Exception as e:
        return jsonify({
            "error": f"Failed to cleanup repository: {str(e)}",
            "status": "error",
            "timestamp": int(time.time() * 1000)
        }), 500


@code_bp.route('/code/generate', methods=['POST'])
def generate_code():
    """
    POST /api/code/generate - Generate code based on repository context
    Proxy to code-generation-service
    
    Expected JSON payload:
    {
        "repository_id": "repo_id",
        "requirements": "code generation requirements",
        "language": "python",
        "file_type": "class",
        "context_files": ["file1.py", "file2.py"]
    }
    
    Returns:
        JSON response with generated code
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "error": "Request body is required",
                "status": "error"
            }), 400

        # Proxy request to code-generation-service
        response = requests.post(
            f"{CODE_SERVICE_URL}/code/generate",
            json=data,
            timeout=120  # Code generation can take time
        )
        
        return jsonify(response.json()), response.status_code
        
    except requests.RequestException as e:
        return jsonify({
            "error": f"Failed to connect to code generation service: {str(e)}",
            "status": "error",
            "timestamp": int(time.time() * 1000)
        }), 500
    except Exception as e:
        return jsonify({
            "error": f"Failed to generate code: {str(e)}",
            "status": "error",
            "timestamp": int(time.time() * 1000)
        }), 500
