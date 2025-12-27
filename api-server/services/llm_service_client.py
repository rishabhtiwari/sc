"""
LLM Service Client - Interface for communicating with the LLM service
"""

import requests
import logging
from typing import Dict, Any, Optional, Union
from datetime import datetime
import json


class LLMServiceClient:
    """Client for communicating with the LLM service"""
    
    def __init__(self, base_url: str = "http://ichat-llm-service:8083", timeout: int = 300):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.logger = logging.getLogger('api-server')
    
    def chat_with_llm(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        context: Optional[str] = None,
        use_rag: bool = False
    ) -> Dict[str, Any]:
        """
        Send chat message to LLM service

        Args:
            message: User message
            conversation_id: Optional conversation ID
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            context: Additional context
            use_rag: Whether to use RAG (Retrieval-Augmented Generation)

        Returns:
            Dict containing LLM response or error
        """
        try:
            payload = {
                "message": message
            }

            if conversation_id:
                payload["conversation_id"] = conversation_id
            if max_tokens is not None:
                payload["max_tokens"] = max_tokens
            if temperature is not None:
                payload["temperature"] = temperature
            if context:
                payload["context"] = context
            if use_rag:
                payload["use_rag"] = use_rag
            
            self.logger.info(f"Sending chat request to LLM service: {message[:50]}...")
            
            response = requests.post(
                f"{self.base_url}/llm/chat",
                json=payload,
                timeout=self.timeout,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                result = response.json()
                self.logger.info(f"LLM response received: {len(result.get('response', ''))} chars")
                return {
                    "status": "success",
                    "response": result.get("response", ""),
                    "conversation_id": result.get("conversation_id"),
                    "model": result.get("model"),
                    "tokens_used": result.get("tokens_used"),
                    "timestamp": result.get("timestamp")
                }
            else:
                error_msg = f"LLM service error: {response.status_code}"
                self.logger.error(error_msg)
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error", error_msg)
                except:
                    pass
                
                return {
                    "status": "error",
                    "error": error_msg,
                    "timestamp": int(datetime.now().timestamp() * 1000)
                }
                
        except requests.exceptions.Timeout:
            error_msg = "LLM service timeout"
            self.logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg,
                "timestamp": int(datetime.now().timestamp() * 1000)
            }
        except requests.exceptions.ConnectionError:
            error_msg = "Cannot connect to LLM service"
            self.logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg,
                "timestamp": int(datetime.now().timestamp() * 1000)
            }
        except Exception as e:
            error_msg = f"LLM service client error: {str(e)}"
            self.logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg,
                "timestamp": int(datetime.now().timestamp() * 1000)
            }
    
    def generate_with_rag(
        self,
        query: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Generate text using RAG (Retrieval-Augmented Generation)

        Args:
            query: Query text for RAG generation
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Top-p sampling parameter

        Returns:
            Dict containing generated text with RAG context or error
        """
        try:
            payload = {
                "query": query,
                "use_rag": True
            }

            if max_tokens is not None:
                payload["max_tokens"] = max_tokens
            if temperature is not None:
                payload["temperature"] = temperature
            if top_p is not None:
                payload["top_p"] = top_p

            self.logger.info(f"Sending RAG generation request: {query[:50]}...")

            response = requests.post(
                f"{self.base_url}/llm/generate",
                json=payload,
                timeout=self.timeout,
                headers={'Content-Type': 'application/json'}
            )

            if response.status_code == 200:
                result = response.json()
                context_used = result.get("context_used", False)
                context_chunks = result.get("context_chunks", 0)
                self.logger.info(f"RAG response: context_used={context_used}, chunks={context_chunks}")
                return {
                    "status": "success",
                    "response": result.get("response", ""),
                    "model": result.get("model"),
                    "context_used": context_used,
                    "context_chunks": context_chunks,
                    "context_length": result.get("context_length", 0),
                    "response_type": result.get("response_type", "unknown"),
                    "timestamp": result.get("timestamp")
                }
            else:
                error_msg = f"RAG generation error: {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error", error_msg)
                except:
                    pass

                return {
                    "status": "error",
                    "error": error_msg,
                    "timestamp": int(datetime.now().timestamp() * 1000)
                }

        except Exception as e:
            error_msg = f"RAG generation client error: {str(e)}"
            self.logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg,
                "timestamp": int(datetime.now().timestamp() * 1000)
            }

    def generate_text(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Generate text using LLM service

        Args:
            prompt: Text prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Top-p sampling parameter

        Returns:
            Dict containing generated text or error
        """
        try:
            payload = {
                "prompt": prompt
            }

            if max_tokens is not None:
                payload["max_tokens"] = max_tokens
            if temperature is not None:
                payload["temperature"] = temperature
            if top_p is not None:
                payload["top_p"] = top_p

            self.logger.info(f"Sending generation request to LLM service: {prompt[:50]}...")

            response = requests.post(
                f"{self.base_url}/llm/generate",
                json=payload,
                timeout=self.timeout,
                headers={'Content-Type': 'application/json'}
            )

            if response.status_code == 200:
                result = response.json()
                return {
                    "status": "success",
                    "response": result.get("response", ""),
                    "model": result.get("model"),
                    "tokens_used": result.get("tokens_used"),
                    "timestamp": result.get("timestamp")
                }
            else:
                error_msg = f"LLM generation error: {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error", error_msg)
                except:
                    pass

                return {
                    "status": "error",
                    "error": error_msg,
                    "timestamp": int(datetime.now().timestamp() * 1000)
                }

        except Exception as e:
            error_msg = f"LLM generation client error: {str(e)}"
            self.logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg,
                "timestamp": int(datetime.now().timestamp() * 1000)
            }
    
    def get_llm_status(self) -> Dict[str, Any]:
        """
        Get LLM service status
        
        Returns:
            Dict containing service status
        """
        try:
            response = requests.get(
                f"{self.base_url}/health",
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "status": "error",
                    "error": f"LLM service unavailable: {response.status_code}",
                    "timestamp": int(datetime.now().timestamp() * 1000)
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": f"Cannot reach LLM service: {str(e)}",
                "timestamp": int(datetime.now().timestamp() * 1000)
            }
    
    def get_models_info(self) -> Dict[str, Any]:
        """
        Get available models information
        
        Returns:
            Dict containing models information
        """
        try:
            response = requests.get(
                f"{self.base_url}/llm/models",
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "status": "error",
                    "error": f"Cannot get models info: {response.status_code}",
                    "timestamp": int(datetime.now().timestamp() * 1000)
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": f"Models info error: {str(e)}",
                "timestamp": int(datetime.now().timestamp() * 1000)
            }
    
    def get_conversation_history(self, conversation_id: str) -> Dict[str, Any]:
        """
        Get conversation history from LLM service
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            Dict containing conversation history
        """
        try:
            response = requests.get(
                f"{self.base_url}/llm/conversation/{conversation_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "status": "error",
                    "error": f"Cannot get conversation: {response.status_code}",
                    "timestamp": int(datetime.now().timestamp() * 1000)
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": f"Conversation history error: {str(e)}",
                "timestamp": int(datetime.now().timestamp() * 1000)
            }
    
    def clear_conversation(self, conversation_id: str) -> Dict[str, Any]:
        """
        Clear conversation history
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            Dict containing operation result
        """
        try:
            response = requests.delete(
                f"{self.base_url}/llm/conversation/{conversation_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "status": "error",
                    "error": f"Cannot clear conversation: {response.status_code}",
                    "timestamp": int(datetime.now().timestamp() * 1000)
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": f"Clear conversation error: {str(e)}",
                "timestamp": int(datetime.now().timestamp() * 1000)
            }

    def generate_with_context(
        self,
        query: str,
        context: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Generate response using provided context (for client-side document storage)

        Args:
            query: User query
            context: Pre-built context from client documents
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            Dict containing generated response or error
        """
        try:
            payload = {
                "query": query,
                "context": context,
                "use_rag": True
            }

            # Add optional parameters
            if max_tokens is not None:
                payload["max_tokens"] = max_tokens
            if temperature is not None:
                payload["temperature"] = temperature

            self.logger.info(f"🤖 Generating response with provided context (length: {len(context)})")

            response = requests.post(
                f"{self.base_url}/llm/generate",
                json=payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                result = response.json()
                self.logger.info("✅ Context-based generation successful")

                # Add context metadata
                result.update({
                    "context_used": True,
                    "context_length": len(context),
                    "response_type": "context_based"
                })

                return result
            else:
                error_msg = f"Context generation failed: {response.status_code}"
                self.logger.error(error_msg)

                try:
                    error_detail = response.json().get('error', 'Unknown error')
                    error_msg = f"{error_msg} - {error_detail}"
                except:
                    pass

                return {
                    "status": "error",
                    "error": error_msg,
                    "timestamp": int(datetime.now().timestamp() * 1000)
                }

        except Exception as e:
            error_msg = f"Context generation client error: {str(e)}"
            self.logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg,
                "timestamp": int(datetime.now().timestamp() * 1000)
            }


# Global LLM client instance with 5-minute timeout
llm_client = LLMServiceClient(timeout=300)
