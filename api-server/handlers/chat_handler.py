"""
Chat Handler - HTTP request/response handling for chat endpoints
"""

import time

from flask import (
    request,
    jsonify,
    current_app
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

            # Log request details
            print(f"🔍 Chat request from {client}: {len(message)} characters")

            # Process message through controller
            response_data = ChatController.process_message(message, client)

            # Check if processing was successful
            if response_data.get('status') == 'error':
                return jsonify(response_data), 400

            # Return successful response
            return jsonify(response_data), 200

        except Exception as e:
            print(f"❌ Error in chat handler: {str(e)}")
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
