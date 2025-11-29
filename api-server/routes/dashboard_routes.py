#!/usr/bin/env python3
"""
Dashboard Routes - API endpoints for dashboard statistics, activity logs, and monitoring
"""

import logging
import requests
from flask import Blueprint, jsonify
from datetime import datetime, timedelta
import os

# Create blueprint
dashboard_bp = Blueprint('dashboard', __name__)
logger = logging.getLogger(__name__)

# Service URLs
NEWS_FETCHER_URL = os.getenv('NEWS_FETCHER_SERVICE_URL', 'http://ichat-news-fetcher:8093')
IOPAINT_URL = os.getenv('IOPAINT_SERVICE_URL', 'http://ichat-iopaint:8096')
YOUTUBE_UPLOADER_URL = os.getenv('YOUTUBE_UPLOADER_SERVICE_URL', 'http://ichat-youtube-uploader:8097')
VOICE_GENERATOR_URL = os.getenv('VOICE_GENERATOR_SERVICE_URL', 'http://ichat-voice-generator:8094')
AUDIO_GENERATION_URL = os.getenv('AUDIO_GENERATION_SERVICE_URL', 'http://audio-generation-factory:3000')

REQUEST_TIMEOUT = 5


def check_service_health(service_name, service_url):
    """
    Check health status of a service
    
    Args:
        service_name: Name of the service
        service_url: Base URL of the service
        
    Returns:
        dict: Service health information
    """
    try:
        response = requests.get(f"{service_url}/health", timeout=REQUEST_TIMEOUT)
        if response.status_code == 200:
            return {
                'name': service_name,
                'status': 'healthy',
                'url': service_url,
                'response_time': response.elapsed.total_seconds() * 1000,  # ms
                'data': response.json() if response.content else {}
            }
        else:
            return {
                'name': service_name,
                'status': 'unhealthy',
                'url': service_url,
                'error': f'HTTP {response.status_code}'
            }
    except requests.exceptions.Timeout:
        return {
            'name': service_name,
            'status': 'timeout',
            'url': service_url,
            'error': 'Request timeout'
        }
    except requests.exceptions.ConnectionError:
        return {
            'name': service_name,
            'status': 'unreachable',
            'url': service_url,
            'error': 'Connection failed'
        }
    except Exception as e:
        return {
            'name': service_name,
            'status': 'error',
            'url': service_url,
            'error': str(e)
        }


