"""
OCR Controller - Handles OCR-related endpoints
"""

import time
from flask import request
from typing import Dict, Any, Tuple, Union, Optional

from .base_controller import BaseController
from services.document_service import DocumentService
from utils.validators import FileValidator
from utils.logger import get_logger


class OCRController(BaseController):
    """
    Controller for OCR operations
    """
    
    def __init__(self):
        self.document_service = DocumentService()
        self.file_validator = FileValidator()
        self.logger = get_logger(__name__)
    
    def convert_document(self) -> Tuple[Dict, int]:
        """
        Convert document to text using OCR
        
        Returns:
            Tuple of (response_dict, status_code)
        """
        try:
            # Validate request
            validation_result = self._validate_convert_request()
            if validation_result:
                return validation_result
            
            file = request.files['file']
            language = request.form.get('language', 'en')
            output_format = request.form.get('output_format', 'text')
            
            self.logger.info(f"Processing document: {file.filename}, Language: {language}, Format: {output_format}")
            
            # Process the document
            result = self.document_service.process_document(
                file, 
                language=language, 
                output_format=output_format
            )
            
            if result['status'] == 'success':
                self.logger.info(f"Document processed successfully: {len(result.get('text', ''))} characters extracted")
                return self.success_response(result)
            else:
                self.logger.error(f"Document processing failed: {result.get('error', 'Unknown error')}")
                return self.error_response(result.get('error', 'Processing failed'), 400)
                
        except Exception as e:
            self.logger.error(f"Error in convert endpoint: {str(e)}")
            return self.error_response(f"Internal server error: {str(e)}", 500)
    
    def get_supported_formats(self) -> Tuple[Dict, int]:
        """
        Get supported file formats
        
        Returns:
            Tuple of (response_dict, status_code)
        """
        data = {
            "supported_formats": {
                "images": ["PNG", "JPG", "JPEG", "BMP", "TIFF", "WEBP"],
                "documents": ["PDF", "DOCX"],
                "output_formats": ["text", "json", "markdown"]
            },
            "languages": ["en", "ch", "fr", "german", "korean", "japan"],
            "max_file_size": "10MB"
        }
        return self.success_response(data)
    
    def _validate_convert_request(self) -> Optional[Tuple[Dict, int]]:
        """
        Validate convert document request
        
        Returns:
            Error response if validation fails, None if valid
        """
        errors = {}
        
        # Check if file is present
        if 'file' not in request.files:
            errors['file'] = 'No file provided'
        else:
            file = request.files['file']
            if file.filename == '':
                errors['file'] = 'No file selected'
            else:
                # Validate file
                file_validation = self.file_validator.validate_file(file)
                if not file_validation['valid']:
                    errors['file'] = file_validation['error']
        
        # Validate language
        language = request.form.get('language', 'en')
        valid_languages = ["en", "ch", "fr", "german", "korean", "japan"]
        if language not in valid_languages:
            errors['language'] = f'Invalid language. Supported: {", ".join(valid_languages)}'
        
        # Validate output format
        output_format = request.form.get('output_format', 'text')
        valid_formats = ["text", "json", "markdown"]
        if output_format not in valid_formats:
            errors['output_format'] = f'Invalid format. Supported: {", ".join(valid_formats)}'
        
        if errors:
            return self.validation_error(errors)
        
        return None
