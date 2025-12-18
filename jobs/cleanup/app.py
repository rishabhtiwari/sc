#!/usr/bin/env python3
"""
Cleanup Job Service
Automatically deletes old news articles and their associated files (audio, video, images)
"""

import os
import sys
from datetime import datetime
from typing import Dict, Any
from flask import jsonify, request

# Add parent directories to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.models.base_job import BaseJob
from common.utils.multi_tenant_db import extract_user_context_from_headers
from config.settings import Config, JobStatus
from services.cleanup_service import CleanupService


class CleanupJob(BaseJob):
    """
    Cleanup Job Implementation
    Extends BaseJob to provide automatic cleanup of old news articles
    """

    def __init__(self):
        super().__init__('cleanup', Config)
        
        # Validate configuration
        Config.validate_config()
        
        # Initialize cleanup service
        self.cleanup_service = CleanupService(Config, logger=self.logger)
        
        self.logger.info("🧹 Cleanup Job initialized")
        self.logger.info(f"⏰ Scheduled to run every {Config.JOB_INTERVAL_SECONDS} seconds")
        self.logger.info(f"📅 Retention period: {Config.CLEANUP_RETENTION_HOURS} hours")
        self.logger.info(f"🔍 Dry-run mode: {Config.CLEANUP_DRY_RUN}")

    def get_job_type(self) -> str:
        """Return the job type identifier"""
        return 'cleanup'

    def is_multi_tenant_job(self) -> bool:
        """
        Cleanup is a multi-tenant job - runs separately for each customer

        Returns:
            True to enable per-customer job execution
        """
        return True

    def run_job(self, job_id: str, is_on_demand: bool = False, **kwargs) -> Dict[str, Any]:
        """
        Execute the cleanup job

        Args:
            job_id: Unique identifier for this job execution
            is_on_demand: True if this is a manual/on-demand job
            **kwargs: Additional parameters (retention_hours, dry_run, customer_id, user_id)

        Returns:
            Dict containing job results and statistics
        """
        # Extract customer_id and user_id from kwargs
        customer_id = kwargs.get('customer_id')
        user_id = kwargs.get('user_id')

        customer_info = f" for customer {customer_id}" if customer_id else ""
        self.logger.info("=" * 80)
        self.logger.info(f"🧹 Starting Cleanup Job - ID: {job_id}{customer_info}")
        self.logger.info(f"🎯 Trigger: {'On-Demand' if is_on_demand else 'Scheduled'}")
        self.logger.info("=" * 80)

        start_time = datetime.utcnow()

        try:
            # Get parameters from kwargs or use config defaults
            retention_hours = kwargs.get('retention_hours', Config.CLEANUP_RETENTION_HOURS)
            dry_run = kwargs.get('dry_run', Config.CLEANUP_DRY_RUN)

            # Run cleanup with customer_id for multi-tenancy
            cleanup_stats = self.cleanup_service.cleanup_old_articles(
                retention_hours=retention_hours,
                dry_run=dry_run,
                customer_id=customer_id
            )
            
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            # Determine job status
            if cleanup_stats['errors']:
                status = JobStatus.PARTIAL_FAILURE.value
            else:
                status = JobStatus.COMPLETED.value
            
            result = {
                'job_id': job_id,
                'status': status,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration_seconds': duration,
                'statistics': cleanup_stats,
                'message': f"Cleanup completed: {cleanup_stats['total_articles_deleted']} articles deleted, "
                          f"{cleanup_stats['total_files_deleted']} files deleted, "
                          f"{self._format_bytes(cleanup_stats['total_space_freed_bytes'])} freed"
            }
            
            self.logger.info("=" * 80)
            self.logger.info(f"✅ Cleanup Job Completed - ID: {job_id}")
            self.logger.info(f"⏱️ Duration: {duration:.2f} seconds")
            self.logger.info(f"📊 Status: {status}")
            self.logger.info("=" * 80)
            
            return result
            
        except Exception as e:
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            error_msg = f"Cleanup job failed: {str(e)}"
            self.logger.error(f"❌ {error_msg}")
            
            return {
                'job_id': job_id,
                'status': JobStatus.FAILED.value,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration_seconds': duration,
                'error': error_msg,
                'message': error_msg
            }

    def validate_job_params(self, params: Dict[str, Any]) -> list:
        """
        Validate job parameters
        
        Args:
            params: Job parameters to validate
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Validate retention_hours if provided
        if 'retention_hours' in params:
            try:
                retention_hours = int(params['retention_hours'])
                if retention_hours < 1:
                    errors.append("retention_hours must be at least 1")
            except (ValueError, TypeError):
                errors.append("retention_hours must be a valid integer")
        
        # Validate dry_run if provided
        if 'dry_run' in params:
            dry_run = params['dry_run']
            if not isinstance(dry_run, bool) and dry_run not in ['true', 'false', 'True', 'False']:
                errors.append("dry_run must be a boolean value")
        
        return errors

    def _setup_custom_routes(self):
        """Setup custom routes for cleanup job"""
        
        @self.app.route('/cleanup/stats', methods=['GET'])
        def get_cleanup_stats():
            """Get cleanup statistics from last run"""
            try:
                # Get last completed job
                last_job = self.job_instance_service.get_last_completed_job(self.get_job_type())
                
                if not last_job:
                    return jsonify({
                        'message': 'No cleanup jobs have been completed yet',
                        'status': 'info'
                    }), 404
                
                return jsonify({
                    'job_id': last_job.get('job_id'),
                    'completed_at': last_job.get('end_time'),
                    'statistics': last_job.get('result', {}).get('statistics', {}),
                    'status': 'success'
                })
                
            except Exception as e:
                self.logger.error(f"Error getting cleanup stats: {str(e)}")
                return jsonify({
                    'error': str(e),
                    'status': 'error'
                }), 500

        @self.app.route('/cleanup/preview', methods=['POST'])
        def preview_cleanup():
            """Preview what would be deleted (dry-run)"""
            try:
                data = request.get_json() or {}
                retention_hours = data.get('retention_hours', Config.CLEANUP_RETENTION_HOURS)
                
                # Force dry-run mode
                cleanup_stats = self.cleanup_service.cleanup_old_articles(
                    retention_hours=retention_hours,
                    dry_run=True
                )
                
                return jsonify({
                    'message': 'Preview completed',
                    'statistics': cleanup_stats,
                    'status': 'success'
                })
                
            except Exception as e:
                self.logger.error(f"Error previewing cleanup: {str(e)}")
                return jsonify({
                    'error': str(e),
                    'status': 'error'
                }), 500

    def _format_bytes(self, bytes_value: int) -> str:
        """Format bytes to human-readable string"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.2f} PB"


def main():
    """Main entry point"""
    try:
        # Create and run the cleanup job
        cleanup_job = CleanupJob()
        
        # Setup custom routes
        cleanup_job._setup_custom_routes()
        
        # Start Flask server
        cleanup_job.logger.info(f"🚀 Starting Cleanup Job Service on port {Config.FLASK_PORT}")
        cleanup_job.app.run(
            host=Config.FLASK_HOST,
            port=Config.FLASK_PORT,
            debug=Config.FLASK_DEBUG
        )
        
    except KeyboardInterrupt:
        cleanup_job.logger.info("⚠️ Cleanup Job Service stopped by user")
    except Exception as e:
        print(f"❌ Failed to start Cleanup Job Service: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()

