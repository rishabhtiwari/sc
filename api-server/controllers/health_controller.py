"""
Health Controller - System health and monitoring
"""

import time
import psutil
from typing import Dict, Any

from flask import current_app


class HealthController:
    """
    Controller for handling health check and system monitoring
    """
    
    @staticmethod
    def get_health_status() -> Dict[str, Any]:
        """
        Get comprehensive health status of the application
        
        Returns:
            Dict[str, Any]: Health status information
        """
        try:
            return {
                "status": "healthy",
                "message": "iChat API Server is running smoothly",
                "timestamp": int(time.time() * 1000),
                "version": current_app.config.get('API_VERSION', '2.0.0'),
                "uptime": HealthController._get_uptime(),
                "system": HealthController._get_system_info()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Health check failed: {str(e)}",
                "timestamp": int(time.time() * 1000),
                "error": str(e)
            }
    
    @staticmethod
    def get_detailed_status() -> Dict[str, Any]:
        """
        Get detailed system status including performance metrics
        
        Returns:
            Dict[str, Any]: Detailed status information
        """
        try:
            return {
                "status": "healthy",
                "timestamp": int(time.time() * 1000),
                "application": {
                    "name": current_app.config.get('API_TITLE', 'iChat API Server'),
                    "version": current_app.config.get('API_VERSION', '2.0.0'),
                    "debug_mode": current_app.config.get('DEBUG', False),
                    "uptime": HealthController._get_uptime()
                },
                "system": HealthController._get_system_info(),
                "performance": HealthController._get_performance_metrics(),
                "endpoints": {
                    "chat": "/api/chat",
                    "health": "/api/health",
                    "status": "/api/status"
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to get detailed status: {str(e)}",
                "timestamp": int(time.time() * 1000)
            }
    
    @staticmethod
    def _get_uptime() -> str:
        """
        Get application uptime (simplified version)
        
        Returns:
            str: Uptime information
        """
        try:
            # This is a simplified uptime - in production you'd track actual start time
            boot_time = psutil.boot_time()
            uptime_seconds = time.time() - boot_time
            
            days = int(uptime_seconds // 86400)
            hours = int((uptime_seconds % 86400) // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            
            return f"{days}d {hours}h {minutes}m"
        except:
            return "unknown"
    
    @staticmethod
    def _get_system_info() -> Dict[str, Any]:
        """
        Get basic system information
        
        Returns:
            Dict[str, Any]: System information
        """
        try:
            return {
                "platform": psutil.WINDOWS if hasattr(psutil, 'WINDOWS') else "unix",
                "cpu_count": psutil.cpu_count(),
                "memory_total": f"{psutil.virtual_memory().total // (1024**3)}GB",
                "python_version": f"{psutil.version_info if hasattr(psutil, 'version_info') else 'unknown'}"
            }
        except:
            return {
                "platform": "unknown",
                "cpu_count": "unknown",
                "memory_total": "unknown",
                "python_version": "unknown"
            }
    
    @staticmethod
    def _get_performance_metrics() -> Dict[str, Any]:
        """
        Get performance metrics
        
        Returns:
            Dict[str, Any]: Performance metrics
        """
        try:
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            return {
                "cpu_usage": f"{cpu_percent}%",
                "memory_usage": f"{memory.percent}%",
                "memory_available": f"{memory.available // (1024**2)}MB",
                "disk_usage": "N/A"  # Simplified for now
            }
        except:
            return {
                "cpu_usage": "unknown",
                "memory_usage": "unknown",
                "memory_available": "unknown",
                "disk_usage": "unknown"
            }
