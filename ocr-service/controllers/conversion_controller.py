"""
Document Conversion Controller - Handles document format conversion requests
"""

from flask import request, send_file
from typing import Dict, Tuple, Any, Union, Optional
import io
import tempfile
import os

from controllers.base_controller import BaseController
from services.document_converter import DocumentConverter
from utils.logger import get_logger


class ConversionController(BaseController):
    """
    Controller for handling document conversion operations
    """
    
    def __init__(self):
        """
        Initialize conversion controller
        """
        super().__init__()
        self.document_converter = DocumentConverter()
        self.logger = get_logger(__name__)
    
    def convert_document(self) -> Tuple[Dict, int]:
        """
        Convert document from one format to another
        
        Expected form data:
        - file: Document file to convert
        - target_format: Target format (pdf, docx, txt)
        - options: Optional conversion parameters (JSON string)
        
        Returns:
            Tuple of (response_dict, status_code)
        """
        try:
            # Validate request
            validation_result = self._validate_conversion_request()
            if validation_result:
                return validation_result
            
            file = request.files['file']
            target_format = request.form.get('target_format', '').lower()
            
            self.logger.info(f"Converting document: {file.filename} to {target_format.upper()}")
            
            # Parse options if provided
            options = {}
            if 'options' in request.form:
                try:
                    import json
                    options = json.loads(request.form['options'])
                except json.JSONDecodeError:
                    return self.error_response("Invalid options JSON format", 400)
            
            # Perform conversion
            result = self.document_converter.convert_document(
                file, 
                target_format,
                options
            )
            
            if result['status'] == 'success':
                self.logger.info(f"Document converted successfully: {result['converted_filename']}")
                
                # Return file data as downloadable response
                file_data = result['file_data']
                converted_filename = result['converted_filename']
                
                # Create file-like object from bytes
                file_obj = io.BytesIO(file_data)
                
                # Determine MIME type
                mime_type = self._get_mime_type(target_format)
                
                return send_file(
                    file_obj,
                    as_attachment=True,
                    download_name=converted_filename,
                    mimetype=mime_type
                )
            else:
                self.logger.error(f"Document conversion failed: {result.get('error', 'Unknown error')}")
                return self.error_response(result.get('error', 'Conversion failed'), 400)
                
        except Exception as e:
            self.logger.error(f"Error in conversion endpoint: {str(e)}")
            return self.error_response(f"Internal server error: {str(e)}", 500)
    
    def get_conversion_info(self) -> Tuple[Dict, int]:
        """
        Get information about supported conversions
        
        Returns:
            Tuple of (response_dict, status_code)
        """
        try:
            conversion_info = self.document_converter.get_supported_conversions()
            return self.success_response(conversion_info)
            
        except Exception as e:
            self.logger.error(f"Error getting conversion info: {str(e)}")
            return self.error_response(f"Failed to get conversion info: {str(e)}", 500)
    
    def _validate_conversion_request(self) -> Optional[Tuple[Dict, int]]:
        """
        Validate conversion request parameters
        
        Returns:
            Error response tuple if validation fails, None if valid
        """
        errors = {}
        
        # Check if file is provided
        if 'file' not in request.files:
            errors['file'] = 'No file provided'
        else:
            file = request.files['file']
            if not file or not file.filename:
                errors['file'] = 'No file selected'
            else:
                # Check file extension
                allowed_extensions = {'.pdf', '.docx', '.txt'}
                file_ext = os.path.splitext(file.filename.lower())[1]
                if file_ext not in allowed_extensions:
                    errors['file'] = f'Unsupported file format. Allowed: {", ".join(allowed_extensions)}'
        
        # Check target format
        if 'target_format' not in request.form:
            errors['target_format'] = 'Target format not specified'
        else:
            target_format = request.form['target_format'].lower()
            valid_formats = ['pdf', 'docx', 'txt']
            if target_format not in valid_formats:
                errors['target_format'] = f'Invalid target format. Supported: {", ".join(valid_formats)}'
        
        if errors:
            return self.validation_error(errors)
        
        return None
    
    def _get_mime_type(self, format_type: str) -> str:
        """
        Get MIME type for file format
        
        Args:
            format_type: File format (pdf, docx, txt)
            
        Returns:
            MIME type string
        """
        mime_types = {
            'pdf': 'application/pdf',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'txt': 'text/plain'
        }
        return mime_types.get(format_type, 'application/octet-stream')
