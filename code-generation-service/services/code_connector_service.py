"""
Code Connector Service
Handles connections to various code repositories (Git, local filesystem, GitHub, GitLab)
"""
import os
import shutil
import tempfile
import subprocess
import requests
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Optional
from pathlib import Path
import fnmatch
from urllib.parse import urlparse

from config.settings import Config
from utils.logger import setup_logger


class CodeConnectorService:
    """Service for connecting to and managing code repositories"""
    
    def __init__(self):
        self.logger = setup_logger('code-connector')
        self.temp_dir = Config.TEMP_REPO_DIR
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def connect_repository(self, repo_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Connect to a code repository and return connection info
        
        Args:
            repo_config: Repository configuration containing:
                - type: 'git', 'local', 'github', 'gitlab'
                - url: Repository URL (for git/github/gitlab)
                - path: Local path (for local type)
                - branch: Branch name (optional, default: main/master)
                - credentials: Authentication info (optional)
        
        Returns:
            Dictionary with connection status and repository info
        """
        try:
            repo_type = repo_config.get('type', '').lower()
            
            if repo_type not in Config.SUPPORTED_REPO_TYPES:
                raise ValueError(f"Unsupported repository type: {repo_type}")
            
            self.logger.info(f"Connecting to {repo_type} repository")
            
            if repo_type == 'local':
                return self._connect_local_repository(repo_config)
            elif repo_type in ['git', 'github', 'gitlab']:
                return self._connect_git_repository(repo_config)
            else:
                raise ValueError(f"Repository type {repo_type} not implemented")
                
        except Exception as e:
            self.logger.error(f"Failed to connect to repository: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "repository_id": None
            }
    
    def _connect_local_repository(self, repo_config: Dict[str, Any]) -> Dict[str, Any]:
        """Connect to a local filesystem repository"""
        local_path = repo_config.get('path')
        
        if not local_path:
            raise ValueError("Local path is required for local repository type")
        
        if not os.path.exists(local_path):
            raise ValueError(f"Local path does not exist: {local_path}")
        
        if not os.path.isdir(local_path):
            raise ValueError(f"Local path is not a directory: {local_path}")
        
        # Generate repository ID
        repo_id = f"local_{hash(local_path)}"
        
        # Get repository info
        repo_info = self._analyze_repository_structure(local_path)
        
        return {
            "status": "success",
            "repository_id": repo_id,
            "type": "local",
            "path": local_path,
            "info": repo_info
        }
    
    def _connect_git_repository(self, repo_config: Dict[str, Any]) -> Dict[str, Any]:
        """Connect to a Git repository with authentication support"""
        repo_url = repo_config.get('url')
        branch = repo_config.get('branch', 'main')
        credentials = repo_config.get('credentials', {})

        if not repo_url:
            raise ValueError("Repository URL is required for Git repositories")

        # Validate repository URL
        if not self._validate_repository_url(repo_url):
            raise ValueError(f"Invalid repository URL: {repo_url}")

        # Generate repository ID from URL
        parsed_url = urlparse(repo_url)
        repo_name = os.path.basename(parsed_url.path).replace('.git', '')
        repo_id = f"git_{hash(repo_url)}_{repo_name}"

        # Create temporary directory for cloning
        clone_path = os.path.join(self.temp_dir, repo_id)

        # Remove existing clone if it exists
        if os.path.exists(clone_path):
            shutil.rmtree(clone_path)

        try:
            # Clone repository with authentication
            self.logger.info(f"Cloning repository: {repo_url}")
            authenticated_url = self._prepare_authenticated_url(repo_url, credentials)

            clone_cmd = ['git', 'clone', '--depth', '1']
            if branch != 'main':
                clone_cmd.extend(['--branch', branch])
            clone_cmd.extend([authenticated_url, clone_path])

            # Set up environment for authentication
            env = os.environ.copy()

            # Handle SSH authentication
            if repo_url.startswith('git@') or repo_url.startswith('ssh://'):
                # SSH authentication - set up SSH key if provided
                ssh_key_path = credentials.get('ssh_key_path')
                ssh_key_content = credentials.get('ssh_key_content')

                if ssh_key_content:
                    # Create temporary SSH key file
                    ssh_key_file = os.path.join(self.temp_dir, f"{repo_id}_ssh_key")
                    with open(ssh_key_file, 'w') as f:
                        f.write(ssh_key_content)
                    os.chmod(ssh_key_file, 0o600)  # Set proper permissions
                    env['GIT_SSH_COMMAND'] = f'ssh -i {ssh_key_file} -o StrictHostKeyChecking=no'
                elif ssh_key_path and os.path.exists(ssh_key_path):
                    # Use existing SSH key file
                    env['GIT_SSH_COMMAND'] = f'ssh -i {ssh_key_path} -o StrictHostKeyChecking=no'
                else:
                    # Use default SSH key (assumes SSH agent or default key is set up)
                    env['GIT_SSH_COMMAND'] = 'ssh -o StrictHostKeyChecking=no'
            elif credentials.get('token'):
                # HTTPS token authentication
                env['GIT_ASKPASS'] = 'echo'
                env['GIT_USERNAME'] = credentials.get('username', 'token')
                env['GIT_PASSWORD'] = credentials.get('token')

            result = subprocess.run(
                clone_cmd,
                capture_output=True,
                text=True,
                timeout=Config.ANALYSIS_TIMEOUT,
                env=env
            )

            if result.returncode != 0:
                # Try with master branch if main failed
                if branch == 'main':
                    self.logger.info("Retrying with master branch")
                    clone_cmd = ['git', 'clone', '--depth', '1', '--branch', 'master', authenticated_url, clone_path]
                    result = subprocess.run(
                        clone_cmd,
                        capture_output=True,
                        text=True,
                        timeout=Config.ANALYSIS_TIMEOUT,
                        env=env
                    )

                if result.returncode != 0:
                    raise Exception(f"Git clone failed: {result.stderr}")

            # Validate successful clone
            if not self._validate_repository_clone(clone_path):
                raise Exception("Repository clone validation failed")

            # Check repository size
            repo_size = self._get_directory_size(clone_path)
            if repo_size > Config.MAX_REPO_SIZE_MB * 1024 * 1024:
                shutil.rmtree(clone_path)
                raise ValueError(f"Repository size ({repo_size / 1024 / 1024:.1f}MB) exceeds limit ({Config.MAX_REPO_SIZE_MB}MB)")

            # Analyze repository structure
            repo_info = self._analyze_repository_structure(clone_path)

            # Validate that repository was properly indexed
            if not self._validate_repository_indexing(repo_info):
                raise Exception("Repository indexing validation failed")

            # Store repository content in RAG system (optional)
            try:
                rag_result = self._store_repository_in_rag(repo_id, clone_path, repo_info)
                if rag_result.get('success', False):
                    self.logger.info(f"Successfully stored repository in RAG system: {rag_result.get('documents_stored', 0)} documents")
                else:
                    self.logger.warning(f"Failed to store repository in RAG system: {rag_result.get('error', 'Unknown error')}")
            except Exception as e:
                self.logger.warning(f"RAG integration failed (non-critical): {str(e)}")
                # Don't fail the connection, RAG is optional
            
            return {
                "status": "success",
                "repository_id": repo_id,
                "type": "git",
                "url": repo_url,
                "branch": branch,
                "local_path": clone_path,
                "size_mb": repo_size / 1024 / 1024,
                "info": repo_info
            }
            
        except Exception as e:
            # Clean up on failure
            if os.path.exists(clone_path):
                shutil.rmtree(clone_path)
            raise e
    
    def _analyze_repository_structure(self, repo_path: str) -> Dict[str, Any]:
        """Analyze repository structure and extract metadata"""
        try:
            structure = {
                "languages": {},
                "total_files": 0,
                "total_lines": 0,
                "directories": [],
                "main_files": [],
                "config_files": []
            }
            
            for root, dirs, files in os.walk(repo_path):
                # Skip ignored directories
                dirs[:] = [d for d in dirs if not self._should_ignore(d)]
                
                rel_root = os.path.relpath(root, repo_path)
                if rel_root != '.':
                    structure["directories"].append(rel_root)
                
                for file in files:
                    if self._should_ignore(file):
                        continue
                    
                    file_path = os.path.join(root, file)
                    rel_file_path = os.path.relpath(file_path, repo_path)
                    
                    # Check file size
                    try:
                        file_size = os.path.getsize(file_path)
                        if file_size > Config.MAX_FILE_SIZE_KB * 1024:
                            continue
                    except OSError:
                        continue
                    
                    # Determine language
                    _, ext = os.path.splitext(file)
                    language = Config.get_language_from_extension(ext)
                    
                    if language != 'unknown':
                        if language not in structure["languages"]:
                            structure["languages"][language] = {
                                "files": 0,
                                "lines": 0
                            }
                        
                        structure["languages"][language]["files"] += 1
                        structure["total_files"] += 1
                        
                        # Count lines
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                lines = sum(1 for _ in f)
                                structure["languages"][language]["lines"] += lines
                                structure["total_lines"] += lines
                        except (OSError, UnicodeDecodeError):
                            pass
                    
                    # Identify important files
                    if file.lower() in ['readme.md', 'readme.txt', 'readme.rst', 'readme']:
                        structure["main_files"].append(rel_file_path)
                    elif file.lower() in ['package.json', 'requirements.txt', 'pom.xml', 'cargo.toml', 'go.mod', 'composer.json']:
                        structure["config_files"].append(rel_file_path)
            
            return structure
            
        except Exception as e:
            self.logger.error(f"Failed to analyze repository structure: {str(e)}")
            return {"error": str(e)}
    
    def _should_ignore(self, name: str) -> bool:
        """Check if file/directory should be ignored"""
        for pattern in Config.IGNORE_PATTERNS:
            if fnmatch.fnmatch(name, pattern):
                return True
        return False
    
    def _get_directory_size(self, path: str) -> int:
        """Get total size of directory in bytes"""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(file_path)
                except OSError:
                    pass
        return total_size
    
    def get_repository_files(self, repository_id: str, language: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get list of files from a connected repository
        
        Args:
            repository_id: Repository identifier
            language: Filter by programming language (optional)
        
        Returns:
            List of file information dictionaries
        """
        try:
            # This would typically query a database or cache
            # For now, we'll implement a simple file system lookup
            repo_path = self._get_repository_path(repository_id)
            
            if not repo_path or not os.path.exists(repo_path):
                raise ValueError(f"Repository not found: {repository_id}")
            
            files = []
            for root, dirs, filenames in os.walk(repo_path):
                dirs[:] = [d for d in dirs if not self._should_ignore(d)]
                
                for filename in filenames:
                    if self._should_ignore(filename):
                        continue
                    
                    file_path = os.path.join(root, filename)
                    rel_path = os.path.relpath(file_path, repo_path)
                    
                    _, ext = os.path.splitext(filename)
                    file_language = Config.get_language_from_extension(ext)
                    
                    if language and file_language != language:
                        continue
                    
                    if Config.is_supported_file(filename):
                        files.append({
                            "path": rel_path,
                            "name": filename,
                            "language": file_language,
                            "size": os.path.getsize(file_path)
                        })
            
            return files
            
        except Exception as e:
            self.logger.error(f"Failed to get repository files: {str(e)}")
            return []

    def _validate_repository_url(self, url: str) -> bool:
        """Validate repository URL format"""
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False

            # Check for common Git hosting services
            valid_hosts = ['github.com', 'gitlab.com', 'bitbucket.org']
            if parsed.netloc.lower() in valid_hosts:
                return True

            # Allow other hosts if they look like Git URLs
            return url.endswith('.git') or '/git/' in url.lower()
        except Exception:
            return False

    def _prepare_authenticated_url(self, url: str, credentials: Dict[str, Any]) -> str:
        """Prepare URL with authentication credentials"""
        if not credentials:
            return url

        # Handle SSH URLs - no modification needed, authentication handled by SSH keys
        if url.startswith('git@') or url.startswith('ssh://'):
            return url

        username = credentials.get('username')
        token = credentials.get('token')
        password = credentials.get('password')

        if token:
            # Use token authentication (GitHub, GitLab)
            parsed = urlparse(url)
            if username:
                auth_url = f"{parsed.scheme}://{username}:{token}@{parsed.netloc}{parsed.path}"
            else:
                auth_url = f"{parsed.scheme}://token:{token}@{parsed.netloc}{parsed.path}"
            return auth_url
        elif username and password:
            # Use username/password authentication
            parsed = urlparse(url)
            auth_url = f"{parsed.scheme}://{username}:{password}@{parsed.netloc}{parsed.path}"
            return auth_url

        return url

    def _validate_repository_clone(self, clone_path: str) -> bool:
        """Validate that repository was successfully cloned"""
        try:
            # Check if .git directory exists
            git_dir = os.path.join(clone_path, '.git')
            if not os.path.exists(git_dir):
                self.logger.error("No .git directory found in cloned repository")
                return False

            # Check if there are any files
            files = list(Path(clone_path).rglob('*'))
            if len(files) < 2:  # At least .git and one other file
                self.logger.error("Repository appears to be empty")
                return False

            self.logger.info(f"Repository clone validated: {len(files)} files found")
            return True

        except Exception as e:
            self.logger.error(f"Repository clone validation failed: {str(e)}")
            return False

    def _validate_repository_indexing(self, repo_info: Dict[str, Any]) -> bool:
        """Validate that repository was properly indexed"""
        try:
            # Check if we found any code files
            languages = repo_info.get('languages', {})
            if not languages:
                self.logger.warning("No programming languages detected in repository")
                return True  # Still valid, might be documentation-only repo

            # Check if we have reasonable file counts
            total_files = repo_info.get('total_files', 0)
            if total_files == 0:
                self.logger.error("No files indexed in repository")
                return False

            # Check if we have main files or directories
            main_files = repo_info.get('main_files', [])
            directories = repo_info.get('directories', [])

            if not main_files and not directories:
                self.logger.error("No main files or directories found")
                return False

            self.logger.info(f"Repository indexing validated: {total_files} files, {len(languages)} languages")
            return True

        except Exception as e:
            self.logger.error(f"Repository indexing validation failed: {str(e)}")
            return False

    def _store_repository_in_rag(self, repo_id: str, repo_path: str, repo_info: Dict[str, Any]) -> Dict[str, Any]:
        """Store repository content in RAG system for future reference using threading"""
        try:
            # Get embedding service URL
            embedding_service_url = Config.get_embedding_service_url()
            if not embedding_service_url:
                return {"success": False, "error": "Embedding service not configured"}

            # Get all files in the repository (not just important ones)
            all_files = self._get_all_repository_files(repo_path)

            if not all_files:
                return {"success": False, "error": "No files found in repository"}

            # Threading configuration
            max_threads = Config.RAG_SYNC_THREADS
            batch_size = Config.RAG_SYNC_BATCH_SIZE

            # Thread-safe counters and collections
            processed_files = 0
            failed_files = 0
            document_ids = []
            lock = threading.Lock()

            self.logger.info(f"Processing {len(all_files)} files for repository {repo_id} using {max_threads} threads")
            start_time = time.time()

            def process_file_batch(file_batch: List[Dict[str, Any]]) -> Dict[str, Any]:
                """Process a batch of files in a single thread with true batching"""
                batch_processed = 0
                batch_failed = 0
                batch_document_ids = []

                # Prepare all documents in the batch for a single request
                documents = []

                for file_info in file_batch:
                    try:
                        file_path = os.path.join(repo_path, file_info['path'])

                        # Skip large files
                        if os.path.getsize(file_path) > Config.MAX_FILE_SIZE_KB * 1024:
                            self.logger.debug(f"Skipping large file: {file_info['path']}")
                            continue

                        # Read file content
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()

                        # Skip empty files
                        if not content.strip():
                            self.logger.debug(f"Skipping empty file: {file_info['path']}")
                            continue

                        # Create document for batch processing
                        file_content = f"File: {file_info['path']}\n" + \
                                      f"Language: {file_info['language']}\n" + \
                                      f"Repository: {repo_id}\n" + \
                                      f"Content:\n{content}"

                        # Prepare metadata for batch processing
                        metadata = {
                            "type": "code_file",
                            "repository_id": repo_id,
                            "file_path": file_info['path'],
                            "language": file_info['language'],
                            "source": "code_connector",
                            "file_size": len(content)
                        }

                        # Add to batch documents
                        documents.append({
                            "content": file_content,
                            "metadata": metadata
                        })

                    except Exception as e:
                        self.logger.warning(f"Failed to read file {file_info['path']}: {str(e)}")
                        batch_failed += 1
                        continue

                # Send entire batch in a single request
                if documents:
                    try:
                        response = requests.post(
                            f"{embedding_service_url}/embed/documents",
                            json={"documents": documents},
                            timeout=120,  # Increased timeout for batch processing
                            headers={'Content-Type': 'application/json'}
                        )

                        if response.status_code == 200:
                            result = response.json()
                            batch_processed = len(documents)
                            if result.get("document_ids"):
                                batch_document_ids.extend(result["document_ids"])
                            self.logger.debug(f"Successfully processed batch of {len(documents)} files")
                        else:
                            self.logger.warning(f"Failed to process batch of {len(documents)} files: {response.status_code} - {response.text}")
                            batch_failed += len(documents)

                    except Exception as e:
                        self.logger.warning(f"Failed to send batch of {len(documents)} files: {str(e)}")
                        batch_failed += len(documents)

                return {
                    "processed": batch_processed,
                    "failed": batch_failed,
                    "document_ids": batch_document_ids
                }

            # Split files into batches for threading
            file_batches = []
            for i in range(0, len(all_files), batch_size):
                file_batches.append(all_files[i:i + batch_size])

            # Process files using ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=max_threads) as executor:
                # Submit all batches to the thread pool
                future_to_batch = {executor.submit(process_file_batch, batch): batch for batch in file_batches}

                # Process completed futures
                for future in as_completed(future_to_batch):
                    try:
                        result = future.result()

                        # Thread-safe update of counters
                        with lock:
                            processed_files += result["processed"]
                            failed_files += result["failed"]
                            document_ids.extend(result["document_ids"])

                            # Log progress every 50 files
                            if processed_files % 50 == 0:
                                elapsed_time = time.time() - start_time
                                rate = processed_files / elapsed_time if elapsed_time > 0 else 0
                                self.logger.info(f"Processed {processed_files}/{len(all_files)} files ({rate:.1f} files/sec)")

                    except Exception as e:
                        self.logger.error(f"Thread execution failed: {str(e)}")
                        with lock:
                            failed_files += len(future_to_batch[future])

            # Store repository metadata as a separate document
            try:
                metadata_content = f"Repository: {repo_id}\n" + \
                                 f"Languages: {', '.join(repo_info.get('languages', {}).keys())}\n" + \
                                 f"Total files: {repo_info.get('total_files', 0)}\n" + \
                                 f"Main files: {', '.join(repo_info.get('main_files', []))}\n" + \
                                 f"Directories: {', '.join(repo_info.get('directories', []))}"

                metadata_doc = [{
                    "content": metadata_content,
                    "metadata": {
                        "type": "repository_metadata",
                        "repository_id": repo_id,
                        "source": "code_connector"
                    }
                }]

                response = requests.post(
                    f"{embedding_service_url}/embed/documents",
                    json={"documents": metadata_doc},
                    timeout=30,
                    headers={'Content-Type': 'application/json'}
                )

                if response.status_code == 200:
                    result = response.json()
                    if result.get("document_ids"):
                        document_ids.extend(result["document_ids"])

            except Exception as e:
                self.logger.warning(f"Failed to store repository metadata: {str(e)}")

            elapsed_time = time.time() - start_time
            avg_rate = processed_files / elapsed_time if elapsed_time > 0 else 0

            self.logger.info(f"Repository RAG storage complete: {processed_files} files processed, {failed_files} failed, "
                           f"{len(document_ids)} documents created in {elapsed_time:.1f}s ({avg_rate:.1f} files/sec)")

            return {
                "success": True,
                "files_processed": processed_files,
                "files_failed": failed_files,
                "documents_stored": len(document_ids),
                "document_ids": document_ids,
                "processing_time_seconds": elapsed_time,
                "processing_rate_files_per_second": avg_rate
            }

        except Exception as e:
            self.logger.error(f"Failed to store repository in RAG system: {str(e)}")
            return {"success": False, "error": str(e)}

    def _get_important_files(self, repo_path: str, repo_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get list of important files to include in RAG system"""
        important_files = []

        # Priority order for file types
        priority_files = [
            'README.md', 'README.rst', 'README.txt', 'README',
            'package.json', 'requirements.txt', 'setup.py', 'Cargo.toml', 'go.mod',
            'main.py', 'index.js', 'app.py', 'server.js', 'main.go', 'main.rs'
        ]

        # Get main files (these are actual file paths)
        main_files = repo_info.get('main_files', [])
        for file_path in main_files:
            important_files.append({
                'path': file_path,
                'language': 'markdown' if file_path.endswith('.md') else 'text',
                'priority': 0 if os.path.basename(file_path) in priority_files else 10
            })

        # Get config files (these are actual file paths)
        config_files = repo_info.get('config_files', [])
        for file_path in config_files:
            filename = os.path.basename(file_path)
            if filename in priority_files:
                important_files.append({
                    'path': file_path,
                    'language': self._detect_file_language(file_path),
                    'priority': priority_files.index(filename)
                })

        # Add some sample files from each language (scan directory for actual files)
        try:
            for lang, lang_info in repo_info.get('languages', {}).items():
                if lang_info.get('files', 0) > 0:  # Only if language has files
                    sample_files = self._find_sample_files_for_language(repo_path, lang, limit=2)
                    for file_path in sample_files:
                        important_files.append({
                            'path': file_path,
                            'language': lang,
                            'priority': 50  # Medium priority for sample files
                        })
        except Exception as e:
            self.logger.warning(f"Failed to get sample files: {str(e)}")

        # Sort by priority and return unique files
        seen_paths = set()
        unique_files = []
        for file_info in sorted(important_files, key=lambda x: x['priority']):
            if file_info['path'] not in seen_paths:
                seen_paths.add(file_info['path'])
                unique_files.append(file_info)

        return unique_files

    def _detect_file_language(self, file_path: str) -> str:
        """Detect programming language from file extension"""
        ext = os.path.splitext(file_path)[1].lower()
        ext_map = {
            '.py': 'python', '.js': 'javascript', '.ts': 'typescript',
            '.java': 'java', '.go': 'go', '.rs': 'rust', '.cpp': 'cpp',
            '.c': 'c', '.cs': 'csharp', '.php': 'php', '.rb': 'ruby',
            '.swift': 'swift', '.kt': 'kotlin', '.json': 'json',
            '.yaml': 'yaml', '.yml': 'yaml', '.toml': 'toml',
            '.md': 'markdown', '.txt': 'text'
        }
        return ext_map.get(ext, 'text')

    def _find_sample_files_for_language(self, repo_path: str, language: str, limit: int = 2) -> List[str]:
        """Find sample files for a specific language in the repository"""
        sample_files = []

        # Language extension mapping
        lang_extensions = {
            'python': ['.py'],
            'javascript': ['.js'],
            'typescript': ['.ts'],
            'java': ['.java'],
            'go': ['.go'],
            'rust': ['.rs'],
            'cpp': ['.cpp', '.cc', '.cxx'],
            'c': ['.c'],
            'csharp': ['.cs'],
            'php': ['.php'],
            'ruby': ['.rb'],
            'swift': ['.swift'],
            'kotlin': ['.kt']
        }

        extensions = lang_extensions.get(language, [])
        if not extensions:
            return sample_files

        try:
            # Walk through repository directory
            for root, dirs, files in os.walk(repo_path):
                # Skip hidden directories and common non-source directories
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'target', 'build']]

                for file in files:
                    if len(sample_files) >= limit:
                        break

                    file_ext = os.path.splitext(file)[1].lower()
                    if file_ext in extensions:
                        # Get relative path from repo root
                        full_path = os.path.join(root, file)
                        rel_path = os.path.relpath(full_path, repo_path)

                        # Skip test files and very large files
                        if not ('test' in rel_path.lower() or file.startswith('test_')):
                            try:
                                if os.path.getsize(full_path) < Config.MAX_FILE_SIZE_KB * 1024:
                                    sample_files.append(rel_path)
                            except OSError:
                                continue

                if len(sample_files) >= limit:
                    break

        except Exception as e:
            self.logger.warning(f"Failed to find sample files for {language}: {str(e)}")

        return sample_files

    def _get_all_repository_files(self, repo_path: str) -> List[Dict[str, Any]]:
        """Get all code files in the repository for RAG processing"""
        try:
            all_files = []

            for root, dirs, files in os.walk(repo_path):
                # Skip ignored directories
                dirs[:] = [d for d in dirs if not self._should_ignore(d)]

                for filename in files:
                    if self._should_ignore(filename):
                        continue

                    file_path = os.path.join(root, filename)
                    rel_path = os.path.relpath(file_path, repo_path)

                    # Skip files that are too large
                    try:
                        file_size = os.path.getsize(file_path)
                        if file_size > Config.MAX_FILE_SIZE_KB * 1024:
                            continue
                    except OSError:
                        continue

                    # Get file extension and language
                    _, ext = os.path.splitext(filename)
                    file_language = Config.get_language_from_extension(ext)

                    # Include all supported files (not just code files)
                    if Config.is_supported_file(filename) or ext.lower() in ['.md', '.txt', '.rst', '.json', '.yaml', '.yml', '.xml']:
                        all_files.append({
                            "path": rel_path,
                            "name": filename,
                            "language": file_language or 'text',
                            "size": file_size,
                            "extension": ext.lower()
                        })

            self.logger.info(f"Found {len(all_files)} files for RAG processing")
            return all_files

        except Exception as e:
            self.logger.error(f"Failed to get all repository files: {str(e)}")
            return []

    def _get_repository_path(self, repository_id: str) -> Optional[str]:
        """Get local path for repository ID"""
        # This is a simplified implementation
        # In a real system, you'd store repository metadata in a database
        if repository_id.startswith('local_'):
            # For local repos, we'd need to store the mapping
            return None
        elif repository_id.startswith('git_'):
            return os.path.join(self.temp_dir, repository_id)
        return None
    
    def cleanup_repository(self, repository_id: str) -> bool:
        """Clean up temporary repository files"""
        try:
            repo_path = self._get_repository_path(repository_id)
            if repo_path and os.path.exists(repo_path) and repo_path.startswith(self.temp_dir):
                shutil.rmtree(repo_path)
                self.logger.info(f"Cleaned up repository: {repository_id}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to cleanup repository {repository_id}: {str(e)}")
            return False
