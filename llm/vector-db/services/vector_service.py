"""
Vector Service - Core vector database operations using ChromaDB
"""

import os
import time
import logging
import uuid
import hashlib
import threading
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from config.settings import Config
from services.embedding_factory import embedding_factory, EmbeddingModelConfig
from services.embedding_factory import embedding_factory, EmbeddingModelConfig


class VectorService:
    """Core vector database service using ChromaDB"""
    
    def __init__(self):
        self.logger = logging.getLogger('vector-db')
        self.client = None
        self.collection = None
        self.embedding_model = None
        self.config = Config()
        self._cleanup_timer = None
        self._start_cleanup_scheduler()
        
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
        """Initialize embedding model using factory pattern"""
        try:
            model_name = self.config.EMBEDDING_MODEL
            self.logger.info(f"Loading embedding model: {model_name}")

            # Use factory to create model
            self.embedding_model = embedding_factory.create_model(model_name)

            if not self.embedding_model:
                raise RuntimeError(f"Failed to create embedding model: {model_name}")

            # Update config with actual model dimension
            model_config = EmbeddingModelConfig.get_model_config(model_name)
            if model_config:
                self.config.EMBEDDING_DIMENSION = model_config['dimension']
                self.logger.info(f"Model dimension: {self.config.EMBEDDING_DIMENSION}")

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

    def _generate_content_hash(self, content: str) -> str:
        """Generate SHA-256 hash of document content"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def _find_duplicate_by_hash(self, content_hash: str) -> Optional[Dict[str, Any]]:
        """Find existing document by content hash"""
        try:
            # Get all documents with matching content hash using where filter
            results = self.collection.get(
                where={"content_hash": content_hash},
                limit=1
            )

            if results['documents'] and len(results['documents']) > 0:
                return {
                    'id': results['ids'][0],
                    'document': results['documents'][0],
                    'metadata': results['metadatas'][0] if results['metadatas'] else {}
                }
            return None

        except Exception as e:
            self.logger.warning(f"Error checking for duplicates: {str(e)}")
            return None

    def _update_document_metadata(self, doc_id: str, new_metadata: Dict[str, Any]) -> bool:
        """Update metadata for existing document"""
        try:
            # Get current document
            current = self.collection.get(ids=[doc_id])
            if not current['documents']:
                return False

            # Merge metadata - keep existing, add new fields, update timestamp
            existing_metadata = current['metadatas'][0] if current['metadatas'] else {}
            merged_metadata = {**existing_metadata, **new_metadata}
            merged_metadata['last_updated'] = int(time.time())
            merged_metadata['update_count'] = existing_metadata.get('update_count', 0) + 1

            # Update the document with new metadata
            self.collection.update(
                ids=[doc_id],
                metadatas=[merged_metadata]
            )

            self.logger.info(f"Updated metadata for document {doc_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to update document metadata: {str(e)}")
            return False
    
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
        ids: Optional[List[str]] = None,
        skip_duplicates: bool = True
    ) -> Dict[str, Any]:
        """Add documents to the vector database with deduplication"""
        try:
            if not documents:
                return {"status": "error", "error": "No documents provided"}

            # Prepare metadata - ChromaDB requires non-empty metadata
            if not metadatas:
                metadatas = [{"source": "api", "timestamp": int(time.time())} for _ in documents]

            # Process documents for deduplication
            new_documents = []
            new_metadatas = []
            new_ids = []
            updated_documents = []
            skipped_duplicates = []

            for i, doc in enumerate(documents):
                content_hash = self._generate_content_hash(doc)

                # Add content hash to metadata
                current_metadata = metadatas[i] if i < len(metadatas) else {"source": "api"}
                current_metadata["content_hash"] = content_hash
                current_metadata["timestamp"] = int(time.time())

                if skip_duplicates:
                    # Check for existing document with same hash
                    existing = self._find_duplicate_by_hash(content_hash)

                    if existing:
                        # Update existing document metadata
                        if self._update_document_metadata(existing['id'], current_metadata):
                            updated_documents.append({
                                'id': existing['id'],
                                'action': 'updated_metadata'
                            })
                        else:
                            skipped_duplicates.append({
                                'content_hash': content_hash,
                                'reason': 'duplicate_update_failed'
                            })
                        continue

                # Add to new documents list
                new_documents.append(doc)
                new_metadatas.append(current_metadata)

                # Generate ID if not provided
                if ids and i < len(ids):
                    new_ids.append(ids[i])
                else:
                    new_ids.append(str(uuid.uuid4()))

            # Add new documents to collection
            documents_added = 0
            if new_documents:
                self.logger.info(f"Generating embeddings for {len(new_documents)} new documents...")
                embeddings = self.embedding_model.encode(new_documents).tolist()

                self.collection.add(
                    documents=new_documents,
                    embeddings=embeddings,
                    metadatas=new_metadatas,
                    ids=new_ids
                )

                documents_added = len(new_documents)
                self.logger.info(f"Successfully added {documents_added} new documents to collection")

            # Collect all document IDs for client context storage
            all_document_ids = new_ids.copy()  # Start with new document IDs
            for updated_doc in updated_documents:
                all_document_ids.append(updated_doc['id'])  # Add updated document IDs

            return {
                "status": "success",
                "documents_added": documents_added,
                "documents_updated": len(updated_documents),
                "duplicates_skipped": len(skipped_duplicates),
                "new_document_ids": new_ids,
                "updated_documents": updated_documents,
                "skipped_duplicates": skipped_duplicates,
                "all_document_ids": all_document_ids,  # Complete list for context storage
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

    def _start_cleanup_scheduler(self):
        """Start the cleanup scheduler"""
        def schedule_cleanup():
            try:
                # Schedule cleanup to run every 24 hours
                self._cleanup_timer = threading.Timer(24 * 60 * 60, schedule_cleanup)  # 24 hours
                self._cleanup_timer.daemon = True
                self._cleanup_timer.start()

                # Run cleanup for documents older than 7 days
                self.cleanup_old_duplicates(days_old=7)

            except Exception as e:
                self.logger.error(f"Error in cleanup scheduler: {str(e)}")

        # Start the first cleanup after 1 hour
        self._cleanup_timer = threading.Timer(60 * 60, schedule_cleanup)  # 1 hour
        self._cleanup_timer.daemon = True
        self._cleanup_timer.start()

        self.logger.info("Cleanup scheduler started - will run every 24 hours")

    def cleanup_old_duplicates(self, days_old: int = 7) -> Dict[str, Any]:
        """Clean up duplicate documents older than specified days"""
        try:
            self.logger.info(f"Starting cleanup of duplicates older than {days_old} days...")

            # Calculate cutoff timestamp (7 days ago)
            cutoff_time = int((datetime.now() - timedelta(days=days_old)).timestamp())

            # Get all documents
            all_docs = self.collection.get()

            if not all_docs['documents']:
                return {
                    "status": "success",
                    "message": "No documents found for cleanup",
                    "cleaned_count": 0
                }

            # Group documents by content hash
            hash_groups = {}
            for i, doc_id in enumerate(all_docs['ids']):
                metadata = all_docs['metadatas'][i] if all_docs['metadatas'] else {}
                content_hash = metadata.get('content_hash')
                timestamp = metadata.get('timestamp', 0)

                if content_hash:
                    if content_hash not in hash_groups:
                        hash_groups[content_hash] = []

                    hash_groups[content_hash].append({
                        'id': doc_id,
                        'timestamp': timestamp,
                        'metadata': metadata
                    })

            # Find duplicates to remove
            ids_to_remove = []
            for content_hash, docs in hash_groups.items():
                if len(docs) > 1:
                    # Sort by timestamp (keep the newest)
                    docs.sort(key=lambda x: x['timestamp'], reverse=True)

                    # Mark older duplicates for removal if they're older than cutoff
                    for doc in docs[1:]:  # Skip the first (newest) document
                        if doc['timestamp'] < cutoff_time:
                            ids_to_remove.append(doc['id'])

            # Remove old duplicates
            cleaned_count = 0
            if ids_to_remove:
                # Remove in batches to avoid overwhelming the database
                batch_size = 100
                for i in range(0, len(ids_to_remove), batch_size):
                    batch = ids_to_remove[i:i + batch_size]
                    self.collection.delete(ids=batch)
                    cleaned_count += len(batch)

                self.logger.info(f"Cleaned up {cleaned_count} old duplicate documents")

            return {
                "status": "success",
                "message": f"Cleanup completed successfully",
                "cleaned_count": cleaned_count,
                "cutoff_days": days_old,
                "timestamp": int(time.time() * 1000)
            }

        except Exception as e:
            self.logger.error(f"Failed to cleanup old duplicates: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": int(time.time() * 1000)
            }

    def clear_all_documents(self) -> Dict[str, Any]:
        """Clear all documents from the vector database"""
        try:
            self.logger.info("Clearing all documents from vector database...")

            # Get count before deletion
            count_before = self.collection.count()

            # Delete the entire collection and recreate it
            collection_name = self.collection.name
            self.client.delete_collection(collection_name)

            # Recreate the collection
            self.collection = self.client.create_collection(
                name=collection_name,
                embedding_function=None,  # We handle embeddings manually
                metadata={"hnsw:space": "cosine"}
            )

            self.logger.info(f"Successfully cleared {count_before} documents from vector database")

            return {
                "status": "success",
                "message": f"Successfully cleared {count_before} documents",
                "documents_deleted": count_before,
                "timestamp": int(time.time() * 1000)
            }

        except Exception as e:
            self.logger.error(f"Failed to clear all documents: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": int(time.time() * 1000)
            }

    def switch_embedding_model(self, new_model_name: str) -> Dict[str, Any]:
        """Switch to a different embedding model"""
        try:
            self.logger.info(f"Switching embedding model from {self.config.EMBEDDING_MODEL} to {new_model_name}")

            # Validate model name
            if not EmbeddingModelConfig.is_valid_model(new_model_name):
                available = list(EmbeddingModelConfig.get_available_models().keys())
                return {
                    "status": "error",
                    "error": f"Invalid model name: {new_model_name}. Available: {available}",
                    "timestamp": int(time.time() * 1000)
                }

            # Check if we need to clear existing data (different dimensions)
            old_config = EmbeddingModelConfig.get_model_config(self.config.EMBEDDING_MODEL)
            new_config = EmbeddingModelConfig.get_model_config(new_model_name)

            dimension_changed = old_config.get('dimension') != new_config.get('dimension')

            if dimension_changed and self.collection.count() > 0:
                self.logger.warning(f"Model dimension changed ({old_config.get('dimension')} -> {new_config.get('dimension')}). Existing data will be cleared.")
                # Clear existing data since embeddings are incompatible
                self.clear_all_documents()

            # Update configuration
            self.config.EMBEDDING_MODEL = new_model_name
            self.config.EMBEDDING_DIMENSION = new_config['dimension']

            # Load new model
            self.embedding_model = embedding_factory.create_model(new_model_name)

            if not self.embedding_model:
                return {
                    "status": "error",
                    "error": f"Failed to load model: {new_model_name}",
                    "timestamp": int(time.time() * 1000)
                }

            self.logger.info(f"Successfully switched to model: {new_model_name}")

            return {
                "status": "success",
                "message": f"Successfully switched to model: {new_model_name}",
                "old_model": old_config.get('name', 'unknown'),
                "new_model": new_config.get('name'),
                "dimension_changed": dimension_changed,
                "data_cleared": dimension_changed and self.collection.count() == 0,
                "new_dimension": new_config['dimension'],
                "timestamp": int(time.time() * 1000)
            }

        except Exception as e:
            self.logger.error(f"Failed to switch embedding model: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": int(time.time() * 1000)
            }

    def get_model_info(self) -> Dict[str, Any]:
        """Get current model information and available models"""
        try:
            current_config = EmbeddingModelConfig.get_model_config(self.config.EMBEDDING_MODEL)
            available_models = EmbeddingModelConfig.get_available_models()

            return {
                "status": "success",
                "current_model": {
                    "name": self.config.EMBEDDING_MODEL,
                    "dimension": self.config.EMBEDDING_DIMENSION,
                    "config": current_config
                },
                "available_models": available_models,
                "document_count": self.collection.count() if self.collection else 0,
                "timestamp": int(time.time() * 1000)
            }

        except Exception as e:
            self.logger.error(f"Failed to get model info: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": int(time.time() * 1000)
            }

    def get_duplicate_stats(self) -> Dict[str, Any]:
        """Get statistics about duplicates in the database"""
        try:
            # Get all documents
            all_docs = self.collection.get()

            if not all_docs['documents']:
                return {
                    "status": "success",
                    "total_documents": 0,
                    "unique_documents": 0,
                    "duplicate_groups": 0,
                    "total_duplicates": 0
                }

            # Group by content hash
            hash_groups = {}
            for i, doc_id in enumerate(all_docs['ids']):
                metadata = all_docs['metadatas'][i] if all_docs['metadatas'] else {}
                content_hash = metadata.get('content_hash', 'no_hash')

                if content_hash not in hash_groups:
                    hash_groups[content_hash] = []
                hash_groups[content_hash].append(doc_id)

            # Calculate stats
            total_documents = len(all_docs['documents'])
            unique_documents = len(hash_groups)
            duplicate_groups = sum(1 for docs in hash_groups.values() if len(docs) > 1)
            total_duplicates = sum(len(docs) - 1 for docs in hash_groups.values() if len(docs) > 1)

            return {
                "status": "success",
                "total_documents": total_documents,
                "unique_documents": unique_documents,
                "duplicate_groups": duplicate_groups,
                "total_duplicates": total_duplicates,
                "storage_efficiency": f"{((unique_documents / total_documents) * 100):.1f}%" if total_documents > 0 else "100%",
                "timestamp": int(time.time() * 1000)
            }

        except Exception as e:
            self.logger.error(f"Failed to get duplicate stats: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": int(time.time() * 1000)
            }
