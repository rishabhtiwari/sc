"""
LLM Service for prompt generation and response generation
"""
import time
import requests
import torch
import os
import re
from typing import Dict, List, Any, Optional
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from config.settings import Config
from utils.logger import setup_logger
from models.model_factory import ModelFactory

try:
    from llama_cpp import Llama
    LLAMA_CPP_AVAILABLE = True
except ImportError:
    LLAMA_CPP_AVAILABLE = False
    print("⚠️ llama-cpp-python not available. Install with: pip install llama-cpp-python")

try:
    from huggingface_hub import hf_hub_download
    HF_HUB_AVAILABLE = True
except ImportError:
    HF_HUB_AVAILABLE = False
    print("⚠️ huggingface-hub not available. Install with: pip install huggingface-hub")


class LLMService:
    """Service for LLM-powered prompt generation and response generation"""

    def __init__(self):
        self.logger = setup_logger('llm-service')
        self.logger.info("Initializing LLM Service")

        # Service URLs
        self.retriever_service_url = Config.RETRIEVER_SERVICE_URL

        # Model components
        self.model_instance = None
        self.model_loaded = False

        self.logger.info(f"Retriever Service URL: {self.retriever_service_url}")
        self.logger.info(f"Model Key: {Config.MODEL_KEY}")
        self.logger.info(f"Use GPU: {Config.USE_GPU}")

        # Load model using factory
        self._load_model_via_factory()
    
    def _load_model_via_factory(self):
        """Load model using the model factory"""
        try:
            # Prepare configuration for model factory
            model_config = {
                'cache_dir': Config.MODEL_CACHE_DIR,
                'use_gpu': Config.USE_GPU,
                # Don't override model_name - let factory use its own configuration
                'model_file': Config.MODEL_FILE   # For GGUF models
            }

            # Create model instance using factory
            self.model_instance = ModelFactory.create_model(
                model_key=Config.MODEL_KEY,
                config=model_config,
                logger=self.logger
            )

            if self.model_instance is None:
                self.logger.error("Failed to create model instance")
                return

            # Load the model
            if self.model_instance.load_model():
                self.model_loaded = True
                self.logger.info("Model loaded successfully via factory")

                # Set model type for compatibility with legacy code
                self.model_type = self.model_instance.get_model_type()
                self.logger.info(f"Model type: {self.model_type}")

                # Log model info
                model_info = self.model_instance.get_model_info()
                self.logger.info(f"Model Info: {model_info}")
            else:
                self.logger.error("Failed to load model via factory")

        except Exception as e:
            self.logger.error(f"Error loading model via factory: {str(e)}")

    def _load_model(self):
        """Legacy method - kept for backward compatibility"""
        self.logger.warning("Using legacy model loading method. Consider using factory approach.")
        try:
            self.logger.info(f"Loading model: {Config.MODEL_NAME}")

            # Determine device
            device = "cuda" if Config.USE_GPU and torch.cuda.is_available() else "cpu"
            self.logger.info(f"Using device: {device}")
            
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
            
            # Detect if this is a code generation request
            is_code_request = self._is_code_generation_request(query)

            # Build prompt
            if context and context.strip():
                prompt = Config.RAG_PROMPT_TEMPLATE.format(
                    context=context[:Config.MAX_CONTEXT_LENGTH],
                    question=query
                )
                response_type = "rag"
            elif is_code_request:
                prompt = Config.CODE_GENERATION_PROMPT_TEMPLATE.format(question=query)
                response_type = "code_generation"
            else:
                prompt = Config.FALLBACK_PROMPT_TEMPLATE.format(question=query)
                response_type = "direct"
            
            self.logger.info(f"Using {response_type} response mode")
            
            # Initialize generation_params for return statement
            generation_params = {}

            # Generate response using appropriate method
            if hasattr(self, 'model_instance') and self.model_instance:
                # Use factory model instance
                if context and context.strip():
                    result = self.model_instance.generate_with_context(query, context)
                else:
                    result = self.model_instance.generate_response(prompt)

                if result.get('status') == 'success':
                    response_text = result.get('response', '').strip()
                    # Get generation params from the result if available
                    generation_params = result.get('generation_params', {})
                else:
                    response_text = "I apologize, but I couldn't generate a response at this time."
                    self.logger.error(f"Model generation failed: {result.get('error', 'Unknown error')}")
            else:
                # Fallback to legacy pipeline method
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

            # Post-process response for better formatting
            if is_code_request:
                response_text = self._format_code_response(response_text)

            # Get actual model name from model instance if available
            actual_model_name = Config.MODEL_NAME
            if hasattr(self, 'model_instance') and self.model_instance:
                model_info = self.model_instance.get_model_info()
                actual_model_name = model_info.get('model_name', Config.MODEL_NAME)

            return {
                "status": "success",
                "query": query,
                "response": response_text,
                "response_type": response_type,
                "context_used": bool(context and context.strip()),
                "context_length": len(context) if context else 0,
                "context_chunks": len(context_chunks),
                "model": actual_model_name,
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
            
            # Get actual model name from model instance if available
            actual_model_name = Config.MODEL_NAME
            if hasattr(self, 'model_instance') and self.model_instance:
                model_info = self.model_instance.get_model_info()
                actual_model_name = model_info.get('model_name', Config.MODEL_NAME)

            return {
                "status": "healthy" if overall_healthy else "degraded",
                "service_name": Config.SERVICE_NAME,
                "version": Config.SERVICE_VERSION,
                "model": actual_model_name,
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

    def _is_code_generation_request(self, query: str) -> bool:
        """
        Detect if the query is asking for code generation

        Args:
            query: User query

        Returns:
            True if this appears to be a code generation request
        """
        code_keywords = [
            'write', 'create', 'generate', 'build', 'implement', 'develop',
            'function', 'class', 'method', 'code', 'script', 'program',
            'algorithm', 'python', 'javascript', 'java', 'cpp', 'c++',
            'html', 'css', 'sql', 'bash', 'shell', 'php', 'ruby', 'go',
            'rust', 'typescript', 'swift', 'kotlin', 'scala', 'api',
            'endpoint', 'component', 'module', 'library', 'framework'
        ]

        query_lower = query.lower()
        return any(keyword in query_lower for keyword in code_keywords)

    def _format_code_response(self, response: str) -> str:
        """
        Format code response to ensure proper code block formatting

        Args:
            response: Raw response from LLM

        Returns:
            Formatted response with proper code blocks
        """

        # If response already has code blocks, return as is
        if '```' in response:
            return response

        # Try to detect code patterns and wrap them in code blocks
        lines = response.split('\n')
        formatted_lines = []
        in_code_block = False
        code_language = None

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Detect start of code block
            if not in_code_block and self._looks_like_code_start(stripped, lines[i:]):
                # Try to detect language
                code_language = self._detect_code_language(response)
                formatted_lines.append(f'```{code_language}')
                formatted_lines.append(line)
                in_code_block = True
            # Detect end of code block
            elif in_code_block and (not stripped or self._looks_like_explanation(stripped)):
                formatted_lines.append('```')
                formatted_lines.append(line)
                in_code_block = False
            else:
                formatted_lines.append(line)

        # Close any open code block
        if in_code_block:
            formatted_lines.append('```')

        return '\n'.join(formatted_lines)

    def _looks_like_code_start(self, line: str, remaining_lines: list) -> bool:
        """Check if a line looks like the start of a code block"""
        code_indicators = [
            'def ', 'class ', 'function ', 'var ', 'let ', 'const ',
            'import ', 'from ', 'if ', 'for ', 'while ', 'try:',
            '#!/', '<?php', '<html', '<script', 'SELECT ', 'CREATE ',
            'public class', 'private ', 'public ', 'protected '
        ]

        # Check if line starts with common code patterns
        if any(line.startswith(indicator) for indicator in code_indicators):
            return True

        # Check if line has code-like structure (assignments, function calls)
        if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*\s*[=\(]', line):
            return True

        # Check if multiple consecutive lines look like code
        code_like_count = 0
        for next_line in remaining_lines[:3]:
            if (next_line.strip() and
                (next_line.startswith('    ') or next_line.startswith('\t') or
                 any(indicator in next_line for indicator in code_indicators))):
                code_like_count += 1

        return code_like_count >= 2

    def _looks_like_explanation(self, line: str) -> bool:
        """Check if a line looks like explanation text rather than code"""
        explanation_indicators = [
            'this function', 'this class', 'this code', 'this script',
            'the above', 'explanation:', 'note:', 'example:', 'usage:',
            'you can', 'this will', 'this creates', 'this implements'
        ]

        return any(indicator in line.lower() for indicator in explanation_indicators)

    def _detect_code_language(self, response: str) -> str:
        """Detect the programming language from the response"""
        language_patterns = {
            'python': ['def ', 'import ', 'from ', 'print(', '__init__', 'self.'],
            'javascript': ['function ', 'var ', 'let ', 'const ', 'console.log', '=>'],
            'java': ['public class', 'private ', 'public static', 'System.out'],
            'cpp': ['#include', 'std::', 'cout', 'cin', 'int main'],
            'html': ['<html', '<div', '<script', '<style', '<!DOCTYPE'],
            'css': ['{', '}', 'color:', 'background:', 'margin:'],
            'sql': ['SELECT', 'FROM', 'WHERE', 'INSERT', 'UPDATE', 'CREATE'],
            'bash': ['#!/bin/bash', 'echo', 'grep', 'awk', 'sed'],
            'php': ['<?php', '$_', 'echo ', 'function '],
            'ruby': ['def ', 'end', 'puts ', 'require '],
            'go': ['package ', 'func ', 'import ', 'fmt.'],
            'rust': ['fn ', 'let ', 'mut ', 'println!'],
            'swift': ['func ', 'var ', 'let ', 'print('],
            'kotlin': ['fun ', 'val ', 'var ', 'println(']
        }

        response_lower = response.lower()

        for language, patterns in language_patterns.items():
            if any(pattern.lower() in response_lower for pattern in patterns):
                return language

        return ''  # Default to no language specification
