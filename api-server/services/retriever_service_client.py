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
            error_msg = f"Error building RAG context from documents: {str(e)}"
            self.logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg,
                "timestamp": int(datetime.now().timestamp() * 1000)
            }

    def build_context_aware_rag(
        self,
        query: str,
        repository_names: List[str] = None,
        remote_host_names: List[str] = None,
        document_names: List[str] = None,
        file_types: List[str] = None,
        content_types: List[str] = None,
        max_chunks: int = 5
    ) -> Dict[str, Any]:
        """
        Build context-aware RAG using hybrid filtering with separated resource types

        Args:
            query: Search query
            repository_names: List of repository names to search within
            remote_host_names: List of remote host names to search within
            document_names: List of document names to search within
            file_types: File extensions to prioritize
            content_types: Content types to prioritize
            max_chunks: Maximum number of chunks to retrieve

        Returns:
            Dict containing RAG context or error
        """
        try:
            payload = {
                "query": query,
                "max_chunks": max_chunks
            }

            # Add context filtering parameters by resource type
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

            # Calculate total resources for logging
            total_resources = (len(repository_names) if repository_names else 0) + \
                            (len(remote_host_names) if remote_host_names else 0) + \
                            (len(document_names) if document_names else 0)

            # 🐛 DEBUG: Log detailed payload being sent to retriever service
            self.logger.debug(f"🚀 DEBUG - Retriever Service Client Payload:")
            self.logger.debug(f"  🌐 URL: {self.base_url}/retrieve/rag/context-aware")
            self.logger.debug(f"  📝 Query: '{query}'")
            self.logger.debug(f"  📂 Repository Names ({len(repository_names) if repository_names else 0}): {repository_names}")
            self.logger.debug(f"  🌐 Remote Host Names ({len(remote_host_names) if remote_host_names else 0}): {remote_host_names}")
            self.logger.debug(f"  📄 Document Names ({len(document_names) if document_names else 0}): {document_names}")
            self.logger.debug(f"  📁 File Types: {file_types}")
            self.logger.debug(f"  🏷️  Content Types: {content_types}")
            self.logger.debug(f"  🔢 Max Chunks: {max_chunks}")
            self.logger.debug(f"  📦 Full Payload: {payload}")

            # 🐛 DEBUG: Log the complete JSON payload that will be sent
            import json
            self.logger.debug(f"🌐 DEBUG - Complete HTTP Request:")
            self.logger.debug(f"  📡 Method: POST")
            self.logger.debug(f"  🔗 URL: {self.base_url}/retrieve/rag/context-aware")
            self.logger.debug(f"  📋 Headers: {{'Content-Type': 'application/json'}}")
            self.logger.debug(f"  📦 JSON Body:")
            self.logger.debug(json.dumps(payload, indent=4))

            self.logger.info(f"Building context-aware RAG from {total_resources} resources")

            response = requests.post(
                f"{self.base_url}/retrieve/rag/context-aware",
                json=payload,
                timeout=self.timeout,
                headers={'Content-Type': 'application/json'}
            )

            if response.status_code == 200:
                result = response.json()
                context_length = result.get('context_length', 0)
                total_chunks = result.get('total_chunks', 0)

                # 🐛 DEBUG: Log detailed response from retriever service
                self.logger.debug(f"✅ DEBUG - Retriever Service Response:")
                self.logger.debug(f"  🌐 Status Code: {response.status_code}")
                self.logger.debug(f"  📊 Total Chunks: {total_chunks}")
                self.logger.debug(f"  📏 Context Length: {context_length} chars")
                self.logger.debug(f"  🔍 Search Type: {result.get('search_type', 'unknown')}")
                self.logger.debug(f"  📝 Context Preview: '{result.get('context', '')[:200]}...'")
                self.logger.debug(f"  📋 Full Response Keys: {list(result.keys())}")

                self.logger.info(f"Built context-aware RAG: {context_length} chars, {total_chunks} chunks")
                return {
                    "status": "success",
                    "data": result,
                    "timestamp": int(datetime.now().timestamp() * 1000)
                }
            else:
                # 🐛 DEBUG: Log detailed error response from retriever service
                self.logger.debug(f"❌ DEBUG - Retriever Service Error:")
                self.logger.debug(f"  🌐 Status Code: {response.status_code}")
                self.logger.debug(f"  📝 Response Text: {response.text}")
                self.logger.debug(f"  📦 Request Payload: {payload}")

                error_msg = f"Context-aware RAG error: {response.status_code} - {response.text}"
                self.logger.error(error_msg)
                return {
                    "status": "error",
                    "error": error_msg,
                    "timestamp": int(datetime.now().timestamp() * 1000)
                }

        except Exception as e:
            # 🐛 DEBUG: Log detailed exception information
            self.logger.debug(f"💥 DEBUG - Client Exception:")
            self.logger.debug(f"  🚫 Exception Type: {type(e).__name__}")
            self.logger.debug(f"  📝 Exception Message: {str(e)}")
            self.logger.debug(f"  📦 Request Payload: {payload}")

            error_msg = f"Context-aware RAG client error: {str(e)}"
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
