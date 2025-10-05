"""
Remote Host MCP Service
Handles authentication and credential management for remote host connections
"""

import sqlite3
import json
import uuid
import hashlib
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from cryptography.fernet import Fernet
import paramiko
import requests
from ftplib import FTP
import subprocess
import os
import stat
import io
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

class RemoteHostMCPService:
    def __init__(self, db_path: str = "data/remote_host_mcp.db"):
        self.db_path = db_path
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)
        self._init_database()
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for credential storage"""
        try:
            with open("data/remote_host_encryption.key", "rb") as key_file:
                return key_file.read()
        except FileNotFoundError:
            key = Fernet.generate_key()
            with open("data/remote_host_encryption.key", "wb") as key_file:
                key_file.write(key)
            return key
    
    def _init_database(self):
        """Initialize the remote host MCP database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Remote host connections table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS remote_host_connections (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    protocol TEXT NOT NULL,
                    host TEXT NOT NULL,
                    port INTEGER,
                    username TEXT,
                    encrypted_password TEXT,
                    encrypted_private_key TEXT,
                    base_path TEXT,
                    connection_params TEXT,
                    status TEXT DEFAULT 'inactive',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_tested TIMESTAMP,
                    test_result TEXT
                )
            ''')
            
            # Remote host resources table (files/folders)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS remote_host_resources (
                    id TEXT PRIMARY KEY,
                    connection_id TEXT NOT NULL,
                    resource_type TEXT NOT NULL,
                    path TEXT NOT NULL,
                    name TEXT NOT NULL,
                    size INTEGER,
                    modified_time TIMESTAMP,
                    file_type TEXT,
                    metadata TEXT,
                    sync_status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (connection_id) REFERENCES remote_host_connections (id)
                )
            ''')
            
            # Sync sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sync_sessions (
                    id TEXT PRIMARY KEY,
                    connection_id TEXT NOT NULL,
                    session_type TEXT NOT NULL,
                    status TEXT DEFAULT 'active',
                    credentials_hash TEXT,
                    expires_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (connection_id) REFERENCES remote_host_connections (id)
                )
            ''')
            
            conn.commit()
    
    def add_remote_host(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new remote host connection"""
        try:
            connection_id = str(uuid.uuid4())
            
            # Encrypt sensitive data
            encrypted_password = None
            encrypted_private_key = None
            
            if config.get('password'):
                encrypted_password = self.cipher_suite.encrypt(
                    config['password'].encode()
                ).decode()
            
            if config.get('private_key'):
                encrypted_private_key = self.cipher_suite.encrypt(
                    config['private_key'].encode()
                ).decode()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO remote_host_connections 
                    (id, name, protocol, host, port, username, encrypted_password, 
                     encrypted_private_key, base_path, connection_params)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    connection_id,
                    config['name'],
                    config['protocol'],
                    config['host'],
                    config.get('port', self._get_default_port(config['protocol'])),
                    config.get('username'),
                    encrypted_password,
                    encrypted_private_key,
                    config.get('base_path', '/'),
                    json.dumps(config.get('connection_params', {}))
                ))
                conn.commit()
            
            logger.info(f"Added remote host connection: {config['name']}")

            # Test the connection immediately after creation and update status
            try:
                test_result = self.test_connection(connection_id)
                if test_result['status'] == 'success':
                    # Update status to active if test is successful
                    with sqlite3.connect(self.db_path) as conn:
                        cursor = conn.cursor()
                        cursor.execute('''
                            UPDATE remote_host_connections
                            SET status = 'active', last_tested = CURRENT_TIMESTAMP, test_result = ?
                            WHERE id = ?
                        ''', (json.dumps(test_result), connection_id))
                        conn.commit()
                    logger.info(f"Connection {config['name']} tested successfully and set to active")
                else:
                    logger.warning(f"Connection {config['name']} test failed, keeping inactive status")
            except Exception as test_error:
                logger.warning(f"Failed to test connection after creation: {str(test_error)}")

            return {
                "status": "success",
                "connection_id": connection_id,
                "message": f"Remote host '{config['name']}' added successfully"
            }
            
        except Exception as e:
            logger.error(f"Error adding remote host: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to add remote host: {str(e)}"
            }
    
    def test_connection(self, connection_id: str) -> Dict[str, Any]:
        """Test connection to remote host"""
        try:
            connection = self.get_connection(connection_id)
            if not connection:
                return {"status": "error", "message": "Connection not found"}
            
            # Decrypt credentials
            credentials = self._decrypt_credentials(connection)
            
            # Test connection based on protocol
            result = self._test_protocol_connection(connection, credentials)
            
            # Update test result in database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE remote_host_connections 
                    SET last_tested = CURRENT_TIMESTAMP, test_result = ?, status = ?
                    WHERE id = ?
                ''', (json.dumps(result), 
                      'active' if result['status'] == 'success' else 'error',
                      connection_id))
                conn.commit()
            
            return result
            
        except Exception as e:
            logger.error(f"Error testing connection {connection_id}: {str(e)}")
            return {
                "status": "error",
                "message": f"Connection test failed: {str(e)}"
            }

    def test_connection_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Test connection configuration without saving to database"""
        try:
            # Validate required fields
            required_fields = ['protocol', 'host', 'port']
            for field in required_fields:
                if field not in config or not config[field]:
                    return {
                        "status": "error",
                        "message": f"Missing required field: {field}"
                    }

            # Create a temporary connection object for testing
            temp_connection = {
                'protocol': config['protocol'],
                'host': config['host'],
                'port': int(config['port']),
                'base_path': config.get('base_path', '/'),
                'username': config.get('username'),
            }

            # Create temporary credentials
            temp_credentials = {
                'password': config.get('password', '')
            }

            # Test connection based on protocol
            result = self._test_protocol_connection(temp_connection, temp_credentials)

            return result

        except Exception as e:
            logger.error(f"Error testing connection config: {str(e)}")
            return {
                "status": "error",
                "message": f"Configuration test failed: {str(e)}"
            }

    def get_connection(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Get connection details by ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM remote_host_connections WHERE id = ?
            ''', (connection_id,))
            
            row = cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, row))
            return None
    
    def get_all_connections(self) -> List[Dict[str, Any]]:
        """Get all remote host connections"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, name, protocol, host, port, username, base_path, 
                       status, created_at, last_tested, test_result
                FROM remote_host_connections
                ORDER BY created_at DESC
            ''')
            
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def create_sync_session(self, connection_id: str) -> Dict[str, Any]:
        """Create a sync session with decrypted credentials for remote-host-syncer"""
        try:
            connection = self.get_connection(connection_id)
            if not connection:
                return {"status": "error", "message": "Connection not found"}
            
            # Test connection first
            test_result = self.test_connection(connection_id)
            if test_result['status'] != 'success':
                return {
                    "status": "error", 
                    "message": f"Connection test failed: {test_result.get('message', 'Unknown error')}"
                }
            
            # Create sync session
            session_id = str(uuid.uuid4())
            credentials = self._decrypt_credentials(connection)
            credentials_hash = hashlib.sha256(
                json.dumps(credentials, sort_keys=True).encode()
            ).hexdigest()
            
            # Session expires in 24 hours
            expires_at = datetime.now().timestamp() + (24 * 60 * 60)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO sync_sessions 
                    (id, connection_id, session_type, credentials_hash, expires_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (session_id, connection_id, 'document_sync', credentials_hash, expires_at))
                conn.commit()
            
            # Return session with credentials for remote-host-syncer
            return {
                "status": "success",
                "session_id": session_id,
                "connection_id": connection_id,
                "credentials": {
                    "protocol": connection['protocol'],
                    "host": connection['host'],
                    "port": connection['port'],
                    "username": connection['username'],
                    "password": credentials.get('password'),
                    "private_key": credentials.get('private_key'),
                    "base_path": connection['base_path'],
                    "connection_params": json.loads(connection.get('connection_params', '{}'))
                },
                "expires_at": expires_at
            }
            
        except Exception as e:
            logger.error(f"Error creating sync session: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to create sync session: {str(e)}"
            }
    
    def _decrypt_credentials(self, connection: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt stored credentials"""
        credentials = {}
        
        if connection.get('encrypted_password'):
            credentials['password'] = self.cipher_suite.decrypt(
                connection['encrypted_password'].encode()
            ).decode()
        
        if connection.get('encrypted_private_key'):
            credentials['private_key'] = self.cipher_suite.decrypt(
                connection['encrypted_private_key'].encode()
            ).decode()
        
        return credentials
    
    def _test_protocol_connection(self, connection: Dict[str, Any], credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Test connection based on protocol"""
        protocol = connection['protocol'].lower()
        
        try:
            if protocol == 'ssh':
                return self._test_ssh_connection(connection, credentials)
            elif protocol == 'sftp':
                return self._test_sftp_connection(connection, credentials)
            elif protocol == 'ftp':
                return self._test_ftp_connection(connection, credentials)
            elif protocol in ['http', 'https']:
                return self._test_http_connection(connection, credentials)
            elif protocol == 'rsync':
                return self._test_rsync_connection(connection, credentials)
            else:
                return {
                    "status": "error",
                    "message": f"Unsupported protocol: {protocol}"
                }
        except Exception as e:
            return {
                "status": "error",
                "message": f"{protocol.upper()} connection failed: {str(e)}"
            }
    
    def _test_ssh_connection(self, connection: Dict[str, Any], credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Test SSH connection"""
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            if credentials.get('private_key'):
                # Use private key authentication
                from io import StringIO
                private_key = paramiko.RSAKey.from_private_key(StringIO(credentials['private_key']))
                client.connect(
                    hostname=connection['host'],
                    port=connection['port'],
                    username=connection['username'],
                    pkey=private_key,
                    timeout=10
                )
            else:
                # Use password authentication
                client.connect(
                    hostname=connection['host'],
                    port=connection['port'],
                    username=connection['username'],
                    password=credentials.get('password'),
                    timeout=10
                )
            
            # Test basic command
            stdin, stdout, stderr = client.exec_command('pwd')
            result = stdout.read().decode().strip()
            
            client.close()
            return {
                "status": "success",
                "message": "SSH connection successful",
                "details": {"working_directory": result}
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"SSH connection failed: {str(e)}"
            }
        finally:
            client.close()
    
    def _test_sftp_connection(self, connection: Dict[str, Any], credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Test SFTP connection"""
        transport = paramiko.Transport((connection['host'], connection['port']))
        
        try:
            if credentials.get('private_key'):
                from io import StringIO
                private_key = paramiko.RSAKey.from_private_key(StringIO(credentials['private_key']))
                transport.connect(username=connection['username'], pkey=private_key)
            else:
                transport.connect(username=connection['username'], password=credentials.get('password'))
            
            sftp = paramiko.SFTPClient.from_transport(transport)
            
            # Test listing directory
            files = sftp.listdir(connection.get('base_path', '/'))
            
            sftp.close()
            transport.close()
            
            return {
                "status": "success",
                "message": "SFTP connection successful",
                "details": {"file_count": len(files)}
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"SFTP connection failed: {str(e)}"
            }
        finally:
            transport.close()
    
    def _test_ftp_connection(self, connection: Dict[str, Any], credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Test FTP connection"""
        try:
            ftp = FTP()
            ftp.connect(connection['host'], connection['port'])
            ftp.login(connection['username'], credentials.get('password', ''))
            
            # Test listing directory
            files = ftp.nlst(connection.get('base_path', '/'))
            
            ftp.quit()
            
            return {
                "status": "success",
                "message": "FTP connection successful",
                "details": {"file_count": len(files)}
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"FTP connection failed: {str(e)}"
            }
    
    def _test_http_connection(self, connection: Dict[str, Any], credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Test HTTP/HTTPS connection"""
        try:
            url = f"{connection['protocol']}://{connection['host']}"
            if connection['port'] not in [80, 443]:
                url += f":{connection['port']}"
            url += connection.get('base_path', '/')
            
            auth = None
            if connection.get('username') and credentials.get('password'):
                auth = (connection['username'], credentials['password'])
            
            response = requests.get(url, auth=auth, timeout=10)
            
            return {
                "status": "success",
                "message": "HTTP connection successful",
                "details": {"status_code": response.status_code}
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"HTTP connection failed: {str(e)}"
            }
    
    def _test_rsync_connection(self, connection: Dict[str, Any], credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Test RSYNC connection"""
        try:
            # Test rsync connection with dry-run
            host_path = f"{connection['username']}@{connection['host']}:{connection.get('base_path', '/')}"
            
            cmd = [
                'rsync', '--dry-run', '--list-only',
                '-e', f'ssh -p {connection["port"]}',
                host_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return {
                    "status": "success",
                    "message": "RSYNC connection successful",
                    "details": {"output_lines": len(result.stdout.split('\n'))}
                }
            else:
                return {
                    "status": "error",
                    "message": f"RSYNC failed: {result.stderr}"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"RSYNC connection failed: {str(e)}"
            }

    def _list_files_by_protocol(self, connection: Dict[str, Any], credentials: Dict[str, Any], path: str) -> List[Dict[str, Any]]:
        """List files based on protocol"""
        protocol = connection['protocol'].lower()

        try:
            if protocol == 'ssh':
                return self._list_files_ssh(connection, credentials, path)
            elif protocol == 'sftp':
                return self._list_files_sftp(connection, credentials, path)
            elif protocol == 'ftp':
                return self._list_files_ftp(connection, credentials, path)
            elif protocol in ['http', 'https']:
                return self._list_files_http(connection, credentials, path)
            else:
                logger.warning(f"File listing not supported for protocol: {protocol}")
                return []
        except Exception as e:
            logger.error(f"Error listing files via {protocol}: {str(e)}")
            return []

    def _get_file_content_by_protocol(self, connection: Dict[str, Any], credentials: Dict[str, Any], file_path: str) -> str:
        """Get file content based on protocol"""
        protocol = connection['protocol'].lower()

        try:
            if protocol == 'ssh':
                return self._get_file_content_ssh(connection, credentials, file_path)
            elif protocol == 'sftp':
                return self._get_file_content_sftp(connection, credentials, file_path)
            elif protocol == 'ftp':
                return self._get_file_content_ftp(connection, credentials, file_path)
            elif protocol in ['http', 'https']:
                return self._get_file_content_http(connection, credentials, file_path)
            else:
                logger.warning(f"File content retrieval not supported for protocol: {protocol}")
                return ""
        except Exception as e:
            logger.error(f"Error getting file content via {protocol}: {str(e)}")
            return ""
    
    def delete_connection(self, connection_id: str) -> Dict[str, Any]:
        """Delete a remote host connection"""
        logger.info(f"🗑️ DELETE METHOD CALLED FOR CONNECTION: {connection_id}")
        print(f"DELETE METHOD CALLED FOR CONNECTION: {connection_id}")
        import sys
        sys.stdout.flush()
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Check if connection exists
                cursor.execute('SELECT id FROM remote_host_connections WHERE id = ?', (connection_id,))
                if not cursor.fetchone():
                    print(f"CONNECTION NOT FOUND: {connection_id}")
                    return {
                        "status": "error",
                        "message": "Connection not found"
                    }

                print(f"DELETING CONNECTION: {connection_id}")
                logger.info(f"Deleting connection {connection_id}")

                # Delete related sync sessions first
                cursor.execute('DELETE FROM sync_sessions WHERE connection_id = ?', (connection_id,))
                sessions_deleted = cursor.rowcount
                print(f"DELETED {sessions_deleted} SYNC SESSIONS")
                logger.info(f"Deleted {sessions_deleted} sync sessions")

                # Delete related resources (files/folders)
                cursor.execute('DELETE FROM remote_host_resources WHERE connection_id = ?', (connection_id,))
                resources_deleted = cursor.rowcount
                print(f"DELETED {resources_deleted} RESOURCES")
                logger.info(f"Deleted {resources_deleted} resources")

                # Delete the connection
                cursor.execute('DELETE FROM remote_host_connections WHERE id = ?', (connection_id,))
                connections_deleted = cursor.rowcount
                print(f"DELETED {connections_deleted} CONNECTIONS")
                logger.info(f"Deleted {connections_deleted} connections")

                conn.commit()
                print(f"TRANSACTION COMMITTED FOR CONNECTION: {connection_id}")
                logger.info(f"Transaction committed for connection {connection_id}")

                return {
                    "status": "success",
                    "message": "Connection deleted successfully"
                }

        except Exception as e:
            print(f"ERROR DELETING CONNECTION {connection_id}: {str(e)}")
            logger.error(f"Error deleting connection {connection_id}: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to delete connection: {str(e)}"
            }

    def list_files(self, connection_id: str, path: str = None) -> Dict[str, Any]:
        """List files from remote host connection"""
        try:
            connection = self.get_connection(connection_id)
            if not connection:
                return {"status": "error", "message": "Connection not found"}

            # Decrypt credentials
            credentials = self._decrypt_credentials(connection)

            # Use base_path if no specific path provided
            if path is None:
                path = connection.get('base_path', '/')

            # List files based on protocol
            files = self._list_files_by_protocol(connection, credentials, path)

            return {
                "status": "success",
                "files": files,
                "connection_id": connection_id,
                "path": path
            }

        except Exception as e:
            logger.error(f"Failed to list files for connection {connection_id}: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to list files: {str(e)}"
            }

    def get_file_content(self, connection_id: str, file_path: str) -> Dict[str, Any]:
        """Get file content from remote host connection"""
        try:
            connection = self.get_connection(connection_id)
            if not connection:
                return {"status": "error", "message": "Connection not found"}

            # Decrypt credentials
            credentials = self._decrypt_credentials(connection)

            # Get file content based on protocol
            content = self._get_file_content_by_protocol(connection, credentials, file_path)

            return {
                "status": "success",
                "content": content,
                "connection_id": connection_id,
                "file_path": file_path
            }

        except Exception as e:
            logger.error(f"Failed to get file content for {file_path} from connection {connection_id}: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to get file content: {str(e)}"
            }

    def _get_default_port(self, protocol: str) -> int:
        """Get default port for protocol"""
        defaults = {
            'ssh': 22,
            'sftp': 22,
            'ftp': 21,
            'http': 80,
            'https': 443,
            'rsync': 873
        }
        return defaults.get(protocol.lower(), 22)

    def _list_files_ssh(self, connection: Dict[str, Any], credentials: Dict[str, Any], path: str) -> List[Dict[str, Any]]:
        """List files via SSH"""
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            # Connect
            if credentials.get('private_key'):
                private_key = paramiko.RSAKey.from_private_key(io.StringIO(credentials['private_key']))
                client.connect(
                    connection['host'],
                    port=connection['port'],
                    username=connection['username'],
                    pkey=private_key,
                    timeout=10
                )
            else:
                client.connect(
                    connection['host'],
                    port=connection['port'],
                    username=connection['username'],
                    password=credentials.get('password', ''),
                    timeout=10
                )

            # List files recursively using find command (no limit)
            stdin, stdout, stderr = client.exec_command(f'find "{path}" -type f -exec ls -la {{}} \\; 2>/dev/null')
            output = stdout.read().decode('utf-8')

            files = []
            for line in output.strip().split('\n'):
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 9:
                        file_path = ' '.join(parts[8:])
                        files.append({
                            'path': file_path,
                            'name': os.path.basename(file_path),
                            'size': int(parts[4]) if parts[4].isdigit() else 0,
                            'modified_time': ' '.join(parts[5:8]),
                            'type': 'file'
                        })

            return files  # No limit - return all files

        except Exception as e:
            logger.error(f"SSH file listing failed: {str(e)}")
            return []
        finally:
            client.close()

    def _list_files_sftp(self, connection: Dict[str, Any], credentials: Dict[str, Any], path: str) -> List[Dict[str, Any]]:
        """List files via SFTP"""
        transport = paramiko.Transport((connection['host'], connection['port']))

        try:
            # Connect
            if credentials.get('private_key'):
                private_key = paramiko.RSAKey.from_private_key(io.StringIO(credentials['private_key']))
                transport.connect(username=connection['username'], pkey=private_key)
            else:
                transport.connect(username=connection['username'], password=credentials.get('password', ''))

            sftp = paramiko.SFTPClient.from_transport(transport)

            files = []

            def _recursive_list_sftp(current_path):
                """Recursively list all files in directory and subdirectories"""
                try:
                    file_list = sftp.listdir_attr(current_path)
                    for file_attr in file_list:
                        if not file_attr.filename.startswith('.'):
                            file_path = os.path.join(current_path, file_attr.filename).replace('\\', '/')

                            if stat.S_ISDIR(file_attr.st_mode):
                                # Recursively process subdirectory
                                _recursive_list_sftp(file_path)
                            else:
                                # Add file to list
                                files.append({
                                    'path': file_path,
                                    'name': file_attr.filename,
                                    'size': file_attr.st_size or 0,
                                    'modified_time': file_attr.st_mtime,
                                    'type': 'file'
                                })
                except Exception as e:
                    logger.warning(f"Could not list directory {current_path}: {str(e)}")

            _recursive_list_sftp(path)
            return files  # No limit - return all files

        except Exception as e:
            logger.error(f"SFTP file listing failed: {str(e)}")
            return []
        finally:
            transport.close()

    def _list_files_ftp(self, connection: Dict[str, Any], credentials: Dict[str, Any], path: str) -> List[Dict[str, Any]]:
        """List files via FTP"""
        try:
            ftp = FTP()
            ftp.connect(connection['host'], connection['port'])
            ftp.login(connection['username'], credentials.get('password', ''))

            files = []

            def _recursive_list_ftp(current_path):
                """Recursively list all files in directory and subdirectories"""
                try:
                    ftp.cwd(current_path)
                    file_list = []
                    ftp.retrlines('LIST', file_list.append)

                    for line in file_list:  # No limit - process all files
                        parts = line.split()
                        if len(parts) >= 9:
                            filename = ' '.join(parts[8:])
                            if not filename.startswith('.') and filename not in ['.', '..']:
                                file_path = os.path.join(current_path, filename).replace('\\', '/')

                                if line.startswith('d'):
                                    # Directory - recurse into it
                                    _recursive_list_ftp(file_path)
                                else:
                                    # File - add to list
                                    files.append({
                                        'path': file_path,
                                        'name': filename,
                                        'size': int(parts[4]) if parts[4].isdigit() else 0,
                                        'modified_time': ' '.join(parts[5:8]),
                                        'type': 'file'
                                    })
                except Exception as e:
                    logger.warning(f"Could not list FTP directory {current_path}: {str(e)}")

            _recursive_list_ftp(path)
            ftp.quit()
            return files  # No limit - return all files

        except Exception as e:
            logger.error(f"FTP file listing failed: {str(e)}")
            return []

    def _list_files_http(self, connection: Dict[str, Any], credentials: Dict[str, Any], path: str) -> List[Dict[str, Any]]:
        """List files via HTTP (basic directory listing)"""
        try:
            base_url = f"{connection['protocol']}://{connection['host']}"
            if connection['port'] not in [80, 443]:
                base_url += f":{connection['port']}"

            url = urljoin(base_url, path)

            auth = None
            if connection.get('username') and credentials.get('password'):
                auth = (connection['username'], credentials['password'])

            response = requests.get(url, auth=auth, timeout=10)
            response.raise_for_status()

            files = []
            visited_urls = set()  # Track visited URLs to avoid infinite loops

            def _recursive_list_http(current_url, current_path=""):
                """Recursively list all files from HTTP directory listings"""
                if current_url in visited_urls:
                    return
                visited_urls.add(current_url)

                try:
                    auth = None
                    if connection.get('username') and credentials.get('password'):
                        auth = (connection['username'], credentials['password'])

                    response = requests.get(current_url, auth=auth, timeout=10)
                    response.raise_for_status()

                    # Enhanced HTML parsing for directory listings with size extraction
                    content = response.text.lower()
                    if 'index of' in content or '<a href=' in content:
                        import re
                        from datetime import datetime

                        # Parse HTML table rows to extract file information
                        # Look for patterns like: <a href="file.txt">file.txt</a>    date    size
                        html_content = response.text

                        # Try to extract file info from table rows or pre-formatted listings
                        # Pattern 1: Standard Apache/nginx directory listing
                        table_rows = re.findall(r'<tr[^>]*>.*?</tr>', html_content, re.IGNORECASE | re.DOTALL)

                        if not table_rows:
                            # Pattern 2: Simple pre-formatted listing
                            lines = html_content.split('\n')
                            table_rows = [line for line in lines if '<a href=' in line.lower()]

                        for row in table_rows:
                            # Extract link
                            link_match = re.search(r'<a href="([^"]+)"[^>]*>([^<]+)</a>', row, re.IGNORECASE)
                            if not link_match:
                                continue

                            href, text = link_match.groups()

                            if href.startswith('..') or href.startswith('http') or href == '/':
                                continue

                            full_url = urljoin(current_url, href)

                            if href.endswith('/'):
                                # Directory - recurse into it
                                _recursive_list_http(full_url, os.path.join(current_path, href.rstrip('/')))
                            elif '.' in href:
                                # File - extract size and date if available
                                file_size = 0
                                modified_time = ''

                                # Try to extract size from the row
                                # Look for patterns like "1.2K", "345", "1.5M", etc.
                                size_patterns = [
                                    r'(\d+(?:\.\d+)?[KMG]?)\s*(?:bytes?)?',  # 1.2K, 345, 1.5M
                                    r'>(\d+)<',  # >12345<
                                    r'\s(\d+)\s',  # space-separated numbers
                                ]

                                for pattern in size_patterns:
                                    size_match = re.search(pattern, row, re.IGNORECASE)
                                    if size_match:
                                        size_str = size_match.group(1)
                                        try:
                                            # Convert size string to bytes
                                            if size_str.endswith('K'):
                                                file_size = int(float(size_str[:-1]) * 1024)
                                            elif size_str.endswith('M'):
                                                file_size = int(float(size_str[:-1]) * 1024 * 1024)
                                            elif size_str.endswith('G'):
                                                file_size = int(float(size_str[:-1]) * 1024 * 1024 * 1024)
                                            else:
                                                file_size = int(size_str)
                                            break
                                        except (ValueError, IndexError):
                                            continue

                                # Try to extract date (basic attempt)
                                date_patterns = [
                                    r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})',  # 2025-07-01 05:23
                                    r'(\d{2}-\w{3}-\d{4}\s+\d{2}:\d{2})',  # 01-Jul-2025 05:23
                                ]

                                for pattern in date_patterns:
                                    date_match = re.search(pattern, row)
                                    if date_match:
                                        modified_time = date_match.group(1)
                                        break

                                file_path = os.path.join(current_path, href).replace('\\', '/') if current_path else href
                                files.append({
                                    'path': full_url,
                                    'name': href,
                                    'size': file_size,
                                    'modified_time': modified_time,
                                    'type': 'file'
                                })

                                logger.debug(f"Parsed file: {href}, size: {file_size}, modified: {modified_time}")
                except Exception as e:
                    logger.warning(f"Could not list HTTP directory {current_url}: {str(e)}")

            _recursive_list_http(url)
            return files  # No limit - return all files

        except Exception as e:
            logger.error(f"HTTP file listing failed: {str(e)}")
            return []

    def _get_file_content_ssh(self, connection: Dict[str, Any], credentials: Dict[str, Any], file_path: str) -> str:
        """Get file content via SSH"""
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            # Connect
            if credentials.get('private_key'):
                private_key = paramiko.RSAKey.from_private_key(io.StringIO(credentials['private_key']))
                client.connect(
                    connection['host'],
                    port=connection['port'],
                    username=connection['username'],
                    pkey=private_key,
                    timeout=10
                )
            else:
                client.connect(
                    connection['host'],
                    port=connection['port'],
                    username=connection['username'],
                    password=credentials.get('password', ''),
                    timeout=10
                )

            # Get file content
            stdin, stdout, stderr = client.exec_command(f'cat "{file_path}"')
            content = stdout.read().decode('utf-8', errors='ignore')

            return content

        except Exception as e:
            logger.error(f"SSH file content retrieval failed: {str(e)}")
            return ""
        finally:
            client.close()

    def _get_file_content_sftp(self, connection: Dict[str, Any], credentials: Dict[str, Any], file_path: str) -> str:
        """Get file content via SFTP"""
        transport = paramiko.Transport((connection['host'], connection['port']))

        try:
            # Connect
            if credentials.get('private_key'):
                private_key = paramiko.RSAKey.from_private_key(io.StringIO(credentials['private_key']))
                transport.connect(username=connection['username'], pkey=private_key)
            else:
                transport.connect(username=connection['username'], password=credentials.get('password', ''))

            sftp = paramiko.SFTPClient.from_transport(transport)

            # Get file content
            with sftp.open(file_path, 'r') as file:
                content = file.read().decode('utf-8', errors='ignore')

            return content

        except Exception as e:
            logger.error(f"SFTP file content retrieval failed: {str(e)}")
            return ""
        finally:
            transport.close()

    def _get_file_content_ftp(self, connection: Dict[str, Any], credentials: Dict[str, Any], file_path: str) -> str:
        """Get file content via FTP"""
        try:
            ftp = FTP()
            ftp.connect(connection['host'], connection['port'])
            ftp.login(connection['username'], credentials.get('password', ''))

            # Get file content
            content_lines = []
            ftp.retrlines(f'RETR {file_path}', content_lines.append)
            content = '\n'.join(content_lines)

            ftp.quit()
            return content

        except Exception as e:
            logger.error(f"FTP file content retrieval failed: {str(e)}")
            return ""

    def _get_file_content_http(self, connection: Dict[str, Any], credentials: Dict[str, Any], file_path: str) -> str:
        """Get file content via HTTP"""
        try:
            auth = None
            if connection.get('username') and credentials.get('password'):
                auth = (connection['username'], credentials['password'])

            # The file_path is already a complete URL from _list_files_http
            # Try both the original URL and URL-decoded version
            from urllib.parse import unquote

            logger.debug(f"Attempting to fetch HTTP file content from: {file_path}")

            # First try the original URL as-is
            try:
                response = requests.get(file_path, auth=auth, timeout=30)
                response.raise_for_status()
                logger.debug(f"Successfully fetched content using original URL: {file_path}")
                return response.text
            except requests.exceptions.RequestException as e1:
                logger.debug(f"Original URL failed ({e1}), trying URL-decoded version")

                # If that fails, try URL-decoded version
                decoded_file_path = unquote(file_path)
                logger.debug(f"Attempting URL-decoded path: {decoded_file_path}")
                response = requests.get(decoded_file_path, auth=auth, timeout=30)
                response.raise_for_status()
                logger.debug(f"Successfully fetched content using decoded URL: {decoded_file_path}")
                return response.text

        except Exception as e:
            logger.error(f"HTTP file content retrieval failed for {file_path}: {str(e)}")
            return ""
