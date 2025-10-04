"""
GitHub Repository Syncer Job
Main application that runs the sync job on schedule
"""
import os
import time
import schedule
import threading
from datetime import datetime
from flask import Flask, jsonify, request

from config.settings import Config
from services.syncer_service import GitHubRepoSyncerService
from utils.logger import setup_logger

# Initialize configuration and logger
config = Config()
logger = setup_logger('github-repo-syncer-app')

# Initialize services
syncer_service = GitHubRepoSyncerService()

# Flask app for health checks and manual triggers
app = Flask(__name__)

# Global state
last_sync_result = None

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    # Check if any sync jobs are currently active
    active_jobs = syncer_service.job_instance_service.get_active_jobs()
    sync_in_progress = len(active_jobs) > 0

    return jsonify({
        'status': 'healthy',
        'service': 'github-repo-syncer',
        'version': config.JOB_VERSION,
        'timestamp': datetime.now().isoformat(),
        'last_sync': last_sync_result.get('timestamp') if last_sync_result else None,
        'sync_in_progress': sync_in_progress,
        'active_jobs': len(active_jobs)
    })

@app.route('/sync', methods=['POST'])
def trigger_sync():
    """Manual sync trigger endpoint"""
    # Check if any sync jobs are currently active
    active_jobs = syncer_service.job_instance_service.get_active_jobs()
    if active_jobs:
        return jsonify({
            'status': 'error',
            'message': 'Sync already in progress',
            'active_jobs': len(active_jobs)
        }), 409
    
    # Create a bulk sync job instance
    job_id = syncer_service.job_instance_service.create_job_instance(
        job_type='bulk_sync',
        repository_id=None,
        metadata={'triggered_manually': True, 'sync_type': 'all_repositories'}
    )

    # Create cancellation event
    cancel_event = threading.Event()

    # Run sync in background thread
    thread = threading.Thread(target=run_sync_job, args=(job_id, cancel_event))
    thread.daemon = True
    thread.start()

    # Register the job thread
    syncer_service.register_job_thread(job_id, thread, cancel_event)

    # Get immediate job status to return to client
    job_status = syncer_service.job_instance_service.get_job_instance(job_id)

    return jsonify({
        'status': 'success',
        'message': 'Sync job started',
        'job_id': job_id,
        'job': {
            'id': job_id,
            'status': job_status['status'] if job_status else 'pending',
            'progress': job_status.get('progress', 0) if job_status else 0,
            'total_files': job_status.get('total_files', 0) if job_status else 0,
            'processed_files': job_status.get('processed_files', 0) if job_status else 0,
            'repository_id': None,  # bulk sync doesn't have single repository
            'created_at': job_status['created_at'] if job_status else None
        }
    })

@app.route('/sync/repository/<repository_id>', methods=['POST'])
def trigger_repository_sync(repository_id):
    """Manual sync trigger for specific repository (path parameter)"""
    return _trigger_repository_sync_internal(repository_id)

@app.route('/sync/repository', methods=['POST'])
def trigger_repository_sync_query():
    """Manual sync trigger for specific repository (query parameter)"""
    repository_id = request.args.get('repository_id')
    if not repository_id:
        return jsonify({
            'status': 'error',
            'error': 'repository_id query parameter is required'
        }), 400
    return _trigger_repository_sync_internal(repository_id)

def _trigger_repository_sync_internal(repository_id):
    """Manual sync trigger for specific repository"""

    # First, find the repository and get its internal ID
    repositories = syncer_service.get_active_repositories()
    target_repository = None
    internal_repo_id = repository_id  # Default to input ID

    for repo in repositories:
        # Check both internal ID and display name (full_name) formats
        if repo['id'] == repository_id or repo.get('full_name') == repository_id:
            target_repository = repo
            internal_repo_id = repo['id']  # Use the internal ID format
            break

    if not target_repository:
        return jsonify({
            'status': 'error',
            'message': f'Repository {repository_id} not found or not active'
        }), 404

    # Check if there's already an active job for this repository (using internal ID)
    active_jobs = syncer_service.job_instance_service.get_active_repository_jobs(internal_repo_id)
    if active_jobs:
        active_job = active_jobs[0]
        return jsonify({
            'status': 'error',
            'message': 'Sync already in progress for this repository',
            'job_id': active_job['id']
        }), 409

    # Create job instance with internal repository ID
    job_id = syncer_service.job_instance_service.create_job_instance(
        job_type='repository_sync',
        repository_id=internal_repo_id,
        metadata={'triggered_manually': True, 'display_name': repository_id}
    )

    # Create cancellation event
    cancel_event = threading.Event()

    # Run sync for specific repository in background thread (using internal ID)
    thread = threading.Thread(target=run_repository_sync, args=(internal_repo_id, job_id, cancel_event))
    thread.daemon = True
    thread.start()

    # Register the job thread with the syncer service
    syncer_service.register_job_thread(job_id, thread, cancel_event)

    # Get immediate job status to return to client
    job_status = syncer_service.job_instance_service.get_job_instance(job_id)

    return jsonify({
        'status': 'success',
        'message': f'Sync job started for repository {repository_id}',
        'job_id': job_id,
        'job': {
            'id': job_id,
            'status': job_status['status'] if job_status else 'pending',
            'progress': job_status.get('progress', 0) if job_status else 0,
            'total_files': job_status.get('total_files', 0) if job_status else 0,
            'processed_files': job_status.get('processed_files', 0) if job_status else 0,
            'repository_id': repository_id,
            'created_at': job_status['created_at'] if job_status else None
        }
    })

