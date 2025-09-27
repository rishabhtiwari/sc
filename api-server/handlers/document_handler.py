"""
Document Handler - HTTP request/response handling for document operations
"""

import time
import json

from flask import request, jsonify
from typing import Dict, Any

from controllers.document_controller import DocumentController
from services.embedding_service_client import embedding_client


class DocumentHandler:
    """
    Handler for document-related HTTP requests
    """
    
    @staticmethod
    def handle_document_upload() -> Dict[str, Any]:
        """
        Handle document upload and processing request
        
        Expected form data:
        - file: Document file to process
        - output_format: text|json|markdown (optional, default: text)
        - language: en|ch|fr|german|korean|japan (optional, default: en)
        
        Returns:
            JSON response with processing result
        """
        try:
            # Check if file is present
            if 'file' not in request.files:
                return jsonify({
                    "error": "No file provided in request",
                    "status": "error"
                }), 400
            
            file = request.files['file']
            
            # Get optional parameters
            output_format = request.form.get('output_format', 'text')
            language = request.form.get('language', 'en')
            
            # Process document
            result = DocumentController.process_document_upload(
                file=file,
                output_format=output_format,
                language=language
            )
            
            # Return appropriate HTTP status
            if result['status'] == 'success':
                return jsonify(result), 200
            elif result['status'] == 'service_unavailable':
                return jsonify(result), 503
            elif result['status'] == 'processing_error':
                return jsonify(result), 422
            else:
                return jsonify(result), 400
                
        except Exception as e:
            return jsonify({
                "error": f"Request handling error: {str(e)}",
                "status": "error"
            }), 500

    @staticmethod
    def handle_document_embed() -> Dict[str, Any]:
        """
        Handle document embedding for RAG

        Expected form data:
        - file: Document file to embed
        - title: Document title (optional)
        - author: Document author (optional)
        - category: Document category (optional)

        Returns:
            JSON response with embedding result
        """
        try:
            # Check if file is present
            if 'file' not in request.files:
                return jsonify({
                    "error": "No file provided in request",
                    "status": "error"
                }), 400

            file = request.files['file']

            # Check if file is empty
            if file.filename == '':
                return jsonify({
                    "error": "No file selected",
                    "status": "error"
                }), 400

            # Get optional metadata
            title = request.form.get('title')
            author = request.form.get('author')
            category = request.form.get('category')

            print(f"📄 Embedding document: {file.filename}")
            print(f"📋 Metadata: title={title}, author={author}, category={category}")

            # Embed document using DocumentController
            result = DocumentController.embed_document(
                file=file,
                title=title,
                author=author,
                category=category
            )

            if result['status'] == 'success':
                return jsonify(result), 200
            else:
                return jsonify(result), 500

        except Exception as e:
            print(f"❌ Error embedding document: {str(e)}")
            return jsonify({
                "error": f"Document embedding failed: {str(e)}",
                "status": "error",
                "timestamp": int(time.time() * 1000)
            }), 500

    @staticmethod
    def handle_document_info(document_id):
        """
        Handle GET /api/documents/info/<document_id> requests
        Get document information by ID

        Args:
            document_id (str): Document ID from embedding service

        Returns:
            Flask Response: JSON response with document information
        """
        try:
            # Validate document_id
            if not document_id or not document_id.strip():
                return jsonify({
                    "error": "Document ID is required",
                    "status": "error"
                }), 400

            # Get document info using DocumentController
            result = DocumentController.get_document_info(document_id.strip())

            return jsonify(result), 200

        except Exception as e:
            print(f"❌ Error getting document info: {str(e)}")
            return jsonify({
                "error": f"Failed to get document info: {str(e)}",
                "status": "error",
                "timestamp": int(time.time() * 1000)
            }), 500

    @staticmethod
    def handle_get_formats() -> Dict[str, Any]:
        """
        Handle request for supported formats
        
        Returns:
            JSON response with supported formats
        """
        try:
            result = DocumentController.get_supported_formats()
            
            if result['status'] == 'success':
                return jsonify(result), 200
            else:
                return jsonify(result), 500
                
        except Exception as e:
            return jsonify({
                "error": f"Request handling error: {str(e)}",
                "status": "error"
            }), 500
    
    @staticmethod
    def handle_service_status() -> Dict[str, Any]:
        """
        Handle request for OCR service status
        
        Returns:
            JSON response with service status
        """
        try:
            result = DocumentController.get_ocr_service_status()
            
            if result['status'] == 'success':
                return jsonify(result), 200
            else:
                return jsonify(result), 500
                
        except Exception as e:
            return jsonify({
                "error": f"Request handling error: {str(e)}",
                "status": "error"
            }), 500
    

    
    @staticmethod
    def handle_document_test() -> Dict[str, Any]:
        """
        Handle test request for document endpoints
        
        Returns:
            JSON response confirming document endpoints are working
        """
        try:
            # Check OCR service connectivity
            ocr_status = DocumentController.get_ocr_service_status()
            
            return jsonify({
                "message": "Document processing endpoints are operational",
                "status": "success",
                "endpoints": {
                    "upload": "/api/documents/upload",
                    "formats": "/api/documents/formats",
                    "status": "/api/documents/status"
                },
                "ocr_service": ocr_status.get('ocr_service', {}).get('status', 'unknown'),
                "timestamp": int(__import__('time').time() * 1000)
            }), 200
            
        except Exception as e:
            return jsonify({
                "error": f"Test endpoint error: {str(e)}",
                "status": "error"
            }), 500
