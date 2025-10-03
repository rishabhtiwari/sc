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
