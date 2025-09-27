"""
Logging utility for the Retriever Service
"""
import logging
import os
from logging.handlers import RotatingFileHandler
from config.settings import Config


def setup_logger(name: str = None) -> logging.Logger:
    """
    Set up logger with file and console handlers
    
    Args:
        name: Logger name (defaults to 'retriever-service')
        
    Returns:
        Configured logger instance
    """
    if name is None:
        name = 'retriever-service'
    
    logger = logging.getLogger(name)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    # Set log level
    log_level = getattr(logging, Config.LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter(Config.LOG_FORMAT)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if log directory exists)
    log_dir = os.path.dirname(Config.LOG_FILE)
    if os.path.exists(log_dir) or log_dir == '/app/logs':
        try:
            # Create log directory if it doesn't exist
            os.makedirs(log_dir, exist_ok=True)
            
            # Rotating file handler (10MB max, 5 backup files)
            file_handler = RotatingFileHandler(
                Config.LOG_FILE,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except (OSError, PermissionError) as e:
            logger.warning(f"Could not set up file logging: {e}")
    
    return logger
