"""
Prompt Template Routes - Generic prompt template management and content generation
These routes are used across different features (products, videos, audio, text generation, etc.)
"""

from flask import Blueprint, jsonify, request
import requests
import logging
import os

from middleware.jwt_middleware import get_request_headers_with_context

# Create prompt template blueprint
prompt_template_bp = Blueprint('prompt_template', __name__)
logger = logging.getLogger(__name__)

# Service URLs
INVENTORY_CREATION_SERVICE_URL = os.getenv(
    'INVENTORY_CREATION_SERVICE_URL',
    'http://ichat-inventory-creation-service:5001'
)


def proxy_to_inventory_service(path, method='GET', json_data=None, params=None):
    """
    Proxy requests to inventory creation service with proper timeout handling

    Args:
        path: API path to call on inventory creation service
        method: HTTP method (GET, POST, PUT, DELETE)
        json_data: JSON data for POST/PUT requests
        params: Query parameters

    Returns:
        tuple: (response_data, status_code)
    """
    try:
        headers = get_request_headers_with_context()
        headers['Content-Type'] = 'application/json'

        # Set timeout based on endpoint
        # - 2 minutes for generation endpoints (LLM can take time)
        # - 30 seconds for CRUD operations
        if '/generate' in path:
            timeout = 120
        else:
            timeout = 30

        url = f'{INVENTORY_CREATION_SERVICE_URL}{path}'
        
        kwargs = {
            'headers': headers,
            'timeout': timeout
        }
        
        if json_data:
            kwargs['json'] = json_data
        if params:
            kwargs['params'] = params
        
        # Make request based on method
        if method == 'GET':
            response = requests.get(url, **kwargs)
        elif method == 'POST':
            response = requests.post(url, **kwargs)
        elif method == 'PUT':
            response = requests.put(url, **kwargs)
        elif method == 'DELETE':
            response = requests.delete(url, **kwargs)
        else:
            return {'status': 'error', 'message': f'Unsupported method: {method}'}, 400
        
        return response.json(), response.status_code
        
    except requests.exceptions.Timeout:
        logger.error(f"❌ Timeout calling inventory creation service: {path}")
        return {'status': 'error', 'message': 'Request timeout'}, 504
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error calling inventory creation service: {str(e)}")
        return {'status': 'error', 'message': str(e)}, 500
    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}")
        return {'status': 'error', 'message': str(e)}, 500


# ========== CRUD Operations ==========

@prompt_template_bp.route('/prompt-templates', methods=['GET'])
def get_prompt_templates():
    """
    GET /api/prompt-templates - Get all prompt templates
    
    Query Parameters:
        category: Filter by category (optional)
        search: Search in name/description (optional)
        page: Page number (optional)
        limit: Items per page (optional)
    
    Returns:
        JSON response with list of templates
    """
    params = request.args.to_dict()
    response_data, status_code = proxy_to_inventory_service(
        '/api/prompt-templates', 
        method='GET',
        params=params
    )
    return jsonify(response_data), status_code


@prompt_template_bp.route('/prompt-templates/<template_id>', methods=['GET'])
def get_prompt_template(template_id):
    """
    GET /api/prompt-templates/<id> - Get a specific prompt template
    
    Args:
        template_id: Template ID
    
    Returns:
        JSON response with template details
    """
    response_data, status_code = proxy_to_inventory_service(
        f'/api/prompt-templates/{template_id}', 
        method='GET'
    )
    return jsonify(response_data), status_code


@prompt_template_bp.route('/prompt-templates', methods=['POST'])
def create_prompt_template():
    """
    POST /api/prompt-templates - Create a new prompt template
    
    Request Body:
        {
            "name": "Template name",
            "description": "Template description",
            "category": "text_generation|product_description|etc",
            "prompt": "Template prompt with {variables}",
            "variables": ["variable1", "variable2"],
            "output_schema": {...}
        }
    
    Returns:
        JSON response with created template
    """
    response_data, status_code = proxy_to_inventory_service(
        '/api/prompt-templates', 
        method='POST', 
        json_data=request.get_json()
    )
    return jsonify(response_data), status_code


@prompt_template_bp.route('/prompt-templates/<template_id>', methods=['PUT'])
def update_prompt_template(template_id):
    """
    PUT /api/prompt-templates/<id> - Update a prompt template

    Args:
        template_id: Template ID

    Request Body: Same as create

    Returns:
        JSON response with updated template
    """
    response_data, status_code = proxy_to_inventory_service(
        f'/api/prompt-templates/{template_id}',
        method='PUT',
        json_data=request.get_json()
    )
    return jsonify(response_data), status_code


