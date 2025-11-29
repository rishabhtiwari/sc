#!/usr/bin/env python3
"""
WebSocket Routes - Real-time updates for job status and progress
Provides Socket.IO endpoints for real-time communication with frontend
"""

import logging
from flask import request
from flask_socketio import SocketIO, emit, join_room, leave_room, rooms
import time

logger = logging.getLogger(__name__)

# Global SocketIO instance (will be initialized in app.py)
socketio = None


def init_socketio(app):
    """
    Initialize Socket.IO with Flask app
    
    Args:
        app: Flask application instance
        
    Returns:
        SocketIO instance
    """
    global socketio
    
    socketio = SocketIO(
        app,
        cors_allowed_origins="*",  # Allow all origins for development
        async_mode='threading',
        logger=True,
        engineio_logger=True,
        ping_timeout=60,
        ping_interval=25
    )
    
    logger.info("✅ Socket.IO initialized successfully")
    
    # Register event handlers
    register_handlers()
    
    return socketio


def register_handlers():
    """Register Socket.IO event handlers"""
    
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection"""
        logger.info(f"🔌 Client connected: {request.sid}")
        emit('connection_response', {
            'status': 'connected',
            'sid': request.sid,
            'timestamp': int(time.time() * 1000)
        })
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        logger.info(f"🔌 Client disconnected: {request.sid}")
    
    @socketio.on('join_room')
    def handle_join_room(data):
        """
        Handle client joining a room for specific updates
        Rooms: 'news-fetcher', 'audio-generation', 'video-generation', 'youtube-upload'
        """
        room = data.get('room')
        if room:
            join_room(room)
            logger.info(f"👥 Client {request.sid} joined room: {room}")
            emit('room_joined', {
                'room': room,
                'timestamp': int(time.time() * 1000)
            })
    
    @socketio.on('leave_room')
    def handle_leave_room(data):
        """Handle client leaving a room"""
        room = data.get('room')
        if room:
            leave_room(room)
            logger.info(f"👥 Client {request.sid} left room: {room}")
            emit('room_left', {
                'room': room,
                'timestamp': int(time.time() * 1000)
            })
    
    @socketio.on('ping')
    def handle_ping():
        """Handle ping from client"""
        emit('pong', {'timestamp': int(time.time() * 1000)})


# ============================================================================
# BROADCAST FUNCTIONS - Called by backend services to send updates
# ============================================================================

def broadcast_news_fetch_status(status_data):
    """
    Broadcast news fetching status update
    
    Args:
        status_data: {
            'status': 'running' | 'completed' | 'error',
            'progress': 0-100,
            'current_source': 'source_name',
            'articles_fetched': 10,
            'total_sources': 5,
            'message': 'Status message'
        }
    """
    if socketio:
        socketio.emit('news_fetch_update', status_data, room='news-fetcher')
        logger.info(f"📡 Broadcast news fetch update: {status_data.get('status')}")


def broadcast_audio_generation_status(status_data):
    """
    Broadcast audio generation status update
    
    Args:
        status_data: {
            'status': 'running' | 'completed' | 'error',
            'progress': 0-100,
            'current_article': 'article_id',
            'articles_processed': 5,
            'total_articles': 20,
            'message': 'Status message'
        }
    """
    if socketio:
        socketio.emit('audio_generation_update', status_data, room='audio-generation')
        logger.info(f"📡 Broadcast audio generation update: {status_data.get('status')}")


def broadcast_video_generation_status(status_data):
    """
    Broadcast video generation status update
    
    Args:
        status_data: {
            'status': 'running' | 'completed' | 'error',
            'progress': 0-100,
            'current_video': 'video_id',
            'videos_processed': 3,
            'total_videos': 10,
            'message': 'Status message'
        }
    """
    if socketio:
        socketio.emit('video_generation_update', status_data, room='video-generation')
        logger.info(f"📡 Broadcast video generation update: {status_data.get('status')}")


def broadcast_youtube_upload_status(status_data):
    """
    Broadcast YouTube upload status update
    
    Args:
        status_data: {
            'status': 'running' | 'completed' | 'error',
            'progress': 0-100,
            'current_video': 'video_title',
            'videos_uploaded': 2,
            'total_videos': 20,
            'message': 'Status message',
            'video_url': 'https://youtube.com/...'
        }
    """
    if socketio:
        socketio.emit('youtube_upload_update', status_data, room='youtube-upload')
        logger.info(f"📡 Broadcast YouTube upload update: {status_data.get('status')}")


def broadcast_image_cleaning_status(status_data):
    """
    Broadcast image cleaning status update
    
    Args:
        status_data: {
            'status': 'running' | 'completed' | 'error',
            'progress': 0-100,
            'current_image': 'image_id',
            'images_processed': 5,
            'total_images': 50,
            'message': 'Status message'
        }
    """
    if socketio:
        socketio.emit('image_cleaning_update', status_data, room='image-cleaning')
        logger.info(f"📡 Broadcast image cleaning update: {status_data.get('status')}")


def broadcast_general_notification(notification_data):
    """
    Broadcast general notification to all connected clients
    
    Args:
        notification_data: {
            'type': 'info' | 'success' | 'warning' | 'error',
            'title': 'Notification title',
            'message': 'Notification message',
            'timestamp': 1234567890
        }
    """
    if socketio:
        socketio.emit('notification', notification_data, broadcast=True)
        logger.info(f"📡 Broadcast notification: {notification_data.get('title')}")


# ============================================================================
# REST API ENDPOINTS FOR TRIGGERING UPDATES (for testing)
# ============================================================================

from flask import Blueprint, jsonify

websocket_bp = Blueprint('websocket', __name__)


@websocket_bp.route('/websocket/test/news-fetch', methods=['POST'])
def test_news_fetch_update():
    """Test endpoint to trigger news fetch update"""
    from flask import request
    data = request.get_json() or {}
    
    broadcast_news_fetch_status({
        'status': data.get('status', 'running'),
        'progress': data.get('progress', 50),
        'current_source': data.get('current_source', 'Test Source'),
        'articles_fetched': data.get('articles_fetched', 10),
        'total_sources': data.get('total_sources', 5),
        'message': data.get('message', 'Fetching news...')
    })
    
    return jsonify({'success': True, 'message': 'Update broadcast'}), 200


@websocket_bp.route('/websocket/test/audio-generation', methods=['POST'])
def test_audio_generation_update():
    """Test endpoint to trigger audio generation update"""
    from flask import request
    data = request.get_json() or {}
    
    broadcast_audio_generation_status({
        'status': data.get('status', 'running'),
        'progress': data.get('progress', 50),
        'current_article': data.get('current_article', 'test-article-123'),
        'articles_processed': data.get('articles_processed', 5),
        'total_articles': data.get('total_articles', 20),
        'message': data.get('message', 'Generating audio...')
    })
    
    return jsonify({'success': True, 'message': 'Update broadcast'}), 200


@websocket_bp.route('/websocket/test/youtube-upload', methods=['POST'])
def test_youtube_upload_update():
    """Test endpoint to trigger YouTube upload update"""
    from flask import request
    data = request.get_json() or {}
    
    broadcast_youtube_upload_status({
        'status': data.get('status', 'running'),
        'progress': data.get('progress', 50),
        'current_video': data.get('current_video', 'Test Video'),
        'videos_uploaded': data.get('videos_uploaded', 2),
        'total_videos': data.get('total_videos', 20),
        'message': data.get('message', 'Uploading to YouTube...'),
        'video_url': data.get('video_url', '')
    })
    
    return jsonify({'success': True, 'message': 'Update broadcast'}), 200


@websocket_bp.route('/websocket/test/notification', methods=['POST'])
def test_notification():
    """Test endpoint to trigger general notification"""
    from flask import request
    data = request.get_json() or {}
    
    broadcast_general_notification({
        'type': data.get('type', 'info'),
        'title': data.get('title', 'Test Notification'),
        'message': data.get('message', 'This is a test notification'),
        'timestamp': int(time.time() * 1000)
    })
    
    return jsonify({'success': True, 'message': 'Notification broadcast'}), 200


@websocket_bp.route('/websocket/status', methods=['GET'])
def get_websocket_status():
    """Get WebSocket server status"""
    return jsonify({
        'status': 'running' if socketio else 'not_initialized',
        'connected_clients': len(socketio.server.manager.rooms.get('/', {}).keys()) if socketio else 0,
        'rooms': list(socketio.server.manager.rooms.keys()) if socketio else []
    }), 200

