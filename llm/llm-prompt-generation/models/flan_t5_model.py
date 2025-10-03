"""
FLAN-T5 Model Implementation
"""
import time
import torch
from typing import Dict, List, Any, Optional
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
from .base_model import BaseLLMModel


class FlanT5Model(BaseLLMModel):
    """FLAN-T5 model implementation"""
    
    def __init__(self, config: Dict[str, Any], logger):
        super().__init__(config, logger)
        self.tokenizer = None
        self.model = None
        self.generator = None
        self.model_type = "seq2seq"
        
    def load_model(self) -> bool:
        """Load FLAN-T5 model"""
        try:
            model_name = self.config.get('model_name', 'google/flan-t5-base')
            cache_dir = self.config.get('cache_dir', '/app/cache')
            use_gpu = self.config.get('use_gpu', False)
            
            self.logger.info(f"Loading FLAN-T5 model: {model_name}")
            
            # Determine device
            device = "cuda" if use_gpu and torch.cuda.is_available() else "cpu"
            self.logger.info(f"Using device: {device}")
            
            # Load tokenizer
            self.logger.info("Loading tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                cache_dir=cache_dir,
                trust_remote_code=True
            )
            
            # Add pad token if it doesn't exist
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Load model
            self.logger.info("Loading model...")
            self.model = AutoModelForSeq2SeqLM.from_pretrained(
                model_name,
                cache_dir=cache_dir,
                torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                device_map="auto" if device == "cuda" else None,
                trust_remote_code=True
            )
            
            # Create pipeline
            self.generator = pipeline(
                "text2text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if device == "cuda" else -1,
                torch_dtype=torch.float16 if device == "cuda" else torch.float32
            )
            
            self.model_loaded = True
            self.logger.info("FLAN-T5 model loaded successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load FLAN-T5 model: {str(e)}")
            return False
    
    def generate_response(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate response from prompt"""
        try:
            if not self.model_loaded:
                return {"status": "error", "error": "Model not loaded"}
            
            # Generation parameters
            max_length = kwargs.get('max_length', 512)
            temperature = kwargs.get('temperature', 0.7)
            do_sample = kwargs.get('do_sample', True)
            
            # Generate response
            generated = self.generator(
                prompt,
                max_length=max_length,
                temperature=temperature,
                do_sample=do_sample,
                pad_token_id=self.tokenizer.pad_token_id,
                num_return_sequences=1
            )
            
            if generated and len(generated) > 0:
                response_text = generated[0]['generated_text'].strip()
                
                return {
                    "status": "success",
                    "response": response_text,
                    "model": self.config.get('model_name'),
                    "timestamp": int(time.time() * 1000)
                }
            else:
                return {"status": "error", "error": "No response generated"}
                
        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    def generate_with_context(self, query: str, context: str, **kwargs) -> Dict[str, Any]:
        """Generate response with context (for RAG)"""
        try:
            # Create context-aware prompt for FLAN-T5
            prompt = f"Context: {context}\n\nQuestion: {query}\n\nAnswer:"
            
            return self.generate_response(prompt, **kwargs)
            
        except Exception as e:
            self.logger.error(f"Error generating response with context: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    def is_healthy(self) -> bool:
        """Check if model is loaded and healthy"""
        return self.model_loaded and self.model is not None
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        return {
            "model_name": self.config.get('model_name'),
            "model_type": "flan-t5",
            "architecture": "seq2seq",
            "loaded": self.model_loaded,
            "device": "cuda" if torch.cuda.is_available() and self.config.get('use_gpu') else "cpu"
        }
