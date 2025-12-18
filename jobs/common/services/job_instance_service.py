"""
Common Job Instance Service
Manages job execution tracking and status for all job types using MongoDB
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError, ConnectionFailure
import os

class JobInstanceService:
    """Service for managing job instances and their execution status in MongoDB"""

    def __init__(self, mongodb_url: str = None):
        self.mongodb_url = mongodb_url or os.getenv('MONGODB_URL', 'mongodb://ichat_app:ichat_app_password_2024@localhost:27017/ichat_db?authSource=admin')
        self.client = None
        self.db = None
        self.collection = None
        self._init_database()
    
    def _init_database(self):
        """Initialize MongoDB connection"""
        try:
            self.client = MongoClient(self.mongodb_url)
            self.db = self.client.get_database()  # Uses database from connection string
            self.collection = self.db.job_instances

            # Test connection
            self.client.admin.command('ping')

        except ConnectionFailure as e:
            raise Exception(f"Failed to connect to MongoDB: {str(e)}")
        except Exception as e:
            raise Exception(f"Error connecting to MongoDB: {str(e)}")
    
    def create_job_instance(self, job_type: str, status: str = 'pending',
                          metadata: Optional[Dict] = None, check_running: bool = True,
                          customer_id: Optional[str] = None) -> str:
        """
        Create a new job instance

        Args:
            job_type: Type of job (e.g., 'news_fetch', 'github_sync')
            status: Initial status (default: 'pending')
            metadata: Additional metadata for the job
            check_running: Whether to check if a job of this type is already running
            customer_id: Customer ID for multi-tenant jobs (None for system-wide jobs)

        Returns:
            job_id: Unique identifier for the created job instance
        """
        try:
            # Check if there's already a running job of this type for this customer (if check_running is True)
            if check_running:
                query = {
                    'job_type': job_type,
                    'status': {'$in': ['pending', 'running']},
                    'cancelled': {'$ne': True}
                }

                # Add customer_id filter for multi-tenant jobs
                if customer_id is not None:
                    query['customer_id'] = customer_id
                else:
                    # For system-wide jobs, check for jobs with null customer_id
                    query['customer_id'] = None

                running_job = self.collection.find_one(query)
                if running_job:
                    customer_info = f" for customer {customer_id}" if customer_id else ""
                    raise Exception(f"Job of type '{job_type}'{customer_info} is already running (job_id: {running_job['job_id']})")

            job_id = str(uuid.uuid4())
            now = datetime.utcnow()

            job_doc = {
                'job_id': job_id,
                'job_type': job_type,
                'customer_id': customer_id,  # Add customer_id field
                'status': status,
                'created_at': now,
                'updated_at': now,
                'started_at': None,
                'completed_at': None,
                'error_message': None,
                'result': None,
                'metadata': metadata or {},
                'progress': 0,
                'total_items': 0,
                'cancelled': False
            }

            self.collection.insert_one(job_doc)
            return job_id

        except Exception as e:
            raise Exception(f"Error creating job instance: {str(e)}")
    
    def update_job_instance(self, job_id: str, status: Optional[str] = None,
                          error_message: Optional[str] = None,
                          result: Optional[Dict] = None,
                          metadata: Optional[Dict] = None,
                          progress: Optional[int] = None,
                          total_items: Optional[int] = None) -> bool:
        """Update an existing job instance"""
        try:
            now = datetime.utcnow()
            update_doc = {'updated_at': now}

            if status is not None:
                update_doc['status'] = status

                if status == 'running':
                    update_doc['started_at'] = now
                elif status in ['completed', 'failed']:
                    update_doc['completed_at'] = now

            if error_message is not None:
                update_doc['error_message'] = error_message

            if result is not None:
                update_doc['result'] = result

            if metadata is not None:
                update_doc['metadata'] = metadata

            if progress is not None:
                update_doc['progress'] = progress

            if total_items is not None:
                update_doc['total_items'] = total_items

            result = self.collection.update_one(
                {'job_id': job_id},
                {'$set': update_doc}
            )

            return result.modified_count > 0

        except Exception as e:
            raise Exception(f"Error updating job instance {job_id}: {str(e)}")
    
    def get_job_instance(self, job_id: str) -> Optional[Dict]:
        """Get a job instance by ID"""
        try:
            job_doc = self.collection.find_one({'job_id': job_id})

            if not job_doc:
                return None

            # Remove MongoDB's _id field and return the document
            job_doc.pop('_id', None)
            return job_doc

        except Exception as e:
            raise Exception(f"Error getting job instance {job_id}: {str(e)}")
    
    def list_job_instances(self, job_type: Optional[str] = None,
                         status: Optional[str] = None,
                         limit: int = 50,
                         customer_id: Optional[str] = None) -> List[Dict]:
        """
        List job instances with optional filtering

        Args:
            job_type: Filter by job type
            status: Filter by status
            limit: Maximum number of results
            customer_id: Filter by customer ID (None for system-wide jobs, omit to get all)

        Returns:
            List of job instances
        """
        try:
            query_filter = {}

            if job_type:
                query_filter['job_type'] = job_type

            if status:
                query_filter['status'] = status

            # Add customer_id filter if specified
            if customer_id is not None:
                query_filter['customer_id'] = customer_id

            cursor = self.collection.find(query_filter).sort('created_at', -1).limit(limit)

            jobs = []
            for job_doc in cursor:
                # Remove MongoDB's _id field
                job_doc.pop('_id', None)
                jobs.append(job_doc)

            return jobs

        except Exception as e:
            raise Exception(f"Error listing job instances: {str(e)}")
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a running or pending job"""
        try:
            result = self.collection.update_one(
                {
                    'job_id': job_id,
                    'status': {'$in': ['pending', 'running']}
                },
                {
                    '$set': {
                        'status': 'cancelled',
                        'cancelled': True,
                        'updated_at': datetime.utcnow(),
                        'completed_at': datetime.utcnow()
                    }
                }
            )
            return result.modified_count > 0
        except Exception as e:
            raise Exception(f"Error cancelling job: {str(e)}")

    def is_job_cancelled(self, job_id: str) -> bool:
        """Check if a job has been cancelled"""
        try:
            job = self.collection.find_one({'job_id': job_id})
            return job and job.get('cancelled', False)
        except Exception as e:
            raise Exception(f"Error checking job cancellation status: {str(e)}")

    def cancel_running_jobs_by_type(self, job_type: str, trigger: str = None) -> int:
        """
        Cancel all running or pending jobs of a specific type

        Args:
            job_type: Type of job to cancel
            trigger: Optional filter by trigger type ('manual' or 'scheduled')

        Returns:
            Number of jobs cancelled
        """
        try:
            query = {
                'job_type': job_type,
                'status': {'$in': ['pending', 'running']},
                'cancelled': {'$ne': True}
            }

            # If trigger is specified, only cancel jobs with that trigger type
            if trigger:
                query['metadata.trigger'] = trigger

            result = self.collection.update_many(
                query,
                {
                    '$set': {
                        'status': 'cancelled',
                        'cancelled': True,
                        'updated_at': datetime.utcnow(),
                        'completed_at': datetime.utcnow()
                    }
                }
            )
            return result.modified_count
        except Exception as e:
            raise Exception(f"Error cancelling running jobs: {str(e)}")

    def cleanup_old_jobs(self, days: int = 30) -> int:
        """Clean up job instances older than specified days"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            result = self.collection.delete_many({
                'created_at': {'$lt': cutoff_date},
                'status': {'$in': ['completed', 'failed', 'cancelled']}
            })

            return result.deleted_count

        except Exception as e:
            raise Exception(f"Error cleaning up old jobs: {str(e)}")

    def cleanup_stuck_jobs_on_startup(self, job_type: str) -> int:
        """
        Cancel all running/pending jobs of a specific type on service startup.
        This handles jobs that were left in 'running' state due to service crashes or restarts.

        Args:
            job_type: Type of job to cleanup

        Returns:
            Number of jobs cancelled
        """
        try:
            result = self.collection.update_many(
                {
                    'job_type': job_type,
                    'status': {'$in': ['pending', 'running']},
                    'cancelled': {'$ne': True}
                },
                {
                    '$set': {
                        'status': 'cancelled',
                        'cancelled': True,
                        'updated_at': datetime.utcnow(),
                        'completed_at': datetime.utcnow(),
                        'error_message': 'Job cancelled on service startup (cleanup of stuck jobs from previous session)'
                    }
                }
            )
            return result.modified_count
        except Exception as e:
            raise Exception(f"Error cleaning up stuck jobs on startup: {str(e)}")

    def close_connection(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