@app.route('/repositories', methods=['GET'])
def get_repositories():
    """Get all active repositories available for sync"""
    try:
        repositories = syncer_service.get_active_repositories()
        return jsonify({
            'status': 'success',
            'repositories': repositories,
            'count': len(repositories)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/job/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """Get job status by ID"""
    try:
        job = syncer_service.job_instance_service.get_job_instance(job_id)
        if not job:
            return jsonify({
                'status': 'error',
                'error': 'Job not found'
            }), 404

        return jsonify({
            'status': 'success',
            'job': job
        })
    except Exception as e:
        logger.error(f"Failed to get job status: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/job/<job_id>/cancel', methods=['POST'])
def cancel_job(job_id):
    """Cancel a specific job (customer-facing)"""
    try:
        job = syncer_service.job_instance_service.get_job_instance(job_id)
        if not job:
            return jsonify({
                'status': 'error',
                'error': 'Job not found'
            }), 404

        if job['status'] not in ['pending', 'running']:
            return jsonify({
                'status': 'error',
                'error': f'Cannot cancel job with status: {job["status"]}'
            }), 400

        # Signal the thread to cancel (if it's still running)
        thread_cancelled = syncer_service.cancel_job_thread(job_id)

        # Mark job as cancelled in database
        syncer_service.job_instance_service.update_job_status(
            job_id, 'cancelled',
            error_message='Job cancelled by user'
        )

        logger.info(f"Job {job_id} cancelled by user (thread signal sent: {thread_cancelled})")

        return jsonify({
            'status': 'success',
            'message': 'Job cancelled successfully',
            'job_id': job_id,
            'thread_cancelled': thread_cancelled
        })
    except Exception as e:
        logger.error(f"Failed to cancel job {job_id}: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/jobs/active', methods=['GET'])
def get_active_jobs():
    """Get all active jobs with details"""
    try:
        active_jobs = syncer_service.job_instance_service.get_active_jobs()

        # Enhance jobs with display names from metadata
        enhanced_jobs = []
        for job in active_jobs:
            enhanced_job = dict(job)

            # Parse metadata to get display name
            if job.get('metadata'):
                try:
                    import json
                    metadata = json.loads(job['metadata']) if isinstance(job['metadata'], str) else job['metadata']
                    if metadata.get('display_name'):
                        enhanced_job['display_name'] = metadata['display_name']
                except:
                    pass

            enhanced_jobs.append(enhanced_job)

        return jsonify({
            'status': 'success',
            'jobs': enhanced_jobs,
            'count': len(enhanced_jobs)
        })

    except Exception as e:
        logger.error(f"Failed to get active jobs: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/jobs/cleanup-all-stale', methods=['POST'])
def cleanup_all_stale_jobs():
    """Clean up all stale jobs regardless of age (customer-facing emergency cleanup)"""
    try:
        # Mark all pending/running jobs as failed
        stale_count = syncer_service.job_instance_service.cleanup_stale_jobs(max_age_minutes=0)

        return jsonify({
            'status': 'success',
            'message': f'Emergency cleanup: Marked {stale_count} jobs as failed',
            'stale_count': stale_count,
            'warning': 'This action cancelled all active jobs'
        })
    except Exception as e:
        logger.error(f"Failed to cleanup all stale jobs: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/status', methods=['GET'])
def get_status():
    """Get sync status and history"""
    # Check if any sync jobs are currently active
    active_jobs = syncer_service.job_instance_service.get_active_jobs()
    sync_in_progress = len(active_jobs) > 0

    return jsonify({
        'status': 'success',
        'sync_in_progress': sync_in_progress,
        'active_jobs': len(active_jobs),
        'last_sync_result': last_sync_result,
        'config': {
            'sync_frequency': config.SYNC_FREQUENCY,
            'sync_time': config.SYNC_TIME,
            'max_file_size_mb': config.MAX_FILE_SIZE_MB,
            'batch_size': config.BATCH_SIZE,
            'supported_extensions': config.SUPPORTED_EXTENSIONS
        }
    })

@app.route('/api-docs', methods=['GET'])
def api_docs():
    """API documentation"""
    docs = {
        'service': 'GitHub Repository Syncer',
        'version': config.JOB_VERSION,
        'endpoints': {
            'GET /health': 'Health check endpoint',
            'GET /status': 'Get current sync status and configuration',
            'GET /repositories': 'Get all active repositories available for sync',
            'GET /job/<id>': 'Get job status by ID',
            'POST /sync': 'Trigger manual sync for all repositories',
            'POST /sync/repository/<id>': 'Trigger manual sync for specific repository',
            'POST /job/<id>/cancel': 'Cancel a specific job (customer-facing)',
            'GET /api-docs': 'This API documentation'
        },
        'examples': {
            'trigger_sync': 'curl -X POST http://localhost:8092/sync',
            'sync_specific_repository': 'curl -X POST http://localhost:8092/sync/repository/abc-123',
            'get_repositories': 'curl http://localhost:8092/repositories'
        }
    }

    return jsonify(docs)

def run_sync_job(job_id: str = None, cancel_event: threading.Event = None):
    """Run the sync job with cancellation support"""
    global last_sync_result

    # For manual jobs, don't check for active jobs since we have job_id tracking
    if not job_id:
        # Check if any sync jobs are currently active (for scheduled jobs)
        active_jobs = syncer_service.job_instance_service.get_active_jobs()
        if active_jobs:
            logger.warning("Sync job already in progress, skipping")
            return

    start_time = time.time()

    try:
        logger.info("🚀 Starting scheduled sync job")

        # Validate configuration
        config.validate()

        # Update job status if we have a job_id
        if job_id:
            syncer_service.job_instance_service.update_job_status(job_id, 'running')

        # Run sync
        result = syncer_service.sync_all_repositories()

        # Update global state
        last_sync_result = {
            **result,
            'timestamp': datetime.now().isoformat(),
            'duration_seconds': int(time.time() - start_time)
        }

        # Update job status if we have a job_id
        if job_id:
            if result['status'] == 'success':
                syncer_service.job_instance_service.update_job_status(job_id, 'completed')
            else:
                syncer_service.job_instance_service.update_job_status(
                    job_id, 'failed',
                    error_message=result.get('error', 'Unknown error')
                )

        if result['status'] == 'success':
            logger.info(
                f"✅ Sync job completed successfully: "
                f"{result['successful_syncs']}/{result['repositories_processed']} repositories, "
                f"{result['total_files']} files processed"
            )
        else:
            logger.error(f"❌ Sync job failed: {result.get('error', 'Unknown error')}")

    except Exception as e:
        error_msg = f"Sync job failed with exception: {str(e)}"
        logger.error(error_msg)

        # Update job status if we have a job_id
        if job_id:
            syncer_service.job_instance_service.update_job_status(
                job_id, 'failed',
                error_message=error_msg
            )

        last_sync_result = {
            'status': 'error',
            'error': error_msg,
            'timestamp': datetime.now().isoformat(),
            'duration_seconds': int(time.time() - start_time),
            'repositories_processed': 0,
            'total_files': 0
        }

    finally:
        # Always unregister the job thread when done
        if job_id:
            syncer_service.unregister_job_thread(job_id)

def run_repository_sync(repository_id: str, job_id: str = None, cancel_event: threading.Event = None):
    """Run sync for a specific repository with cancellation support"""
    global last_sync_result

    start_time = time.time()

    try:
        logger.info(f"🚀 Starting sync for repository: {repository_id}")

        # Get the specific repository
        repositories = syncer_service.get_active_repositories()
        target_repository = None

        for repo in repositories:
            # Check both internal ID and display name (full_name) formats
            if repo['id'] == repository_id or repo.get('full_name') == repository_id:
                target_repository = repo
                break

        if not target_repository:
            error_msg = f"Repository {repository_id} not found or not active"
            logger.error(error_msg)

            last_sync_result = {
                'status': 'error',
                'error': error_msg,
                'timestamp': datetime.now().isoformat(),
                'duration_seconds': int(time.time() - start_time),
                'repositories_processed': 0,
                'total_files': 0
            }
            return

        # Sync the specific repository with cancellation support
        result = syncer_service.sync_repository(target_repository, job_id, cancel_event)

        # Update global state
        last_sync_result = {
            'status': result['status'],
            'message': f"Single repository sync: {result['message']}",
            'repository_id': repository_id,
            'repository_name': target_repository.get('name', 'Unknown'),
            'files_processed': result.get('files_processed', 0),
            'files_indexed': result.get('files_indexed', 0),
            'timestamp': datetime.now().isoformat(),
            'duration_seconds': int(time.time() - start_time),
            'repositories_processed': 1,
            'total_files': result.get('files_processed', 0)
        }

        if result['status'] == 'success':
            # Update job status to completed
            if job_id:
                syncer_service.job_instance_service.update_job_status(
                    job_id, 'completed'
                )

            logger.info(
                f"✅ Repository sync completed successfully: "
                f"{target_repository.get('name', 'Unknown')}, "
                f"{result.get('files_processed', 0)} files processed"
            )
        elif result['status'] == 'cancelled':
            # Update job status to cancelled
            if job_id:
                syncer_service.job_instance_service.update_job_status(
                    job_id, 'cancelled'
                )

            logger.info(f"🚫 Repository sync cancelled: {target_repository.get('name', 'Unknown')}")
        else:
            # Update job status to failed
            if job_id:
                syncer_service.job_instance_service.update_job_status(
                    job_id, 'failed',
                    error_message=result.get('error', 'Unknown error')
                )

            logger.error(f"❌ Repository sync failed: {result.get('error', 'Unknown error')}")

    except Exception as e:
        error_msg = f"Repository sync failed with exception: {str(e)}"
        logger.error(error_msg)

        # Update job status if we have a job_id
        if job_id:
            syncer_service.job_instance_service.update_job_status(
                job_id, 'failed',
                error_message=error_msg
            )

        last_sync_result = {
            'status': 'error',
            'error': error_msg,
            'timestamp': datetime.now().isoformat(),
            'duration_seconds': int(time.time() - start_time),
            'repositories_processed': 0,
            'total_files': 0
        }

    finally:
        # Always unregister the job thread when done
        if job_id:
            syncer_service.unregister_job_thread(job_id)

def setup_scheduler():
    """Setup job scheduler based on configuration"""
    if config.SYNC_FREQUENCY == 'daily':
        schedule.every().day.at(config.SYNC_TIME).do(run_sync_job)
        logger.info(f"Scheduled daily sync at {config.SYNC_TIME}")

    elif config.SYNC_FREQUENCY == 'hourly':
        schedule.every().hour.do(run_sync_job)
        logger.info("Scheduled hourly sync")

    elif config.SYNC_FREQUENCY == 'weekly':
        # Parse day and time for weekly schedule
        schedule.every().monday.at(config.SYNC_TIME).do(run_sync_job)
        logger.info(f"Scheduled weekly sync on Monday at {config.SYNC_TIME}")

    else:
        logger.warning(f"Unknown sync frequency: {config.SYNC_FREQUENCY}")

def run_scheduler():
    """Run the job scheduler"""
    logger.info("Starting job scheduler...")

    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
        except Exception as e:
            logger.error(f"Scheduler error: {str(e)}")
            time.sleep(60)

def main():
    """Main application entry point"""
    logger.info(f"🚀 Starting GitHub Repository Syncer v{config.JOB_VERSION}")

    try:
        # Validate configuration
        config.validate()
        logger.info("Configuration validated successfully")

        # Setup scheduler
        setup_scheduler()

        # Start scheduler in background thread
        scheduler_thread = threading.Thread(target=run_scheduler)
        scheduler_thread.daemon = True
        scheduler_thread.start()

        # Run initial sync if requested
        if os.getenv('RUN_INITIAL_SYNC', 'false').lower() == 'true':
            logger.info("Running initial sync...")
            initial_thread = threading.Thread(target=run_sync_job)
            initial_thread.daemon = True
            initial_thread.start()

        # Start Flask app for health checks
        logger.info(f"Starting health check server on port {config.HEALTH_CHECK_PORT}")
        app.run(
            host='0.0.0.0',
            port=config.HEALTH_CHECK_PORT,
            debug=False,
            use_reloader=False
        )

    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        raise

if __name__ == '__main__':
    main()
