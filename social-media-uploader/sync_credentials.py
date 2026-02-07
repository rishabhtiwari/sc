#!/usr/bin/env python3
"""
Sync YouTube credentials from file system to MongoDB
"""
import json
import os
import sys
from datetime import datetime
from pymongo import MongoClient
import uuid

# Add parent directory to path for common utilities
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# MongoDB connection
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://ichat_admin:ichat_secure_password_2024@ichat-mongodb:27017/')
client = MongoClient(MONGO_URI)
db = client['news']
credentials_collection = db['youtube_credentials']

def sync_credentials(customer_id='customer_system'):
    """
    Sync credentials from file system to MongoDB

    Args:
        customer_id: Customer ID to assign to the credential (default: 'customer_system')
    """
    
    # Load client secrets
    client_secrets_path = '/app/credentials/client_secrets.json'
    youtube_creds_path = '/app/credentials/youtube_credentials.json'
    
    if not os.path.exists(client_secrets_path):
        print(f"❌ Client secrets file not found: {client_secrets_path}")
        return
    
    if not os.path.exists(youtube_creds_path):
        print(f"❌ YouTube credentials file not found: {youtube_creds_path}")
        return
    
    # Read client secrets
    with open(client_secrets_path, 'r') as f:
        client_secrets_data = json.load(f)
        client_secrets = client_secrets_data.get('installed', {})
    
    # Read YouTube credentials
    with open(youtube_creds_path, 'r') as f:
        youtube_creds = json.load(f)
    
    # Parse token expiry
    token_expiry = None
    if 'expiry' in youtube_creds:
        try:
            token_expiry = datetime.fromisoformat(youtube_creds['expiry'].replace('Z', '+00:00'))
        except:
            token_expiry = datetime.now()
    
    # Create credential document
    credential_doc = {
        'credential_id': 'default-youtube-credential',
        'name': 'Default YouTube Account',
        'client_id': client_secrets.get('client_id'),
        'client_secret': client_secrets.get('client_secret'),
        'project_id': client_secrets.get('project_id'),
        'auth_uri': client_secrets.get('auth_uri'),
        'token_uri': client_secrets.get('token_uri'),
        'auth_provider_x509_cert_url': client_secrets.get('auth_provider_x509_cert_url'),
        'redirect_uris': client_secrets.get('redirect_uris', []),
        'access_token': youtube_creds.get('token'),
        'refresh_token': youtube_creds.get('refresh_token'),
        'token_expiry': token_expiry,
        'scopes': youtube_creds.get('scopes', []),
        'channel_id': None,
        'channel_name': None,
        'is_active': True,
        'is_authenticated': True,
        'last_used_at': None,
        'created_at': datetime.now(),
        'updated_at': datetime.now(),
        'created_by': 'system',
        'notes': 'Synced from file system credentials',
        'customer_id': customer_id,  # Add customer_id for multi-tenancy
        'is_deleted': False
    }
    
    # Insert or update the credential
    result = credentials_collection.update_one(
        {'credential_id': 'default-youtube-credential'},
        {'$set': credential_doc},
        upsert=True
    )
    
    print("✅ Credential sync completed!")
    print(f"   - Matched: {result.matched_count}")
    print(f"   - Modified: {result.modified_count}")
    print(f"   - Upserted ID: {result.upserted_id}")
    
    # Verify the insertion
    inserted = credentials_collection.find_one({'credential_id': 'default-youtube-credential'})
    if inserted:
        print("\n📋 Synced credential:")
        print(f"   - ID: {inserted['credential_id']}")
        print(f"   - Name: {inserted['name']}")
        print(f"   - Project: {inserted['project_id']}")
        print(f"   - Active: {inserted['is_active']}")
        print(f"   - Authenticated: {inserted['is_authenticated']}")
        print(f"   - Token Expiry: {inserted.get('token_expiry')}")
        print(f"   - Has Access Token: {bool(inserted.get('access_token'))}")
        print(f"   - Has Refresh Token: {bool(inserted.get('refresh_token'))}")

if __name__ == '__main__':
    # Get customer_id from command line argument or environment variable
    import sys
    customer_id = sys.argv[1] if len(sys.argv) > 1 else os.getenv('CUSTOMER_ID', 'customer_system')
    print(f"Syncing credentials for customer: {customer_id}")
    sync_credentials(customer_id=customer_id)

