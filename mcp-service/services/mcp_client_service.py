"""
MCP Client Service - Handles MCP client connections and operations
"""

import json
import uuid
import time
import logging
import asyncio
import subprocess
import threading
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from config.settings import MCPConfig


@dataclass
class MCPConnection:
    """Represents an MCP connection"""
    connection_id: str
    name: str
    command: List[str]
    args: List[str]
    env: Dict[str, str]
    protocol: str
    status: str
    created_at: int
    process: Optional[subprocess.Popen] = None
    server_info: Optional[Dict] = None
    tools: Optional[List[Dict]] = None
    resources: Optional[List[Dict]] = None
    last_activity: Optional[int] = None


class MCPClientService:
    """Service for managing MCP client connections"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.connections: Dict[str, MCPConnection] = {}
        self.config = MCPConfig()
        
    def connect(self, name: str, command: List[str], args: List[str] = None, 
                env: Dict[str, str] = None, protocol: str = 'stdio') -> Dict[str, Any]:
        """
        Connect to an MCP server
        
        Args:
            name: Server name
            command: Command to start the server
            args: Additional arguments
            env: Environment variables
            protocol: Communication protocol
            
        Returns:
            Dict with connection result
        """
        try:
            # Check connection limits
            if len(self.connections) >= self.config.MAX_CONNECTIONS:
                return {
                    "status": "error",
                    "error": f"Maximum connections ({self.config.MAX_CONNECTIONS}) reached"
                }
            
            # Validate protocol
            if protocol not in self.config.ALLOWED_MCP_PROTOCOLS:
                return {
                    "status": "error",
                    "error": f"Protocol '{protocol}' not allowed. Allowed: {self.config.ALLOWED_MCP_PROTOCOLS}"
                }
            
            connection_id = str(uuid.uuid4())
            args = args or []
            env = env or {}
            
            self.logger.info(f"🔌 Starting MCP server: {name} with command: {command}")
            
            # Create connection object
            connection = MCPConnection(
                connection_id=connection_id,
                name=name,
                command=command,
                args=args,
                env=env,
                protocol=protocol,
                status='connecting',
                created_at=int(time.time() * 1000)
            )
            
            # Start the MCP server process
            if protocol == 'stdio':
                result = self._start_stdio_connection(connection)
            elif protocol == 'sse':
                result = self._start_sse_connection(connection)
            elif protocol == 'websocket':
                result = self._start_websocket_connection(connection)
            else:
                return {
                    "status": "error",
                    "error": f"Unsupported protocol: {protocol}"
                }
            
            if result['status'] == 'success':
                connection.status = 'connected'
                connection.server_info = result.get('server_info', {})
                connection.tools = result.get('tools', [])
                connection.resources = result.get('resources', [])
                connection.last_activity = int(time.time() * 1000)
                
                self.connections[connection_id] = connection
                
                self.logger.info(f"✅ Successfully connected to MCP server: {name}")
                return {
                    "status": "success",
                    "connection_id": connection_id,
                    "server_info": connection.server_info,
                    "tools": connection.tools,
                    "resources": connection.resources
                }
            else:
                connection.status = 'error'
                return result
                
        except Exception as e:
            self.logger.error(f"❌ Failed to connect to MCP server: {str(e)}")
            return {
                "status": "error",
                "error": f"Connection failed: {str(e)}"
            }
    
    def _start_stdio_connection(self, connection: MCPConnection) -> Dict[str, Any]:
        """
        Start an MCP server with stdio protocol
        
        Args:
            connection: The connection object
            
        Returns:
            Dict with connection result
        """
        try:
            # Prepare environment
            full_env = {**connection.env}
            full_env.update(os.environ)
            
            # Start the process
            full_command = connection.command + connection.args
            process = subprocess.Popen(
                full_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=full_env,
                text=True,
                bufsize=0
            )
            
            connection.process = process
            
            # Initialize MCP handshake
            handshake_result = self._perform_mcp_handshake(connection)
            
            if handshake_result['status'] == 'success':
                return {
                    "status": "success",
                    "server_info": handshake_result.get('server_info', {}),
                    "tools": handshake_result.get('tools', []),
                    "resources": handshake_result.get('resources', [])
                }
            else:
                # Clean up process if handshake failed
                if process.poll() is None:
                    process.terminate()
                return handshake_result
                
        except Exception as e:
            self.logger.error(f"❌ Failed to start stdio connection: {str(e)}")
            return {
                "status": "error",
                "error": f"Failed to start stdio connection: {str(e)}"
            }

    def _start_sse_connection(self, connection: MCPConnection) -> Dict[str, Any]:
        """
        Start an MCP server with SSE protocol

        Args:
            connection: The connection object

        Returns:
            Dict with connection result
        """
        # SSE implementation would go here
        return {
            "status": "error",
            "error": "SSE protocol not yet implemented"
        }

    def _start_websocket_connection(self, connection: MCPConnection) -> Dict[str, Any]:
        """
        Start an MCP server with WebSocket protocol

        Args:
            connection: The connection object

        Returns:
            Dict with connection result
        """
        # WebSocket implementation would go here
        return {
            "status": "error",
            "error": "WebSocket protocol not yet implemented"
        }

    def _perform_mcp_handshake(self, connection: MCPConnection) -> Dict[str, Any]:
        """
        Perform MCP handshake with the server

        Args:
            connection: The connection object

        Returns:
            Dict with handshake result
        """
        try:
            if not connection.process:
                return {
                    "status": "error",
                    "error": "No process available for handshake"
                }

            # Send initialize request
            initialize_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {},
                        "resources": {}
                    },
                    "clientInfo": {
                        "name": "iChat MCP Service",
                        "version": "1.0.0"
                    }
                }
            }

            # Send the request
            request_json = json.dumps(initialize_request) + '\n'
            connection.process.stdin.write(request_json)
            connection.process.stdin.flush()

            # Read response with timeout
            import select
            import sys

            # Wait for response (with timeout)
            ready, _, _ = select.select([connection.process.stdout], [], [], self.config.CONNECTION_TIMEOUT)

            if ready:
                response_line = connection.process.stdout.readline()
                if response_line:
                    try:
                        response = json.loads(response_line.strip())

                        if response.get('id') == 1 and 'result' in response:
                            server_info = response['result']

                            # Get tools and resources
                            tools = self._get_server_tools(connection)
                            resources = self._get_server_resources(connection)

                            return {
                                "status": "success",
                                "server_info": server_info,
                                "tools": tools,
                                "resources": resources
                            }
                        else:
                            return {
                                "status": "error",
                                "error": f"Invalid handshake response: {response}"
                            }
                    except json.JSONDecodeError as e:
                        return {
                            "status": "error",
                            "error": f"Invalid JSON response: {str(e)}"
                        }
                else:
                    return {
                        "status": "error",
                        "error": "No response received from server"
                    }
            else:
                return {
                    "status": "error",
                    "error": "Handshake timeout"
                }

        except Exception as e:
            self.logger.error(f"❌ MCP handshake failed: {str(e)}")
            return {
                "status": "error",
                "error": f"Handshake failed: {str(e)}"
            }

    def _get_server_tools(self, connection: MCPConnection) -> List[Dict]:
        """Get available tools from the server"""
        try:
            if not connection.process:
                return []

            # Send tools/list request
            tools_request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            }

            request_json = json.dumps(tools_request) + '\n'
            connection.process.stdin.write(request_json)
            connection.process.stdin.flush()

            # Read response
            import select
            ready, _, _ = select.select([connection.process.stdout], [], [], 5)

            if ready:
                response_line = connection.process.stdout.readline()
                if response_line:
                    response = json.loads(response_line.strip())
                    if response.get('id') == 2 and 'result' in response:
                        return response['result'].get('tools', [])

            return []

        except Exception as e:
            self.logger.error(f"❌ Failed to get server tools: {str(e)}")
            return []

    def _get_server_resources(self, connection: MCPConnection) -> List[Dict]:
        """Get available resources from the server"""
        try:
            if not connection.process:
                return []

            # Send resources/list request
            resources_request = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "resources/list",
                "params": {}
            }

            request_json = json.dumps(resources_request) + '\n'
            connection.process.stdin.write(request_json)
            connection.process.stdin.flush()

            # Read response
            import select
            ready, _, _ = select.select([connection.process.stdout], [], [], 5)

            if ready:
                response_line = connection.process.stdout.readline()
                if response_line:
                    response = json.loads(response_line.strip())
                    if response.get('id') == 3 and 'result' in response:
                        return response['result'].get('resources', [])

            return []

        except Exception as e:
            self.logger.error(f"❌ Failed to get server resources: {str(e)}")
            return []

    def disconnect(self, connection_id: str) -> Dict[str, Any]:
        """
        Disconnect from an MCP server

        Args:
            connection_id: The connection ID to disconnect

        Returns:
            Dict with disconnection result
        """
        try:
            if connection_id not in self.connections:
                return {
                    "status": "error",
                    "error": "Connection not found"
                }

            connection = self.connections[connection_id]

            # Terminate the process if it exists
            if connection.process and connection.process.poll() is None:
                connection.process.terminate()
                # Wait a bit for graceful termination
                try:
                    connection.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    connection.process.kill()

            # Remove from connections
            del self.connections[connection_id]

            self.logger.info(f"✅ Successfully disconnected from MCP server: {connection.name}")
            return {
                "status": "success",
                "message": f"Successfully disconnected from {connection.name}"
            }

        except Exception as e:
            self.logger.error(f"❌ Failed to disconnect from MCP server: {str(e)}")
            return {
                "status": "error",
                "error": f"Disconnection failed: {str(e)}"
            }

    def list_connections(self) -> List[Dict[str, Any]]:
        """
        List all active connections

        Returns:
            List of connection information
        """
        connections_list = []

        for connection_id, connection in self.connections.items():
            # Check if process is still alive
            if connection.process:
                is_alive = connection.process.poll() is None
                if not is_alive and connection.status == 'connected':
                    connection.status = 'disconnected'
            else:
                is_alive = False

            connections_list.append({
                "connection_id": connection_id,
                "name": connection.name,
                "protocol": connection.protocol,
                "status": connection.status,
                "created_at": connection.created_at,
                "last_activity": connection.last_activity,
                "is_alive": is_alive,
                "tools_count": len(connection.tools or []),
                "resources_count": len(connection.resources or []),
                "server_info": connection.server_info
            })

        return connections_list

    def get_connection_status(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a specific connection

        Args:
            connection_id: The connection ID to check

        Returns:
            Connection status or None if not found
        """
        if connection_id not in self.connections:
            return None

        connection = self.connections[connection_id]

        # Check if process is still alive
        is_alive = False
        if connection.process:
            is_alive = connection.process.poll() is None
            if not is_alive and connection.status == 'connected':
                connection.status = 'disconnected'

        return {
            "connection_id": connection_id,
            "name": connection.name,
            "command": connection.command,
            "args": connection.args,
            "protocol": connection.protocol,
            "status": connection.status,
            "created_at": connection.created_at,
            "last_activity": connection.last_activity,
            "is_alive": is_alive,
            "server_info": connection.server_info,
            "tools": connection.tools,
            "resources": connection.resources
        }

    def execute_tool(self, connection_id: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool on an MCP server

        Args:
            connection_id: The connection ID
            tool_name: Name of the tool to execute
            arguments: Tool arguments

        Returns:
            Dict with execution result
        """
        try:
            if connection_id not in self.connections:
                return {
                    "status": "error",
                    "error": "Connection not found"
                }

            connection = self.connections[connection_id]

            if not connection.process or connection.process.poll() is not None:
                return {
                    "status": "error",
                    "error": "Connection is not active"
                }

            # Send tool execution request
            tool_request = {
                "jsonrpc": "2.0",
                "id": int(time.time() * 1000),  # Use timestamp as ID
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }

            request_json = json.dumps(tool_request) + '\n'
            connection.process.stdin.write(request_json)
            connection.process.stdin.flush()

            # Read response with timeout
            import select
            ready, _, _ = select.select([connection.process.stdout], [], [], self.config.EXECUTION_TIMEOUT)

            if ready:
                response_line = connection.process.stdout.readline()
                if response_line:
                    response = json.loads(response_line.strip())

                    if 'result' in response:
                        connection.last_activity = int(time.time() * 1000)
                        return {
                            "status": "success",
                            "result": response['result']
                        }
                    elif 'error' in response:
                        return {
                            "status": "error",
                            "error": response['error']
                        }
                    else:
                        return {
                            "status": "error",
                            "error": f"Invalid response: {response}"
                        }
                else:
                    return {
                        "status": "error",
                        "error": "No response received from server"
                    }
            else:
                return {
                    "status": "error",
                    "error": "Tool execution timeout"
                }

        except Exception as e:
            self.logger.error(f"❌ Tool execution failed: {str(e)}")
            return {
                "status": "error",
                "error": f"Tool execution failed: {str(e)}"
            }

    def list_tools(self, connection_id: str) -> Optional[List[Dict]]:
        """
        List tools for a specific connection

        Args:
            connection_id: The connection ID

        Returns:
            List of tools or None if connection not found
        """
        if connection_id not in self.connections:
            return None

        return self.connections[connection_id].tools or []

    def list_resources(self, connection_id: str) -> Optional[List[Dict]]:
        """
        List resources for a specific connection

        Args:
            connection_id: The connection ID

        Returns:
            List of resources or None if connection not found
        """
        if connection_id not in self.connections:
            return None

        return self.connections[connection_id].resources or []
