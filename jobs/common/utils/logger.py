"""
Common logging utility for all job services
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime

def setup_logger(name: str, log_file: str = None, level: str = 'INFO', 
                max_bytes: int = 10485760, backup_count: int = 5) -> logging.Logger:
    """
    Setup logger with both file and console handlers
    
    Args:
        name: Logger name
        log_file: Path to log file (optional)
        level: Logging level
        max_bytes: Maximum log file size before rotation
        backup_count: Number of backup files to keep
        
    Returns:
        Configured logger instance
    """
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, level.upper()))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if log_file is provided)
    if log_file:
        # Ensure log directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def log_job_start(logger: logging.Logger, job_type: str, job_id: str, params: dict = None):
    """Log job start with standard format"""
    logger.info(f"=== JOB START ===")
    logger.info(f"Job Type: {job_type}")
    logger.info(f"Job ID: {job_id}")
    logger.info(f"Start Time: {datetime.utcnow().isoformat()}")
    if params:
        logger.info(f"Parameters: {params}")
    logger.info(f"================")

def log_job_end(logger: logging.Logger, job_type: str, job_id: str, 
                status: str, result: dict = None, error: str = None):
    """Log job end with standard format"""
    logger.info(f"=== JOB END ===")
    logger.info(f"Job Type: {job_type}")
    logger.info(f"Job ID: {job_id}")
    logger.info(f"Status: {status}")
    logger.info(f"End Time: {datetime.utcnow().isoformat()}")
    if result:
        logger.info(f"Result: {result}")
    if error:
        logger.error(f"Error: {error}")
    logger.info(f"==============")

def log_progress(logger: logging.Logger, job_id: str, current: int, total: int, message: str = ""):
    """Log job progress"""
    percentage = (current / total * 100) if total > 0 else 0
    logger.info(f"Job {job_id} Progress: {current}/{total} ({percentage:.1f}%) {message}")

def log_api_request(logger: logging.Logger, method: str, url: str, status_code: int = None, 
                   response_time: float = None):
    """Log API request details"""
    log_msg = f"API Request: {method} {url}"
    if status_code:
        log_msg += f" -> {status_code}"
    if response_time:
        log_msg += f" ({response_time:.2f}s)"
    logger.info(log_msg)
