"""
Syncer Routes - API endpoints for Remote Host Syncer integration
"""

from flask import Blueprint, jsonify, request

from handlers.syncer_handler import SyncerHandler

# Create Syncer blueprint
syncer_bp = Blueprint('syncer', __name__)


@syncer_bp.route('/syncer/health', methods=['GET'])
def syncer_health():
    """
    GET /api/syncer/health - Check syncer service health
    
    Returns:
        JSON response with health status
    """
    return SyncerHandler.handle_health_check()


@syncer_bp.route('/syncer/status', methods=['GET'])
def get_sync_status():
    """
    GET /api/syncer/status - Get current sync status
    
    Returns:
        JSON response with sync status and configuration
    """
    return SyncerHandler.handle_get_sync_status()


@syncer_bp.route('/syncer/connections', methods=['GET'])
def get_sync_connections():
    """
    GET /api/syncer/connections - Get all active connections available for sync
    
    Returns:
        JSON response with connections list
    """
    return SyncerHandler.handle_get_connections()


@syncer_bp.route('/syncer/history', methods=['GET'])
def get_sync_history():
    """
    GET /api/syncer/history - Get sync history
    
    Query parameters:
        limit: Number of records to return (default: 50)
        days: Number of days to look back (default: 7)
        connection_id: Filter by specific connection ID
    
    Returns:
        JSON response with sync history
    """
    return SyncerHandler.handle_get_sync_history()


@syncer_bp.route('/syncer/sync', methods=['POST'])
def trigger_sync():
    """
    POST /api/syncer/sync - Trigger sync for all remote host connections
    
    Returns:
        JSON response with sync trigger result
    """
    return SyncerHandler.handle_trigger_sync()


@syncer_bp.route('/syncer/sync/connection/<connection_id>', methods=['POST'])
def trigger_connection_sync(connection_id):
    """
    POST /api/syncer/sync/connection/<connection_id> - Trigger sync for specific connection

    Args:
        connection_id: The ID of the connection to sync

    Returns:
        JSON response with sync trigger result
    """
    return SyncerHandler.handle_trigger_connection_sync(connection_id)


@syncer_bp.route('/syncer/job/<job_id>/cancel', methods=['POST'])
def cancel_job(job_id):
    """
    POST /api/syncer/job/<job_id>/cancel - Cancel a specific job (customer-facing)

    Args:
        job_id: The ID of the job to cancel

    Returns:
        JSON response with cancel result
    """
    return SyncerHandler.handle_cancel_job(job_id)


@syncer_bp.route('/syncer/jobs/cleanup-all-stale', methods=['POST'])
def cleanup_all_stale_jobs():
    """
    POST /api/syncer/jobs/cleanup-all-stale - Emergency cleanup of all active jobs (customer-facing)

    Returns:
        JSON response with cleanup result
    """
    return SyncerHandler.handle_cleanup_all_stale_jobs()


@syncer_bp.route('/syncer/jobs/active', methods=['GET'])
def get_active_jobs():
    """
    GET /api/syncer/jobs/active - Get all active jobs

    Returns:
        JSON response with active jobs
    """
    return SyncerHandler.handle_get_active_jobs()


@syncer_bp.route('/syncer/sync/force', methods=['POST'])
def force_sync():
    """
    POST /api/syncer/sync/force - Force sync even if one is in progress (use with caution)

    Returns:
        JSON response with force sync result
    """
    return SyncerHandler.handle_force_sync()


@syncer_bp.route('/syncer/job/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """
    GET /api/syncer/job/<job_id> - Get job status by ID

    Args:
        job_id: The ID of the job to get status for

    Returns:
        JSON response with job status
    """
    return SyncerHandler.handle_get_job_status(job_id)


@syncer_bp.route('/syncer/jobs/connection/<connection_id>', methods=['GET'])
def get_connection_jobs(connection_id):
    """
    GET /api/syncer/jobs/connection/<connection_id> - Get recent jobs for a connection

    Args:
        connection_id: The ID of the connection to get jobs for

    Query parameters:
        limit: Number of jobs to return (default: 10)

    Returns:
        JSON response with connection jobs
    """
    limit = request.args.get('limit', 10, type=int)
    return SyncerHandler.handle_get_connection_jobs(connection_id, limit)



