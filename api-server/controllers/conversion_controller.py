"""
Document Conversion Controller - Business logic for document format conversion operations
"""

import time
from typing import Dict, Any, Optional
from werkzeug.datastructures import FileStorage

from flask import current_app
from services.ocr_service_client import ocr_client


class ConversionController:
    """
    Controller for handling document conversion business logic
    """
    
    @staticmethod
    def convert_document_format(
        file: FileStorage,
        target_format: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Convert document from one format to another using OCR service
        
        Args:
            file (FileStorage): Uploaded file
            target_format (str): Target format (pdf, docx, txt)
            options (Dict): Optional conversion parameters
            
        Returns:
            Dict[str, Any]: Conversion results with file data
        """
        try:
            # Validate file
            if not file or not file.filename:
                return {
                    "error": "No file provided",
                    "status": "error"
                }
            
            # Validate target format
            valid_formats = ['pdf', 'docx', 'txt']
            if target_format.lower() not in valid_formats:
                return {
                    "error": f"Invalid target format. Supported: {', '.join(valid_formats)}",
                    "status": "error"
                }
            
            # Get source format
            import os
            source_ext = os.path.splitext(file.filename.lower())[1][1:]  # Remove dot
            
            # Check if conversion is needed
            if source_ext == target_format.lower():
                return {
                    "error": "Source and target formats are the same",
                    "status": "error"
                }
            
            # Validate source format
            if source_ext not in valid_formats:
                return {
                    "error": f"Source format '{source_ext}' not supported",
                    "status": "error"
                }
            
            # Check OCR service health
            health_check = ocr_client.health_check()
            if health_check['status'] != 'healthy':
                return {
                    "error": "OCR service is currently unavailable",
                    "status": "service_unavailable",
                    "details": health_check.get('error', 'Unknown error')
                }
            
            print(f"🔄 Converting document: {file.filename} ({source_ext.upper()} → {target_format.upper()})")
            
            # Process document conversion with OCR service
            start_time = time.time()
            result = ocr_client.convert_document_format(
                file_data=file,
                filename=file.filename,
                target_format=target_format,
                options=options or {}
            )
            
            processing_time = time.time() - start_time
            
            if result['status'] == 'success':
                print(f"✅ Document converted successfully in {processing_time:.2f}s")
                result['processing_time'] = processing_time
                return result
            else:
                print(f"❌ Document conversion failed: {result.get('error', 'Unknown error')}")
                return result
                
        except Exception as e:
            print(f"❌ Conversion controller error: {str(e)}")
            return {
                "error": f"Document conversion failed: {str(e)}",
                "status": "error"
            }
    
    @staticmethod
    def get_conversion_info() -> Dict[str, Any]:
        """
        Get information about supported document conversions
        
        Returns:
            Dict[str, Any]: Conversion information and capabilities
        """
        try:
            # Get conversion info from OCR service
            result = ocr_client.get_conversion_info()
            
            if result['status'] == 'success':
                return {
                    "status": "success",
                    "data": result['data'],
                    "timestamp": int(time.time() * 1000)
                }
            else:
                return {
                    "error": "Failed to get conversion information",
                    "status": "error",
                    "details": result.get('error', 'Unknown error')
                }
                
        except Exception as e:
            print(f"❌ Error getting conversion info: {str(e)}")
            return {
                "error": f"Failed to get conversion info: {str(e)}",
                "status": "error"
            }
