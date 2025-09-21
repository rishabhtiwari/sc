"""
Validation utilities for OCR Service
"""

import os
from typing import Dict, Any
from werkzeug.datastructures import FileStorage


class FileValidator:
    """
    File validation utilities
    """
    
    # Maximum file size (10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024
    
    # Allowed file extensions
    ALLOWED_EXTENSIONS = {
        'images': {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp'},
        'documents': {'.pdf', '.docx'}
    }
    
    def __init__(self):
        self.all_extensions = set()
        for ext_group in self.ALLOWED_EXTENSIONS.values():
            self.all_extensions.update(ext_group)
    
    def validate_file(self, file: FileStorage) -> Dict[str, Any]:
        """
        Validate uploaded file
        
        Args:
            file: Uploaded file object
            
        Returns:
            Dictionary with validation result
        """
        if not file or not file.filename:
            return {
                'valid': False,
                'error': 'No file provided'
            }
        
        # Check file extension
        file_ext = os.path.splitext(file.filename.lower())[1]
        if file_ext not in self.all_extensions:
            return {
                'valid': False,
                'error': f'Unsupported file type: {file_ext}. Allowed: {", ".join(sorted(self.all_extensions))}'
            }
        
        # Check file size (if available)
        if hasattr(file, 'content_length') and file.content_length:
            if file.content_length > self.MAX_FILE_SIZE:
                return {
                    'valid': False,
                    'error': f'File too large. Maximum size: {self.MAX_FILE_SIZE // (1024*1024)}MB'
                }
        
        # Additional checks can be added here (file content validation, etc.)
        
        return {
            'valid': True,
            'file_type': self._get_file_type(file_ext),
            'extension': file_ext
        }
    
    def _get_file_type(self, extension: str) -> str:
        """
        Get file type category based on extension
        
        Args:
            extension: File extension
            
        Returns:
            File type category
        """
        for file_type, extensions in self.ALLOWED_EXTENSIONS.items():
            if extension in extensions:
                return file_type
        return 'unknown'
    
    @staticmethod
    def validate_language(language: str) -> Dict[str, Any]:
        """
        Validate language parameter
        
        Args:
            language: Language code
            
        Returns:
            Dictionary with validation result
        """
        valid_languages = ["en", "ch", "fr", "german", "korean", "japan"]
        
        if language not in valid_languages:
            return {
                'valid': False,
                'error': f'Invalid language: {language}. Supported: {", ".join(valid_languages)}'
            }
        
        return {'valid': True}
    
    @staticmethod
    def validate_output_format(output_format: str) -> Dict[str, Any]:
        """
        Validate output format parameter
        
        Args:
            output_format: Output format
            
        Returns:
            Dictionary with validation result
        """
        valid_formats = ["text", "json", "markdown"]
        
        if output_format not in valid_formats:
            return {
                'valid': False,
                'error': f'Invalid output format: {output_format}. Supported: {", ".join(valid_formats)}'
            }
        
        return {'valid': True}
