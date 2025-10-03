"""
Logging utilities for Remote Host Syncer Job
"""
import logging
import os
from datetime import datetime
from config.settings import Config

def setup_logger(name: str = None) -> logging.Logger:
    """
    Set up logger with file and console handlers
    
    Args:
        name: Logger name (defaults to job name)
    
    Returns:
        Configured logger instance
    """
    if name is None:
        name = Config.JOB_NAME
    
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    logger.setLevel(getattr(logging, Config.LOG_LEVEL.upper()))
    
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(Config.LOG_FILE)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # File handler
    file_handler = logging.FileHandler(Config.LOG_FILE)
    file_handler.setLevel(logging.DEBUG)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def log_sync_event(logger: logging.Logger, event_type: str, connection_id: str, 
                   details: dict = None):
    """
    Log sync events with structured format
    
    Args:
        logger: Logger instance
        event_type: Type of sync event (start, complete, error, etc.)
        connection_id: ID of the connection being synced
        details: Additional event details
    """
    timestamp = datetime.now().isoformat()
    log_data = {
        'timestamp': timestamp,
        'event_type': event_type,
        'connection_id': connection_id,
        'details': details or {}
    }
    
    if event_type == 'error':
        logger.error(f"SYNC_EVENT: {log_data}")
    elif event_type == 'warning':
        logger.warning(f"SYNC_EVENT: {log_data}")
    else:
        logger.info(f"SYNC_EVENT: {log_data}")

def log_performance(logger: logging.Logger, operation: str, duration_ms: int, 
                   items_processed: int = None):
    """
    Log performance metrics
    
    Args:
        logger: Logger instance
        operation: Operation name
        duration_ms: Duration in milliseconds
        items_processed: Number of items processed
    """
    perf_data = {
        'operation': operation,
        'duration_ms': duration_ms,
        'items_processed': items_processed
    }
    
    logger.info(f"PERFORMANCE: {perf_data}")
