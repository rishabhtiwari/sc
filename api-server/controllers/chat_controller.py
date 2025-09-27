"""
Chat Controller - Business logic for chat operations
"""

import time
import random
from typing import Dict, Any, Optional

from flask import current_app
from services.llm_service_client import llm_client
from services.retriever_service_client import retriever_client


class ChatController:
    """
    Controller for handling chat-related business logic
    """

    # Client context storage (in-memory for now, could be moved to Redis/database)
    _client_contexts = {}

    # Sample responses for demonstration
    SAMPLE_RESPONSES = [
        "That's a great question! Let me help you with that. 🤔",
        "I understand what you're looking for. Here's what I think... 💡",
        "Thanks for sharing that with me! I'd be happy to assist. ✨",
        "Interesting point! Let me provide you with some insights. 🎯",
        "I'm here to help! Let me break that down for you. 📝",
        "That's a fascinating topic! Here's my perspective... 🌟",
        "I appreciate you asking! Let me give you a detailed answer. 📚",
        "Great minds think alike! Here's what I would suggest... 🧠",
        "Excellent question! Let me share my thoughts on this... 💭",
        "I love discussing this topic! Here's what I think... ❤️"
    ]
    
    @classmethod
    def process_message(cls, message: str, client: str = "unknown", conversation_id: str = None,
                       use_rag: bool = False, session_id: str = "default_session") -> Dict[str, Any]:
        """
        Process a chat message and generate a response using LLM service

        Args:
            message (str): The user's message
            client (str): The client identifier
            conversation_id (str): Optional conversation ID for context
            use_rag (bool): Whether to use RAG for enhanced responses

        Returns:
            Dict[str, Any]: Response data
        """
        try:
            # Log the incoming message
            current_app.logger.info(f"📨 Received message from {client}: {message[:100]}...")

            # Validate message
            if not message or not message.strip():
                return {
                    "error": "Empty message not allowed",
                    "status": "error"
                }
            
            # Check message length
            max_length = current_app.config.get('MAX_MESSAGE_LENGTH', 1000)
            if len(message) > max_length:
                return {
                    "error": f"Message too long. Maximum {max_length} characters allowed.",
                    "status": "error"
                }

            # Try to use LLM service first
            try:
                if use_rag:
                    # Check if client has pre-set context
                    context_key = f"{client}:{session_id}"
                    client_context = cls._client_contexts.get(context_key)

                    if client_context and client_context.get('document_ids'):
                        # Use client context for RAG
                        current_app.logger.info(f"🔍 Using client context with {len(client_context['document_ids'])} documents")

                        # Build context from client documents
                        context_result = cls.build_rag_context(
                            query=message.strip(),
                            max_chunks=5,
                            document_ids=client_context['document_ids']
                        )

                        if context_result.get('status') == 'success' and context_result.get('context'):
                            # Use RAG with client context
                            llm_result = llm_client.generate_with_context(
                                query=message.strip(),
                                context=context_result['context'],
                                max_tokens=150,
                                temperature=0.7
                            )
                        else:
                            # Fallback to regular RAG
                            llm_result = llm_client.generate_with_rag(
                                query=message.strip(),
                                max_tokens=150,
                                temperature=0.7
                            )
                    else:
                        # Use regular RAG-enabled generation
                        llm_result = llm_client.generate_with_rag(
                            query=message.strip(),
                            max_tokens=150,
                            temperature=0.7
                        )
                else:
                    # Use regular chat
                    llm_result = llm_client.chat_with_llm(
                        message=message.strip(),
                        conversation_id=conversation_id,
                        max_tokens=150,
                        temperature=0.7,
                        use_rag=use_rag
                    )

                if llm_result['status'] == 'success':
                    response_source = "rag" if use_rag and llm_result.get('context_used') else "llm"
                    current_app.logger.info(f"📤 LLM response generated successfully (source: {response_source})")

                    response_data = {
                        "message": llm_result['response'],
                        "timestamp": int(time.time() * 1000),
                        "status": "success",
                        "original_message": message,
                        "client": client,
                        "conversation_id": llm_result.get('conversation_id'),
                        "model": llm_result.get('model'),
                        "tokens_used": llm_result.get('tokens_used'),
                        "source": response_source
                    }

                    # Add RAG-specific information if available
                    if use_rag:
                        response_data.update({
                            "context_used": llm_result.get('context_used', False),
                            "context_chunks": llm_result.get('context_chunks', 0),
                            "context_length": llm_result.get('context_length', 0),
                            "response_type": llm_result.get('response_type', 'unknown')
                        })

                    return response_data
                else:
                    current_app.logger.warning(f"LLM service error: {llm_result.get('error')}")
                    # Fall back to simple response

            except Exception as llm_error:
                current_app.logger.error(f"LLM service exception: {str(llm_error)}")
                # Fall back to simple response

            # Fallback: Generate simple chat response
            current_app.logger.info("Using fallback response generation")
            response_message = ChatController._generate_response(message)

            # Create response data
            response_data = {
                "message": response_message,
                "timestamp": int(time.time() * 1000),
                "status": "success",
                "original_message": message,
                "client": client,
                "source": "fallback"
            }

            current_app.logger.info(f"📤 Sending fallback response")
            return response_data
            
        except Exception as e:
            current_app.logger.error(f"❌ Error processing message: {str(e)}")
            return {
                "error": f"Failed to process message: {str(e)}",
                "status": "error"
            }
    
    @staticmethod
    def _generate_response(message: str) -> str:
        """
        Generate a response based on the input message
        
        Args:
            message (str): The user's message
            
        Returns:
            str: Generated response
        """
        message_lower = message.lower().strip()
        
        # Handle specific message types
        if message_lower in ['ping', 'test']:
            return f"Pong! I received your '{message}' message. System is working perfectly! ✅"
        
        elif message_lower in ['hello', 'hi', 'hey']:
            return f"Hello there! 👋 Thanks for saying '{message}'. How can I help you today?"
        
        elif message_lower in ['how are you', 'how are you?']:
            return "I'm doing great, thank you for asking! I'm here and ready to help. How are you doing? 😊"
        
        elif 'help' in message_lower:
            return "I'm here to help! You can ask me anything, and I'll do my best to provide useful responses. What would you like to know? 🤝"
        
        elif 'thank' in message_lower:
            return "You're very welcome! I'm happy I could help. Feel free to ask me anything else! 🙏"
        
        elif '?' in message:
            return "That's a thoughtful question! " + random.choice(ChatController.SAMPLE_RESPONSES)
        
        else:
            # Return a random response for general messages
            return random.choice(ChatController.SAMPLE_RESPONSES)
    
    @staticmethod
    def search_documents(query: str, limit: int = 5) -> Dict[str, Any]:
        """
        Search documents using the retriever service

        Args:
            query (str): Search query
            limit (int): Maximum number of results

        Returns:
            Dict[str, Any]: Search results
        """
        try:
            current_app.logger.info(f"🔍 Searching documents: {query[:50]}...")

            # Search using retriever service
            search_result = retriever_client.search_documents(
                query=query,
                limit=limit,
                min_similarity=0.2
            )

            if search_result['status'] == 'success':
                results = search_result['data'].get('results', [])
                current_app.logger.info(f"📚 Found {len(results)} documents")
                return {
                    "status": "success",
                    "query": query,
                    "results": results,
                    "total_results": len(results),
                    "timestamp": int(time.time() * 1000)
                }
            else:
                current_app.logger.error(f"Document search failed: {search_result.get('error')}")
                return {
                    "status": "error",
                    "error": search_result.get('error', 'Document search failed'),
                    "timestamp": int(time.time() * 1000)
                }

        except Exception as e:
            current_app.logger.error(f"❌ Error searching documents: {str(e)}")
            return {
                "status": "error",
                "error": f"Document search error: {str(e)}",
                "timestamp": int(time.time() * 1000)
            }

    @staticmethod
    def build_rag_context(query: str, max_chunks: int = 3, document_ids: list = None) -> Dict[str, Any]:
        """
        Build RAG context for a query

        Args:
            query (str): Query for context building
            max_chunks (int): Maximum number of chunks to include
            document_ids (list): Optional list of specific document IDs to search

        Returns:
            Dict[str, Any]: RAG context data
        """
        try:
            current_app.logger.info(f"🧠 Building RAG context: {query[:50]}...")

            # Build context using retriever service
            if document_ids:
                # Use specific documents for context building
                context_result = retriever_client.build_rag_context_from_documents(
                    query=query,
                    document_ids=document_ids,
                    max_chunks=max_chunks,
                    context_window_size=4000
                )
            else:
                # Use all available documents
                context_result = retriever_client.build_rag_context(
                    query=query,
                    max_chunks=max_chunks,
                    context_window_size=4000
                )

            if context_result['status'] == 'success':
                context_data = context_result['data']
                context_length = context_data.get('context_length', 0)
                total_chunks = context_data.get('total_chunks', 0)
                current_app.logger.info(f"📝 Built context: {context_length} chars, {total_chunks} chunks")
                return {
                    "status": "success",
                    "context": context_data.get('context', ''),
                    "chunks": context_data.get('chunks', []),
                    "context_length": context_length,
                    "total_chunks": total_chunks,
                    "timestamp": int(time.time() * 1000)
                }
            else:
                current_app.logger.error(f"RAG context building failed: {context_result.get('error')}")
                return {
                    "status": "error",
                    "error": context_result.get('error', 'RAG context building failed'),
                    "timestamp": int(time.time() * 1000)
                }

        except Exception as e:
            current_app.logger.error(f"❌ Error building RAG context: {str(e)}")
            return {
                "status": "error",
                "error": f"RAG context error: {str(e)}",
                "timestamp": int(time.time() * 1000)
            }

    @staticmethod
    def get_chat_stats() -> Dict[str, Any]:
        """
        Get chat statistics (placeholder for future implementation)
        
        Returns:
            Dict[str, Any]: Chat statistics
        """
        return {
            "total_messages": 0,
            "active_sessions": 0,
            "uptime": int(time.time() * 1000),
            "status": "operational"
        }

    @classmethod
    def set_client_context(cls, document_ids: list, client_id: str = "default_client",
                          session_id: str = "default_session") -> Dict[str, Any]:
        """
        Set context using client-stored document IDs

        Args:
            document_ids (list): List of document IDs from client storage
            client_id (str): Client identifier
            session_id (str): Session identifier

        Returns:
            Dict[str, Any]: Context setup result
        """
        try:
            context_key = f"{client_id}:{session_id}"

            # Validate document IDs exist in embedding service
            valid_documents = []
            invalid_documents = []

            for doc_id in document_ids:
                try:
                    # Check if document exists in embedding service
                    doc_info = retriever_client.get_document_context(doc_id)
                    if doc_info and doc_info.get('status') == 'success':
                        valid_documents.append(doc_id)
                    else:
                        invalid_documents.append(doc_id)
                except Exception as e:
                    print(f"⚠️ Document {doc_id} validation failed: {str(e)}")
                    invalid_documents.append(doc_id)

            # Store valid document IDs in context
            cls._client_contexts[context_key] = {
                "document_ids": valid_documents,
                "client_id": client_id,
                "session_id": session_id,
                "created_at": int(time.time() * 1000),
                "last_updated": int(time.time() * 1000)
            }

            return {
                "status": "success",
                "message": "Client context set successfully",
                "context_key": context_key,
                "valid_documents": len(valid_documents),
                "invalid_documents": len(invalid_documents),
                "invalid_document_ids": invalid_documents,
                "total_requested": len(document_ids),
                "timestamp": int(time.time() * 1000)
            }

        except Exception as e:
            print(f"❌ Error setting client context: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to set client context: {str(e)}",
                "timestamp": int(time.time() * 1000)
            }

    @classmethod
    def get_context_status(cls, client_id: str = "default_client",
                          session_id: str = "default_session") -> Dict[str, Any]:
        """
        Get current context status for a client/session

        Args:
            client_id (str): Client identifier
            session_id (str): Session identifier

        Returns:
            Dict[str, Any]: Context status information
        """
        try:
            context_key = f"{client_id}:{session_id}"

            if context_key in cls._client_contexts:
                context = cls._client_contexts[context_key]
                return {
                    "status": "success",
                    "has_context": True,
                    "context_key": context_key,
                    "document_count": len(context["document_ids"]),
                    "document_ids": context["document_ids"],
                    "created_at": context["created_at"],
                    "last_updated": context["last_updated"],
                    "client_id": context["client_id"],
                    "session_id": context["session_id"],
                    "timestamp": int(time.time() * 1000)
                }
            else:
                return {
                    "status": "success",
                    "has_context": False,
                    "context_key": context_key,
                    "document_count": 0,
                    "message": "No context set for this client/session",
                    "timestamp": int(time.time() * 1000)
                }

        except Exception as e:
            print(f"❌ Error getting context status: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to get context status: {str(e)}",
                "timestamp": int(time.time() * 1000)
            }

    @classmethod
    def clear_context(cls, client_id: str = "default_client",
                     session_id: str = "default_session") -> Dict[str, Any]:
        """
        Clear context for a client/session

        Args:
            client_id (str): Client identifier
            session_id (str): Session identifier

        Returns:
            Dict[str, Any]: Clear operation result
        """
        try:
            context_key = f"{client_id}:{session_id}"

            if context_key in cls._client_contexts:
                removed_context = cls._client_contexts.pop(context_key)
                return {
                    "status": "success",
                    "message": "Context cleared successfully",
                    "context_key": context_key,
                    "documents_removed": len(removed_context["document_ids"]),
                    "timestamp": int(time.time() * 1000)
                }
            else:
                return {
                    "status": "success",
                    "message": "No context to clear",
                    "context_key": context_key,
                    "documents_removed": 0,
                    "timestamp": int(time.time() * 1000)
                }

        except Exception as e:
            print(f"❌ Error clearing context: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to clear context: {str(e)}",
                "timestamp": int(time.time() * 1000)
            }
