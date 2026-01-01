"""
Asset Service Configuration
"""
import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "Asset Service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8099
    
    # MongoDB
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://ichat-mongodb:27017/")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "ichat_db")
    
    # MinIO
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "minio:9000")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    MINIO_SECURE: bool = os.getenv("MINIO_SECURE", "false").lower() == "true"
    MINIO_REGION: str = os.getenv("MINIO_REGION", "us-east-1")
    
    # Buckets
    AUDIO_BUCKET: str = "audio-assets"
    IMAGE_BUCKET: str = "image-assets"
    VIDEO_BUCKET: str = "video-assets"
    DOCUMENT_BUCKET: str = "document-assets"
    TEMP_BUCKET: str = "temp-uploads"
    
    # JWT Authentication
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:3003",
    ]
    
    # File Upload Limits
    MAX_UPLOAD_SIZE: int = 500 * 1024 * 1024  # 500MB
    CHUNK_SIZE: int = 5 * 1024 * 1024  # 5MB chunks
    
    # Allowed File Types
    ALLOWED_AUDIO_TYPES: List[str] = [
        "audio/wav", "audio/mpeg", "audio/mp3", 
        "audio/ogg", "audio/flac", "audio/x-wav"
    ]
    ALLOWED_IMAGE_TYPES: List[str] = [
        "image/png", "image/jpeg", "image/jpg",
        "image/webp", "image/svg+xml"
    ]
    ALLOWED_VIDEO_TYPES: List[str] = [
        "video/mp4", "video/webm", "video/avi",
        "video/quicktime"
    ]
    ALLOWED_DOCUMENT_TYPES: List[str] = [
        "application/pdf", "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain"
    ]
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "json"
    
    # Temp Directory
    TEMP_DIR: str = "/app/temp"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()

