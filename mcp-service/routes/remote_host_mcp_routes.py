"""
Remote Host MCP Routes
API endpoints for managing remote host connections as MCP providers
"""

from flask import Blueprint, request, jsonify
import logging
from services.remote_host_mcp_service import RemoteHostMCPService

logger = logging.getLogger(__name__)

remote_host_mcp_bp = Blueprint('remote_host_mcp', __name__)
remote_host_service = RemoteHostMCPService()

@remote_host_mcp_bp.route('/test', methods=['GET'])
def test_route():
    """Simple test route"""
    return {"status": "success", "message": "Remote host MCP routes are working"}

@remote_host_mcp_bp.route('/remote-host/connections', methods=['GET'])
def get_remote_host_connections():
    """Get all remote host connections"""
    try:
        connections = remote_host_service.get_all_connections()
        return jsonify({
            "status": "success",
            "connections": connections,
            "count": len(connections)
        })
    except Exception as e:
        logger.error(f"Error getting remote host connections: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Failed to get connections: {str(e)}"
        }), 500

@remote_host_mcp_bp.route('/remote-host/connections', methods=['POST'])
def add_remote_host_connection():
    """Add a new remote host connection"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'protocol', 'host']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "status": "error",
                    "message": f"Missing required field: {field}"
                }), 400
        
        # Validate protocol
        supported_protocols = ['ssh', 'sftp', 'ftp', 'http', 'https', 'rsync']
        if data['protocol'].lower() not in supported_protocols:
            return jsonify({
                "status": "error",
                "message": f"Unsupported protocol. Supported: {', '.join(supported_protocols)}"
            }), 400
        
        result = remote_host_service.add_remote_host(data)
        
        if result['status'] == 'success':
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error adding remote host connection: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Failed to add connection: {str(e)}"
        }), 500

@remote_host_mcp_bp.route('/remote-host/connections/<connection_id>', methods=['GET'])
def get_remote_host_connection(connection_id):
    """Get specific remote host connection"""
    try:
        connection = remote_host_service.get_connection(connection_id)
        
        if not connection:
            return jsonify({
                "status": "error",
                "message": "Connection not found"
            }), 404
        
        # Remove sensitive data from response
        safe_connection = {k: v for k, v in connection.items() 
                          if k not in ['encrypted_password', 'encrypted_private_key']}
        
        return jsonify({
            "status": "success",
            "connection": safe_connection
        })
        
    except Exception as e:
        logger.error(f"Error getting remote host connection: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Failed to get connection: {str(e)}"
        }), 500

@remote_host_mcp_bp.route('/remote-host/connections/<connection_id>/test', methods=['POST'])
def test_remote_host_connection(connection_id):
    """Test remote host connection"""
    try:
        result = remote_host_service.test_connection(connection_id)
        
        status_code = 200 if result['status'] == 'success' else 400
        return jsonify(result), status_code
        
    except Exception as e:
        logger.error(f"Error testing remote host connection: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Connection test failed: {str(e)}"
        }), 500

@remote_host_mcp_bp.route('/remote-host/test-config', methods=['POST'])
def test_remote_host_config():
    """Test remote host connection configuration without saving"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "status": "error",
                "message": "No configuration data provided"
            }), 400

        # Test the configuration directly
        result = remote_host_service.test_connection_config(data)

        status_code = 200 if result['status'] == 'success' else 400
        return jsonify(result), status_code

    except Exception as e:
        logger.error(f"Error testing remote host configuration: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Failed to test configuration: {str(e)}"
        }), 500

@remote_host_mcp_bp.route('/remote-host/connections/<connection_id>/sync-session', methods=['POST'])
def create_sync_session(connection_id):
    """Create sync session for remote-host-syncer"""
    try:
        result = remote_host_service.create_sync_session(connection_id)
        
        status_code = 200 if result['status'] == 'success' else 400
        return jsonify(result), status_code
        
    except Exception as e:
        logger.error(f"Error creating sync session: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Failed to create sync session: {str(e)}"
        }), 500

@remote_host_mcp_bp.route('/remote-host/test-delete/<connection_id>', methods=['GET'])
def test_delete_route(connection_id):
    """Test route to see if routes are working"""
    print(f"TEST ROUTE CALLED FOR CONNECTION: {connection_id}")
    return {"status": "success", "message": f"Test route called for {connection_id}"}

