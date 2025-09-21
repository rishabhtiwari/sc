"""
Chat Controller - Business logic for chat operations
"""

import time
import random
from typing import Dict, Any, Optional

from flask import current_app
from utils.document_detector import document_detector
from services.ocr_service_client import ocr_client


class ChatController:
    """
    Controller for handling chat-related business logic
    """
    
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
    
    @staticmethod
    def process_message(message: str, client: str = "unknown") -> Dict[str, Any]:
        """
        Process a chat message and generate a response
        
        Args:
            message (str): The user's message
            client (str): The client identifier
            
        Returns:
            Dict[str, Any]: Response data
        """
        try:
            # Log the incoming message
            print(f"📨 Received message from {client}: {message}")
            
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
            
            # Simulate processing time
            delay = current_app.config.get('CHAT_RESPONSE_DELAY', 0.5)
            if delay > 0:
                time.sleep(delay)
            
            # Check if this is a document-related query
            document_intent = document_detector.extract_intent(message)

            # Generate response based on message content
            if document_intent['is_document_query']:
                response_message = document_detector.generate_document_response(document_intent)
                # Add OCR service status
                ocr_status = ocr_client.health_check()
                if ocr_status['status'] == 'healthy':
                    response_message += "\n\n✅ OCR service is ready and operational!"
                else:
                    response_message += "\n\n⚠️ OCR service is currently unavailable. Please try again later."
            else:
                response_message = ChatController._generate_response(message)
            
            # Create response data
            response_data = {
                "message": response_message,
                "timestamp": int(time.time() * 1000),
                "status": "success",
                "original_message": message,
                "client": client
            }
            
            print(f"📤 Sending response: {response_message}")
            return response_data
            
        except Exception as e:
            print(f"❌ Error processing message: {str(e)}")
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
