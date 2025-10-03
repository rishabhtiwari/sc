"""
Model Factory for creating different LLM model instances
"""
from typing import Dict, Any, Optional
from .base_model import BaseLLMModel
from .flan_t5_model import FlanT5Model
from .mistral_gguf_model import MistralGGUFModel


class ModelFactory:
    """Factory class for creating LLM model instances"""
    
    # Registry of available models
    MODEL_REGISTRY = {
        'flan-t5': FlanT5Model,
        'mistral-gguf': MistralGGUFModel,
    }
    
    # Model configurations - these can be selected via LLM_MODEL_KEY environment variable
    MODEL_CONFIGS = {
        'flan-t5-base': {
            'model_type': 'flan-t5',
            'model_name': 'google/flan-t5-base',
            'description': 'FLAN-T5 Base (250M params) - Good balance of performance and speed',
            'memory_requirement': '2-3GB'
        },
        'flan-t5-small': {
            'model_type': 'flan-t5',
            'model_name': 'google/flan-t5-small',
            'description': 'FLAN-T5 Small (80M params) - Fastest, lower quality',
            'memory_requirement': '1-2GB'
        },
        'flan-t5-large': {
            'model_type': 'flan-t5',
            'model_name': 'google/flan-t5-large',
            'description': 'FLAN-T5 Large (780M params) - High quality, resource intensive',
            'memory_requirement': '8-12GB'
        },
        'mistral-7b-q4': {
            'model_type': 'mistral-gguf',
            'model_name': 'TheBloke/Mistral-7B-Instruct-v0.2-GGUF',
            'model_file': 'mistral-7b-instruct-v0.2.Q4_K_M.gguf',
            'description': 'Mistral 7B Q4 Quantized - Excellent quality, moderate resource usage',
            'memory_requirement': '4-6GB'
        },
        'mistral-7b-q5': {
            'model_type': 'mistral-gguf',
            'model_name': 'TheBloke/Mistral-7B-Instruct-v0.2-GGUF',
            'model_file': 'mistral-7b-instruct-v0.2.Q5_K_M.gguf',
            'description': 'Mistral 7B Q5 Quantized - Higher quality, more resource usage',
            'memory_requirement': '5-7GB'
        },
        'mistral-7b-q2': {
            'model_type': 'mistral-gguf',
            'model_name': 'TheBloke/Mistral-7B-Instruct-v0.2-GGUF',
            'model_file': 'mistral-7b-instruct-v0.2.Q2_K.gguf',
            'description': 'Mistral 7B Q2 Quantized - Lower quality, minimal resource usage',
            'memory_requirement': '2-3GB'
        }
    }
    
    @classmethod
    def create_model(cls, model_key: str, config: Dict[str, Any], logger) -> Optional[BaseLLMModel]:
        """
        Create a model instance based on model key
        
        Args:
            model_key: Key identifying the model configuration
            config: Additional configuration parameters
            logger: Logger instance
            
        Returns:
            BaseLLMModel instance or None if model not found
        """
        try:
            if model_key not in cls.MODEL_CONFIGS:
                logger.error(f"Unknown model key: {model_key}")
                logger.info(f"Available models: {list(cls.MODEL_CONFIGS.keys())}")
                return None
            
            model_config = cls.MODEL_CONFIGS[model_key].copy()
            model_type = model_config.pop('model_type')
            
            # Merge with provided config
            final_config = {**model_config, **config}
            
            if model_type not in cls.MODEL_REGISTRY:
                logger.error(f"Unknown model type: {model_type}")
                return None
            
            model_class = cls.MODEL_REGISTRY[model_type]
            logger.info(f"Creating {model_type} model: {model_key}")
            
            return model_class(final_config, logger)
            
        except Exception as e:
            logger.error(f"Failed to create model {model_key}: {str(e)}")
            return None
    
    @classmethod
    def get_available_models(cls) -> Dict[str, Dict[str, Any]]:
        """Get list of available models with their configurations"""
        return cls.MODEL_CONFIGS.copy()
    
    @classmethod
    def get_model_info(cls, model_key: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific model"""
        return cls.MODEL_CONFIGS.get(model_key)
    
    @classmethod
    def register_model(cls, model_key: str, model_config: Dict[str, Any]):
        """Register a new model configuration"""
        cls.MODEL_CONFIGS[model_key] = model_config
    
    @classmethod
    def register_model_type(cls, model_type: str, model_class):
        """Register a new model type implementation"""
        cls.MODEL_REGISTRY[model_type] = model_class
