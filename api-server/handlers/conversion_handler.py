"""
Document Conversion Handler - HTTP request handling for document format conversion
"""

from flask import request, jsonify, send_file
from typing import Dict, Any
import io

from controllers.conversion_controller import ConversionController


class ConversionHandler:
    """
    Handler for document conversion HTTP requests
    """
    
    @staticmethod
    def handle_document_conversion() -> Dict[str, Any]:
        """
        Handle document format conversion request
        
        Expected form data:
        - file: Document file to convert
        - target_format: Target format (pdf, docx, txt)
        - options: Optional conversion parameters (JSON string)
        
        Returns:
            File download response or JSON error response
        """
        try:
            # Validate request
            if 'file' not in request.files:
                return jsonify({
                    "error": "No file provided",
                    "status": "error"
                }), 400
            
            if 'target_format' not in request.form:
                return jsonify({
                    "error": "Target format not specified",
                    "status": "error"
                }), 400
            
            file = request.files['file']
            target_format = request.form.get('target_format', '').lower()
            
            # Parse options if provided
            options = {}
            if 'options' in request.form:
                try:
                    import json
                    options = json.loads(request.form['options'])
                except json.JSONDecodeError:
                    return jsonify({
                        "error": "Invalid options JSON format",
                        "status": "error"
                    }), 400
            
            # Process conversion
            result = ConversionController.convert_document_format(
                file=file,
                target_format=target_format,
                options=options
            )
            
            if result['status'] == 'success':
                # Return file as download
                file_data = result.get('file_data')
                filename = result.get('filename', f'converted.{target_format}')
                content_type = result.get('content_type', 'application/octet-stream')
                
                if file_data:
                    file_obj = io.BytesIO(file_data)
                    return send_file(
                        file_obj,
                        as_attachment=True,
                        download_name=filename,
                        mimetype=content_type
                    )
                else:
                    return jsonify({
                        "error": "No file data in conversion result",
                        "status": "error"
                    }), 500
            else:
                return jsonify(result), 400
                
        except Exception as e:
            return jsonify({
                "error": f"Document conversion failed: {str(e)}",
                "status": "error"
            }), 500
    
    @staticmethod
    def handle_conversion_info() -> Dict[str, Any]:
        """
        Handle request for conversion information
        
        Returns:
            JSON response with conversion capabilities
        """
        try:
            result = ConversionController.get_conversion_info()
            
            if result['status'] == 'success':
                return jsonify(result), 200
            else:
                return jsonify(result), 500
                
        except Exception as e:
            return jsonify({
                "error": f"Failed to get conversion info: {str(e)}",
                "status": "error"
            }), 500
    
    @staticmethod
    def handle_conversion_test() -> Dict[str, Any]:
        """
        Handle test request for conversion endpoints
        
        Returns:
            JSON response confirming conversion endpoints are working
        """
        try:
            # Check OCR service connectivity for conversions
            conversion_info = ConversionController.get_conversion_info()
            
            return jsonify({
                "message": "Document conversion endpoints are operational",
                "status": "success",
                "endpoints": {
                    "convert": "/api/documents/convert-format",
                    "info": "/api/documents/conversion-info",
                    "test": "/api/documents/conversion-test"
                },
                "conversion_service": conversion_info.get('status', 'unknown'),
                "timestamp": int(__import__('time').time() * 1000)
            }), 200
            
        except Exception as e:
            return jsonify({
                "error": f"Conversion test failed: {str(e)}",
                "status": "error"
            }), 500
