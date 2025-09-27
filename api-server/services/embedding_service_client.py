"""
Embedding Service Client - Interface for communicating with the embedding service
"""

import requests
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from werkzeug.datastructures import FileStorage


class EmbeddingServiceClient:
    """Client for communicating with the embedding service"""
    
    def __init__(self, base_url: str = "http://ichat-embedding-service:8085", timeout: int = 120):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.logger = logging.getLogger('api-server')
    
    def embed_document(
        self,
        file: FileStorage,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Upload and embed a document
        
        Args:
            file: Document file to embed
            metadata: Optional metadata for the document
            
        Returns:
            Dict containing embedding result or error
        """
        try:
            # Reset file stream to beginning if possible
            if hasattr(file, 'stream') and hasattr(file.stream, 'seek'):
                file.stream.seek(0)
            elif hasattr(file, 'seek'):
                file.seek(0)

            # Prepare files and data for multipart upload
            files = {
                'file': (file.filename, file.stream, file.content_type or 'application/octet-stream')
            }

            data = {}
            if metadata:
                # Convert metadata dict to individual form fields
                for key, value in metadata.items():
                    data[key] = str(value)

            self.logger.info(f"Embedding document: {file.filename} with metadata: {metadata}")

            response = requests.post(
                f"{self.base_url}/embed/document",
                files=files,
                data=data,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                self.logger.info(f"Document embedded successfully: {result.get('document_id')}")
                return {
                    "status": "success",
                    "data": result,
                    "timestamp": int(datetime.now().timestamp() * 1000)
                }
            else:
                error_msg = f"Embedding service error: {response.status_code}"
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
            error_msg = "Embedding service timeout"
            self.logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg,
                "timestamp": int(datetime.now().timestamp() * 1000)
            }
        except requests.exceptions.ConnectionError:
            error_msg = "Cannot connect to embedding service"
            self.logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg,
                "timestamp": int(datetime.now().timestamp() * 1000)
            }
        except Exception as e:
            error_msg = f"Embedding service client error: {str(e)}"
            self.logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg,
                "timestamp": int(datetime.now().timestamp() * 1000)
            }
    
    def search_documents(
        self,
        query: str,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Search for documents using semantic search
        
        Args:
            query: Search query text
            limit: Maximum number of results to return
            
        Returns:
            Dict containing search results or error
        """
        try:
            payload = {
                "query": query
            }
            
            if limit is not None:
                payload["limit"] = limit
            
            self.logger.info(f"Searching documents via embedding service: {query[:50]}...")
            
            response = requests.post(
                f"{self.base_url}/embed/search",
                json=payload,
                timeout=self.timeout,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                result = response.json()
                self.logger.info(f"Found {len(result.get('results', []))} documents")
                return {
                    "status": "success",
                    "data": result,
                    "timestamp": int(datetime.now().timestamp() * 1000)
                }
            else:
                error_msg = f"Embedding search error: {response.status_code}"
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
            error_msg = f"Embedding search client error: {str(e)}"
            self.logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg,
                "timestamp": int(datetime.now().timestamp() * 1000)
            }
    
    def get_document_info(self, document_id: str) -> Dict[str, Any]:
        """
        Get information about a specific document
        
        Args:
            document_id: Document ID
            
        Returns:
            Dict containing document information or error
        """
        try:
            self.logger.info(f"Getting document info: {document_id}")
            
            response = requests.get(
                f"{self.base_url}/embed/document/{document_id}",
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
                error_msg = f"Document info error: {response.status_code}"
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
            error_msg = f"Document info client error: {str(e)}"
            self.logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg,
                "timestamp": int(datetime.now().timestamp() * 1000)
            }
    
    def get_embedding_status(self) -> Dict[str, Any]:
        """
        Get embedding service status
        
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
                    "error": f"Embedding service unavailable: {response.status_code}",
                    "timestamp": int(datetime.now().timestamp() * 1000)
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": f"Cannot reach embedding service: {str(e)}",
                "timestamp": int(datetime.now().timestamp() * 1000)
            }


# Global embedding client instance
embedding_client = EmbeddingServiceClient()