@remote_host_mcp_bp.route('/remote-host/test-delete-real/<connection_id>', methods=['DELETE'])
def test_delete_real_route(connection_id):
    """Test DELETE route to see if DELETE method works"""
    logger.info(f"🧪 TEST DELETE ROUTE CALLED FOR CONNECTION: {connection_id}")
    print(f"🧪 TEST DELETE ROUTE CALLED FOR CONNECTION: {connection_id}")
    import sys
    sys.stdout.flush()
    return {"status": "success", "message": f"Test DELETE route called for {connection_id}"}

@remote_host_mcp_bp.route('/remote-host/connections/<connection_id>', methods=['DELETE'])
def delete_remote_host_connection_v2(connection_id):
    """Delete remote host connection"""
    logger.info("=" * 50)
    logger.info(f"🗑️  DELETE ROUTE CALLED FOR CONNECTION: {connection_id}")
    logger.info("=" * 50)
    print("=" * 50)
    print(f"🗑️  DELETE ROUTE CALLED FOR CONNECTION: {connection_id}")
    print("=" * 50)
    import sys
    sys.stdout.flush()
    try:
        logger.info(f"🔄 Calling delete_connection service method...")
        print(f"🔄 Calling delete_connection service method...")
        sys.stdout.flush()
        result = remote_host_service.delete_connection(connection_id)
        logger.info(f"✅ Service method returned: {result}")
        print(f"✅ Service method returned: {result}")
        sys.stdout.flush()

        if result['status'] == 'error':
            if 'not found' in result['message'].lower():
                return jsonify(result), 404
            else:
                return jsonify(result), 500

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error deleting remote host connection: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Failed to delete connection: {str(e)}"
        }), 500

@remote_host_mcp_bp.route('/remote-host/providers', methods=['GET'])
def get_remote_host_providers():
    """Get remote host as MCP provider info"""
    try:
        connections = remote_host_service.get_all_connections()
        
        # Format as MCP provider resources
        resources = []
        for conn in connections:
            resources.append({
                "id": conn['id'],
                "name": conn['name'],
                "type": "remote_host",
                "protocol": conn['protocol'],
                "host": conn['host'],
                "status": conn['status'],
                "last_tested": conn.get('last_tested'),
                "resource_count": 0,  # TODO: Get actual resource count
                "sync_enabled": conn['status'] == 'active'
            })
        
        return jsonify({
            "status": "success",
            "provider": {
                "name": "Remote Host Provider",
                "type": "remote_host",
                "description": "Connect to remote hosts via SSH, SFTP, FTP, HTTP, RSYNC",
                "supported_protocols": ["ssh", "sftp", "ftp", "http", "https", "rsync"],
                "resources": resources,
                "total_resources": len(resources)
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting remote host providers: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Failed to get providers: {str(e)}"
        }), 500

@remote_host_mcp_bp.route('/remote-host/sync-credentials/<session_id>', methods=['GET'])
def get_sync_credentials(session_id):
    """Get credentials for active sync session (used by remote-host-syncer)"""
    try:
        # This endpoint is called by remote-host-syncer to get credentials
        # TODO: Implement session validation and credential retrieval
        return jsonify({
            "status": "success",
            "message": "Sync credentials endpoint - implementation needed"
        })
        
    except Exception as e:
        logger.error(f"Error getting sync credentials: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Failed to get credentials: {str(e)}"
        }), 500

@remote_host_mcp_bp.route('/remote-host/connections/<connection_id>/files', methods=['GET'])
def list_connection_files(connection_id):
    """List files from a remote host connection"""
    try:
        path = request.args.get('path', None)
        result = remote_host_service.list_files(connection_id, path)

        if result['status'] == 'success':
            return jsonify(result)
        else:
            return jsonify(result), 400

    except Exception as e:
        logger.error(f"Error listing files for connection {connection_id}: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Failed to list files: {str(e)}"
        }), 500

@remote_host_mcp_bp.route('/remote-host/connections/<connection_id>/files/content', methods=['POST'])
def get_file_content(connection_id):
    """Get file content from a remote host connection"""
    try:
        data = request.get_json()
        file_path = data.get('file_path')

        if not file_path:
            return jsonify({
                "status": "error",
                "message": "file_path is required"
            }), 400

        result = remote_host_service.get_file_content(connection_id, file_path)

        if result['status'] == 'success':
            return jsonify(result)
        else:
            return jsonify(result), 400

    except Exception as e:
        logger.error(f"Error getting file content for connection {connection_id}: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Failed to get file content: {str(e)}"
        }), 500
