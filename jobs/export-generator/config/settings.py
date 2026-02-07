"""
Configuration settings for the Export Generation Job Service
"""
import os


class Config:
    """Configuration class for export generation job service"""

    # Service Configuration
    SERVICE_NAME = "Export Generation Job Service"
    SERVICE_VERSION = "1.0.0"
    SERVICE_DESCRIPTION = "Export generation service for Design Editor projects"

    # Server Configuration
    HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    PORT = int(os.getenv('FLASK_PORT', 8101))
    DEBUG = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'

    # BaseJob expects these Flask attributes
    FLASK_HOST = HOST
    FLASK_PORT = PORT
    FLASK_DEBUG = DEBUG

    # Environment
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'production')

    # MongoDB Configuration
    MONGODB_HOST = os.getenv('MONGODB_HOST', 'localhost')
    MONGODB_PORT = int(os.getenv('MONGODB_PORT', 27017))
    MONGODB_USERNAME = os.getenv('MONGODB_USERNAME', 'ichat_app')
    MONGODB_PASSWORD = os.getenv('MONGODB_PASSWORD', 'ichat_app_password_2024')
    MONGODB_DATABASE = os.getenv('MONGODB_DATABASE', 'ichat_db')
    MONGODB_URI = os.getenv('MONGODB_URL', f'mongodb://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@{MONGODB_HOST}:{MONGODB_PORT}/{MONGODB_DATABASE}?authSource=admin')
    MONGODB_URL = MONGODB_URI  # Alias for compatibility

    # News Database Configuration (for video/audio library)
    NEWS_MONGODB_DATABASE = os.getenv('NEWS_MONGODB_DATABASE', 'news')
    NEWS_MONGODB_URL = os.getenv('NEWS_MONGODB_URL', f'mongodb://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@{MONGODB_HOST}:{MONGODB_PORT}/{NEWS_MONGODB_DATABASE}?authSource=admin')

    # Job Configuration
    JOB_INTERVAL_MINUTES = int(os.getenv('JOB_INTERVAL_MINUTES', 0))  # 0 = no scheduled runs, only on-demand
    MAX_THREADS = int(os.getenv('MAX_THREADS', 2))
    MAX_PARALLEL_TASKS = int(os.getenv('MAX_PARALLEL_TASKS', 3))

    # Export Configuration
    EXPORT_OUTPUT_DIR = os.getenv('EXPORT_OUTPUT_DIR', '/app/exports')
    TEMP_DIR = os.getenv('TEMP_DIR', '/app/temp')
    MAX_EXPORT_DURATION = int(os.getenv('MAX_EXPORT_DURATION', 600))  # 10 minutes max

    # Video Specifications
    VIDEO_WIDTH = int(os.getenv('VIDEO_WIDTH', 1920))
    VIDEO_HEIGHT = int(os.getenv('VIDEO_HEIGHT', 1080))
    VIDEO_FPS = int(os.getenv('VIDEO_FPS', 30))
    VIDEO_CODEC = os.getenv('VIDEO_CODEC', 'libx264')
    AUDIO_CODEC = os.getenv('AUDIO_CODEC', 'aac')

    # FFmpeg Configuration
    FFMPEG_PATH = os.getenv('FFMPEG_PATH', '/usr/bin/ffmpeg')
    FFPROBE_PATH = os.getenv('FFPROBE_PATH', '/usr/bin/ffprobe')

    # MinIO Configuration
    MINIO_ENDPOINT = os.getenv('MINIO_ENDPOINT', 'localhost:9000')
    MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
    MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY', 'minioadmin')
    MINIO_SECURE = os.getenv('MINIO_SECURE', 'false').lower() == 'true'
    MINIO_BUCKET_EXPORTS = os.getenv('MINIO_BUCKET_EXPORTS', 'exported-videos')

    # Processing Configuration
    PROCESSING_TIMEOUT = int(os.getenv('PROCESSING_TIMEOUT', 600))  # 10 minutes per export

    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FILE = os.getenv('LOG_FILE', '/app/logs/export-generator.log')

    # Request Timeouts
    HTTP_TIMEOUT = int(os.getenv('HTTP_TIMEOUT', 30))

    # Asset Service Configuration
    # Note: Asset service handles /api/audio-studio/* and /api/assets/* endpoints
    ASSET_SERVICE_URL = os.getenv('ASSET_SERVICE_URL', 'http://ichat-asset-service:8099')

    @classmethod
    def validate_config(cls):
        """Validate configuration settings"""
        errors = []

        # Validate MongoDB connection
        if not cls.MONGODB_URI:
            errors.append("MONGODB_URI is not configured")

        # Validate MinIO configuration
        if not cls.MINIO_ENDPOINT:
            errors.append("MINIO_ENDPOINT is not configured")

        if not cls.MINIO_ACCESS_KEY or not cls.MINIO_SECRET_KEY:
            errors.append("MinIO credentials are not configured")

        # Validate directories
        if not cls.TEMP_DIR:
            errors.append("TEMP_DIR is not configured")

        if errors:
            raise ValueError(f"Configuration validation failed: {', '.join(errors)}")

        return True


# Create a singleton instance
config = Config()

