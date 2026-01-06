"""
LLM Handler - HTTP request handling for LLM operations
"""

from flask import request, jsonify
from typing import Dict, Any
import json

from controllers.llm_controller import LLMController


class LLMHandler:
    """
    Handler for LLM HTTP requests
    """
    
    @staticmethod
    def handle_chat_request() -> Dict[str, Any]:
        """
        Handle chat request to LLM service
        
        Expected JSON payload:
        {
            "message": "User message",
            "conversation_id": "optional_conversation_id",
            "max_tokens": 128,
            "temperature": 0.7,
            "context": "optional_context"
        }
        
        Returns:
            JSON response with chat result
        """
        try:
            # Validate request
            if not request.is_json:
                return jsonify({
                    "status": "error",
                    "error": "Request must be JSON",
                    "timestamp": int(request.environ.get('REQUEST_TIME', 0) * 1000)
                }), 400
            
            data = request.get_json()
            
            # Validate required fields
            if 'message' not in data or not data['message'].strip():
                return jsonify({
                    "status": "error",
                    "error": "Message is required",
                    "timestamp": int(request.environ.get('REQUEST_TIME', 0) * 1000)
                }), 400
            
            message = data['message'].strip()
            conversation_id = data.get('conversation_id')
            max_tokens = data.get('max_tokens')
            temperature = data.get('temperature')
            context = data.get('context')
            
            # Process chat message
            result = LLMController.process_chat_message(
                message=message,
                conversation_id=conversation_id,
                max_tokens=max_tokens,
                temperature=temperature,
                context=context
            )
            
            if result['status'] == 'success':
                return jsonify(result), 200
            else:
                return jsonify(result), 500
                
        except Exception as e:
            return jsonify({
                "status": "error",
                "error": "Internal server error",
                "timestamp": int(request.environ.get('REQUEST_TIME', 0) * 1000)
            }), 500
    
    @staticmethod
    def handle_text_generation() -> Dict[str, Any]:
        """
        Handle text generation request
        
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
        try:
            # Validate request
            if not request.is_json:
                return jsonify({
                    "status": "error",
                    "error": "Request must be JSON",
                    "timestamp": int(request.environ.get('REQUEST_TIME', 0) * 1000)
                }), 400

            data = request.get_json()

            # Accept both 'query' and 'prompt' for backward compatibility
            query = data.get('query') or data.get('prompt')

            # Validate required fields
            if not query or not query.strip():
                return jsonify({
                    "status": "error",
                    "error": "Query or prompt is required",
                    "timestamp": int(request.environ.get('REQUEST_TIME', 0) * 1000)
                }), 400

            query = query.strip()
            use_rag = data.get('use_rag', False)
            detect_code = data.get('detect_code', False)
            context = data.get('context')
            max_tokens = data.get('max_tokens')
            temperature = data.get('temperature')
            top_p = data.get('top_p')

            # Generate text
            result = LLMController.generate_text(
                query=query,
                use_rag=use_rag,
                detect_code=detect_code,
                context=context,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p
            )
            
            if result['status'] == 'success':
                return jsonify(result), 200
            else:
                return jsonify(result), 500
                
        except Exception as e:
            return jsonify({
                "status": "error",
                "error": "Internal server error",
                "timestamp": int(request.environ.get('REQUEST_TIME', 0) * 1000)
            }), 500
    
    @staticmethod
    def handle_llm_status() -> Dict[str, Any]:
        """
        Handle LLM status request
        
        Returns:
            JSON response with LLM service status
        """
        try:
            result = LLMController.get_llm_status()
            
            if result['status'] == 'success':
                return jsonify(result), 200
            else:
                return jsonify(result), 503
                
        except Exception as e:
            return jsonify({
                "status": "error",
                "error": "Failed to get LLM status",
                "timestamp": int(request.environ.get('REQUEST_TIME', 0) * 1000)
            }), 500
    
    @staticmethod
    def handle_models_info() -> Dict[str, Any]:
        """
        Handle models information request
        
        Returns:
            JSON response with models information
        """
        try:
            result = LLMController.get_models_info()
            
            if result['status'] == 'success':
                return jsonify(result), 200
            else:
                return jsonify(result), 500
                
        except Exception as e:
            return jsonify({
                "status": "error",
                "error": "Failed to get models information",
                "timestamp": int(request.environ.get('REQUEST_TIME', 0) * 1000)
            }), 500
    
    @staticmethod
    def handle_conversation_history(conversation_id: str) -> Dict[str, Any]:
        """
        Handle conversation history request
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            JSON response with conversation history
        """
        try:
            if not conversation_id or not conversation_id.strip():
                return jsonify({
                    "status": "error",
                    "error": "Conversation ID is required",
                    "timestamp": int(request.environ.get('REQUEST_TIME', 0) * 1000)
                }), 400
            
            result = LLMController.get_conversation_history(conversation_id.strip())
            
            if result['status'] == 'success':
                return jsonify(result), 200
            else:
                return jsonify(result), 404
                
        except Exception as e:
            return jsonify({
                "status": "error",
                "error": "Failed to get conversation history",
                "timestamp": int(request.environ.get('REQUEST_TIME', 0) * 1000)
            }), 500
    
    @staticmethod
    def handle_clear_conversation(conversation_id: str) -> Dict[str, Any]:
        """
        Handle clear conversation request
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            JSON response with operation result
        """
        try:
            if not conversation_id or not conversation_id.strip():
                return jsonify({
                    "status": "error",
                    "error": "Conversation ID is required",
                    "timestamp": int(request.environ.get('REQUEST_TIME', 0) * 1000)
                }), 400
            
            result = LLMController.clear_conversation(conversation_id.strip())
            
            if result['status'] == 'success':
                return jsonify(result), 200
            else:
                return jsonify(result), 404
                
        except Exception as e:
            return jsonify({
                "status": "error",
                "error": "Failed to clear conversation",
                "timestamp": int(request.environ.get('REQUEST_TIME', 0) * 1000)
            }), 500
    
    @staticmethod
    def handle_llm_test() -> Dict[str, Any]:
        """
        Handle LLM service test request
        
        Returns:
            JSON response with test results
        """
        try:
            # Test basic connectivity
            status_result = LLMController.get_llm_status()
            
            if status_result['status'] == 'success':
                # Test simple generation
                test_result = LLMController.generate_text(
                    prompt="Hello, this is a test.",
                    max_tokens=20,
                    temperature=0.7
                )
                
                return jsonify({
                    "status": "success",
                    "message": "LLM service is operational",
                    "service_status": status_result['data'],
                    "test_generation": test_result.get('data', {}),
                    "endpoints": {
                        "chat": "/api/llm/chat",
                        "generate": "/api/llm/generate",
                        "status": "/api/llm/status",
                        "models": "/api/llm/models",
                        "test": "/api/llm/test"
                    },
                    "timestamp": int(request.environ.get('REQUEST_TIME', 0) * 1000)
                }), 200
            else:
                return jsonify({
                    "status": "error",
                    "error": "LLM service is not available",
                    "service_status": status_result,
                    "timestamp": int(request.environ.get('REQUEST_TIME', 0) * 1000)
                }), 503
                
        except Exception as e:
            return jsonify({
                "status": "error",
                "error": "LLM service test failed",
                "timestamp": int(request.environ.get('REQUEST_TIME', 0) * 1000)
            }), 500
