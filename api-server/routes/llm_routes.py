"""
LLM Routes - API endpoints for LLM service integration
"""

from flask import Blueprint, jsonify
from datetime import datetime

from handlers.llm_handler import LLMHandler

# Create LLM blueprint
llm_bp = Blueprint('llm', __name__)


@llm_bp.route('/llm/chat', methods=['POST'])
def chat_with_llm():
    """
    POST /api/llm/chat - Chat with LLM service
    
    Expected JSON payload:
    {
        "message": "User message",
        "conversation_id": "optional_conversation_id",
        "max_tokens": 128,
        "temperature": 0.7,
        "context": "optional_context"
    }
    
    Returns:
        JSON response with LLM chat result
    """
    return LLMHandler.handle_chat_request()


@llm_bp.route('/llm/generate', methods=['POST'])
def generate_text():
    """
    POST /api/llm/generate - Generate text using LLM service
    
    Expected JSON payload:
    {
        "prompt": "Text prompt",
        "max_tokens": 128,
        "temperature": 0.7,
        "top_p": 0.95
    }
    
    Returns:
        JSON response with generated text
    """
    return LLMHandler.handle_text_generation()


@llm_bp.route('/llm/status', methods=['GET'])
def get_llm_status():
    """
    GET /api/llm/status - Get LLM service status
    
    Returns:
        JSON response with LLM service status
    """
    return LLMHandler.handle_llm_status()


@llm_bp.route('/llm/models', methods=['GET'])
def get_models_info():
    """
    GET /api/llm/models - Get available models information
    
    Returns:
        JSON response with models information
    """
    return LLMHandler.handle_models_info()


@llm_bp.route('/llm/conversation/<conversation_id>', methods=['GET'])
def get_conversation_history(conversation_id):
    """
    GET /api/llm/conversation/<id> - Get conversation history
    
    Args:
        conversation_id: Conversation ID
    
    Returns:
        JSON response with conversation history
    """
    return LLMHandler.handle_conversation_history(conversation_id)


@llm_bp.route('/llm/conversation/<conversation_id>', methods=['DELETE'])
def clear_conversation(conversation_id):
    """
    DELETE /api/llm/conversation/<id> - Clear conversation history
    
    Args:
        conversation_id: Conversation ID
    
    Returns:
        JSON response with operation result
    """
    return LLMHandler.handle_clear_conversation(conversation_id)


@llm_bp.route('/llm/test', methods=['GET'])
def test_llm_service():
    """
    GET /api/llm/test - Test LLM service connectivity and functionality
    
    Returns:
        JSON response with test results
    """
    return LLMHandler.handle_llm_test()


@llm_bp.route('/llm/help', methods=['GET'])
def llm_help():
    """
    GET /api/llm/help - Get LLM API help and documentation
    
    Returns:
        JSON response with API documentation
    """
    return jsonify({
        "service": "LLM API",
        "version": "1.0.0",
        "description": "API endpoints for LLM service integration",
        "endpoints": {
            "chat": {
                "method": "POST",
                "url": "/api/llm/chat",
                "description": "Chat with LLM service",
                "parameters": {
                    "message": "User message (required)",
                    "conversation_id": "Conversation ID (optional)",
                    "max_tokens": "Maximum tokens to generate (optional, default: 128)",
                    "temperature": "Sampling temperature (optional, default: 0.7)",
                    "context": "Additional context (optional)"
                }
            },
            "generate": {
                "method": "POST",
                "url": "/api/llm/generate",
                "description": "Generate text using LLM",
                "parameters": {
                    "prompt": "Text prompt (required)",
                    "max_tokens": "Maximum tokens (optional, default: 128)",
                    "temperature": "Temperature (optional, default: 0.7)",
                    "top_p": "Top-p sampling (optional, default: 0.95)"
                }
            },
            "status": {
                "method": "GET",
                "url": "/api/llm/status",
                "description": "Get LLM service status"
            },
            "models": {
                "method": "GET",
                "url": "/api/llm/models",
                "description": "Get available models information"
            },
            "conversation_history": {
                "method": "GET",
                "url": "/api/llm/conversation/<id>",
                "description": "Get conversation history"
            },
            "clear_conversation": {
                "method": "DELETE",
                "url": "/api/llm/conversation/<id>",
                "description": "Clear conversation history"
            },
            "test": {
                "method": "GET",
                "url": "/api/llm/test",
                "description": "Test LLM service connectivity"
            },
            "help": {
                "method": "GET",
                "url": "/api/llm/help",
                "description": "Get API documentation"
            }
        },
        "examples": {
            "chat": {
                "url": "/api/llm/chat",
                "method": "POST",
                "payload": {
                    "message": "Hello! How can you help me?",
                    "max_tokens": 100,
                    "temperature": 0.7
                }
            },
            "generate": {
                "url": "/api/llm/generate",
                "method": "POST",
                "payload": {
                    "prompt": "The benefits of learning Python are:",
                    "max_tokens": 128,
                    "temperature": 0.8
                }
            }
        },
        "response_format": {
            "success": {
                "status": "success",
                "data": {
                    "response": "Generated text response",
                    "conversation_id": "uuid-string",
                    "model": "model-name",
                    "tokens_used": 45,
                    "timestamp": 1234567890
                },
                "timestamp": 1234567890
            },
            "error": {
                "status": "error",
                "error": "Error description",
                "timestamp": 1234567890
            }
        },
        "status": "success",
        "timestamp": int(datetime.now().timestamp() * 1000)
    })
