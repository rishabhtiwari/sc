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
import tiktoken
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
        # Initialize tokenizer for token-based chunking
        self.tokenizer = tiktoken.get_encoding("cl100k_base")  # GPT-4 tokenizer
        
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
        """Split text into chunks for vector storage using token-based chunking"""
        try:
            chunks = []
            chunk_size_tokens = Config.CHUNK_SIZE  # tokens
            overlap_tokens = Config.CHUNK_OVERLAP  # tokens
            min_chunk_tokens = Config.MIN_CHUNK_SIZE  # tokens

            # Tokenize the entire text
            tokens = self.tokenizer.encode(text)

            # Token-based chunking with overlap
            start_token = 0
            chunk_index = 0

            while start_token < len(tokens):
                end_token = min(start_token + chunk_size_tokens, len(tokens))
                chunk_tokens = tokens[start_token:end_token]

                # Skip chunks that are too small
                if len(chunk_tokens) < min_chunk_tokens:
                    break

                # Decode tokens back to text
                chunk_text = self.tokenizer.decode(chunk_tokens)

                # Create enhanced chunk metadata for hybrid filtering
                file_extension = os.path.splitext(filename)[1].lower() if filename else ""
                folder_path = os.path.dirname(filename) if filename else ""

                chunk_data = {
                    "id": f"{document_id}_chunk_{chunk_index}",
                    "text": chunk_text.strip(),
                    "metadata": {
                        "document_id": document_id,
                        "filename": filename,
                        "file_extension": file_extension,
                        "folder_path": folder_path,
                        "chunk_index": chunk_index,
                        "chunk_size": len(chunk_tokens),  # token count
                        "chunk_size_chars": len(chunk_text),  # character count for reference
                        "start_position": start_token,  # token position
                        "end_position": end_token,  # token position
                        "content_type": self._detect_content_type(chunk_text, file_extension),
                        "created_at": int(time.time() * 1000)
                    }
                }

                chunks.append(chunk_data)
                chunk_index += 1

                # Calculate next start position with overlap
                next_start = end_token - overlap_tokens

                # Ensure we make progress - if next_start would be <= current start_token,
                # move forward by at least 1 token to avoid infinite loops
                if next_start <= start_token:
                    next_start = start_token + 1

                # If we've reached the end of the document, break
                if end_token >= len(tokens):
                    break

                start_token = next_start

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

    def search_documents_hybrid(
        self,
        query: str,
        metadata_filters: Dict[str, Any] = None,
        repository_names: List[str] = None,
        remote_host_names: List[str] = None,
        document_names: List[str] = None,
        file_types: List[str] = None,
        folders: List[str] = None,
        content_types: List[str] = None,
        limit: int = None,
        min_similarity: float = None
    ) -> Dict[str, Any]:
        """
        Hybrid search: Exact metadata match + semantic similarity with separated resource types

        Args:
            query: Semantic search query
            metadata_filters: Custom exact match filters
            repository_names: List of repository names to include
            remote_host_names: List of remote host names to include
            document_names: List of document names to include
            file_types: File extensions to include ['.py', '.js']
            folders: Folder paths to include
            content_types: Content types to include ['code', 'documentation']
            limit: Maximum results
            min_similarity: Minimum similarity threshold

        Returns:
            Dictionary containing filtered and ranked results
        """
        try:
            # Build comprehensive metadata filter using ChromaDB's $and operator
            filter_conditions = []

            # 1. Context resource filtering - separated by resource type for precise filtering
            resource_filters = []

            # Repository filtering
            if repository_names:
                self.logger.debug(f"🏗️ Adding repository filters for: {repository_names}")
                for repo_name in repository_names:
                    resource_filters.append({"repository_name": repo_name})

            # Remote host filtering
            if remote_host_names:
                self.logger.debug(f"🌐 Adding remote host filters for: {remote_host_names}")
                for host_name in remote_host_names:
                    # Extract host from URL format (e.g., "http://host.docker.internal" -> "host.docker.internal")
                    if host_name.startswith(('http://', 'https://')):
                        host_only = host_name.split('://', 1)[1].split(':')[0]  # Remove protocol and port
                    else:
                        host_only = host_name.split(':')[0]  # Remove port if present
                    resource_filters.append({"host": host_only})

            # Document filtering
            if document_names:
                self.logger.debug(f"📄 Adding document filters for: {document_names}")
                for doc_name in document_names:
                    resource_filters.append({"document_name": doc_name})
                    resource_filters.append({"filename": doc_name})  # Also check filename field

            # Combine all resource filters with OR (any resource match)
            if resource_filters:
                self.logger.debug(f"🔗 Combined resource filters: {len(resource_filters)} conditions")
                if len(resource_filters) == 1:
                    # Single filter - don't wrap in $or (ChromaDB requires at least 2 conditions for $or)
                    filter_conditions.append(resource_filters[0])
                else:
                    # Multiple filters - use $or
                    filter_conditions.append({"$or": resource_filters})
            else:
                self.logger.debug("⚠️ No resource filters applied - will search all documents")

            # 3. File type filtering - apply post-search for compatibility with existing data
            # 4. Content type filtering - apply post-search for compatibility with existing data

            # 5. Custom metadata filters (exact match)
            if metadata_filters:
                for key, value in metadata_filters.items():
                    filter_conditions.append({key: value})

            # Combine all conditions with $and
            if len(filter_conditions) == 0:
                where_clause = None
            elif len(filter_conditions) == 1:
                where_clause = filter_conditions[0]
            else:
                where_clause = {"$and": filter_conditions}

            # Set defaults
            if limit is None:
                limit = Config.DEFAULT_SEARCH_LIMIT
            if min_similarity is None:
                min_similarity = Config.MIN_SIMILARITY_THRESHOLD

            self.logger.info(f"Hybrid search: query='{query[:50]}...', filters={where_clause}")

            # Prepare search parameters
            search_params = {
                "query": query,
                "n_results": limit * 2,  # Get more results for better filtering
                "where": where_clause if where_clause else None
            }

            # Execute search with metadata pre-filtering
            search_result = self._search_vector_db(search_params)

            if search_result.get("status") != "success":
                return search_result

            # Apply similarity threshold filtering
            filtered_results = []
            for result in search_result.get("results", []):
                # Convert distance to similarity (distance is inverse of similarity)
                distance = result.get("distance", 1.0)
                similarity = 1.0 - distance  # Convert distance to similarity
                result["similarity"] = similarity  # Add similarity field

                if similarity >= min_similarity:
                    # Add hybrid search metadata
                    result["search_type"] = "hybrid"
                    result["applied_filters"] = self._get_applied_filters(
                        result.get("metadata", {}), where_clause
                    )
                    filtered_results.append(result)

            # Sort by similarity (highest first) and limit results
            filtered_results.sort(key=lambda x: x.get("similarity", 0), reverse=True)
            filtered_results = filtered_results[:limit]

            self.logger.info(f"Hybrid search found {len(filtered_results)} results above threshold")

            return {
                "status": "success",
                "query": query,
                "metadata_filters": where_clause,
                "results": filtered_results,
                "total_results": len(filtered_results),
                "search_type": "hybrid",
                "parameters": {
                    "limit": limit,
                    "min_similarity": min_similarity,
                    "applied_filters": list(where_clause.keys()) if where_clause else []
                },
                "timestamp": int(time.time() * 1000)
            }

        except Exception as e:
            self.logger.error(f"Hybrid search failed: {str(e)}")
            return {
                "status": "error",
                "error": f"Hybrid search failed: {str(e)}",
                "timestamp": int(time.time() * 1000)
            }

    def _detect_content_type(self, text: str, file_extension: str) -> str:
        """
        Detect content type based on text content and file extension

        Args:
            text: Text content to analyze
            file_extension: File extension (e.g., '.py', '.md')

        Returns:
            Content type string
        """
        # Code file extensions
        code_extensions = {
            '.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.cpp', '.c', '.h',
            '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.scala',
            '.r', '.m', '.sh', '.bat', '.ps1'
        }

        # Documentation file extensions
        doc_extensions = {
            '.md', '.rst', '.txt', '.doc', '.docx', '.pdf'
        }

        # Configuration file extensions
        config_extensions = {
            '.json', '.yaml', '.yml', '.xml', '.ini', '.conf', '.cfg',
            '.env', '.properties', '.toml'
        }

        # Data file extensions
        data_extensions = {
            '.csv', '.tsv', '.xlsx', '.xls', '.sql', '.db', '.sqlite'
        }

        if file_extension in code_extensions:
            return "code"
        elif file_extension in doc_extensions:
            return "documentation"
        elif file_extension in config_extensions:
            return "configuration"
        elif file_extension in data_extensions:
            return "data"
        else:
            # Analyze content for unknown extensions
            text_lower = text.lower()
            if any(keyword in text_lower for keyword in ['def ', 'function', 'class ', 'import ', 'from ']):
                return "code"
            elif any(keyword in text_lower for keyword in ['# ', '## ', '### ', 'readme', 'documentation']):
                return "documentation"
            elif any(keyword in text_lower for keyword in ['{', '}', ':', '=', 'config']):
                return "configuration"
            else:
                return "text"

    def _get_applied_filters(self, metadata: Dict[str, Any], filters: Dict[str, Any]) -> List[str]:
        """
        Get list of filters that were applied to this result

        Args:
            metadata: Document metadata
            filters: Applied filters (can be None)

        Returns:
            List of matched filter descriptions
        """
        matched = []

        if filters is None:
            return matched

        for key, value in filters.items():
            if key in metadata:
                if isinstance(value, dict) and "$in" in value:
                    if metadata[key] in value["$in"]:
                        matched.append(f"{key}={metadata[key]}")
                elif metadata[key] == value:
                    matched.append(f"{key}={value}")

        return matched

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

    def process_documents_bulk(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process multiple documents in bulk for repository integration

        Args:
            documents: List of document objects with 'content' and 'metadata' fields

        Returns:
            Dictionary with processing results
        """
        try:
            start_time = time.time()
            document_ids = []
            total_chunks = 0

            self.logger.info(f"Starting bulk processing of {len(documents)} documents")

            for i, doc in enumerate(documents):
                try:
                    content = doc.get('content', '')
                    metadata = doc.get('metadata', {})

                    if not content.strip():
                        self.logger.warning(f"Document {i} has empty content, skipping")
                        continue

                    # Generate document ID
                    document_id = str(uuid.uuid4())
                    document_ids.append(document_id)

                    # Create a synthetic filename from metadata
                    file_path = metadata.get('file_path', f'document_{i}')
                    filename = os.path.basename(file_path) if file_path else f'document_{i}.txt'

                    # Apply whitelist filtering (same as single document processing)
                    if not Config.is_allowed_file(filename):
                        self.logger.info(f"Skipping document {i+1}/{len(documents)}: {filename} (file type not whitelisted)")
                        continue

                    self.logger.info(f"Processing document {i+1}/{len(documents)}: {filename}")

                    # Chunk the text content
                    chunks = self._chunk_text(content, document_id, filename)

                    # Add enhanced metadata to each chunk for hybrid filtering
                    file_extension = os.path.splitext(filename)[1].lower() if filename else ""
                    folder_path = os.path.dirname(filename) if filename else ""

                    for chunk in chunks:
                        # Update with original metadata
                        chunk['metadata'].update(metadata)

                        # Add enhanced metadata for hybrid filtering
                        chunk['metadata']['document_id'] = document_id
                        chunk['metadata']['filename'] = filename
                        chunk['metadata']['file_extension'] = file_extension
                        chunk['metadata']['folder_path'] = folder_path
                        chunk['metadata']['content_type'] = self._detect_content_type(chunk['text'], file_extension)
                        chunk['metadata']['source'] = 'bulk_processing'

                        # Add resource_id if provided in metadata
                        if 'resource_id' in metadata:
                            chunk['metadata']['resource_id'] = metadata['resource_id']

                    # Store chunks in vector database
                    if chunks:
                        self._store_chunks_in_vector_db(chunks, document_id)
                        total_chunks += len(chunks)
                        self.logger.info(f"Stored {len(chunks)} chunks for document {filename}")

                except Exception as e:
                    self.logger.error(f"Error processing document {i}: {str(e)}")
                    continue

            processing_time = int((time.time() - start_time) * 1000)

            result = {
                "document_ids": document_ids,
                "total_documents": len(document_ids),
                "total_chunks": total_chunks,
                "processing_time_ms": processing_time
            }

            self.logger.info(f"Bulk processing completed: {len(document_ids)} documents, {total_chunks} chunks in {processing_time}ms")
            return result

        except Exception as e:
            self.logger.error(f"Error in bulk document processing: {str(e)}")
            raise e
