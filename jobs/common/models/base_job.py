"""
Base Job Class - Common framework for all job implementations with parallel task support
"""

import os
import sys
import threading
import time
import uuid
import concurrent.futures
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from flask import Flask, jsonify, request
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

# Add common directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from common.services.job_instance_service import JobInstanceService
from common.utils.logger import setup_logger

class BaseJob(ABC):
    """
    Abstract base class for all job implementations
    Provides common functionality like scheduling, job tracking, and Flask endpoints
    """
    
    def __init__(self, job_name: str, config_class):
        self.job_name = job_name
        self.config = config_class
        self.logger = setup_logger(job_name, config_class.LOG_FILE)

        # Threading configuration
        self.max_threads = getattr(config_class, 'MAX_THREADS', 1)
        self.current_threads = 0
        self.thread_lock = threading.Lock()

        # Parallel task configuration
        self.max_parallel_tasks = getattr(config_class, 'MAX_PARALLEL_TASKS', 3)
        self.task_executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.max_parallel_tasks)

        # Initialize Flask app
        self.app = Flask(__name__)
        self.app.config.from_object(config_class)

        # Initialize services
        self.job_instance_service = JobInstanceService(config_class.MONGODB_URL)

        # Initialize scheduler
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()

        # Setup Flask routes
        self._setup_routes()

        # Setup scheduled job if interval is specified
        if (hasattr(config_class, 'JOB_INTERVAL_MINUTES') and config_class.JOB_INTERVAL_MINUTES > 0) or \
           (hasattr(config_class, 'JOB_INTERVAL_SECONDS') and config_class.JOB_INTERVAL_SECONDS > 0):
            self._setup_scheduled_job()
    
    @abstractmethod
    def run_job(self, job_id: str, is_on_demand: bool = False, **kwargs) -> Dict[str, Any]:
        """
        Abstract method that must be implemented by each job

        Args:
            job_id: Unique identifier for this job execution
            is_on_demand: True if this is a manual/on-demand job, False for scheduled jobs
            **kwargs: Additional parameters for the job

        Returns:
            Dict containing job results and metadata
        """
        pass
    
    @abstractmethod
    def get_job_type(self) -> str:
        """Return the job type identifier"""
        pass

    def get_parallel_tasks(self) -> List[Dict[str, Any]]:
        """
        Override this method to define parallel tasks for the job

        Returns:
            List of task definitions, each containing:
            {
                'name': 'task_name',
                'function': callable_function,
                'args': tuple_of_args,
                'kwargs': dict_of_kwargs
            }
        """
        return []

    def validate_job_params(self, params: Dict) -> Dict[str, str]:
        """
        Validate job parameters

        Args:
            params: Parameters to validate

        Returns:
            Dict of validation errors (empty if valid)
        """
        return {}

    def run_parallel_tasks(self, job_id: str, **kwargs) -> Dict[str, Any]:
        """
        Execute all parallel tasks defined by the job

        Args:
            job_id: Unique identifier for this job execution
            **kwargs: Additional parameters passed to tasks

        Returns:
            Dict containing results from all tasks
        """
        tasks = self.get_parallel_tasks()
        if not tasks:
            self.logger.info(f"No parallel tasks defined for job {job_id}")
            return {'tasks': [], 'total_tasks': 0}

        self.logger.info(f"🔄 Starting {len(tasks)} parallel tasks for job {job_id}")

        # Prepare task results
        task_results = {
            'tasks': [],
            'total_tasks': len(tasks),
            'successful_tasks': 0,
            'failed_tasks': 0,
            'task_details': {}
        }

        # Submit all tasks to thread pool
        future_to_task = {}
        for task in tasks:
            task_name = task.get('name', 'unnamed_task')
            task_function = task.get('function')
            task_args = task.get('args', ())
            task_kwargs = task.get('kwargs', {})

            if not callable(task_function):
                self.logger.error(f"❌ Task '{task_name}' function is not callable")
                task_results['failed_tasks'] += 1
                task_results['task_details'][task_name] = {
                    'status': 'failed',
                    'error': 'Task function is not callable'
                }
                continue

            # Add job_id to task kwargs
            task_kwargs['job_id'] = job_id
            task_kwargs.update(kwargs)

            self.logger.info(f"🚀 Submitting task: {task_name}")
            future = self.task_executor.submit(
                self._execute_task_with_logging,
                task_name,
                task_function,
                task_args,
                task_kwargs
            )
            future_to_task[future] = task_name

        # Wait for all tasks to complete
        for future in concurrent.futures.as_completed(future_to_task):
            task_name = future_to_task[future]
            try:
                result = future.result()
                task_results['successful_tasks'] += 1
                task_results['task_details'][task_name] = {
                    'status': 'completed',
                    'result': result
                }
                self.logger.info(f"✅ Task '{task_name}' completed successfully")

            except Exception as e:
                task_results['failed_tasks'] += 1
                task_results['task_details'][task_name] = {
                    'status': 'failed',
                    'error': str(e)
                }
                self.logger.error(f"❌ Task '{task_name}' failed: {str(e)}")

        self.logger.info(f"🏁 Parallel tasks completed: {task_results['successful_tasks']} successful, {task_results['failed_tasks']} failed")
        return task_results

    def _execute_task_with_logging(self, task_name: str, task_function: Callable, args: tuple, kwargs: dict) -> Any:
        """
        Execute a single task with proper logging and error handling

        Args:
            task_name: Name of the task
            task_function: Function to execute
            args: Positional arguments for the function
            kwargs: Keyword arguments for the function

        Returns:
            Result from the task function
        """
        start_time = datetime.utcnow()
        self.logger.info(f"🔧 Executing task: {task_name}")

        try:
            result = task_function(*args, **kwargs)
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            self.logger.info(f"⏱️ Task '{task_name}' completed in {execution_time:.2f} seconds")
            return result

        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            self.logger.error(f"💥 Task '{task_name}' failed after {execution_time:.2f} seconds: {str(e)}")
            raise

    def _setup_routes(self):
        """Setup common Flask routes"""
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            try:
                return jsonify({
                    'status': 'healthy',
                    'service': self.job_name,
                    'job_type': self.get_job_type(),
                    'timestamp': datetime.utcnow().isoformat(),
                    'scheduler_running': self.scheduler.running
                }), 200
            except Exception as e:
                self.logger.error(f"Health check failed: {str(e)}")
                return jsonify({
                    'status': 'unhealthy',
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                }), 500
        
        @self.app.route('/run', methods=['POST'])
        def trigger_job():
            """Manually trigger job execution"""
            try:
                # Get job parameters from request
                params = request.get_json() or {}

                # Validate parameters
                validation_errors = self.validate_job_params(params)
                if validation_errors:
                    return jsonify({
                        'error': 'Invalid parameters',
                        'validation_errors': validation_errors
                    }), 400

                self.logger.info(f"Manual {self.get_job_type()} job triggered")

                # Cancel any existing running jobs of this type (manual or scheduled) before starting new on-demand job
                # This ensures on-demand jobs always start fresh and take priority
                cancelled_count = self.job_instance_service.cancel_running_jobs_by_type(
                    self.get_job_type()
                )
                if cancelled_count > 0:
                    self.logger.info(f"Cancelled {cancelled_count} existing running job(s) of type {self.get_job_type()}")

                # Create job instance (skip running check since we just cancelled existing jobs)
                job_id = self.job_instance_service.create_job_instance(
                    job_type=self.get_job_type(),
                    status='running',
                    metadata={
                        'trigger': 'manual',
                        'started_at': datetime.utcnow().isoformat(),
                        'params': params
                    },
                    check_running=False  # Skip check since we just cancelled existing jobs
                )
                
                # Run job in background thread with thread management
                def run_job_async():
                    with self.thread_lock:
                        self.current_threads += 1

                    try:
                        # Check if job was cancelled before starting
                        if self.job_instance_service.is_job_cancelled(job_id):
                            self.logger.info(f"Job {job_id} was cancelled before execution")
                            return

                        # Update job status to running
                        self.job_instance_service.update_job_instance(
                            job_id,
                            status='running',
                            metadata={'started_at': datetime.utcnow().isoformat()}
                        )

                        # Execute the job with cancellation checks (manual job)
                        result = self.run_job(job_id, is_on_demand=True, **params)

                        # Check if job was cancelled during execution
                        if self.job_instance_service.is_job_cancelled(job_id):
                            self.logger.info(f"Job {job_id} was cancelled during execution")
                            return

                        self.job_instance_service.update_job_instance(
                            job_id,
                            status='completed',
                            result=result,
                            metadata={'completed_at': datetime.utcnow().isoformat()}
                        )
                        self.logger.info(f"Manual {self.get_job_type()} job completed. Job ID: {job_id}")
                    except Exception as e:
                        self.logger.error(f"Error in manual {self.get_job_type()} job: {str(e)}")
                        self.job_instance_service.update_job_instance(
                            job_id,
                            status='failed',
                            error_message=str(e),
                            metadata={'failed_at': datetime.utcnow().isoformat()}
                        )
                    finally:
                        with self.thread_lock:
                            self.current_threads -= 1

                # Check thread limit before starting
                if self.current_threads >= self.max_threads:
                    return jsonify({
                        'status': 'error',
                        'message': f'Maximum threads ({self.max_threads}) already running'
                    }), 429

                thread = threading.Thread(target=run_job_async)
                thread.daemon = True
                thread.start()
                
                return jsonify({
                    'message': f'{self.get_job_type()} job started',
                    'job_id': job_id,
                    'status': 'running'
                }), 202
                
            except Exception as e:
                self.logger.error(f"Error triggering manual job: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/status/<job_id>', methods=['GET'])
        def get_job_status(job_id):
            """Get status of a specific job"""
            try:
                job = self.job_instance_service.get_job_instance(job_id)
                if not job:
                    return jsonify({'error': 'Job not found'}), 404

                return jsonify(job), 200

            except Exception as e:
                self.logger.error(f"Error getting job status: {str(e)}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/cancel/<job_id>', methods=['POST'])
        def cancel_job(job_id):
            """Cancel a running or pending job"""
            try:
                success = self.job_instance_service.cancel_job(job_id)
                if not success:
                    return jsonify({
                        'error': 'Job not found or cannot be cancelled (already completed/failed)'
                    }), 404

                self.logger.info(f"Job {job_id} cancelled successfully")
                return jsonify({
                    'message': f'Job {job_id} cancelled successfully',
                    'job_id': job_id,
                    'status': 'cancelled'
                }), 200

            except Exception as e:
                self.logger.error(f"Error cancelling job: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/jobs', methods=['GET'])
        def list_jobs():
            """List recent job instances"""
            try:
                limit = request.args.get('limit', 50, type=int)
                status = request.args.get('status')
                
                jobs = self.job_instance_service.list_job_instances(
                    job_type=self.get_job_type(),
                    status=status,
                    limit=limit
                )
                
                return jsonify({
                    'jobs': jobs,
                    'count': len(jobs),
                    'job_type': self.get_job_type()
                }), 200
                
            except Exception as e:
                self.logger.error(f"Error listing jobs: {str(e)}")
                return jsonify({'error': str(e)}), 500
    
    def _setup_scheduled_job(self):
        """Setup scheduled job execution"""
        def scheduled_job_wrapper():
            """Wrapper for scheduled job execution with overlap prevention"""
            job_id = None
            try:
                # Check if there's already a running job of this type
                running_jobs_count = self.job_instance_service.collection.count_documents({
                    'job_type': self.get_job_type(),
                    'status': {'$in': ['pending', 'running']},
                    'cancelled': {'$ne': True}
                })

                if running_jobs_count > 0:
                    self.logger.info(f"Skipping scheduled {self.get_job_type()} job - previous job still running")
                    return

                self.logger.info(f"Starting scheduled {self.get_job_type()} job")

                # Create job instance
                job_id = self.job_instance_service.create_job_instance(
                    job_type=self.get_job_type(),
                    status='running',
                    metadata={
                        'trigger': 'scheduled',
                        'started_at': datetime.utcnow().isoformat()
                    },
                    check_running=False  # We already checked above
                )

                # Run the job (scheduled job)
                result = self.run_job(job_id, is_on_demand=False)

                # Check if job was cancelled during execution
                if self.job_instance_service.is_job_cancelled(job_id):
                    self.logger.info(f"Scheduled job {job_id} was cancelled during execution")
                    return

                # Update job instance with results
                self.job_instance_service.update_job_instance(
                    job_id,
                    status='completed',
                    result=result,
                    metadata={'completed_at': datetime.utcnow().isoformat()}
                )

                self.logger.info(f"Scheduled {self.get_job_type()} job completed successfully. Job ID: {job_id}")

            except Exception as e:
                self.logger.error(f"Error in scheduled {self.get_job_type()} job: {str(e)}")
                if job_id:
                    self.job_instance_service.update_job_instance(
                        job_id,
                        status='failed',
                        error_message=str(e),
                        metadata={'failed_at': datetime.utcnow().isoformat()}
                    )
        
        # Schedule the job with overlap prevention
        # Support both minutes and seconds configuration
        if hasattr(self.config, 'JOB_INTERVAL_SECONDS') and self.config.JOB_INTERVAL_SECONDS > 0:
            trigger = IntervalTrigger(seconds=self.config.JOB_INTERVAL_SECONDS)
            interval_desc = f"{self.config.JOB_INTERVAL_SECONDS} seconds"
        else:
            trigger = IntervalTrigger(minutes=self.config.JOB_INTERVAL_MINUTES)
            interval_desc = f"{self.config.JOB_INTERVAL_MINUTES} minutes"

        self.scheduler.add_job(
            func=scheduled_job_wrapper,
            trigger=trigger,
            id=f'{self.job_name}_scheduled_job',
            name=f'Scheduled {self.job_name} job',
            replace_existing=False,  # Don't replace existing scheduled jobs
            max_instances=1  # Only allow one instance of this job to run at a time
        )

        self.logger.info(f"Scheduled job setup: {self.job_name} every {interval_desc}")
    
    def run_flask_app(self):
        """Run the Flask application"""
        self.logger.info(f"Starting {self.job_name} Job Service")
        self.logger.info(f"Scheduler running: {self.scheduler.running}")
        
        self.app.run(
            host=self.config.FLASK_HOST,
            port=self.config.FLASK_PORT,
            debug=self.config.FLASK_DEBUG
        )
    
    def shutdown(self):
        """Gracefully shutdown the job service"""
        self.logger.info(f"Shutting down {self.job_name} Job Service")
        if self.scheduler.running:
            self.scheduler.shutdown()
        self.logger.info(f"{self.job_name} Job Service shutdown complete")
