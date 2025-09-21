"""
Document Detector - Utility to detect document-related queries and intents
"""

import re
from typing import Dict, Any, List, Optional


class DocumentDetector:
    """
    Utility class to detect document-related queries and extract relevant information
    """
    
    # Keywords that indicate document-related queries
    DOCUMENT_KEYWORDS = {
        'read', 'extract', 'parse', 'analyze', 'scan', 'ocr', 'text', 'document', 
        'file', 'pdf', 'image', 'photo', 'picture', 'screenshot', 'convert',
        'transcribe', 'digitize', 'content', 'words', 'characters', 'handwriting',
        'typed', 'written', 'manuscript', 'paper', 'page', 'sheet'
    }
    
    # Action keywords that suggest OCR processing
    ACTION_KEYWORDS = {
        'read': 'extract text from',
        'extract': 'extract text from',
        'parse': 'parse content from',
        'analyze': 'analyze content in',
        'scan': 'scan and extract text from',
        'ocr': 'perform OCR on',
        'convert': 'convert',
        'transcribe': 'transcribe',
        'digitize': 'digitize'
    }
    
    # File format patterns
    FILE_FORMAT_PATTERNS = [
        r'\b\w+\.(pdf|docx|png|jpg|jpeg|bmp|tiff|webp)\b',
        r'\bpdf\b', r'\bdocx?\b', r'\bimage\b', r'\bphoto\b', r'\bpicture\b'
    ]
    
    @staticmethod
    def is_document_query(message: str) -> bool:
        """
        Check if the message is document-related
        
        Args:
            message (str): User message to analyze
            
        Returns:
            bool: True if message appears to be document-related
        """
        message_lower = message.lower()
        
        # Check for document keywords
        for keyword in DocumentDetector.DOCUMENT_KEYWORDS:
            if keyword in message_lower:
                return True
        
        # Check for file format patterns
        for pattern in DocumentDetector.FILE_FORMAT_PATTERNS:
            if re.search(pattern, message_lower):
                return True
        
        return False
    
    @staticmethod
    def extract_intent(message: str) -> Dict[str, Any]:
        """
        Extract document processing intent from message
        
        Args:
            message (str): User message to analyze
            
        Returns:
            Dict[str, Any]: Intent information
        """
        message_lower = message.lower()
        intent = {
            'is_document_query': False,
            'action': None,
            'suggested_format': 'text',
            'confidence': 0.0,
            'keywords_found': [],
            'file_formats_mentioned': []
        }
        
        # Check if it's a document query
        if not DocumentDetector.is_document_query(message):
            return intent
        
        intent['is_document_query'] = True
        
        # Find keywords
        found_keywords = []
        for keyword in DocumentDetector.DOCUMENT_KEYWORDS:
            if keyword in message_lower:
                found_keywords.append(keyword)
        
        intent['keywords_found'] = found_keywords
        
        # Determine action
        for action, description in DocumentDetector.ACTION_KEYWORDS.items():
            if action in message_lower:
                intent['action'] = description
                break
        
        if not intent['action']:
            intent['action'] = 'process'
        
        # Find file formats mentioned
        file_formats = []
        for pattern in DocumentDetector.FILE_FORMAT_PATTERNS:
            matches = re.findall(pattern, message_lower)
            file_formats.extend(matches)
        
        intent['file_formats_mentioned'] = list(set(file_formats))
        
        # Determine suggested output format
        if any(word in message_lower for word in ['json', 'structured', 'data']):
            intent['suggested_format'] = 'json'
        elif any(word in message_lower for word in ['markdown', 'formatted', 'md']):
            intent['suggested_format'] = 'markdown'
        else:
            intent['suggested_format'] = 'text'
        
        # Calculate confidence based on keyword matches
        confidence = min(len(found_keywords) * 0.3, 1.0)
        if intent['file_formats_mentioned']:
            confidence += 0.2
        if intent['action'] != 'process':
            confidence += 0.1
        
        intent['confidence'] = min(confidence, 1.0)
        
        return intent
    
    @staticmethod
    def generate_document_response(intent: Dict[str, Any]) -> str:
        """
        Generate a response for document-related queries
        
        Args:
            intent (Dict[str, Any]): Document intent information
            
        Returns:
            str: Generated response
        """
        if not intent['is_document_query']:
            return "I can help you with document processing! Please upload a document and I'll extract the text for you."
        
        action = intent.get('action', 'process')
        formats = intent.get('file_formats_mentioned', [])
        
        response_parts = []
        
        # Main response
        if formats:
            format_list = ', '.join(formats).upper()
            response_parts.append(f"I can help you {action} {format_list} documents! 📄")
        else:
            response_parts.append(f"I can help you {action} your documents! 📄")
        
        # Instructions
        response_parts.append(
            "To get started:\n"
            "1. Upload your document (PDF, DOCX, PNG, JPG, etc.)\n"
            "2. I'll automatically extract the text using OCR\n"
            "3. You'll get the content in your preferred format"
        )
        
        # Supported formats
        response_parts.append(
            "📋 Supported formats: PDF, DOCX, PNG, JPG, JPEG, BMP, TIFF, WEBP\n"
            "🌍 Languages: English, Chinese, French, German, Korean, Japanese\n"
            "📤 Output: Text, JSON, or Markdown format"
        )
        
        return "\n\n".join(response_parts)
    
    @staticmethod
    def get_upload_instructions() -> str:
        """
        Get instructions for document upload
        
        Returns:
            str: Upload instructions
        """
        return (
            "📎 **How to upload documents:**\n\n"
            "**Via API:**\n"
            "```\n"
            "POST /api/documents/upload\n"
            "Content-Type: multipart/form-data\n"
            "- file: [your document]\n"
            "- output_format: text|json|markdown\n"
            "- language: en|ch|fr|german|korean|japan\n"
            "```\n\n"
            "**Supported Files:** PDF, DOCX, PNG, JPG, JPEG, BMP, TIFF, WEBP\n"
            "**Max Size:** 10MB\n"
            "**Processing Time:** Usually 2-10 seconds depending on document size"
        )


# Global document detector instance
document_detector = DocumentDetector()
