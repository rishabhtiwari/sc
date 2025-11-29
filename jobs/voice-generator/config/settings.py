"""
Voice Generator Job Configuration
"""

import os
from typing import List


class Config:
    """Configuration class for Voice Generator Job"""
    
    # Job Configuration
    JOB_NAME = 'voice-generator'
    JOB_INTERVAL_MINUTES = int(os.getenv('JOB_FREQUENCY_MINUTES', 30))  # Run every 30 minutes
    JOB_INTERVAL_SECONDS = int(os.getenv('JOB_INTERVAL_SECONDS', 0))   # Override with seconds if needed
    
    # Threading Configuration
    MAX_THREADS = int(os.getenv('MAX_THREADS', 1))
    MAX_PARALLEL_TASKS = int(os.getenv('MAX_PARALLEL_TASKS', 2))
    
    # Audio Generation Service Configuration
    AUDIO_GENERATION_SERVICE_URL = os.getenv('AUDIO_GENERATION_SERVICE_URL', 'http://audio-generation-factory:3000')
    AUDIO_GENERATION_TIMEOUT = int(os.getenv('AUDIO_GENERATION_TIMEOUT', 120))  # 2 minutes timeout
    
    # File Storage Configuration
    DATA_DIR = os.getenv('DATA_DIR', '/app/data')
    MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE_MB', 50))
    
    # Database Configuration - Main ichat database
    MONGODB_HOST = os.getenv('MONGODB_HOST', 'localhost')
    MONGODB_PORT = int(os.getenv('MONGODB_PORT', 27017))
    MONGODB_DATABASE = os.getenv('MONGODB_DATABASE', 'ichat_db')
    MONGODB_USERNAME = os.getenv('MONGODB_USERNAME', 'ichat_app')
    MONGODB_PASSWORD = os.getenv('MONGODB_PASSWORD', 'ichat_app_password_2024')
    MONGODB_URL = os.getenv('MONGODB_URL', f'mongodb://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@{MONGODB_HOST}:{MONGODB_PORT}/{MONGODB_DATABASE}?authSource=admin')
    
    # News Database Configuration - Separate news database
    NEWS_MONGODB_DATABASE = os.getenv('NEWS_MONGODB_DATABASE', 'news')
    NEWS_MONGODB_URL = os.getenv('NEWS_MONGODB_URL', f'mongodb://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@{MONGODB_HOST}:{MONGODB_PORT}/{NEWS_MONGODB_DATABASE}?authSource=admin')
    
    # Audio Generation Configuration
    DEFAULT_AUDIO_MODEL = os.getenv('DEFAULT_AUDIO_MODEL', 'kokoro-82m')  # Default to Kokoro-82M for English
    HINDI_AUDIO_MODEL = os.getenv('HINDI_AUDIO_MODEL', 'mms-tts-hin')     # Hindi model
    AUDIO_BATCH_SIZE = int(os.getenv('AUDIO_BATCH_SIZE', 5))              # Process 5 articles at a time
    AUDIO_GENERATION_DELAY = int(os.getenv('AUDIO_GENERATION_DELAY', 2))  # Delay between generations (seconds)

    # Voice/Anchor Configuration for Kokoro-82M model
    # Male voices: am_adam, am_michael, bm_george, bm_lewis
    # Female voices: af_bella, af_nicole, af_sarah, af_sky, bf_emma, bf_isabella
    MALE_VOICES = os.getenv('MALE_VOICES', 'am_adam,am_michael').split(',')  # Default male voices
    FEMALE_VOICES = os.getenv('FEMALE_VOICES', 'af_bella,af_sarah').split(',')  # Default female voices
    DEFAULT_MALE_VOICE = os.getenv('DEFAULT_MALE_VOICE', 'am_adam')  # Default male anchor voice
    DEFAULT_FEMALE_VOICE = os.getenv('DEFAULT_FEMALE_VOICE', 'af_bella')  # Default female anchor voice
    ENABLE_VOICE_ALTERNATION = os.getenv('ENABLE_VOICE_ALTERNATION', 'true').lower() == 'true'  # Enable alternating voices
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/voice-generator.log')
    
    # Health Check Configuration
    HEALTH_CHECK_PORT = int(os.getenv('HEALTH_CHECK_PORT', 8094))
    
    @classmethod
    def validate_config(cls) -> List[str]:
        """
        Validate configuration settings
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Validate required URLs
        if not cls.AUDIO_GENERATION_SERVICE_URL:
            errors.append("AUDIO_GENERATION_SERVICE_URL is required")
        
        if not cls.MONGODB_URL:
            errors.append("MONGODB_URL is required")
            
        if not cls.NEWS_MONGODB_URL:
            errors.append("NEWS_MONGODB_URL is required")
        
        # Validate numeric values
        if cls.JOB_INTERVAL_MINUTES <= 0 and cls.JOB_INTERVAL_SECONDS <= 0:
            errors.append("Either JOB_INTERVAL_MINUTES or JOB_INTERVAL_SECONDS must be > 0")
        
        if cls.MAX_THREADS <= 0:
            errors.append("MAX_THREADS must be > 0")
            
        if cls.MAX_PARALLEL_TASKS <= 0:
            errors.append("MAX_PARALLEL_TASKS must be > 0")
            
        if cls.AUDIO_GENERATION_TIMEOUT <= 0:
            errors.append("AUDIO_GENERATION_TIMEOUT must be > 0")

        if cls.AUDIO_BATCH_SIZE <= 0:
            errors.append("AUDIO_BATCH_SIZE must be > 0")
        
        # Validate directories
        if not cls.DATA_DIR:
            errors.append("DATA_DIR is required")
        
        return errors
