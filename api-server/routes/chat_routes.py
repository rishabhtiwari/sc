"""
Chat Routes - URL routing for chat-related endpoints
"""

from flask import Blueprint

from handlers.chat_handler import ChatHandler

# Create blueprint for chat routes
chat_bp = Blueprint('chat', __name__)


@chat_bp.route('/chat', methods=['POST'])
def chat_message():
    """
    POST /api/chat - Send a chat message and get response
    
    Expected JSON payload:
    {
        "message": "User's message text",
        "timestamp": 1640995200000,  # optional
        "client": "desktop"          # optional
    }
    
    Returns:
        JSON response with chat response
    """
    return ChatHandler.handle_chat_message()


@chat_bp.route('/chat/stats', methods=['GET'])
def chat_stats():
    """
    GET /api/chat/stats - Get chat statistics
    
    Returns:
        JSON response with chat statistics
    """
    return ChatHandler.handle_chat_stats()


@chat_bp.route('/chat/test', methods=['GET'])
def chat_test():
    """
    GET /api/chat/test - Test chat endpoint connectivity
    
    Returns:
        JSON response confirming chat endpoint is working
    """
    return ChatHandler.handle_chat_test()


# Additional routes can be added here
@chat_bp.route('/chat/ping', methods=['GET'])
def chat_ping():
    """
    GET /api/chat/ping - Simple ping for chat service
    
    Returns:
        Simple pong response
    """
    return ChatHandler.handle_chat_test()  # Reuse test handler for simplicity
