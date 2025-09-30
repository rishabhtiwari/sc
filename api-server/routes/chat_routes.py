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
        "client": "desktop",         # optional
        "use_rag": false            # optional, enables RAG
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


# RAG-enabled routes
@chat_bp.route('/chat/search', methods=['POST'])
def search_documents():
    """
    POST /api/chat/search - Search documents using semantic search

    Expected JSON payload:
    {
        "query": "search query text",
        "limit": 5  # optional, default: 5, max: 20
    }

    Returns:
        JSON response with search results
    """
    return ChatHandler.handle_document_search()


@chat_bp.route('/chat/context', methods=['POST'])
def build_rag_context():
    """
    POST /api/chat/context - Build RAG context for a query

    Expected JSON payload:
    {
        "query": "query for context building",
        "max_chunks": 3  # optional, default: 3, max: 10
    }

    Returns:
        JSON response with RAG context data
    """
    return ChatHandler.handle_rag_context()


@chat_bp.route('/chat/set-context', methods=['POST'])
def set_client_context():
    """
    POST /api/chat/set-context - Set context using client-stored document IDs

    Expected JSON payload:
    {
        "document_ids": ["doc_123", "doc_456"],  # Array of document IDs from client
        "client_id": "client_uuid",              # Optional client identifier
        "session_id": "session_uuid"             # Optional session identifier
    }

    Returns:
        JSON response with context setup status
    """
    return ChatHandler.handle_set_client_context()


@chat_bp.route('/chat/context-status', methods=['GET'])
def get_context_status():
    """
    GET /api/chat/context-status - Get current context status

    Query parameters:
    - client_id: Client identifier (optional)
    - session_id: Session identifier (optional)

    Returns:
        JSON response with current context information
    """
    return ChatHandler.handle_context_status()


@chat_bp.route('/chat/clear-context', methods=['POST'])
def clear_client_context():
    """
    POST /api/chat/clear-context - Clear current client context

    Expected JSON payload:
    {
        "client_id": "client_uuid",    # Optional client identifier
        "session_id": "session_uuid"   # Optional session identifier
    }

    Returns:
        JSON response with clear operation status
    """
    return ChatHandler.handle_clear_context()


@chat_bp.route('/chat/stream', methods=['POST'])
def stream_chat():
    """
    POST /api/chat/stream - Stream chat response with chunked processing

    Expected JSON payload:
    {
        "message": "User's message text",
        "session_id": "session_uuid",   # optional
        "client": "desktop",            # optional
        "use_rag": true                 # optional, enables RAG
    }

    Returns:
        Server-Sent Events stream with chunked response
    """
    return ChatHandler.handle_stream_chat()


@chat_bp.route('/chat/stream-direct', methods=['POST'])
def stream_chat_direct():
    """
    POST /api/chat/stream-direct - Stream chat response without RAG

    Expected JSON payload:
    {
        "message": "User's message text",
        "session_id": "session_uuid",   # optional
        "client": "desktop"             # optional
    }

    Returns:
        Server-Sent Events stream with direct response
    """
    return ChatHandler.handle_stream_chat_direct()


# Additional routes can be added here
@chat_bp.route('/chat/ping', methods=['GET'])
def chat_ping():
    """
    GET /api/chat/ping - Simple ping for chat service

    Returns:
        Simple pong response
    """
    return ChatHandler.handle_chat_test()  # Reuse test handler for simplicity
