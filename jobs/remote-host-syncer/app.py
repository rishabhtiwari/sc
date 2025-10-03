"""
Remote Host Syncer Job
Main application that runs the sync job on schedule
"""
import os
import time
import schedule
import threading
from datetime import datetime
from flask import Flask, jsonify, request

from config.settings import Config
from services.syncer_service import RemoteHostSyncerService
from utils.logger import setup_logger

# Initialize configuration and logger
config = Config()
logger = setup_logger('remote-host-syncer-app')

# Initialize services
syncer_service = RemoteHostSyncerService()

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
        'service': 'remote-host-syncer',
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
        connection_id=None,
        metadata={'triggered_manually': True, 'sync_type': 'all_connections'}
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
            'connection_id': None,  # bulk sync doesn't have single connection
            'created_at': job_status['created_at'] if job_status else None
        }
    })

@app.route('/sync/connection/<connection_id>', methods=['POST'])
def trigger_connection_sync(connection_id):
    """Manual sync trigger for specific connection"""

    # Check if there's already an active job for this connection
    active_jobs = syncer_service.job_instance_service.get_active_connection_jobs(connection_id)
    if active_jobs:
        active_job = active_jobs[0]
        return jsonify({
            'status': 'error',
            'message': 'Sync already in progress for this connection',
            'job_id': active_job['id']
        }), 409

    # Create job instance first
    job_id = syncer_service.job_instance_service.create_job_instance(
        job_type='connection_sync',
        connection_id=connection_id,
        metadata={'triggered_manually': True}
    )

    # Create cancellation event
    cancel_event = threading.Event()

    # Run sync for specific connection in background thread
    thread = threading.Thread(target=run_connection_sync, args=(connection_id, job_id, cancel_event))
    thread.daemon = True
    thread.start()

    # Register the job thread with the syncer service
    syncer_service.register_job_thread(job_id, thread, cancel_event)

    # Get immediate job status to return to client
    job_status = syncer_service.job_instance_service.get_job_instance(job_id)

    return jsonify({
        'status': 'success',
        'message': f'Sync job started for connection {connection_id}',
        'job_id': job_id,
        'job': {
            'id': job_id,
            'status': job_status['status'] if job_status else 'pending',
            'progress': job_status.get('progress', 0) if job_status else 0,
            'total_files': job_status.get('total_files', 0) if job_status else 0,
            'processed_files': job_status.get('processed_files', 0) if job_status else 0,
            'connection_id': connection_id,
            'created_at': job_status['created_at'] if job_status else None
        }
    })

@app.route('/sync/force', methods=['POST'])
def force_sync():
    """Force sync even if one is in progress (use with caution)"""
    # Run sync in background thread regardless of current state
    thread = threading.Thread(target=run_sync_job)
    thread.daemon = True
    thread.start()

    return jsonify({
        'status': 'success',
        'message': 'Force sync job started',
        'warning': 'This may cause conflicts if another sync is running'
    })

