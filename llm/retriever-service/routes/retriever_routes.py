"""
Routes for retriever service endpoints
"""
from flask import Blueprint
from controllers.retriever_controller import RetrieverController
from controllers.health_controller import HealthController

# Create blueprint
retriever_bp = Blueprint('retriever', __name__)

# Initialize controllers
retriever_controller = RetrieverController()
health_controller = HealthController()

# Retriever endpoints
@retriever_bp.route('/retrieve/search', methods=['POST'])
def search_documents():
    """Unified search endpoint supporting both hybrid and regular search"""
    response, status_code = retriever_controller.search_documents()
    return response, status_code

@retriever_bp.route('/retrieve/context/<document_ids>', methods=['GET'])
def get_document_context(document_ids):
    """Get context for specific documents"""
    response, status_code = retriever_controller.get_document_context(document_ids)
    return response, status_code

@retriever_bp.route('/retrieve/rag', methods=['POST'])
def build_rag_context():
    """Build RAG context for a query"""
    response, status_code = retriever_controller.build_rag_context()
    return response, status_code

@retriever_bp.route('/retrieve/rag/context-aware', methods=['POST'])
def build_context_aware_rag():
    """Build context-aware RAG using hybrid filtering"""
    response, status_code = retriever_controller.build_context_aware_rag()
    return response, status_code



# Health endpoints
@retriever_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    response, status_code = health_controller.health_check()
    return response, status_code

@retriever_bp.route('/status', methods=['GET'])
@retriever_bp.route('/', methods=['GET'])
def service_info():
    """Service information endpoint"""
    response, status_code = health_controller.service_info()
    return response, status_code
