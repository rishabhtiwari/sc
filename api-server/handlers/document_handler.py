"""
Document Handler - HTTP request/response handling for document operations
"""

from flask import request, jsonify
from typing import Dict, Any

from controllers.document_controller import DocumentController


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
