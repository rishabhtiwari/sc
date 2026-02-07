"""
Social Media Uploader Service Configuration
Supports YouTube, Instagram, TikTok, Twitter, LinkedIn, Facebook, Reddit
"""
import os


class Config:
    """Configuration for Social Media Uploader Service"""
    
    # Flask Configuration
    FLASK_PORT = int(os.getenv('FLASK_PORT', 8097))
    FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
    
    # MongoDB Configuration
    MONGODB_URL = os.getenv('MONGODB_URL', 'mongodb://ichat_app:ichat_app_password_2024@ichat-mongodb:27017/news?authSource=admin')
    MONGODB_DATABASE = os.getenv('MONGODB_DATABASE', 'news')
    MONGODB_COLLECTION = os.getenv('MONGODB_COLLECTION', 'news_document')

    # LLM Service Configuration
    LLM_SERVICE_URL = os.getenv('LLM_SERVICE_URL', 'http://ichat-llm-service:8083')
    
    # YouTube API Configuration
    YOUTUBE_CLIENT_SECRETS_FILE = os.getenv('YOUTUBE_CLIENT_SECRETS_FILE', '/app/credentials/client_secrets.json')
    YOUTUBE_CREDENTIALS_FILE = os.getenv('YOUTUBE_CREDENTIALS_FILE', '/app/credentials/youtube_credentials.json')
    YOUTUBE_API_SERVICE_NAME = 'youtube'
    YOUTUBE_API_VERSION = 'v3'
    YOUTUBE_SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
    
    # Video Upload Configuration
    VIDEO_BASE_PATH = os.getenv('VIDEO_BASE_PATH', '/app/public')
    DEFAULT_CATEGORY_ID = os.getenv('DEFAULT_CATEGORY_ID', '25')  # News & Politics
    DEFAULT_PRIVACY_STATUS = os.getenv('DEFAULT_PRIVACY_STATUS', 'private')  # public, private, unlisted
    
    # Upload Settings
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', 5))  # Increased from 3 to 5 for better reliability
    CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', 10 * 1024 * 1024))  # 10MB chunks (increased from 1MB for better performance)
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FILE = os.getenv('LOG_FILE', '/app/logs/youtube-uploader.log')
    
    # Default Tags
    DEFAULT_TAGS = os.getenv('DEFAULT_TAGS', 'news,hindi news,breaking news,latest news').split(',')

    # Instagram API Configuration (Default values - actual credentials come from Master App in DB)
    # OAuth callback goes through API server (port 8080), not directly to this service
    INSTAGRAM_REDIRECT_URI = os.getenv('INSTAGRAM_REDIRECT_URI', 'http://localhost:8080/api/social-media/instagram/oauth/callback')
    INSTAGRAM_SCOPES = ['pages_show_list', 'instagram_basic', 'instagram_content_publish', 'pages_read_engagement']

