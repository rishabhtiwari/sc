"""
Video Service Client - Interface to Video Generation Service
"""

import requests
import logging
from typing import Dict, Any
from config.app_config import AppConfig


class VideoServiceClient:
    """Client for communicating with the Video Generation Service"""
    
    def __init__(self):
        self.base_url = AppConfig.VIDEO_SERVICE_URL
        self.timeout = AppConfig.VIDEO_SERVICE_TIMEOUT
        self.logger = logging.getLogger(__name__)
        
    def merge_latest_videos(self) -> Dict[str, Any]:
        """
        Merge latest 20 news videos into a single compilation video
        
        Returns:
            Dictionary with merge operation status and details
        """
        try:
            self.logger.info("🎬 Starting merge of latest 20 news videos")
            
            response = requests.post(
                f"{self.base_url}/merge-latest",
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                self.logger.info(f"✅ Video merge started successfully for {data.get('video_count', 0)} videos")
                return {
                    'status': 'success',
                    'data': data
                }
            else:
                error_msg = f"Video service returned status {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', error_msg)
                except:
                    pass
                self.logger.error(f"❌ {error_msg}")
                return {
                    'status': 'error',
                    'error': error_msg,
                    'data': None
                }
                
        except requests.exceptions.Timeout:
            error_msg = f"Video service request timed out after {self.timeout}s"
            self.logger.error(f"⏰ {error_msg}")
            return {
                'status': 'error',
                'error': error_msg,
                'data': None
            }
        except requests.exceptions.ConnectionError:
            error_msg = "Could not connect to video service"
            self.logger.error(f"🔌 {error_msg}")
            return {
                'status': 'error',
                'error': error_msg,
                'data': None
            }
        except Exception as e:
            error_msg = f"Unexpected error calling video service: {str(e)}"
            self.logger.error(f"💥 {error_msg}")
            return {
                'status': 'error',
                'error': error_msg,
                'data': None
            }
    
    def get_merge_status(self) -> Dict[str, Any]:
        """
        Check the status of video merging process
        
        Returns:
            Dictionary with merge status and file info
        """
        try:
            self.logger.info("🔍 Checking video merge status")
            
            response = requests.get(
                f"{self.base_url}/merge-status",
                timeout=30  # Shorter timeout for status check
            )
            
            if response.status_code == 200:
                data = response.json()
                self.logger.info(f"✅ Merge status: {data.get('status', 'unknown')}")
                return {
                    'status': 'success',
                    'data': data
                }
            else:
                error_msg = f"Video service returned status {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', error_msg)
                except:
                    pass
                self.logger.error(f"❌ {error_msg}")
                return {
                    'status': 'error',
                    'error': error_msg,
                    'data': None
                }
                
        except Exception as e:
            error_msg = f"Error checking merge status: {str(e)}"
            self.logger.error(f"💥 {error_msg}")
            return {
                'status': 'error',
                'error': error_msg,
                'data': None
            }
    
    def download_merged_video(self) -> Dict[str, Any]:
        """
        Get the download URL for the merged video
        
        Returns:
            Dictionary with download information
        """
        try:
            self.logger.info("📥 Getting merged video download info")
            
            # First check if the video is ready
            status_result = self.get_merge_status()
            if status_result['status'] != 'success':
                return status_result
                
            status_data = status_result['data']
            if status_data.get('status') != 'completed':
                return {
                    'status': 'error',
                    'error': 'Merged video is not ready yet. Please check merge status.',
                    'data': status_data
                }
            
            # Return download URL
            download_url = f"{self.base_url}/download/latest-20-news.mp4"
            return {
                'status': 'success',
                'data': {
                    'download_url': download_url,
                    'file_info': status_data
                }
            }
                
        except Exception as e:
            error_msg = f"Error getting download info: {str(e)}"
            self.logger.error(f"💥 {error_msg}")
            return {
                'status': 'error',
                'error': error_msg,
                'data': None
            }
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check if video service is healthy
        
        Returns:
            Dictionary with health status
        """
        try:
            response = requests.get(
                f"{self.base_url}/health",
                timeout=5  # Short timeout for health check
            )
            
            if response.status_code == 200:
                return {
                    'status': 'healthy',
                    'service': 'video-generator'
                }
            else:
                return {
                    'status': 'unhealthy',
                    'service': 'video-generator',
                    'error': f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            return {
                'status': 'unhealthy',
                'service': 'video-generator',
                'error': str(e)
            }
