"""
Retriever Service for document retrieval and RAG functionality
"""
import time
import requests
from typing import Dict, List, Any, Optional
from config.settings import Config
from utils.logger import setup_logger


class RetrieverService:
    """Service for document retrieval and RAG operations"""

    def __init__(self):
        self.logger = setup_logger('retriever-service')
        self.logger.info("Initializing Retriever Service")

        # Service URLs
        self.embedding_service_url = Config.EMBEDDING_SERVICE_URL
        self.vector_db_url = Config.VECTOR_DB_URL

        self.logger.info(f"Embedding Service URL: {self.embedding_service_url}")
        self.logger.info(f"Vector DB URL: {self.vector_db_url}")

    def search_documents(self, query: str, limit: int = None,
                         min_similarity: float = None) -> Dict[str, Any]:
        """
        Search for relevant documents using semantic search
        
        Args:
            query: Search query text
            limit: Maximum number of results to return
            min_similarity: Minimum similarity threshold
            
        Returns:
            Dictionary containing search results
        """
        try:
            # Set defaults
            if limit is None:
                limit = Config.DEFAULT_SEARCH_LIMIT
            if min_similarity is None:
                min_similarity = Config.MIN_SIMILARITY_THRESHOLD

            # Validate parameters
            limit = min(limit, Config.MAX_SEARCH_LIMIT)

            self.logger.info(f"Searching documents: query='{query}', limit={limit}, min_similarity={min_similarity}")

            # Call embedding service for search
            search_url = Config.get_embedding_url(Config.EMBEDDING_SEARCH_ENDPOINT)

            payload = {
                "query": query,
                "use_hybrid": False,  # Regular search, not hybrid
                "limit": limit
            }

            response = requests.post(
                search_url,
                json=payload,
                timeout=Config.EMBEDDING_TIMEOUT,
                headers={'Content-Type': 'application/json'}
            )

            if response.status_code != 200:
                raise Exception(f"Embedding service returned status {response.status_code}: {response.text}")

            search_results = response.json()

            # Filter results by similarity threshold
            filtered_results = []
            for result in search_results.get("results", []):
                distance = result.get("distance", float('inf'))
                # Convert distance to similarity using inverse relationship
                # Lower distance = higher similarity
                similarity = 1.0 / (1.0 + distance)  # This gives values between 0 and 1
                if similarity >= min_similarity:
                    result["similarity"] = similarity
                    filtered_results.append(result)

            self.logger.info(f"Found {len(filtered_results)} documents above similarity threshold")

            return {
                "status": "success",
                "query": query,
                "results": filtered_results,
                "total_results": len(filtered_results),
                "parameters": {
                    "limit": limit,
                    "min_similarity": min_similarity
                },
                "timestamp": int(time.time() * 1000)
            }

        except Exception as e:
            self.logger.error(f"Error searching documents: {str(e)}")
            raise e

    def get_document_context(self, document_ids: List[str]) -> Dict[str, Any]:
        """
        Retrieve full context for specific documents
        
        Args:
            document_ids: List of document IDs to retrieve
            
        Returns:
            Dictionary containing document contexts
        """
        try:
            self.logger.info(f"Retrieving context for {len(document_ids)} documents")

            contexts = []
            for doc_id in document_ids:
                try:
                    # Query vector database for chunks with this document_id
                    search_payload = {
                        "query": f"document_id:{doc_id}",
                        "n_results": 50,  # Get all chunks for this document
                        "collection_name": "documents"
                    }

                    vector_db_url = Config.get_vector_db_url(Config.VECTOR_DB_SEARCH_ENDPOINT)
                    response = requests.post(
                        vector_db_url,
                        json=search_payload,
                        timeout=Config.VECTOR_DB_TIMEOUT,
                        headers={'Content-Type': 'application/json'}
                    )

                    if response.status_code == 200:
                        search_results = response.json()

                        # Filter results to only include chunks from this specific document
                        document_chunks = []
                        for result in search_results.get("results", []):
                            metadata = result.get("metadata", {})
                            if metadata.get("document_id") == doc_id:
                                document_chunks.append(result)

                        contexts.append({
                            "document_id": doc_id,
                            "chunks": document_chunks,
                            "total_chunks": len(document_chunks)
                        })

                        self.logger.info(f"Found {len(document_chunks)} chunks for document {doc_id}")
                    else:
                        self.logger.warning(f"Could not retrieve chunks for document {doc_id}: {response.status_code}")
                        contexts.append({
                            "document_id": doc_id,
                            "chunks": [],
                            "total_chunks": 0
                        })

                except Exception as e:
                    self.logger.error(f"Error retrieving context for document {doc_id}: {str(e)}")
                    contexts.append({
                        "document_id": doc_id,
                        "chunks": [],
                        "total_chunks": 0
                    })
                    continue

            return {
                "status": "success",
                "contexts": contexts,
                "total_documents": len(contexts),
                "timestamp": int(time.time() * 1000)
            }

        except Exception as e:
            self.logger.error(f"Error retrieving document contexts: {str(e)}")
            raise e

    def build_rag_context(self, query: str, max_chunks: int = None) -> Dict[str, Any]:
        """
        Build context for RAG (Retrieval-Augmented Generation)
        
        Args:
            query: User query for context building
            max_chunks: Maximum number of chunks to include
            
        Returns:
            Dictionary containing RAG context
        """
        try:
            if max_chunks is None:
                max_chunks = Config.MAX_CONTEXT_CHUNKS

            self.logger.info(f"Building RAG context for query: '{query}', max_chunks={max_chunks}")

            # Search for relevant documents
            search_results = self.search_documents(
                query=query,
                limit=max_chunks * 2,  # Get more results to have better selection
                min_similarity=Config.MIN_SIMILARITY_THRESHOLD
            )

            # Extract and rank chunks
            chunks = []
            total_context_length = 0

            for result in search_results.get("results", []):
                chunk_text = result.get("document", "")
                chunk_length = len(chunk_text)

                # Check if adding this chunk would exceed context window
                if total_context_length + chunk_length > Config.CONTEXT_WINDOW_SIZE:
                    break

                chunks.append({
                    "text": chunk_text,
                    "similarity": result.get("similarity", 0.0),
                    "document_id": result.get("metadata", {}).get("document_id"),
                    "chunk_id": result.get("id"),
                    "metadata": result.get("metadata", {})
                })

                total_context_length += chunk_length

                # Stop if we have enough chunks
                if len(chunks) >= max_chunks:
                    break

            # Build final context string
            context_text = "\n\n".join([chunk["text"] for chunk in chunks])

            self.logger.info(f"Built RAG context with {len(chunks)} chunks, {total_context_length} characters")

            return {
                "status": "success",
                "query": query,
                "context": context_text,
                "chunks": chunks,
                "total_chunks": len(chunks),
                "context_length": total_context_length,
                "parameters": {
                    "max_chunks": max_chunks,
                    "context_window_size": Config.CONTEXT_WINDOW_SIZE,
                    "min_similarity": Config.MIN_SIMILARITY_THRESHOLD
                },
                "timestamp": int(time.time() * 1000)
            }

        except Exception as e:
            self.logger.error(f"Error building RAG context: {str(e)}")
            raise e

    def build_context_aware_rag(
            self,
            query: str,
            repository_names: List[str] = None,
            remote_host_names: List[str] = None,
            document_names: List[str] = None,
            file_types: List[str] = None,
            content_types: List[str] = None,
            max_chunks: int = None,
            min_similarity: float = None
    ) -> Dict[str, Any]:
        """
        Build RAG context using hybrid filtering based on separated resource types

        Args:
            query: User query for context building
            repository_names: List of repository names to search within
            remote_host_names: List of remote host names to search within
            document_names: List of document names to search within
            file_types: File extensions to prioritize ['.py', '.js']
            content_types: Content types to prioritize ['code', 'documentation']
            max_chunks: Maximum number of chunks to include

        Returns:
            Dictionary containing context-aware RAG context
        """
        try:
            if max_chunks is None:
                max_chunks = Config.MAX_CONTEXT_CHUNKS
            if min_similarity is None:
                min_similarity = Config.MIN_SIMILARITY_THRESHOLD

            # Calculate total resources for logging
            total_resources = (len(repository_names) if repository_names else 0) + \
                            (len(remote_host_names) if remote_host_names else 0) + \
                            (len(document_names) if document_names else 0)

            self.logger.info(f"Building context-aware RAG: query='{query}', "
                             f"total_resources={total_resources}")
            self.logger.debug(f"Resource breakdown: repos={len(repository_names) if repository_names else 0}, "
                            f"hosts={len(remote_host_names) if remote_host_names else 0}, "
                            f"docs={len(document_names) if document_names else 0}")

            # Use hybrid search with separated resource type filtering
            search_results = self.search_documents_hybrid(
                query=query,
                repository_names=repository_names,
                remote_host_names=remote_host_names,
                document_names=document_names,
                file_types=file_types,
                content_types=content_types,
                limit=max_chunks * 2,  # Get more results for better selection
                min_similarity=min_similarity
            )

            # Extract and rank chunks
            chunks = []
            total_context_length = 0

            for result in search_results.get("results", []):
                chunk_text = result.get("document", "")
                chunk_length = len(chunk_text)

                # Check if adding this chunk would exceed context window
                if total_context_length + chunk_length > Config.CONTEXT_WINDOW_SIZE:
                    break

                chunks.append({
                    "text": chunk_text,
                    "similarity": result.get("similarity", 0.0),
                    "document_id": result.get("metadata", {}).get("document_id"),
                    "chunk_id": result.get("id"),
                    "metadata": result.get("metadata", {}),
                    "applied_filters": result.get("applied_filters", []),
                    "search_type": "context_aware_hybrid"
                })

                total_context_length += chunk_length

                # Stop if we have enough chunks
                if len(chunks) >= max_chunks:
                    break

            # Build final context string
            context_text = "\n\n".join([chunk["text"] for chunk in chunks])

            self.logger.info(f"Built context-aware RAG with {len(chunks)} chunks, "
                             f"{total_context_length} characters")

            return {
                "status": "success",
                "query": query,
                "context": context_text,
                "chunks": chunks,
                "total_chunks": len(chunks),
                "context_length": total_context_length,
                "search_type": "context_aware_hybrid",
                "context_resources": context_resources,
                "parameters": {
                    "max_chunks": max_chunks,
                    "context_window_size": Config.CONTEXT_WINDOW_SIZE,
                    "min_similarity": Config.MIN_SIMILARITY_THRESHOLD,
                    "file_types": file_types,
                    "content_types": content_types
                },
                "timestamp": int(time.time() * 1000)
            }

        except Exception as e:
            self.logger.error(f"Error building context-aware RAG: {str(e)}")
            raise e

    def search_documents_hybrid(
            self,
            query: str,
            repository_names: List[str] = None,
            remote_host_names: List[str] = None,
            document_names: List[str] = None,
            file_types: List[str] = None,
            content_types: List[str] = None,
            limit: int = None,
            min_similarity: float = None
    ) -> Dict[str, Any]:
        """
        Hybrid search using embedding service with separated resource type filtering

        Args:
            query: Search query
            repository_names: List of repository names to search within
            remote_host_names: List of remote host names to search within
            document_names: List of document names to search within
            file_types: File extensions to include
            content_types: Content types to include
            limit: Maximum number of results
            min_similarity: Minimum similarity threshold

        Returns:
            Dictionary containing search results
        """
        try:
            # Set defaults
            if limit is None:
                limit = Config.DEFAULT_SEARCH_LIMIT
            if min_similarity is None:
                min_similarity = Config.MIN_SIMILARITY_THRESHOLD

            # Validate parameters
            limit = min(limit, Config.MAX_SEARCH_LIMIT)

            # Calculate total resources for logging
            total_resources = (len(repository_names) if repository_names else 0) + \
                            (len(remote_host_names) if remote_host_names else 0) + \
                            (len(document_names) if document_names else 0)

            self.logger.info(f"Hybrid search: query='{query}', total_resources={total_resources}")
            self.logger.debug(f"Resource breakdown: repos={len(repository_names) if repository_names else 0}, "
                            f"hosts={len(remote_host_names) if remote_host_names else 0}, "
                            f"docs={len(document_names) if document_names else 0}")

            # Call embedding service for hybrid search
            search_url = Config.get_embedding_url("/embed/search")

            payload = {
                "query": query,
                "use_hybrid": True,  # Enable hybrid search
                "limit": limit,
                "min_similarity": min_similarity
            }

            # Add separated resource type filtering parameters
            if repository_names:
                payload["repository_names"] = repository_names
            if remote_host_names:
                payload["remote_host_names"] = remote_host_names
            if document_names:
                payload["document_names"] = document_names
            if file_types:
                payload["file_types"] = file_types
            if content_types:
                payload["content_types"] = content_types

            response = requests.post(
                search_url,
                json=payload,
                timeout=Config.EMBEDDING_TIMEOUT,
                headers={'Content-Type': 'application/json'}
            )

            if response.status_code != 200:
                raise Exception(f"Embedding service returned status {response.status_code}: {response.text}")

            search_results = response.json()

            if search_results.get("status") != "success":
                raise Exception(f"Embedding service error: {search_results.get('error', 'Unknown error')}")

            results = search_results.get("results", [])

            self.logger.info(f"Hybrid search found {len(results)} results")

            return {
                "status": "success",
                "query": query,
                "results": results,
                "total_results": len(results),
                "search_type": "hybrid",
                "parameters": {
                    "limit": limit,
                    "min_similarity": min_similarity,
                    "context_resources": context_resources,
                    "file_types": file_types,
                    "content_types": content_types
                },
                "timestamp": int(time.time() * 1000)
            }

        except Exception as e:
            self.logger.error(f"Error in hybrid search: {str(e)}")
            raise e

    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on retriever service and dependencies
        
        Returns:
            Dictionary containing health status
        """
        try:
            health_status = {
                "service": "healthy",
                "embedding_service": "unknown",
                "vector_db": "unknown"
            }

            # Check embedding service
            try:
                embedding_health_url = Config.get_embedding_url(Config.EMBEDDING_HEALTH_ENDPOINT)
                response = requests.get(embedding_health_url, timeout=5)
                health_status["embedding_service"] = "healthy" if response.status_code == 200 else "unhealthy"
            except Exception:
                health_status["embedding_service"] = "unhealthy"

            # Check vector database
            try:
                vector_db_health_url = Config.get_vector_db_url(Config.VECTOR_DB_HEALTH_ENDPOINT)
                response = requests.get(vector_db_health_url, timeout=5)
                health_status["vector_db"] = "healthy" if response.status_code == 200 else "unhealthy"
            except Exception:
                health_status["vector_db"] = "unhealthy"

            overall_healthy = all(status == "healthy" for status in health_status.values())

            return {
                "status": "healthy" if overall_healthy else "degraded",
                "service_name": Config.SERVICE_NAME,
                "version": Config.SERVICE_VERSION,
                "dependencies": health_status,
                "timestamp": int(time.time() * 1000)
            }

        except Exception as e:
            self.logger.error(f"Health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": int(time.time() * 1000)
            }
