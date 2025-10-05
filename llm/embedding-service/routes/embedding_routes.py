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
                "error": f"File type not allowed. Only whitelisted types are accepted: {', '.join(sorted(Config.WHITELISTED_EXTENSIONS))}",
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

@embedding_bp.route('/documents', methods=['POST'])
def process_documents_bulk():
    """
    Process multiple documents in bulk for repository integration

    Expected JSON payload:
    - documents: List of document objects with:
      - content: Text content of the document
      - metadata: Document metadata (type, repository_id, file_path, language, etc.)

    Returns:
    - document_ids: List of generated document IDs
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

        # Get JSON payload
        if not request.is_json:
            return jsonify({
                "status": "error",
                "error": "Content-Type must be application/json",
                "timestamp": int(time.time() * 1000)
            }), 400

        data = request.get_json()
        documents = data.get('documents', [])

        if not documents or not isinstance(documents, list):
            return jsonify({
                "status": "error",
                "error": "Documents list is required",
                "timestamp": int(time.time() * 1000)
            }), 400

        logger.info(f"Processing {len(documents)} documents in bulk")

        # Process documents in bulk
        result = embedding_service.process_documents_bulk(documents)

        return jsonify({
            "status": "success",
            "document_ids": result["document_ids"],
            "total_documents": result["total_documents"],
            "total_chunks": result["total_chunks"],
            "processing_time_ms": result["processing_time_ms"],
            "timestamp": int(time.time() * 1000)
        }), 200

    except Exception as e:
        logger.error(f"Error processing documents in bulk: {str(e)}")
        return jsonify({
            "status": "error",
            "error": "Failed to process documents in bulk",
            "details": str(e),
            "timestamp": int(time.time() * 1000)
        }), 500

@embedding_bp.route('/search', methods=['POST'])
def search_documents():
    """
    Unified search endpoint supporting both regular and hybrid search

    Expected JSON payload:
    {
        "query": "search query text",
        "use_hybrid": true/false (optional, default: true),
        "document_ids": ["doc1", "doc2"] (optional, for regular search),
        "metadata_filters": {...} (optional, for hybrid search),
        "context_resources": ["resource1", "resource2"] (optional, for hybrid search),
        "file_types": [".java", ".py"] (optional, for hybrid search),
        "folders": ["src/", "lib/"] (optional, for hybrid search),
        "content_types": ["code", "documentation"] (optional, for hybrid search),
        "limit": 20 (optional, default from config),
        "min_similarity": 0.4 (optional, default from config, for hybrid search)
    }

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

        # Check if hybrid search should be used (default from config)
        use_hybrid = data.get('use_hybrid', Config.DEFAULT_USE_HYBRID)
        limit = data.get('limit', Config.DEFAULT_SEARCH_LIMIT)

        if use_hybrid:
            # Hybrid search path
            logger.info(f"Hybrid search: query='{query[:50]}...'")

            # Extract hybrid search parameters - separated by resource type
            metadata_filters = data.get('metadata_filters', {})
            repository_names = data.get('repository_names', [])
            remote_host_names = data.get('remote_host_names', [])
            document_names = data.get('document_names', [])
            file_types = data.get('file_types', [])
            folders = data.get('folders', [])
            content_types = data.get('content_types', [])
            min_similarity = data.get('min_similarity', Config.MIN_SIMILARITY_THRESHOLD)

            # Debug logging for embedding service payload
            logger.debug(f"🔍 EMBEDDING SERVICE - Received hybrid search request:")
            logger.debug(f"   Query: '{query}'")
            logger.debug(f"   Repository names: {repository_names}")
            logger.debug(f"   Remote host names: {remote_host_names}")
            logger.debug(f"   Document names: {document_names}")
            logger.debug(f"   File types: {file_types}")
            logger.debug(f"   Content types: {content_types}")
            logger.debug(f"   Limit: {limit}, Min similarity: {min_similarity}")

            # Validate and cap limits
            if limit > 50:
                limit = 50  # Cap at reasonable limit

            if min_similarity < 0 or min_similarity > 1:
                min_similarity = Config.MIN_SIMILARITY_THRESHOLD  # Default to config threshold

            # Execute hybrid search with separated resource types
            result = embedding_service.search_documents_hybrid(
                query=query,
                metadata_filters=metadata_filters,
                repository_names=repository_names,
                remote_host_names=remote_host_names,
                document_names=document_names,
                file_types=file_types,
                folders=folders,
                content_types=content_types,
                limit=limit,
                min_similarity=min_similarity
            )

        else:
            # Regular search path
            logger.info(f"Regular search: query='{query[:50]}...'")

            # Debug logging for embedding service payload
            logger.debug(f"🔍 EMBEDDING SERVICE - Received regular search request:")
            logger.debug(f"   Full payload: {data}")
            logger.debug(f"   Query: '{query}'")
            logger.debug(f"   Limit: {limit}")

            document_ids = data.get('document_ids', [])

            # Prepare search parameters
            search_params = {
                "query": query,
                "limit": limit
            }

            # Add document filter if specified
            if document_ids:
                search_params["filter"] = {"document_id": {"$in": document_ids}}

            result = embedding_service._search_vector_db(search_params)

        # Return unified response format
        if result.get("status") == "success":
            return jsonify(result), 200
        else:
            return jsonify(result), 500

    except ValueError as e:
        logger.error(f"Validation error in search: {str(e)}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": int(time.time() * 1000)
        }), 400

    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        return jsonify({
            "status": "error",
            "error": "Failed to search documents",
            "details": str(e),
            "timestamp": int(time.time() * 1000)
        }), 500


