"""
Remote Host Syncer Service
Handles syncing data from remote host connections to embedding service
"""
import os
import time
import json
import sqlite3
import requests
import paramiko
import ftplib
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

from config.settings import Config
from utils.logger import setup_logger, log_sync_event, log_performance
from services.job_instance_service import JobInstanceService

class RemoteHostSyncerService:
    """Service for syncing remote host data to embedding service"""

    def __init__(self):
        self.logger = setup_logger('syncer-service')
        self.config = Config()
        self.job_instance_service = JobInstanceService(self.config)
        # Track active jobs and their cancellation events
        self.active_jobs = {}  # job_id -> {'thread': thread, 'cancel_event': Event}
        self.jobs_lock = threading.Lock()
        self._init_database()
        
    def _init_database(self):
        """Initialize SQLite database for tracking sync state"""
        db_dir = os.path.dirname(self.config.DB_PATH)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
            
        with sqlite3.connect(self.config.DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sync_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    connection_id TEXT NOT NULL,
                    sync_started_at TIMESTAMP,
                    sync_completed_at TIMESTAMP,
                    status TEXT NOT NULL,
                    files_processed INTEGER DEFAULT 0,
                    files_indexed INTEGER DEFAULT 0,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS file_sync_state (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    connection_id TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_hash TEXT,
                    last_modified TIMESTAMP,
                    last_synced TIMESTAMP,
                    sync_status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(connection_id, file_path)
                )
            ''')
            conn.commit()

    def register_job_thread(self, job_id: str, thread: threading.Thread, cancel_event: threading.Event):
        """Register a job thread with its cancellation event"""
        with self.jobs_lock:
            self.active_jobs[job_id] = {
                'thread': thread,
                'cancel_event': cancel_event,
                'registered_at': time.time()
            }
            self.logger.info(f"Registered job thread {job_id}")

    def unregister_job_thread(self, job_id: str):
        """Unregister a job thread when it completes"""
        with self.jobs_lock:
            if job_id in self.active_jobs:
                del self.active_jobs[job_id]
                self.logger.info(f"Unregistered job thread {job_id}")

    def cancel_job_thread(self, job_id: str) -> bool:
        """Cancel a specific job thread by setting its cancellation event"""
        with self.jobs_lock:
            if job_id in self.active_jobs:
                job_info = self.active_jobs[job_id]
                cancel_event = job_info['cancel_event']
                cancel_event.set()
                self.logger.info(f"Cancellation signal sent to job {job_id}")
                return True
            else:
                self.logger.warning(f"Job {job_id} not found in active jobs for cancellation")
                return False

    def get_active_job_threads(self) -> Dict[str, Dict]:
        """Get information about all active job threads"""
        with self.jobs_lock:
            return dict(self.active_jobs)

    def cleanup_finished_threads(self):
        """Clean up finished threads from active jobs tracking"""
        with self.jobs_lock:
            finished_jobs = []
            for job_id, job_info in self.active_jobs.items():
                thread = job_info['thread']
                if not thread.is_alive():
                    finished_jobs.append(job_id)

            for job_id in finished_jobs:
                del self.active_jobs[job_id]
                self.logger.info(f"Cleaned up finished thread for job {job_id}")

    def get_active_connections(self) -> List[Dict[str, Any]]:
        """Get all active remote host connections from MCP service"""
        try:
            response = requests.get(
                f"{self.config.API_SERVER_URL}/api/mcp/providers/remote_host/connections",
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            if data.get('status') == 'success':
                # Filter only active connections
                active_connections = [
                    conn for conn in data.get('connections', [])
                    if conn.get('status') == 'active'
                ]
                self.logger.info(f"Found {len(active_connections)} active connections")
                return active_connections
            else:
                self.logger.error(f"Failed to get connections: {data.get('error', 'Unknown error')}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error getting active connections: {str(e)}")
            return []
    
    def sync_all_connections(self) -> Dict[str, Any]:
        """Sync data from all active connections"""
        start_time = time.time()
        self.logger.info("🔄 Starting sync for all active connections")
        
        connections = self.get_active_connections()
        if not connections:
            self.logger.warning("No active connections found to sync")
            return {
                'status': 'success',
                'message': 'No active connections to sync',
                'connections_processed': 0,
                'total_files': 0,
                'duration_ms': int((time.time() - start_time) * 1000)
            }
        
        results = []
        total_files = 0
        
        # Process connections concurrently (but limited)
        with ThreadPoolExecutor(max_workers=self.config.MAX_CONCURRENT_CONNECTIONS) as executor:
            future_to_connection = {
                executor.submit(self.sync_connection, conn): conn 
                for conn in connections
            }
            
            for future in as_completed(future_to_connection):
                connection = future_to_connection[future]
                try:
                    result = future.result()
                    results.append(result)
                    total_files += result.get('files_processed', 0)
                    
                    log_sync_event(
                        self.logger, 
                        'complete' if result['status'] == 'success' else 'error',
                        connection['id'],
                        result
                    )
                    
                except Exception as e:
                    error_result = {
                        'connection_id': connection['id'],
                        'connection_name': connection.get('name', 'Unknown'),
                        'status': 'error',
                        'error': str(e),
                        'files_processed': 0
                    }
                    results.append(error_result)
                    
                    log_sync_event(
                        self.logger, 
                        'error',
                        connection['id'],
                        {'error': str(e)}
                    )
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Log performance
        log_performance(
            self.logger,
            'sync_all_connections',
            duration_ms,
            total_files
        )
        
        successful_syncs = len([r for r in results if r['status'] == 'success'])
        
        return {
            'status': 'success',
            'message': f'Sync completed: {successful_syncs}/{len(connections)} connections successful',
            'connections_processed': len(connections),
            'successful_syncs': successful_syncs,
            'total_files': total_files,
            'duration_ms': duration_ms,
            'results': results
        }

    def sync_connection(self, connection: Dict[str, Any], job_id: str = None, cancel_event: threading.Event = None) -> Dict[str, Any]:
        """Sync data from a single connection with cancellation support"""
        connection_id = connection['id']
        connection_name = connection.get('name', 'Unknown')
        protocol = connection.get('protocol', 'unknown')

        self.logger.info(f"🔄 Starting sync for connection: {connection_name} ({protocol})")

        # Helper function to check for cancellation
        def is_cancelled():
            if cancel_event and cancel_event.is_set():
                return True
            # Also check database status as fallback
            if job_id:
                job = self.job_instance_service.get_job_instance(job_id)
                if job and job['status'] == 'cancelled':
                    return True
            return False

        # Check if there's already an active job for this connection (excluding current job)
        active_jobs = self.job_instance_service.get_active_connection_jobs(connection_id)
        if active_jobs:
            # Filter out the current job if it exists
            other_active_jobs = [job for job in active_jobs if job['id'] != job_id]
            if other_active_jobs:
                active_job = other_active_jobs[0]
                self.logger.warning(f"Sync already in progress for connection {connection_name} (job: {active_job['id']})")
                return {
                    'connection_id': connection_id,
                    'connection_name': connection_name,
                    'status': 'skipped',
                    'message': 'Sync already in progress',
                    'job_id': active_job['id']
                }

        # Create or update job instance
        if not job_id:
            job_id = self.job_instance_service.create_job_instance(
                job_type='connection_sync',
                connection_id=connection_id,
                metadata={'connection_name': connection_name, 'protocol': protocol}
            )

        # Update job status to running
        self.job_instance_service.update_job_status(job_id, 'running')

        # Record sync start
        sync_id = self._record_sync_start(connection_id)

        try:
            start_time = time.time()

            # Check for cancellation before starting
            if is_cancelled():
                self.logger.info(f"Job {job_id} was cancelled before file fetching")
                self._record_sync_complete(sync_id, 'cancelled', 0, 0, 'Job cancelled by user')
                self.job_instance_service.update_job_status(job_id, 'cancelled', error_message='Job cancelled by user')
                return {
                    'connection_id': connection_id,
                    'connection_name': connection_name,
                    'status': 'cancelled',
                    'message': 'Job cancelled by user',
                    'files_processed': 0,
                    'files_indexed': 0,
                    'job_id': job_id
                }

            # Get files from remote host based on protocol
            files = self._fetch_files_from_connection(connection)

            # Check for cancellation after file fetching
            if is_cancelled():
                self.logger.info(f"Job {job_id} was cancelled after file fetching")
                self._record_sync_complete(sync_id, 'cancelled', 0, 0, 'Job cancelled by user')
                self.job_instance_service.update_job_status(job_id, 'cancelled', error_message='Job cancelled by user')
                return {
                    'connection_id': connection_id,
                    'connection_name': connection_name,
                    'status': 'cancelled',
                    'message': 'Job cancelled by user',
                    'files_processed': 0,
                    'files_indexed': 0,
                    'job_id': job_id
                }

            if not files:
                self.logger.warning(f"No files found for connection {connection_name}")
                self._record_sync_complete(sync_id, 'success', 0, 0)
                self.job_instance_service.update_job_status(job_id, 'completed', 100, 0, 0)
                return {
                    'connection_id': connection_id,
                    'connection_name': connection_name,
                    'status': 'success',
                    'message': 'No files to sync',
                    'files_processed': 0,
                    'files_indexed': 0,
                    'job_id': job_id
                }

            # No filtering - process all files
            files_to_sync = files

            # Update job with total files count
            self.job_instance_service.update_job_status(
                job_id, 'running',
                total_files=len(files),
                processed_files=0
            )

            if not files_to_sync:
                self.logger.info(f"No files found for connection {connection_name}")
                self._record_sync_complete(sync_id, 'success', 0, 0)
                self.job_instance_service.update_job_status(job_id, 'completed', 100, 0, 0)
                return {
                    'connection_id': connection_id,
                    'connection_name': connection_name,
                    'status': 'success',
                    'message': 'No files to process',
                    'files_processed': 0,
                    'files_indexed': 0,
                    'files_skipped': 0,
                    'job_id': job_id
                }

            # Process files in batches - no filtering, process all files
            files_indexed = 0
            total_failed_files = 0
            all_failed_files = []

            self.logger.info(f"Processing all {len(files_to_sync)} files (no filtering applied)")

            for i in range(0, len(files_to_sync), self.config.BATCH_SIZE):
                # Check for cancellation before processing each batch
                if is_cancelled():
                    self.logger.info(f"Job {job_id} was cancelled during batch processing (batch {i//self.config.BATCH_SIZE + 1})")
                    self._record_sync_complete(sync_id, 'cancelled', processed_files, files_indexed, 'Job cancelled by user')
                    self.job_instance_service.update_job_status(job_id, 'cancelled', error_message='Job cancelled by user')
                    return {
                        'connection_id': connection_id,
                        'connection_name': connection_name,
                        'status': 'cancelled',
                        'message': f'Job cancelled during processing (processed {processed_files}/{len(files)} files)',
                        'files_processed': processed_files,
                        'files_indexed': files_indexed,
                        'job_id': job_id
                    }

                batch = files_to_sync[i:i + self.config.BATCH_SIZE]
                batch_result = self._process_file_batch(connection, batch)

                files_indexed += batch_result.get('files_indexed', 0)
                total_failed_files += batch_result.get('files_failed', 0)
                all_failed_files.extend(batch_result.get('failed_files', []))

                # Update progress - no skipped files since we process all files
                files_actually_processed = min(i + self.config.BATCH_SIZE, len(files_to_sync))
                processed_files = files_actually_processed
                progress = int((processed_files / len(files_to_sync)) * 100)
                self.job_instance_service.update_job_status(
                    job_id, 'running',
                    progress=progress,
                    processed_files=processed_files
                )

                self.logger.info(f"Batch {i//self.config.BATCH_SIZE + 1}: {batch_result.get('files_indexed', 0)} indexed, {batch_result.get('files_failed', 0)} failed")

            # Final check for cancellation after all batches are processed
            if is_cancelled():
                self.logger.info(f"Job {job_id} was cancelled after batch processing completed")
                self._record_sync_complete(sync_id, 'cancelled', processed_files, files_indexed, 'Job cancelled by user')
                self.job_instance_service.update_job_status(job_id, 'cancelled', error_message='Job cancelled by user')
                return {
                    'connection_id': connection_id,
                    'connection_name': connection_name,
                    'status': 'cancelled',
                    'message': f'Job cancelled after processing (processed {processed_files}/{len(files)} files)',
                    'files_processed': processed_files,
                    'files_indexed': files_indexed,
                    'job_id': job_id
                }

            duration_ms = int((time.time() - start_time) * 1000)

            # Record successful sync
            self._record_sync_complete(sync_id, 'success', len(files_to_sync), files_indexed)

            # Final processed files count - all files were processed (no skipping)
            final_processed_files = len(files_to_sync)

            # Update job status to completed
            self.job_instance_service.update_job_status(
                job_id, 'completed',
                progress=100,
                processed_files=final_processed_files
            )

            self.logger.info(
                f"✅ Sync completed for {connection_name}: "
                f"{files_indexed}/{len(files_to_sync)} files indexed, {total_failed_files} failed in {duration_ms}ms"
            )

            return {
                'connection_id': connection_id,
                'connection_name': connection_name,
                'status': 'success',
                'message': f'Sync completed: {files_indexed} indexed, {total_failed_files} failed',
                'files_processed': final_processed_files,
                'files_indexed': files_indexed,
                'files_failed': total_failed_files,
                'files_skipped': 0,  # No files skipped since we process all files
                'failed_files': all_failed_files[:10] if all_failed_files else [],  # Limit to first 10 for response size
                'duration_ms': duration_ms,
                'job_id': job_id
            }

        except Exception as e:
            error_msg = f"Sync failed for {connection_name}: {str(e)}"
            self.logger.error(error_msg)
            self._record_sync_complete(sync_id, 'error', 0, 0, str(e))

            # Update job status to failed
            self.job_instance_service.update_job_status(
                job_id, 'failed',
                error_message=str(e)
            )

            return {
                'connection_id': connection_id,
                'connection_name': connection_name,
                'status': 'error',
                'error': str(e),
                'files_processed': 0,
                'files_indexed': 0,
                'job_id': job_id
            }

    def _record_sync_start(self, connection_id: str) -> int:
        """Record sync start in database"""
        with sqlite3.connect(self.config.DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO sync_history (connection_id, sync_started_at, status)
                VALUES (?, CURRENT_TIMESTAMP, 'running')
            ''', (connection_id,))
            conn.commit()
            return cursor.lastrowid

    def _record_sync_complete(self, sync_id: int, status: str, files_processed: int,
                             files_indexed: int, error_message: str = None):
        """Record sync completion in database"""
        with sqlite3.connect(self.config.DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE sync_history
                SET sync_completed_at = CURRENT_TIMESTAMP,
                    status = ?,
                    files_processed = ?,
                    files_indexed = ?,
                    error_message = ?
                WHERE id = ?
            ''', (status, files_processed, files_indexed, error_message, sync_id))
            conn.commit()

    def _fetch_files_from_connection(self, connection: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch file list from remote connection via MCP service"""
        try:
            connection_id = connection.get('id')
            if not connection_id:
                self.logger.error(f"No connection ID found for connection: {connection.get('name', 'Unknown')}")
                return []

            # Call MCP service directly to list files
            response = requests.get(
                f"{self.config.MCP_SERVICE_URL}/mcp/remote-host/connections/{connection_id}/files",
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'success':
                    files = result.get('files', [])
                    self.logger.info(f"Retrieved {len(files)} files from connection {connection.get('name', 'Unknown')}")
                    return files
                else:
                    self.logger.warning(f"MCP service returned error for connection {connection.get('name', 'Unknown')}: {result.get('message', 'Unknown error')}")
                    return []
            else:
                self.logger.error(f"Failed to get files from MCP service for connection {connection.get('name', 'Unknown')}: HTTP {response.status_code}")
                return []

        except Exception as e:
            self.logger.error(f"Error fetching files from {connection.get('name', 'Unknown')}: {str(e)}")
            return []

    def _fetch_file_content_directly(self, connection: Dict[str, Any], file_path: str) -> str:
        """Fetch file content directly from remote host"""
        try:
            protocol = connection.get('protocol', '').lower()

            if protocol in ['http', 'https']:
                return self._fetch_file_content_http(connection, file_path)
            elif protocol == 'ssh':
                return self._fetch_file_content_ssh(connection, file_path)
            elif protocol == 'sftp':
                return self._fetch_file_content_sftp(connection, file_path)
            elif protocol == 'ftp':
                return self._fetch_file_content_ftp(connection, file_path)
            else:
                self.logger.error(f"Unsupported protocol for file content fetching: {protocol}")
                return ""

        except Exception as e:
            self.logger.error(f"Error fetching file content for {file_path}: {str(e)}")
            return ""

    def _fetch_file_content_http(self, connection: Dict[str, Any], file_path: str) -> str:
        """Fetch file content via HTTP/HTTPS"""
        try:
            # Get credentials from MCP service for authentication
            credentials = self._get_connection_credentials(connection['id'])

            auth = None
            if credentials and credentials.get('username'):
                auth = (credentials['username'], credentials.get('password', ''))

            # First try the original URL as-is
            try:
                response = requests.get(file_path, auth=auth, timeout=30)
                response.raise_for_status()
                self.logger.debug(f"Successfully fetched content using original URL: {file_path}")
                return response.text
            except requests.exceptions.RequestException as e1:
                self.logger.debug(f"Original URL failed ({e1}), trying URL-decoded version")

                # If that fails, try URL-decoded version
                from urllib.parse import unquote
                decoded_file_path = unquote(file_path)
                self.logger.debug(f"Attempting URL-decoded path: {decoded_file_path}")
                response = requests.get(decoded_file_path, auth=auth, timeout=30)
                response.raise_for_status()
                self.logger.debug(f"Successfully fetched content using decoded URL: {decoded_file_path}")
                return response.text

        except Exception as e:
            self.logger.error(f"HTTP file content retrieval failed for {file_path}: {str(e)}")
            return ""

    def _fetch_file_content_ssh(self, connection: Dict[str, Any], file_path: str) -> str:
        """Fetch file content via SSH"""
        import paramiko
        import io

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            # Get credentials from MCP service
            credentials = self._get_connection_credentials(connection['id'])
            if not credentials:
                self.logger.error(f"No credentials found for SSH connection {connection['id']}")
                return ""

            # Connect
            if credentials.get('private_key'):
                private_key = paramiko.RSAKey.from_private_key(io.StringIO(credentials['private_key']))
                client.connect(
                    connection['host'],
                    port=connection.get('port', 22),
                    username=connection['username'],
                    pkey=private_key,
                    timeout=10
                )
            else:
                client.connect(
                    connection['host'],
                    port=connection.get('port', 22),
                    username=connection['username'],
                    password=credentials.get('password', ''),
                    timeout=10
                )

            # Get file content
            stdin, stdout, stderr = client.exec_command(f'cat "{file_path}"')
            content = stdout.read().decode('utf-8', errors='ignore')

            return content

        except Exception as e:
            self.logger.error(f"SSH file content retrieval failed for {file_path}: {str(e)}")
            return ""
        finally:
            client.close()

    def _fetch_file_content_sftp(self, connection: Dict[str, Any], file_path: str) -> str:
        """Fetch file content via SFTP"""
        import paramiko
        import io

        transport = None
        try:
            # Get credentials from MCP service
            credentials = self._get_connection_credentials(connection['id'])
            if not credentials:
                self.logger.error(f"No credentials found for SFTP connection {connection['id']}")
                return ""

            # Create transport
            transport = paramiko.Transport((connection['host'], connection.get('port', 22)))

            if credentials.get('private_key'):
                private_key = paramiko.RSAKey.from_private_key(io.StringIO(credentials['private_key']))
                transport.connect(username=connection['username'], pkey=private_key)
            else:
                transport.connect(username=connection['username'], password=credentials.get('password', ''))

            # Create SFTP client
            sftp = paramiko.SFTPClient.from_transport(transport)

            # Get file content
            with sftp.open(file_path, 'r') as remote_file:
                content = remote_file.read().decode('utf-8', errors='ignore')

            return content

        except Exception as e:
            self.logger.error(f"SFTP file content retrieval failed for {file_path}: {str(e)}")
            return ""
        finally:
            if transport:
                transport.close()

    def _fetch_file_content_ftp(self, connection: Dict[str, Any], file_path: str) -> str:
        """Fetch file content via FTP"""
        from ftplib import FTP

        try:
            # Get credentials from MCP service
            credentials = self._get_connection_credentials(connection['id'])

            ftp = FTP()
            ftp.connect(connection['host'], connection.get('port', 21))
            ftp.login(connection['username'], credentials.get('password', '') if credentials else '')

            # Get file content
            content_lines = []
            ftp.retrlines(f'RETR {file_path}', content_lines.append)
            content = '\n'.join(content_lines)

            ftp.quit()
            return content

        except Exception as e:
            self.logger.error(f"FTP file content retrieval failed for {file_path}: {str(e)}")
            return ""

    def _get_connection_credentials(self, connection_id: str) -> Dict[str, Any]:
        """Get decrypted credentials for a connection from MCP service"""
        try:
            response = requests.get(
                f"{self.config.MCP_SERVICE_URL}/mcp/remote-host/connections/{connection_id}/credentials",
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'success':
                    return result.get('credentials', {})

            self.logger.error(f"Failed to get credentials for connection {connection_id}")
            return {}

        except Exception as e:
            self.logger.error(f"Error getting credentials for connection {connection_id}: {str(e)}")
            return {}



    def _process_file_batch(self, connection: Dict[str, Any], files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process a batch of files and send to embedding service"""
        connection_id = connection['id']
        connection_name = connection.get('name', 'Unknown')

        documents = []
        processed_files = []
        failed_files = []

        for file_info in files:
            file_path = file_info['path']

            try:
                # Fetch file content directly from remote host
                content = self._fetch_file_content_directly(connection, file_path)

                if not content:
                    self.logger.warning(f"Could not fetch content for {file_path}, skipping...")
                    failed_files.append({'file_path': file_path, 'error': 'No content retrieved'})
                    continue

                # Prepare document for embedding service
                document = {
                    'content': content,
                    'metadata': {
                        'source': 'remote_host',
                        'connection_id': connection_id,
                        'connection_name': connection_name,
                        'file_path': file_path,
                        'file_name': file_info.get('name', os.path.basename(file_path)),
                        'file_size': file_info.get('size', 0),
                        'modified_time': file_info.get('modified_time'),
                        'protocol': connection.get('protocol'),
                        'host': connection.get('host'),
                        'sync_timestamp': datetime.now().isoformat()
                    }
                }

                documents.append(document)
                processed_files.append(file_info)

            except Exception as e:
                self.logger.warning(f"Error processing file {file_path}: {str(e)}, skipping...")
                failed_files.append({'file_path': file_path, 'error': str(e)})
                # Mark file as failed in sync state
                self._update_file_sync_state(connection_id, [file_info], 'failed')
                continue

        if not documents:
            self.logger.warning(f"No documents to process in batch. Failed files: {len(failed_files)}")
            return {
                'files_indexed': 0,
                'files_failed': len(failed_files),
                'failed_files': failed_files,
                'error': 'No documents to process'
            }

        # Send batch to embedding service
        try:
            response = requests.post(
                f"{self.config.EMBEDDING_SERVICE_URL}/embed/documents",
                json={'documents': documents},
                timeout=300  # 5 minutes for batch processing
            )
            response.raise_for_status()

            result = response.json()

            if result.get('status') == 'success':
                files_indexed = result.get('total_documents', 0)

                # Update file sync state
                self._update_file_sync_state(connection_id, processed_files, 'synced')

                self.logger.info(f"Successfully indexed {files_indexed} files from {connection_name}. Failed: {len(failed_files)}")

                return {
                    'files_indexed': files_indexed,
                    'files_failed': len(failed_files),
                    'failed_files': failed_files,
                    'total_chunks': result.get('total_chunks', 0),
                    'processing_time_ms': result.get('processing_time_ms', 0)
                }
            else:
                error_msg = result.get('error', 'Unknown error from embedding service')
                self.logger.error(f"Embedding service error: {error_msg}")
                self._update_file_sync_state(connection_id, processed_files, 'error')
                return {
                    'files_indexed': 0,
                    'files_failed': len(failed_files),
                    'failed_files': failed_files,
                    'error': error_msg
                }

        except Exception as e:
            error_msg = f"Failed to send documents to embedding service: {str(e)}"
            self.logger.error(error_msg)
            self._update_file_sync_state(connection_id, processed_files, 'error')
            return {
                'files_indexed': 0,
                'files_failed': len(failed_files),
                'failed_files': failed_files,
                'error': error_msg
            }

    def _update_file_sync_state(self, connection_id: str, files: List[Dict[str, Any]], status: str):
        """Update sync state for processed files"""
        with sqlite3.connect(self.config.DB_PATH) as conn:
            cursor = conn.cursor()

            for file_info in files:
                file_path = file_info['path']
                modified_time = file_info.get('modified_time')

                cursor.execute('''
                    INSERT OR REPLACE INTO file_sync_state
                    (connection_id, file_path, file_hash, last_modified, last_synced, sync_status)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
                ''', (connection_id, file_path, None, modified_time, status))

            conn.commit()
