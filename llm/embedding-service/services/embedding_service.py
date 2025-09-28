"""
Embedding Service - Core document processing and embedding functionality

This service handles:
1. Document processing via OCR service
2. Text chunking and preprocessing
3. Vector storage via Vector DB service
4. Document ID generation and management
"""

import os
import time
import uuid
import requests
import tempfile
from typing import Dict, List, Optional, Tuple, Any
from werkzeug.datastructures import FileStorage

from config.settings import Config
from utils.logger import setup_logger

class EmbeddingService:
    """Main embedding service for document processing and vector storage"""
    
    def __init__(self):
        self.logger = setup_logger('embedding-service')
        self.ocr_service_url = Config.get_ocr_url()
        self.vector_db_url = Config.get_vector_db_url()
        self.initialized = False
        
    def initialize(self) -> bool:
        """Initialize the embedding service and check external dependencies"""
        try:
            self.logger.info("Initializing Embedding Service...")
            
            # Check OCR service health
            if not self._check_ocr_service():
                self.logger.error("OCR service is not available")
                return False
                
            # Check Vector DB service health
            if not self._check_vector_db_service():
                self.logger.error("Vector DB service is not available")
                return False
                
            self.initialized = True
            self.logger.info("Embedding Service initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize embedding service: {str(e)}")
            return False
    
    def is_healthy(self) -> bool:
        """Check if the service is healthy and ready to process requests"""
        return (self.initialized and 
                self._check_ocr_service() and 
                self._check_vector_db_service())
    
    def process_document(self, file: FileStorage, filename: str) -> Dict[str, Any]:
        """
        Process a document: OCR -> Chunking -> Vector Storage
        
        Args:
            file: Uploaded file object
            filename: Original filename
            
        Returns:
            Dictionary with processing results including document_id
        """
        document_id = None
        temp_file_path = None
        
        try:
            self.logger.info(f"Processing document: {filename}")
            
            # Generate unique document ID
            document_id = self._generate_document_id()
            
            # Validate file
            if not Config.is_allowed_file(filename):
                raise ValueError(f"File type not allowed: {filename}")
            
            # Save file temporarily
            temp_file_path = self._save_temp_file(file, filename)
            
            # Extract text using OCR service
            self.logger.info(f"Extracting text from document {document_id}")
            extracted_text = self._extract_text_via_ocr(temp_file_path, filename)
            
            if not extracted_text or not extracted_text.strip():
                raise ValueError("No text could be extracted from the document")
            
            # Chunk the text
            self.logger.info(f"Chunking text for document {document_id}")
            chunks = self._chunk_text(extracted_text, document_id, filename)
            
            if not chunks:
                raise ValueError("No valid chunks could be created from the text")
            
            # Store chunks in vector database
            self.logger.info(f"Storing {len(chunks)} chunks in vector database")
            storage_result = self._store_chunks_in_vector_db(chunks, document_id)
            
            # Clean up temporary file
            if temp_file_path and os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            
            result = {
                "status": "success",
                "document_id": document_id,
                "filename": filename,
                "chunks_created": len(chunks),
                "chunks_stored": storage_result.get("documents_added", 0),
                "text_length": len(extracted_text),
                "processing_time": time.time(),
                "timestamp": int(time.time() * 1000)
            }
            
            self.logger.info(f"Successfully processed document {document_id}: {len(chunks)} chunks")
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing document {document_id or 'unknown'}: {str(e)}")
            
            # Clean up on error
            if temp_file_path and os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            
            # If we have a document_id, try to clean up any partial data
            if document_id:
                try:
                    self._cleanup_document(document_id)
                except Exception as cleanup_error:
                    self.logger.error(f"Error during cleanup: {str(cleanup_error)}")
            
            raise e
    
    def get_document_chunks(self, document_id: str) -> Dict[str, Any]:
        """Get all chunks for a specific document"""
        try:
            # Use a generic query to find chunks, then filter by document_id
            # Since vector DB requires a query, we'll use a broad search term
            search_result = self._search_vector_db({
                "query": "document text content",  # Generic query to match any text
                "limit": Config.MAX_CHUNKS_PER_DOCUMENT * 2  # Get more results to filter
            })

            # Filter results to only include chunks from the specified document
            document_chunks = []
            for result in search_result.get("results", []):
                if result.get("metadata", {}).get("document_id") == document_id:
                    document_chunks.append(result)

            return {
                "status": "success",
                "document_id": document_id,
                "chunks": document_chunks,
                "total_chunks": len(document_chunks),
                "timestamp": int(time.time() * 1000)
            }

        except Exception as e:
            self.logger.error(f"Error retrieving chunks for document {document_id}: {str(e)}")
            raise e
    
    def delete_document(self, document_id: str) -> Dict[str, Any]:
        """Delete all chunks for a specific document"""
        try:
            # Get all chunk IDs for this document
            chunks_result = self.get_document_chunks(document_id)
            chunk_ids = [chunk.get("id") for chunk in chunks_result.get("chunks", [])]
            
            if not chunk_ids:
                return {
                    "status": "success",
                    "document_id": document_id,
                    "deleted_chunks": 0,
                    "message": "No chunks found for this document",
                    "timestamp": int(time.time() * 1000)
                }
            
            # Delete chunks from vector database
            delete_result = self._delete_from_vector_db(chunk_ids)
            
            return {
                "status": "success",
                "document_id": document_id,
                "deleted_chunks": delete_result.get("deleted_count", 0),
                "timestamp": int(time.time() * 1000)
            }
            
        except Exception as e:
            self.logger.error(f"Error deleting document {document_id}: {str(e)}")
            raise e

    def _check_ocr_service(self) -> bool:
        """Check if OCR service is available"""
        try:
            response = requests.get(
                Config.get_ocr_url(Config.OCR_HEALTH_ENDPOINT),
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            self.logger.warning(f"OCR service health check failed: {str(e)}")
            return False

    def _check_vector_db_service(self) -> bool:
        """Check if Vector DB service is available"""
        try:
            response = requests.get(
                Config.get_vector_db_url(Config.VECTOR_DB_HEALTH_ENDPOINT),
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            self.logger.warning(f"Vector DB service health check failed: {str(e)}")
            return False

    def _generate_document_id(self) -> str:
        """Generate a unique document ID"""
        unique_id = str(uuid.uuid4()).replace('-', '')[:Config.DOCUMENT_ID_LENGTH]
        return f"{Config.DOCUMENT_ID_PREFIX}_{unique_id}"

    def _save_temp_file(self, file: FileStorage, filename: str) -> str:
        """Save uploaded file to temporary location"""
        try:
            # Create temporary file with original extension
            file_ext = os.path.splitext(filename)[1]
            temp_fd, temp_path = tempfile.mkstemp(suffix=file_ext)

            # Save file content
            with os.fdopen(temp_fd, 'wb') as temp_file:
                file.save(temp_file)

            return temp_path

        except Exception as e:
            self.logger.error(f"Error saving temporary file: {str(e)}")
            raise e

    def _extract_text_via_ocr(self, file_path: str, filename: str) -> str:
        """Extract text from document using OCR service"""
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (filename, f, 'application/octet-stream')}

                response = requests.post(
                    Config.get_ocr_url(Config.OCR_EXTRACT_ENDPOINT),
                    files=files,
                    timeout=Config.OCR_TIMEOUT
                )

                if response.status_code != 200:
                    raise Exception(f"OCR service returned status {response.status_code}: {response.text}")

                result = response.json()

                if result.get("status") != "success":
                    raise Exception(f"OCR extraction failed: {result.get('error', 'Unknown error')}")

                return result.get("text", "")

        except Exception as e:
            self.logger.error(f"Error extracting text via OCR: {str(e)}")
            raise e

    def _chunk_text(self, text: str, document_id: str, filename: str) -> List[Dict[str, Any]]:
        """Split text into chunks for vector storage"""
        try:
            chunks = []
            chunk_size = Config.CHUNK_SIZE
            overlap = Config.CHUNK_OVERLAP

            # Simple text chunking with overlap
            start = 0
            chunk_index = 0

            while start < len(text):
                end = start + chunk_size
                chunk_text = text[start:end]

                # Skip chunks that are too small
                if len(chunk_text.strip()) < Config.MIN_CHUNK_SIZE:
                    break

                # Create chunk metadata
                chunk_data = {
                    "id": f"{document_id}_chunk_{chunk_index}",
                    "text": chunk_text.strip(),
                    "metadata": {
                        "document_id": document_id,
                        "filename": filename,
                        "chunk_index": chunk_index,
                        "chunk_size": len(chunk_text),
                        "start_position": start,
                        "end_position": end,
                        "created_at": int(time.time() * 1000)
                    }
                }

                chunks.append(chunk_data)
                chunk_index += 1

                # Move start position with overlap
                start = end - overlap

                # Prevent infinite loops and respect max chunks limit
                if chunk_index >= Config.MAX_CHUNKS_PER_DOCUMENT:
                    self.logger.warning(f"Reached maximum chunks limit for document {document_id}")
                    break

            return chunks

        except Exception as e:
            self.logger.error(f"Error chunking text: {str(e)}")
            raise e

    def _store_chunks_in_vector_db(self, chunks: List[Dict[str, Any]], document_id: str) -> Dict[str, Any]:
        """Store text chunks in vector database"""
        try:
            # Prepare data for vector database
            documents = []
            metadatas = []
            ids = []

            for chunk in chunks:
                # Include filename context in the embedded text for better search
                filename = chunk["metadata"].get("filename", "")
                chunk_text = chunk["text"]

                # Prepend filename context to improve search matching
                # This allows searches like "resume" to match documents with "Resume" in filename
                if filename:
                    # Extract meaningful parts from filename (remove extension, replace underscores)
                    filename_clean = os.path.splitext(filename)[0].replace('_', ' ').replace('-', ' ')
                    enhanced_text = f"Document: {filename_clean}\n\n{chunk_text}"
                else:
                    enhanced_text = chunk_text

                documents.append(enhanced_text)
                metadatas.append(chunk["metadata"])
                ids.append(chunk["id"])

            # Send to vector database
            payload = {
                "documents": documents,
                "metadatas": metadatas,
                "ids": ids
            }

            response = requests.post(
                Config.get_vector_db_url(Config.VECTOR_DB_DOCUMENTS_ENDPOINT),
                json=payload,
                timeout=Config.VECTOR_DB_TIMEOUT
            )

            if response.status_code not in [200, 201]:
                raise Exception(f"Vector DB returned status {response.status_code}: {response.text}")

            result = response.json()

            if result.get("status") != "success":
                raise Exception(f"Vector DB storage failed: {result.get('error', 'Unknown error')}")

            return result

        except Exception as e:
            self.logger.error(f"Error storing chunks in vector DB: {str(e)}")
            raise e

    def _search_vector_db(self, query_data: Dict[str, Any]) -> Dict[str, Any]:
        """Search vector database"""
        try:
            response = requests.post(
                Config.get_vector_db_url(Config.VECTOR_DB_SEARCH_ENDPOINT),
                json=query_data,
                timeout=Config.VECTOR_DB_TIMEOUT
            )

            if response.status_code != 200:
                raise Exception(f"Vector DB search returned status {response.status_code}: {response.text}")

            return response.json()

        except Exception as e:
            self.logger.error(f"Error searching vector DB: {str(e)}")
            raise e

    def _delete_from_vector_db(self, ids: List[str]) -> Dict[str, Any]:
        """Delete documents from vector database"""
        try:
            payload = {"ids": ids}

            response = requests.delete(
                Config.get_vector_db_url(Config.VECTOR_DB_DOCUMENTS_ENDPOINT),
                json=payload,
                timeout=Config.VECTOR_DB_TIMEOUT
            )

            if response.status_code != 200:
                raise Exception(f"Vector DB delete returned status {response.status_code}: {response.text}")

            return response.json()

        except Exception as e:
            self.logger.error(f"Error deleting from vector DB: {str(e)}")
            raise e

    def _cleanup_document(self, document_id: str) -> None:
        """Clean up any partial document data on error"""
        try:
            self.logger.info(f"Cleaning up partial data for document {document_id}")
            self.delete_document(document_id)
        except Exception as e:
            self.logger.error(f"Error during document cleanup: {str(e)}")
