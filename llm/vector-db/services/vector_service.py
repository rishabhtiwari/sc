"""
Vector Service - Core vector database operations using ChromaDB
"""

import os
import time
import logging
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from config.settings import Config


class VectorService:
    """Core vector database service using ChromaDB"""
    
    def __init__(self):
        self.logger = logging.getLogger('vector-db')
        self.client = None
        self.collection = None
        self.embedding_model = None
        self.config = Config()
        
    def initialize(self) -> bool:
        """Initialize ChromaDB client and embedding model"""
        try:
            self.logger.info("Initializing Vector Service...")
            
            # Initialize ChromaDB client
            self._initialize_chroma_client()
            
            # Initialize embedding model
            self._initialize_embedding_model()
            
            # Create or get collection
            self._initialize_collection()
            
            self.logger.info("Vector Service initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Vector Service: {str(e)}")
            return False
    
    def _initialize_chroma_client(self):
        """Initialize ChromaDB client"""
        try:
            # Ensure data directory exists
            os.makedirs(self.config.CHROMA_PERSIST_DIRECTORY, exist_ok=True)
            
            # Create ChromaDB client with persistence
            self.client = chromadb.PersistentClient(
                path=self.config.CHROMA_PERSIST_DIRECTORY,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            self.logger.info(f"ChromaDB client initialized with persistence: {self.config.CHROMA_PERSIST_DIRECTORY}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize ChromaDB client: {str(e)}")
            raise
    
    def _initialize_embedding_model(self):
        """Initialize sentence transformer embedding model"""
        try:
            self.logger.info(f"Loading embedding model: {self.config.EMBEDDING_MODEL}")
            self.embedding_model = SentenceTransformer(self.config.EMBEDDING_MODEL)
            self.logger.info("Embedding model loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to load embedding model: {str(e)}")
            raise
    
    def _initialize_collection(self):
        """Initialize or get ChromaDB collection"""
        try:
            # Try to get existing collection
            try:
                self.collection = self.client.get_collection(
                    name=self.config.CHROMA_COLLECTION_NAME
                )
                self.logger.info(f"Using existing collection: {self.config.CHROMA_COLLECTION_NAME}")
                
            except Exception:
                # Create new collection if it doesn't exist
                self.collection = self.client.create_collection(
                    name=self.config.CHROMA_COLLECTION_NAME,
                    metadata={"description": "Document embeddings for RAG"}
                )
                self.logger.info(f"Created new collection: {self.config.CHROMA_COLLECTION_NAME}")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize collection: {str(e)}")
            raise
    
    def health_check(self) -> Dict[str, Any]:
        """Check service health"""
        try:
            if not self.client or not self.collection or not self.embedding_model:
                return {
                    "status": "unhealthy",
                    "error": "Service not properly initialized",
                    "timestamp": int(time.time() * 1000)
                }
            
            # Get collection info
            collection_count = self.collection.count()
            
            return {
                "status": "healthy",
                "collections": 1,
                "documents": collection_count,
                "embedding_model": self.config.EMBEDDING_MODEL,
                "timestamp": int(time.time() * 1000)
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": int(time.time() * 1000)
            }
    
    def add_documents(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Add documents to the vector database"""
        try:
            if not documents:
                return {"status": "error", "error": "No documents provided"}
            
            # Generate IDs if not provided
            if not ids:
                ids = [str(uuid.uuid4()) for _ in documents]
            
            # Generate embeddings
            self.logger.info(f"Generating embeddings for {len(documents)} documents...")
            embeddings = self.embedding_model.encode(documents).tolist()
            
            # Prepare metadata - ChromaDB requires non-empty metadata
            if not metadatas:
                metadatas = [{"source": "api", "timestamp": int(time.time())} for _ in documents]

            # Add to collection
            self.collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            
            self.logger.info(f"Successfully added {len(documents)} documents to collection")
            
            return {
                "status": "success",
                "documents_added": len(documents),
                "ids": ids,
                "timestamp": int(time.time() * 1000)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to add documents: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": int(time.time() * 1000)
            }

    def search_documents(
        self,
        query: str,
        n_results: int = None,
        where: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Search for similar documents"""
        try:
            if not query.strip():
                return {"status": "error", "error": "Empty query provided"}

            # Use default if not specified
            if n_results is None:
                n_results = self.config.DEFAULT_SEARCH_RESULTS

            # Limit results
            n_results = min(n_results, self.config.MAX_SEARCH_RESULTS)

            # Generate query embedding
            query_embedding = self.embedding_model.encode([query]).tolist()[0]

            # Search in collection
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where
            )

            # Format results
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    result = {
                        'id': results['ids'][0][i],
                        'document': doc,
                        'distance': results['distances'][0][i] if results['distances'] else None,
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {}
                    }
                    formatted_results.append(result)

            return {
                "status": "success",
                "query": query,
                "results": formatted_results,
                "total_results": len(formatted_results),
                "timestamp": int(time.time() * 1000)
            }

        except Exception as e:
            self.logger.error(f"Search failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": int(time.time() * 1000)
            }

    def delete_documents(self, ids: List[str]) -> Dict[str, Any]:
        """Delete documents by IDs"""
        try:
            if not ids:
                return {"status": "error", "error": "No document IDs provided"}

            self.collection.delete(ids=ids)

            return {
                "status": "success",
                "deleted_count": len(ids),
                "timestamp": int(time.time() * 1000)
            }

        except Exception as e:
            self.logger.error(f"Failed to delete documents: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": int(time.time() * 1000)
            }

    def get_collection_info(self) -> Dict[str, Any]:
        """Get collection information"""
        try:
            count = self.collection.count()

            return {
                "status": "success",
                "collection_name": self.config.CHROMA_COLLECTION_NAME,
                "document_count": count,
                "embedding_model": self.config.EMBEDDING_MODEL,
                "embedding_dimension": self.config.EMBEDDING_DIMENSION,
                "timestamp": int(time.time() * 1000)
            }

        except Exception as e:
            self.logger.error(f"Failed to get collection info: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": int(time.time() * 1000)
            }
