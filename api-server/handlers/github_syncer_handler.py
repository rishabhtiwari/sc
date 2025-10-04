"""
GitHub Repository Syncer Handler - API handlers for GitHub Repository Syncer integration
"""

import logging
import requests
from flask import jsonify

from config.app_config import AppConfig

class GitHubSyncerHandler:
    """Handler for GitHub Repository Syncer API operations"""
    
    # GitHub Repo Syncer service URL
    GITHUB_SYNCER_URL = AppConfig.GITHUB_SYNCER_URL
    
    @staticmethod
    def _make_github_syncer_request(method: str, endpoint: str, data=None):
        """
        Make HTTP request to GitHub Repository Syncer service
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            data: Request data for POST requests
            
        Returns:
            Response data as dict
            
        Raises:
            Exception: If request fails
        """
        url = f"{GitHubSyncerHandler.GITHUB_SYNCER_URL}{endpoint}"
        
        try:
            if method == 'GET':
                response = requests.get(url, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.ConnectionError:
            raise Exception(f"Cannot connect to GitHub Repository Syncer service at {url}")
        except requests.exceptions.Timeout:
            raise Exception("GitHub Repository Syncer service request timed out")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise Exception("GitHub Repository Syncer service endpoint not found")
            else:
                try:
                    error_data = e.response.json()
                    raise Exception(error_data.get('error', str(e)))
                except:
                    raise Exception(f"GitHub Repository Syncer service error: {str(e)}")
        except Exception as e:
            raise Exception(f"GitHub Repository Syncer service error: {str(e)}")

    @staticmethod
    def handle_health_check():
        """
        Handle health check for GitHub Repository Syncer service
        
        Returns:
            JSON response with health status
        """
        try:
            logging.info("🏥 Checking GitHub Repository Syncer service health")
            
            result = GitHubSyncerHandler._make_github_syncer_request('GET', '/health')
            return jsonify(result)
            
        except Exception as e:
            logging.error(f"❌ GitHub Repository Syncer health check failed: {str(e)}")
            return jsonify({
                "status": "error",
                "error": f"GitHub Repository Syncer service unavailable: {str(e)}"
            }), 503

    @staticmethod
    def handle_trigger_sync():
        """
        Handle trigger sync for all GitHub repositories
        
        Returns:
            JSON response with sync trigger result
        """
        try:
            logging.info("🚀 Triggering sync for all GitHub repositories")
            
            result = GitHubSyncerHandler._make_github_syncer_request('POST', '/sync')
            return jsonify(result)
            
        except Exception as e:
            logging.error(f"❌ Trigger GitHub sync failed: {str(e)}")
            return jsonify({
                "status": "error",
                "error": f"Failed to trigger GitHub sync: {str(e)}"
            }), 500

    @staticmethod
    def handle_trigger_repository_sync(repository_id: str):
        """
        Handle trigger sync for specific GitHub repository

        Args:
            repository_id: The ID of the repository to sync

        Returns:
            JSON response with sync trigger result
        """
        try:
            logging.info(f"🚀 Triggering sync for GitHub repository: {repository_id}")

            # Use query parameter approach to handle repository IDs with forward slashes
            import urllib.parse
            encoded_repo_id = urllib.parse.quote(repository_id, safe='')
            result = GitHubSyncerHandler._make_github_syncer_request('POST', f'/sync/repository?repository_id={encoded_repo_id}')
            return jsonify(result)

        except Exception as e:
            logging.error(f"❌ Trigger GitHub repository sync failed: {str(e)}")
            return jsonify({
                "status": "error",
                "error": f"Failed to trigger GitHub repository sync: {str(e)}"
            }), 500

    @staticmethod
    def handle_get_sync_status():
        """
        Handle get GitHub sync status
        
        Returns:
            JSON response with sync status
        """
        try:
            logging.info("📊 Getting GitHub sync status")
            
            result = GitHubSyncerHandler._make_github_syncer_request('GET', '/status')
            return jsonify(result)
            
        except Exception as e:
            logging.error(f"❌ Get GitHub sync status failed: {str(e)}")
            return jsonify({
                "status": "error",
                "error": f"Failed to get GitHub sync status: {str(e)}"
            }), 500

    @staticmethod
    def handle_get_repositories():
        """
        Handle get all active GitHub repositories
        
        Returns:
            JSON response with repositories list
        """
        try:
            logging.info("📋 Getting active GitHub repositories")
            
            result = GitHubSyncerHandler._make_github_syncer_request('GET', '/repositories')
            return jsonify(result)
            
        except Exception as e:
            logging.error(f"❌ Get GitHub repositories failed: {str(e)}")
            return jsonify({
                "status": "error",
                "error": f"Failed to get GitHub repositories: {str(e)}"
            }), 500

    @staticmethod
    def handle_get_job_status(job_id: str):
        """
        Handle get job status by ID
        
        Args:
            job_id: The ID of the job
            
        Returns:
            JSON response with job status
        """
        try:
            logging.info(f"📊 Getting GitHub sync job status: {job_id}")
            
            result = GitHubSyncerHandler._make_github_syncer_request('GET', f'/job/{job_id}')
            return jsonify(result)
            
        except Exception as e:
            logging.error(f"❌ Get GitHub job status failed: {str(e)}")
            return jsonify({
                "status": "error",
                "error": f"Failed to get GitHub job status: {str(e)}"
            }), 500

    @staticmethod
    def handle_get_active_jobs():
        """
        Handle get all active GitHub sync jobs

        Returns:
            JSON response with active jobs
        """
        try:
            logging.info("📋 Getting active GitHub sync jobs")

            # Use the dedicated active jobs endpoint
            result = GitHubSyncerHandler._make_github_syncer_request('GET', '/jobs/active')
            return jsonify(result)

        except Exception as e:
            logging.error(f"❌ Get active GitHub jobs failed: {str(e)}")
            return jsonify({
                "status": "error",
                "error": f"Failed to get active GitHub jobs: {str(e)}"
            }), 500

    @staticmethod
    def handle_cancel_job(job_id: str):
        """
        Handle cancel GitHub sync job
        
        Args:
            job_id: The ID of the job to cancel
            
        Returns:
            JSON response with cancellation result
        """
        try:
            logging.info(f"🛑 Cancelling GitHub sync job: {job_id}")
            
            result = GitHubSyncerHandler._make_github_syncer_request('POST', f'/job/{job_id}/cancel')
            return jsonify(result)
            
        except Exception as e:
            logging.error(f"❌ Cancel GitHub job failed: {str(e)}")
            return jsonify({
                "status": "error",
                "error": f"Failed to cancel GitHub job: {str(e)}"
            }), 500

    @staticmethod
    def handle_get_repository_jobs(repository_id: str, limit: int = 10):
        """
        Handle get recent jobs for a specific repository
        
        Args:
            repository_id: The ID of the repository
            limit: Maximum number of jobs to return
            
        Returns:
            JSON response with repository jobs
        """
        try:
            logging.info(f"📋 Getting jobs for GitHub repository: {repository_id}")
            
            result = GitHubSyncerHandler._make_github_syncer_request('GET', f'/jobs/repository/{repository_id}?limit={limit}')
            return jsonify(result)
            
        except Exception as e:
            logging.error(f"❌ Get GitHub repository jobs failed: {str(e)}")
            return jsonify({
                "status": "error",
                "error": f"Failed to get GitHub repository jobs: {str(e)}"
            }), 500
