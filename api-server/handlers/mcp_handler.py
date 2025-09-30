"""
MCP Handler - Handles MCP (Model Context Protocol) requests
"""

import json
import logging
import requests
from flask import request, jsonify
from typing import Dict, Any, Optional

from config.app_config import AppConfig


class MCPHandler:
    """Handler for MCP operations"""
    
    @staticmethod
    def _get_mcp_service_url() -> str:
        """Get MCP service URL"""
        return f"http://{AppConfig.MCP_SERVICE_HOST}:{AppConfig.MCP_SERVICE_PORT}"
    
    @staticmethod
    def _make_mcp_request(method: str, endpoint: str, data: Optional[Dict] = None, 
                         params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make request to MCP service
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request data
            params: Query parameters
            
        Returns:
            Response from MCP service
        """
        try:
            url = f"{MCPHandler._get_mcp_service_url()}{endpoint}"
            
            response = requests.request(
                method=method,
                url=url,
                json=data,
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "status": "error",
                    "error": f"MCP service error: {response.status_code}",
                    "details": response.text
                }
                
        except requests.RequestException as e:
            logging.error(f"❌ MCP service request failed: {str(e)}")
            return {
                "status": "error",
                "error": f"Failed to connect to MCP service: {str(e)}"
            }
        except Exception as e:
            logging.error(f"❌ MCP request failed: {str(e)}")
            return {
                "status": "error",
                "error": f"MCP request failed: {str(e)}"
            }
    
    @staticmethod
    def handle_get_providers():
        """Handle GET /api/mcp/providers"""
        try:
            result = MCPHandler._make_mcp_request('GET', '/providers')
            return jsonify(result)
            
        except Exception as e:
            logging.error(f"❌ Get providers failed: {str(e)}")
            return jsonify({
                "status": "error",
                "error": f"Failed to get providers: {str(e)}"
            }), 500
    
    @staticmethod
    def handle_configure_provider(provider: str):
        """Handle POST /api/mcp/provider/<provider>/config"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({
                    "status": "error",
                    "error": "Request body is required"
                }), 400
            
            result = MCPHandler._make_mcp_request('POST', f'/provider/{provider}/config', data)
            return jsonify(result)
            
        except Exception as e:
            logging.error(f"❌ Configure provider failed: {str(e)}")
            return jsonify({
                "status": "error",
                "error": f"Failed to configure provider: {str(e)}"
            }), 500
    
    @staticmethod
    def handle_start_auth(provider: str):
        """Handle POST /api/mcp/provider/<provider>/auth"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({
                    "status": "error",
                    "error": "Request body is required"
                }), 400
            
            result = MCPHandler._make_mcp_request('POST', f'/provider/{provider}/auth', data)
            return jsonify(result)
            
        except Exception as e:
            logging.error(f"❌ Start auth failed: {str(e)}")
            return jsonify({
                "status": "error",
                "error": f"Failed to start authentication: {str(e)}"
            }), 500
    
    @staticmethod
    def handle_oauth_callback(provider: str):
        """Handle GET /api/mcp/oauth/<provider>/callback"""
        try:
            # Get query parameters
            code = request.args.get('code')
            state = request.args.get('state')
            
            if not code or not state:
                return jsonify({
                    "status": "error",
                    "error": "Missing required parameters: code and state"
                }), 400
            
            params = {'code': code, 'state': state}
            result = MCPHandler._make_mcp_request('GET', f'/oauth/{provider}/callback', params=params)
            
            # If successful, redirect to success page or return JSON
            if result.get('status') == 'success':
                # For web interface, you might want to redirect to a success page
                # For API clients, return JSON
                return jsonify(result)
            else:
                return jsonify(result), 400
            
        except Exception as e:
            logging.error(f"❌ OAuth callback failed: {str(e)}")
            return jsonify({
                "status": "error",
                "error": f"OAuth callback failed: {str(e)}"
            }), 500
    
    @staticmethod
    def handle_list_connections():
        """Handle GET /api/mcp/connections"""
        try:
            result = MCPHandler._make_mcp_request('GET', '/connections')
            return jsonify(result)
            
        except Exception as e:
            logging.error(f"❌ List connections failed: {str(e)}")
            return jsonify({
                "status": "error",
                "error": f"Failed to list connections: {str(e)}"
            }), 500
    
    @staticmethod
    def handle_connection_status(connection_id: str):
        """Handle GET /api/mcp/connection/<connection_id>/status"""
        try:
            result = MCPHandler._make_mcp_request('GET', f'/connection/{connection_id}/status')
            return jsonify(result)
            
        except Exception as e:
            logging.error(f"❌ Get connection status failed: {str(e)}")
            return jsonify({
                "status": "error",
                "error": f"Failed to get connection status: {str(e)}"
            }), 500
    
    @staticmethod
    def handle_disconnect_connection(connection_id: str):
        """Handle POST /api/mcp/connection/<connection_id>/disconnect"""
        try:
            result = MCPHandler._make_mcp_request('POST', f'/connection/{connection_id}/disconnect')
            return jsonify(result)
            
        except Exception as e:
            logging.error(f"❌ Disconnect connection failed: {str(e)}")
            return jsonify({
                "status": "error",
                "error": f"Failed to disconnect connection: {str(e)}"
            }), 500
    
    @staticmethod
    def handle_list_tools(connection_id: str):
        """Handle GET /api/mcp/connection/<connection_id>/tools"""
        try:
            result = MCPHandler._make_mcp_request('GET', f'/connection/{connection_id}/tools')
            return jsonify(result)
            
        except Exception as e:
            logging.error(f"❌ List tools failed: {str(e)}")
            return jsonify({
                "status": "error",
                "error": f"Failed to list tools: {str(e)}"
            }), 500
    
    @staticmethod
    def handle_tool_execution(connection_id: str):
        """Handle POST /api/mcp/connection/<connection_id>/execute"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({
                    "status": "error",
                    "error": "Request body is required"
                }), 400
            
            result = MCPHandler._make_mcp_request('POST', f'/connection/{connection_id}/execute', data)
            return jsonify(result)
            
        except Exception as e:
            logging.error(f"❌ Tool execution failed: {str(e)}")
            return jsonify({
                "status": "error",
                "error": f"Failed to execute tool: {str(e)}"
            }), 500
    
    @staticmethod
    def handle_list_resources(connection_id: str):
        """Handle GET /api/mcp/connection/<connection_id>/resources"""
        try:
            result = MCPHandler._make_mcp_request('GET', f'/connection/{connection_id}/resources')
            return jsonify(result)
            
        except Exception as e:
            logging.error(f"❌ List resources failed: {str(e)}")
            return jsonify({
                "status": "error",
                "error": f"Failed to list resources: {str(e)}"
            }), 500
    
    @staticmethod
    def handle_list_tokens():
        """Handle GET /api/mcp/tokens"""
        try:
            result = MCPHandler._make_mcp_request('GET', '/tokens')
            return jsonify(result)
            
        except Exception as e:
            logging.error(f"❌ List tokens failed: {str(e)}")
            return jsonify({
                "status": "error",
                "error": f"Failed to list tokens: {str(e)}"
            }), 500
    
    @staticmethod
    def handle_revoke_token(token_id: str):
        """Handle POST /api/mcp/token/<token_id>/revoke"""
        try:
            result = MCPHandler._make_mcp_request('POST', f'/token/{token_id}/revoke')
            return jsonify(result)
            
        except Exception as e:
            logging.error(f"❌ Revoke token failed: {str(e)}")
            return jsonify({
                "status": "error",
                "error": f"Failed to revoke token: {str(e)}"
            }), 500

    # Legacy MCP methods (for backward compatibility)

    @staticmethod
    def handle_mcp_connect():
        """Handle POST /api/mcp/connect (legacy)"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({
                    "status": "error",
                    "error": "Request body is required"
                }), 400

            result = MCPHandler._make_mcp_request('POST', '/connect', data)
            return jsonify(result)

        except Exception as e:
            logging.error(f"❌ MCP connect failed: {str(e)}")
            return jsonify({
                "status": "error",
                "error": f"Failed to connect: {str(e)}"
            }), 500

    @staticmethod
    def handle_mcp_disconnect():
        """Handle POST /api/mcp/disconnect (legacy)"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({
                    "status": "error",
                    "error": "Request body is required"
                }), 400

            result = MCPHandler._make_mcp_request('POST', '/disconnect', data)
            return jsonify(result)

        except Exception as e:
            logging.error(f"❌ MCP disconnect failed: {str(e)}")
            return jsonify({
                "status": "error",
                "error": f"Failed to disconnect: {str(e)}"
            }), 500

    @staticmethod
    def handle_store_config():
        """Handle POST /api/mcp/config"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({
                    "status": "error",
                    "error": "Request body is required"
                }), 400

            result = MCPHandler._make_mcp_request('POST', '/config', data)
            return jsonify(result)

        except Exception as e:
            logging.error(f"❌ Store config failed: {str(e)}")
            return jsonify({
                "status": "error",
                "error": f"Failed to store config: {str(e)}"
            }), 500

    @staticmethod
    def handle_get_config(config_id: str):
        """Handle GET /api/mcp/config/<config_id>"""
        try:
            result = MCPHandler._make_mcp_request('GET', f'/config/{config_id}')
            return jsonify(result)

        except Exception as e:
            logging.error(f"❌ Get config failed: {str(e)}")
            return jsonify({
                "status": "error",
                "error": f"Failed to get config: {str(e)}"
            }), 500

    @staticmethod
    def handle_delete_config(config_id: str):
        """Handle DELETE /api/mcp/config/<config_id>"""
        try:
            result = MCPHandler._make_mcp_request('DELETE', f'/config/{config_id}')
            return jsonify(result)

        except Exception as e:
            logging.error(f"❌ Delete config failed: {str(e)}")
            return jsonify({
                "status": "error",
                "error": f"Failed to delete config: {str(e)}"
            }), 500

    @staticmethod
    def handle_list_configs():
        """Handle GET /api/mcp/configs"""
        try:
            result = MCPHandler._make_mcp_request('GET', '/configs')
            return jsonify(result)

        except Exception as e:
            logging.error(f"❌ List configs failed: {str(e)}")
            return jsonify({
                "status": "error",
                "error": f"Failed to list configs: {str(e)}"
            }), 500

    @staticmethod
    def handle_mcp_test():
        """Handle GET /api/mcp/test"""
        try:
            result = MCPHandler._make_mcp_request('GET', '/test')
            return jsonify(result)

        except Exception as e:
            logging.error(f"❌ MCP test failed: {str(e)}")
            return jsonify({
                "status": "error",
                "error": f"Failed to test MCP service: {str(e)}"
            }), 500

    @staticmethod
    def handle_connection_suggestions():
        """Handle POST /api/mcp/suggest"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({
                    "status": "error",
                    "error": "Request body is required"
                }), 400

            result = MCPHandler._make_mcp_request('POST', '/suggest', data)
            return jsonify(result)

        except Exception as e:
            logging.error(f"❌ Connection suggestions failed: {str(e)}")
            return jsonify({
                "status": "error",
                "error": f"Failed to get suggestions: {str(e)}"
            }), 500

    @staticmethod
    def handle_request_routing():
        """Handle POST /api/mcp/route"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({
                    "status": "error",
                    "error": "Request body is required"
                }), 400

            result = MCPHandler._make_mcp_request('POST', '/route', data)
            return jsonify(result)

        except Exception as e:
            logging.error(f"❌ Request routing failed: {str(e)}")
            return jsonify({
                "status": "error",
                "error": f"Failed to route request: {str(e)}"
            }), 500

    # GitHub-specific handlers

    @staticmethod
    def handle_github_repositories():
        """Handle GET /api/mcp/github/repositories"""
        try:
            # Get query parameters
            token_id = request.args.get('token_id')
            repo_type = request.args.get('type', 'owner')
            sort = request.args.get('sort', 'updated')
            per_page = request.args.get('per_page', '30')

            if not token_id:
                return jsonify({
                    "status": "error",
                    "error": "token_id parameter is required"
                }), 400

            params = {
                'token_id': token_id,
                'type': repo_type,
                'sort': sort,
                'per_page': per_page
            }

            result = MCPHandler._make_mcp_request('GET', '/github/repositories', params=params)
            return jsonify(result)

        except Exception as e:
            logging.error(f"❌ GitHub repositories failed: {str(e)}")
            return jsonify({
                "status": "error",
                "error": f"Failed to get repositories: {str(e)}"
            }), 500

    @staticmethod
    def handle_github_repository_details(owner: str, repo: str):
        """Handle GET /api/mcp/github/repository/<owner>/<repo>"""
        try:
            token_id = request.args.get('token_id')

            if not token_id:
                return jsonify({
                    "status": "error",
                    "error": "token_id parameter is required"
                }), 400

            params = {
                'token_id': token_id,
                'owner': owner,
                'repo': repo
            }

            result = MCPHandler._make_mcp_request('GET', f'/github/repository/{owner}/{repo}', params=params)
            return jsonify(result)

        except Exception as e:
            logging.error(f"❌ GitHub repository details failed: {str(e)}")
            return jsonify({
                "status": "error",
                "error": f"Failed to get repository details: {str(e)}"
            }), 500

    @staticmethod
    def handle_github_repository_clone(owner: str, repo: str):
        """Handle POST /api/mcp/github/repository/<owner>/<repo>/clone"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({
                    "status": "error",
                    "error": "Request body is required"
                }), 400

            token_id = data.get('token_id')
            if not token_id:
                return jsonify({
                    "status": "error",
                    "error": "token_id is required"
                }), 400

            # Add owner and repo to the data
            data['owner'] = owner
            data['repo'] = repo

            result = MCPHandler._make_mcp_request('POST', f'/github/repository/{owner}/{repo}/clone', data)
            return jsonify(result)

        except Exception as e:
            logging.error(f"❌ GitHub repository clone failed: {str(e)}")
            return jsonify({
                "status": "error",
                "error": f"Failed to clone repository: {str(e)}"
            }), 500

    @staticmethod
    def handle_get_provider_resources(provider_id: str):
        """
        Handle GET /mcp/provider/<provider_id>/resources requests
        Get resources from MCP provider
        """
        try:
            # Forward query parameters (like token_id)
            params = request.args.to_dict()

            result = MCPHandler._make_mcp_request('GET', f'/provider/{provider_id}/resources', params=params)
            return jsonify(result)

        except Exception as e:
            logging.error(f"❌ Get provider resources failed: {str(e)}")
            return jsonify({
                "status": "error",
                "error": f"Failed to get provider resources: {str(e)}"
            }), 500
