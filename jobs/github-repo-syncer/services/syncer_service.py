"""
GitHub Repository Syncer Service
Handles syncing data from GitHub repositories to embedding service
"""
import os
import time
import json
import sqlite3
import requests
import threading
import tempfile
import shutil
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import subprocess

from config.settings import Config
from utils.logger import setup_logger, log_sync_event, log_performance, ProgressLogger
from services.job_instance_service import JobInstanceService

class GitHubRepoSyncerService:
    """Service for syncing GitHub repository data to embedding service"""

    def __init__(self):
        self.logger = setup_logger('github-syncer-service')
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
                    repository_id TEXT NOT NULL,
                    sync_started_at TIMESTAMP,
                    sync_completed_at TIMESTAMP,
                    status TEXT NOT NULL,
                    files_processed INTEGER DEFAULT 0,
                    files_indexed INTEGER DEFAULT 0,
                    error_message TEXT,
                    commit_sha TEXT,
                    branch TEXT DEFAULT 'main',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS file_sync_state (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    repository_id TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_hash TEXT,
                    last_modified TIMESTAMP,
                    file_size INTEGER,
                    sync_status TEXT DEFAULT 'pending',
                    last_synced_at TIMESTAMP,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(repository_id, file_path)
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sync_history_repo ON sync_history(repository_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_file_sync_repo ON file_sync_state(repository_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_file_sync_status ON file_sync_state(sync_status)')
            
            conn.commit()
    
    def register_job_thread(self, job_id: str, thread: threading.Thread, cancel_event: threading.Event):
        """Register a job thread for cancellation tracking"""
        with self.jobs_lock:
            self.active_jobs[job_id] = {
                'thread': thread,
                'cancel_event': cancel_event,
                'registered_at': datetime.now().isoformat()
            }
    
    def unregister_job_thread(self, job_id: str):
        """Unregister a job thread"""
        with self.jobs_lock:
            if job_id in self.active_jobs:
                del self.active_jobs[job_id]
    
    def cancel_job_thread(self, job_id: str) -> bool:
        """Cancel a job thread by setting its cancel event"""
        with self.jobs_lock:
            if job_id in self.active_jobs:
                self.active_jobs[job_id]['cancel_event'].set()
                return True
            return False
    
    def get_active_job_threads(self) -> Dict[str, Any]:
        """Get information about active job threads"""
        with self.jobs_lock:
            return self.active_jobs.copy()
    
    def cleanup_finished_threads(self):
        """Clean up finished threads from tracking"""
        with self.jobs_lock:
            finished_jobs = []
            for job_id, info in self.active_jobs.items():
                if not info['thread'].is_alive():
                    finished_jobs.append(job_id)
            
            for job_id in finished_jobs:
                del self.active_jobs[job_id]
    
    def get_active_repositories(self) -> List[Dict[str, Any]]:
        """Get all active GitHub repositories from MCP service"""
        try:
            # Get GitHub tokens from MCP service
            response = requests.get(
                f"{self.config.MCP_SERVICE_URL}/github/tokens",
                timeout=self.config.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            tokens_data = response.json()

            if not tokens_data.get('tokens'):
                self.logger.warning("No GitHub tokens found")
                return []

            repositories = []

            # Get repositories for each token
            for token_info in tokens_data['tokens']:
                token_id = token_info['token_id']
                
                try:
                    repo_response = requests.get(
                        f"{self.config.MCP_SERVICE_URL}/github/repositories",
                        params={'token_id': token_id},
                        timeout=self.config.REQUEST_TIMEOUT
                    )
                    repo_response.raise_for_status()
                    repo_data = repo_response.json()
                    
                    if repo_data.get('repositories'):
                        for repo in repo_data['repositories']:
                            repositories.append({
                                'id': f"github_{token_id}_{repo['id']}",
                                'token_id': token_id,
                                'github_id': repo['id'],
                                'name': repo['name'],
                                'full_name': repo['full_name'],
                                'clone_url': repo['clone_url'],
                                'default_branch': repo.get('default_branch', 'main'),
                                'private': repo.get('private', False),
                                'language': repo.get('language'),
                                'description': repo.get('description', ''),
                                'updated_at': repo.get('updated_at'),
                                'size': repo.get('size', 0)
                            })
                            
                except Exception as e:
                    self.logger.error(f"Failed to get repositories for token {token_id}: {str(e)}")
                    continue
            
            self.logger.info(f"Found {len(repositories)} active repositories")
            return repositories
            
        except Exception as e:
            self.logger.error(f"Failed to get active repositories: {str(e)}")
            return []
    
    def get_github_token(self, token_id: str) -> Optional[str]:
        """Get GitHub token by token ID"""
        try:
            response = requests.get(
                f"{self.config.MCP_SERVICE_URL}/github/token/{token_id}",
                timeout=self.config.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            token_data = response.json()
            return token_data.get('data', {}).get('access_token')
            
        except Exception as e:
            self.logger.error(f"Failed to get GitHub token {token_id}: {str(e)}")
            return None
    
    def sync_all_repositories(self) -> Dict[str, Any]:
        """Sync all active repositories"""
        start_time = time.time()
        
        try:
            repositories = self.get_active_repositories()
            if not repositories:
                return {
                    'status': 'success',
                    'message': 'No repositories to sync',
                    'repositories_processed': 0,
                    'successful_syncs': 0,
                    'failed_syncs': 0,
                    'total_files': 0
                }
            
            self.logger.info(f"Starting sync for {len(repositories)} repositories")
            
            successful_syncs = 0
            failed_syncs = 0
            total_files = 0
            
            # Use ThreadPoolExecutor for concurrent repository syncing
            with ThreadPoolExecutor(max_workers=self.config.MAX_CONCURRENT_REPOS) as executor:
                # Submit all repository sync tasks
                future_to_repo = {
                    executor.submit(self.sync_repository, repo): repo 
                    for repo in repositories
                }
                
                # Process completed tasks
                for future in as_completed(future_to_repo):
                    repo = future_to_repo[future]
                    try:
                        result = future.result()
                        if result['status'] == 'success':
                            successful_syncs += 1
                            total_files += result.get('files_processed', 0)
                        else:
                            failed_syncs += 1
                            
                    except Exception as e:
                        self.logger.error(f"Repository sync failed for {repo['name']}: {str(e)}")
                        failed_syncs += 1
            
            duration = time.time() - start_time
            
            result = {
                'status': 'success',
                'message': f'Sync completed: {successful_syncs} successful, {failed_syncs} failed',
                'repositories_processed': len(repositories),
                'successful_syncs': successful_syncs,
                'failed_syncs': failed_syncs,
                'total_files': total_files,
                'duration_seconds': duration
            }
            
            self.logger.info(f"Bulk sync completed in {duration:.2f}s: {result['message']}")
            return result
            
        except Exception as e:
            error_msg = f"Bulk sync failed: {str(e)}"
            self.logger.error(error_msg)
            return {
                'status': 'error',
                'error': error_msg,
                'repositories_processed': 0,
                'successful_syncs': 0,
                'failed_syncs': 0,
                'total_files': 0
            }
    
    def sync_repository(self, repository: Dict[str, Any], job_id: str = None,
                       cancel_event: threading.Event = None) -> Dict[str, Any]:
        """Sync a single repository"""
        repo_id = repository['id']
        repo_name = repository['name']

        start_time = time.time()

        # Update job status to running if job_id provided
        if job_id:
            self.job_instance_service.update_job_status(job_id, 'running')

        # Record sync start
        sync_id = self._record_sync_start(repo_id)

        try:
            self.logger.info(f"🔄 Starting sync for repository: {repo_name}")

            # Check for cancellation
            if cancel_event and cancel_event.is_set():
                return {'status': 'cancelled', 'message': 'Sync cancelled by user'}
            
            # Get GitHub token
            token = self.get_github_token(repository['token_id'])
            if not token:
                raise Exception(f"Failed to get GitHub token for repository {repo_name}")
            
            # Clone repository to temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                clone_path = os.path.join(temp_dir, repo_name)
                
                # Clone repository
                clone_result = self._clone_repository(repository, clone_path, token)
                if not clone_result['success']:
                    raise Exception(f"Failed to clone repository: {clone_result['error']}")
                
                # Check for cancellation after clone
                if cancel_event and cancel_event.is_set():
                    return {'status': 'cancelled', 'message': 'Sync cancelled by user'}
                
                # Process files in repository
                result = self._process_repository_files(
                    repository, clone_path, job_id, cancel_event
                )
                
                if result['status'] == 'cancelled':
                    return result
                
                # Record sync completion
                self._record_sync_completion(
                    sync_id, 'success', 
                    result['files_processed'], 
                    result['files_indexed'],
                    clone_result.get('commit_sha'),
                    repository['default_branch']
                )
                
                duration = time.time() - start_time
                
                log_sync_event(
                    self.logger, 'sync_completed', repo_id,
                    {
                        'files_processed': result['files_processed'],
                        'files_indexed': result['files_indexed'],
                        'duration': duration
                    }
                )
                
                return {
                    'status': 'success',
                    'message': f'Repository {repo_name} synced successfully',
                    'files_processed': result['files_processed'],
                    'files_indexed': result['files_indexed'],
                    'duration_seconds': duration
                }
                
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"❌ Repository sync failed for {repo_name}: {error_msg}")
            
            # Record sync failure
            self._record_sync_completion(sync_id, 'failed', 0, 0, error_message=error_msg)
            
            log_sync_event(
                self.logger, 'sync_failed', repo_id,
                {'error': error_msg, 'duration': time.time() - start_time}
            )
            
            return {
                'status': 'error',
                'error': error_msg,
                'files_processed': 0,
                'files_indexed': 0
            }

    def _clone_repository(self, repository: Dict[str, Any], clone_path: str, token: str) -> Dict[str, Any]:
        """Clone repository using git"""
        try:
            clone_url = repository['clone_url']

            # Insert token into clone URL for authentication
            if clone_url.startswith('https://github.com/'):
                auth_url = clone_url.replace('https://github.com/', f'https://{token}@github.com/')
            else:
                auth_url = clone_url

            # Git clone command with shallow clone for performance
            cmd = [
                'git', 'clone',
                '--depth', str(self.config.CLONE_DEPTH),
                '--branch', repository['default_branch'],
                auth_url,
                clone_path
            ]

            self.logger.debug(f"Cloning repository: {repository['name']} (branch: {repository['default_branch']})")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout for clone
            )

            # If the default branch doesn't exist, try cloning without specifying a branch
            if result.returncode != 0 and 'not found in upstream' in result.stderr:
                self.logger.warning(f"Default branch '{repository['default_branch']}' not found, trying without branch specification")

                # Try again without specifying branch (let Git use the actual default)
                cmd_fallback = [
                    'git', 'clone',
                    '--depth', str(self.config.CLONE_DEPTH),
                    auth_url,
                    clone_path
                ]

                result = subprocess.run(
                    cmd_fallback,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minute timeout for clone
                )

            if result.returncode != 0:
                return {
                    'success': False,
                    'error': f"Git clone failed: {result.stderr}"
                }

            # Get commit SHA
            commit_sha = None
            try:
                sha_result = subprocess.run(
                    ['git', 'rev-parse', 'HEAD'],
                    cwd=clone_path,
                    capture_output=True,
                    text=True
                )
                if sha_result.returncode == 0:
                    commit_sha = sha_result.stdout.strip()
            except Exception:
                pass  # Not critical if we can't get SHA

            return {
                'success': True,
                'commit_sha': commit_sha
            }

        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': "Git clone timed out"
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Clone failed: {str(e)}"
            }

    def _process_repository_files(self, repository: Dict[str, Any], repo_path: str,
                                 job_id: str = None, cancel_event: threading.Event = None) -> Dict[str, Any]:
        """Process all files in the repository"""
        repo_id = repository['id']
        files_processed = 0
        files_indexed = 0

        try:
            # Get all files in repository
            all_files = []
            for root, dirs, files in os.walk(repo_path):
                # Skip .git directory
                if '.git' in dirs:
                    dirs.remove('.git')

                for file in files:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, repo_path)

                    # Check if file should be processed
                    if self.config.is_supported_file(file):
                        all_files.append({
                            'absolute_path': file_path,
                            'relative_path': rel_path,
                            'filename': file
                        })

            if not all_files:
                self.logger.info(f"No supported files found in repository {repository['name']}")
                return {
                    'status': 'success',
                    'files_processed': 0,
                    'files_indexed': 0
                }

            self.logger.info(f"Processing {len(all_files)} files from repository {repository['name']}")

            # Update job progress if job_id provided
            if job_id:
                self.job_instance_service.update_job_progress(
                    job_id, 0, len(all_files), 0
                )

            # Create progress logger
            progress_logger = ProgressLogger(self.logger, f"Repository {repository['name']}", len(all_files))

            # Process files in batches
            batch_size = self.config.BATCH_SIZE
            for i in range(0, len(all_files), batch_size):
                # Check for cancellation
                if cancel_event and cancel_event.is_set():
                    return {'status': 'cancelled', 'message': 'File processing cancelled by user'}

                batch = all_files[i:i + batch_size]
                batch_result = self._process_file_batch(repository, batch, repo_path)

                files_processed += batch_result['files_processed']
                files_indexed += batch_result['files_indexed']

                # Update progress
                progress_logger.update(
                    len(batch),
                    {'current_item': batch[-1]['relative_path']}
                )

                # Update job progress if job_id provided
                if job_id:
                    progress_pct = int((files_processed / len(all_files)) * 100)
                    self.job_instance_service.update_job_progress(
                        job_id, progress_pct, len(all_files), files_processed
                    )

            progress_logger.complete({
                'success_count': files_indexed,
                'error_count': files_processed - files_indexed
            })

            return {
                'status': 'success',
                'files_processed': files_processed,
                'files_indexed': files_indexed
            }

        except Exception as e:
            self.logger.error(f"File processing failed for repository {repository['name']}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'files_processed': files_processed,
                'files_indexed': files_indexed
            }

    def _process_file_batch(self, repository: Dict[str, Any], files: List[Dict[str, Any]],
                           repo_path: str) -> Dict[str, Any]:
        """Process a batch of files"""
        files_processed = 0
        files_indexed = 0

        for file_info in files:
            try:
                result = self._process_single_file(repository, file_info, repo_path)
                files_processed += 1
                if result['indexed']:
                    files_indexed += 1

            except Exception as e:
                self.logger.warning(f"Failed to process file {file_info['relative_path']}: {str(e)}")
                files_processed += 1

        return {
            'files_processed': files_processed,
            'files_indexed': files_indexed
        }

    def _process_single_file(self, repository: Dict[str, Any], file_info: Dict[str, Any],
                            repo_path: str) -> Dict[str, Any]:
        """Process a single file"""
        file_path = file_info['absolute_path']
        rel_path = file_info['relative_path']

        try:
            # Check file size
            file_size = os.path.getsize(file_path)
            max_size_bytes = self.config.MAX_FILE_SIZE_MB * 1024 * 1024

            if file_size > max_size_bytes:
                self.logger.debug(f"Skipping large file: {rel_path} ({file_size} bytes)")
                return {'indexed': False, 'reason': 'file_too_large'}

            # Read file content
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                # Try with different encoding
                try:
                    with open(file_path, 'r', encoding='latin-1') as f:
                        content = f.read()
                except Exception:
                    self.logger.debug(f"Skipping binary file: {rel_path}")
                    return {'indexed': False, 'reason': 'binary_file'}

            # Send to embedding service
            result = self._send_to_embedding_service(repository, rel_path, content)

            if result['success']:
                return {'indexed': True}
            else:
                self.logger.warning(f"Failed to index file {rel_path}: {result['error']}")
                return {'indexed': False, 'reason': 'embedding_failed'}

        except Exception as e:
            self.logger.warning(f"Error processing file {rel_path}: {str(e)}")
            return {'indexed': False, 'reason': 'processing_error'}

    def _send_to_embedding_service(self, repository: Dict[str, Any], file_path: str,
                                  content: str) -> Dict[str, Any]:
        """Send file content to embedding service"""
        try:
            payload = {
                'documents': [{
                    'id': f"{repository['id']}:{file_path}",
                    'content': content,
                    'metadata': {
                        'repository_id': repository['id'],
                        'repository_name': repository['name'],
                        'file_path': file_path,
                        'source_type': 'github_repository',
                        'language': repository.get('language'),
                        'branch': repository['default_branch']
                    }
                }]
            }

            response = requests.post(
                f"{self.config.EMBEDDING_SERVICE_URL}/embed/documents",
                json=payload,
                timeout=self.config.REQUEST_TIMEOUT
            )

            response.raise_for_status()
            return {'success': True}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _record_sync_start(self, repository_id: str) -> int:
        """Record sync start in database"""
        with sqlite3.connect(self.config.DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO sync_history (repository_id, sync_started_at, status)
                VALUES (?, CURRENT_TIMESTAMP, 'running')
            ''', (repository_id,))
            conn.commit()
            return cursor.lastrowid

    def _record_sync_completion(self, sync_id: int, status: str, files_processed: int,
                               files_indexed: int, commit_sha: str = None,
                               branch: str = None, error_message: str = None):
        """Record sync completion in database"""
        with sqlite3.connect(self.config.DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE sync_history
                SET sync_completed_at = CURRENT_TIMESTAMP,
                    status = ?,
                    files_processed = ?,
                    files_indexed = ?,
                    commit_sha = ?,
                    branch = ?,
                    error_message = ?
                WHERE id = ?
            ''', (status, files_processed, files_indexed, commit_sha, branch, error_message, sync_id))
            conn.commit()

    def get_sync_history(self, repository_id: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get sync history"""
        with sqlite3.connect(self.config.DB_PATH) as conn:
            cursor = conn.cursor()

            if repository_id:
                cursor.execute('''
                    SELECT id, repository_id, sync_started_at, sync_completed_at,
                           status, files_processed, files_indexed, error_message,
                           commit_sha, branch, created_at
                    FROM sync_history
                    WHERE repository_id = ?
                    ORDER BY sync_started_at DESC
                    LIMIT ?
                ''', (repository_id, limit))
            else:
                cursor.execute('''
                    SELECT id, repository_id, sync_started_at, sync_completed_at,
                           status, files_processed, files_indexed, error_message,
                           commit_sha, branch, created_at
                    FROM sync_history
                    ORDER BY sync_started_at DESC
                    LIMIT ?
                ''', (limit,))

            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
