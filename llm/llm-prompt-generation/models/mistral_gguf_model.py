"""
Mistral GGUF Model Implementation using llama-cpp-python
"""
import time
import os
from typing import Dict, List, Any, Optional
from .base_model import BaseLLMModel

try:
    from llama_cpp import Llama

    LLAMA_CPP_AVAILABLE = True
except ImportError:
    LLAMA_CPP_AVAILABLE = False

try:
    from huggingface_hub import hf_hub_download

    HF_HUB_AVAILABLE = True
except ImportError:
    HF_HUB_AVAILABLE = False


class MistralGGUFModel(BaseLLMModel):
    """Mistral GGUF model implementation using llama-cpp-python"""

    def __init__(self, config: Dict[str, Any], logger):
        super().__init__(config, logger)
        self.llm = None
        self.model_path = None
        self.model_type = "gguf"

    def load_model(self) -> bool:
        """Load Mistral GGUF model"""
        try:
            if not LLAMA_CPP_AVAILABLE:
                self.logger.error("llama-cpp-python not available. Install with: pip install llama-cpp-python")
                return False

            if not HF_HUB_AVAILABLE:
                self.logger.error("huggingface-hub not available. Install with: pip install huggingface-hub")
                return False

            model_name = self.config.get('model_name', 'TheBloke/Mistral-7B-Instruct-v0.2-GGUF')
            model_file = self.config.get('model_file', 'mistral-7b-instruct-v0.2.Q4_K_M.gguf')
            cache_dir = self.config.get('cache_dir', '/app/cache')

            self.logger.info(f"Loading Mistral GGUF model: {model_name}/{model_file}")

            # Download model if not exists
            try:
                self.model_path = hf_hub_download(
                    repo_id=model_name,
                    filename=model_file,
                    cache_dir=cache_dir,
                    local_files_only=False
                )
                self.logger.info(f"Model downloaded to: {self.model_path}")
            except Exception as e:
                self.logger.error(f"Failed to download model: {str(e)}")
                return False

            # Load model with llama-cpp
            self.logger.info("Initializing Llama model...")

            # Import Config to get context window settings
            from config.settings import Config

            # Determine GPU layers based on use_gpu config
            # -1 means offload all layers to GPU, 0 means CPU only
            n_gpu_layers = -1 if self.config.get('use_gpu', False) else 0

            self.logger.info(f"GPU layers: {n_gpu_layers} ({'GPU' if n_gpu_layers != 0 else 'CPU'} mode)")

            self.llm = Llama(
                model_path=self.model_path,
                n_ctx=Config.N_CTX,  # Use configurable context window (2048)
                n_batch=Config.N_BATCH,  # Use configurable batch size
                n_threads=4,  # CPU threads
                verbose=True,
                use_mmap=True,  # Memory mapping for efficiency
                use_mlock=False,  # Don't lock memory
                n_gpu_layers=n_gpu_layers  # Offload layers to GPU if available
            )

            self.model_loaded = True
            self.logger.info("Mistral GGUF model loaded successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to load Mistral GGUF model: {str(e)}")
            return False

    def generate_response(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate response from prompt"""
        try:
            if not self.model_loaded:
                return {"status": "error", "error": "Model not loaded"}

            # Generation parameters
            max_tokens = kwargs.get('max_tokens', 512)
            temperature = kwargs.get('temperature', 0.7)
            top_p = kwargs.get('top_p', 0.9)

            # Generate response
            response = self.llm(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                echo=False,  # Don't echo the prompt
                stop=["</s>", "[INST]", "[/INST]"]  # Stop tokens
            )

            if response and 'choices' in response and len(response['choices']) > 0:
                response_text = response['choices'][0]['text'].strip()

                return {
                    "status": "success",
                    "response": response_text,
                    "model": self.config.get('model_name'),
                    "usage": response.get('usage', {}),
                    "timestamp": int(time.time() * 1000)
                }
            else:
                return {"status": "error", "error": "No response generated"}

        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}")
            return {"status": "error", "error": str(e)}

    def generate_streaming_response(self, prompt: str, **kwargs):
        """Generate streaming response from prompt"""
        try:
            if not self.model_loaded:
                yield {"status": "error", "error": "Model not loaded"}
                return

            # Generation parameters
            max_tokens = kwargs.get('max_tokens', 512)
            temperature = kwargs.get('temperature', 0.7)
            top_p = kwargs.get('top_p', 0.9)

            # Generate response with streaming
            response_stream = self.llm(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                echo=False,  # Don't echo the prompt
                stop=["</s>", "[INST]", "[/INST]"],  # Stop tokens
                stream=True  # Enable streaming
            )

            # Stream tokens
            for chunk in response_stream:
                if 'choices' in chunk and len(chunk['choices']) > 0:
                    choice = chunk['choices'][0]
                    if 'text' in choice and choice['text']:
                        yield {
                            "status": "streaming",
                            "token": choice['text']
                        }

                    # Check if this is the final chunk
                    if choice.get('finish_reason') is not None:
                        finish_reason = choice.get('finish_reason')
                        self.logger.info(f"Model streaming complete with finish_reason: {finish_reason}")
                        yield {
                            "status": "complete",
                            "finish_reason": finish_reason
                        }
                        return

            # If we exit the loop without a finish_reason, still send complete
            self.logger.info("Model streaming complete without explicit finish_reason (assuming natural stop)")
            yield {
                "status": "complete",
                "finish_reason": "stop"  # Assume natural completion if no explicit reason
            }

        except Exception as e:
            self.logger.error(f"Error in streaming response: {str(e)}")
            yield {"status": "error", "error": str(e)}

    def generate_with_context(self, query: str, context: str, **kwargs) -> Dict[str, Any]:
        """Generate response with context (for RAG)"""
        try:
            # Create Mistral-style prompt with context
            prompt = f"""[INST] Based on the following context, please answer the question.

Context:
{context}

Question: {query}

Please provide a detailed and accurate answer based only on the information provided in the context. [/INST]"""

            return self.generate_response(prompt, **kwargs)

        except Exception as e:
            self.logger.error(f"Error generating response with context: {str(e)}")
            return {"status": "error", "error": str(e)}

    def is_healthy(self) -> bool:
        """Check if model is loaded and healthy"""
        return self.model_loaded and self.llm is not None

    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        return {
            "model_name": self.config.get('model_name'),
            "model_file": self.config.get('model_file'),
            "model_type": "mistral-gguf",
            "architecture": "causal-lm",
            "loaded": self.model_loaded,
            "model_path": self.model_path,
            "backend": "llama-cpp-python"
        }

    def cleanup(self):
        """Cleanup resources"""
        if self.llm:
            del self.llm
            self.llm = None
        self.model_loaded = False