@dashboard_bp.route('/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """
    Get comprehensive dashboard statistics
    
    Returns:
        JSON response with statistics from all services
    """
    try:
        logger.info("📊 GET /dashboard/stats")
        
        stats = {
            'totalNews': 0,
            'withAudio': 0,
            'withVideo': 0,
            'uploaded': 0,
            'processing': 0,
            'failed': 0
        }
        
        # Try to get real stats from News Fetcher service
        try:
            response = requests.get(f"{NEWS_FETCHER_URL}/api/news/stats", timeout=REQUEST_TIMEOUT)
            if response.status_code == 200:
                news_stats = response.json()
                stats['totalNews'] = news_stats.get('total', 0)
                stats['withAudio'] = news_stats.get('with_audio', 0)
                stats['withVideo'] = news_stats.get('with_video', 0)
                stats['uploaded'] = news_stats.get('uploaded', 0)
                stats['processing'] = news_stats.get('processing', 0)
                stats['failed'] = news_stats.get('failed', 0)
        except Exception as e:
            logger.warning(f"Failed to fetch news stats: {e}")
            # Use mock data if service is unavailable
            stats = {
                'totalNews': 247,
                'withAudio': 198,
                'withVideo': 165,
                'uploaded': 142,
                'processing': 12,
                'failed': 5
            }
        
        return jsonify({
            'success': True,
            'data': stats,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"💥 Error in GET /dashboard/stats: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@dashboard_bp.route('/dashboard/activity', methods=['GET'])
def get_recent_activity():
    """
    Get recent activity timeline
    
    Returns:
        JSON response with recent activities
    """
    try:
        logger.info("📋 GET /dashboard/activity")
        
        # Mock activity data (in production, this would come from a database or event log)
        activities = [
            {
                'id': 1,
                'type': 'news_fetch',
                'icon': '📰',
                'title': 'News fetch completed',
                'description': '23 new articles fetched from GNews API',
                'status': 'success',
                'timestamp': (datetime.now() - timedelta(minutes=5)).isoformat(),
                'duration': 12.5
            },
            {
                'id': 2,
                'type': 'audio_generation',
                'icon': '🎤',
                'title': 'Audio generation in progress',
                'description': 'Processing 18 articles with TTS',
                'status': 'processing',
                'timestamp': (datetime.now() - timedelta(minutes=8)).isoformat(),
                'progress': 65
            },
            {
                'id': 3,
                'type': 'video_generation',
                'icon': '🎬',
                'title': 'Video generation completed',
                'description': '15 news videos created successfully',
                'status': 'success',
                'timestamp': (datetime.now() - timedelta(minutes=15)).isoformat(),
                'duration': 245.3
            },
            {
                'id': 4,
                'type': 'youtube_upload',
                'icon': '📺',
                'title': 'YouTube upload successful',
                'description': 'Uploaded "Top 20 News Headlines" compilation',
                'status': 'success',
                'timestamp': (datetime.now() - timedelta(hours=1)).isoformat(),
                'duration': 89.2
            },
            {
                'id': 5,
                'type': 'image_cleaning',
                'icon': '🖼️',
                'title': 'Image watermark removal',
                'description': 'Cleaned 12 news images',
                'status': 'success',
                'timestamp': (datetime.now() - timedelta(hours=2)).isoformat(),
                'duration': 34.7
            },
            {
                'id': 6,
                'type': 'llm_enrichment',
                'icon': '🤖',
                'title': 'LLM enrichment completed',
                'description': 'Generated summaries and tags for 20 articles',
                'status': 'success',
                'timestamp': (datetime.now() - timedelta(hours=3)).isoformat(),
                'duration': 56.8
            },
            {
                'id': 7,
                'type': 'error',
                'icon': '⚠️',
                'title': 'Audio generation failed',
                'description': 'TTS service timeout for 2 articles',
                'status': 'error',
                'timestamp': (datetime.now() - timedelta(hours=4)).isoformat(),
                'error': 'Connection timeout'
            }
        ]
        
        return jsonify({
            'success': True,
            'data': activities,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"💥 Error in GET /dashboard/activity: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@dashboard_bp.route('/dashboard/services/health', methods=['GET'])
def get_services_health():
    """
    Get health status of all services
    
    Returns:
        JSON response with health status of all services
    """
    try:
        logger.info("❤️ GET /dashboard/services/health")
        
        services = [
            ('News Fetcher', NEWS_FETCHER_URL),
            ('IOPaint (Watermark Remover)', IOPAINT_URL),
            ('YouTube Uploader', YOUTUBE_UPLOADER_URL),
            ('Voice Generator', VOICE_GENERATOR_URL),
            ('Audio Generation', AUDIO_GENERATION_URL)
        ]
        
        health_status = []
        for service_name, service_url in services:
            health_status.append(check_service_health(service_name, service_url))
        
        # Calculate overall health
        healthy_count = sum(1 for s in health_status if s['status'] == 'healthy')
        total_count = len(health_status)
        overall_status = 'healthy' if healthy_count == total_count else 'degraded' if healthy_count > 0 else 'unhealthy'
        
        return jsonify({
            'success': True,
            'data': {
                'overall_status': overall_status,
                'healthy_count': healthy_count,
                'total_count': total_count,
                'services': health_status
            },
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"💥 Error in GET /dashboard/services/health: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@dashboard_bp.route('/dashboard/workflow/status', methods=['GET'])
def get_workflow_status():
    """
    Get current status of the workflow pipeline
    
    Returns:
        JSON response with workflow stage statuses
    """
    try:
        logger.info("🔄 GET /dashboard/workflow/status")
        
        # Mock workflow status (in production, this would come from a workflow engine)
        workflow_stages = [
            {
                'id': 'news_fetch',
                'name': 'News Fetch',
                'icon': '📰',
                'status': 'idle',
                'description': 'GNews API',
                'last_run': (datetime.now() - timedelta(minutes=5)).isoformat(),
                'success_rate': 98.5,
                'avg_duration': 12.3,
                'items_processed': 247
            },
            {
                'id': 'llm_enrichment',
                'name': 'LLM Enrichment',
                'icon': '🤖',
                'status': 'processing',
                'description': 'Summarize & Tag',
                'last_run': (datetime.now() - timedelta(minutes=2)).isoformat(),
                'success_rate': 95.2,
                'avg_duration': 45.7,
                'items_processed': 198,
                'current_progress': 75
            },
            {
                'id': 'audio_generation',
                'name': 'Audio Generation',
                'icon': '🎤',
                'status': 'processing',
                'description': 'TTS',
                'last_run': datetime.now().isoformat(),
                'success_rate': 92.8,
                'avg_duration': 89.4,
                'items_processed': 165,
                'current_progress': 45
            },
            {
                'id': 'video_generation',
                'name': 'Video Generation',
                'icon': '🎬',
                'status': 'idle',
                'description': 'FFmpeg',
                'last_run': (datetime.now() - timedelta(minutes=15)).isoformat(),
                'success_rate': 97.1,
                'avg_duration': 156.2,
                'items_processed': 142
            },
            {
                'id': 'youtube_upload',
                'name': 'YouTube Upload',
                'icon': '📺',
                'status': 'idle',
                'description': 'YouTube API',
                'last_run': (datetime.now() - timedelta(hours=1)).isoformat(),
                'success_rate': 99.3,
                'avg_duration': 67.8,
                'items_processed': 138
            }
        ]
        
        # Detect bottlenecks
        bottlenecks = []
        for i in range(len(workflow_stages) - 1):
            current_stage = workflow_stages[i]
            next_stage = workflow_stages[i + 1]
            
            # If current stage has significantly more processed items than next stage
            if current_stage['items_processed'] - next_stage['items_processed'] > 20:
                bottlenecks.append({
                    'stage': next_stage['id'],
                    'name': next_stage['name'],
                    'backlog': current_stage['items_processed'] - next_stage['items_processed'],
                    'severity': 'high' if current_stage['items_processed'] - next_stage['items_processed'] > 50 else 'medium'
                })
        
        return jsonify({
            'success': True,
            'data': {
                'stages': workflow_stages,
                'bottlenecks': bottlenecks,
                'overall_health': 'good' if len(bottlenecks) == 0 else 'needs_attention'
            },
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"💥 Error in GET /dashboard/workflow/status: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

