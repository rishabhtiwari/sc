#!/usr/bin/env python3
"""
Test script for persistent token storage
"""

import os
import sys
import time
import uuid
import logging

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.token_storage_service import TokenStorageService
from services.github_oauth_service import GitHubOAuthService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_token_storage():
    """Test the persistent token storage system"""
    
    logger.info("🧪 Starting token storage tests...")
    
    try:
        # Initialize storage service
        storage = TokenStorageService()
        logger.info("✅ Token storage service initialized")
        
        # Test 1: Store and retrieve OAuth configuration
        logger.info("\n📝 Test 1: OAuth Configuration Storage")
        
        config_id = str(uuid.uuid4())
        config_data = {
            'client_id': 'test_client_id',
            'client_secret': 'test_client_secret',
            'redirect_uri': 'http://localhost:8080/callback',
            'scope': 'repo,read:user',
            'provider': 'github'
        }
        
        # Store configuration
        success = storage.store_oauth_config(config_id, 'github', config_data)
        assert success, "Failed to store OAuth configuration"
        logger.info(f"✅ Stored OAuth config: {config_id}")
        
        # Retrieve configuration
        retrieved_config = storage.get_oauth_config(config_id)
        assert retrieved_config is not None, "Failed to retrieve OAuth configuration"
        assert retrieved_config['client_id'] == config_data['client_id'], "Configuration data mismatch"
        logger.info("✅ Retrieved OAuth config successfully")
        
        # Test 2: Store and retrieve OAuth token
        logger.info("\n🔑 Test 2: OAuth Token Storage")
        
        token_id = str(uuid.uuid4())
        token_data = {
            'access_token': 'ghp_test_token_12345',
            'token_type': 'bearer',
            'scope': 'repo,read:user'
        }
        
        user_info = {
            'login': 'testuser',
            'name': 'Test User',
            'email': 'test@example.com'
        }
        
        # Store token
        success = storage.store_oauth_token(
            token_id=token_id,
            provider='github',
            config_id=config_id,
            token_data=token_data,
            user_info=user_info
        )
        assert success, "Failed to store OAuth token"
        logger.info(f"✅ Stored OAuth token: {token_id}")
        
        # Retrieve token
        retrieved_token = storage.get_oauth_token(token_id)
        assert retrieved_token is not None, "Failed to retrieve OAuth token"
        assert retrieved_token['access_token'] == token_data['access_token'], "Token data mismatch"
        assert retrieved_token['provider'] == 'github', "Provider mismatch"
        logger.info("✅ Retrieved OAuth token successfully")
        
        # Test 3: List tokens
        logger.info("\n📋 Test 3: Token Listing")
        
        tokens_list = storage.list_oauth_tokens(provider='github')
        assert len(tokens_list) >= 1, "Token list should contain at least one token"
        
        found_token = None
        for token in tokens_list:
            if token['token_id'] == token_id:
                found_token = token
                break
        
        assert found_token is not None, "Token not found in list"
        assert found_token['user_login'] == 'testuser', "User info mismatch"
        logger.info(f"✅ Listed {len(tokens_list)} tokens")
        
        # Test 4: OAuth state management
        logger.info("\n🔒 Test 4: OAuth State Management")
        
        state = str(uuid.uuid4())
        
        # Store state
        success = storage.store_oauth_state(state, config_id, expires_in=60)
        assert success, "Failed to store OAuth state"
        logger.info(f"✅ Stored OAuth state: {state}")
        
        # Validate state
        validated_config_id = storage.validate_oauth_state(state)
        assert validated_config_id == config_id, "State validation failed"
        logger.info("✅ Validated OAuth state successfully")
        
        # Try to validate same state again (should fail)
        validated_again = storage.validate_oauth_state(state)
        assert validated_again is None, "State should be consumed after validation"
        logger.info("✅ State properly consumed after validation")
        
        # Test 5: Token revocation
        logger.info("\n🗑️ Test 5: Token Revocation")
        
        success = storage.revoke_oauth_token(token_id)
        assert success, "Failed to revoke token"
        logger.info(f"✅ Revoked token: {token_id}")
        
        # Try to retrieve revoked token
        revoked_token = storage.get_oauth_token(token_id)
        assert revoked_token is None, "Revoked token should not be retrievable"
        logger.info("✅ Revoked token properly removed")
        
        # Test 6: Storage statistics
        logger.info("\n📊 Test 6: Storage Statistics")
        
        stats = storage.get_storage_stats()
        assert 'total_configs' in stats, "Stats should include total_configs"
        assert 'total_tokens' in stats, "Stats should include total_tokens"
        logger.info(f"✅ Storage stats: {stats}")
        
        # Test 7: GitHub OAuth Service Integration
        logger.info("\n🐙 Test 7: GitHub OAuth Service Integration")
        
        github_service = GitHubOAuthService()
        
        # Store a configuration
        test_config_id = github_service.store_oauth_config(
            client_id='test_github_client',
            client_secret='test_github_secret',
            redirect_uri='http://localhost:8080/callback',
            scope='repo,read:user'
        )
        
        logger.info(f"✅ GitHub OAuth service stored config: {test_config_id}")
        
        # List tokens (should be empty now)
        tokens = github_service.list_tokens()
        logger.info(f"✅ GitHub OAuth service listed {len(tokens)} tokens")
        
        logger.info("\n🎉 All tests passed! Persistent storage is working correctly.")
        
        # Cleanup
        storage.close()
        logger.info("✅ Storage service closed")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {str(e)}")
        raise

if __name__ == "__main__":
    test_token_storage()
