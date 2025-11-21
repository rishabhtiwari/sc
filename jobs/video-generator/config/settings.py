"""
Configuration settings for the Video Generation Job Service
"""
import os
from typing import Dict, Any


class Config:
    """Configuration class for video generation job service"""

    # Service Configuration
    SERVICE_NAME = "Video Generation Job Service"
    SERVICE_VERSION = "1.0.0"
    SERVICE_DESCRIPTION = "Video generation service for news articles with audio and background images"

    # Server Configuration
    HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    PORT = int(os.getenv('FLASK_PORT', 8095))
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
    MONGODB_DATABASE = os.getenv('MONGODB_DATABASE', 'ichat_db')
    MONGODB_USERNAME = os.getenv('MONGODB_USERNAME', 'ichat_app')
    MONGODB_PASSWORD = os.getenv('MONGODB_PASSWORD', 'ichat_app_password_2024')
    MONGODB_URI = os.getenv('MONGODB_URI', f'mongodb://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@{MONGODB_HOST}:{MONGODB_PORT}/{MONGODB_DATABASE}?authSource=admin')
    MONGODB_URL = os.getenv('MONGODB_URL', MONGODB_URI)  # Use environment variable or fallback to URI

    # News Database Configuration
    NEWS_MONGODB_DATABASE = os.getenv('NEWS_MONGODB_DATABASE', 'news')
    NEWS_MONGODB_URL = os.getenv('NEWS_MONGODB_URL', f'mongodb://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@{MONGODB_HOST}:{MONGODB_PORT}/{NEWS_MONGODB_DATABASE}?authSource=admin')

    # Job Configuration
    JOB_INTERVAL_MINUTES = int(os.getenv('JOB_INTERVAL_MINUTES', 5))  # Run every 5 minutes
    MAX_THREADS = int(os.getenv('MAX_THREADS', 2))
    MAX_PARALLEL_TASKS = int(os.getenv('MAX_PARALLEL_TASKS', 3))

    # Video Generation Configuration
    VIDEO_OUTPUT_DIR = os.getenv('VIDEO_OUTPUT_DIR', '/app/public')
    TEMP_DIR = os.getenv('TEMP_DIR', '/app/temp')
    MAX_VIDEO_DURATION = int(os.getenv('MAX_VIDEO_DURATION', 300))  # 5 minutes max
    VIDEO_QUALITY = os.getenv('VIDEO_QUALITY', 'high')  # high, medium, low
    
    # Video Specifications
    VIDEO_WIDTH = int(os.getenv('VIDEO_WIDTH', 1920))
    VIDEO_HEIGHT = int(os.getenv('VIDEO_HEIGHT', 1080))
    VIDEO_FPS = int(os.getenv('VIDEO_FPS', 30))
    VIDEO_CODEC = os.getenv('VIDEO_CODEC', 'libx264')
    AUDIO_CODEC = os.getenv('AUDIO_CODEC', 'aac')
    
    # FFmpeg Configuration
    FFMPEG_PATH = os.getenv('FFMPEG_PATH', '/usr/bin/ffmpeg')
    FFPROBE_PATH = os.getenv('FFPROBE_PATH', '/usr/bin/ffprobe')
    
    # Image Processing Configuration
    IMAGE_DOWNLOAD_TIMEOUT = int(os.getenv('IMAGE_DOWNLOAD_TIMEOUT', 30))  # seconds
    MAX_IMAGE_SIZE_MB = int(os.getenv('MAX_IMAGE_SIZE_MB', 10))
    SUPPORTED_IMAGE_FORMATS = ['jpg', 'jpeg', 'png', 'webp', 'bmp']
    
    # Text Overlay Configuration
    TITLE_FONT_SIZE = int(os.getenv('TITLE_FONT_SIZE', 48))
    DESCRIPTION_FONT_SIZE = int(os.getenv('DESCRIPTION_FONT_SIZE', 24))
    TEXT_COLOR = os.getenv('TEXT_COLOR', 'white')
    TEXT_BACKGROUND_COLOR = os.getenv('TEXT_BACKGROUND_COLOR', 'rgba(0,0,0,0.7)')

    # Effects Configuration
    ENABLE_KEN_BURNS = os.getenv('ENABLE_KEN_BURNS', 'true').lower() == 'true'
    KEN_BURNS_ZOOM_START = float(os.getenv('KEN_BURNS_ZOOM_START', 1.0))
    KEN_BURNS_ZOOM_END = float(os.getenv('KEN_BURNS_ZOOM_END', 1.2))
    KEN_BURNS_EASING = os.getenv('KEN_BURNS_EASING', 'ease_in_out')  # linear, ease_in, ease_out, ease_in_out

    # Fade Text Effect Configuration
    ENABLE_FADE_TEXT = os.getenv('ENABLE_FADE_TEXT', 'true').lower() == 'true'
    FADE_TEXT_IN_DURATION = float(os.getenv('FADE_TEXT_IN_DURATION', 0.5))
    FADE_TEXT_OUT_DURATION = float(os.getenv('FADE_TEXT_OUT_DURATION', 0.5))
    FADE_TEXT_TYPE = os.getenv('FADE_TEXT_TYPE', 'both')  # both, in, out

    # Logo Watermark Effect Configuration
    ENABLE_LOGO_WATERMARK = os.getenv('ENABLE_LOGO_WATERMARK', 'true').lower() == 'true'
    LOGO_PATH = os.getenv('LOGO_PATH', '/app/assets/logo.png')
    LOGO_POSITION = os.getenv('LOGO_POSITION', 'top-right')  # top-left, top-right, bottom-left, bottom-right, center
    LOGO_OPACITY = float(os.getenv('LOGO_OPACITY', 0.9))  # 0.0 to 1.0
    LOGO_SCALE = float(os.getenv('LOGO_SCALE', 0.12))  # Relative to video width (0.12 = 12% of video width)
    LOGO_MARGIN = int(os.getenv('LOGO_MARGIN', 30))  # Margin from edges in pixels

    # Processing Configuration
    BATCH_SIZE = int(os.getenv('BATCH_SIZE', 5))  # Process 5 videos at a time
    PROCESSING_TIMEOUT = int(os.getenv('PROCESSING_TIMEOUT', 600))  # 10 minutes per video
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FILE = os.getenv('LOG_FILE', '/app/logs/video-generator.log')

    # Request Timeouts
    HTTP_TIMEOUT = int(os.getenv('HTTP_TIMEOUT', 30))
    
    @classmethod
    def validate_config(cls):
        """Validate configuration settings"""
        errors = []
        
        # Check required directories
        required_dirs = [cls.VIDEO_OUTPUT_DIR, cls.TEMP_DIR]
        for dir_path in required_dirs:
            if not os.path.exists(dir_path):
                try:
                    os.makedirs(dir_path, exist_ok=True)
                except Exception as e:
                    errors.append(f"Cannot create directory {dir_path}: {str(e)}")
        
        # Check FFmpeg installation
        if not os.path.exists(cls.FFMPEG_PATH):
            errors.append(f"FFmpeg not found at {cls.FFMPEG_PATH}")
            
        # Validate video dimensions
        if cls.VIDEO_WIDTH <= 0 or cls.VIDEO_HEIGHT <= 0:
            errors.append("Video dimensions must be positive integers")
            
        # Validate FPS
        if cls.VIDEO_FPS <= 0 or cls.VIDEO_FPS > 60:
            errors.append("Video FPS must be between 1 and 60")
        
        if errors:
            raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")
        
        return True

    @classmethod
    def get_video_quality_settings(cls) -> Dict[str, Any]:
        """Get video quality settings based on configured quality level"""
        quality_settings = {
            'high': {
                'crf': 18,  # Constant Rate Factor (lower = better quality)
                'preset': 'medium',
                'bitrate': '5000k'
            },
            'medium': {
                'crf': 23,
                'preset': 'fast',
                'bitrate': '2500k'
            },
            'low': {
                'crf': 28,
                'preset': 'faster',
                'bitrate': '1000k'
            }
        }
        
        return quality_settings.get(cls.VIDEO_QUALITY.lower(), quality_settings['medium'])
