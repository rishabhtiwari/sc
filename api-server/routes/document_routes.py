"""
Document Routes - URL routing for document processing endpoints
"""

from flask import Blueprint

from handlers.document_handler import DocumentHandler
from handlers.conversion_handler import ConversionHandler

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





@document_bp.route('/documents/convert-format', methods=['POST'])
def convert_document_format():
    """
    POST /api/documents/convert-format - Convert document from one format to another

    Expected form data:
    - file: Document file to convert (PDF, DOCX, TXT)
    - target_format: Target format (pdf|docx|txt)
    - options: Optional conversion parameters (JSON string)

    Returns:
        File download response with converted document
    """
    return ConversionHandler.handle_document_conversion()


@document_bp.route('/documents/conversion-info', methods=['GET'])
def get_conversion_info():
    """
    GET /api/documents/conversion-info - Get supported conversion formats and capabilities

    Returns:
        JSON response with conversion information
    """
    return ConversionHandler.handle_conversion_info()


@document_bp.route('/documents/conversion-test', methods=['GET'])
def test_conversion_endpoints():
    """
    GET /api/documents/conversion-test - Test document conversion endpoints

    Returns:
        JSON response confirming conversion endpoints are operational
    """
    return ConversionHandler.handle_conversion_test()


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
            "convert_format": {
                "method": "POST",
                "url": "/api/documents/convert-format",
                "description": "Convert document from one format to another",
                "parameters": {
                    "file": "Document file to convert (required)",
                    "target_format": "pdf|docx|txt (required)",
                    "options": "Optional conversion parameters (JSON string)"
                }
            },
            "conversion_info": {
                "method": "GET",
                "url": "/api/documents/conversion-info",
                "description": "Get supported conversion formats and capabilities"
            }
        },
        "supported_formats": ["PDF", "DOCX", "PNG", "JPG", "JPEG", "BMP", "TIFF", "WEBP"],
        "supported_languages": ["en", "ch", "fr", "german", "korean", "japan"],
        "output_formats": ["text", "json", "markdown"],
        "max_file_size": "10MB",
        "upload_instructions": "Upload documents via POST /api/documents/upload with multipart form data",
        "timestamp": int(__import__('time').time() * 1000)
    }, 200
