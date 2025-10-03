"""
Remote Host Syncer Handler - Handles remote host sync operations
"""

import json
import logging
import requests
from flask import request, jsonify
from typing import Dict, Any, Optional

from config.app_config import AppConfig


class SyncerHandler:
    """Handler for Remote Host Syncer operations"""
    
    @staticmethod
    def _get_syncer_service_url() -> str:
        """Get Remote Host Syncer service URL"""
        return f"http://{AppConfig.SYNCER_SERVICE_HOST}:{AppConfig.SYNCER_SERVICE_PORT}"
    
    @staticmethod
    def _make_syncer_request(method: str, endpoint: str, data: Optional[Dict] = None, 
                           params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make request to Remote Host Syncer service
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request data
            params: Query parameters
            
        Returns:
            Response from Syncer service
        """
        try:
            url = f"{SyncerHandler._get_syncer_service_url()}{endpoint}"
            
            response = requests.request(
                method=method,
                url=url,
                json=data,
                params=params,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                return {
                    "status": "error",
                    "error": f"Syncer service returned {response.status_code}: {response.text}"
                }
                
        except requests.exceptions.RequestException as e:
            logging.error(f"❌ Syncer service request failed: {str(e)}")
            return {
                "status": "error",
                "error": f"Failed to connect to syncer service: {str(e)}"
            }
        except Exception as e:
            logging.error(f"❌ Unexpected error in syncer request: {str(e)}")
            return {
                "status": "error",
                "error": f"Unexpected error: {str(e)}"
            }

    @staticmethod
    def handle_trigger_sync():
        """
        Handle trigger sync for all remote host connections
        
        Returns:
            JSON response with sync trigger result
        """
        try:
            logging.info("🚀 Triggering sync for all remote host connections")
            
            result = SyncerHandler._make_syncer_request('POST', '/sync')
            return jsonify(result)
            
        except Exception as e:
            logging.error(f"❌ Trigger sync failed: {str(e)}")
            return jsonify({
                "status": "error",
                "error": f"Failed to trigger sync: {str(e)}"
            }), 500

    @staticmethod
    def handle_trigger_connection_sync(connection_id: str):
        """
        Handle trigger sync for specific connection
        
        Args:
            connection_id: The ID of the connection to sync
            
        Returns:
            JSON response with sync trigger result
        """
        try:
            logging.info(f"🚀 Triggering sync for connection: {connection_id}")
            
            result = SyncerHandler._make_syncer_request('POST', f'/sync/connection/{connection_id}')
            return jsonify(result)
            
        except Exception as e:
            logging.error(f"❌ Trigger connection sync failed: {str(e)}")
            return jsonify({
                "status": "error",
                "error": f"Failed to trigger connection sync: {str(e)}"
            }), 500

    @staticmethod
    def handle_get_sync_status():
        """
        Handle get sync status
        
        Returns:
            JSON response with sync status
        """
        try:
            logging.info("📊 Getting sync status")
            
            result = SyncerHandler._make_syncer_request('GET', '/status')
            return jsonify(result)
            
        except Exception as e:
            logging.error(f"❌ Get sync status failed: {str(e)}")
            return jsonify({
                "status": "error",
                "error": f"Failed to get sync status: {str(e)}"
            }), 500

    @staticmethod
    def handle_get_sync_history():
        """
        Handle get sync history
        
        Returns:
            JSON response with sync history
        """
        try:
            logging.info("📜 Getting sync history")
            
            # Get query parameters from request
            params = {}
            if request.args.get('limit'):
                params['limit'] = request.args.get('limit')
            if request.args.get('days'):
                params['days'] = request.args.get('days')
            if request.args.get('connection_id'):
                params['connection_id'] = request.args.get('connection_id')
            
            result = SyncerHandler._make_syncer_request('GET', '/history', params=params)
            return jsonify(result)
            
        except Exception as e:
            logging.error(f"❌ Get sync history failed: {str(e)}")
            return jsonify({
                "status": "error",
                "error": f"Failed to get sync history: {str(e)}"
            }), 500

    @staticmethod
    def handle_get_connections():
        """
        Handle get all active connections available for sync
        
        Returns:
            JSON response with connections list
        """
        try:
            logging.info("📋 Getting active connections for sync")
            
            result = SyncerHandler._make_syncer_request('GET', '/connections')
            return jsonify(result)
            
        except Exception as e:
            logging.error(f"❌ Get connections failed: {str(e)}")
            return jsonify({
                "status": "error",
                "error": f"Failed to get connections: {str(e)}"
            }), 500

    @staticmethod
    def handle_force_sync():
        """
        Handle force sync (use with caution)

        Returns:
            JSON response with force sync result
        """
        try:
            logging.info("⚠️ Force triggering sync (overriding sync-in-progress protection)")

            result = SyncerHandler._make_syncer_request('POST', '/sync/force')
            return jsonify(result)

        except Exception as e:
            logging.error(f"❌ Force sync failed: {str(e)}")
            return jsonify({
                "status": "error",
                "error": f"Failed to force sync: {str(e)}"
            }), 500

    @staticmethod
    def handle_cancel_job(job_id: str):
        """
        Handle cancel specific job (customer-facing)

        Args:
            job_id: The ID of the job to cancel

        Returns:
            JSON response with cancel result
        """
        try:
            logging.info(f"🛑 Cancelling job: {job_id}")

            result = SyncerHandler._make_syncer_request('POST', f'/job/{job_id}/cancel')
            return jsonify(result)

        except Exception as e:
            logging.error(f"❌ Cancel job failed: {str(e)}")
            return jsonify({
                "status": "error",
                "error": f"Failed to cancel job: {str(e)}"
            }), 500

    @staticmethod
    def handle_cleanup_all_stale_jobs():
        """
        Handle emergency cleanup of all active jobs (customer-facing)

        Returns:
            JSON response with cleanup result
        """
        try:
            logging.info("🧹 Emergency cleanup: Marking all active jobs as failed")

            result = SyncerHandler._make_syncer_request('POST', '/jobs/cleanup-all-stale')
            return jsonify(result)

        except Exception as e:
            logging.error(f"❌ Emergency cleanup failed: {str(e)}")
            return jsonify({
                "status": "error",
                "error": f"Failed to cleanup jobs: {str(e)}"
            }), 500

    @staticmethod
    def handle_get_active_jobs():
        """
        Handle get all active jobs

        Returns:
            JSON response with active jobs
        """
        try:
            logging.info("📋 Getting active jobs")

            result = SyncerHandler._make_syncer_request('GET', '/jobs/active')
            return jsonify(result)

        except Exception as e:
            logging.error(f"❌ Get active jobs failed: {str(e)}")
            return jsonify({
                "status": "error",
                "error": f"Failed to get active jobs: {str(e)}"
            }), 500

    @staticmethod
    def handle_health_check():
        """
        Handle syncer service health check

        Returns:
            JSON response with health status
        """
        try:
            logging.info("🏥 Checking syncer service health")

            result = SyncerHandler._make_syncer_request('GET', '/health')
            return jsonify(result)

        except Exception as e:
            logging.error(f"❌ Health check failed: {str(e)}")
            return jsonify({
                "status": "error",
                "error": f"Failed to check syncer health: {str(e)}"
            }), 500

    @staticmethod
    def handle_get_job_status(job_id):
        """
        Handle get job status request

        Args:
            job_id: Job ID to get status for

        Returns:
            JSON response with job status
        """
        try:
            logging.info(f"📊 Getting job status for: {job_id}")

            result = SyncerHandler._make_syncer_request('GET', f'/job/{job_id}')
            return jsonify(result)

        except Exception as e:
            logging.error(f"❌ Get job status failed: {str(e)}")
            return jsonify({
                "status": "error",
                "error": f"Failed to get job status: {str(e)}"
            }), 500

    @staticmethod
    def handle_get_connection_jobs(connection_id, limit=10):
        """
        Handle get connection jobs request

        Args:
            connection_id: Connection ID to get jobs for
            limit: Maximum number of jobs to return

        Returns:
            JSON response with connection jobs
        """
        try:
            logging.info(f"📋 Getting jobs for connection: {connection_id}")

            result = SyncerHandler._make_syncer_request('GET', f'/jobs/connection/{connection_id}?limit={limit}')
            return jsonify(result)

        except Exception as e:
            logging.error(f"❌ Get connection jobs failed: {str(e)}")
            return jsonify({
                "status": "error",
                "error": f"Failed to get connection jobs: {str(e)}"
            }), 500

    @staticmethod
    def handle_get_active_jobs():
        """
        Handle get active jobs request

        Returns:
            JSON response with active jobs
        """
        try:
            logging.info("🔄 Getting active jobs")

            result = SyncerHandler._make_syncer_request('GET', '/jobs/active')
            return jsonify(result)

        except Exception as e:
            logging.error(f"❌ Get active jobs failed: {str(e)}")
            return jsonify({
                "status": "error",
                "error": f"Failed to get active jobs: {str(e)}"
            }), 500
