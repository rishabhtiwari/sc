"""
Protocol-specific handlers for fetching files from remote hosts
"""
import os
import time
import paramiko
import ftplib
import requests
from datetime import datetime
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse

from config.settings import Config
from utils.logger import setup_logger

class ProtocolHandlers:
    """Handlers for different protocols to fetch files from remote hosts"""
    
    def __init__(self):
        self.logger = setup_logger('protocol-handlers')
        self.config = Config()
    
    def fetch_files_ssh_sftp(self, connection: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch files using SSH/SFTP"""
        host = connection.get('host')
        port = connection.get('port', 22)
        username = connection.get('username')
        base_path = connection.get('base_path', '/')
        
        files = []
        ssh_client = None
        sftp_client = None
        
        try:
            # Create SSH client
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect (credentials would need to be decrypted from MCP service)
            # For now, we'll make a request to MCP service to get file listing
            files = self._request_file_listing_from_mcp(connection['id'], 'sftp')
            
        except Exception as e:
            self.logger.error(f"SSH/SFTP connection failed for {host}: {str(e)}")
            
        finally:
            if sftp_client:
                sftp_client.close()
            if ssh_client:
                ssh_client.close()
        
        return files
    
    def fetch_files_ftp(self, connection: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch files using FTP"""
        host = connection.get('host')
        port = connection.get('port', 21)
        username = connection.get('username', 'anonymous')
        base_path = connection.get('base_path', '/')
        
        files = []
        ftp_client = None
        
        try:
            # For security, we'll delegate to MCP service for actual file operations
            files = self._request_file_listing_from_mcp(connection['id'], 'ftp')
            
        except Exception as e:
            self.logger.error(f"FTP connection failed for {host}: {str(e)}")
            
        finally:
            if ftp_client:
                try:
                    ftp_client.quit()
                except:
                    pass
        
        return files
    
    def fetch_files_http(self, connection: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch files using HTTP/HTTPS (for web servers with directory listing)"""
        protocol = connection.get('protocol', 'http')
        host = connection.get('host')
        port = connection.get('port', 80 if protocol == 'http' else 443)
        base_path = connection.get('base_path', '/')
        
        files = []
        
        try:
            # For HTTP, we'll also delegate to MCP service for consistency
            files = self._request_file_listing_from_mcp(connection['id'], protocol)
            
        except Exception as e:
            self.logger.error(f"HTTP connection failed for {host}: {str(e)}")
        
        return files
    
    def _request_file_listing_from_mcp(self, connection_id: str, protocol: str) -> List[Dict[str, Any]]:
        """Request file listing from MCP service for a connection"""
        try:
            # Use MCP service to get file listing (this would need to be implemented in MCP service)
            response = requests.get(
                f"{self.config.MCP_SERVICE_URL}/mcp/remote-host/connections/{connection_id}/files",
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    return data.get('files', [])
            
            # If MCP service doesn't have file listing endpoint, return empty for now
            self.logger.warning(f"File listing not available for connection {connection_id}")
            return []
            
        except Exception as e:
            self.logger.error(f"Error requesting file listing from MCP service: {str(e)}")
            return []
    
    def fetch_file_content(self, connection: Dict[str, Any], file_path: str) -> Optional[str]:
        """Fetch content of a specific file"""
        try:
            # Request file content from MCP service
            response = requests.post(
                f"{self.config.MCP_SERVICE_URL}/mcp/remote-host/connections/{connection['id']}/files/content",
                json={'file_path': file_path},
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    return data.get('content')
            
            self.logger.error(f"Failed to fetch file content: {file_path}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error fetching file content for {file_path}: {str(e)}")
            return None
    
    def _parse_directory_listing(self, html_content: str, base_url: str) -> List[Dict[str, Any]]:
        """Parse HTML directory listing (basic implementation)"""
        files = []
        
        # This is a simplified parser - in production, you'd want a more robust solution
        # For now, we'll return empty list and rely on MCP service implementation
        
        return files
    
    def _get_file_info_from_stat(self, file_path: str, stat_info) -> Dict[str, Any]:
        """Convert file stat info to standardized format"""
        return {
            'path': file_path,
            'name': os.path.basename(file_path),
            'size': getattr(stat_info, 'st_size', 0),
            'modified_time': datetime.fromtimestamp(getattr(stat_info, 'st_mtime', 0)).isoformat(),
            'is_directory': hasattr(stat_info, 'st_mode') and os.path.stat.S_ISDIR(stat_info.st_mode),
            'permissions': oct(getattr(stat_info, 'st_mode', 0))[-3:] if hasattr(stat_info, 'st_mode') else '644'
        }
