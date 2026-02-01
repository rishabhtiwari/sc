#!/usr/bin/env python3
"""
Image Auto-Marker Job Service
Automatically marks images as cleaned for customers with auto_mark_cleaned enabled
"""

import os
import sys
from datetime import datetime
from typing import Dict, Any, List

# Add parent directories to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.models.base_job import BaseJob
from config.settings import Config
from services.image_auto_marker_service import ImageAutoMarkerService


class ImageAutoMarkerJob(BaseJob):
    """
    Image Auto-Marker Job Implementation
    Extends BaseJob to provide automatic image marking functionality
    """

    def __init__(self):
        super().__init__('image-auto-marker', Config)
        
        # Initialize the auto-marker service
        self.auto_marker_service = ImageAutoMarkerService(Config, logger=self.logger)
        
        self.logger.info("✅ Image Auto-Marker Job initialized")

    def get_job_type(self) -> str:
        """Return the job type identifier"""
        return 'image_auto_marker'

    def is_multi_tenant_job(self) -> bool:
        """
        Image auto-marker is a multi-tenant job - runs separately for each customer

        Returns:
            True to enable per-customer job execution
        """
        return True

    def get_parallel_tasks(self) -> List[Dict[str, Any]]:
        """
        Define parallel tasks for image auto-marker job

        Returns:
            List of task definitions for parallel execution
        """
        return [
            {
                'name': 'auto_mark_images',
                'function': self.auto_marker_service.process_pending_images,
                'args': (),
                'kwargs': {}
            }
        ]

    def validate_job_params(self, params: Dict[str, Any]) -> List[str]:
        """
        Validate job parameters

        Args:
            params: Job parameters to validate

        Returns:
            List of validation errors (empty if valid)
        """
        # Auto-marker doesn't require specific parameters
        return []

    def run_job(self, job_id: str, is_on_demand: bool = False, **kwargs) -> Dict[str, Any]:
        """
        Main job execution method - processes pending images for auto-marking

        Args:
            job_id: Job instance ID for tracking
            is_on_demand: True if this is a manual/on-demand job, False for scheduled jobs
            **kwargs: Additional parameters (customer_id for multi-tenant jobs)

        Returns:
            Dict containing job results
        """
        customer_id = kwargs.get('customer_id')
        
        self.logger.info(f"🚀 Starting image auto-marker job for customer: {customer_id}")
        
        try:
            # Check if auto-mark is enabled for this customer
            if not self.auto_marker_service.is_auto_mark_enabled(customer_id):
                self.logger.info(f"⏭️ Auto-mark disabled for customer {customer_id}, skipping")
                return {
                    'status': 'skipped',
                    'reason': 'auto_mark_cleaned is disabled',
                    'customer_id': customer_id
                }
            
            # Process pending images
            result = self.auto_marker_service.process_pending_images(customer_id=customer_id)
            
            self.logger.info(
                f"✅ Auto-marker job completed for customer {customer_id}: "
                f"{result.get('images_marked', 0)} images marked"
            )
            
            return result
            
        except Exception as e:
            error_msg = f"Auto-marker job failed for customer {customer_id}: {str(e)}"
            self.logger.error(f"❌ {error_msg}")
            raise


def main():
    """Main entry point"""
    try:
        # Create and start the job
        job = ImageAutoMarkerJob()

        # Start the Flask app with scheduler
        job.run_flask_app()

    except KeyboardInterrupt:
        job.logger.info("⚠️ Image Auto-Marker Job stopped by user")
        job.shutdown()
    except Exception as e:
        print(f"❌ Failed to start Image Auto-Marker Job: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()

