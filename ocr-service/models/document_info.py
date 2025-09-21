"""
Document Information Model
"""

import os
import time
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional
from werkzeug.datastructures import FileStorage


@dataclass
class DocumentInfo:
    """
    Model for document information
    """
    filename: str
    file_size: int
    file_type: str
    extension: str
    mime_type: Optional[str] = None
    upload_timestamp: Optional[int] = None
    
    def __post_init__(self):
        """Set upload timestamp if not provided"""
        if self.upload_timestamp is None:
            self.upload_timestamp = int(time.time() * 1000)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary
        
        Returns:
            Dictionary representation
        """
        return asdict(self)
    
    @property
    def formatted_file_size(self) -> str:
        """
        Get human-readable file size
        
        Returns:
            Formatted file size string
        """
        return self._format_bytes(self.file_size)
    
    @property
    def is_image(self) -> bool:
        """
        Check if document is an image
        
        Returns:
            True if image, False otherwise
        """
        return self.file_type == 'images'
    
    @property
    def is_document(self) -> bool:
        """
        Check if document is a text document
        
        Returns:
            True if document, False otherwise
        """
        return self.file_type == 'documents'
    
    @staticmethod
    def _format_bytes(bytes_value: int) -> str:
        """
        Format bytes to human readable format
        
        Args:
            bytes_value: Number of bytes
            
        Returns:
            Formatted string
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} TB"
    
    @classmethod
    def from_file_storage(cls, file: FileStorage) -> 'DocumentInfo':
        """
        Create DocumentInfo from FileStorage object
        
        Args:
            file: Uploaded file object
            
        Returns:
            DocumentInfo instance
        """
        # Get file extension
        extension = os.path.splitext(file.filename.lower())[1] if file.filename else ''
        
        # Determine file type
        image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp'}
        document_extensions = {'.pdf', '.docx'}
        
        if extension in image_extensions:
            file_type = 'images'
        elif extension in document_extensions:
            file_type = 'documents'
        else:
            file_type = 'unknown'
        
        # Get file size
        file_size = 0
        if hasattr(file, 'content_length') and file.content_length:
            file_size = file.content_length
        
        return cls(
            filename=file.filename or 'unknown',
            file_size=file_size,
            file_type=file_type,
            extension=extension,
            mime_type=file.content_type
        )
