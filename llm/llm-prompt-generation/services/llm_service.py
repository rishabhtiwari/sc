"""
LLM Service for prompt generation and response generation
"""
import time
import requests
import torch
from typing import Dict, List, Any, Optional
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from config.settings import Config
from utils.logger import setup_logger


class LLMService:
    """Service for LLM-powered prompt generation and response generation"""
    
    def __init__(self):
        self.logger = setup_logger('llm-service')
        self.logger.info("Initializing LLM Service")
        
        # Service URLs
        self.retriever_service_url = Config.RETRIEVER_SERVICE_URL
        
        # Model components
        self.tokenizer = None
        self.model = None
        self.generator = None
        self.model_loaded = False
        
        self.logger.info(f"Retriever Service URL: {self.retriever_service_url}")
        self.logger.info(f"Model: {Config.MODEL_NAME}")
        self.logger.info(f"Use GPU: {Config.USE_GPU}")
        
        # Load model
        self._load_model()
    
    def _load_model(self):
        """Load the LLM model and tokenizer"""
        try:
            self.logger.info(f"Loading model: {Config.MODEL_NAME}")
            
            # Determine device
            device = "cuda" if Config.USE_GPU and torch.cuda.is_available() else "cpu"
            self.logger.info(f"Using device: {device}")
            
            # Load tokenizer
            self.logger.info("Loading tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                Config.MODEL_NAME,
                cache_dir=Config.MODEL_CACHE_DIR,
                trust_remote_code=True
            )
            
            # Add pad token if it doesn't exist
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Load model - try seq2seq first (T5, FLAN-T5), then causal LM (GPT, DialoGPT)
            self.logger.info("Loading model...")
            try:
                # Try loading as seq2seq model first (for T5, FLAN-T5, etc.)
                from transformers import AutoModelForSeq2SeqLM
                self.model = AutoModelForSeq2SeqLM.from_pretrained(
                    Config.MODEL_NAME,
                    cache_dir=Config.MODEL_CACHE_DIR,
                    torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                    device_map="auto" if device == "cuda" else None,
                    trust_remote_code=True
                )
                self.model_type = "seq2seq"
                pipeline_task = "text2text-generation"
                self.logger.info("Loaded as seq2seq model")
            except:
                # Fall back to causal LM (GPT, DialoGPT, etc.)
                self.model = AutoModelForCausalLM.from_pretrained(
                    Config.MODEL_NAME,
                    cache_dir=Config.MODEL_CACHE_DIR,
                    torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                    device_map="auto" if device == "cuda" else None,
                    trust_remote_code=True
                )
                self.model_type = "causal"
                pipeline_task = "text-generation"
                self.logger.info("Loaded as causal LM model")

            if device == "cpu":
                self.model = self.model.to(device)

            # Create appropriate pipeline based on model type
            pipeline_kwargs = {
                "model": self.model,
                "tokenizer": self.tokenizer,
                "device": 0 if device == "cuda" else -1,
            }

            # Only add return_full_text for causal models
            if self.model_type == "causal":
                pipeline_kwargs["return_full_text"] = False

            self.generator = pipeline(pipeline_task, **pipeline_kwargs)
            
            self.model_loaded = True
            self.logger.info("Model loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to load model: {str(e)}")
            self.model_loaded = False
            raise e
    
    def generate_response(self, query: str, use_rag: bool = True, 
                         context: str = None) -> Dict[str, Any]:
        """
        Generate response using LLM with optional RAG context
        
        Args:
            query: User query
            use_rag: Whether to use RAG (retrieve context)
            context: Pre-provided context (optional)
            
        Returns:
            Dictionary containing generated response
        """
        try:
            if not self.model_loaded:
                raise Exception("Model not loaded")
            
            self.logger.info(f"Generating response for query: '{query[:50]}...'")
            
            # Get context if RAG is enabled and no context provided
            if use_rag and context is None:
                context_result = self._get_rag_context(query)
                context = context_result.get("context", "")
                context_chunks = context_result.get("chunks", [])
            else:
                context_chunks = []
            
            # Build prompt
            if context and context.strip():
                prompt = Config.RAG_PROMPT_TEMPLATE.format(
                    context=context[:Config.MAX_CONTEXT_LENGTH],
                    question=query
                )
                response_type = "rag"
            else:
                prompt = Config.FALLBACK_PROMPT_TEMPLATE.format(question=query)
                response_type = "direct"
            
            self.logger.info(f"Using {response_type} response mode")
            
            # Generate response
            generation_params = Config.get_generation_params(self.model_type)
            
            # Generate text
            generated = self.generator(
                prompt,
                **generation_params
            )
            
            # Extract generated text based on model type
            if generated and len(generated) > 0:
                if self.model_type == "seq2seq":
                    # For seq2seq models (T5, FLAN-T5), the response is the full generated text
                    response_text = generated[0]['generated_text'].strip()
                else:
                    # For causal LM models (GPT, DialoGPT), remove the prompt
                    response_text = generated[0]['generated_text'].strip()
                    # Clean up response (remove prompt if it's included)
                    if prompt in response_text:
                        response_text = response_text.replace(prompt, "").strip()
            else:
                response_text = "I apologize, but I couldn't generate a response at this time."
            
            self.logger.info(f"Generated response ({len(response_text)} chars)")
            
            return {
                "status": "success",
                "query": query,
                "response": response_text,
                "response_type": response_type,
                "context_used": bool(context and context.strip()),
                "context_length": len(context) if context else 0,
                "context_chunks": len(context_chunks),
                "model": Config.MODEL_NAME,
                "generation_params": generation_params,
                "timestamp": int(time.time() * 1000)
            }
            
        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}")
            raise e
    
    def _get_rag_context(self, query: str) -> Dict[str, Any]:
        """
        Get RAG context from retriever service
        
        Args:
            query: User query
            
        Returns:
            Dictionary containing context and chunks
        """
        try:
            self.logger.info(f"Retrieving RAG context for: '{query[:50]}...'")
            
            # Call retriever service
            rag_url = Config.get_retriever_url(Config.RETRIEVER_RAG_ENDPOINT)
            
            payload = {
                "query": query,
                "max_chunks": Config.MAX_CONTEXT_CHUNKS
            }
            
            response = requests.post(
                rag_url,
                json=payload,
                timeout=Config.RETRIEVER_TIMEOUT,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code != 200:
                self.logger.warning(f"Retriever service returned status {response.status_code}")
                return {"context": "", "chunks": []}
            
            rag_result = response.json()
            
            context = rag_result.get("context", "")
            chunks = rag_result.get("chunks", [])
            
            self.logger.info(f"Retrieved context: {len(context)} chars, {len(chunks)} chunks")
            
            return {
                "context": context,
                "chunks": chunks,
                "total_chunks": len(chunks)
            }
            
        except Exception as e:
            self.logger.error(f"Error retrieving RAG context: {str(e)}")
            return {"context": "", "chunks": []}
    
    def search_documents(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """
        Search documents using retriever service
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            Dictionary containing search results
        """
        try:
            self.logger.info(f"Searching documents for: '{query[:50]}...'")
            
            # Call retriever service
            search_url = Config.get_retriever_url(Config.RETRIEVER_SEARCH_ENDPOINT)
            
            payload = {
                "query": query,
                "limit": limit,
                "min_similarity": Config.MIN_SIMILARITY_THRESHOLD
            }
            
            response = requests.post(
                search_url,
                json=payload,
                timeout=Config.RETRIEVER_TIMEOUT,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code != 200:
                raise Exception(f"Retriever service returned status {response.status_code}: {response.text}")
            
            search_result = response.json()
            
            self.logger.info(f"Found {search_result.get('total_results', 0)} documents")
            
            return search_result
            
        except Exception as e:
            self.logger.error(f"Error searching documents: {str(e)}")
            raise e
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on LLM service and dependencies
        
        Returns:
            Dictionary containing health status
        """
        try:
            health_status = {
                "service": "healthy" if self.model_loaded else "unhealthy",
                "model_loaded": self.model_loaded,
                "retriever_service": "unknown"
            }
            
            # Check retriever service
            try:
                retriever_health_url = Config.get_retriever_url(Config.RETRIEVER_HEALTH_ENDPOINT)
                response = requests.get(retriever_health_url, timeout=5)
                health_status["retriever_service"] = "healthy" if response.status_code == 200 else "unhealthy"
            except Exception:
                health_status["retriever_service"] = "unhealthy"
            
            overall_healthy = (health_status["service"] == "healthy" and 
                             health_status["retriever_service"] == "healthy")
            
            return {
                "status": "healthy" if overall_healthy else "degraded",
                "service_name": Config.SERVICE_NAME,
                "version": Config.SERVICE_VERSION,
                "model": Config.MODEL_NAME,
                "model_loaded": self.model_loaded,
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
