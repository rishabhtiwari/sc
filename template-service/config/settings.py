"""
Configuration settings for the Template Service
"""
import os


class Config:
    """Configuration class for template service"""

    # Service Configuration
    SERVICE_NAME = "Template Service"
    SERVICE_VERSION = "1.0.0"
    SERVICE_DESCRIPTION = "Video template management and resolution service"

    # Server Configuration
    HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    PORT = int(os.getenv('FLASK_PORT', 5000))
    DEBUG = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'

    # Environment
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'production')

    # MongoDB Configuration
    MONGODB_HOST = os.getenv('MONGODB_HOST', 'localhost')
    MONGODB_PORT = int(os.getenv('MONGODB_PORT', 27017))
    MONGODB_DATABASE = os.getenv('MONGODB_DATABASE', 'news')
    MONGODB_USERNAME = os.getenv('MONGODB_USERNAME', 'ichat_app')
    MONGODB_PASSWORD = os.getenv('MONGODB_PASSWORD', 'ichat_app_password_2024')
    MONGODB_URI = os.getenv('MONGODB_URI', f'mongodb://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@{MONGODB_HOST}:{MONGODB_PORT}/{MONGODB_DATABASE}?authSource=admin')
    MONGODB_URL = os.getenv('MONGODB_URL', MONGODB_URI)

    # Template Configuration
    TEMPLATE_DIR = os.getenv('TEMPLATE_DIR', '/app/templates')
    TEMPLATE_CACHE_ENABLED = os.getenv('TEMPLATE_CACHE_ENABLED', 'true').lower() == 'true'
    TEMPLATE_CACHE_TTL = int(os.getenv('TEMPLATE_CACHE_TTL', 300))  # 5 minutes

    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', '/app/logs/template-service.log')

    # CORS Configuration
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*')

    # Default Template Settings
    DEFAULT_LONG_VIDEO_TEMPLATE = os.getenv('DEFAULT_LONG_VIDEO_TEMPLATE', 'modern_news_v1')
    DEFAULT_SHORTS_TEMPLATE = os.getenv('DEFAULT_SHORTS_TEMPLATE', 'vertical_overlay_v1')
    DEFAULT_PRODUCT_TEMPLATE = os.getenv('DEFAULT_PRODUCT_TEMPLATE', 'product_showcase_v1')

    # Video Specifications (for validation)
    LONG_VIDEO_WIDTH = 1920
    LONG_VIDEO_HEIGHT = 1080
    SHORTS_VIDEO_WIDTH = 1080
    SHORTS_VIDEO_HEIGHT = 1920

    @classmethod
    def get_template_path(cls, category: str, template_id: str) -> str:
        """Get full path to template file"""
        return os.path.join(cls.TEMPLATE_DIR, category, f"{template_id}.json")

    @classmethod
    def validate(cls):
        """Validate configuration"""
        errors = []

        # Check template directory exists
        if not os.path.exists(cls.TEMPLATE_DIR):
            errors.append(f"Template directory does not exist: {cls.TEMPLATE_DIR}")

        # Check MongoDB connection string
        if not cls.MONGODB_URL:
            errors.append("MongoDB URL is not configured")

        if errors:
            raise ValueError(f"Configuration errors: {'; '.join(errors)}")

        return True

