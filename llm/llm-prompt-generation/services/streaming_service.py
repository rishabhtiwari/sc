"""
Streaming Service for multi-pass chunked responses with buffered background generation
"""
import time
import asyncio
import json
import threading
import queue
from typing import Dict, List, Any, Generator, AsyncGenerator
from config.settings import Config
from utils.logger import setup_logger


class StreamingService:
    """Service for handling streaming responses with chunking"""

    def __init__(self, llm_service):
        self.logger = setup_logger('streaming-service')
        self.llm_service = llm_service

        # Producer-Consumer components for seamless streaming
        self.token_buffer = queue.Queue()
        self.generation_complete = threading.Event()
        self.continuation_ready = threading.Event()

        self.logger.info("Streaming Service initialized with producer-consumer pattern")

    def _token_producer(self, query: str, context: str = None):
        """
        Producer: Independently generates all tokens across multiple passes.
        Doesn't rely on consumer - just keeps generating until LLM says complete or natural end.
        """
        try:
            complete_output = ""
            history_tokens = Config.SLIDING_WINDOW_TOKENS
            max_loops = Config.MAX_CONTINUATION_LOOPS
            cumulative_token_count = 0  # Track total tokens across all passes

            # Start with first prompt
            current_prompt = self._build_initial_prompt(query, context)

            # Debug: Log context usage
            if context and context.strip():
                self.logger.info(f"Producer: Using RAG context ({len(context)} chars)")
                self.logger.info(f"Producer: Context preview: '{context[:100]}...'")
            else:
                self.logger.info("Producer: No RAG context provided")

            self.logger.info(f"Producer: Initial prompt length: {len(current_prompt)} chars")

            loop_idx = 0
            while True:
                self.logger.info(f"Producer starting pass {loop_idx + 1}")

                # Get model instance for streaming
                model_instance = self.llm_service.get_model_instance()
                if not model_instance:
                    self.token_buffer.put({"status": "error", "error": "Model instance not available"})
                    return

                # Generate tokens from model (no delays here)
                token_count = 0
                current_chunk = ""

                # Always use streaming method - no fallbacks
                self.logger.info(f"Producer: Starting streaming generation for pass {loop_idx + 1}")
                self.logger.info(f"Producer: Model instance type: {type(model_instance)}")

                # Get streaming generator from model
                stream_generator = model_instance.generate_streaming_response(current_prompt)

                self.logger.info(f"Producer starting to iterate through stream for pass {loop_idx + 1}")
                chunk_count = 0
                hit_limit = False

                for chunk in stream_generator:
                    chunk_count += 1

                    if chunk.get("status") == "error":
                        self.token_buffer.put({"status": "error", "error": chunk.get("error")})
                        return

                    if chunk.get("status") == "streaming":
                        token_text = chunk.get("token", "")
                        if token_text:
                            current_chunk += token_text
                            token_count += 1
                            # Stream token to consumer immediately
                            self.token_buffer.put({
                                "status": "streaming",
                                "token": token_text,
                                "pass": loop_idx + 1,
                                "token_count": token_count
                            })

                    elif chunk.get("status") == "complete":
                        # Check if this was a forced truncation or natural completion
                        finish_reason = None
                        if isinstance(chunk, dict) and 'finish_reason' in chunk:
                            finish_reason = chunk.get('finish_reason')

                        self.logger.info(f"Producer: Pass {loop_idx + 1} completed with {token_count} tokens")
                        self.logger.info(f"Producer: Finish reason: {finish_reason}")

                        # NEW LOGIC: Check finish_reason for continuation decision
                        if finish_reason == 'length':
                            # Model hit token limit - FORCE CONTINUATION (no max_loops restriction)
                            self.logger.info(f"Producer: finish_reason='length' - MODEL HIT TOKEN LIMIT - CONTINUING")
                            hit_limit = True
                            break
                        elif finish_reason in ['stop', 'eos_token'] or finish_reason is None:
                            # Natural completion - STOP
                            cumulative_token_count += token_count  # Add final pass tokens
                            self.logger.info(f"Producer: Total tokens so far: {cumulative_token_count}")
                            self.logger.info(
                                f"Producer: finish_reason='{finish_reason}' - NATURAL COMPLETION - STOPPING")
                            self.logger.info(f"Producer: FINAL TOTAL TOKENS: {cumulative_token_count}")
                            self.token_buffer.put({"status": "complete", "total_passes": loop_idx + 1,
                                                   "total_tokens": cumulative_token_count})
                            return
                        else:
                            # Unknown finish_reason - log and stop to be safe
                            cumulative_token_count += token_count  # Add final pass tokens
                            self.logger.info(f"Producer: Total tokens so far: {cumulative_token_count}")
                            self.logger.info(f"Producer: Unknown finish_reason='{finish_reason}' - STOPPING")
                            self.logger.info(f"Producer: FINAL TOTAL TOKENS: {cumulative_token_count}")
                            self.token_buffer.put({"status": "complete", "total_passes": loop_idx + 1,
                                                   "total_tokens": cumulative_token_count})
                            return

                # Add tokens to complete output for sliding window
                complete_output += current_chunk

                # If we hit limit, prepare next pass
                if hit_limit:
                    cumulative_token_count += token_count  # Add current pass tokens to cumulative count
                    self.logger.info(f"Producer: Total tokens accumulated: {cumulative_token_count}")

                    # Signal end of current pass to consumer
                    self.token_buffer.put({
                        "status": "pass_complete",
                        "pass": loop_idx + 1,
                        "tokens_in_pass": token_count,
                        "total_tokens_so_far": cumulative_token_count
                    })

                    # Small delay to let consumer process the pass completion
                    import time
                    time.sleep(0.1)  # 100ms delay between passes

                    self.logger.info(f"Producer preparing next pass {loop_idx + 2}")
                    # Build next prompt with sliding window context
                    prev_text = self._get_sliding_window_context(complete_output, history_tokens)
                    current_prompt = self._build_continuation_prompt(query, context, prev_text)

                    # Debug: Log continuation prompt details
                    self.logger.info(f"Producer: Continuation prompt length: {len(current_prompt)} chars")
                    self.logger.info(f"Producer: Sliding window context length: {len(prev_text)} chars")
                    if context:
                        self.logger.info(f"Producer: RAG context preserved in continuation: {len(context)} chars")

                    # Reset for next pass
                    current_chunk = ""
                    token_count = 0
                    hit_limit = False
                    loop_idx += 1

                    continue
                else:
                    # Natural completion - should not reach here as model handles completion in streaming loop
                    cumulative_token_count += token_count  # Add final pass tokens
                    self.logger.info(f"Producer: Generation complete after {loop_idx + 1} passes")
                    self.logger.info(f"Producer: FINAL TOTAL TOKENS: {cumulative_token_count}")
                    self.logger.info(f"Producer finished: hit_limit={hit_limit}, loop_idx={loop_idx}")
                    self.token_buffer.put(
                        {"status": "complete", "total_passes": loop_idx + 1, "total_tokens": cumulative_token_count})
                    return

        except Exception as e:
            self.logger.error(f"Producer error: {str(e)}")
            self.token_buffer.put({"status": "error", "error": str(e)})

    def _token_consumer(self):
        """
        Consumer: Simply streams buffered tokens to user with 50ms delay for smooth UX.
        Just consumes whatever producer generates - no complex logic.
        """
        try:
            while True:
                try:
                    # Get token from buffer (wait if needed) - 5 minute timeout for very slow model startup
                    token_data = self.token_buffer.get(timeout=300)  # 5 minute timeout

                    if token_data.get("status") == "error":
                        yield {
                            "type": "error",
                            "error": token_data.get("error", "Unknown error"),
                            "timestamp": int(time.time() * 1000)
                        }
                        break

                    elif token_data.get("status") == "complete":
                        # Producer finished all passes
                        total_passes = token_data.get("total_passes", 1)
                        total_tokens = token_data.get("total_tokens", 0)
                        self.logger.info(
                            f"Consumer: Producer completed all {total_passes} passes with {total_tokens} tokens")

                        yield {
                            "type": "complete",
                            "total_passes": total_passes,
                            "total_tokens": total_tokens,
                            "timestamp": int(time.time() * 1000)
                        }
                        break

                    elif token_data.get("status") == "pass_complete":
                        # Producer completed a pass, log it but don't yield to user
                        pass_num = token_data.get("pass", 1)
                        tokens_in_pass = token_data.get("tokens_in_pass", 0)
                        total_tokens_so_far = token_data.get("total_tokens_so_far", 0)
                        self.logger.info(
                            f"Consumer: Pass {pass_num} completed with {tokens_in_pass} tokens (total: {total_tokens_so_far})")
                        # Don't yield - just continue to next token
                        continue

                    elif token_data.get("status") == "streaming":
                        # Get token content (producer sends 'token', UI expects 'content')
                        token_content = token_data.get("token", "")

                        # Log first few tokens received by consumer
                        if token_data.get("token_count", 0) <= 3:
                            self.logger.info(
                                f"Consumer received token {token_data.get('token_count', 0)} from pass {token_data.get('pass', 1)}: '{token_content}'")

                        # Stream token to user with 50ms delay (UI expects 'type': 'token')
                        yield {
                            "type": "token",
                            "content": token_content,
                            "pass": token_data.get("pass", 1),
                            "token_count": token_data.get("token_count", 0),
                            "timestamp": int(time.time() * 1000)
                        }

                        # 50ms delay for smooth user experience
                        time.sleep(0.05)

                except queue.Empty:
                    self.logger.warning("Consumer timeout waiting for tokens")
                    yield {
                        "type": "error",
                        "error": "Generation timeout",
                        "timestamp": int(time.time() * 1000)
                    }
                    break

        except Exception as e:
            self.logger.error(f"Consumer error: {str(e)}")
            yield {
                "type": "error",
                "error": str(e),
                "timestamp": int(time.time() * 1000)
            }

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

        # Token-based context truncation using configured MAX_CONTEXT_LENGTH (tokens)
        max_context_tokens = Config.MAX_CONTEXT_LENGTH

        # Estimate query tokens (rough approximation: ~4 chars per token)
        query_chars = len(query)
        estimated_query_tokens = query_chars // 4

        # Reserve tokens for query and prompt template
        if estimated_query_tokens > 200:  # Very long query
            max_context_tokens = int(max_context_tokens * 0.67)  # Reserve more space
        elif estimated_query_tokens > 100:  # Medium query
            max_context_tokens = int(max_context_tokens * 0.83)  # Reserve some space
        else:
            max_context_tokens = int(max_context_tokens * 0.9)  # Reserve minimal space

        # Convert token limit to approximate character limit
        max_context_chars = max_context_tokens * 4

        if len(context) <= max_context_chars:
            return context

        # Truncate context while trying to preserve sentence boundaries
        truncated = context[:max_context_chars]

        # Try to end at a sentence boundary
        last_period = truncated.rfind('. ')
        if last_period > max_context_chars * 0.8:  # If we can keep 80% and end at sentence
            truncated = truncated[:last_period + 1]

        self.logger.info(
            f"Truncated context from ~{len(context)//4} to ~{len(truncated)//4} tokens to fit within token limits")
        return truncated

    def generate_streaming_response(self, query: str, context_info: dict = None) -> Generator[Dict[str, Any], None, None]:
        """
        Generate streaming response with sliding window continuation for long responses

        Args:
            query: User query
            context_info: Optional context information dict with repository_names, etc.

        Yields:
            Dictionary containing streaming response tokens
        """
        try:
            self.logger.info(f"Starting streaming response with continuation for query: '{query[:50]}...'")

            # Get RAG context with context information
            context = None
            if context_info:
                context_result = self.llm_service._get_rag_context(query, context_info)
                context = context_result.get("context", "")
            else:
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

            # Always use sliding window continuation with streaming
            self.logger.info(
                f"Using sliding window continuation with streaming (MAX_NEW_TOKENS={Config.MAX_NEW_TOKENS})")
            yield from self._generate_with_sliding_window(query, context)

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

    def _generate_with_sliding_window(self, query: str, context: str = None) -> Generator[Dict[str, Any], None, None]:
        """
        Generate response using sliding window continuation with producer-consumer pattern.
        Producer independently generates all tokens across multiple passes.
        Consumer simply streams whatever producer generates.

        Args:
            query: User query
            context: RAG context

        Yields:
            Dictionary containing streaming response tokens
        """
        try:
            # Clear previous state
            self.token_buffer = queue.Queue()
            self.generation_complete.clear()
            self.continuation_ready.clear()

            # Start single producer thread that handles all passes independently
            producer_thread = threading.Thread(
                target=self._token_producer,
                args=(query, context),
                daemon=True
            )
            producer_thread.start()

            # Start consumer to stream tokens to user
            for token_data in self._token_consumer():
                if token_data.get("type") == "error":
                    yield {
                        "type": "error",
                        "error": token_data.get("error"),
                        "timestamp": int(time.time() * 1000)
                    }
                    break

                elif token_data.get("type") == "token":
                    content = token_data.get("content", "")

                    # Stream token to client (consumer already has 50ms delay)
                    yield {
                        "type": "token",
                        "content": content,
                        "pass": token_data.get("pass", 1),
                        "timestamp": int(time.time() * 1000)
                    }

                elif token_data.get("type") == "complete":
                    # Producer finished all passes
                    total_passes = token_data.get("total_passes", 1)
                    total_tokens = token_data.get("total_tokens", 0)

                    yield {
                        "type": "complete",
                        "total_passes": total_passes,
                        "total_tokens": total_tokens,
                        "timestamp": int(time.time() * 1000)
                    }
                    break

            # Wait for producer thread to complete
            producer_thread.join(timeout=10)

        except Exception as e:
            self.logger.error(f"Error in sliding window generation: {str(e)}")
            yield {
                "type": "error",
                "error": str(e),
                "timestamp": int(time.time() * 1000)
            }

    def _get_sliding_window_context(self, complete_output: str, history_tokens: int) -> str:
        """
        Get sliding window context from complete output

        Args:
            complete_output: Full generated text so far
            history_tokens: Number of tokens to keep for context

        Returns:
            Truncated text containing last N tokens (approximately)
        """
        if not complete_output:
            return ""

        try:
            # Approximate token-based truncation
            # Average ~4 characters per token for most models
            chars_per_token = 4
            target_chars = history_tokens * chars_per_token

            if len(complete_output) <= target_chars:
                return complete_output

            # Keep last N characters (approximately N/4 tokens)
            sliding_window_text = complete_output[-target_chars:]

            # Try to start at a word boundary to avoid cutting words in half
            first_space = sliding_window_text.find(' ')
            if first_space > 0 and first_space < 50:  # Only if space is near the beginning
                sliding_window_text = sliding_window_text[first_space + 1:]

            actual_chars = len(sliding_window_text)
            estimated_tokens = actual_chars // chars_per_token

            self.logger.info(
                f"Sliding window: kept last ~{estimated_tokens} tokens ({actual_chars} chars) from {len(complete_output)} total chars")
            return sliding_window_text

        except Exception as e:
            self.logger.error(f"Error creating sliding window: {str(e)}")
            return complete_output[-2000:]  # Fallback: keep last 2000 characters

    def _build_initial_prompt(self, query: str, context: str = None) -> str:
        """
        Build initial prompt for first generation

        Args:
            query: User query
            context: RAG context

        Returns:
            Formatted prompt string
        """
        if context and context.strip():
            return Config.RAG_PROMPT_TEMPLATE.format(
                context=context[:Config.MAX_CONTEXT_LENGTH],
                question=query
            )
        else:
            return Config.FALLBACK_PROMPT_TEMPLATE.format(question=query)

    def _build_continuation_prompt(self, query: str, context: str, prev_text: str) -> str:
        """
        Build continuation prompt with sliding window context

        For continuation passes, we SKIP the RAG context since it was already
        provided in the initial prompt. Only use sliding window for continuity.

        Args:
            query: Original user query
            context: RAG context (IGNORED for continuation - already used in initial prompt)
            prev_text: Previous output (sliding window)

        Returns:
            Formatted continuation prompt (without RAG context)
        """
        # For continuation passes, ALWAYS use direct continuation without RAG context
        # The RAG context was already provided in the initial prompt
        continuation_template = """Question: {question}

Previous response: {previous}

Continue the response naturally:"""

        return continuation_template.format(
            question=query,
            previous=prev_text
        )
