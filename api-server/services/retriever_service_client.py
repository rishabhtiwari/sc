"""
Retriever Service Client - Interface for communicating with the retriever service
"""

import requests
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import json


class RetrieverServiceClient:
    """Client for communicating with the retriever service"""
    
    def __init__(self, base_url: str = "http://ichat-retriever-service:8086", timeout: int = 300):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.logger = logging.getLogger('api-server')
    
    def search_documents(
        self,
        query: str,
        limit: Optional[int] = None,
        min_similarity: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Search for documents using semantic search
        
        Args:
            query: Search query text
            limit: Maximum number of results to return
            min_similarity: Minimum similarity threshold
            
        Returns:
            Dict containing search results or error
        """
        try:
            payload = {
                "query": query
            }
            
            if limit is not None:
                payload["limit"] = limit
            if min_similarity is not None:
                payload["min_similarity"] = min_similarity
            
            self.logger.info(f"Searching documents: {query[:50]}...")
            
            response = requests.post(
                f"{self.base_url}/retrieve/search",
                json=payload,
                timeout=self.timeout,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                result = response.json()
                self.logger.info(f"Found {result.get('total_results', 0)} documents")
                return {
                    "status": "success",
                    "data": result,
                    "timestamp": int(datetime.now().timestamp() * 1000)
                }
            else:
                error_msg = f"Retriever service error: {response.status_code}"
                self.logger.error(error_msg)
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error", error_msg)
                except:
                    pass
                
                return {
                    "status": "error",
                    "error": error_msg,
                    "timestamp": int(datetime.now().timestamp() * 1000)
                }
                
        except requests.exceptions.Timeout:
            error_msg = "Retriever service timeout"
            self.logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg,
                "timestamp": int(datetime.now().timestamp() * 1000)
            }
        except requests.exceptions.ConnectionError:
            error_msg = "Cannot connect to retriever service"
            self.logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg,
                "timestamp": int(datetime.now().timestamp() * 1000)
            }
        except Exception as e:
            error_msg = f"Retriever service client error: {str(e)}"
            self.logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg,
                "timestamp": int(datetime.now().timestamp() * 1000)
            }
    
    def build_rag_context(
        self,
        query: str,
        max_chunks: Optional[int] = None,
        context_window_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Build RAG context for a query
        
        Args:
            query: Query text for context building
            max_chunks: Maximum number of chunks to include
            context_window_size: Maximum context size in characters
            
        Returns:
            Dict containing RAG context or error
        """
        try:
            payload = {
                "query": query
            }
            
            if max_chunks is not None:
                payload["max_chunks"] = max_chunks
            if context_window_size is not None:
                payload["context_window_size"] = context_window_size
            
            self.logger.info(f"Building RAG context for: {query[:50]}...")
            
            response = requests.post(
                f"{self.base_url}/retrieve/rag",
                json=payload,
                timeout=self.timeout,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                result = response.json()
                context_length = result.get('context_length', 0)
                total_chunks = result.get('total_chunks', 0)
                self.logger.info(f"Built RAG context: {context_length} chars, {total_chunks} chunks")
                return {
                    "status": "success",
                    "data": result,
                    "timestamp": int(datetime.now().timestamp() * 1000)
                }
            else:
                error_msg = f"RAG context error: {response.status_code}"
                self.logger.error(error_msg)
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error", error_msg)
                except:
                    pass
                
                return {
                    "status": "error",
                    "error": error_msg,
                    "timestamp": int(datetime.now().timestamp() * 1000)
                }
                
        except Exception as e:
            error_msg = f"RAG context client error: {str(e)}"
            self.logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg,
                "timestamp": int(datetime.now().timestamp() * 1000)
            }
    
    def get_document_context(self, document_ids: str) -> Dict[str, Any]:
        """
        Get context for specific documents
        
        Args:
            document_ids: Comma-separated document IDs
            
        Returns:
            Dict containing document context or error
        """
        try:
            self.logger.info(f"Getting context for documents: {document_ids}")
            
            response = requests.get(
                f"{self.base_url}/retrieve/context/{document_ids}",
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "status": "success",
                    "data": result,
                    "timestamp": int(datetime.now().timestamp() * 1000)
                }
            else:
                error_msg = f"Document context error: {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error", error_msg)
                except:
                    pass
                
                return {
                    "status": "error",
                    "error": error_msg,
                    "timestamp": int(datetime.now().timestamp() * 1000)
                }
                
        except Exception as e:
            error_msg = f"Document context client error: {str(e)}"
            self.logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg,
                "timestamp": int(datetime.now().timestamp() * 1000)
            }
    
    def get_retriever_status(self) -> Dict[str, Any]:
        """
        Get retriever service status
        
        Returns:
            Dict containing service status
        """
        try:
            response = requests.get(
                f"{self.base_url}/health",
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "status": "error",
                    "error": f"Retriever service unavailable: {response.status_code}",
                    "timestamp": int(datetime.now().timestamp() * 1000)
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": f"Cannot reach retriever service: {str(e)}",
                "timestamp": int(datetime.now().timestamp() * 1000)
            }

    def build_rag_context_from_documents(
        self,
        query: str,
        document_ids: list,
        max_chunks: int = 3,
        context_window_size: int = 4000
    ) -> Dict[str, Any]:
        """
        Build RAG context from specific documents

        Args:
            query: Search query
            document_ids: List of document IDs to search within
            max_chunks: Maximum number of chunks to retrieve
            context_window_size: Maximum context size in characters

        Returns:
            Dict containing RAG context or error
        """
        try:
            self.logger.info(f"Building RAG context from {len(document_ids)} documents")

            # Get context for specific documents using existing endpoint
            doc_ids_str = ",".join(document_ids)
            response = requests.get(
                f"{self.base_url}/retrieve/context/{doc_ids_str}",
                timeout=self.timeout
            )

            if response.status_code == 200:
                result = response.json()

                # Extract chunks from all documents
                all_chunks = []
                total_length = 0

                for context in result.get("contexts", []):
                    for chunk in context.get("chunks", []):
                        # The chunk text is in the 'document' field, not 'text'
                        chunk_text = chunk.get("document", "")
                        chunk_length = len(chunk_text)

                        # Check context window size
                        if total_length + chunk_length > context_window_size:
                            break

                        all_chunks.append({
                            "text": chunk_text,
                            "document_id": context.get("document_id"),
                            "chunk_id": chunk.get("id"),
                            "metadata": chunk.get("metadata", {})
                        })

                        total_length += chunk_length

                        # Check max chunks limit
                        if len(all_chunks) >= max_chunks:
                            break

                    if len(all_chunks) >= max_chunks:
                        break

                # Build context text
                context_text = "\n\n".join([chunk["text"] for chunk in all_chunks])

                return {
                    "status": "success",
                    "data": {
                        "query": query,
                        "context": context_text,
                        "chunks": all_chunks,
                        "total_chunks": len(all_chunks),
                        "context_length": total_length,
                        "document_ids": document_ids
                    },
                    "timestamp": int(datetime.now().timestamp() * 1000)
                }
            else:
                error_msg = f"Document context error: {response.status_code} - {response.text}"
                self.logger.error(error_msg)
                return {
                    "status": "error",
                    "error": error_msg,
                    "timestamp": int(datetime.now().timestamp() * 1000)
                }

        except Exception as e:
            error_msg = f"Context building client error: {str(e)}"
            self.logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg,
                "timestamp": int(datetime.now().timestamp() * 1000)
            }


# Global retriever client instance
retriever_client = RetrieverServiceClient()
