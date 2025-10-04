"""
GitHub Repository Syncer Routes - API endpoints for GitHub Repository Syncer integration
"""

from flask import Blueprint, jsonify, request

from handlers.github_syncer_handler import GitHubSyncerHandler

# Create GitHub Syncer blueprint
github_syncer_bp = Blueprint('github_syncer', __name__)


@github_syncer_bp.route('/github-syncer/health', methods=['GET'])
def github_syncer_health():
    """
    GET /api/github-syncer/health - Check GitHub syncer service health
    
    Returns:
        JSON response with health status
    """
    return GitHubSyncerHandler.handle_health_check()


@github_syncer_bp.route('/github-syncer/status', methods=['GET'])
def get_github_sync_status():
    """
    GET /api/github-syncer/status - Get current GitHub sync status
    
    Returns:
        JSON response with sync status and configuration
    """
    return GitHubSyncerHandler.handle_get_sync_status()


@github_syncer_bp.route('/github-syncer/repositories', methods=['GET'])
def get_github_repositories():
    """
    GET /api/github-syncer/repositories - Get all active GitHub repositories
    
    Returns:
        JSON response with repositories list
    """
    return GitHubSyncerHandler.handle_get_repositories()


@github_syncer_bp.route('/github-syncer/sync', methods=['POST'])
def trigger_github_sync():
    """
    POST /api/github-syncer/sync - Trigger sync for all GitHub repositories
    
    Returns:
        JSON response with sync trigger result
    """
    return GitHubSyncerHandler.handle_trigger_sync()


@github_syncer_bp.route('/github-syncer/sync/repository', methods=['POST'])
@github_syncer_bp.route('/github-syncer/sync/repository/<repository_id>', methods=['POST'])
def trigger_github_repository_sync(repository_id=None):
    """
    POST /api/github-syncer/sync/repository/<repository_id> - Trigger sync for specific repository (path parameter)
    POST /api/github-syncer/sync/repository?repository_id=<repository_id> - Trigger sync for specific repository (query parameter)

    Args:
        repository_id: The ID of the repository to sync (from path parameter)

    Query Parameters:
        repository_id: The ID of the repository to sync (alternative to path parameter)

    Returns:
        JSON response with sync trigger result
    """
    # If repository_id is not in path, try to get it from query parameters
    if repository_id is None:
        repository_id = request.args.get('repository_id')
        if not repository_id:
            return jsonify({
                'status': 'error',
                'error': 'repository_id must be provided either as path parameter or query parameter'
            }), 400

    return GitHubSyncerHandler.handle_trigger_repository_sync(repository_id)


@github_syncer_bp.route('/github-syncer/job/<job_id>', methods=['GET'])
def get_github_job_status(job_id):
    """
    GET /api/github-syncer/job/<job_id> - Get job status by ID
    
    Args:
        job_id: The ID of the job
        
    Returns:
        JSON response with job status
    """
    return GitHubSyncerHandler.handle_get_job_status(job_id)


@github_syncer_bp.route('/github-syncer/jobs/active', methods=['GET'])
def get_github_active_jobs():
    """
    GET /api/github-syncer/jobs/active - Get all active GitHub sync jobs
    
    Returns:
        JSON response with active jobs
    """
    return GitHubSyncerHandler.handle_get_active_jobs()


@github_syncer_bp.route('/github-syncer/job/<job_id>/cancel', methods=['POST'])
def cancel_github_job(job_id):
    """
    POST /api/github-syncer/job/<job_id>/cancel - Cancel a GitHub sync job
    
    Args:
        job_id: The ID of the job to cancel
        
    Returns:
        JSON response with cancellation result
    """
    return GitHubSyncerHandler.handle_cancel_job(job_id)


@github_syncer_bp.route('/github-syncer/jobs/repository/<repository_id>', methods=['GET'])
def get_github_repository_jobs(repository_id):
    """
    GET /api/github-syncer/jobs/repository/<repository_id> - Get recent jobs for a repository
    
    Args:
        repository_id: The ID of the repository
        
    Query Parameters:
        limit: Maximum number of jobs to return (default: 10)
        
    Returns:
        JSON response with repository jobs
    """
    limit = request.args.get('limit', 10, type=int)
    return GitHubSyncerHandler.handle_get_repository_jobs(repository_id, limit)


@github_syncer_bp.route('/github-syncer/history', methods=['GET'])
def get_github_sync_history():
    """
    GET /api/github-syncer/history - Get GitHub sync history
    
    Query Parameters:
        limit: Maximum number of entries to return (default: 50)
        days: Number of days to look back (default: 7)
        repository_id: Filter by specific repository ID
        
    Returns:
        JSON response with sync history
    """
    try:
        limit = request.args.get('limit', 50, type=int)
        days = request.args.get('days', 7, type=int)
        repository_id = request.args.get('repository_id')
        
        # Build query parameters for the syncer service
        params = {'limit': limit, 'days': days}
        if repository_id:
            params['repository_id'] = repository_id
        
        # Make request to GitHub syncer service
        import requests
        from config.app_config import AppConfig
        
        response = requests.get(
            f"{AppConfig.GITHUB_SYNCER_URL}/history",
            params=params,
            timeout=30
        )
        response.raise_for_status()
        
        return jsonify(response.json())
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": f"Failed to get GitHub sync history: {str(e)}"
        }), 500


@github_syncer_bp.route('/github-syncer/force-sync', methods=['POST'])
def force_github_sync():
    """
    POST /api/github-syncer/force-sync - Force sync even if one is in progress (use with caution)
    
    Returns:
        JSON response with force sync result
    """
    try:
        import requests
        from config.app_config import AppConfig
        
        response = requests.post(
            f"{AppConfig.GITHUB_SYNCER_URL}/sync/force",
            timeout=30
        )
        response.raise_for_status()
        
        return jsonify(response.json())
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": f"Failed to force GitHub sync: {str(e)}"
        }), 500


@github_syncer_bp.route('/github-syncer/cleanup-jobs', methods=['POST'])
def cleanup_github_jobs():
    """
    POST /api/github-syncer/cleanup-jobs - Emergency cleanup of all active GitHub jobs
    
    Returns:
        JSON response with cleanup result
    """
    try:
        import requests
        from config.app_config import AppConfig
        
        response = requests.post(
            f"{AppConfig.GITHUB_SYNCER_URL}/jobs/cleanup-all-stale",
            timeout=30
        )
        response.raise_for_status()
        
        return jsonify(response.json())
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": f"Failed to cleanup GitHub jobs: {str(e)}"
        }), 500
