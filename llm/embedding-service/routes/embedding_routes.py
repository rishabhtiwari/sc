"""
API Routes for Embedding Service

This module defines all the REST API endpoints for the embedding service
including document processing, retrieval, and management operations.
"""

import time
from flask import Blueprint, request, jsonify, current_app
from werkzeug.datastructures import FileStorage

from config.settings import Config
from utils.logger import setup_logger

# Create blueprint
embedding_bp = Blueprint('embedding', __name__, url_prefix='/embed')

# Setup logging
logger = setup_logger('embedding-routes')

@embedding_bp.route('/document', methods=['POST'])
def process_document():
    """
    Process a document: OCR extraction -> Text chunking -> Vector storage
    
    Expected form data:
    - file: Document file (PDF, DOC, DOCX, TXT, images)
    
    Returns:
    - document_id: Unique identifier for the processed document
    - processing statistics
    """
    try:
        # Get embedding service from app context
        embedding_service = getattr(current_app, 'embedding_service', None)
        if not embedding_service:
            return jsonify({
                "status": "error",
                "error": "Embedding service not available",
                "timestamp": int(time.time() * 1000)
            }), 503
        
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({
                "status": "error",
                "error": "No file provided",
                "timestamp": int(time.time() * 1000)
            }), 400
        
        file = request.files['file']
        
        # Check if file is selected
        if file.filename == '':
            return jsonify({
                "status": "error",
                "error": "No file selected",
                "timestamp": int(time.time() * 1000)
            }), 400
        
        # Validate file type
        if not Config.is_allowed_file(file.filename):
            return jsonify({
                "status": "error",
                "error": f"File type not allowed. Supported types: {', '.join(Config.ALLOWED_EXTENSIONS)}",
                "timestamp": int(time.time() * 1000)
            }), 400
        
        # Process the document
        logger.info(f"Processing document upload: {file.filename}")
        result = embedding_service.process_document(file, file.filename)
        
        return jsonify(result), 200
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": int(time.time() * 1000)
        }), 400
        
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        return jsonify({
            "status": "error",
            "error": "Failed to process document",
            "details": str(e),
            "timestamp": int(time.time() * 1000)
        }), 500

@embedding_bp.route('/document/<document_id>/chunks', methods=['GET'])
def get_document_chunks(document_id: str):
    """
    Get all chunks for a specific document
    
    Args:
        document_id: Document identifier
        
    Returns:
        List of text chunks with metadata
    """
    try:
        embedding_service = getattr(current_app, 'embedding_service', None)
        if not embedding_service:
            return jsonify({
                "status": "error",
                "error": "Embedding service not available",
                "timestamp": int(time.time() * 1000)
            }), 503
        
        if not document_id:
            return jsonify({
                "status": "error",
                "error": "Document ID is required",
                "timestamp": int(time.time() * 1000)
            }), 400
        
        logger.info(f"Retrieving chunks for document: {document_id}")
        result = embedding_service.get_document_chunks(document_id)
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error retrieving document chunks: {str(e)}")
        return jsonify({
            "status": "error",
            "error": "Failed to retrieve document chunks",
            "details": str(e),
            "timestamp": int(time.time() * 1000)
        }), 500

@embedding_bp.route('/document/<document_id>', methods=['DELETE'])
def delete_document(document_id: str):
    """
    Delete all chunks for a specific document
    
    Args:
        document_id: Document identifier
        
    Returns:
        Deletion confirmation and statistics
    """
    try:
        embedding_service = getattr(current_app, 'embedding_service', None)
        if not embedding_service:
            return jsonify({
                "status": "error",
                "error": "Embedding service not available",
                "timestamp": int(time.time() * 1000)
            }), 503
        
        if not document_id:
            return jsonify({
                "status": "error",
                "error": "Document ID is required",
                "timestamp": int(time.time() * 1000)
            }), 400
        
        logger.info(f"Deleting document: {document_id}")
        result = embedding_service.delete_document(document_id)
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        return jsonify({
            "status": "error",
            "error": "Failed to delete document",
            "details": str(e),
            "timestamp": int(time.time() * 1000)
        }), 500

@embedding_bp.route('/search', methods=['POST'])
def search_documents():
    """
    Search across all documents or within specific documents
    
    Expected JSON payload:
    - query: Search query text
    - document_ids: Optional list of document IDs to search within
    - limit: Optional result limit (default: 10)
    
    Returns:
        Relevant text chunks with similarity scores
    """
    try:
        embedding_service = getattr(current_app, 'embedding_service', None)
        if not embedding_service:
            return jsonify({
                "status": "error",
                "error": "Embedding service not available",
                "timestamp": int(time.time() * 1000)
            }), 503
        
        # Parse request data
        data = request.get_json()
        if not data:
            return jsonify({
                "status": "error",
                "error": "JSON payload required",
                "timestamp": int(time.time() * 1000)
            }), 400
        
        query = data.get('query', '')
        if not query:
            return jsonify({
                "status": "error",
                "error": "Query text is required",
                "timestamp": int(time.time() * 1000)
            }), 400
        
        document_ids = data.get('document_ids', [])
        limit = data.get('limit', 10)
        
        # Prepare search parameters
        search_params = {
            "query": query,
            "limit": limit
        }
        
        # Add document filter if specified
        if document_ids:
            search_params["filter"] = {"document_id": {"$in": document_ids}}
        
        logger.info(f"Searching documents with query: {query[:50]}...")
        result = embedding_service._search_vector_db(search_params)
        
        return jsonify({
            "status": "success",
            "query": query,
            "results": result.get("results", []),
            "total_results": len(result.get("results", [])),
            "timestamp": int(time.time() * 1000)
        }), 200
        
    except Exception as e:
        logger.error(f"Error searching documents: {str(e)}")
        return jsonify({
            "status": "error",
            "error": "Failed to search documents",
            "details": str(e),
            "timestamp": int(time.time() * 1000)
        }), 500
