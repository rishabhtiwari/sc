"""
Controller for retriever service endpoints
"""
from flask import request, jsonify
from typing import Dict, Tuple, Any
from services.retriever_service import RetrieverService
from config.settings import Config
from utils.logger import setup_logger


class RetrieverController:
    """Controller for handling retriever service requests"""
    
    def __init__(self):
        self.retriever_service = RetrieverService()
        self.logger = setup_logger('retriever-controller')
    
    def search_documents(self) -> Tuple[Dict[str, Any], int]:
        """
        Search for documents using semantic search
        
        Expected JSON payload:
        {
            "query": "search query text",
            "limit": 5,  // optional
            "min_similarity": 0.7  // optional
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
            
            limit = data.get('limit', Config.DEFAULT_SEARCH_LIMIT)
            min_similarity = data.get('min_similarity', Config.MIN_SIMILARITY_THRESHOLD)
            
            # Validate parameters
            try:
                limit = int(limit)
                min_similarity = float(min_similarity)
            except (ValueError, TypeError):
                return self.error_response("Invalid parameter types", 400)
            
            if limit <= 0 or limit > Config.MAX_SEARCH_LIMIT:
                return self.error_response(f"Limit must be between 1 and {Config.MAX_SEARCH_LIMIT}", 400)
            
            if not 0.0 <= min_similarity <= 1.0:
                return self.error_response("min_similarity must be between 0.0 and 1.0", 400)
            
            self.logger.info(f"Search request: query='{query}', limit={limit}, min_similarity={min_similarity}")
            
            # Perform search
            result = self.retriever_service.search_documents(
                query=query,
                limit=limit,
                min_similarity=min_similarity
            )
            
            return self.success_response(result), 200
            
        except Exception as e:
            self.logger.error(f"Error in search_documents: {str(e)}")
            return self.error_response(f"Search failed: {str(e)}", 500)
    
    def get_document_context(self, document_ids: str) -> Tuple[Dict[str, Any], int]:
        """
        Get context for specific documents
        
        Args:
            document_ids: Comma-separated list of document IDs
            
        Returns:
            Tuple of (response_dict, status_code)
        """
        try:
            # Parse document IDs
            if not document_ids:
                return self.error_response("Document IDs are required", 400)
            
            doc_id_list = [doc_id.strip() for doc_id in document_ids.split(',') if doc_id.strip()]
            if not doc_id_list:
                return self.error_response("Valid document IDs are required", 400)
            
            self.logger.info(f"Context request for {len(doc_id_list)} documents")
            
            # Get context
            result = self.retriever_service.get_document_context(doc_id_list)
            
            return self.success_response(result), 200
            
        except Exception as e:
            self.logger.error(f"Error in get_document_context: {str(e)}")
            return self.error_response(f"Context retrieval failed: {str(e)}", 500)
    
    def build_rag_context(self) -> Tuple[Dict[str, Any], int]:
        """
        Build RAG context for a query
        
        Expected JSON payload:
        {
            "query": "user query text",
            "max_chunks": 10  // optional
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
            
            max_chunks = data.get('max_chunks', Config.MAX_CONTEXT_CHUNKS)
            
            # Validate parameters
            try:
                max_chunks = int(max_chunks)
            except (ValueError, TypeError):
                return self.error_response("max_chunks must be an integer", 400)
            
            if max_chunks <= 0 or max_chunks > Config.MAX_CONTEXT_CHUNKS * 2:
                return self.error_response(f"max_chunks must be between 1 and {Config.MAX_CONTEXT_CHUNKS * 2}", 400)
            
            self.logger.info(f"RAG context request: query='{query}', max_chunks={max_chunks}")
            
            # Build RAG context
            result = self.retriever_service.build_rag_context(
                query=query,
                max_chunks=max_chunks
            )
            
            return self.success_response(result), 200
            
        except Exception as e:
            self.logger.error(f"Error in build_rag_context: {str(e)}")
            return self.error_response(f"RAG context building failed: {str(e)}", 500)
    
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
