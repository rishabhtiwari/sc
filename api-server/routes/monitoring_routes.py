#!/usr/bin/env python3
"""
Monitoring Routes - API endpoints for logs, error tracking, and alerts
"""

import logging
import requests
from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
import os

# Create blueprint
monitoring_bp = Blueprint('monitoring', __name__)
logger = logging.getLogger(__name__)

# Service URLs
NEWS_FETCHER_URL = os.getenv('NEWS_FETCHER_SERVICE_URL', 'http://ichat-news-fetcher:8093')
IOPAINT_URL = os.getenv('IOPAINT_SERVICE_URL', 'http://ichat-iopaint:8096')
YOUTUBE_UPLOADER_URL = os.getenv('YOUTUBE_UPLOADER_SERVICE_URL', 'http://ichat-youtube-uploader:8097')
VOICE_GENERATOR_URL = os.getenv('VOICE_GENERATOR_SERVICE_URL', 'http://ichat-voice-generator:8094')
AUDIO_GENERATION_URL = os.getenv('AUDIO_GENERATION_SERVICE_URL', 'http://audio-generation-factory:3000')

REQUEST_TIMEOUT = 5


@monitoring_bp.route('/monitoring/logs', methods=['GET'])
def get_logs():
    """
    Get system logs with filtering
    
    Query Parameters:
        - level: Log level filter (info, warning, error, debug)
        - service: Service name filter
        - limit: Number of logs to return (default: 100)
        - offset: Pagination offset (default: 0)
        
    Returns:
        JSON response with filtered logs
    """
    try:
        # Get query parameters
        level = request.args.get('level', 'all')
        service = request.args.get('service', 'all')
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        logger.info(f"📜 GET /monitoring/logs - level={level}, service={service}, limit={limit}, offset={offset}")
        
        # Mock log data (in production, this would come from a centralized logging system)
        all_logs = [
            {
                'id': 1,
                'timestamp': (datetime.now() - timedelta(minutes=1)).isoformat(),
                'level': 'info',
                'service': 'news-fetcher',
                'message': 'Successfully fetched 23 articles from GNews API',
                'details': {'articles_count': 23, 'source': 'gnews'}
            },
            {
                'id': 2,
                'timestamp': (datetime.now() - timedelta(minutes=2)).isoformat(),
                'level': 'info',
                'service': 'audio-generation',
                'message': 'Started audio generation for article: "Breaking News Update"',
                'details': {'article_id': 'art_12345', 'voice': 'kavya'}
            },
            {
                'id': 3,
                'timestamp': (datetime.now() - timedelta(minutes=3)).isoformat(),
                'level': 'warning',
                'service': 'voice-generator',
                'message': 'TTS service response time exceeded threshold',
                'details': {'response_time': 5.2, 'threshold': 3.0}
            },
            {
                'id': 4,
                'timestamp': (datetime.now() - timedelta(minutes=5)).isoformat(),
                'level': 'error',
                'service': 'youtube-uploader',
                'message': 'Failed to upload video: API quota exceeded',
                'details': {'video_id': 'vid_67890', 'error_code': 'QUOTA_EXCEEDED'}
            },
            {
                'id': 5,
                'timestamp': (datetime.now() - timedelta(minutes=7)).isoformat(),
                'level': 'info',
                'service': 'iopaint',
                'message': 'Watermark removed from image successfully',
                'details': {'image_id': 'img_54321', 'processing_time': 2.3}
            },
            {
                'id': 6,
                'timestamp': (datetime.now() - timedelta(minutes=10)).isoformat(),
                'level': 'debug',
                'service': 'news-fetcher',
                'message': 'Connecting to GNews API endpoint',
                'details': {'endpoint': 'https://gnews.io/api/v4/top-headlines'}
            },
            {
                'id': 7,
                'timestamp': (datetime.now() - timedelta(minutes=12)).isoformat(),
                'level': 'error',
                'service': 'audio-generation',
                'message': 'Audio generation failed: TTS service timeout',
                'details': {'article_id': 'art_99999', 'timeout': 30}
            },
            {
                'id': 8,
                'timestamp': (datetime.now() - timedelta(minutes=15)).isoformat(),
                'level': 'info',
                'service': 'video-generation',
                'message': 'Video compilation completed successfully',
                'details': {'video_count': 15, 'total_duration': 245.3}
            },
            {
                'id': 9,
                'timestamp': (datetime.now() - timedelta(minutes=18)).isoformat(),
                'level': 'warning',
                'service': 'news-fetcher',
                'message': 'API rate limit approaching threshold',
                'details': {'current_usage': 850, 'limit': 1000}
            },
            {
                'id': 10,
                'timestamp': (datetime.now() - timedelta(minutes=20)).isoformat(),
                'level': 'info',
                'service': 'youtube-uploader',
                'message': 'Video uploaded successfully to YouTube',
                'details': {'video_id': 'yt_abc123', 'title': 'Top 20 News Headlines'}
            }
        ]
        
        # Filter by level
        if level != 'all':
            all_logs = [log for log in all_logs if log['level'] == level]
        
        # Filter by service
        if service != 'all':
            all_logs = [log for log in all_logs if log['service'] == service]
        
        # Apply pagination
        total_count = len(all_logs)
        paginated_logs = all_logs[offset:offset + limit]
        
        return jsonify({
            'success': True,
            'data': {
                'logs': paginated_logs,
                'total_count': total_count,
                'limit': limit,
                'offset': offset,
                'has_more': offset + limit < total_count
            },
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"💥 Error in GET /monitoring/logs: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@monitoring_bp.route('/monitoring/errors', methods=['GET'])
def get_errors():
    """
    Get error tracking information
    
    Query Parameters:
        - hours: Time range in hours (default: 24)
        - service: Service name filter
        
    Returns:
        JSON response with error statistics and recent errors
    """
    try:
        hours = int(request.args.get('hours', 24))
        service = request.args.get('service', 'all')
        
        logger.info(f"🚨 GET /monitoring/errors - hours={hours}, service={service}")
        
        # Mock error data
        errors = [
            {
                'id': 1,
                'timestamp': (datetime.now() - timedelta(minutes=5)).isoformat(),
                'service': 'youtube-uploader',
                'error_type': 'QUOTA_EXCEEDED',
                'message': 'YouTube API quota exceeded',
                'severity': 'high',
                'count': 3,
                'first_seen': (datetime.now() - timedelta(hours=2)).isoformat(),
                'last_seen': (datetime.now() - timedelta(minutes=5)).isoformat(),
                'stack_trace': 'Error: Quota exceeded at YouTubeUploader.upload()'
            },
            {
                'id': 2,
                'timestamp': (datetime.now() - timedelta(minutes=12)).isoformat(),
                'service': 'audio-generation',
                'error_type': 'TIMEOUT',
                'message': 'TTS service timeout',
                'severity': 'medium',
                'count': 2,
                'first_seen': (datetime.now() - timedelta(hours=1)).isoformat(),
                'last_seen': (datetime.now() - timedelta(minutes=12)).isoformat(),
                'stack_trace': 'TimeoutError: Request timeout after 30s'
            },
            {
                'id': 3,
                'timestamp': (datetime.now() - timedelta(hours=3)).isoformat(),
                'service': 'news-fetcher',
                'error_type': 'API_ERROR',
                'message': 'GNews API returned 500 error',
                'severity': 'low',
                'count': 1,
                'first_seen': (datetime.now() - timedelta(hours=3)).isoformat(),
                'last_seen': (datetime.now() - timedelta(hours=3)).isoformat(),
                'stack_trace': 'HTTPError: 500 Server Error'
            }
        ]
        
        # Filter by service
        if service != 'all':
            errors = [err for err in errors if err['service'] == service]
        
        # Calculate error statistics
        total_errors = sum(err['count'] for err in errors)
        error_by_service = {}
        error_by_type = {}
        
        for err in errors:
            # By service
            if err['service'] not in error_by_service:
                error_by_service[err['service']] = 0
            error_by_service[err['service']] += err['count']
            
            # By type
            if err['error_type'] not in error_by_type:
                error_by_type[err['error_type']] = 0
            error_by_type[err['error_type']] += err['count']
        
        return jsonify({
            'success': True,
            'data': {
                'errors': errors,
                'statistics': {
                    'total_errors': total_errors,
                    'unique_errors': len(errors),
                    'by_service': error_by_service,
                    'by_type': error_by_type
                }
            },
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"💥 Error in GET /monitoring/errors: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@monitoring_bp.route('/monitoring/alerts', methods=['GET'])
def get_alerts():
    """
    Get active alerts and notifications
    
    Returns:
        JSON response with active alerts
    """
    try:
        logger.info("🔔 GET /monitoring/alerts")
        
        # Mock alerts data
        alerts = [
            {
                'id': 1,
                'type': 'quota',
                'severity': 'critical',
                'title': 'YouTube API Quota Critical',
                'message': 'YouTube API quota at 95% (950/1000 requests)',
                'service': 'youtube-uploader',
                'timestamp': (datetime.now() - timedelta(minutes=5)).isoformat(),
                'acknowledged': False,
                'actions': ['Pause uploads', 'Wait for quota reset']
            },
            {
                'id': 2,
                'type': 'performance',
                'severity': 'warning',
                'title': 'Audio Generation Slow',
                'message': 'Average processing time increased by 40%',
                'service': 'audio-generation',
                'timestamp': (datetime.now() - timedelta(minutes=15)).isoformat(),
                'acknowledged': False,
                'actions': ['Check TTS service', 'Review queue']
            },
            {
                'id': 3,
                'type': 'bottleneck',
                'severity': 'warning',
                'title': 'Workflow Bottleneck Detected',
                'message': '56 articles waiting for video generation',
                'service': 'video-generation',
                'timestamp': (datetime.now() - timedelta(minutes=30)).isoformat(),
                'acknowledged': True,
                'actions': ['Scale up workers', 'Optimize FFmpeg settings']
            }
        ]
        
        # Separate by severity
        critical_alerts = [a for a in alerts if a['severity'] == 'critical' and not a['acknowledged']]
        warning_alerts = [a for a in alerts if a['severity'] == 'warning' and not a['acknowledged']]
        
        return jsonify({
            'success': True,
            'data': {
                'alerts': alerts,
                'summary': {
                    'total': len(alerts),
                    'critical': len(critical_alerts),
                    'warning': len(warning_alerts),
                    'unacknowledged': len([a for a in alerts if not a['acknowledged']])
                }
            },
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"💥 Error in GET /monitoring/alerts: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@monitoring_bp.route('/monitoring/alerts/<int:alert_id>/acknowledge', methods=['POST'])
def acknowledge_alert(alert_id):
    """
    Acknowledge an alert
    
    Args:
        alert_id: ID of the alert to acknowledge
        
    Returns:
        JSON response confirming acknowledgment
    """
    try:
        logger.info(f"✅ POST /monitoring/alerts/{alert_id}/acknowledge")
        
        # In production, this would update the alert in the database
        return jsonify({
            'success': True,
            'message': f'Alert {alert_id} acknowledged',
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"💥 Error in POST /monitoring/alerts/{alert_id}/acknowledge: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@monitoring_bp.route('/monitoring/metrics', methods=['GET'])
def get_metrics():
    """
    Get system performance metrics
    
    Returns:
        JSON response with performance metrics
    """
    try:
        logger.info("📈 GET /monitoring/metrics")
        
        # Mock metrics data
        metrics = {
            'system': {
                'cpu_usage': 45.2,
                'memory_usage': 62.8,
                'disk_usage': 38.5,
                'network_in': 125.4,  # MB/s
                'network_out': 89.2   # MB/s
            },
            'services': {
                'news-fetcher': {
                    'requests_per_minute': 12,
                    'avg_response_time': 234,  # ms
                    'error_rate': 1.5  # %
                },
                'audio-generation': {
                    'requests_per_minute': 8,
                    'avg_response_time': 4567,  # ms
                    'error_rate': 3.2  # %
                },
                'video-generation': {
                    'requests_per_minute': 5,
                    'avg_response_time': 12345,  # ms
                    'error_rate': 2.1  # %
                },
                'youtube-uploader': {
                    'requests_per_minute': 3,
                    'avg_response_time': 3456,  # ms
                    'error_rate': 0.5  # %
                }
            },
            'database': {
                'connections': 15,
                'queries_per_second': 45,
                'avg_query_time': 23  # ms
            }
        }
        
        return jsonify({
            'success': True,
            'data': metrics,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"💥 Error in GET /monitoring/metrics: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

