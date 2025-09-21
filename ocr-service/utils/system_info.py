"""
System information utilities for OCR Service
"""

import time
import os
from typing import Dict, Any, Optional

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


class SystemInfo:
    """
    System information and metrics utilities
    """
    
    def __init__(self):
        self.start_time = time.time()
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """
        Get current system metrics
        
        Returns:
            Dictionary with system metrics
        """
        if not PSUTIL_AVAILABLE:
            return {
                "cpu_usage": "N/A",
                "memory_usage": "N/A",
                "disk_usage": "N/A",
                "note": "psutil not available"
            }
        
        try:
            return {
                "cpu_usage": f"{psutil.cpu_percent(interval=1)}%",
                "memory_usage": f"{psutil.virtual_memory().percent}%",
                "disk_usage": f"{psutil.disk_usage('/').percent}%",
                "load_average": self._get_load_average()
            }
        except Exception as e:
            return {
                "error": f"Failed to get system metrics: {str(e)}"
            }
    
    def get_uptime(self) -> str:
        """
        Get service uptime
        
        Returns:
            Formatted uptime string
        """
        uptime_seconds = int(time.time() - self.start_time)
        
        days = uptime_seconds // 86400
        hours = (uptime_seconds % 86400) // 3600
        minutes = (uptime_seconds % 3600) // 60
        seconds = uptime_seconds % 60
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m {seconds}s"
        elif hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    
    def _get_load_average(self) -> Optional[str]:
        """
        Get system load average (Unix-like systems only)
        
        Returns:
            Load average string or None
        """
        try:
            if hasattr(os, 'getloadavg'):
                load1, load5, load15 = os.getloadavg()
                return f"{load1:.2f}, {load5:.2f}, {load15:.2f}"
        except (OSError, AttributeError):
            pass
        return None
    
    def get_memory_info(self) -> Dict[str, Any]:
        """
        Get detailed memory information
        
        Returns:
            Dictionary with memory information
        """
        if not PSUTIL_AVAILABLE:
            return {"error": "psutil not available"}
        
        try:
            memory = psutil.virtual_memory()
            return {
                "total": self._format_bytes(memory.total),
                "available": self._format_bytes(memory.available),
                "used": self._format_bytes(memory.used),
                "percentage": f"{memory.percent}%"
            }
        except Exception as e:
            return {"error": f"Failed to get memory info: {str(e)}"}
    
    def get_disk_info(self) -> Dict[str, Any]:
        """
        Get disk usage information
        
        Returns:
            Dictionary with disk information
        """
        if not PSUTIL_AVAILABLE:
            return {"error": "psutil not available"}
        
        try:
            disk = psutil.disk_usage('/')
            return {
                "total": self._format_bytes(disk.total),
                "used": self._format_bytes(disk.used),
                "free": self._format_bytes(disk.free),
                "percentage": f"{(disk.used / disk.total) * 100:.1f}%"
            }
        except Exception as e:
            return {"error": f"Failed to get disk info: {str(e)}"}
    
    @staticmethod
    def _format_bytes(bytes_value: int) -> str:
        """
        Format bytes to human readable format
        
        Args:
            bytes_value: Number of bytes
            
        Returns:
            Formatted string
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} PB"
