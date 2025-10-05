"""
Cross-encoder reranking service for improving document retrieval quality
"""
import logging
import time
from typing import List, Dict, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

try:
    from sentence_transformers import CrossEncoder
    RERANKING_AVAILABLE = True
except ImportError:
    RERANKING_AVAILABLE = False
    CrossEncoder = None

from config.settings import Config


class RerankerService:
    """Cross-encoder reranking service with thread pool support"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.model = None
        self.model_lock = threading.Lock()
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the cross-encoder model"""
        if not Config.ENABLE_RERANKING:
            self.logger.info("Reranking is disabled in configuration")
            return
            
        if not RERANKING_AVAILABLE:
            self.logger.error("sentence-transformers not available. Install with: pip install sentence-transformers")
            return
            
        try:
            self.logger.info(f"Loading reranker model: {Config.RERANKER_MODEL}")
            start_time = time.time()
            
            self.model = CrossEncoder(Config.RERANKER_MODEL)
            
            load_time = time.time() - start_time
            self.logger.info(f"Reranker model loaded successfully in {load_time:.2f}s")
            
        except Exception as e:
            self.logger.error(f"Failed to load reranker model: {str(e)}")
            self.model = None
    
    def is_available(self) -> bool:
        """Check if reranking is available"""
        return (Config.ENABLE_RERANKING and 
                RERANKING_AVAILABLE and 
                self.model is not None)
    
    def _batch_rerank(self, query_doc_pairs: List[Tuple[str, str]], batch_start: int) -> List[Tuple[int, float]]:
        """
        Rerank a batch of query-document pairs
        
        Args:
            query_doc_pairs: List of (query, document) tuples
            batch_start: Starting index for this batch
            
        Returns:
            List of (original_index, score) tuples
        """
        try:
            if not self.model:
                return [(batch_start + i, 0.0) for i in range(len(query_doc_pairs))]
            
            # Get scores for this batch
            with self.model_lock:
                scores = self.model.predict(query_doc_pairs)
            
            # Return (original_index, score) pairs
            return [(batch_start + i, float(score)) for i, score in enumerate(scores)]
            
        except Exception as e:
            self.logger.error(f"Error in batch reranking: {str(e)}")
            # Return zero scores for failed batch
            return [(batch_start + i, 0.0) for i in range(len(query_doc_pairs))]
    
    def rerank_documents(self, query: str, documents: List[Dict[str, Any]], 
                        top_k: int = None) -> List[Dict[str, Any]]:
        """
        Rerank documents using cross-encoder model with thread pool
        
        Args:
            query: Search query
            documents: List of document dictionaries with 'document' or 'text' field
            top_k: Number of top documents to return (default: all)
            
        Returns:
            List of reranked documents with added 'rerank_score' field
        """
        if not self.is_available():
            self.logger.warning("Reranking not available, returning original order")
            return documents[:top_k] if top_k else documents
        
        if not documents:
            return documents
        
        try:
            start_time = time.time()
            
            # Extract document texts
            doc_texts = []
            for doc in documents:
                # Try different possible text fields
                text = doc.get('document') or doc.get('text') or doc.get('content', '')
                if not text:
                    self.logger.warning(f"No text found in document: {doc.keys()}")
                    text = str(doc)  # Fallback to string representation
                doc_texts.append(text)
            
            # Create query-document pairs
            query_doc_pairs = [(query, text) for text in doc_texts]
            
            # Split into batches for parallel processing
            batch_size = Config.RERANKER_BATCH_SIZE
            batches = []
            for i in range(0, len(query_doc_pairs), batch_size):
                batch = query_doc_pairs[i:i + batch_size]
                batches.append((batch, i))
            
            self.logger.info(f"Reranking {len(documents)} documents in {len(batches)} batches "
                           f"(batch_size={batch_size}, workers={Config.RERANKER_MAX_WORKERS})")
            
            # Process batches in parallel
            all_scores = []
            with ThreadPoolExecutor(max_workers=Config.RERANKER_MAX_WORKERS) as executor:
                # Submit all batches
                future_to_batch = {
                    executor.submit(self._batch_rerank, batch, batch_start): (batch, batch_start)
                    for batch, batch_start in batches
                }
                
                # Collect results
                for future in as_completed(future_to_batch, timeout=Config.RERANKER_TIMEOUT):
                    try:
                        batch_results = future.result()
                        all_scores.extend(batch_results)
                    except Exception as e:
                        batch, batch_start = future_to_batch[future]
                        self.logger.error(f"Batch reranking failed for batch starting at {batch_start}: {str(e)}")
                        # Add zero scores for failed batch
                        all_scores.extend([(batch_start + i, 0.0) for i in range(len(batch))])
            
            # Sort scores by original index to maintain order
            all_scores.sort(key=lambda x: x[0])
            scores = [score for _, score in all_scores]
            
            # Add rerank scores to documents
            reranked_docs = []
            for i, (doc, score) in enumerate(zip(documents, scores)):
                doc_copy = doc.copy()
                doc_copy['rerank_score'] = score
                reranked_docs.append(doc_copy)
            
            # Sort by rerank score (highest first)
            reranked_docs.sort(key=lambda x: x.get('rerank_score', 0), reverse=True)
            
            # Return top_k if specified
            if top_k:
                reranked_docs = reranked_docs[:top_k]
            
            rerank_time = time.time() - start_time
            self.logger.info(f"Reranking completed in {rerank_time:.2f}s. "
                           f"Top score: {reranked_docs[0].get('rerank_score', 0):.4f}, "
                           f"Bottom score: {reranked_docs[-1].get('rerank_score', 0):.4f}")
            
            return reranked_docs
            
        except Exception as e:
            self.logger.error(f"Error in document reranking: {str(e)}")
            # Return original documents on error
            return documents[:top_k] if top_k else documents
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model"""
        return {
            'available': self.is_available(),
            'enabled': Config.ENABLE_RERANKING,
            'model_name': Config.RERANKER_MODEL,
            'batch_size': Config.RERANKER_BATCH_SIZE,
            'max_workers': Config.RERANKER_MAX_WORKERS,
            'timeout': Config.RERANKER_TIMEOUT,
            'sentence_transformers_available': RERANKING_AVAILABLE,
            'model_loaded': self.model is not None
        }
