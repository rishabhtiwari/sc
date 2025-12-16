"""
MongoDB Client Utility
Provides MongoDB connection and database access for multi-tenant system
"""

import os
import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

logger = logging.getLogger(__name__)


class MongoDBClient:
    """
    MongoDB client singleton for managing database connections
    """
    _instance = None
    _client = None
    _news_db = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDBClient, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize MongoDB connection"""
        try:
            # Get MongoDB connection details from environment
            mongodb_host = os.getenv('MONGODB_HOST', 'ichat-mongodb')
            mongodb_port = int(os.getenv('MONGODB_PORT', 27017))
            mongodb_username = os.getenv('MONGODB_USERNAME', 'ichat_app')
            mongodb_password = os.getenv('MONGODB_PASSWORD', 'ichat_app_password_2024')
            
            # Create MongoDB connection URL
            mongodb_url = f'mongodb://{mongodb_username}:{mongodb_password}@{mongodb_host}:{mongodb_port}/?authSource=admin'
            
            # Create MongoDB client
            self._client = MongoClient(mongodb_url)
            
            # Test connection
            self._client.admin.command('ping')
            logger.info(f"✅ Connected to MongoDB at {mongodb_host}:{mongodb_port}")
            
            # Get news database
            self._news_db = self._client['news']
            
        except ConnectionFailure as e:
            logger.error(f"❌ Failed to connect to MongoDB: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"❌ Error initializing MongoDB client: {str(e)}")
            raise
    
    @property
    def client(self):
        """Get MongoDB client"""
        return self._client
    
    @property
    def news_db(self):
        """Get news database"""
        return self._news_db
    
    # Collection accessors
    @property
    def customers(self):
        """Get customers collection"""
        return self._news_db['customers']
    
    @property
    def users(self):
        """Get users collection"""
        return self._news_db['users']
    
    @property
    def roles(self):
        """Get roles collection"""
        return self._news_db['roles']
    
    @property
    def permissions(self):
        """Get permissions collection"""
        return self._news_db['permissions']
    
    @property
    def audit_logs(self):
        """Get audit_logs collection"""
        return self._news_db['audit_logs']
    
    @property
    def news_document(self):
        """Get news_document collection"""
        return self._news_db['news_document']
    
    @property
    def long_video_configs(self):
        """Get long_video_configs collection"""
        return self._news_db['long_video_configs']
    
    @property
    def youtube_credentials(self):
        """Get youtube_credentials collection"""
        return self._news_db['youtube_credentials']
    
    @property
    def news_seed_urls(self):
        """Get news_seed_urls collection"""
        return self._news_db['news_seed_urls']


# Global instance
def get_mongodb_client():
    """
    Get MongoDB client instance
    
    Returns:
        MongoDBClient: MongoDB client singleton
    """
    return MongoDBClient()

