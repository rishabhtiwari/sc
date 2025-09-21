"""
OCR Service Configuration
"""

import os


class OCRConfig:
    """
    Base configuration class for OCR service
    """
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'ocr-secret-key-change-in-production'
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Server settings
    HOST = os.environ.get('FLASK_HOST', '0.0.0.0')
    PORT = int(os.environ.get('FLASK_PORT', 8081))
    
    # OCR settings
    OCR_LANGUAGE = os.environ.get('OCR_DEFAULT_LANGUAGE', 'en')
    OCR_USE_GPU = os.environ.get('OCR_USE_GPU', 'False').lower() == 'true'
    OCR_USE_ANGLE_CLS = os.environ.get('OCR_USE_ANGLE_CLS', 'True').lower() == 'true'
    
    # File upload settings
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_FILE_SIZE', 10 * 1024 * 1024))  # 10MB
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', '/app/uploads')
    OUTPUT_FOLDER = os.environ.get('OUTPUT_FOLDER', '/app/outputs')
    
    # Supported file extensions
    ALLOWED_EXTENSIONS = {
        'images': {'png', 'jpg', 'jpeg', 'bmp', 'tiff', 'webp'},
        'documents': {'pdf', 'docx'}
    }
    
    # OCR processing settings
    OCR_CONFIDENCE_THRESHOLD = float(os.environ.get('OCR_CONFIDENCE_THRESHOLD', 0.5))
    OCR_MAX_WORKERS = int(os.environ.get('OCR_MAX_WORKERS', 2))
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')


class DevelopmentConfig(OCRConfig):
    """
    Development configuration
    """
    DEBUG = True
    OCR_USE_GPU = False  # Usually no GPU in dev


class ProductionConfig(OCRConfig):
    """
    Production configuration
    """
    DEBUG = False
    OCR_USE_GPU = True  # Enable GPU if available


class TestingConfig(OCRConfig):
    """
    Testing configuration
    """
    DEBUG = True
    TESTING = True
    OCR_USE_GPU = False
    MAX_CONTENT_LENGTH = 1024 * 1024  # 1MB for testing


# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