@app.route('/connections', methods=['GET'])
def get_connections():
    """Get all active connections available for sync"""
    try:
        connections = syncer_service.get_active_connections()
        return jsonify({
            'status': 'success',
            'connections': connections,
            'count': len(connections)
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

@app.route('/jobs/connection/<connection_id>', methods=['GET'])
def get_connection_jobs(connection_id):
    """Get recent jobs for a connection"""
    try:
        limit = request.args.get('limit', 10, type=int)
        jobs = syncer_service.job_instance_service.get_connection_jobs(connection_id, limit)

        return jsonify({
            'status': 'success',
            'jobs': jobs,
            'count': len(jobs)
        })
    except Exception as e:
        logger.error(f"Failed to get connection jobs: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/jobs/active', methods=['GET'])
def get_active_jobs():
    """Get all active jobs"""
    try:
        jobs = syncer_service.job_instance_service.get_active_jobs()

        return jsonify({
            'status': 'success',
            'jobs': jobs,
            'count': len(jobs)
        })
    except Exception as e:
        logger.error(f"Failed to get active jobs: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/jobs/cleanup-stale', methods=['POST'])
def cleanup_stale_jobs():
    """Clean up stale jobs (mark as failed)"""
    try:
        max_age_minutes = request.json.get('max_age_minutes', 30) if request.json else 30
        stale_count = syncer_service.job_instance_service.cleanup_stale_jobs(max_age_minutes)

        return jsonify({
            'status': 'success',
            'message': f'Marked {stale_count} stale jobs as failed',
            'stale_count': stale_count
        })
    except Exception as e:
        logger.error(f"Failed to cleanup stale jobs: {str(e)}")
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

@app.route('/jobs/threads', methods=['GET'])
def get_active_job_threads():
    """Get information about active job threads (admin endpoint)"""
    try:
        # Clean up finished threads first
        syncer_service.cleanup_finished_threads()

        active_threads = syncer_service.get_active_job_threads()

        # Convert thread info to serializable format
        thread_info = {}
        for job_id, info in active_threads.items():
            thread_info[job_id] = {
                'is_alive': info['thread'].is_alive(),
                'registered_at': info['registered_at'],
                'cancel_event_set': info['cancel_event'].is_set()
            }

        return jsonify({
            'status': 'success',
            'active_threads': thread_info,
            'total_active': len(thread_info)
        })

    except Exception as e:
        logger.error(f"Failed to get active job threads: {str(e)}")
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

@app.route('/history/clear', methods=['DELETE'])
def clear_history():
    """Clear all sync history and job instances (admin endpoint)"""
    try:
        import sqlite3

        with sqlite3.connect(config.DB_PATH) as conn:
            cursor = conn.cursor()

            # Get list of existing tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            history_deleted = 0
            jobs_deleted = 0
            files_deleted = 0

            # Clear sync history if table exists
            if 'sync_history' in tables:
                cursor.execute('DELETE FROM sync_history')
                history_deleted = cursor.rowcount

            # Clear job instances if table exists
            if 'job_instances' in tables:
                cursor.execute('DELETE FROM job_instances')
                jobs_deleted = cursor.rowcount

            # Clear file sync state if table exists
            if 'file_sync_state' in tables:
                cursor.execute('DELETE FROM file_sync_state')
                files_deleted = cursor.rowcount

            conn.commit()

        # Vacuum outside of transaction
        with sqlite3.connect(config.DB_PATH) as conn:
            conn.execute('VACUUM')

        return jsonify({
            'status': 'success',
            'message': 'All history cleared successfully',
            'sync_history_deleted': history_deleted,
            'job_instances_deleted': jobs_deleted,
            'file_sync_state_deleted': files_deleted,
            'tables_found': tables
        })
    except Exception as e:
        logger.error(f"Failed to clear history: {str(e)}")
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

@app.route('/history', methods=['GET'])
def get_sync_history():
    """Get sync history from database"""
    try:
        import sqlite3
        from datetime import datetime, timedelta

        # Get query parameters
        limit = request.args.get('limit', 50, type=int)
        days = request.args.get('days', 7, type=int)
        connection_id = request.args.get('connection_id')

        # Calculate date filter
        since_date = datetime.now() - timedelta(days=days)

        with sqlite3.connect(config.DB_PATH) as conn:
            cursor = conn.cursor()

            # Build query
            query = '''
                SELECT id, connection_id, sync_started_at, sync_completed_at,
                       status, files_processed, files_indexed, error_message
                FROM sync_history
                WHERE sync_started_at >= ?
            '''
            params = [since_date.isoformat()]

            if connection_id:
                query += ' AND connection_id = ?'
                params.append(connection_id)

            query += ' ORDER BY sync_started_at DESC LIMIT ?'
            params.append(limit)

            cursor.execute(query, params)

            columns = [desc[0] for desc in cursor.description]
            history = [dict(zip(columns, row)) for row in cursor.fetchall()]

            return jsonify({
                'status': 'success',
                'history': history,
                'count': len(history),
                'filters': {
                    'limit': limit,
                    'days': days,
                    'connection_id': connection_id
                }
            })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api-docs', methods=['GET'])
def api_docs():
    """API documentation"""
    docs = {
        'service': 'Remote Host Syncer',
        'version': config.JOB_VERSION,
        'endpoints': {
            'GET /health': 'Health check endpoint',
            'GET /status': 'Get current sync status and configuration',
            'GET /connections': 'Get all active connections available for sync',
            'GET /history': 'Get sync history (query params: limit, days, connection_id)',
            'GET /job/<id>': 'Get job status by ID',
            'GET /jobs/active': 'Get all active jobs',
            'GET /jobs/connection/<id>': 'Get recent jobs for a connection',
            'POST /sync': 'Trigger manual sync for all connections',
            'POST /sync/connection/<id>': 'Trigger manual sync for specific connection',
            'POST /sync/force': 'Force sync even if one is in progress (use with caution)',
            'POST /job/<id>/cancel': 'Cancel a specific job (customer-facing)',
            'POST /jobs/cleanup-stale': 'Clean up stale jobs (admin)',
            'POST /jobs/cleanup-all-stale': 'Emergency cleanup of all active jobs (customer-facing)',
            'GET /api-docs': 'This API documentation'
        },
        'examples': {
            'trigger_sync': 'curl -X POST http://localhost:8091/sync',
            'sync_specific_connection': 'curl -X POST http://localhost:8091/sync/connection/abc-123',
            'get_history': 'curl "http://localhost:8091/history?limit=10&days=1"',
            'get_connections': 'curl http://localhost:8091/connections'
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
        result = syncer_service.sync_all_connections()

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
                f"{result['successful_syncs']}/{result['connections_processed']} connections, "
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
            'connections_processed': 0,
            'total_files': 0
        }

    finally:
        # Always unregister the job thread when done
        if job_id:
            syncer_service.unregister_job_thread(job_id)

def run_connection_sync(connection_id: str, job_id: str = None, cancel_event: threading.Event = None):
    """Run sync for a specific connection with cancellation support"""
    global last_sync_result

    start_time = time.time()

    try:
        logger.info(f"🚀 Starting sync for connection: {connection_id}")

        # Get the specific connection
        connections = syncer_service.get_active_connections()
        target_connection = None

        for conn in connections:
            if conn['id'] == connection_id:
                target_connection = conn
                break

        if not target_connection:
            error_msg = f"Connection {connection_id} not found or not active"
            logger.error(error_msg)

            last_sync_result = {
                'status': 'error',
                'error': error_msg,
                'timestamp': datetime.now().isoformat(),
                'duration_seconds': int(time.time() - start_time),
                'connections_processed': 0,
                'total_files': 0
            }
            return

        # Sync the specific connection with cancellation support
        result = syncer_service.sync_connection(target_connection, job_id, cancel_event)

        # Update global state
        last_sync_result = {
            'status': result['status'],
            'message': f"Single connection sync: {result['message']}",
            'connection_id': connection_id,
            'connection_name': target_connection.get('name', 'Unknown'),
            'files_processed': result.get('files_processed', 0),
            'files_indexed': result.get('files_indexed', 0),
            'timestamp': datetime.now().isoformat(),
            'duration_seconds': int(time.time() - start_time),
            'connections_processed': 1,
            'total_files': result.get('files_processed', 0)
        }

        if result['status'] == 'success':
            logger.info(
                f"✅ Connection sync completed successfully: "
                f"{target_connection.get('name', 'Unknown')}, "
                f"{result.get('files_processed', 0)} files processed"
            )
        elif result['status'] == 'cancelled':
            logger.info(f"🚫 Connection sync cancelled: {target_connection.get('name', 'Unknown')}")
        else:
            logger.error(f"❌ Connection sync failed: {result.get('error', 'Unknown error')}")

    except Exception as e:
        error_msg = f"Connection sync failed with exception: {str(e)}"
        logger.error(error_msg)

        last_sync_result = {
            'status': 'error',
            'error': error_msg,
            'timestamp': datetime.now().isoformat(),
            'duration_seconds': int(time.time() - start_time),
            'connections_processed': 0,
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

def recover_interrupted_jobs():
    """Recover jobs that were interrupted by service restart"""
    try:
        logger.info("🔄 Checking for interrupted jobs...")

        # Get all active jobs
        active_jobs = syncer_service.job_instance_service.get_active_jobs()

        if not active_jobs:
            logger.info("No interrupted jobs found")
            return

        logger.info(f"Found {len(active_jobs)} interrupted jobs")

        # Mark old jobs as failed (they were interrupted by restart)
        for job in active_jobs:
            job_id = job['id']
            connection_id = job.get('connection_id')

            # Check if job is truly stale (older than 5 minutes)
            from datetime import datetime, timedelta
            updated_at = datetime.fromisoformat(job['updated_at'].replace('Z', '+00:00'))
            if datetime.utcnow() - updated_at.replace(tzinfo=None) > timedelta(minutes=5):
                syncer_service.job_instance_service.update_job_status(
                    job_id, 'failed',
                    error_message='Job interrupted by service restart'
                )
                logger.info(f"Marked interrupted job {job_id} as failed")

                # Optionally restart the job for the connection
                if connection_id and os.getenv('AUTO_RESTART_INTERRUPTED_JOBS', 'false').lower() == 'true':
                    logger.info(f"Auto-restarting sync for connection {connection_id}")
                    # Start new job in background
                    thread = threading.Thread(target=run_connection_sync, args=(connection_id, None))
                    thread.daemon = True
                    thread.start()
            else:
                logger.info(f"Job {job_id} appears to be recently active, keeping as-is")

    except Exception as e:
        logger.error(f"Failed to recover interrupted jobs: {str(e)}")

def main():
    """Main application entry point"""
    logger.info(f"🚀 Starting Remote Host Syncer v{config.JOB_VERSION}")

    try:
        # Validate configuration
        config.validate()
        logger.info("Configuration validated successfully")

        # Recover interrupted jobs from previous run
        recover_interrupted_jobs()

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
