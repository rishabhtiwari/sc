"""
Code Controller
Handles API endpoints for code generation, repository connection, and analysis
"""
import time
from flask import request, jsonify
from typing import Dict, Tuple, Any

from services.code_connector_service import CodeConnectorService
from services.code_analysis_service import CodeAnalysisService
from services.code_generation_service import CodeGenerationService
from services.github_oauth_service import GitHubOAuthService
from utils.logger import setup_logger


class CodeController:
    """Controller for handling code generation service requests"""
    
    def __init__(self):
        self.code_connector = CodeConnectorService()
        self.code_analysis = CodeAnalysisService()
        self.code_generation = CodeGenerationService()
        self.github_oauth = GitHubOAuthService()
        self.logger = setup_logger('code-controller')
    
    def connect_repository(self) -> Tuple[Dict[str, Any], int]:
        """
        Connect to a code repository
        
        Expected JSON payload:
        {
            "type": "git|local|github|gitlab",
            "url": "repository URL (for git/github/gitlab)",
            "path": "local path (for local type)",
            "branch": "branch name (optional)",
            "session_id": "GitHub OAuth session ID (optional)",
            "credentials": {
                "username": "username",
                "token": "access_token"
            }
        }
        """
        try:
            if not request.is_json:
                return self.error_response("Request must be JSON", 400)
            
            data = request.get_json()
            
            # Validate required fields
            repo_type = data.get('type', '').lower()
            if not repo_type:
                return self.error_response("Repository type is required", 400)
            
            if repo_type == 'local' and not data.get('path'):
                return self.error_response("Local path is required for local repositories", 400)
            
            if repo_type in ['git', 'github', 'gitlab'] and not data.get('url'):
                return self.error_response("Repository URL is required", 400)
            
            self.logger.info(f"Connecting to {repo_type} repository")

            # Handle GitHub OAuth session
            session_id = data.get('session_id')
            if session_id:
                access_token = self.github_oauth.get_access_token(session_id)
                if access_token:
                    # Add GitHub token to credentials
                    if 'credentials' not in data:
                        data['credentials'] = {}
                    data['credentials']['token'] = access_token
                    self.logger.info("Using GitHub OAuth token for repository access")
                else:
                    return self.error_response("Invalid or expired session", 401)

            # Connect to repository
            result = self.code_connector.connect_repository(data)
            
            if result.get('status') == 'success':
                return self.success_response(result), 200
            else:
                return self.error_response(result.get('error', 'Connection failed'), 500)
                
        except Exception as e:
            self.logger.error(f"Error in connect_repository: {str(e)}")
            return self.error_response(f"Repository connection failed: {str(e)}", 500)
    
    def analyze_repository(self) -> Tuple[Dict[str, Any], int]:
        """
        Analyze a connected repository
        
        Expected JSON payload:
        {
            "repository_id": "repository identifier",
            "language": "programming language (optional)"
        }
        """
        try:
            if not request.is_json:
                return self.error_response("Request must be JSON", 400)
            
            data = request.get_json()
            repository_id = data.get('repository_id')
            language = data.get('language')
            
            if not repository_id:
                return self.error_response("Repository ID is required", 400)
            
            self.logger.info(f"Analyzing repository: {repository_id}")
            
            # Get repository path
            repo_path = self.code_connector._get_repository_path(repository_id)
            if not repo_path:
                return self.error_response("Repository not found", 404)
            
            # Analyze repository
            analysis = self.code_analysis.analyze_codebase(repo_path, language)
            
            if 'error' in analysis:
                return self.error_response(analysis['error'], 500)
            
            return self.success_response(analysis), 200
            
        except Exception as e:
            self.logger.error(f"Error in analyze_repository: {str(e)}")
            return self.error_response(f"Repository analysis failed: {str(e)}", 500)
    
    def generate_code(self) -> Tuple[Dict[str, Any], int]:
        """
        Generate code based on repository context and requirements
        
        Expected JSON payload:
        {
            "repository_id": "repository identifier",
            "requirements": "description of what to generate",
            "language": "target programming language",
            "file_type": "class|function|module|test|etc",
            "context_files": ["file1.py", "file2.py"] (optional)
        }
        """
        try:
            if not request.is_json:
                return self.error_response("Request must be JSON", 400)
            
            data = request.get_json()
            
            # Validate required fields
            repository_id = data.get('repository_id')
            requirements = data.get('requirements')
            
            if not repository_id:
                return self.error_response("Repository ID is required", 400)
            
            if not requirements:
                return self.error_response("Requirements description is required", 400)
            
            self.logger.info(f"Generating code for repository: {repository_id}")
            
            # Generate code
            result = self.code_generation.generate_code(data)
            
            if result.get('status') == 'success':
                return self.success_response(result), 200
            else:
                return self.error_response(result.get('error', 'Code generation failed'), 500)
                
        except Exception as e:
            self.logger.error(f"Error in generate_code: {str(e)}")
            return self.error_response(f"Code generation failed: {str(e)}", 500)
    
    def list_repository_files(self) -> Tuple[Dict[str, Any], int]:
        """
        List files in a connected repository
        
        Query parameters:
        - repository_id: repository identifier
        - language: filter by programming language (optional)
        """
        try:
            repository_id = request.args.get('repository_id')
            language = request.args.get('language')
            
            if not repository_id:
                return self.error_response("Repository ID is required", 400)
            
            self.logger.info(f"Listing files for repository: {repository_id}")
            
            # Get repository files
            files = self.code_connector.get_repository_files(repository_id, language)
            
            return self.success_response({
                "repository_id": repository_id,
                "language": language,
                "files": files,
                "total_files": len(files)
            }), 200
            
        except Exception as e:
            self.logger.error(f"Error in list_repository_files: {str(e)}")
            return self.error_response(f"Failed to list files: {str(e)}", 500)
    
    def get_file_content(self) -> Tuple[Dict[str, Any], int]:
        """
        Get content of a specific file from repository
        
        Query parameters:
        - repository_id: repository identifier
        - file_path: relative path to the file
        """
        try:
            repository_id = request.args.get('repository_id')
            file_path = request.args.get('file_path')
            
            if not repository_id:
                return self.error_response("Repository ID is required", 400)
            
            if not file_path:
                return self.error_response("File path is required", 400)
            
            self.logger.info(f"Getting file content: {file_path} from {repository_id}")
            
            # Get repository path
            repo_path = self.code_connector._get_repository_path(repository_id)
            if not repo_path:
                return self.error_response("Repository not found", 404)
            
            # Read file content
            import os
            full_file_path = os.path.join(repo_path, file_path)
            
            if not os.path.exists(full_file_path):
                return self.error_response("File not found", 404)
            
            if not os.path.isfile(full_file_path):
                return self.error_response("Path is not a file", 400)
            
            try:
                with open(full_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                return self.success_response({
                    "repository_id": repository_id,
                    "file_path": file_path,
                    "content": content,
                    "size": len(content)
                }), 200
                
            except Exception as e:
                return self.error_response(f"Failed to read file: {str(e)}", 500)
            
        except Exception as e:
            self.logger.error(f"Error in get_file_content: {str(e)}")
            return self.error_response(f"Failed to get file content: {str(e)}", 500)
    
    def cleanup_repository(self) -> Tuple[Dict[str, Any], int]:
        """
        Clean up temporary repository files
        
        Expected JSON payload:
        {
            "repository_id": "repository identifier"
        }
        """
        try:
            if not request.is_json:
                return self.error_response("Request must be JSON", 400)
            
            data = request.get_json()
            repository_id = data.get('repository_id')
            
            if not repository_id:
                return self.error_response("Repository ID is required", 400)
            
            self.logger.info(f"Cleaning up repository: {repository_id}")
            
            # Cleanup repository
            success = self.code_connector.cleanup_repository(repository_id)
            
            if success:
                return self.success_response({
                    "repository_id": repository_id,
                    "cleaned_up": True
                }), 200
            else:
                return self.error_response("Failed to cleanup repository", 500)
                
        except Exception as e:
            self.logger.error(f"Error in cleanup_repository: {str(e)}")
            return self.error_response(f"Cleanup failed: {str(e)}", 500)
    
    def success_response(self, data: Any) -> Dict[str, Any]:
        """Create success response"""
        return {
            "status": "success",
            "data": data,
            "timestamp": int(time.time() * 1000)
        }
    
    def error_response(self, message: str, status_code: int = 500) -> Dict[str, Any]:
        """Create error response"""
        return {
            "status": "error",
            "error": message,
            "code": status_code,
            "timestamp": int(time.time() * 1000)
        }

    # GitHub OAuth Methods

    def github_oauth_config(self) -> Tuple[Dict[str, Any], int]:
        """
        Store GitHub OAuth configuration

        Expected JSON payload:
        {
            "client_id": "your_github_client_id",
            "client_secret": "your_github_client_secret",
            "redirect_uri": "http://localhost:8088/code/auth/github/callback",
            "scope": "repo,read:user"
        }
        """
        try:
            from flask import request

            if not request.is_json:
                return self.error_response("Request must be JSON", 400)

            data = request.get_json()

            # Validate required fields
            client_id = data.get('client_id')
            client_secret = data.get('client_secret')
            redirect_uri = data.get('redirect_uri')
            scope = data.get('scope', 'repo,read:user')

            if not client_id:
                return self.error_response("client_id is required", 400)

            if not client_secret:
                return self.error_response("client_secret is required", 400)

            if not redirect_uri:
                return self.error_response("redirect_uri is required", 400)

            # Store OAuth configuration
            config_id = self.github_oauth.store_oauth_config(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                scope=scope
            )

            return self.success_response({
                "config_id": config_id,
                "message": "OAuth configuration stored successfully",
                "scope": scope
            }), 200

        except Exception as e:
            self.logger.error(f"Error in github_oauth_config: {str(e)}")
            return self.error_response(f"OAuth configuration failed: {str(e)}", 500)

    def github_oauth_login(self) -> Tuple[Dict[str, Any], int]:
        """
        Initiate GitHub OAuth login flow

        Expected query parameters:
        - config_id: OAuth configuration ID from /code/auth/github/config
        """
        try:
            from flask import request

            config_id = request.args.get('config_id')

            if not config_id:
                return self.error_response("config_id parameter is required", 400)

            auth_url, state = self.github_oauth.generate_auth_url(config_id)

            return self.success_response({
                "auth_url": auth_url,
                "state": state,
                "config_id": config_id,
                "message": "Redirect user to auth_url to complete GitHub authentication"
            }), 200

        except Exception as e:
            self.logger.error(f"Error in github_oauth_login: {str(e)}")
            return self.error_response(f"OAuth login failed: {str(e)}", 500)

    def github_oauth_callback(self) -> Tuple[Dict[str, Any], int]:
        """
        Handle GitHub OAuth callback

        Expected query parameters:
        - code: Authorization code from GitHub
        - state: State parameter for CSRF protection
        """
        try:
            from flask import request

            code = request.args.get('code')
            state = request.args.get('state')
            error = request.args.get('error')

            if error:
                return self.error_response(f"GitHub OAuth error: {error}", 400)

            if not code or not state:
                return self.error_response("Missing code or state parameter", 400)

            # Exchange code for token
            result = self.github_oauth.exchange_code_for_token(code, state)

            return self.success_response({
                "session_id": result['session_id'],
                "user": result['user'],
                "token_info": result['token_info'],
                "message": "Successfully authenticated with GitHub"
            }), 200

        except Exception as e:
            self.logger.error(f"Error in github_oauth_callback: {str(e)}")
            return self.error_response(f"OAuth callback failed: {str(e)}", 500)

    def auth_status(self) -> Tuple[Dict[str, Any], int]:
        """
        Check authentication status

        Expected query parameters:
        - session_id: Session identifier
        """
        try:
            from flask import request

            session_id = request.args.get('session_id')

            if not session_id:
                return self.error_response("Session ID is required", 400)

            session_info = self.github_oauth.get_session_info(session_id)

            if not session_info:
                return self.error_response("Session not found or expired", 404)

            return self.success_response({
                "authenticated": True,
                "user": session_info.get('user', {}),
                "token_info": {
                    "scope": session_info.get('scope', ''),
                    "token_type": session_info.get('token_type', 'bearer')
                },
                "session_created": session_info.get('created_at'),
                "message": "User is authenticated"
            }), 200

        except Exception as e:
            self.logger.error(f"Error in auth_status: {str(e)}")
            return self.error_response(f"Auth status check failed: {str(e)}", 500)
