"""
MCP Controller - Handles MCP (Model Context Protocol) operations
"""

import json
import uuid
import time
import logging
import asyncio
import subprocess
import threading
from typing import Dict, List, Optional, Any, Tuple
from flask import request, jsonify, current_app

from services.mcp_client_service import MCPClientService
from services.mcp_config_service import MCPConfigService


class MCPController:
    """Controller for handling MCP-related requests"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.mcp_client_service = MCPClientService()
        self.config_service = MCPConfigService()
        
    def connect_mcp(self) -> Tuple[Dict[str, Any], int]:
        """
        Handle POST /mcp/connect requests
        
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
            Tuple[Dict, int]: Response data and HTTP status code
        """
        try:
            data = request.get_json()
            if not data:
                return {
                    "status": "error",
                    "error": "No JSON data provided",
                    "timestamp": int(time.time() * 1000)
                }, 400
            
            # Use stored config if config_id provided
            if 'config_id' in data:
                config_result = self.config_service.get_config(data['config_id'])
                if config_result['status'] == 'success':
                    stored_config = config_result['config']
                    # Merge stored config with request data (request data takes precedence)
                    for key, value in stored_config.items():
                        if key not in data:
                            data[key] = value
            
            # Validate required fields
            required_fields = ['name', 'command']
            for field in required_fields:
                if field not in data:
                    return {
                        "status": "error",
                        "error": f"Missing required field: {field}",
                        "timestamp": int(time.time() * 1000)
                    }, 400
            
            # Extract connection parameters
            name = data['name']
            command = data['command']
            args = data.get('args', [])
            env = data.get('env', {})
            protocol = data.get('protocol', 'stdio')
            
            self.logger.info(f"🔌 Connecting to MCP server: {name}")
            
            # Connect to MCP server
            result = self.mcp_client_service.connect(
                name=name,
                command=command,
                args=args,
                env=env,
                protocol=protocol
            )
            
            if result['status'] == 'success':
                self.logger.info(f"✅ Successfully connected to MCP server: {name}")
                return {
                    "status": "success",
                    "message": f"Successfully connected to MCP server: {name}",
                    "connection_id": result['connection_id'],
                    "server_info": result.get('server_info', {}),
                    "available_tools": result.get('tools', []),
                    "available_resources": result.get('resources', []),
                    "timestamp": int(time.time() * 1000)
                }, 200
            else:
                self.logger.error(f"❌ Failed to connect to MCP server: {result.get('error')}")
                return {
                    "status": "error",
                    "error": result.get('error', 'Unknown connection error'),
                    "timestamp": int(time.time() * 1000)
                }, 500
                
        except Exception as e:
            self.logger.error(f"❌ Error in connect_mcp: {str(e)}")
            return {
                "status": "error",
                "error": f"Connection failed: {str(e)}",
                "timestamp": int(time.time() * 1000)
            }, 500

    def disconnect_mcp(self) -> Tuple[Dict[str, Any], int]:
        """
        Handle POST /mcp/disconnect requests

        Expected JSON payload:
        {
            "connection_id": "connection_uuid"
        }

        Returns:
            Tuple[Dict, int]: Response data and HTTP status code
        """
        try:
            data = request.get_json()
            if not data or 'connection_id' not in data:
                return {
                    "status": "error",
                    "error": "Missing connection_id",
                    "timestamp": int(time.time() * 1000)
                }, 400

            connection_id = data['connection_id']
            self.logger.info(f"🔌 Disconnecting from MCP server: {connection_id}")

            result = self.mcp_client_service.disconnect(connection_id)

            if result['status'] == 'success':
                self.logger.info(f"✅ Successfully disconnected from MCP server: {connection_id}")
                return {
                    "status": "success",
                    "message": f"Successfully disconnected from MCP server",
                    "connection_id": connection_id,
                    "timestamp": int(time.time() * 1000)
                }, 200
            else:
                return {
                    "status": "error",
                    "error": result.get('error', 'Unknown disconnection error'),
                    "timestamp": int(time.time() * 1000)
                }, 500

        except Exception as e:
            self.logger.error(f"❌ Error in disconnect_mcp: {str(e)}")
            return {
                "status": "error",
                "error": f"Disconnection failed: {str(e)}",
                "timestamp": int(time.time() * 1000)
            }, 500

    def list_connections(self) -> Tuple[Dict[str, Any], int]:
        """
        Handle GET /mcp/list requests

        Returns:
            Tuple[Dict, int]: Response data and HTTP status code
        """
        try:
            connections = self.mcp_client_service.list_connections()

            return {
                "status": "success",
                "connections": connections,
                "total_connections": len(connections),
                "timestamp": int(time.time() * 1000)
            }, 200

        except Exception as e:
            self.logger.error(f"❌ Error in list_connections: {str(e)}")
            return {
                "status": "error",
                "error": f"Failed to list connections: {str(e)}",
                "timestamp": int(time.time() * 1000)
            }, 500

    def get_connection_status(self, connection_id: str) -> Tuple[Dict[str, Any], int]:
        """
        Handle GET /mcp/status/<connection_id> requests

        Args:
            connection_id: The connection ID to check

        Returns:
            Tuple[Dict, int]: Response data and HTTP status code
        """
        try:
            status = self.mcp_client_service.get_connection_status(connection_id)

            if status:
                return {
                    "status": "success",
                    "connection_status": status,
                    "timestamp": int(time.time() * 1000)
                }, 200
            else:
                return {
                    "status": "error",
                    "error": "Connection not found",
                    "timestamp": int(time.time() * 1000)
                }, 404

        except Exception as e:
            self.logger.error(f"❌ Error in get_connection_status: {str(e)}")
            return {
                "status": "error",
                "error": f"Failed to get connection status: {str(e)}",
                "timestamp": int(time.time() * 1000)
            }, 500

    def execute_tool(self) -> Tuple[Dict[str, Any], int]:
        """
        Handle POST /mcp/execute requests

        Expected JSON payload:
        {
            "connection_id": "connection_uuid",
            "tool_name": "tool_name",
            "arguments": {"arg1": "value1", "arg2": "value2"}
        }

        Returns:
            Tuple[Dict, int]: Response data and HTTP status code
        """
        try:
            data = request.get_json()
            if not data:
                return {
                    "status": "error",
                    "error": "No JSON data provided",
                    "timestamp": int(time.time() * 1000)
                }, 400

            # Validate required fields
            required_fields = ['connection_id', 'tool_name']
            for field in required_fields:
                if field not in data:
                    return {
                        "status": "error",
                        "error": f"Missing required field: {field}",
                        "timestamp": int(time.time() * 1000)
                    }, 400

            connection_id = data['connection_id']
            tool_name = data['tool_name']
            arguments = data.get('arguments', {})

            self.logger.info(f"🔧 Executing tool '{tool_name}' on connection {connection_id}")

            result = self.mcp_client_service.execute_tool(
                connection_id=connection_id,
                tool_name=tool_name,
                arguments=arguments
            )

            if result['status'] == 'success':
                self.logger.info(f"✅ Successfully executed tool '{tool_name}'")
                return {
                    "status": "success",
                    "result": result.get('result'),
                    "tool_name": tool_name,
                    "connection_id": connection_id,
                    "timestamp": int(time.time() * 1000)
                }, 200
            else:
                self.logger.error(f"❌ Failed to execute tool '{tool_name}': {result.get('error')}")
                return {
                    "status": "error",
                    "error": result.get('error', 'Unknown execution error'),
                    "timestamp": int(time.time() * 1000)
                }, 500

        except Exception as e:
            self.logger.error(f"❌ Error in execute_tool: {str(e)}")
            return {
                "status": "error",
                "error": f"Tool execution failed: {str(e)}",
                "timestamp": int(time.time() * 1000)
            }, 500

    def list_tools(self, connection_id: str) -> Tuple[Dict[str, Any], int]:
        """
        Handle GET /mcp/tools/<connection_id> requests

        Args:
            connection_id: The connection ID to list tools for

        Returns:
            Tuple[Dict, int]: Response data and HTTP status code
        """
        try:
            tools = self.mcp_client_service.list_tools(connection_id)

            if tools is not None:
                return {
                    "status": "success",
                    "tools": tools,
                    "connection_id": connection_id,
                    "total_tools": len(tools),
                    "timestamp": int(time.time() * 1000)
                }, 200
            else:
                return {
                    "status": "error",
                    "error": "Connection not found",
                    "timestamp": int(time.time() * 1000)
                }, 404

        except Exception as e:
            self.logger.error(f"❌ Error in list_tools: {str(e)}")
            return {
                "status": "error",
                "error": f"Failed to list tools: {str(e)}",
                "timestamp": int(time.time() * 1000)
            }, 500

    def list_resources(self, connection_id: str) -> Tuple[Dict[str, Any], int]:
        """
        Handle GET /mcp/resources/<connection_id> requests

        Args:
            connection_id: The connection ID to list resources for

        Returns:
            Tuple[Dict, int]: Response data and HTTP status code
        """
        try:
            resources = self.mcp_client_service.list_resources(connection_id)

            if resources is not None:
                return {
                    "status": "success",
                    "resources": resources,
                    "connection_id": connection_id,
                    "total_resources": len(resources),
                    "timestamp": int(time.time() * 1000)
                }, 200
            else:
                return {
                    "status": "error",
                    "error": "Connection not found",
                    "timestamp": int(time.time() * 1000)
                }, 404

        except Exception as e:
            self.logger.error(f"❌ Error in list_resources: {str(e)}")
            return {
                "status": "error",
                "error": f"Failed to list resources: {str(e)}",
                "timestamp": int(time.time() * 1000)
            }, 500

    def store_config(self) -> Tuple[Dict[str, Any], int]:
        """
        Handle POST /mcp/config requests

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
            Tuple[Dict, int]: Response data and HTTP status code
        """
        try:
            data = request.get_json()
            if not data:
                return {
                    "status": "error",
                    "error": "No JSON data provided",
                    "timestamp": int(time.time() * 1000)
                }, 400

            # Validate required fields
            required_fields = ['name', 'command']
            for field in required_fields:
                if field not in data:
                    return {
                        "status": "error",
                        "error": f"Missing required field: {field}",
                        "timestamp": int(time.time() * 1000)
                    }, 400

            result = self.config_service.store_config(data)

            if result['status'] == 'success':
                self.logger.info(f"✅ Successfully stored MCP config: {data['name']}")
                return {
                    "status": "success",
                    "message": "Configuration stored successfully",
                    "config_id": result['config_id'],
                    "name": data['name'],
                    "timestamp": int(time.time() * 1000)
                }, 200
            else:
                return {
                    "status": "error",
                    "error": result.get('error', 'Unknown storage error'),
                    "timestamp": int(time.time() * 1000)
                }, 500

        except Exception as e:
            self.logger.error(f"❌ Error in store_config: {str(e)}")
            return {
                "status": "error",
                "error": f"Configuration storage failed: {str(e)}",
                "timestamp": int(time.time() * 1000)
            }, 500

    def get_config(self, config_id: str) -> Tuple[Dict[str, Any], int]:
        """
        Handle GET /mcp/config/<config_id> requests

        Args:
            config_id: The configuration ID to retrieve

        Returns:
            Tuple[Dict, int]: Response data and HTTP status code
        """
        try:
            result = self.config_service.get_config(config_id)

            if result['status'] == 'success':
                return {
                    "status": "success",
                    "config": result['config'],
                    "config_id": config_id,
                    "timestamp": int(time.time() * 1000)
                }, 200
            else:
                return {
                    "status": "error",
                    "error": result.get('error', 'Configuration not found'),
                    "timestamp": int(time.time() * 1000)
                }, 404

        except Exception as e:
            self.logger.error(f"❌ Error in get_config: {str(e)}")
            return {
                "status": "error",
                "error": f"Failed to retrieve configuration: {str(e)}",
                "timestamp": int(time.time() * 1000)
            }, 500

    def delete_config(self, config_id: str) -> Tuple[Dict[str, Any], int]:
        """
        Handle DELETE /mcp/config/<config_id> requests

        Args:
            config_id: The configuration ID to delete

        Returns:
            Tuple[Dict, int]: Response data and HTTP status code
        """
        try:
            result = self.config_service.delete_config(config_id)

            if result['status'] == 'success':
                self.logger.info(f"✅ Successfully deleted MCP config: {config_id}")
                return {
                    "status": "success",
                    "message": "Configuration deleted successfully",
                    "config_id": config_id,
                    "timestamp": int(time.time() * 1000)
                }, 200
            else:
                return {
                    "status": "error",
                    "error": result.get('error', 'Configuration not found'),
                    "timestamp": int(time.time() * 1000)
                }, 404

        except Exception as e:
            self.logger.error(f"❌ Error in delete_config: {str(e)}")
            return {
                "status": "error",
                "error": f"Failed to delete configuration: {str(e)}",
                "timestamp": int(time.time() * 1000)
            }, 500

    def list_configs(self) -> Tuple[Dict[str, Any], int]:
        """
        Handle GET /mcp/configs requests

        Returns:
            Tuple[Dict, int]: Response data and HTTP status code
        """
        try:
            configs = self.config_service.list_configs()

            return {
                "status": "success",
                "configs": configs,
                "total_configs": len(configs),
                "timestamp": int(time.time() * 1000)
            }, 200

        except Exception as e:
            self.logger.error(f"❌ Error in list_configs: {str(e)}")
            return {
                "status": "error",
                "error": f"Failed to list configurations: {str(e)}",
                "timestamp": int(time.time() * 1000)
            }, 500

    # Provider Management Methods

    def get_providers(self) -> Tuple[Dict[str, Any], int]:
        """
        Handle GET /providers requests

        Returns:
            Tuple[Dict, int]: Response data and HTTP status code
        """
        try:
            from config.settings import MCPConfig
            providers = MCPConfig.get_supported_providers()

            return {
                "status": "success",
                "providers": providers,
                "timestamp": int(time.time() * 1000)
            }, 200

        except Exception as e:
            self.logger.error(f"❌ Error in get_providers: {str(e)}")
            return {
                "status": "error",
                "error": f"Failed to get providers: {str(e)}",
                "timestamp": int(time.time() * 1000)
            }, 500

    def configure_provider(self, provider: str) -> Tuple[Dict[str, Any], int]:
        """
        Handle POST /provider/<provider>/config requests

        Args:
            provider: Provider name (e.g., 'github')

        Returns:
            Tuple[Dict, int]: Response data and HTTP status code
        """
        try:
            from flask import request
            data = request.get_json()

            if not data:
                return {
                    "status": "error",
                    "error": "Request body is required",
                    "timestamp": int(time.time() * 1000)
                }, 400

            if provider == 'github':
                # Configure GitHub OAuth
                client_id = data.get('client_id')
                client_secret = data.get('client_secret')
                redirect_uri = data.get('redirect_uri')
                scope = data.get('scope', 'repo,read:user')

                if not client_id or not client_secret or not redirect_uri:
                    return {
                        "status": "error",
                        "error": "client_id, client_secret, and redirect_uri are required",
                        "timestamp": int(time.time() * 1000)
                    }, 400

                # Store OAuth configuration
                from services.github_oauth_service import GitHubOAuthService
                oauth_service = GitHubOAuthService()
                config_id = oauth_service.store_oauth_config(client_id, client_secret, redirect_uri, scope)

                return {
                    "status": "success",
                    "config_id": config_id,
                    "provider": provider,
                    "message": "Provider configured successfully",
                    "timestamp": int(time.time() * 1000)
                }, 200

            elif provider == 'database':
                # Configure Database Provider
                from services.database_mcp_service import DatabaseMCPService
                db_service = DatabaseMCPService()
                result = db_service.configure_provider(data)

                if result['status'] == 'success':
                    return {
                        "status": "success",
                        "config_id": result['config_id'],
                        "provider": provider,
                        "message": result['message'],
                        "timestamp": int(time.time() * 1000)
                    }, 200
                else:
                    return {
                        "status": "error",
                        "error": result['error'],
                        "timestamp": int(time.time() * 1000)
                    }, 400

            elif provider == 'document_upload':
                # Configure Document Upload Provider
                from services.document_upload_mcp_service import DocumentUploadMCPService
                doc_service = DocumentUploadMCPService()
                result = doc_service.configure_provider(data)

                if result['status'] == 'success':
                    return {
                        "status": "success",
                        "config_id": result['config_id'],
                        "provider": provider,
                        "message": result['message'],
                        "storage_path": result.get('storage_path'),
                        "max_file_size_mb": result.get('max_file_size_mb'),
                        "allowed_extensions": result.get('allowed_extensions'),
                        "timestamp": int(time.time() * 1000)
                    }, 200
                else:
                    return {
                        "status": "error",
                        "error": result['error'],
                        "timestamp": int(time.time() * 1000)
                    }, 400

            else:
                return {
                    "status": "error",
                    "error": f"Provider '{provider}' not supported",
                    "timestamp": int(time.time() * 1000)
                }, 400

        except Exception as e:
            self.logger.error(f"❌ Error in configure_provider: {str(e)}")
            return {
                "status": "error",
                "error": f"Failed to configure provider: {str(e)}",
                "timestamp": int(time.time() * 1000)
            }, 500

    def start_provider_auth(self, provider: str) -> Tuple[Dict[str, Any], int]:
        """
        Handle POST /provider/<provider>/auth requests

        Args:
            provider: Provider name (e.g., 'github')

        Returns:
            Tuple[Dict, int]: Response data and HTTP status code
        """
        try:
            from flask import request
            data = request.get_json()

            if not data:
                return {
                    "status": "error",
                    "error": "Request body is required",
                    "timestamp": int(time.time() * 1000)
                }, 400

            config_id = data.get('config_id')
            if not config_id:
                return {
                    "status": "error",
                    "error": "config_id is required",
                    "timestamp": int(time.time() * 1000)
                }, 400

            if provider == 'github':
                from services.github_oauth_service import GitHubOAuthService
                oauth_service = GitHubOAuthService()
                result = oauth_service.generate_auth_url(config_id)

                if result['status'] == 'success':
                    return {
                        "status": "success",
                        "auth_url": result['auth_url'],
                        "state": result['state'],
                        "provider": provider,
                        "timestamp": int(time.time() * 1000)
                    }, 200
                else:
                    return {
                        "status": "error",
                        "error": result['error'],
                        "timestamp": int(time.time() * 1000)
                    }, 400
            else:
                return {
                    "status": "error",
                    "error": f"Provider '{provider}' not supported",
                    "timestamp": int(time.time() * 1000)
                }, 400

        except Exception as e:
            self.logger.error(f"❌ Error in start_provider_auth: {str(e)}")
            return {
                "status": "error",
                "error": f"Failed to start authentication: {str(e)}",
                "timestamp": int(time.time() * 1000)
            }, 500

    def handle_oauth_callback(self, provider: str) -> Tuple[Dict[str, Any], int]:
        """
        Handle GET /oauth/<provider>/callback requests

        Args:
            provider: Provider name (e.g., 'github')

        Returns:
            Tuple[Dict, int]: Response data and HTTP status code
        """
        try:
            from flask import request

            code = request.args.get('code')
            state = request.args.get('state')

            if not code or not state:
                return {
                    "status": "error",
                    "error": "Missing required parameters: code and state",
                    "timestamp": int(time.time() * 1000)
                }, 400

            if provider == 'github':
                from services.github_oauth_service import GitHubOAuthService
                oauth_service = GitHubOAuthService()
                result = oauth_service.handle_oauth_callback(code, state)

                if result['status'] == 'success':
                    return {
                        "status": "success",
                        "token_id": result['token_id'],
                        "user_info": result['user_info'],
                        "scopes": result['scopes'],
                        "provider": provider,
                        "timestamp": int(time.time() * 1000)
                    }, 200
                else:
                    return {
                        "status": "error",
                        "error": result['error'],
                        "timestamp": int(time.time() * 1000)
                    }, 400
            else:
                return {
                    "status": "error",
                    "error": f"Provider '{provider}' not supported",
                    "timestamp": int(time.time() * 1000)
                }, 400

        except Exception as e:
            self.logger.error(f"❌ Error in handle_oauth_callback: {str(e)}")
            return {
                "status": "error",
                "error": f"OAuth callback failed: {str(e)}",
                "timestamp": int(time.time() * 1000)
            }, 500

    def list_tokens(self) -> Tuple[Dict[str, Any], int]:
        """
        Handle GET /tokens requests

        Returns:
            Tuple[Dict, int]: Response data and HTTP status code
        """
        try:
            from services.github_oauth_service import GitHubOAuthService
            oauth_service = GitHubOAuthService()
            tokens = oauth_service.list_tokens()

            return {
                "status": "success",
                "tokens": tokens,
                "total_tokens": len(tokens),
                "timestamp": int(time.time() * 1000)
            }, 200

        except Exception as e:
            self.logger.error(f"❌ Error in list_tokens: {str(e)}")
            return {
                "status": "error",
                "error": f"Failed to list tokens: {str(e)}",
                "timestamp": int(time.time() * 1000)
            }, 500

    def get_token(self, token_id: str) -> Tuple[Dict[str, Any], int]:
        """
        Handle GET /tokens/<token_id> requests

        Args:
            token_id: Token ID to retrieve

        Returns:
            Tuple[Dict, int]: Response data and HTTP status code
        """
        try:
            from services.github_oauth_service import GitHubOAuthService
            oauth_service = GitHubOAuthService()
            token_data = oauth_service.get_token_info(token_id)

            if not token_data:
                return {
                    "status": "error",
                    "error": "Token not found",
                    "timestamp": int(time.time() * 1000)
                }, 404

            return {
                "status": "success",
                "data": token_data,
                "timestamp": int(time.time() * 1000)
            }, 200

        except Exception as e:
            self.logger.error(f"Failed to get token {token_id}: {str(e)}")
            return {
                "status": "error",
                "error": f"Failed to get token: {str(e)}",
                "timestamp": int(time.time() * 1000)
            }, 500

    def revoke_token(self, token_id: str) -> Tuple[Dict[str, Any], int]:
        """
        Handle POST /token/<token_id>/revoke requests

        Args:
            token_id: Token ID to revoke

        Returns:
            Tuple[Dict, int]: Response data and HTTP status code
        """
        try:
            from services.github_oauth_service import GitHubOAuthService
            oauth_service = GitHubOAuthService()
            result = oauth_service.revoke_token(token_id)

            if result['status'] == 'success':
                return {
                    "status": "success",
                    "message": result['message'],
                    "token_id": token_id,
                    "timestamp": int(time.time() * 1000)
                }, 200
            else:
                return {
                    "status": "error",
                    "error": result['error'],
                    "timestamp": int(time.time() * 1000)
                }, 404

        except Exception as e:
            self.logger.error(f"❌ Error in revoke_token: {str(e)}")
            return {
                "status": "error",
                "error": f"Failed to revoke token: {str(e)}",
                "timestamp": int(time.time() * 1000)
            }, 500

    def test_service(self) -> Tuple[Dict[str, Any], int]:
        """
        Handle GET /test requests

        Returns:
            Tuple[Dict, int]: Response data and HTTP status code
        """
        try:
            return {
                "status": "success",
                "service": "MCP Service",
                "version": "1.0.0",
                "message": "MCP service is running",
                "timestamp": int(time.time() * 1000)
            }, 200

        except Exception as e:
            self.logger.error(f"❌ Error in test_service: {str(e)}")
            return {
                "status": "error",
                "error": f"Service test failed: {str(e)}",
                "timestamp": int(time.time() * 1000)
            }, 500

    # GitHub-specific methods

    def github_repositories(self) -> Tuple[Dict[str, Any], int]:
        """
        Handle GET /github/repositories requests

        Returns:
            Tuple[Dict, int]: Response data and HTTP status code
        """
        try:
            from flask import request
            from services.github_mcp_service import GitHubMCPService

            token_id = request.args.get('token_id')
            if not token_id:
                return {
                    "status": "error",
                    "error": "token_id parameter is required",
                    "timestamp": int(time.time() * 1000)
                }, 400

            github_service = GitHubMCPService()
            arguments = {
                'token_id': token_id,
                'type': request.args.get('type', 'owner'),
                'sort': request.args.get('sort', 'updated'),
                'per_page': int(request.args.get('per_page', 30))
            }

            result = github_service.execute_tool('list_repositories', arguments)

            if result['status'] == 'success':
                return {
                    "status": "success",
                    "repositories": result['repositories'],
                    "timestamp": int(time.time() * 1000)
                }, 200
            else:
                return {
                    "status": "error",
                    "error": result['error'],
                    "timestamp": int(time.time() * 1000)
                }, 400

        except Exception as e:
            self.logger.error(f"❌ Error in github_repositories: {str(e)}")
            return {
                "status": "error",
                "error": f"Failed to get repositories: {str(e)}",
                "timestamp": int(time.time() * 1000)
            }, 500

    def github_repository_details(self, owner: str, repo: str) -> Tuple[Dict[str, Any], int]:
        """
        Handle GET /github/repository/<owner>/<repo> requests

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            Tuple[Dict, int]: Response data and HTTP status code
        """
        try:
            from flask import request
            from services.github_mcp_service import GitHubMCPService

            token_id = request.args.get('token_id')
            if not token_id:
                return {
                    "status": "error",
                    "error": "token_id parameter is required",
                    "timestamp": int(time.time() * 1000)
                }, 400

            github_service = GitHubMCPService()
            arguments = {
                'token_id': token_id,
                'owner': owner,
                'repo': repo
            }

            result = github_service.execute_tool('get_repository', arguments)

            if result['status'] == 'success':
                return {
                    "status": "success",
                    "repository": result['repository'],
                    "timestamp": int(time.time() * 1000)
                }, 200
            else:
                return {
                    "status": "error",
                    "error": result['error'],
                    "timestamp": int(time.time() * 1000)
                }, 400

        except Exception as e:
            self.logger.error(f"❌ Error in github_repository_details: {str(e)}")
            return {
                "status": "error",
                "error": f"Failed to get repository details: {str(e)}",
                "timestamp": int(time.time() * 1000)
            }, 500

    def github_repository_clone(self, owner: str, repo: str) -> Tuple[Dict[str, Any], int]:
        """
        Handle POST /github/repository/<owner>/<repo>/clone requests

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            Tuple[Dict, int]: Response data and HTTP status code
        """
        try:
            from flask import request
            from services.github_mcp_service import GitHubMCPService

            data = request.get_json()
            if not data:
                return {
                    "status": "error",
                    "error": "Request body is required",
                    "timestamp": int(time.time() * 1000)
                }, 400

            token_id = data.get('token_id')
            if not token_id:
                return {
                    "status": "error",
                    "error": "token_id is required",
                    "timestamp": int(time.time() * 1000)
                }, 400

            github_service = GitHubMCPService()
            arguments = {
                'token_id': token_id,
                'owner': owner,
                'repo': repo,
                'branch': data.get('branch', 'main')
            }

            result = github_service.execute_tool('clone_repository', arguments)

            if result['status'] == 'success':
                return {
                    "status": "success",
                    "repository_info": result['repository_info'],
                    "message": result['message'],
                    "timestamp": int(time.time() * 1000)
                }, 200
            else:
                return {
                    "status": "error",
                    "error": result['error'],
                    "timestamp": int(time.time() * 1000)
                }, 400

        except Exception as e:
            self.logger.error(f"❌ Error in github_repository_clone: {str(e)}")
            return {
                "status": "error",
                "error": f"Failed to clone repository: {str(e)}",
                "timestamp": int(time.time() * 1000)
            }, 500

    def get_provider_resources(self, provider_id: str) -> Tuple[Dict[str, Any], int]:
        """
        Handle GET /provider/<provider_id>/resources requests
        Get resources available from an MCP provider

        Args:
            provider_id: MCP provider ID (github, database, document_upload)

        Returns:
            Tuple of (response_dict, status_code)
        """
        try:
            from flask import request

            # Get token_id from query parameters
            token_id = request.args.get('token_id')
            if not token_id:
                return {
                    "status": "error",
                    "error": "token_id query parameter is required",
                    "timestamp": int(time.time() * 1000)
                }, 400

            self.logger.info(f"🔍 Getting resources for provider: {provider_id} with token: {token_id}")

            # Get provider-specific resources
            if provider_id == 'github':
                return self._get_github_resources(token_id)
            elif provider_id == 'database':
                return self._get_database_resources(token_id)
            elif provider_id == 'document_upload':
                return self._get_document_resources(token_id)
            else:
                return {
                    "status": "error",
                    "error": f"Unknown provider: {provider_id}",
                    "timestamp": int(time.time() * 1000)
                }, 400

        except Exception as e:
            self.logger.error(f"❌ Error getting provider resources: {str(e)}")
            return {
                "status": "error",
                "error": f"Failed to get provider resources: {str(e)}",
                "timestamp": int(time.time() * 1000)
            }, 500

    def _get_github_resources(self, token_id: str) -> Tuple[Dict[str, Any], int]:
        """Get GitHub repositories for the given token"""
        try:
            from services.github_mcp_service import GitHubMCPService

            github_service = GitHubMCPService()
            result = github_service.execute_tool('list_repositories', {'token_id': token_id})

            if result['status'] == 'success':
                # Convert repositories to resource format
                resources = []
                for repo in result.get('repositories', []):
                    resources.append({
                        'id': repo['full_name'],
                        'name': repo['name'],
                        'type': 'repository',
                        'description': repo.get('description', ''),
                        'url': repo['html_url'],
                        'clone_url': repo['clone_url'],
                        'default_branch': repo.get('default_branch', 'main'),
                        'language': repo.get('language', ''),
                        'stars': repo.get('stars', 0),
                        'private': repo.get('private', False)
                    })

                return {
                    "status": "success",
                    "resources": resources,
                    "count": len(resources),
                    "timestamp": int(time.time() * 1000)
                }, 200
            else:
                return {
                    "status": "error",
                    "error": result.get('error', 'Failed to get GitHub repositories'),
                    "timestamp": int(time.time() * 1000)
                }, 400

        except Exception as e:
            self.logger.error(f"❌ Error getting GitHub resources: {str(e)}")
            return {
                "status": "error",
                "error": f"Failed to get GitHub resources: {str(e)}",
                "timestamp": int(time.time() * 1000)
            }, 500

    def _get_database_resources(self, token_id: str) -> Tuple[Dict[str, Any], int]:
        """Get database tables/schemas for the given token"""
        try:
            # TODO: Implement database resource listing
            # This would connect to the database and list tables/schemas

            # Mock data for now
            resources = [
                {
                    'id': 'users_table',
                    'name': 'users',
                    'type': 'table',
                    'description': 'User accounts table',
                    'schema': 'public',
                    'columns': ['id', 'username', 'email', 'created_at']
                },
                {
                    'id': 'products_table',
                    'name': 'products',
                    'type': 'table',
                    'description': 'Product catalog table',
                    'schema': 'public',
                    'columns': ['id', 'name', 'price', 'category']
                }
            ]

            return {
                "status": "success",
                "resources": resources,
                "count": len(resources),
                "timestamp": int(time.time() * 1000)
            }, 200

        except Exception as e:
            self.logger.error(f"❌ Error getting database resources: {str(e)}")
            return {
                "status": "error",
                "error": f"Failed to get database resources: {str(e)}",
                "timestamp": int(time.time() * 1000)
            }, 500

    def _get_document_resources(self, token_id: str) -> Tuple[Dict[str, Any], int]:
        """Get uploaded documents for the given token"""
        try:
            # TODO: Implement document resource listing
            # This would list uploaded documents from storage

            # Mock data for now
            resources = [
                {
                    'id': 'doc_1',
                    'name': 'project_requirements.pdf',
                    'type': 'document',
                    'description': 'Project requirements document',
                    'size': '2.5 MB',
                    'uploaded_at': '2024-01-15T10:30:00Z'
                },
                {
                    'id': 'doc_2',
                    'name': 'api_documentation.md',
                    'type': 'document',
                    'description': 'API documentation in Markdown',
                    'size': '1.2 MB',
                    'uploaded_at': '2024-01-14T15:45:00Z'
                }
            ]

            return {
                "status": "success",
                "resources": resources,
                "count": len(resources),
                "timestamp": int(time.time() * 1000)
            }, 200

        except Exception as e:
            self.logger.error(f"❌ Error getting document resources: {str(e)}")
            return {
                "status": "error",
                "error": f"Failed to get document resources: {str(e)}",
                "timestamp": int(time.time() * 1000)
            }, 500