@prompt_template_bp.route('/prompt-templates/<template_id>', methods=['DELETE'])
def delete_prompt_template(template_id):
    """
    DELETE /api/prompt-templates/<id> - Delete a prompt template

    Args:
        template_id: Template ID

    Returns:
        JSON response with deletion status
    """
    response_data, status_code = proxy_to_inventory_service(
        f'/api/prompt-templates/{template_id}',
        method='DELETE'
    )
    return jsonify(response_data), status_code


# ========== AI-Powered Operations ==========

@prompt_template_bp.route('/prompt-templates/generate', methods=['POST'])
def generate_prompt_template():
    """
    POST /api/prompt-templates/generate - Generate a NEW prompt template using AI

    This endpoint uses AI to create a template definition based on user description.

    Request Body:
        {
            "description": "Create a template for writing product descriptions",
            "category": "product_description",
            "examples": ["example1", "example2"] (optional)
        }

    Returns:
        JSON response with generated template definition
        {
            "status": "success",
            "template": {
                "name": "Product Description Generator",
                "prompt": "Write a compelling product description for {product_name}...",
                "variables": ["product_name", "features"],
                "output_schema": {...}
            }
        }
    """
    response_data, status_code = proxy_to_inventory_service(
        '/api/prompt-templates/generate',
        method='POST',
        json_data=request.get_json()
    )
    return jsonify(response_data), status_code


@prompt_template_bp.route('/prompt-templates/<template_id>/generate', methods=['POST'])
def generate_content_with_template(template_id):
    """
    POST /api/prompt-templates/<id>/generate - Generate CONTENT using an existing template

    This endpoint uses an existing template to generate actual content.

    Args:
        template_id: Template ID to use for generation

    Request Body:
        {
            "context": {
                "variable1": "value1",
                "variable2": "value2"
            }
        }

    Example:
        POST /api/prompt-templates/text_gen_headline/generate
        Body: {"context": {}}

        Response:
        {
            "status": "success",
            "data": {
                "content": "Unlock Your Potential Today!"
            }
        }

    Returns:
        JSON response with generated content
    """
    response_data, status_code = proxy_to_inventory_service(
        f'/api/prompt-templates/{template_id}/generate',
        method='POST',
        json_data=request.get_json()
    )
    return jsonify(response_data), status_code


# ========== Help & Documentation ==========

@prompt_template_bp.route('/prompt-templates/help', methods=['GET'])
def prompt_template_help():
    """
    GET /api/prompt-templates/help - Get API documentation

    Returns:
        JSON response with API documentation
    """
    return jsonify({
        "service": "Prompt Template API",
        "version": "1.0.0",
        "description": "Generic prompt template management and content generation API",
        "use_cases": [
            "Text generation (headlines, taglines, captions)",
            "Product descriptions",
            "Video scripts",
            "Audio narration",
            "Social media content",
            "Custom AI-powered content generation"
        ],
        "endpoints": {
            "list_templates": {
                "method": "GET",
                "url": "/api/prompt-templates",
                "description": "Get all prompt templates",
                "query_params": {
                    "category": "Filter by category (optional)",
                    "search": "Search in name/description (optional)",
                    "page": "Page number (optional)",
                    "limit": "Items per page (optional)"
                }
            },
            "get_template": {
                "method": "GET",
                "url": "/api/prompt-templates/<id>",
                "description": "Get a specific template"
            },
            "create_template": {
                "method": "POST",
                "url": "/api/prompt-templates",
                "description": "Create a new template"
            },
            "update_template": {
                "method": "PUT",
                "url": "/api/prompt-templates/<id>",
                "description": "Update a template"
            },
            "delete_template": {
                "method": "DELETE",
                "url": "/api/prompt-templates/<id>",
                "description": "Delete a template"
            },
            "generate_template": {
                "method": "POST",
                "url": "/api/prompt-templates/generate",
                "description": "Generate a NEW template using AI"
            },
            "generate_content": {
                "method": "POST",
                "url": "/api/prompt-templates/<id>/generate",
                "description": "Generate CONTENT using an existing template"
            }
        },
        "examples": {
            "list_text_templates": {
                "url": "/api/prompt-templates?category=text_generation",
                "method": "GET"
            },
            "generate_headline": {
                "url": "/api/prompt-templates/text_gen_headline/generate",
                "method": "POST",
                "body": {
                    "context": {}
                }
            },
            "create_custom_template": {
                "url": "/api/prompt-templates",
                "method": "POST",
                "body": {
                    "name": "Product Tagline",
                    "description": "Generate catchy product taglines",
                    "category": "marketing",
                    "prompt": "Create a catchy tagline for {product_name}",
                    "variables": ["product_name"],
                    "output_schema": {
                        "type": "object",
                        "properties": {
                            "content": {"type": "string"}
                        }
                    }
                }
            }
        },
        "status": "success"
    }), 200

