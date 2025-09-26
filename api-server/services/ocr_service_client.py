"""
OCR Service Client - Interface to communicate with the OCR microservice
"""

import requests
import time
from typing import Dict, Any, Optional, Union
from werkzeug.datastructures import FileStorage
import tempfile
import os


class OCRServiceClient:
    """
    Client for communicating with the OCR microservice
    """
    
    def __init__(self, base_url: str = "http://ichat-ocr-service:8081"):
        """
        Initialize OCR service client
        
        Args:
            base_url (str): Base URL of the OCR service
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = 30  # 30 seconds timeout for OCR operations
        
    def health_check(self) -> Dict[str, Any]:
        """
        Check if OCR service is healthy
        
        Returns:
            Dict[str, Any]: Health status response
        """
        try:
            response = requests.get(
                f"{self.base_url}/health",
                timeout=5
            )
            response.raise_for_status()
            return {
                "status": "healthy",
                "data": response.json()
            }
        except requests.exceptions.RequestException as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def get_supported_formats(self) -> Dict[str, Any]:
        """
        Get supported file formats from OCR service
        
        Returns:
            Dict[str, Any]: Supported formats response
        """
        try:
            response = requests.get(
                f"{self.base_url}/formats",
                timeout=10
            )
            response.raise_for_status()
            return {
                "status": "success",
                "data": response.json()
            }
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def convert_document_format(
        self,
        file_data: Union[FileStorage, bytes, str],
        filename: str,
        target_format: str,
        options: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Convert document format using OCR service

        Args:
            file_data: File data (FileStorage, bytes, or file path)
            filename: Original filename
            target_format: Target format (pdf, docx, txt)
            options: Optional conversion parameters

        Returns:
            Dict[str, Any]: Conversion results with file data
        """
        try:
            temp_file_path = None

            # Handle different file data types
            if isinstance(file_data, FileStorage):
                files = {'file': (filename, file_data, file_data.content_type)}
            elif isinstance(file_data, bytes):
                files = {'file': (filename, file_data)}
            elif isinstance(file_data, str) and os.path.exists(file_data):
                with open(file_data, 'rb') as f:
                    files = {'file': (filename, f.read())}
            else:
                return {
                    "status": "error",
                    "error": "Invalid file data provided"
                }

            # Prepare form data
            data = {
                'target_format': target_format
            }

            # Add options if provided
            if options:
                import json
                data['options'] = json.dumps(options)

            # Make request to OCR service conversion endpoint
            response = requests.post(
                f"{self.base_url}/convert-format",
                files=files,
                data=data,
                timeout=self.timeout
            )

            response.raise_for_status()

            # Handle file download response
            if response.headers.get('content-type', '').startswith('application/'):
                # File download response
                return {
                    "status": "success",
                    "file_data": response.content,
                    "filename": response.headers.get('Content-Disposition', '').split('filename=')[-1].strip('"'),
                    "content_type": response.headers.get('content-type')
                }
            else:
                # JSON error response
                result = response.json()
                return {
                    "status": "error",
                    "error": result.get('error', 'Conversion failed')
                }

        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "error": f"OCR service request failed: {str(e)}"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Conversion failed: {str(e)}"
            }

    def get_conversion_info(self) -> Dict[str, Any]:
        """
        Get conversion information from OCR service

        Returns:
            Dict[str, Any]: Conversion capabilities and supported formats
        """
        try:
            response = requests.get(
                f"{self.base_url}/conversion-info",
                timeout=5
            )
            response.raise_for_status()

            return {
                "status": "success",
                "data": response.json()
            }

        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "error": f"Failed to get conversion info: {str(e)}"
            }
    
    def convert_document(
        self, 
        file_data: Union[FileStorage, bytes, str], 
        filename: str,
        output_format: str = "text",
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Convert document using OCR service
        
        Args:
            file_data: File data (FileStorage, bytes, or file path)
            filename: Original filename
            output_format: Output format (text, json, markdown)
            language: Language for OCR processing
            
        Returns:
            Dict[str, Any]: OCR conversion result
        """
        try:
            # Prepare file for upload
            files = {}
            temp_file_path = None
            
            if isinstance(file_data, FileStorage):
                # Direct FileStorage upload
                files['file'] = (filename, file_data.stream, file_data.content_type)
            elif isinstance(file_data, bytes):
                # Bytes data - create temporary file
                temp_file_path = self._create_temp_file(file_data, filename)
                with open(temp_file_path, 'rb') as f:
                    files['file'] = (filename, f, self._get_content_type(filename))
            elif isinstance(file_data, str) and os.path.exists(file_data):
                # File path
                with open(file_data, 'rb') as f:
                    files['file'] = (filename, f, self._get_content_type(filename))
            else:
                return {
                    "status": "error",
                    "error": "Invalid file data provided"
                }
            
            # Prepare form data
            data = {
                'output_format': output_format,
                'language': language
            }
            
            # Make request to OCR service
            response = requests.post(
                f"{self.base_url}/convert",
                files=files,
                data=data,
                timeout=self.timeout
            )
            
            # Clean up temporary file
            if temp_file_path and os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            
            response.raise_for_status()
            result = response.json()
            
            return {
                "status": "success",
                "data": result
            }
            
        except requests.exceptions.Timeout:
            return {
                "status": "error",
                "error": "OCR service timeout - document processing took too long"
            }
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "error": f"OCR service error: {str(e)}"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Unexpected error: {str(e)}"
            }
    
    def _create_temp_file(self, data: bytes, filename: str) -> str:
        """
        Create a temporary file from bytes data
        
        Args:
            data: File bytes
            filename: Original filename for extension
            
        Returns:
            str: Path to temporary file
        """
        # Get file extension
        _, ext = os.path.splitext(filename)
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as temp_file:
            temp_file.write(data)
            return temp_file.name
    
    def _get_content_type(self, filename: str) -> str:
        """
        Get content type based on file extension
        
        Args:
            filename: File name
            
        Returns:
            str: Content type
        """
        ext = os.path.splitext(filename)[1].lower()
        content_types = {
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.bmp': 'image/bmp',
            '.tiff': 'image/tiff',
            '.webp': 'image/webp'
        }
        return content_types.get(ext, 'application/octet-stream')
    
    def is_supported_file(self, filename: str) -> bool:
        """
        Check if file is supported by OCR service
        
        Args:
            filename: File name to check
            
        Returns:
            bool: True if supported
        """
        ext = os.path.splitext(filename)[1].lower()
        supported_extensions = {
            '.pdf', '.docx', '.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp'
        }
        return ext in supported_extensions


# Global OCR service client instance
ocr_client = OCRServiceClient()
