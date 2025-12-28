"""
Content Generation Service - Generic LLM content generation endpoints

Provides generic content generation capabilities using prompt templates:
- Generate content with prompt templates and variables
- Support for structured JSON output based on template's output_schema
- Independent of specific content types (products, blogs, social media, etc.)
"""

import logging
import os
from flask import Blueprint, request, jsonify
from datetime import datetime

logger = logging.getLogger(__name__)

# Create Blueprint
content_generation_bp = Blueprint('content_generation', __name__, url_prefix='/api/content')


def init_content_generation_service(prompt_template_handler):
    """
    Initialize content generation service with dependencies
    
    Args:
        prompt_template_handler: PromptTemplateHandler instance for LLM generation
    """
    content_generation_bp.prompt_template_handler = prompt_template_handler
    logger.info("✅ Content generation service initialized")


# ========== Generic Content Generation ==========

@content_generation_bp.route('/generate', methods=['POST'])
def generate_content():
    """
    Generic content generation endpoint using prompt templates

    Request Body:
    {
        "template_id": "template_xyz",   // Required
        "template_variables": {          // Variables to fill in the template
            "product_name": "iPhone 15",
            "description": "Latest smartphone...",
            ...
        },
        "temperature": 0.7,              // Optional: LLM temperature
        "max_tokens": 2000               // Optional: max tokens
    }

    Response:
    {
        "status": "success",
        "content": {...},                // Generated content (JSON object)
        "template_id": "template_xyz",
        "generation_time": 1234
    }
    """
    try:
        customer_id = request.headers.get('X-Customer-ID', 'default')
        data = request.get_json()

        # Extract parameters
        template_id = data.get('template_id')
        template_variables = data.get('template_variables', {})
        temperature = data.get('temperature', 0.7)
        max_tokens = data.get('max_tokens', 2000)

        # Validate input
        if not template_id:
            return jsonify({
                'status': 'error',
                'message': 'template_id is required'
            }), 400

        # Generate content
        start_time = datetime.utcnow()

        # Template-based generation
        logger.info(f"Generating content with template: {template_id}")
        logger.info(f"Template variables: {template_variables}")

        # Get template
        template = content_generation_bp.prompt_template_handler.get_template(
            template_id, customer_id
        )

        if not template:
            return jsonify({
                'status': 'error',
                'message': f'Template {template_id} not found'
            }), 404

        # Generate with JSON output
        result = content_generation_bp.prompt_template_handler.generate_with_json_output(
            template=template,
            context=template_variables,
            max_retries=3,
            temperature=temperature,
            max_tokens=max_tokens
        )

        if result['status'] != 'success':
            return jsonify({
                'status': 'error',
                'message': result.get('message', 'Content generation failed')
            }), 500

        # Extract content from result
        # The result contains 'data' (parsed JSON) and 'raw_response'
        content = result['data']

        # SIMPLIFIED: Convert JSON to sections format
        # This ensures frontend always receives { sections: [...] }
        sections = []
        order = 0

        # Iterate through the output schema to maintain field order
        if template.get('output_schema') and template['output_schema'].get('properties'):
            for field_name, field_schema in template['output_schema']['properties'].items():
                if field_name in content:
                    field_value = content[field_name]

                    # Convert field to section
                    section = {
                        'title': field_schema.get('title', field_name.replace('_', ' ').title()),
                        'content': field_value if isinstance(field_value, str) else str(field_value),
                        'order': order,
                        'audio_path': None,
                        'video_path': None,
                        'audio_config': {
                            'speed': 1.0,
                            'voice': 'am_adam',
                            'duration': 0
                        }
                    }
                    sections.append(section)
                    order += 1

        logger.info(f"✅ Converted JSON to {len(sections)} sections")

        # Calculate generation time
        end_time = datetime.utcnow()
        generation_time = int((end_time - start_time).total_seconds() * 1000)

        # SIMPLIFIED: Return only sections format
        return jsonify({
            'status': 'success',
            'sections': sections,            # Sections array for frontend
            'template_id': template_id,
            'generation_time': generation_time
        }), 200
        
    except Exception as e:
        logger.error(f"Error generating content: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

