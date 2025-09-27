"""
Vector Database Routes - API endpoints for vector operations
"""

import logging
from flask import Blueprint, request, jsonify
from typing import Dict, Any

from services.vector_service import VectorService

# Create vector blueprint
vector_bp = Blueprint('vector', __name__)

# Initialize vector service (will be set by app.py)
vector_service = None

def set_vector_service(service: VectorService):
    """Set the vector service instance"""
    global vector_service
    vector_service = service

logger = logging.getLogger('vector-db')


@vector_bp.route('/vector/collections', methods=['GET'])
def get_collection_info():
    """
    GET /vector/collections - Get collection information
    
    Returns:
        JSON response with collection details
    """
    try:
        if not vector_service:
            return jsonify({
                "status": "error",
                "error": "Vector service not initialized"
            }), 503
        
        result = vector_service.get_collection_info()
        
        if result['status'] == 'success':
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Failed to get collection info: {str(e)}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@vector_bp.route('/vector/documents', methods=['POST'])
def add_documents():
    """
    POST /vector/documents - Add documents to vector database
    
    Expected JSON payload:
    {
        "documents": ["text1", "text2", ...],
        "metadatas": [{"key": "value"}, ...],  // optional
        "ids": ["id1", "id2", ...]  // optional
    }
    
    Returns:
        JSON response with operation result
    """
    try:
        if not vector_service:
            return jsonify({
                "status": "error",
                "error": "Vector service not initialized"
            }), 503
        
        data = request.get_json()
        if not data:
            return jsonify({
                "status": "error",
                "error": "No JSON data provided"
            }), 400
        
        documents = data.get('documents', [])
        if not documents:
            return jsonify({
                "status": "error",
                "error": "No documents provided"
            }), 400
        
        metadatas = data.get('metadatas')
        ids = data.get('ids')
        
        # Validate metadatas length if provided
        if metadatas and len(metadatas) != len(documents):
            return jsonify({
                "status": "error",
                "error": "Metadatas length must match documents length"
            }), 400
        
        # Validate ids length if provided
        if ids and len(ids) != len(documents):
            return jsonify({
                "status": "error",
                "error": "IDs length must match documents length"
            }), 400
        
        logger.info(f"Adding {len(documents)} documents to vector database")
        
        result = vector_service.add_documents(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        if result['status'] == 'success':
            return jsonify(result), 201
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Failed to add documents: {str(e)}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@vector_bp.route('/vector/search', methods=['POST'])
def search_documents():
    """
    POST /vector/search - Search for similar documents
    
    Expected JSON payload:
    {
        "query": "search text",
        "n_results": 5,  // optional, default from config
        "where": {"key": "value"}  // optional metadata filter
    }
    
    Returns:
        JSON response with search results
    """
    try:
        if not vector_service:
            return jsonify({
                "status": "error",
                "error": "Vector service not initialized"
            }), 503
        
        data = request.get_json()
        if not data:
            return jsonify({
                "status": "error",
                "error": "No JSON data provided"
            }), 400
        
        query = data.get('query', '').strip()
        if not query:
            return jsonify({
                "status": "error",
                "error": "No query provided"
            }), 400
        
        n_results = data.get('n_results')
        where = data.get('where')
        
        logger.info(f"Searching for: '{query[:50]}...' with {n_results or 'default'} results")
        
        result = vector_service.search_documents(
            query=query,
            n_results=n_results,
            where=where
        )
        
        if result['status'] == 'success':
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@vector_bp.route('/vector/documents', methods=['DELETE'])
def delete_documents():
    """
    DELETE /vector/documents - Delete documents by IDs
    
    Expected JSON payload:
    {
        "ids": ["id1", "id2", ...]
    }
    
    Returns:
        JSON response with deletion result
    """
    try:
        if not vector_service:
            return jsonify({
                "status": "error",
                "error": "Vector service not initialized"
            }), 503
        
        data = request.get_json()
        if not data:
            return jsonify({
                "status": "error",
                "error": "No JSON data provided"
            }), 400
        
        ids = data.get('ids', [])
        if not ids:
            return jsonify({
                "status": "error",
                "error": "No document IDs provided"
            }), 400
        
        logger.info(f"Deleting {len(ids)} documents from vector database")
        
        result = vector_service.delete_documents(ids=ids)
        
        if result['status'] == 'success':
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Failed to delete documents: {str(e)}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@vector_bp.route('/vector/embeddings', methods=['POST'])
def generate_embeddings():
    """
    POST /vector/embeddings - Generate embeddings for text
    
    Expected JSON payload:
    {
        "texts": ["text1", "text2", ...]
    }
    
    Returns:
        JSON response with embeddings
    """
    try:
        if not vector_service:
            return jsonify({
                "status": "error",
                "error": "Vector service not initialized"
            }), 503
        
        data = request.get_json()
        if not data:
            return jsonify({
                "status": "error",
                "error": "No JSON data provided"
            }), 400
        
        texts = data.get('texts', [])
        if not texts:
            return jsonify({
                "status": "error",
                "error": "No texts provided"
            }), 400
        
        logger.info(f"Generating embeddings for {len(texts)} texts")
        
        # Generate embeddings using the service's embedding model
        embeddings = vector_service.embedding_model.encode(texts).tolist()
        
        return jsonify({
            "status": "success",
            "embeddings": embeddings,
            "count": len(embeddings),
            "dimension": len(embeddings[0]) if embeddings else 0,
            "model": vector_service.config.EMBEDDING_MODEL
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to generate embeddings: {str(e)}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500
