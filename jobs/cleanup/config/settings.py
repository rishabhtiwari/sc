"""
Configuration settings for Cleanup Job Service
"""

import os
from enum import Enum


class JobStatus(Enum):
    """Enum for job execution status"""
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    PARTIAL_FAILURE = 'partial_failure'


class Config:
    """Configuration class for Cleanup Job Service"""

    # Flask Configuration
    FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    FLASK_PORT = int(os.getenv('FLASK_PORT', 8099))
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    FLASK_ENV = os.getenv('FLASK_ENV', 'production')

    # Job Configuration
    # Run every 1 hours by default (3600 seconds)
    JOB_INTERVAL_MINUTES = int(os.getenv('JOB_INTERVAL_MINUTES', 0))
    JOB_INTERVAL_SECONDS = int(os.getenv('JOB_INTERVAL_SECONDS', 3600))  # 6 hours
    MAX_THREADS = int(os.getenv('MAX_THREADS', '1'))

    # MongoDB Configuration
    MONGODB_HOST = os.getenv('MONGODB_HOST', 'localhost')
    MONGODB_PORT = int(os.getenv('MONGODB_PORT', 27017))
    MONGODB_DATABASE = os.getenv('MONGODB_DATABASE', 'ichat_db')
    MONGODB_USERNAME = os.getenv('MONGODB_USERNAME', 'ichat_app')
    MONGODB_PASSWORD = os.getenv('MONGODB_PASSWORD', 'ichat_app_password_2024')
    MONGODB_URL = os.getenv('MONGODB_URL',
                            f'mongodb://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@{MONGODB_HOST}:{MONGODB_PORT}/{MONGODB_DATABASE}?authSource=admin')

    # News Database Configuration
    NEWS_MONGODB_DATABASE = os.getenv('NEWS_MONGODB_DATABASE', 'news')
    NEWS_MONGODB_URL = os.getenv('NEWS_MONGODB_URL',
                                 f'mongodb://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@{MONGODB_HOST}:{MONGODB_PORT}/{NEWS_MONGODB_DATABASE}?authSource=admin')

    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/cleanup.log')
    LOG_MAX_BYTES = int(os.getenv('LOG_MAX_BYTES', 10485760))  # 10MB
    LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', 5))

    # Cleanup Configuration
    CLEANUP_RETENTION_HOURS = int(os.getenv('CLEANUP_RETENTION_HOURS', 24))  # Delete articles older than 24 hours (1 day)
    CLEANUP_DRY_RUN = os.getenv('CLEANUP_DRY_RUN', 'false').lower() == 'true'  # Dry-run mode (preview only)
    CLEANUP_BATCH_SIZE = int(os.getenv('CLEANUP_BATCH_SIZE', 100))  # Process 100 articles at a time
    CLEANUP_MAX_ARTICLES_PER_RUN = int(os.getenv('CLEANUP_MAX_ARTICLES_PER_RUN', 10000))  # Safety limit

    # File Paths Configuration
    # These paths should match the volume mounts in docker-compose.yml
    VIDEO_PUBLIC_DIR = os.getenv('VIDEO_PUBLIC_DIR', '/app/video_public')
    AUDIO_PUBLIC_DIR = os.getenv('AUDIO_PUBLIC_DIR', '/app/audio_public')
    IMAGE_PUBLIC_DIR = os.getenv('IMAGE_PUBLIC_DIR', '/app/image_public')

    @classmethod
    def validate_config(cls):
        """Validate configuration settings"""
        errors = []

        # Validate retention hours
        if cls.CLEANUP_RETENTION_HOURS < 1:
            errors.append("CLEANUP_RETENTION_HOURS must be at least 1 hour")

        # Validate batch size
        if cls.CLEANUP_BATCH_SIZE < 1:
            errors.append("CLEANUP_BATCH_SIZE must be at least 1")

        # Validate max articles per run
        if cls.CLEANUP_MAX_ARTICLES_PER_RUN < 1:
            errors.append("CLEANUP_MAX_ARTICLES_PER_RUN must be at least 1")

        if errors:
            raise ValueError(f"Configuration validation failed: {', '.join(errors)}")

        return True
