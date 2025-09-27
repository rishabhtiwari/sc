"""
Logging utilities for Vector Database Service
"""

import logging
import sys
from config.settings import Config


def setup_logging():
    """Setup logging configuration"""
    
    # Create logger
    logger = logging.getLogger('vector-db')
    logger.setLevel(getattr(logging, Config.LOG_LEVEL))
    
    # Prevent duplicate logs
    if logger.handlers:
        return logger
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, Config.LOG_LEVEL))
    
    # Create formatter
    formatter = logging.Formatter(Config.LOG_FORMAT)
    console_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(console_handler)
    
    # Set third-party loggers to WARNING to reduce noise
    logging.getLogger('chromadb').setLevel(logging.WARNING)
    logging.getLogger('sentence_transformers').setLevel(logging.WARNING)
    logging.getLogger('transformers').setLevel(logging.WARNING)
    logging.getLogger('torch').setLevel(logging.WARNING)
    
    return logger
