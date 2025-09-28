"""
GitHub OAuth Service - Handles GitHub OAuth authentication for MCP
"""

import json
import uuid
import time
import logging
import requests
from typing import Dict, List, Optional, Any
from urllib.parse import urlencode

from config.settings import MCPConfig
from services.token_storage_service import TokenStorageService


class GitHubOAuthService:
    """Service for managing GitHub OAuth authentication"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = MCPConfig()

        # Initialize persistent storage service
        self.storage = TokenStorageService()

        self.logger.info("✅ GitHub OAuth service initialized with persistent storage")
    
    def store_oauth_config(self, client_id: str, client_secret: str, 
                          redirect_uri: str, scope: str = "repo,read:user") -> str:
        """
        Store GitHub OAuth configuration
        
        Args:
            client_id: GitHub OAuth app client ID
            client_secret: GitHub OAuth app client secret
            redirect_uri: OAuth redirect URI
            scope: OAuth scopes
            
        Returns:
            Configuration ID
        """
        config_id = str(uuid.uuid4())

        config_data = {
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': redirect_uri,
            'scope': scope,
            'provider': 'github'
        }

        # Store configuration securely
        if self.storage.store_oauth_config(config_id, 'github', config_data):
            self.logger.info(f"✅ Stored GitHub OAuth config: {config_id}")
            return config_id
        else:
            self.logger.error(f"❌ Failed to store GitHub OAuth config")
            raise Exception("Failed to store OAuth configuration")
    
    def generate_auth_url(self, config_id: str, state: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate GitHub OAuth authorization URL
        
        Args:
            config_id: OAuth configuration ID
            state: Optional state parameter for CSRF protection
            
        Returns:
            Dict with authorization URL and state
        """
        try:
            # Get configuration from persistent storage
            config = self.storage.get_oauth_config(config_id)
            if not config:
                return {
                    "status": "error",
                    "error": "OAuth configuration not found"
                }
            
            # Generate state if not provided
            if not state:
                state = str(uuid.uuid4())
            
            # Store state for validation using persistent storage
            if not self.storage.store_oauth_state(state, config_id, expires_in=600):
                return {
                    "status": "error",
                    "error": "Failed to store OAuth state"
                }
            
            # Build authorization URL
            auth_params = {
                'client_id': config['client_id'],
                'redirect_uri': config['redirect_uri'],
                'scope': config['scope'],
                'state': state,
                'response_type': 'code'
            }
            
            auth_url = f"https://github.com/login/oauth/authorize?{urlencode(auth_params)}"
            
            return {
                "status": "success",
                "auth_url": auth_url,
                "state": state,
                "config_id": config_id
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to generate auth URL: {str(e)}")
            return {
                "status": "error",
                "error": f"Failed to generate authorization URL: {str(e)}"
            }
    
    def handle_oauth_callback(self, code: str, state: str) -> Dict[str, Any]:
        """
        Handle OAuth callback and exchange code for token
        
        Args:
            code: Authorization code from GitHub
            state: State parameter for CSRF protection
            
        Returns:
            Dict with token exchange result
        """
        try:
            # Validate state using persistent storage
            config_id = self.storage.validate_oauth_state(state)
            if not config_id:
                return {
                    "status": "error",
                    "error": "Invalid or expired state parameter"
                }

            # Get configuration from persistent storage
            config = self.storage.get_oauth_config(config_id)
            if not config:
                return {
                    "status": "error",
                    "error": "OAuth configuration not found"
                }
            
            # Exchange code for access token
            token_data = {
                'client_id': config['client_id'],
                'client_secret': config['client_secret'],
                'code': code,
                'redirect_uri': config['redirect_uri']
            }
            
            headers = {
                'Accept': 'application/json',
                'User-Agent': 'iChat-MCP-Service/1.0'
            }
            
            response = requests.post(
                'https://github.com/login/oauth/access_token',
                data=token_data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                token_response = response.json()
                
                if 'access_token' in token_response:
                    # Get user info
                    user_info = self._get_user_info(token_response['access_token'])

                    # Store the token securely
                    token_id = str(uuid.uuid4())
                    token_data = {
                        'access_token': token_response['access_token'],
                        'token_type': token_response.get('token_type', 'bearer'),
                        'scope': token_response.get('scope', config['scope'])
                    }

                    # Store token using persistent storage
                    if not self.storage.store_oauth_token(
                        token_id=token_id,
                        provider='github',
                        config_id=config_id,
                        token_data=token_data,
                        user_info=user_info
                    ):
                        return {
                            "status": "error",
                            "error": "Failed to store OAuth token"
                        }
                    
                    self.logger.info(f"✅ Successfully authenticated GitHub user: {user_info.get('login', 'unknown')}")
                    
                    return {
                        "status": "success",
                        "token_id": token_id,
                        "user_info": user_info,
                        "scopes": token_response.get('scope', '').split(',')
                    }
                else:
                    return {
                        "status": "error",
                        "error": f"Token exchange failed: {token_response.get('error_description', 'Unknown error')}"
                    }
            else:
                return {
                    "status": "error",
                    "error": f"Token exchange failed with status {response.status_code}"
                }
                
        except Exception as e:
            self.logger.error(f"❌ OAuth callback failed: {str(e)}")
            return {
                "status": "error",
                "error": f"OAuth callback failed: {str(e)}"
            }
    
    def _get_user_info(self, access_token: str) -> Dict[str, Any]:
        """
        Get GitHub user information
        
        Args:
            access_token: GitHub access token
            
        Returns:
            Dict with user information
        """
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'iChat-MCP-Service/1.0'
            }
            
            response = requests.get(
                'https://api.github.com/user',
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.warning(f"Failed to get user info: {response.status_code}")
                return {}
                
        except Exception as e:
            self.logger.error(f"❌ Failed to get user info: {str(e)}")
            return {}
    
    def get_token_info(self, token_id: str) -> Optional[Dict[str, Any]]:
        """
        Get stored token information

        Args:
            token_id: Token ID

        Returns:
            Token information or None if not found
        """
        return self.storage.get_oauth_token(token_id)
    
    def revoke_token(self, token_id: str) -> Dict[str, Any]:
        """
        Revoke and remove stored token

        Args:
            token_id: Token ID to revoke

        Returns:
            Dict with revocation result
        """
        try:
            if self.storage.revoke_oauth_token(token_id):
                self.logger.info(f"✅ Successfully revoked token: {token_id}")
                return {
                    "status": "success",
                    "message": "Token revoked successfully"
                }
            else:
                return {
                    "status": "error",
                    "error": "Token not found"
                }

        except Exception as e:
            self.logger.error(f"❌ Failed to revoke token: {str(e)}")
            return {
                "status": "error",
                "error": f"Token revocation failed: {str(e)}"
            }
    
    def list_tokens(self) -> List[Dict[str, Any]]:
        """
        List all stored tokens (without sensitive data)

        Returns:
            List of token summaries
        """
        return self.storage.list_oauth_tokens(provider='github')
