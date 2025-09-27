"""
Controller for LLM service endpoints
"""
import time
from flask import request, jsonify
from typing import Dict, Tuple, Any
from services.llm_service import LLMService
from config.settings import Config
from utils.logger import setup_logger


class LLMController:
    """Controller for handling LLM service requests"""
    
    def __init__(self):
        self.llm_service = LLMService()
        self.logger = setup_logger('llm-controller')
    
    def generate_response(self) -> Tuple[Dict[str, Any], int]:
        """
        Generate response using LLM with optional RAG
        
        Expected JSON payload:
        {
            "query": "user question",
            "use_rag": true,  // optional, default true
            "context": "optional pre-provided context"  // optional
        }
        
        Returns:
            Tuple of (response_dict, status_code)
        """
        try:
            # Validate request
            if not request.is_json:
                return self.error_response("Request must be JSON", 400)
            
            data = request.get_json()
            if not data:
                return self.error_response("Empty request body", 400)
            
            # Extract parameters
            query = data.get('query', '').strip()
            if not query:
                return self.error_response("Query is required", 400)
            
            use_rag = data.get('use_rag', True)
            context = data.get('context', None)
            
            # Validate parameters
            if not isinstance(use_rag, bool):
                return self.error_response("use_rag must be a boolean", 400)
            
            if context is not None and not isinstance(context, str):
                return self.error_response("context must be a string", 400)
            
            self.logger.info(f"Generate request: query='{query[:50]}...', use_rag={use_rag}")
            
            # Generate response
            result = self.llm_service.generate_response(
                query=query,
                use_rag=use_rag,
                context=context
            )
            
            return self.success_response(result), 200
            
        except Exception as e:
            self.logger.error(f"Error in generate_response: {str(e)}")
            return self.error_response(f"Response generation failed: {str(e)}", 500)
    
    def search_documents(self) -> Tuple[Dict[str, Any], int]:
        """
        Search documents using retriever service
        
        Expected JSON payload:
        {
            "query": "search query",
            "limit": 5  // optional
        }
        
        Returns:
            Tuple of (response_dict, status_code)
        """
        try:
            # Validate request
            if not request.is_json:
                return self.error_response("Request must be JSON", 400)
            
            data = request.get_json()
            if not data:
                return self.error_response("Empty request body", 400)
            
            # Extract parameters
            query = data.get('query', '').strip()
            if not query:
                return self.error_response("Query is required", 400)
            
            limit = data.get('limit', 5)
            
            # Validate parameters
            try:
                limit = int(limit)
            except (ValueError, TypeError):
                return self.error_response("limit must be an integer", 400)
            
            if limit <= 0 or limit > 20:
                return self.error_response("limit must be between 1 and 20", 400)
            
            self.logger.info(f"Search request: query='{query[:50]}...', limit={limit}")
            
            # Search documents
            result = self.llm_service.search_documents(
                query=query,
                limit=limit
            )
            
            return self.success_response(result), 200
            
        except Exception as e:
            self.logger.error(f"Error in search_documents: {str(e)}")
            return self.error_response(f"Document search failed: {str(e)}", 500)
    
    def chat(self) -> Tuple[Dict[str, Any], int]:
        """
        Chat endpoint that combines search and generation
        
        Expected JSON payload:
        {
            "message": "user message",
            "use_context": true  // optional, default true
        }
        
        Returns:
            Tuple of (response_dict, status_code)
        """
        try:
            # Validate request
            if not request.is_json:
                return self.error_response("Request must be JSON", 400)
            
            data = request.get_json()
            if not data:
                return self.error_response("Empty request body", 400)
            
            # Extract parameters
            message = data.get('message', '').strip()
            if not message:
                return self.error_response("Message is required", 400)
            
            use_context = data.get('use_context', True)
            
            # Validate parameters
            if not isinstance(use_context, bool):
                return self.error_response("use_context must be a boolean", 400)
            
            self.logger.info(f"Chat request: message='{message[:50]}...', use_context={use_context}")
            
            # Generate response with RAG
            result = self.llm_service.generate_response(
                query=message,
                use_rag=use_context
            )
            
            # Format as chat response
            chat_response = {
                "status": "success",
                "message": message,
                "response": result.get("response", ""),
                "context_used": result.get("context_used", False),
                "context_chunks": result.get("context_chunks", 0),
                "response_type": result.get("response_type", "direct"),
                "model": result.get("model", Config.MODEL_NAME),
                "timestamp": result.get("timestamp", int(time.time() * 1000))
            }
            
            return self.success_response(chat_response), 200
            
        except Exception as e:
            self.logger.error(f"Error in chat: {str(e)}")
            return self.error_response(f"Chat failed: {str(e)}", 500)
    
    def success_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a success response"""
        return data
    
    def error_response(self, message: str, status_code: int = 400) -> Dict[str, Any]:
        """Create an error response"""
        return {
            "status": "error",
            "error": message,
            "timestamp": int(__import__('time').time() * 1000)
        }
