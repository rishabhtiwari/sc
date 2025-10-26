"""
Voice Generator Job Configuration
"""

import os
from datetime import timedelta

class Config:
    """Configuration class for Voice Generator Job"""
    
    # Basic Configuration
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 8094))

    # Flask Configuration (required by BaseJob)
    FLASK_HOST = os.environ.get('FLASK_HOST', '0.0.0.0')
    FLASK_PORT = int(os.environ.get('FLASK_PORT', 8094))
    FLASK_DEBUG = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    
    # Job Configuration
    JOB_NAME = 'voice-generator'
    JOB_INTERVAL_MINUTES = int(os.environ.get('JOB_FREQUENCY_MINUTES', 5))  # Check for new requests every 5 minutes
    JOB_INTERVAL_SECONDS = int(os.environ.get('JOB_INTERVAL_SECONDS', 0))  # Use minutes by default
    MAX_THREADS = int(os.environ.get('MAX_THREADS', 1))  # Voice generation is resource intensive
    MAX_PARALLEL_TASKS = int(os.environ.get('MAX_PARALLEL_TASKS', 2))  # Limit parallel voice generations
    
    # Voice Generation Configuration
    VOICE_SERVICE_URL = os.environ.get('VOICE_SERVICE_URL', 'http://voice-cloning-service:5003')
    VOICE_SERVICE_TIMEOUT = int(os.environ.get('VOICE_SERVICE_TIMEOUT', 10800))  # 3 hours
    DEFAULT_LANGUAGE = os.environ.get('DEFAULT_LANGUAGE', 'en')
    MAX_TEXT_LENGTH = int(os.environ.get('MAX_TEXT_LENGTH', 2000))  # XTTS can handle longer text
    
    # File Storage Configuration
    DATA_DIR = os.environ.get('DATA_DIR', '/app/data')
    REFERENCE_AUDIO_DIR = os.path.join(DATA_DIR, 'reference_audio')
    GENERATED_AUDIO_DIR = os.path.join(DATA_DIR, 'generated_audio')
    MAX_FILE_SIZE_MB = int(os.environ.get('MAX_FILE_SIZE_MB', 50))  # Max reference audio file size
    ALLOWED_AUDIO_EXTENSIONS = {'wav', 'mp3', 'flac', 'm4a', 'ogg'}
    
    # Database Configuration
    MONGODB_HOST = os.environ.get('MONGODB_HOST', 'ichat-mongodb')
    MONGODB_PORT = int(os.environ.get('MONGODB_PORT', 27017))
    MONGODB_DATABASE = os.environ.get('MONGODB_DATABASE', 'ichat_db')
    MONGODB_USERNAME = os.environ.get('MONGODB_USERNAME', 'ichat_app')
    MONGODB_PASSWORD = os.environ.get('MONGODB_PASSWORD', 'ichat_app_password_2024')
    MONGODB_URL = os.environ.get('MONGODB_URL', f'mongodb://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@{MONGODB_HOST}:{MONGODB_PORT}/{MONGODB_DATABASE}?authSource=admin')
    
    # Logging Configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'logs/voice-generator.log')
    
    # Health Check Configuration
    HEALTH_CHECK_PORT = int(os.environ.get('HEALTH_CHECK_PORT', PORT))
    
    @classmethod
    def validate_config(cls):
        """Validate configuration settings"""
        errors = []
        
        # Validate required directories
        required_dirs = [cls.DATA_DIR, cls.REFERENCE_AUDIO_DIR, cls.GENERATED_AUDIO_DIR]
        for dir_path in required_dirs:
            if not os.path.exists(dir_path):
                try:
                    os.makedirs(dir_path, exist_ok=True)
                except Exception as e:
                    errors.append(f"Cannot create directory {dir_path}: {e}")
        
        # Validate MongoDB connection string
        if not cls.MONGODB_URL:
            errors.append("MONGODB_URL is required")

        # Validate Voice Service URL
        if not cls.VOICE_SERVICE_URL:
            errors.append("VOICE_SERVICE_URL is required")

        # Validate timeout values
        if cls.VOICE_SERVICE_TIMEOUT <= 0:
            errors.append("VOICE_SERVICE_TIMEOUT must be positive")

        # Validate file size limits
        if cls.MAX_FILE_SIZE_MB <= 0:
            errors.append("MAX_FILE_SIZE_MB must be positive")
        
        if errors:
            raise ValueError(f"Configuration validation failed: {', '.join(errors)}")
        
        return True
