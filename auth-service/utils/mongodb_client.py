"""
MongoDB Client Utility
Provides MongoDB connection and database access
"""

import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from config.settings import settings

logger = logging.getLogger(__name__)


class MongoDBClient:
    """MongoDB client singleton for managing database connections"""
    
    _instance = None
    _client = None
    _db = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDBClient, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize MongoDB connection"""
        try:
            # Create MongoDB client
            self._client = MongoClient(settings.MONGODB_URL)
            
            # Test connection
            self._client.admin.command('ping')
            logger.info(f"✅ Connected to MongoDB at {settings.MONGODB_HOST}:{settings.MONGODB_PORT}")
            
            # Get news database
            self._db = self._client[settings.MONGODB_DATABASE]
            
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
    def db(self):
        """Get database"""
        return self._db
    
    # Collection accessors
    @property
    def customers(self):
        """Get customers collection"""
        return self._db['customers']
    
    @property
    def users(self):
        """Get users collection"""
        return self._db['users']
    
    @property
    def roles(self):
        """Get roles collection"""
        return self._db['roles']
    
    @property
    def permissions(self):
        """Get permissions collection"""
        return self._db['permissions']
    
    @property
    def audit_logs(self):
        """Get audit_logs collection"""
        return self._db['audit_logs']


# Global instance
_mongodb_client = None


def get_mongodb_client():
    """Get MongoDB client instance"""
    global _mongodb_client
    if _mongodb_client is None:
        _mongodb_client = MongoDBClient()
    return _mongodb_client

