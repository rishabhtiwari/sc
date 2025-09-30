"""
Routes for LLM service endpoints
"""
from flask import Blueprint
from controllers.llm_controller import LLMController
from controllers.health_controller import HealthController

# Create blueprint
llm_bp = Blueprint('llm', __name__)

# Initialize controllers
llm_controller = LLMController()
health_controller = HealthController()

# LLM endpoints
@llm_bp.route('/llm/generate', methods=['POST'])
def generate_response():
    """Generate response using LLM with optional RAG"""
    return llm_controller.generate_response()

@llm_bp.route('/llm/chat', methods=['POST'])
def chat():
    """Chat endpoint that combines search and generation"""
    return llm_controller.chat()

@llm_bp.route('/llm/search', methods=['POST'])
def search_documents():
    """Search documents using retriever service"""
    return llm_controller.search_documents()

@llm_bp.route('/llm/stream', methods=['POST'])
def stream_response():
    """Stream response using chunked processing"""
    return llm_controller.stream_response()

@llm_bp.route('/llm/stream-chat', methods=['POST'])
def stream_chat():
    """Stream chat response with RAG context"""
    return llm_controller.stream_chat()

# Health endpoints
@llm_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return health_controller.health_check()

@llm_bp.route('/status', methods=['GET'])
@llm_bp.route('/', methods=['GET'])
def service_info():
    """Service information endpoint"""
    return health_controller.service_info()
