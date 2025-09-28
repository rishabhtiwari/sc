"""
Embedding Model Factory - Factory pattern for different embedding models
"""

import logging
from typing import Dict, Any, Optional
from sentence_transformers import SentenceTransformer
from abc import ABC, abstractmethod


class EmbeddingModelConfig:
    """Configuration for embedding models"""
    
    # Model configurations
    MODELS = {
        'all-MiniLM-L6-v2': {
            'name': 'all-MiniLM-L6-v2',
            'dimension': 384,
            'description': 'Lightweight, fast model good for general purpose',
            'max_seq_length': 256,
            'performance': 'fast',
            'quality': 'good'
        },
        'BAAI/bge-base-en-v1.5': {
            'name': 'BAAI/bge-base-en-v1.5',
            'dimension': 768,
            'description': 'High-quality BGE model, better semantic understanding',
            'max_seq_length': 512,
            'performance': 'medium',
            'quality': 'excellent'
        },
        'BAAI/bge-small-en-v1.5': {
            'name': 'BAAI/bge-small-en-v1.5',
            'dimension': 384,
            'description': 'Smaller BGE model, good balance of speed and quality',
            'max_seq_length': 512,
            'performance': 'fast',
            'quality': 'very good'
        }
    }
    
    @classmethod
    def get_model_config(cls, model_name: str) -> Dict[str, Any]:
        """Get configuration for a specific model"""
        return cls.MODELS.get(model_name, {})
    
    @classmethod
    def get_available_models(cls) -> Dict[str, Dict[str, Any]]:
        """Get all available models"""
        return cls.MODELS.copy()
    
    @classmethod
    def is_valid_model(cls, model_name: str) -> bool:
        """Check if model name is valid"""
        return model_name in cls.MODELS


class BaseEmbeddingModel(ABC):
    """Abstract base class for embedding models"""
    
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.config = EmbeddingModelConfig.get_model_config(model_name)
        self.logger = logging.getLogger('embedding-factory')
        self.model = None
        
    @abstractmethod
    def load_model(self) -> bool:
        """Load the embedding model"""
        pass
    
    @abstractmethod
    def encode(self, texts, **kwargs):
        """Encode texts to embeddings"""
        pass
    
    @property
    def dimension(self) -> int:
        """Get embedding dimension"""
        return self.config.get('dimension', 384)
    
    @property
    def max_seq_length(self) -> int:
        """Get maximum sequence length"""
        return self.config.get('max_seq_length', 256)


class SentenceTransformerModel(BaseEmbeddingModel):
    """Sentence Transformer based embedding model"""
    
    def load_model(self) -> bool:
        """Load the sentence transformer model"""
        try:
            self.logger.info(f"Loading SentenceTransformer model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            self.logger.info(f"Successfully loaded model: {self.model_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load model {self.model_name}: {str(e)}")
            return False
    
    def encode(self, texts, **kwargs):
        """Encode texts using sentence transformer"""
        if not self.model:
            raise RuntimeError(f"Model {self.model_name} not loaded")
        
        # Default parameters for encoding
        default_params = {
            'convert_to_tensor': False,
            'normalize_embeddings': True,
            'show_progress_bar': False
        }
        
        # Merge with provided kwargs
        params = {**default_params, **kwargs}
        
        return self.model.encode(texts, **params)


class EmbeddingModelFactory:
    """Factory for creating embedding models"""
    
    def __init__(self):
        self.logger = logging.getLogger('embedding-factory')
        self._loaded_models = {}  # Cache for loaded models
    
    def create_model(self, model_name: str, use_cache: bool = True) -> Optional[BaseEmbeddingModel]:
        """Create an embedding model instance"""
        
        # Check if model name is valid
        if not EmbeddingModelConfig.is_valid_model(model_name):
            self.logger.error(f"Invalid model name: {model_name}")
            available = list(EmbeddingModelConfig.get_available_models().keys())
            self.logger.error(f"Available models: {available}")
            return None
        
        # Return cached model if available and caching is enabled
        if use_cache and model_name in self._loaded_models:
            self.logger.info(f"Using cached model: {model_name}")
            return self._loaded_models[model_name]
        
        # Create new model instance
        try:
            self.logger.info(f"Creating new model instance: {model_name}")
            
            # All current models use SentenceTransformer
            model = SentenceTransformerModel(model_name)
            
            # Load the model
            if not model.load_model():
                self.logger.error(f"Failed to load model: {model_name}")
                return None
            
            # Cache the model if caching is enabled
            if use_cache:
                self._loaded_models[model_name] = model
                self.logger.info(f"Cached model: {model_name}")
            
            return model
            
        except Exception as e:
            self.logger.error(f"Failed to create model {model_name}: {str(e)}")
            return None
    
    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """Get information about a model"""
        return EmbeddingModelConfig.get_model_config(model_name)
    
    def list_available_models(self) -> Dict[str, Dict[str, Any]]:
        """List all available models"""
        return EmbeddingModelConfig.get_available_models()
    
    def clear_cache(self):
        """Clear the model cache"""
        self.logger.info("Clearing model cache")
        self._loaded_models.clear()
    
    def get_loaded_models(self) -> list:
        """Get list of currently loaded models"""
        return list(self._loaded_models.keys())


# Global factory instance
embedding_factory = EmbeddingModelFactory()
