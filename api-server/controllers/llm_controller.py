"""
LLM Controller - Business logic for LLM operations
"""

import time
import uuid
from typing import Dict, Any, Optional
from flask import current_app

from services.llm_service_client import llm_client


class LLMController:
    """
    Controller for handling LLM business logic
    """
    
    @staticmethod
    def process_chat_message(
        message: str,
        conversation_id: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process chat message through LLM service
        
        Args:
            message: User message
            conversation_id: Optional conversation ID
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            context: Additional context
            
        Returns:
            Dict containing processed response
        """
        try:
            # Generate conversation ID if not provided
            if not conversation_id:
                conversation_id = str(uuid.uuid4())
            
            # Set reasonable defaults
            if max_tokens is None:
                max_tokens = 128
            if temperature is None:
                temperature = 0.7
            
            # Validate parameters
            max_tokens = min(max_tokens, 512)  # Reasonable limit
            temperature = max(0.1, min(temperature, 2.0))  # Valid range
            
            current_app.logger.info(f"Processing chat message - Conv: {conversation_id[:8]}...")
            
            # Call LLM service
            result = llm_client.chat_with_llm(
                message=message,
                conversation_id=conversation_id,
                max_tokens=max_tokens,
                temperature=temperature,
                context=context
            )
            
            if result['status'] == 'success':
                return {
                    "status": "success",
                    "data": {
                        "response": result['response'],
                        "conversation_id": result.get('conversation_id', conversation_id),
                        "model": result.get('model'),
                        "tokens_used": result.get('tokens_used'),
                        "timestamp": result.get('timestamp')
                    },
                    "timestamp": int(time.time() * 1000)
                }
            else:
                return {
                    "status": "error",
                    "error": result.get('error', 'LLM service error'),
                    "conversation_id": conversation_id,
                    "timestamp": int(time.time() * 1000)
                }
                
        except Exception as e:
            current_app.logger.error(f"Chat processing error: {str(e)}")
            return {
                "status": "error",
                "error": "Failed to process chat message",
                "timestamp": int(time.time() * 1000)
            }
    
    @staticmethod
    def generate_text(
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
            Dict containing generated text
        """
        try:
            # Set reasonable defaults
            if max_tokens is None:
                max_tokens = 128
            if temperature is None:
                temperature = 0.7
            if top_p is None:
                top_p = 0.95
            
            # Validate parameters
            max_tokens = min(max_tokens, 512)
            temperature = max(0.1, min(temperature, 2.0))
            top_p = max(0.1, min(top_p, 1.0))
            
            current_app.logger.info(f"Generating text - Prompt length: {len(prompt)}")
            
            # Call LLM service
            result = llm_client.generate_text(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p
            )
            
            if result['status'] == 'success':
                return {
                    "status": "success",
                    "data": {
                        "response": result['response'],
                        "model": result.get('model'),
                        "tokens_used": result.get('tokens_used'),
                        "timestamp": result.get('timestamp')
                    },
                    "timestamp": int(time.time() * 1000)
                }
            else:
                return {
                    "status": "error",
                    "error": result.get('error', 'Text generation failed'),
                    "timestamp": int(time.time() * 1000)
                }
                
        except Exception as e:
            current_app.logger.error(f"Text generation error: {str(e)}")
            return {
                "status": "error",
                "error": "Failed to generate text",
                "timestamp": int(time.time() * 1000)
            }
    
    @staticmethod
    def get_llm_status() -> Dict[str, Any]:
        """
        Get LLM service status
        
        Returns:
            Dict containing service status
        """
        try:
            result = llm_client.get_llm_status()
            
            return {
                "status": "success",
                "data": result,
                "timestamp": int(time.time() * 1000)
            }
            
        except Exception as e:
            current_app.logger.error(f"LLM status error: {str(e)}")
            return {
                "status": "error",
                "error": "Failed to get LLM status",
                "timestamp": int(time.time() * 1000)
            }
    
    @staticmethod
    def get_models_info() -> Dict[str, Any]:
        """
        Get available models information
        
        Returns:
            Dict containing models information
        """
        try:
            result = llm_client.get_models_info()
            
            if result.get('status') == 'success':
                return {
                    "status": "success",
                    "data": result,
                    "timestamp": int(time.time() * 1000)
                }
            else:
                return {
                    "status": "error",
                    "error": result.get('error', 'Failed to get models info'),
                    "timestamp": int(time.time() * 1000)
                }
                
        except Exception as e:
            current_app.logger.error(f"Models info error: {str(e)}")
            return {
                "status": "error",
                "error": "Failed to get models information",
                "timestamp": int(time.time() * 1000)
            }
    
    @staticmethod
    def get_conversation_history(conversation_id: str) -> Dict[str, Any]:
        """
        Get conversation history
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            Dict containing conversation history
        """
        try:
            result = llm_client.get_conversation_history(conversation_id)
            
            if result.get('status') == 'success':
                return {
                    "status": "success",
                    "data": result,
                    "timestamp": int(time.time() * 1000)
                }
            else:
                return {
                    "status": "error",
                    "error": result.get('error', 'Conversation not found'),
                    "timestamp": int(time.time() * 1000)
                }
                
        except Exception as e:
            current_app.logger.error(f"Conversation history error: {str(e)}")
            return {
                "status": "error",
                "error": "Failed to get conversation history",
                "timestamp": int(time.time() * 1000)
            }
    
    @staticmethod
    def clear_conversation(conversation_id: str) -> Dict[str, Any]:
        """
        Clear conversation history
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            Dict containing operation result
        """
        try:
            result = llm_client.clear_conversation(conversation_id)
            
            if result.get('status') == 'success':
                return {
                    "status": "success",
                    "message": f"Conversation {conversation_id} cleared",
                    "timestamp": int(time.time() * 1000)
                }
            else:
                return {
                    "status": "error",
                    "error": result.get('error', 'Failed to clear conversation'),
                    "timestamp": int(time.time() * 1000)
                }
                
        except Exception as e:
            current_app.logger.error(f"Clear conversation error: {str(e)}")
            return {
                "status": "error",
                "error": "Failed to clear conversation",
                "timestamp": int(time.time() * 1000)
            }
