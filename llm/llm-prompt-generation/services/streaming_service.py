"""
Streaming Service for multi-pass chunked responses
"""
import time
import asyncio
import json
from typing import Dict, List, Any, Generator, AsyncGenerator
from config.settings import Config
from utils.logger import setup_logger


class StreamingService:
    """Service for handling streaming responses with chunking"""

    def __init__(self, llm_service):
        self.logger = setup_logger('streaming-service')
        self.llm_service = llm_service
        self.logger.info("Streaming Service initialized")

    def should_use_streaming(self, query: str, context: str = None) -> bool:
        """
        Determine if streaming should be used.
        With larger context window (2048), we can handle most queries without chunking.
        """
        return Config.ENABLE_STREAMING

    def _truncate_context(self, context: str, query: str) -> str:
        """
        Truncate context to fit within the context window limits.

        Args:
            context: RAG context to truncate
            query: User query

        Returns:
            Truncated context that fits within token limits
        """
        if not context:
            return context

        # Estimate token usage:
        # - N_CTX = 2048 tokens total
        # - Query tokens (~50-200 tokens depending on length)
        # - Prompt template tokens (~100-200 tokens)
        # - Response generation space (~300-500 tokens)
        # Available for context: ~1200-1600 tokens

        # Conservative estimate: 1 token ≈ 0.75 words ≈ 4 characters
        # So 1200 tokens ≈ 900 words ≈ 4800 characters
        max_context_chars = 4800

        # Estimate query tokens (rough approximation)
        query_chars = len(query)
        if query_chars > 800:  # Very long query
            max_context_chars = 3200  # Reduce context space
        elif query_chars > 400:  # Medium query
            max_context_chars = 4000

        if len(context) <= max_context_chars:
            return context

        # Truncate context while trying to preserve sentence boundaries
        truncated = context[:max_context_chars]

        # Try to end at a sentence boundary
        last_period = truncated.rfind('. ')
        if last_period > max_context_chars * 0.8:  # If we can keep 80% and end at sentence
            truncated = truncated[:last_period + 1]

        self.logger.info(f"Truncated context from {len(context)} to {len(truncated)} characters to fit within token limits")
        return truncated

    def generate_streaming_response(self, query: str, context: str = None) -> Generator[Dict[str, Any], None, None]:
        """
        Generate streaming response using native token streaming

        Args:
            query: User query
            context: Optional context for RAG

        Yields:
            Dictionary containing streaming response tokens
        """
        try:
            self.logger.info(f"Starting native streaming response for query: '{query[:50]}...'")

            # Get RAG context if not provided
            if context is None:
                context_result = self.llm_service._get_rag_context(query)
                context = context_result.get("context", "")

            # Truncate context if it's too large for the context window
            if context and context.strip():
                context = self._truncate_context(context, query)

            # Send initial metadata
            yield {
                "type": "metadata",
                "query": query,
                "has_context": bool(context and context.strip()),
                "context_length": len(context) if context else 0,
                "timestamp": int(time.time() * 1000)
            }

            # Stream response directly from LLM model
            model_instance = self.llm_service.get_model_instance()

            if context and context.strip():
                # Use RAG context with streaming
                if hasattr(model_instance, 'generate_streaming_with_context'):
                    yield from self._stream_tokens_with_context(model_instance, query, context)
                else:
                    # Fallback to non-streaming with context
                    response = self.llm_service.generate_response(query, use_rag=False, context=context)
                    if response.get("status") == "success":
                        yield from self._stream_text_as_tokens(response.get("response", ""))
                    else:
                        yield {
                            "type": "error",
                            "error": response.get("error", "Failed to generate response"),
                            "timestamp": int(time.time() * 1000)
                        }
            else:
                # Direct response without context
                if hasattr(model_instance, 'generate_streaming_response'):
                    yield from self._stream_tokens_direct(model_instance, query)
                else:
                    # Fallback to non-streaming
                    response = self.llm_service.generate_response(query, use_rag=False)
                    if response.get("status") == "success":
                        yield from self._stream_text_as_tokens(response.get("response", ""))
                    else:
                        yield {
                            "type": "error",
                            "error": response.get("error", "Failed to generate response"),
                            "timestamp": int(time.time() * 1000)
                        }

            # Send completion metadata
            yield {
                "type": "complete",
                "timestamp": int(time.time() * 1000)
            }

        except Exception as e:
            self.logger.error(f"Error in streaming response: {str(e)}")
            yield {
                "type": "error",
                "error": str(e),
                "timestamp": int(time.time() * 1000)
            }

    def _stream_tokens_with_context(self, model_instance, query: str, context: str) -> Generator[Dict[str, Any], None, None]:
        """Stream tokens from model with RAG context"""
        try:
            for token_data in model_instance.generate_streaming_with_context(query, context):
                if token_data.get("status") == "streaming":
                    token_text = token_data.get("token", "")
                    if token_text:
                        yield {
                            "type": "token",
                            "content": token_text,
                            "timestamp": int(time.time() * 1000)
                        }
                        # Native streaming delay
                        if Config.ENABLE_STREAMING:
                            time.sleep(Config.STREAM_DELAY_MS / 1000.0)

                elif token_data.get("status") == "complete":
                    break
                elif token_data.get("status") == "error":
                    yield {
                        "type": "error",
                        "error": token_data.get("error", "Unknown error"),
                        "timestamp": int(time.time() * 1000)
                    }
                    break
        except Exception as e:
            yield {
                "type": "error",
                "error": str(e),
                "timestamp": int(time.time() * 1000)
            }

    def _stream_tokens_direct(self, model_instance, query: str) -> Generator[Dict[str, Any], None, None]:
        """Stream tokens from model without context"""
        try:
            for token_data in model_instance.generate_streaming_response(query):
                if token_data.get("status") == "streaming":
                    token_text = token_data.get("token", "")
                    if token_text:
                        yield {
                            "type": "token",
                            "content": token_text,
                            "timestamp": int(time.time() * 1000)
                        }
                        # Native streaming delay
                        if Config.ENABLE_STREAMING:
                            time.sleep(Config.STREAM_DELAY_MS / 1000.0)

                elif token_data.get("status") == "complete":
                    break
                elif token_data.get("status") == "error":
                    yield {
                        "type": "error",
                        "error": token_data.get("error", "Unknown error"),
                        "timestamp": int(time.time() * 1000)
                    }
                    break
        except Exception as e:
            yield {
                "type": "error",
                "error": str(e),
                "timestamp": int(time.time() * 1000)
            }

    def _stream_text_as_tokens(self, text: str) -> Generator[Dict[str, Any], None, None]:
        """Stream text as individual tokens for fallback"""
        if not text:
            return

        # Split into characters for token-like streaming
        for char in text:
            yield {
                "type": "token",
                "content": char,
                "timestamp": int(time.time() * 1000)
            }
            # Delay for typing effect
            if Config.ENABLE_STREAMING:
                time.sleep(Config.STREAM_DELAY_MS / 1000.0)

    def _generate_direct_streaming_response(self, query: str) -> Generator[Dict[str, Any], None, None]:
        """Generate streaming response without RAG context"""
        try:
            # Send metadata
            yield {
                "type": "metadata",
                "total_chunks": 1,
                "query": query,
                "response_type": "direct",
                "timestamp": int(time.time() * 1000)
            }

            # Stream response directly from LLM model
            model_instance = self.llm_service.get_model_instance()
            if hasattr(model_instance, 'generate_streaming_response'):
                # Use streaming generation
                accumulated_text = ""
                word_index = 0

                for token_data in model_instance.generate_streaming_response(query):
                    if token_data.get("status") == "streaming":
                        token_text = token_data.get("token", "")
                        accumulated_text += token_text

                        # Check if we have complete words to stream
                        words = accumulated_text.split()
                        if len(words) > word_index:
                            # Stream new complete words
                            for i in range(word_index, len(words)):
                                word = words[i]
                                word_with_space = word if i == 0 else " " + word

                                yield {
                                    "type": "text",
                                    "content": word_with_space,
                                    "chunk_index": 0,
                                    "total_chunks": 1,
                                    "word_index": i,
                                    "total_words": len(words),
                                    "timestamp": int(time.time() * 1000)
                                }

                                # Delay for typing effect
                                if Config.ENABLE_STREAMING:
                                    time.sleep(Config.STREAM_DELAY_MS / 1000.0)

                            word_index = len(words)

                    elif token_data.get("status") == "complete":
                        # Handle any remaining partial text
                        if accumulated_text and not accumulated_text.endswith(' '):
                            remaining_text = accumulated_text[len(' '.join(accumulated_text.split()[:word_index])):]
                            if remaining_text.strip():
                                yield {
                                    "type": "text",
                                    "content": remaining_text,
                                    "chunk_index": 0,
                                    "total_chunks": 1,
                                    "word_index": word_index,
                                    "total_words": word_index + 1,
                                    "timestamp": int(time.time() * 1000)
                                }
                        break

                    elif token_data.get("status") == "error":
                        yield {
                            "type": "error",
                            "error": token_data.get("error", "Unknown error"),
                            "timestamp": int(time.time() * 1000)
                        }
                        return
            else:
                # Fallback to non-streaming method
                response = self.llm_service.generate_response(query, use_rag=False)

                if response.get("status") == "success":
                    response_text = response.get("response", "")
                    yield from self._stream_text(response_text, 0, 1)
                else:
                    yield {
                        "type": "error",
                        "error": response.get("error", "Failed to generate response"),
                        "timestamp": int(time.time() * 1000)
                    }
                    return

            # Send completion
            yield {
                "type": "complete",
                "total_chunks": 1,
                "timestamp": int(time.time() * 1000)
            }

        except Exception as e:
            self.logger.error(f"Error in direct streaming response: {str(e)}")
            yield {
                "type": "error",
                "error": str(e),
                "timestamp": int(time.time() * 1000)
            }

    def _stream_text(self, text: str, chunk_index: int, total_chunks: int) -> Generator[Dict[str, Any], None, None]:
        """
        Stream text with typing effect
        
        Args:
            text: Text to stream
            chunk_index: Current chunk index
            total_chunks: Total number of chunks
            
        Yields:
            Dictionary containing text chunks for streaming
        """
        if not text:
            return
            
        # Split text into words for better streaming effect
        words = text.split()
        
        for i, word in enumerate(words):
            # Add space except for first word
            word_with_space = word if i == 0 else " " + word
            
            yield {
                "type": "text",
                "content": word_with_space,
                "chunk_index": chunk_index,
                "total_chunks": total_chunks,
                "word_index": i,
                "total_words": len(words),
                "timestamp": int(time.time() * 1000)
            }
            
            # Delay for typing effect
            if Config.ENABLE_STREAMING:
                time.sleep(Config.STREAM_DELAY_MS / 1000.0)

    async def generate_async_streaming_response(self, query: str, context: str = None) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Async version of streaming response generation
        
        Args:
            query: User query
            context: Optional context for RAG
            
        Yields:
            Dictionary containing streaming response chunks
        """
        try:
            # Convert sync generator to async
            for chunk in self.generate_streaming_response(query, context):
                yield chunk
                # Allow other coroutines to run
                await asyncio.sleep(0)
                
        except Exception as e:
            self.logger.error(f"Error in async streaming response: {str(e)}")
            yield {
                "type": "error",
                "error": str(e),
                "timestamp": int(time.time() * 1000)
            }
