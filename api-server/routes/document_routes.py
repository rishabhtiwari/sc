"""
Document Routes - URL routing for document processing endpoints
"""

from flask import Blueprint

from handlers.document_handler import DocumentHandler

# Create blueprint for document routes
document_bp = Blueprint('documents', __name__)


@document_bp.route('/documents/upload', methods=['POST'])
def upload_document():
    """
    POST /api/documents/upload - Upload and process a document with OCR
    
    Expected form data:
    - file: Document file (PDF, DOCX, PNG, JPG, etc.)
    - output_format: text|json|markdown (optional, default: text)
    - language: en|ch|fr|german|korean|japan (optional, default: en)
    
    Returns:
        JSON response with extracted text and metadata
    """
    return DocumentHandler.handle_document_upload()


@document_bp.route('/documents/formats', methods=['GET'])
def get_supported_formats():
    """
    GET /api/documents/formats - Get supported file formats and languages
    
    Returns:
        JSON response with supported formats information
    """
    return DocumentHandler.handle_get_formats()


@document_bp.route('/documents/status', methods=['GET'])
def get_service_status():
    """
    GET /api/documents/status - Get OCR service status and health
    
    Returns:
        JSON response with service status information
    """
    return DocumentHandler.handle_service_status()


@document_bp.route('/documents/analyze', methods=['POST'])
def analyze_query():
    """
    POST /api/documents/analyze - Analyze text query for document intent
    
    Expected JSON payload:
    {
        "query": "User's text query to analyze"
    }
    
    Returns:
        JSON response with intent analysis and suggestions
    """
    return DocumentHandler.handle_analyze_query()


@document_bp.route('/documents/test', methods=['GET'])
def test_document_endpoints():
    """
    GET /api/documents/test - Test document processing endpoints
    
    Returns:
        JSON response confirming endpoints are operational
    """
    return DocumentHandler.handle_document_test()


@document_bp.route('/documents/ping', methods=['GET'])
def ping_documents():
    """
    GET /api/documents/ping - Simple ping for document service
    
    Returns:
        Simple pong response
    """
    return DocumentHandler.handle_document_test()  # Reuse test handler


# Additional utility routes
@document_bp.route('/documents/help', methods=['GET'])
def get_help():
    """
    GET /api/documents/help - Get help information for document processing
    
    Returns:
        JSON response with usage instructions
    """
    from utils.document_detector import document_detector
    
    return {
        "message": "Document Processing API Help",
        "status": "success",
        "endpoints": {
            "upload": {
                "method": "POST",
                "url": "/api/documents/upload",
                "description": "Upload and process documents with OCR",
                "parameters": {
                    "file": "Document file (required)",
                    "output_format": "text|json|markdown (optional, default: text)",
                    "language": "en|ch|fr|german|korean|japan (optional, default: en)"
                }
            },
            "formats": {
                "method": "GET", 
                "url": "/api/documents/formats",
                "description": "Get supported file formats and languages"
            },
            "status": {
                "method": "GET",
                "url": "/api/documents/status", 
                "description": "Check OCR service health and status"
            },
            "analyze": {
                "method": "POST",
                "url": "/api/documents/analyze",
                "description": "Analyze text for document processing intent"
            }
        },
        "supported_formats": ["PDF", "DOCX", "PNG", "JPG", "JPEG", "BMP", "TIFF", "WEBP"],
        "supported_languages": ["en", "ch", "fr", "german", "korean", "japan"],
        "output_formats": ["text", "json", "markdown"],
        "max_file_size": "10MB",
        "upload_instructions": document_detector.get_upload_instructions(),
        "timestamp": int(__import__('time').time() * 1000)
    }, 200
