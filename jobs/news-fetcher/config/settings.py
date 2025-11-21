"""
Configuration settings for News Fetcher Job Service
"""

import os
from enum import Enum


class ArticleStatus(Enum):
    """Enum for article processing status"""
    PROGRESS = 'progress'
    COMPLETED = 'completed'
    FAILED = 'failed'


class JobStatus(Enum):
    """Enum for job execution status"""
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    PARTIAL_FAILURE = 'partial_failure'


class Config:
    """Configuration class for News Fetcher Job Service"""

    # Flask Configuration
    FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    FLASK_PORT = int(os.getenv('FLASK_PORT', 8093))
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    FLASK_ENV = os.getenv('FLASK_ENV', 'production')

    # Job Configuration
    JOB_INTERVAL_MINUTES = int(os.getenv('JOB_INTERVAL_MINUTES', 5))  # Run every 5 minutes (fallback)
    JOB_INTERVAL_SECONDS = int(os.getenv('JOB_INTERVAL_SECONDS', 0))  # Run every N seconds (takes priority)
    MAX_THREADS = int(os.getenv('MAX_THREADS', '1'))  # Threading support
    MAX_PARALLEL_TASKS = int(os.getenv('MAX_PARALLEL_TASKS', '3'))  # Parallel task support

    # MongoDB Configuration
    MONGODB_HOST = os.getenv('MONGODB_HOST', 'localhost')
    MONGODB_PORT = int(os.getenv('MONGODB_PORT', 27017))
    MONGODB_DATABASE = os.getenv('MONGODB_DATABASE', 'ichat_db')
    MONGODB_USERNAME = os.getenv('MONGODB_USERNAME', 'ichat_app')
    MONGODB_PASSWORD = os.getenv('MONGODB_PASSWORD', 'ichat_app_password_2024')
    MONGODB_URL = os.getenv('MONGODB_URL',
                            f'mongodb://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@{MONGODB_HOST}:{MONGODB_PORT}/{MONGODB_DATABASE}?authSource=admin')

    # News Database Configuration (for seed URLs)
    NEWS_MONGODB_DATABASE = os.getenv('NEWS_MONGODB_DATABASE', 'news')
    NEWS_MONGODB_URL = os.getenv('NEWS_MONGODB_URL',
                                 f'mongodb://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@{MONGODB_HOST}:{MONGODB_PORT}/{NEWS_MONGODB_DATABASE}?authSource=admin')

    # News API Configuration Parameters
    API_KEY = os.getenv('API_KEY', 'c01da20de0ad07ce5ab3b91a7603f7bb')  # GNews API key
    SUPPORTED_CATEGORY = os.getenv('SUPPORTED_CATEGORY', 'general')
    DEFAULT_LANG = os.getenv('DEFAULT_LANG', 'en')
    DEFAULT_COUNTRY = os.getenv('DEFAULT_COUNTRY', 'in')

    # HTTP Configuration
    HTTP_TIMEOUT = int(os.getenv('HTTP_TIMEOUT', 30))
    HTTP_RETRIES = int(os.getenv('HTTP_RETRIES', 3))
    HTTP_BACKOFF_FACTOR = float(os.getenv('HTTP_BACKOFF_FACTOR', 0.3))

    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/news-fetcher.log')
    LOG_MAX_BYTES = int(os.getenv('LOG_MAX_BYTES', 10485760))  # 10MB
    LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', 5))

    # News Processing Configuration
    MAX_ARTICLES_PER_FETCH = int(os.getenv('MAX_ARTICLES_PER_FETCH', 100))
    DUPLICATE_CHECK_HOURS = int(os.getenv('DUPLICATE_CHECK_HOURS', 24))

    # News API Configuration
    DEFAULT_PAGE_SIZE = int(os.getenv('DEFAULT_PAGE_SIZE', 10))
    MAX_PAGE_SIZE = int(os.getenv('MAX_PAGE_SIZE', 50))

    # Default API Filter Values
    DEFAULT_FILTER_CATEGORY = os.getenv('DEFAULT_FILTER_CATEGORY', 'general')
    DEFAULT_FILTER_LANGUAGE = os.getenv('DEFAULT_FILTER_LANGUAGE', 'en')
    DEFAULT_FILTER_COUNTRY = os.getenv('DEFAULT_FILTER_COUNTRY', 'in')

    # LLM Service Configuration - Direct service communication
    LLM_SERVICE_URL = os.getenv('LLM_SERVICE_URL', 'http://ichat-llm-service:8083')
    LLM_TIMEOUT = int(os.getenv('LLM_TIMEOUT', 30))

    @classmethod
    def validate_config(cls):
        """Validate required configuration"""
        required_configs = []

        if not cls.API_KEY:
            required_configs.append('API_KEY')

        if required_configs:
            raise ValueError(f"Missing required configuration: {', '.join(required_configs)}")

    @classmethod
    def get_default_params(cls):
        """Get default news API parameters"""
        return {
            'api_key': cls.API_KEY,
            'category': cls.SUPPORTED_CATEGORY,
            'lang': cls.DEFAULT_LANG,
            'country': cls.DEFAULT_COUNTRY
        }
