"""
Base Model Interface for LLM implementations
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional


class BaseLLMModel(ABC):
    """Abstract base class for LLM model implementations"""
    
    def __init__(self, config: Dict[str, Any], logger):
        self.config = config
        self.logger = logger
        self.model_loaded = False
        
    @abstractmethod
    def load_model(self) -> bool:
        """Load the model and return success status"""
        pass
        
    @abstractmethod
    def generate_response(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate response from prompt"""
        pass
        
    @abstractmethod
    def generate_with_context(self, query: str, context: str, **kwargs) -> Dict[str, Any]:
        """Generate response with context (for RAG)"""
        pass
        
    @abstractmethod
    def is_healthy(self) -> bool:
        """Check if model is loaded and healthy"""
        pass
        
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        pass

    def get_model_type(self) -> str:
        """Get model type (default implementation)"""
        return getattr(self, 'model_type', 'unknown')
        
    def cleanup(self):
        """Cleanup resources (optional override)"""
        pass
