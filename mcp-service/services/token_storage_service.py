"""
Secure Token Storage Service - Production-ready persistent storage for OAuth tokens
"""

import os
import json
import time
import logging
import sqlite3
from typing import Dict, List, Optional, Any
from cryptography.fernet import Fernet
from sqlalchemy import create_engine, Column, String, Float, Text, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from config.settings import MCPConfig

Base = declarative_base()


class OAuthToken(Base):
    """SQLAlchemy model for OAuth tokens"""
    __tablename__ = 'oauth_tokens'
    
    token_id = Column(String(36), primary_key=True)
    provider = Column(String(50), nullable=False)
    config_id = Column(String(36), nullable=False)
    encrypted_token_data = Column(Text, nullable=False)
    scope = Column(String(500))
    user_login = Column(String(100))
    user_name = Column(String(200))
    user_email = Column(String(200))
    created_at = Column(Float, nullable=False)
    last_used_at = Column(Float)
    expires_at = Column(Float)  # For providers that have token expiration


class OAuthConfig(Base):
    """SQLAlchemy model for OAuth configurations"""
    __tablename__ = 'oauth_configs'
    
    config_id = Column(String(36), primary_key=True)
    provider = Column(String(50), nullable=False)
    encrypted_config_data = Column(Text, nullable=False)
    created_at = Column(Float, nullable=False)


class OAuthState(Base):
    """SQLAlchemy model for OAuth states (CSRF protection)"""
    __tablename__ = 'oauth_states'
    
    state = Column(String(36), primary_key=True)
    config_id = Column(String(36), nullable=False)
    created_at = Column(Float, nullable=False)
    expires_at = Column(Float, nullable=False)


