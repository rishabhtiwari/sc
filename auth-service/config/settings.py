"""
Auth Service Configuration
"""

import os


class Settings:
    """Configuration settings for auth service"""
    
    # Service Configuration
    SERVICE_NAME = 'auth-service'
    PORT = int(os.getenv('FLASK_PORT', 8098))
    SERVICE_HOST = os.getenv('SERVICE_HOST', '0.0.0.0')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # MongoDB Configuration
    MONGODB_HOST = os.getenv('MONGODB_HOST', 'ichat-mongodb')
    MONGODB_PORT = int(os.getenv('MONGODB_PORT', 27017))
    MONGODB_USERNAME = os.getenv('MONGODB_USERNAME', 'ichat_app')
    MONGODB_PASSWORD = os.getenv('MONGODB_PASSWORD', 'ichat_app_password_2024')
    MONGODB_DATABASE = 'news'
    MONGODB_URL = f'mongodb://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@{MONGODB_HOST}:{MONGODB_PORT}/?authSource=admin'
    
    # JWT Configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production-please')
    JWT_ALGORITHM = 'HS256'
    JWT_EXPIRATION_HOURS = int(os.getenv('JWT_EXPIRATION_HOURS', 24))
    
    # Password Configuration
    BCRYPT_ROUNDS = 12
    PASSWORD_MIN_LENGTH = 8
    
    # Pagination
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100
    
    # Account Lockout
    MAX_FAILED_LOGIN_ATTEMPTS = 5
    ACCOUNT_LOCKOUT_DURATION_MINUTES = 30
    
    # Email Verification
    EMAIL_VERIFICATION_TOKEN_EXPIRATION_HOURS = 24
    PASSWORD_RESET_TOKEN_EXPIRATION_HOURS = 2
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = 'logs/auth-service.log'


# Global settings instance
settings = Settings()

