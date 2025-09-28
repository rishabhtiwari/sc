"""
GitHub OAuth Service for handling authentication and token management
"""
import os
import time
import uuid
import requests
import urllib.parse
from typing import Dict, Any, Optional, Tuple
from config.settings import Config
from utils.logger import setup_logger


class GitHubOAuthService:
    """Service for handling GitHub OAuth authentication"""
    
    def __init__(self):
        self.logger = setup_logger(__name__)

        # In-memory session storage (in production, use Redis or database)
        self.sessions = {}

        # OAuth configurations will be stored per session
        self.oauth_configs = {}
    
    def store_oauth_config(self, client_id: str, client_secret: str, redirect_uri: str, scope: str = "repo,read:user") -> str:
        """
        Store OAuth configuration and return a config ID

        Args:
            client_id: GitHub OAuth app client ID
            client_secret: GitHub OAuth app client secret
            redirect_uri: OAuth callback URL
            scope: OAuth scope permissions

        Returns:
            Configuration ID for this OAuth setup
        """
        config_id = str(uuid.uuid4())
        self.oauth_configs[config_id] = {
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': redirect_uri,
            'scope': scope,
            'created_at': time.time()
        }

        self.logger.info(f"Stored OAuth config with ID: {config_id}")
        return config_id

    def generate_auth_url(self, config_id: str) -> Tuple[str, str]:
        """
        Generate GitHub OAuth authorization URL using stored config

        Args:
            config_id: Configuration ID from store_oauth_config

        Returns:
            Tuple of (auth_url, state) where state is used for CSRF protection
        """
        try:
            if config_id not in self.oauth_configs:
                raise ValueError("Invalid OAuth configuration ID")

            config = self.oauth_configs[config_id]

            # Generate random state for CSRF protection
            state = str(uuid.uuid4())

            # Store state in session (expires in 10 minutes)
            self.sessions[state] = {
                'created_at': time.time(),
                'type': 'oauth_state',
                'config_id': config_id
            }

            # Build authorization URL
            params = {
                'client_id': config['client_id'],
                'redirect_uri': config['redirect_uri'],
                'scope': config['scope'],
                'state': state,
                'response_type': 'code'
            }

            auth_url = f"https://github.com/login/oauth/authorize?{urllib.parse.urlencode(params)}"

            self.logger.info(f"Generated GitHub OAuth URL with state: {state}")
            return auth_url, state

        except Exception as e:
            self.logger.error(f"Error generating auth URL: {str(e)}")
            raise
    
    def exchange_code_for_token(self, code: str, state: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access token

        Args:
            code: Authorization code from GitHub
            state: State parameter for CSRF protection

        Returns:
            Dictionary containing token information and user data
        """
        try:
            # Validate state and get config
            state_session = self._validate_state(state)
            if not state_session:
                raise ValueError("Invalid or expired state parameter")

            config_id = state_session.get('config_id')
            if not config_id or config_id not in self.oauth_configs:
                raise ValueError("Invalid OAuth configuration")

            config = self.oauth_configs[config_id]

            # Exchange code for token
            token_data = self._request_access_token(code, config)

            if 'access_token' not in token_data:
                raise ValueError("Failed to obtain access token")

            access_token = token_data['access_token']

            # Get user information
            user_data = self._get_user_info(access_token)

            # Store token in session
            session_id = str(uuid.uuid4())
            self.sessions[session_id] = {
                'access_token': access_token,
                'token_type': token_data.get('token_type', 'bearer'),
                'scope': token_data.get('scope', ''),
                'user': user_data,
                'created_at': time.time(),
                'type': 'access_token',
                'config_id': config_id
            }

            # Clean up state session
            if state in self.sessions:
                del self.sessions[state]

            self.logger.info(f"Successfully authenticated user: {user_data.get('login')}")

            return {
                'session_id': session_id,
                'user': user_data,
                'token_info': {
                    'scope': token_data.get('scope', ''),
                    'token_type': token_data.get('token_type', 'bearer')
                }
            }

        except Exception as e:
            self.logger.error(f"Error exchanging code for token: {str(e)}")
            raise
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session information by session ID
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session data or None if not found/expired
        """
        try:
            if session_id not in self.sessions:
                return None
            
            session = self.sessions[session_id]
            
            # Check if session is expired (1 hour)
            if time.time() - session['created_at'] > Config.SESSION_TIMEOUT:
                del self.sessions[session_id]
                return None
            
            return session
            
        except Exception as e:
            self.logger.error(f"Error getting session info: {str(e)}")
            return None
    
    def get_access_token(self, session_id: str) -> Optional[str]:
        """
        Get access token for a session
        
        Args:
            session_id: Session identifier
            
        Returns:
            Access token or None if not found/expired
        """
        session = self.get_session_info(session_id)
        if session and session.get('type') == 'access_token':
            return session.get('access_token')
        return None
    
    def revoke_session(self, session_id: str) -> bool:
        """
        Revoke/delete a session
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if session was revoked, False if not found
        """
        try:
            if session_id in self.sessions:
                del self.sessions[session_id]
                self.logger.info(f"Session revoked: {session_id}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Error revoking session: {str(e)}")
            return False
    
    def _validate_state(self, state: str) -> Optional[Dict[str, Any]]:
        """Validate OAuth state parameter and return session data"""
        if state not in self.sessions:
            return None

        session = self.sessions[state]

        # Check if state is expired (10 minutes)
        if time.time() - session['created_at'] > 600:
            del self.sessions[state]
            return None

        if session.get('type') == 'oauth_state':
            return session
        return None
    
    def _request_access_token(self, code: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Request access token from GitHub"""
        data = {
            'client_id': config['client_id'],
            'client_secret': config['client_secret'],
            'code': code,
            'redirect_uri': config['redirect_uri']
        }
        
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'iChat-CodeGeneration-Service'
        }
        
        response = requests.post(
            'https://github.com/login/oauth/access_token',
            data=data,
            headers=headers,
            timeout=30
        )
        
        response.raise_for_status()
        return response.json()
    
    def _get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information from GitHub API"""
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'iChat-CodeGeneration-Service'
        }
        
        response = requests.get(
            'https://api.github.com/user',
            headers=headers,
            timeout=30
        )
        
        response.raise_for_status()
        return response.json()
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        try:
            current_time = time.time()
            expired_sessions = []
            
            for session_id, session in self.sessions.items():
                # Different timeouts for different session types
                timeout = 600 if session.get('type') == 'oauth_state' else Config.SESSION_TIMEOUT
                
                if current_time - session['created_at'] > timeout:
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                del self.sessions[session_id]
            
            if expired_sessions:
                self.logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
                
        except Exception as e:
            self.logger.error(f"Error cleaning up sessions: {str(e)}")
