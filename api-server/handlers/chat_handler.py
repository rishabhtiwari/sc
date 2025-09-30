"""
Chat Handler - HTTP request/response handling for chat endpoints
"""

import time
import json

from flask import (
    request,
    jsonify,
    current_app,
    Response,
    stream_with_context
)

from controllers.chat_controller import ChatController


class ChatHandler:
    """
    Handler for chat-related HTTP requests
    """

    @staticmethod
    def handle_chat_message():
        """
        Handle POST /api/chat requests
        
        Returns:
            Flask Response: JSON response with chat data
        """
        try:
            # Validate request content type
            if not request.is_json:
                return jsonify({
                    "error": "Content-Type must be application/json",
                    "status": "error"
                }), 400

            # Get JSON data from request
            data = request.get_json()

            if not data:
                return jsonify({
                    "error": "No JSON data provided",
                    "status": "error"
                }), 400

            # Extract and validate required fields
            message = data.get('message', '').strip()
            if not message:
                return jsonify({
                    "error": "Message field is required and cannot be empty",
                    "status": "error"
                }), 400

            # Extract optional fields
            timestamp = data.get('timestamp', int(time.time() * 1000))
            client = data.get('client', 'unknown')
            conversation_id = data.get('conversation_id')
            use_rag = data.get('use_rag', False)
            session_id = data.get('session_id', 'default_session')

            # Log request details
            rag_status = "with RAG" if use_rag else "standard"
            current_app.logger.info(f"🔍 Chat request from {client}:{session_id}: {len(message)} characters ({rag_status})")

            # Process message through controller
            response_data = ChatController.process_message(message, client, conversation_id, use_rag, session_id)

            # Check if processing was successful
            if response_data.get('status') == 'error':
                return jsonify(response_data), 400

            # Return successful response
            return jsonify(response_data), 200

        except Exception as e:
            current_app.logger.error(f"❌ Error in chat handler: {str(e)}")
            return jsonify({
                "error": f"Internal server error: {str(e)}",
                "status": "error",
                "timestamp": int(time.time() * 1000)
            }), 500

    @staticmethod
    def handle_chat_stats():
        """
        Handle GET /api/chat/stats requests
        
        Returns:
            Flask Response: JSON response with chat statistics
        """
        try:
            stats = ChatController.get_chat_stats()
            return jsonify({
                "status": "success",
                "data": stats,
                "timestamp": int(time.time() * 1000)
            }), 200

        except Exception as e:
            print(f"❌ Error getting chat stats: {str(e)}")
            return jsonify({
                "error": f"Failed to get chat statistics: {str(e)}",
                "status": "error",
                "timestamp": int(time.time() * 1000)
            }), 500

    @staticmethod
    def handle_document_search():
        """
        Handle POST /api/chat/search requests - Search documents

        Expected JSON payload:
        {
            "query": "search query text",
            "limit": 5  # optional
        }

        Returns:
            Flask Response: JSON response with search results
        """
        try:
            # Validate request content type
            if not request.is_json:
                return jsonify({
                    "error": "Content-Type must be application/json",
                    "status": "error"
                }), 400

            # Get JSON data from request
            data = request.get_json()

            if not data:
                return jsonify({
                    "error": "No JSON data provided",
                    "status": "error"
                }), 400

            # Extract and validate required fields
            query = data.get('query', '').strip()
            if not query:
                return jsonify({
                    "error": "Query field is required and cannot be empty",
                    "status": "error"
                }), 400

            # Extract optional fields
            limit = data.get('limit', 5)

            # Validate limit
            if not isinstance(limit, int) or limit < 1 or limit > 20:
                return jsonify({
                    "error": "Limit must be an integer between 1 and 20",
                    "status": "error"
                }), 400

            current_app.logger.info(f"🔍 Document search request: {query[:50]}...")

            # Search documents through controller
            search_result = ChatController.search_documents(query, limit)

            # Check if search was successful
            if search_result.get('status') == 'error':
                return jsonify(search_result), 400

            # Return successful response
            return jsonify(search_result), 200

        except Exception as e:
            current_app.logger.error(f"❌ Error in document search handler: {str(e)}")
            return jsonify({
                "error": f"Internal server error: {str(e)}",
                "status": "error",
                "timestamp": int(time.time() * 1000)
            }), 500

    @staticmethod
    def handle_rag_context():
        """
        Handle POST /api/chat/context requests - Build RAG context

        Expected JSON payload:
        {
            "query": "query for context building",
            "max_chunks": 3  # optional
        }

        Returns:
            Flask Response: JSON response with RAG context
        """
        try:
            # Validate request content type
            if not request.is_json:
                return jsonify({
                    "error": "Content-Type must be application/json",
                    "status": "error"
                }), 400

            # Get JSON data from request
            data = request.get_json()

            if not data:
                return jsonify({
                    "error": "No JSON data provided",
                    "status": "error"
                }), 400

            # Extract and validate required fields
            query = data.get('query', '').strip()
            if not query:
                return jsonify({
                    "error": "Query field is required and cannot be empty",
                    "status": "error"
                }), 400

            # Extract optional fields
            max_chunks = data.get('max_chunks', 3)

            # Validate max_chunks
            if not isinstance(max_chunks, int) or max_chunks < 1 or max_chunks > 10:
                return jsonify({
                    "error": "max_chunks must be an integer between 1 and 10",
                    "status": "error"
                }), 400

            current_app.logger.info(f"🧠 RAG context request: {query[:50]}...")

            # Build RAG context through controller
            context_result = ChatController.build_rag_context(query, max_chunks)

            # Check if context building was successful
            if context_result.get('status') == 'error':
                return jsonify(context_result), 400

            # Return successful response
            return jsonify(context_result), 200

        except Exception as e:
            current_app.logger.error(f"❌ Error in RAG context handler: {str(e)}")
            return jsonify({
                "error": f"Internal server error: {str(e)}",
                "status": "error",
                "timestamp": int(time.time() * 1000)
            }), 500

    @staticmethod
    def handle_chat_test():
        """
        Handle GET /api/chat/test requests - for testing connectivity
        
        Returns:
            Flask Response: JSON response with test data
        """
        try:
            return jsonify({
                "status": "success",
                "message": "Chat endpoint is working correctly! 🎉",
                "test_data": {
                    "server_time": int(time.time() * 1000),
                    "version": current_app.config.get('API_VERSION', '2.0.0'),
                    "endpoints": {
                        "chat": "POST /api/chat",
                        "stats": "GET /api/chat/stats",
                        "test": "GET /api/chat/test"
                    }
                },
                "timestamp": int(time.time() * 1000)
            }), 200

        except Exception as e:
            print(f"❌ Error in chat test: {str(e)}")
            return jsonify({
                "error": f"Chat test failed: {str(e)}",
                "status": "error",
                "timestamp": int(time.time() * 1000)
            }), 500

    @staticmethod
    def handle_set_client_context():
        """
        Handle POST /api/chat/set-context requests
        Set context using client-stored document IDs

        Returns:
            Flask Response: JSON response with context setup status
        """
        try:
            # Validate request content type
            if not request.is_json:
                return jsonify({
                    "error": "Content-Type must be application/json",
                    "status": "error"
                }), 400

            # Get JSON data from request
            data = request.get_json()
            if not data:
                return jsonify({
                    "error": "No JSON data provided",
                    "status": "error"
                }), 400

            # Extract and validate required fields
            document_ids = data.get('document_ids', [])
            if not isinstance(document_ids, list) or not document_ids:
                return jsonify({
                    "error": "document_ids field is required and must be a non-empty array",
                    "status": "error"
                }), 400

            # Extract optional fields
            client_id = data.get('client_id', 'default_client')
            session_id = data.get('session_id', 'default_session')

            # Set client context using ChatController
            result = ChatController.set_client_context(
                document_ids=document_ids,
                client_id=client_id,
                session_id=session_id
            )

            return jsonify(result), 200

        except Exception as e:
            print(f"❌ Error setting client context: {str(e)}")
            return jsonify({
                "error": f"Failed to set client context: {str(e)}",
                "status": "error",
                "timestamp": int(time.time() * 1000)
            }), 500

    @staticmethod
    def handle_context_status():
        """
        Handle GET /api/chat/context-status requests
        Get current context status

        Returns:
            Flask Response: JSON response with context status
        """
        try:
            # Extract query parameters
            client_id = request.args.get('client_id', 'default_client')
            session_id = request.args.get('session_id', 'default_session')

            # Get context status using ChatController
            result = ChatController.get_context_status(
                client_id=client_id,
                session_id=session_id
            )

            return jsonify(result), 200

        except Exception as e:
            print(f"❌ Error getting context status: {str(e)}")
            return jsonify({
                "error": f"Failed to get context status: {str(e)}",
                "status": "error",
                "timestamp": int(time.time() * 1000)
            }), 500

    @staticmethod
    def handle_clear_context():
        """
        Handle POST /api/chat/clear-context requests
        Clear current client context

        Returns:
            Flask Response: JSON response with clear operation status
        """
        try:
            # Validate request content type
            if not request.is_json:
                return jsonify({
                    "error": "Content-Type must be application/json",
                    "status": "error"
                }), 400

            # Get JSON data from request
            data = request.get_json()
            if not data:
                data = {}  # Allow empty JSON for clear operation

            # Extract optional fields
            client_id = data.get('client_id', 'default_client')
            session_id = data.get('session_id', 'default_session')

            # Clear context using ChatController
            result = ChatController.clear_context(
                client_id=client_id,
                session_id=session_id
            )

            return jsonify(result), 200

        except Exception as e:
            print(f"❌ Error clearing context: {str(e)}")
            return jsonify({
                "error": f"Failed to clear context: {str(e)}",
                "status": "error",
                "timestamp": int(time.time() * 1000)
            }), 500

    @staticmethod
    def handle_stream_chat():
        """
        Handle POST /api/chat/stream requests - Stream chat response with chunked processing

        Returns:
            Flask Response: Server-Sent Events stream
        """
        try:
            # Validate request
            if not request.is_json:
                return Response(
                    json.dumps({"error": "Request must be JSON"}),
                    status=400,
                    mimetype='application/json'
                )

            data = request.get_json()
            if not data:
                return Response(
                    json.dumps({"error": "Empty request body"}),
                    status=400,
                    mimetype='application/json'
                )

            # Extract required fields
            message = data.get('message', '').strip()
            if not message:
                return Response(
                    json.dumps({"error": "Message is required"}),
                    status=400,
                    mimetype='application/json'
                )

            # Extract optional fields
            session_id = data.get('session_id', 'default_session')
            client = data.get('client', 'web')
            use_rag = data.get('use_rag', True)

            current_app.logger.info(f"🔄 Starting streaming chat for {client}:{session_id}: {message[:50]}...")

            # Create streaming generator
            def generate():
                try:
                    for chunk in ChatController.stream_message(message, client, session_id, use_rag):
                        # Format as Server-Sent Events
                        yield f"data: {json.dumps(chunk)}\n\n"
                except Exception as e:
                    current_app.logger.error(f"Error in streaming generator: {str(e)}")
                    error_chunk = {
                        "type": "error",
                        "error": str(e),
                        "timestamp": int(time.time() * 1000)
                    }
                    yield f"data: {json.dumps(error_chunk)}\n\n"

            return Response(
                stream_with_context(generate()),
                mimetype='text/event-stream',
                headers={
                    'Cache-Control': 'no-cache',
                    'Connection': 'keep-alive',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type, Accept, Authorization, Origin',
                    'Access-Control-Allow-Methods': 'POST, OPTIONS'
                }
            )

        except Exception as e:
            current_app.logger.error(f"❌ Error in stream_chat: {str(e)}")
            return Response(
                json.dumps({"error": f"Streaming failed: {str(e)}"}),
                status=500,
                mimetype='application/json'
            )

    @staticmethod
    def handle_stream_chat_direct():
        """
        Handle POST /api/chat/stream-direct requests - Stream chat response without RAG

        Returns:
            Flask Response: Server-Sent Events stream
        """
        try:
            # Validate request
            if not request.is_json:
                return Response(
                    json.dumps({"error": "Request must be JSON"}),
                    status=400,
                    mimetype='application/json'
                )

            data = request.get_json()
            if not data:
                return Response(
                    json.dumps({"error": "Empty request body"}),
                    status=400,
                    mimetype='application/json'
                )

            # Extract required fields
            message = data.get('message', '').strip()
            if not message:
                return Response(
                    json.dumps({"error": "Message is required"}),
                    status=400,
                    mimetype='application/json'
                )

            # Extract optional fields
            session_id = data.get('session_id', 'default_session')
            client = data.get('client', 'web')

            current_app.logger.info(f"🔄 Starting direct streaming chat for {client}:{session_id}: {message[:50]}...")

            # Create streaming generator
            def generate():
                try:
                    for chunk in ChatController.stream_message(message, client, session_id, use_rag=False):
                        # Format as Server-Sent Events
                        yield f"data: {json.dumps(chunk)}\n\n"
                except Exception as e:
                    current_app.logger.error(f"Error in direct streaming generator: {str(e)}")
                    error_chunk = {
                        "type": "error",
                        "error": str(e),
                        "timestamp": int(time.time() * 1000)
                    }
                    yield f"data: {json.dumps(error_chunk)}\n\n"

            return Response(
                stream_with_context(generate()),
                mimetype='text/event-stream',
                headers={
                    'Cache-Control': 'no-cache',
                    'Connection': 'keep-alive',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type, Accept, Authorization, Origin',
                    'Access-Control-Allow-Methods': 'POST, OPTIONS'
                }
            )

        except Exception as e:
            current_app.logger.error(f"❌ Error in stream_chat_direct: {str(e)}")
            return Response(
                json.dumps({"error": f"Direct streaming failed: {str(e)}"}),
                status=500,
                mimetype='application/json'
            )