class TokenStorageService:
    """Production-ready secure token storage service"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = MCPConfig()
        
        # Initialize encryption
        self._init_encryption()
        
        # Initialize database
        self._init_database()
        
        self.logger.info("✅ Token storage service initialized with persistent storage")
    
    def _init_encryption(self):
        """Initialize encryption key for token security"""
        try:
            # Get encryption key from environment or generate new one
            key_path = os.path.join(self.config.MCP_CONFIG_STORAGE_PATH, 'encryption.key')
            
            if os.path.exists(key_path):
                # Load existing key
                with open(key_path, 'rb') as key_file:
                    self.encryption_key = key_file.read()
                self.logger.info("✅ Loaded existing encryption key")
            else:
                # Generate new key
                self.encryption_key = Fernet.generate_key()
                
                # Ensure directory exists
                os.makedirs(os.path.dirname(key_path), exist_ok=True)
                
                # Save key securely
                with open(key_path, 'wb') as key_file:
                    key_file.write(self.encryption_key)
                
                # Set secure permissions (owner read/write only)
                os.chmod(key_path, 0o600)
                
                self.logger.info("✅ Generated new encryption key")
            
            self.cipher_suite = Fernet(self.encryption_key)
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize encryption: {str(e)}")
            raise
    
    def _init_database(self):
        """Initialize SQLite database with proper security"""
        try:
            # Database path
            db_path = os.path.join(self.config.MCP_CONFIG_STORAGE_PATH, 'tokens.db')
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            
            # Create database engine
            self.engine = create_engine(
                f'sqlite:///{db_path}',
                echo=False,  # Set to True for SQL debugging
                pool_pre_ping=True,
                connect_args={
                    'check_same_thread': False,
                    'timeout': 30
                }
            )
            
            # Create tables
            Base.metadata.create_all(self.engine)
            
            # Create session factory
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            
            # Set secure permissions on database file
            if os.path.exists(db_path):
                os.chmod(db_path, 0o600)
            
            self.logger.info(f"✅ Database initialized at: {db_path}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize database: {str(e)}")
            raise
    
    def _encrypt_data(self, data: Dict[str, Any]) -> str:
        """Encrypt sensitive data"""
        try:
            json_data = json.dumps(data)
            encrypted_data = self.cipher_suite.encrypt(json_data.encode())
            return encrypted_data.decode()
        except Exception as e:
            self.logger.error(f"❌ Encryption failed: {str(e)}")
            raise
    
    def _decrypt_data(self, encrypted_data: str) -> Dict[str, Any]:
        """Decrypt sensitive data"""
        try:
            decrypted_data = self.cipher_suite.decrypt(encrypted_data.encode())
            return json.loads(decrypted_data.decode())
        except Exception as e:
            self.logger.error(f"❌ Decryption failed: {str(e)}")
            raise
    
    def get_session(self) -> Session:
        """Get database session"""
        return self.SessionLocal()
    
    # OAuth Configuration Methods
    
    def store_oauth_config(self, config_id: str, provider: str, config_data: Dict[str, Any]) -> bool:
        """
        Store OAuth configuration securely
        
        Args:
            config_id: Unique configuration ID
            provider: Provider name (e.g., 'github')
            config_data: Configuration data to encrypt and store
            
        Returns:
            True if successful, False otherwise
        """
        try:
            session = self.get_session()
            
            # Encrypt sensitive configuration data
            encrypted_config = self._encrypt_data(config_data)
            
            # Create or update configuration
            oauth_config = session.query(OAuthConfig).filter_by(config_id=config_id).first()
            
            if oauth_config:
                # Update existing
                oauth_config.encrypted_config_data = encrypted_config
            else:
                # Create new
                oauth_config = OAuthConfig(
                    config_id=config_id,
                    provider=provider,
                    encrypted_config_data=encrypted_config,
                    created_at=time.time()
                )
                session.add(oauth_config)
            
            session.commit()
            session.close()
            
            self.logger.info(f"✅ Stored OAuth config for provider: {provider}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to store OAuth config: {str(e)}")
            if 'session' in locals():
                session.rollback()
                session.close()
            return False
    
    def get_oauth_config(self, config_id: str) -> Optional[Dict[str, Any]]:
        """
        Get OAuth configuration
        
        Args:
            config_id: Configuration ID
            
        Returns:
            Decrypted configuration data or None if not found
        """
        try:
            session = self.get_session()
            
            oauth_config = session.query(OAuthConfig).filter_by(config_id=config_id).first()
            session.close()
            
            if oauth_config:
                return self._decrypt_data(oauth_config.encrypted_config_data)
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Failed to get OAuth config: {str(e)}")
            if 'session' in locals():
                session.close()
            return None

    # OAuth Token Methods

    def store_oauth_token(self, token_id: str, provider: str, config_id: str,
                         token_data: Dict[str, Any], user_info: Dict[str, Any] = None,
                         expires_at: float = None) -> bool:
        """
        Store OAuth token securely

        Args:
            token_id: Unique token ID
            provider: Provider name (e.g., 'github')
            config_id: Associated configuration ID
            token_data: Token data to encrypt and store
            user_info: User information (optional)
            expires_at: Token expiration timestamp (optional)

        Returns:
            True if successful, False otherwise
        """
        try:
            session = self.get_session()

            # Encrypt sensitive token data
            encrypted_token = self._encrypt_data(token_data)

            # Create or update token
            oauth_token = session.query(OAuthToken).filter_by(token_id=token_id).first()

            if oauth_token:
                # Update existing
                oauth_token.encrypted_token_data = encrypted_token
                oauth_token.last_used_at = time.time()
            else:
                # Create new
                oauth_token = OAuthToken(
                    token_id=token_id,
                    provider=provider,
                    config_id=config_id,
                    encrypted_token_data=encrypted_token,
                    scope=token_data.get('scope', ''),
                    user_login=user_info.get('login', '') if user_info else '',
                    user_name=user_info.get('name', '') if user_info else '',
                    user_email=user_info.get('email', '') if user_info else '',
                    created_at=time.time(),
                    last_used_at=time.time(),
                    expires_at=expires_at
                )
                session.add(oauth_token)

            session.commit()
            session.close()

            self.logger.info(f"✅ Stored OAuth token for provider: {provider}")
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to store OAuth token: {str(e)}")
            if 'session' in locals():
                session.rollback()
                session.close()
            return False

    def get_oauth_token(self, token_id: str) -> Optional[Dict[str, Any]]:
        """
        Get OAuth token

        Args:
            token_id: Token ID

        Returns:
            Decrypted token data or None if not found
        """
        try:
            session = self.get_session()

            oauth_token = session.query(OAuthToken).filter_by(token_id=token_id).first()

            if oauth_token:
                # Update last used timestamp
                oauth_token.last_used_at = time.time()
                session.commit()

                # Decrypt token data
                token_data = self._decrypt_data(oauth_token.encrypted_token_data)

                # Add metadata
                token_data.update({
                    'token_id': oauth_token.token_id,
                    'provider': oauth_token.provider,
                    'config_id': oauth_token.config_id,
                    'scope': oauth_token.scope,
                    'created_at': oauth_token.created_at,
                    'last_used_at': oauth_token.last_used_at,
                    'expires_at': oauth_token.expires_at
                })

                session.close()
                return token_data
            else:
                session.close()
                return None

        except Exception as e:
            self.logger.error(f"❌ Failed to get OAuth token: {str(e)}")
            if 'session' in locals():
                session.close()
            return None

    def list_oauth_tokens(self, provider: str = None) -> List[Dict[str, Any]]:
        """
        List OAuth tokens (without sensitive data)

        Args:
            provider: Filter by provider (optional)

        Returns:
            List of token summaries
        """
        try:
            session = self.get_session()

            query = session.query(OAuthToken)
            if provider:
                query = query.filter_by(provider=provider)

            tokens = query.all()
            session.close()

            tokens_list = []
            for token in tokens:
                tokens_list.append({
                    'token_id': token.token_id,
                    'provider': token.provider,
                    'scope': token.scope,
                    'user_login': token.user_login,
                    'user_name': token.user_name,
                    'user_email': token.user_email,
                    'created_at': token.created_at,
                    'last_used_at': token.last_used_at,
                    'expires_at': token.expires_at,
                    'is_expired': token.expires_at and token.expires_at < time.time() if token.expires_at else False
                })

            return tokens_list

        except Exception as e:
            self.logger.error(f"❌ Failed to list OAuth tokens: {str(e)}")
            if 'session' in locals():
                session.close()
            return []

    def revoke_oauth_token(self, token_id: str) -> bool:
        """
        Revoke and delete OAuth token

        Args:
            token_id: Token ID to revoke

        Returns:
            True if successful, False otherwise
        """
        try:
            session = self.get_session()

            oauth_token = session.query(OAuthToken).filter_by(token_id=token_id).first()

            if oauth_token:
                session.delete(oauth_token)
                session.commit()
                session.close()

                self.logger.info(f"✅ Revoked OAuth token: {token_id}")
                return True
            else:
                session.close()
                self.logger.warning(f"⚠️ Token not found for revocation: {token_id}")
                return False

        except Exception as e:
            self.logger.error(f"❌ Failed to revoke OAuth token: {str(e)}")
            if 'session' in locals():
                session.rollback()
                session.close()
            return False

    # OAuth State Methods (CSRF Protection)

    def store_oauth_state(self, state: str, config_id: str, expires_in: int = 600) -> bool:
        """
        Store OAuth state for CSRF protection

        Args:
            state: Unique state string
            config_id: Associated configuration ID
            expires_in: State expiration time in seconds (default: 10 minutes)

        Returns:
            True if successful, False otherwise
        """
        try:
            session = self.get_session()

            # Clean up expired states first
            self._cleanup_expired_states(session)

            # Create new state
            oauth_state = OAuthState(
                state=state,
                config_id=config_id,
                created_at=time.time(),
                expires_at=time.time() + expires_in
            )

            session.add(oauth_state)
            session.commit()
            session.close()

            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to store OAuth state: {str(e)}")
            if 'session' in locals():
                session.rollback()
                session.close()
            return False

    def validate_oauth_state(self, state: str) -> Optional[str]:
        """
        Validate OAuth state and return associated config_id

        Args:
            state: State string to validate

        Returns:
            Config ID if valid, None otherwise
        """
        try:
            session = self.get_session()

            # Clean up expired states first
            self._cleanup_expired_states(session)

            oauth_state = session.query(OAuthState).filter_by(state=state).first()

            if oauth_state and oauth_state.expires_at > time.time():
                config_id = oauth_state.config_id

                # Remove used state
                session.delete(oauth_state)
                session.commit()
                session.close()

                return config_id
            else:
                session.close()
                return None

        except Exception as e:
            self.logger.error(f"❌ Failed to validate OAuth state: {str(e)}")
            if 'session' in locals():
                session.close()
            return None

    def _cleanup_expired_states(self, session: Session):
        """Clean up expired OAuth states"""
        try:
            current_time = time.time()
            expired_states = session.query(OAuthState).filter(OAuthState.expires_at < current_time).all()

            for state in expired_states:
                session.delete(state)

            if expired_states:
                self.logger.info(f"🧹 Cleaned up {len(expired_states)} expired OAuth states")

        except Exception as e:
            self.logger.error(f"❌ Failed to cleanup expired states: {str(e)}")

    # Utility Methods

    def cleanup_expired_tokens(self):
        """Clean up expired tokens (for providers that have token expiration)"""
        try:
            session = self.get_session()

            current_time = time.time()
            expired_tokens = session.query(OAuthToken).filter(
                OAuthToken.expires_at.isnot(None),
                OAuthToken.expires_at < current_time
            ).all()

            for token in expired_tokens:
                session.delete(token)

            session.commit()
            session.close()

            if expired_tokens:
                self.logger.info(f"🧹 Cleaned up {len(expired_tokens)} expired tokens")

        except Exception as e:
            self.logger.error(f"❌ Failed to cleanup expired tokens: {str(e)}")
            if 'session' in locals():
                session.rollback()
                session.close()

    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        try:
            session = self.get_session()

            total_configs = session.query(OAuthConfig).count()
            total_tokens = session.query(OAuthToken).count()
            total_states = session.query(OAuthState).count()

            # Count by provider
            provider_stats = {}
            providers = session.query(OAuthToken.provider).distinct().all()

            for (provider,) in providers:
                count = session.query(OAuthToken).filter_by(provider=provider).count()
                provider_stats[provider] = count

            session.close()

            return {
                'total_configs': total_configs,
                'total_tokens': total_tokens,
                'total_states': total_states,
                'provider_stats': provider_stats,
                'timestamp': time.time()
            }

        except Exception as e:
            self.logger.error(f"❌ Failed to get storage stats: {str(e)}")
            if 'session' in locals():
                session.close()
            return {}

    def close(self):
        """Close database connections"""
        try:
            if hasattr(self, 'engine'):
                self.engine.dispose()
            self.logger.info("✅ Token storage service closed")
        except Exception as e:
            self.logger.error(f"❌ Error closing token storage service: {str(e)}")
