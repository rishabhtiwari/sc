"""
Logging utilities for GitHub Repository Syncer
"""
import os
import logging
import time
from datetime import datetime
from functools import wraps
from typing import Any, Dict, Optional

def setup_logger(name: str, log_file: str = None, level: str = 'INFO') -> logging.Logger:
    """Setup logger with file and console handlers"""
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
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
    
    # File handler (if log_file specified)
    if log_file:
        # Create log directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
            
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def log_sync_event(logger: logging.Logger, event_type: str, repository_id: str, 
                  details: Dict[str, Any] = None):
    """Log sync events with structured format"""
    details = details or {}
    
    log_data = {
        'event_type': event_type,
        'repository_id': repository_id,
        'timestamp': datetime.now().isoformat(),
        **details
    }
    
    # Format log message
    message_parts = [f"{event_type.upper()}: Repository {repository_id}"]
    
    if 'files_processed' in details:
        message_parts.append(f"Files: {details['files_processed']}")
    
    if 'files_indexed' in details:
        message_parts.append(f"Indexed: {details['files_indexed']}")
        
    if 'duration' in details:
        message_parts.append(f"Duration: {details['duration']:.2f}s")
        
    if 'error' in details:
        message_parts.append(f"Error: {details['error']}")
    
    message = " | ".join(message_parts)
    
    # Log at appropriate level
    if event_type in ['sync_started', 'sync_completed']:
        logger.info(message)
    elif event_type in ['sync_failed', 'file_error']:
        logger.error(message)
    elif event_type in ['file_skipped', 'rate_limited']:
        logger.warning(message)
    else:
        logger.debug(message)

def log_performance(logger: logging.Logger, operation: str, duration: float, 
                   details: Dict[str, Any] = None):
    """Log performance metrics"""
    details = details or {}
    
    message_parts = [f"PERFORMANCE: {operation}"]
    message_parts.append(f"Duration: {duration:.2f}s")
    
    if 'items_processed' in details:
        items = details['items_processed']
        rate = items / duration if duration > 0 else 0
        message_parts.append(f"Items: {items}")
        message_parts.append(f"Rate: {rate:.2f}/s")
    
    if 'memory_usage' in details:
        message_parts.append(f"Memory: {details['memory_usage']:.2f}MB")
        
    if 'api_calls' in details:
        message_parts.append(f"API Calls: {details['api_calls']}")
    
    message = " | ".join(message_parts)
    logger.info(message)

def performance_monitor(operation_name: str):
    """Decorator to monitor function performance"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get logger from first argument if it's a class instance
            logger = None
            if args and hasattr(args[0], 'logger'):
                logger = args[0].logger
            else:
                logger = logging.getLogger('performance')
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Extract performance details from result if it's a dict
                details = {}
                if isinstance(result, dict):
                    if 'files_processed' in result:
                        details['items_processed'] = result['files_processed']
                    if 'api_calls' in result:
                        details['api_calls'] = result['api_calls']
                
                log_performance(logger, operation_name, duration, details)
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                log_performance(logger, f"{operation_name}_FAILED", duration, {'error': str(e)})
                raise
                
        return wrapper
    return decorator

def log_github_api_call(logger: logging.Logger, method: str, url: str, 
                       status_code: int, response_time: float, 
                       rate_limit_remaining: Optional[int] = None):
    """Log GitHub API calls with rate limiting info"""
    message_parts = [f"GITHUB_API: {method} {url}"]
    message_parts.append(f"Status: {status_code}")
    message_parts.append(f"Time: {response_time:.2f}s")
    
    if rate_limit_remaining is not None:
        message_parts.append(f"Rate Limit Remaining: {rate_limit_remaining}")
    
    message = " | ".join(message_parts)
    
    if status_code >= 400:
        logger.error(message)
    elif status_code >= 300:
        logger.warning(message)
    else:
        logger.debug(message)

def log_file_processing(logger: logging.Logger, file_path: str, action: str, 
                       details: Dict[str, Any] = None):
    """Log file processing events"""
    details = details or {}
    
    message_parts = [f"FILE_{action.upper()}: {file_path}"]
    
    if 'size' in details:
        size_mb = details['size'] / (1024 * 1024)
        message_parts.append(f"Size: {size_mb:.2f}MB")
    
    if 'encoding' in details:
        message_parts.append(f"Encoding: {details['encoding']}")
        
    if 'lines' in details:
        message_parts.append(f"Lines: {details['lines']}")
        
    if 'error' in details:
        message_parts.append(f"Error: {details['error']}")
    
    message = " | ".join(message_parts)
    
    if action in ['processed', 'indexed']:
        logger.debug(message)
    elif action in ['skipped', 'failed']:
        logger.warning(message)
    else:
        logger.info(message)

class ProgressLogger:
    """Logger for tracking progress of long-running operations"""
    
    def __init__(self, logger: logging.Logger, operation: str, total_items: int):
        self.logger = logger
        self.operation = operation
        self.total_items = total_items
        self.processed_items = 0
        self.start_time = time.time()
        self.last_log_time = self.start_time
        self.log_interval = 10  # Log every 10 seconds
        
    def update(self, increment: int = 1, details: Dict[str, Any] = None):
        """Update progress and log if needed"""
        self.processed_items += increment
        current_time = time.time()
        
        # Log progress at intervals or when complete
        should_log = (
            current_time - self.last_log_time >= self.log_interval or
            self.processed_items >= self.total_items
        )
        
        if should_log:
            self._log_progress(details)
            self.last_log_time = current_time
    
    def _log_progress(self, details: Dict[str, Any] = None):
        """Log current progress"""
        details = details or {}
        
        elapsed = time.time() - self.start_time
        progress_pct = (self.processed_items / self.total_items * 100) if self.total_items > 0 else 0
        rate = self.processed_items / elapsed if elapsed > 0 else 0
        
        # Estimate remaining time
        if rate > 0 and self.processed_items < self.total_items:
            remaining_items = self.total_items - self.processed_items
            eta_seconds = remaining_items / rate
            eta_str = f"ETA: {eta_seconds:.0f}s"
        else:
            eta_str = "ETA: --"
        
        message_parts = [f"PROGRESS: {self.operation}"]
        message_parts.append(f"{self.processed_items}/{self.total_items} ({progress_pct:.1f}%)")
        message_parts.append(f"Rate: {rate:.2f}/s")
        message_parts.append(eta_str)
        
        if 'current_item' in details:
            message_parts.append(f"Current: {details['current_item']}")
        
        message = " | ".join(message_parts)
        self.logger.info(message)
    
    def complete(self, details: Dict[str, Any] = None):
        """Mark operation as complete and log final stats"""
        details = details or {}
        
        total_time = time.time() - self.start_time
        avg_rate = self.processed_items / total_time if total_time > 0 else 0
        
        message_parts = [f"COMPLETED: {self.operation}"]
        message_parts.append(f"Items: {self.processed_items}/{self.total_items}")
        message_parts.append(f"Duration: {total_time:.2f}s")
        message_parts.append(f"Avg Rate: {avg_rate:.2f}/s")
        
        if 'success_count' in details:
            success_pct = (details['success_count'] / self.processed_items * 100) if self.processed_items > 0 else 0
            message_parts.append(f"Success: {details['success_count']} ({success_pct:.1f}%)")
        
        if 'error_count' in details:
            message_parts.append(f"Errors: {details['error_count']}")
        
        message = " | ".join(message_parts)
        self.logger.info(message)
