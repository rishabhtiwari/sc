"""
Document Controller - Business logic for document processing operations
"""

import time
from typing import Dict, Any, Optional
from werkzeug.datastructures import FileStorage

from flask import current_app
from services.ocr_service_client import ocr_client
from services.embedding_service_client import embedding_client



class DocumentController:
    """
    Controller for handling document processing business logic
    """
    
    @staticmethod
    def process_document_upload(
        file: FileStorage,
        output_format: str = "text",
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Process an uploaded document using OCR service
        
        Args:
            file (FileStorage): Uploaded file
            output_format (str): Desired output format (text, json, markdown)
            language (str): Language for OCR processing
            
        Returns:
            Dict[str, Any]: Processing result
        """
        try:
            # Validate file
            if not file or not file.filename:
                return {
                    "error": "No file provided",
                    "status": "error"
                }
            
            # Check if file type is supported
            if not ocr_client.is_supported_file(file.filename):
                return {
                    "error": f"Unsupported file type. Supported formats: PDF, DOCX, PNG, JPG, JPEG, BMP, TIFF, WEBP",
                    "status": "error"
                }
            
            # Validate output format
            valid_formats = ['text', 'json', 'markdown']
            if output_format not in valid_formats:
                return {
                    "error": f"Invalid output format. Supported: {', '.join(valid_formats)}",
                    "status": "error"
                }
            
            # Validate language
            valid_languages = ['en', 'ch', 'fr', 'german', 'korean', 'japan']
            if language not in valid_languages:
                return {
                    "error": f"Invalid language. Supported: {', '.join(valid_languages)}",
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
            
            print(f"📄 Processing document: {file.filename} (format: {output_format}, language: {language})")
            
            # Process document with OCR service
            start_time = time.time()
            result = ocr_client.convert_document(
                file_data=file,
                filename=file.filename,
                output_format=output_format,
                language=language
            )
            processing_time = time.time() - start_time
            
            if result['status'] == 'success':
                ocr_data = result['data']
                
                # Create response
                response_data = {
                    "status": "success",
                    "filename": file.filename,
                    "output_format": output_format,
                    "language": language,
                    "processing_time": round(processing_time, 2),
                    "timestamp": int(time.time() * 1000),
                    "ocr_result": ocr_data
                }
                
                print(f"✅ Document processed successfully in {processing_time:.2f}s")
                return response_data
            else:
                print(f"❌ OCR processing failed: {result.get('error', 'Unknown error')}")
                return {
                    "error": f"OCR processing failed: {result.get('error', 'Unknown error')}",
                    "status": "processing_error",
                    "filename": file.filename
                }
                
        except Exception as e:
            print(f"❌ Error processing document: {str(e)}")
            return {
                "error": f"Failed to process document: {str(e)}",
                "status": "error"
            }
    
    @staticmethod
    def get_supported_formats() -> Dict[str, Any]:
        """
        Get supported file formats and languages
        
        Returns:
            Dict[str, Any]: Supported formats information
        """
        try:
            # Get formats from OCR service
            formats_result = ocr_client.get_supported_formats()
            
            if formats_result['status'] == 'success':
                return {
                    "status": "success",
                    "data": formats_result['data'],
                    "timestamp": int(time.time() * 1000)
                }
            else:
                # Fallback to hardcoded formats
                return {
                    "status": "success",
                    "data": {
                        "supported_formats": {
                            "documents": ["PDF", "DOCX"],
                            "images": ["PNG", "JPG", "JPEG", "BMP", "TIFF", "WEBP"],
                            "output_formats": ["text", "json", "markdown"]
                        },
                        "languages": ["en", "ch", "fr", "german", "korean", "japan"],
                        "max_file_size": "10MB"
                    },
                    "timestamp": int(time.time() * 1000),
                    "note": "OCR service unavailable, showing cached formats"
                }
                
        except Exception as e:
            return {
                "error": f"Failed to get supported formats: {str(e)}",
                "status": "error"
            }
    
    @staticmethod
    def get_ocr_service_status() -> Dict[str, Any]:
        """
        Get OCR service status and health information
        
        Returns:
            Dict[str, Any]: Service status
        """
        try:
            health_check = ocr_client.health_check()
            
            return {
                "status": "success",
                "ocr_service": {
                    "status": health_check['status'],
                    "url": ocr_client.base_url,
                    "timeout": ocr_client.timeout,
                    "data": health_check.get('data', {}),
                    "error": health_check.get('error')
                },
                "timestamp": int(time.time() * 1000)
            }
            
        except Exception as e:
            return {
                "error": f"Failed to check OCR service status: {str(e)}",
                "status": "error"
            }

    @staticmethod
    def embed_document(file: FileStorage, title: str = None, author: str = None,
                      category: str = None) -> Dict[str, Any]:
        """
        Embed document for RAG using embedding service

        Args:
            file (FileStorage): Uploaded file
            title (str): Document title
            author (str): Document author
            category (str): Document category

        Returns:
            Dict[str, Any]: Embedding result with client storage info
        """
        try:
            current_app.logger.info(f"📄 Embedding document: {file.filename}")

            # Prepare metadata
            metadata = {
                "upload_timestamp": int(time.time() * 1000)
            }
            if title:
                metadata["title"] = title
            if author:
                metadata["author"] = author
            if category:
                metadata["category"] = category

            # Get file size before processing (without consuming the stream)
            file_size = 0
            if hasattr(file, 'content_length') and file.content_length:
                file_size = file.content_length
            elif hasattr(file, 'stream'):
                # Save current position
                current_pos = file.stream.tell()
                # Seek to end to get size
                file.stream.seek(0, 2)
                file_size = file.stream.tell()
                # Reset to original position
                file.stream.seek(current_pos)

            # Embed document using embedding service
            result = embedding_client.embed_document(
                file=file,
                metadata=metadata
            )

            if result and result.get('status') == 'success':
                # Extract data from embedding service response
                embed_data = result.get('data', {})
                document_id = embed_data.get('document_id')

                return {
                    "status": "success",
                    "message": "Document embedded successfully",
                    "document_id": document_id,
                    "filename": file.filename,
                    "metadata": metadata,
                    "text_length": embed_data.get('text_length', 0),
                    "chunks_created": embed_data.get('chunks_created', 0),
                    "chunks_stored": embed_data.get('chunks_stored', 0),
                    "processing_time": embed_data.get('processing_time', 0),
                    "client_storage_info": {
                        "document_id": document_id,
                        "filename": file.filename,
                        "title": title or file.filename,
                        "author": author or "Unknown",
                        "category": category or "General",
                        "upload_date": int(time.time() * 1000),
                        "file_size": file_size,
                        "storage_key": f"client_doc_{document_id}"
                    },
                    "timestamp": int(time.time() * 1000)
                }
            else:
                return {
                    "status": "error",
                    "message": f"Document embedding failed: {result.get('error', 'Unknown error')}",
                    "timestamp": int(time.time() * 1000)
                }

        except Exception as e:
            current_app.logger.error(f"Error embedding document: {str(e)}")
            return {
                "status": "error",
                "message": f"Document embedding failed: {str(e)}",
                "timestamp": int(time.time() * 1000)
            }

    @staticmethod
    def get_document_info(document_id: str) -> Dict[str, Any]:
        """
        Get document information by ID from embedding service

        Args:
            document_id (str): Document ID from embedding service

        Returns:
            Dict[str, Any]: Document information
        """
        try:
            # Get document info from embedding service
            result = embedding_client.get_document_info(document_id)

            if result and result.get('status') == 'success':
                return {
                    "status": "success",
                    "document_id": document_id,
                    "document_info": result.get('document_info', {}),
                    "metadata": result.get('metadata', {}),
                    "chunks_count": result.get('chunks_count', 0),
                    "timestamp": int(time.time() * 1000)
                }
            else:
                return {
                    "status": "error",
                    "message": f"Document not found or service error: {result.get('error', 'Unknown error')}",
                    "document_id": document_id,
                    "timestamp": int(time.time() * 1000)
                }

        except Exception as e:
            current_app.logger.error(f"Error getting document info for {document_id}: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to get document info: {str(e)}",
                "document_id": document_id,
                "timestamp": int(time.time() * 1000)
            }
    

