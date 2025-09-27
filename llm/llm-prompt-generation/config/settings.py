"""
Configuration settings for the LLM Prompt Generation Service
"""
import os
from typing import Dict, Any


class Config:
    """Configuration class for LLM prompt generation service"""
    
    # Service Configuration
    SERVICE_NAME = "LLM Prompt Generation Service"
    SERVICE_VERSION = "1.0.0"
    SERVICE_DESCRIPTION = "LLM-powered prompt generation and response service for iChat RAG"
    
    # Server Configuration
    HOST = os.getenv('LLM_HOST', '0.0.0.0')
    PORT = int(os.getenv('LLM_PORT', 8087))
    DEBUG = os.getenv('LLM_DEBUG', 'false').lower() == 'true'
    
    # Environment
    ENVIRONMENT = os.getenv('LLM_ENV', 'development')
    
    # External Services
    RETRIEVER_SERVICE_URL = os.getenv('RETRIEVER_SERVICE_URL', 'http://localhost:8086')
    
    # Retriever Service Endpoints
    RETRIEVER_SEARCH_ENDPOINT = '/retrieve/search'
    RETRIEVER_RAG_ENDPOINT = '/retrieve/rag'
    RETRIEVER_CONTEXT_ENDPOINT = '/retrieve/context'
    RETRIEVER_HEALTH_ENDPOINT = '/health'
    
    # LLM Configuration
    MODEL_NAME = os.getenv('LLM_MODEL_NAME', 'google/flan-t5-base')
    MODEL_CACHE_DIR = os.getenv('MODEL_CACHE_DIR', '/app/cache')
    USE_GPU = os.getenv('LLM_USE_GPU', 'false').lower() == 'true'
    
    # Generation Parameters
    MAX_LENGTH = int(os.getenv('LLM_MAX_LENGTH', 512))
    MAX_NEW_TOKENS = int(os.getenv('LLM_MAX_NEW_TOKENS', 150))
    TEMPERATURE = float(os.getenv('LLM_TEMPERATURE', 0.7))
    TOP_P = float(os.getenv('LLM_TOP_P', 0.9))
    TOP_K = int(os.getenv('LLM_TOP_K', 50))
    DO_SAMPLE = os.getenv('LLM_DO_SAMPLE', 'true').lower() == 'true'
    
    # RAG Configuration
    MAX_CONTEXT_LENGTH = int(os.getenv('MAX_CONTEXT_LENGTH', 2000))
    MAX_CONTEXT_CHUNKS = int(os.getenv('MAX_CONTEXT_CHUNKS', 5))
    MIN_SIMILARITY_THRESHOLD = float(os.getenv('MIN_SIMILARITY_THRESHOLD', 0.2))
    
    # Prompt Templates
    SYSTEM_PROMPT = os.getenv('SYSTEM_PROMPT', 
        "You are a helpful AI assistant. Use the provided context to answer questions accurately and concisely.")
    
    RAG_PROMPT_TEMPLATE = """Answer the following question using the provided context. Be helpful, accurate, and concise.

Context: {context}

Question: {question}

Answer:"""

    FALLBACK_PROMPT_TEMPLATE = """Answer the following question. Be helpful, accurate, and concise.

Question: {question}

Answer:"""
    
    # Request Timeouts (seconds)
    RETRIEVER_TIMEOUT = int(os.getenv('RETRIEVER_TIMEOUT', 30))
    MODEL_LOAD_TIMEOUT = int(os.getenv('MODEL_LOAD_TIMEOUT', 120))
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FILE = os.getenv('LOG_FILE', '/app/logs/llm-service.log')
    
    # CORS Configuration
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')
    
    @classmethod
    def get_retriever_url(cls, endpoint: str) -> str:
        """Get full URL for retriever service endpoint"""
        return f"{cls.RETRIEVER_SERVICE_URL}{endpoint}"
    
    @classmethod
    def get_generation_params(cls, model_type: str = "causal") -> Dict[str, Any]:
        """Get generation parameters for the model"""
        base_params = {
            'max_length': cls.MAX_LENGTH,
            'max_new_tokens': cls.MAX_NEW_TOKENS,
            'temperature': cls.TEMPERATURE,
            'top_p': cls.TOP_P,
            'top_k': cls.TOP_K,
            'do_sample': cls.DO_SAMPLE,
        }

        # Add model-specific parameters
        if model_type == "causal":
            # For GPT-style models
            base_params.update({
                'pad_token_id': 50256,  # GPT-2 pad token
                'eos_token_id': 50256,  # GPT-2 end token
            })
        # For seq2seq models (T5, FLAN-T5), we don't need these specific tokens

        return base_params
    
    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'service_name': cls.SERVICE_NAME,
            'service_version': cls.SERVICE_VERSION,
            'service_description': cls.SERVICE_DESCRIPTION,
            'host': cls.HOST,
            'port': cls.PORT,
            'debug': cls.DEBUG,
            'environment': cls.ENVIRONMENT,
            'retriever_service_url': cls.RETRIEVER_SERVICE_URL,
            'model_name': cls.MODEL_NAME,
            'use_gpu': cls.USE_GPU,
            'max_length': cls.MAX_LENGTH,
            'max_new_tokens': cls.MAX_NEW_TOKENS,
            'temperature': cls.TEMPERATURE,
            'max_context_length': cls.MAX_CONTEXT_LENGTH,
            'max_context_chunks': cls.MAX_CONTEXT_CHUNKS,
            'log_level': cls.LOG_LEVEL
        }
