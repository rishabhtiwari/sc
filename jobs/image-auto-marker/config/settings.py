"""
Configuration settings for Image Auto-Marker Job
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Configuration class for Image Auto-Marker Job"""
    
    # Job Configuration
    JOB_NAME = 'image-auto-marker'
    JOB_INTERVAL_MINUTES = int(os.getenv('JOB_INTERVAL_MINUTES', 5))  # Run every 5 minutes
    JOB_INTERVAL_SECONDS = int(os.getenv('JOB_INTERVAL_SECONDS', 0))  # Override with seconds if needed
    
    # Threading Configuration
    MAX_THREADS = int(os.getenv('MAX_THREADS', 1))
    MAX_PARALLEL_TASKS = int(os.getenv('MAX_PARALLEL_TASKS', 1))
    
    # MongoDB Configuration
    MONGODB_URL = os.getenv('MONGODB_URL', 'mongodb://ichat-mongodb:27017/news')
    
    # Batch Processing
    BATCH_SIZE = int(os.getenv('AUTO_MARK_BATCH_SIZE', 50))  # Process 50 images per run

    # Output Directory (where cleaned images are saved)
    OUTPUT_DIR = os.getenv('OUTPUT_DIR', '/app/output')

    # Flask Configuration
    FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    FLASK_PORT = int(os.getenv('FLASK_PORT', 8102))
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    
    # Logging
    LOG_FILE = os.getenv('LOG_FILE', '/var/log/image-auto-marker.log')
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    @staticmethod
    def validate_config():
        """Validate configuration settings"""
        errors = []
        
        if not Config.MONGODB_URL:
            errors.append("MONGODB_URL is required")
        
        if Config.JOB_INTERVAL_MINUTES <= 0 and Config.JOB_INTERVAL_SECONDS <= 0:
            errors.append("JOB_INTERVAL_MINUTES or JOB_INTERVAL_SECONDS must be > 0")
        
        if Config.BATCH_SIZE <= 0:
            errors.append("BATCH_SIZE must be > 0")
        
        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")
        
        return True


class JobStatus:
    """Job status constants"""
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'

