"""
Export Generator Job Service
Handles project export generation using the BaseJob framework
"""

import os
import sys

# Add common directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'common'))

from common.models.base_job import BaseJob
from config.settings import Config
from services.export_service import ExportService
from flask import jsonify, request
from typing import Dict, Any


class ExportGeneratorJob(BaseJob):
    """Export Generation Job that extends BaseJob framework"""

    def __init__(self):
        super().__init__("export-generator", Config)
        self.export_service = ExportService(self.config, self.logger)

        # Initialize MongoDB connection
        from pymongo import MongoClient
        self.mongo_client = MongoClient(self.config.MONGODB_URI)
        self.db = self.mongo_client[self.config.MONGODB_DATABASE]
        
        # Connect to news database for video/audio library
        self.news_client = MongoClient(self.config.NEWS_MONGODB_URL)
        self.news_db = self.news_client[self.config.NEWS_MONGODB_DATABASE]

        # Validate configuration
        try:
            self.config.validate_config()
            self.logger.info("✅ Configuration validation passed")
        except ValueError as e:
            self.logger.error(f"❌ Configuration validation failed: {str(e)}")
            raise

        # Setup custom routes
        self._setup_custom_routes()

    def get_job_type(self) -> str:
        """Return the job type identifier"""
        return "export-generator"

    def is_multi_tenant_job(self) -> bool:
        """
        Export generator is a multi-tenant job - runs separately for each customer

        Returns:
            True to enable per-customer job execution
        """
        return True

    def run_job(self, job_id: str, is_on_demand: bool = False, **kwargs) -> Dict[str, Any]:
        """
        Main job execution method - processes export requests
        
        This is called by the BaseJob framework for scheduled jobs.
        For on-demand exports, we use the custom /export endpoint instead.

        Args:
            job_id: Job instance ID for tracking
            is_on_demand: True if this is a manual/on-demand job
            **kwargs: Additional job parameters (customer_id, user_id, export_request)

        Returns:
            Dict containing job results
        """
        try:
            customer_id = kwargs.get('customer_id')
            user_id = kwargs.get('user_id')
            export_request = kwargs.get('export_request')

            if not export_request:
                return {
                    'status': 'error',
                    'error': 'No export request provided'
                }

            self.logger.info(f"🚀 Starting export job {job_id} for customer {customer_id}")

            # Process the export
            result = self.export_service.process_export(
                job_id=job_id,
                project_id=export_request['project_id'],
                customer_id=customer_id,
                user_id=user_id,
                export_format=export_request['format'],
                settings=export_request['settings']
            )

            return result

        except Exception as e:
            self.logger.error(f"❌ Error in export job {job_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }

    def _setup_custom_routes(self):
        """Setup custom Flask routes for export functionality"""

        @self.app.route('/export', methods=['POST'])
        def create_export():
            """Create a new export job"""
            try:
                data = request.get_json()
                
                # Extract parameters
                project_id = data.get('project_id')
                customer_id = data.get('customer_id')
                user_id = data.get('user_id')
                export_format = data.get('format', 'mp4')
                settings = data.get('settings', {})

                if not project_id or not customer_id or not user_id:
                    return jsonify({
                        'error': 'Missing required parameters: project_id, customer_id, user_id'
                    }), 400

                # Create job instance
                job_id = self.job_instance_service.create_job_instance(
                    job_type=self.get_job_type(),
                    status='pending',
                    customer_id=customer_id,
                    metadata={
                        'project_id': project_id,
                        'user_id': user_id,
                        'format': export_format,
                        'settings': settings,
                        'trigger': 'api'
                    },
                    check_running=False
                )

                # Start export processing in background
                import threading
                import traceback
                def run_export():
                    try:
                        self.logger.info(f"🎬 Export thread started for job {job_id}")
                        self.job_instance_service.update_job_instance(job_id, status='running')

                        result = self.run_job(
                            job_id,
                            is_on_demand=True,
                            customer_id=customer_id,
                            user_id=user_id,
                            export_request={
                                'project_id': project_id,
                                'format': export_format,
                                'settings': settings
                            }
                        )

                        status = 'completed' if result.get('status') == 'success' else 'failed'
                        self.job_instance_service.update_job_instance(
                            job_id,
                            status=status,
                            result=result
                        )
                        self.logger.info(f"✅ Export thread completed for job {job_id}")
                    except Exception as e:
                        self.logger.error(f"❌ Export job {job_id} failed: {str(e)}")
                        self.logger.error(f"Traceback: {traceback.format_exc()}")
                        self.job_instance_service.update_job_instance(
                            job_id,
                            status='failed',
                            error_message=str(e)
                        )

                thread = threading.Thread(target=run_export)
                thread.daemon = True
                thread.start()
                self.logger.info(f"🚀 Export thread launched for job {job_id}")

                return jsonify({
                    'success': True,
                    'export_job_id': job_id,
                    'status': 'pending',
                    'message': 'Export job created successfully'
                }), 202

            except Exception as e:
                self.logger.error(f"Error creating export: {str(e)}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/export/<job_id>/status', methods=['GET'])
        def get_export_status(job_id):
            """Get export job status"""
            try:
                customer_id = request.args.get('customer_id')

                if not customer_id:
                    return jsonify({'error': 'Missing customer_id parameter'}), 400

                # Get export job from export_service
                export_job = self.export_service.get_export_job(job_id, customer_id)

                if not export_job:
                    return jsonify({'error': 'Export job not found'}), 404

                return jsonify(export_job), 200

            except Exception as e:
                self.logger.error(f"Error getting export status: {str(e)}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/export/<job_id>', methods=['DELETE'])
        def cancel_export(job_id):
            """Cancel an export job"""
            try:
                customer_id = request.args.get('customer_id')

                if not customer_id:
                    return jsonify({'error': 'Missing customer_id parameter'}), 400

                # Get export job
                export_job = self.export_service.get_export_job(job_id, customer_id)

                if not export_job:
                    return jsonify({'error': 'Export job not found'}), 404

                # Check if job can be cancelled
                status = export_job.get('status')
                if status in ['completed', 'failed']:
                    return jsonify({
                        'error': f'Cannot cancel export in {status} status'
                    }), 400

                # Update status to cancelled
                self.export_service._update_export_job(job_id, customer_id, {
                    'status': 'cancelled'
                })

                # Also update job instance if it exists
                try:
                    self.job_instance_service.update_job_instance(
                        job_id,
                        status='cancelled'
                    )
                except Exception:
                    pass  # Job instance might not exist

                return jsonify({
                    'success': True,
                    'message': 'Export job cancelled'
                }), 200

            except Exception as e:
                self.logger.error(f"Error cancelling export: {str(e)}")
                return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # Create and run the job service
    job = ExportGeneratorJob()

    # Start the Flask application with job scheduling
    job.run_flask_app()

