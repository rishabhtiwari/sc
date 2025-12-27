"""
Prompt Template Service - Flask Blueprint for managing LLM prompt templates

Handles all prompt template operations:
- CRUD operations (create, read, update, delete)
- List templates by category
- Get system default templates
- Validate template structure
- AI-powered template generation
"""

import logging
import os
import requests
from flask import Blueprint, request, jsonify
from bson import ObjectId
from datetime import datetime
import jsonschema
import json

from common.utils import serialize_document

logger = logging.getLogger(__name__)

# Create Blueprint
prompt_template_bp = Blueprint('prompt_template', __name__, url_prefix='/api/prompt-templates')


def init_prompt_template_service(prompt_templates_collection):
    """
    Initialize prompt template service with dependencies
    
    Args:
        prompt_templates_collection: MongoDB collection for prompt templates
    """
    prompt_template_bp.prompt_templates_collection = prompt_templates_collection
    logger.info("✅ Prompt template service initialized")


# ========== CRUD Operations ==========

@prompt_template_bp.route('', methods=['GET'])
def get_prompt_templates():
    """Get all prompt templates for a customer"""
    try:
        customer_id = request.headers.get('X-Customer-ID', 'default')
        category = request.args.get('category')
        include_system = request.args.get('include_system', 'true').lower() == 'true'
        
        # Build query
        query = {'is_active': True}
        
        if include_system:
            # Include both customer templates and system templates
            query['$or'] = [
                {'customer_id': customer_id},
                {'customer_id': 'customer_system', 'is_system_default': True}
            ]
        else:
            # Only customer templates
            query['customer_id'] = customer_id
        
        if category:
            query['category'] = category
        
        templates = list(prompt_template_bp.prompt_templates_collection.find(query).sort('name', 1))
        
        for template in templates:
            serialize_document(template)
        
        return jsonify({
            'status': 'success',
            'templates': templates,
            'count': len(templates)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting prompt templates: {str(e)}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ========== AI-Powered Template Generation ==========
# NOTE: This route MUST come before /<template_id> routes to avoid matching conflicts

@prompt_template_bp.route('/generate', methods=['POST'])
def generate_prompt_template():
    """
    Generate a prompt template using AI based on user description

    Request body:
    {
        "description": "What the user wants the AI to do"
    }

    Returns:
    {
        "status": "success",
        "data": {
            "template_id": "generated_template_id",
            "name": "Generated Template Name",
            "description": "What this template does",
            "category": "category_name",
            "variables": [...],
            "output_fields": [...],
            "prompt_text": "The complete prompt with {variables}",
            "output_schema": {...}
        }
    }
    """
    try:
        data = request.get_json()
        if not data or 'description' not in data:
            return jsonify({'status': 'error', 'message': 'description is required'}), 400

        user_description = data['description'].strip()
        if not user_description:
            return jsonify({'status': 'error', 'message': 'description cannot be empty'}), 400

        logger.info(f"🤖 Generating prompt template from description: {user_description[:100]}...")

        # Create a meta-prompt to instruct the LLM to generate a prompt template configuration
        meta_prompt = f"""You are an expert prompt engineer. Based on the user's description, generate a complete prompt template configuration.

User's Description:
{user_description}

Generate a JSON object with the following structure:
{{
    "name": "A clear, concise name for this template (max 50 chars)",
    "description": "A brief description of what this template does (max 200 chars)",
    "category": "One of: E-commerce, Social Media, News & Media, Marketing, Product Summary, Section Content, Custom",
    "instruction": "The main instruction/task for the AI (1-2 sentences)",
    "context": "Any context or background information needed (optional, 1-2 sentences)",
    "variables": [
        {{
            "name": "variable_name",
            "type": "text|long_text|number|url|list",
            "description": "What this variable represents",
            "required": true|false,
            "default": "default value if any"
        }}
    ],
    "output_fields": [
        {{
            "name": "field_name",
            "type": "text|long_text|number|list|boolean",
            "description": "What this output field contains",
            "required": true|false,
            "constraints": {{
                "min_length": number (optional),
                "max_length": number (optional),
                "min": number (optional),
                "max": number (optional),
                "pattern": "regex pattern" (optional)
            }}
        }}
    ]
}}

Guidelines:
1. Choose appropriate variable types based on the expected input
2. Include only necessary variables - don't over-complicate
3. Output fields should match what the user wants to generate
4. Set reasonable constraints for output fields
5. Make the instruction clear and specific
6. Category should best match the use case

Return ONLY the JSON object, no additional text."""

        # Call the LLM service to generate the template configuration
        llm_service_url = "http://ichat-llm-service:8083/llm/generate"

        llm_request = {
            "query": meta_prompt,
            "use_rag": False,
            "detect_code": False
        }

        logger.info(f"📤 Calling LLM service at {llm_service_url}")

        try:
            import requests
            llm_response = requests.post(
                llm_service_url,
                json=llm_request,
                timeout=90  # 90 second timeout (LLM generation can take 50-60 seconds)
            )
            llm_response.raise_for_status()
            llm_data = llm_response.json()

            logger.info(f"📥 LLM response status: {llm_response.status_code}")
            logger.info(f"📥 LLM response keys: {list(llm_data.keys())}")

            if llm_data.get('status') != 'success':
                error_msg = llm_data.get('message', 'LLM service returned error')
                logger.error(f"❌ LLM service error: {error_msg}")
                return jsonify({
                    'status': 'error',
                    'message': f'Failed to generate template: {error_msg}'
                }), 500

            # Extract the response - it's directly in llm_data, not nested in 'data'
            generated_text = llm_data.get('response', '').strip()
            logger.info(f"📝 Generated text length: {len(generated_text)}")
            logger.info(f"📝 Generated text preview: {generated_text[:200] if generated_text else 'EMPTY'}")

        except requests.exceptions.Timeout:
            logger.error("⏱️ LLM service request timed out")
            return jsonify({
                'status': 'error',
                'message': 'Template generation timed out. Please try again.'
            }), 504
        except requests.exceptions.RequestException as e:
            logger.error(f"🔌 LLM service connection error: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': f'Failed to connect to LLM service: {str(e)}'
            }), 503

        # Parse the JSON response from LLM
        try:
            # Try to extract JSON from the response (in case LLM added extra text)
            import re
            json_match = re.search(r'\{.*\}', generated_text, re.DOTALL)
            if json_match:
                generated_text = json_match.group(0)

            import json
            template_config = json.loads(generated_text)
            logger.debug(f"✅ Successfully parsed template configuration")

        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse LLM response as JSON: {str(e)}")
            logger.error(f"Response text: {generated_text[:500]}")
            return jsonify({
                'status': 'error',
                'message': 'Failed to parse generated template. Please try again.'
            }), 500

        # Validate required fields in the generated config
        required_fields = ['name', 'description', 'category', 'instruction', 'variables', 'output_fields']
        missing_fields = [field for field in required_fields if field not in template_config]
        if missing_fields:
            logger.error(f"❌ Generated config missing fields: {missing_fields}")
            return jsonify({
                'status': 'error',
                'message': f'Generated template is incomplete. Missing: {", ".join(missing_fields)}'
            }), 500

        # Build the complete prompt_text from instruction, context, and variables
        prompt_parts = []

        # Add instruction
        prompt_parts.append(template_config['instruction'])

        # Add context if provided
        if template_config.get('context'):
            prompt_parts.append(f"\nContext: {template_config['context']}")

        # Add variable placeholders
        if template_config['variables']:
            prompt_parts.append("\n\nInput:")
            for var in template_config['variables']:
                var_name = var['name']
                var_desc = var.get('description', var_name)
                prompt_parts.append(f"- {var_desc}: {{{var_name}}}")

        prompt_text = '\n'.join(prompt_parts)

        # Build the output_schema from output_fields
        output_schema = {
            "type": "object",
            "properties": {},
            "required": []
        }

        for field in template_config['output_fields']:
            field_name = field['name']
            field_type = field['type']
            field_desc = field.get('description', '')

            # Map our field types to JSON schema types
            type_mapping = {
                'text': 'string',
                'long_text': 'string',
                'number': 'number',
                'list': 'array',
                'boolean': 'boolean'
            }

            json_type = type_mapping.get(field_type, 'string')

            field_schema = {
                "type": json_type,
                "description": field_desc
            }

            # Add constraints if provided
            if 'constraints' in field:
                constraints = field['constraints']
                if 'min_length' in constraints:
                    field_schema['minLength'] = constraints['min_length']
                if 'max_length' in constraints:
                    field_schema['maxLength'] = constraints['max_length']
                if 'min' in constraints:
                    field_schema['minimum'] = constraints['min']
                if 'max' in constraints:
                    field_schema['maximum'] = constraints['max']
                if 'pattern' in constraints:
                    field_schema['pattern'] = constraints['pattern']

            output_schema['properties'][field_name] = field_schema

            if field.get('required', False):
                output_schema['required'].append(field_name)

        # Generate a unique template_id
        import uuid
        template_id = f"template_{uuid.uuid4().hex[:12]}"

        # Normalize category to lowercase to match database schema
        category = template_config['category'].lower().replace(' ', '_').replace('&', 'and')
        # Map common variations to valid categories
        category_mapping = {
            'e-commerce': 'ecommerce',
            'e_commerce': 'ecommerce',
            'socialmedia': 'social_media',
            'newsandmedia': 'news',
            'news_and_media': 'news',
            'productsummary': 'product_summary',
            'sectioncontent': 'section_content',
        }
        category = category_mapping.get(category, category)

        # Validate category is in allowed list
        valid_categories = ['ecommerce', 'social_media', 'news', 'marketing', 'product_summary', 'section_content', 'custom']
        if category not in valid_categories:
            logger.warning(f"⚠️ Invalid category '{category}', defaulting to 'custom'")
            category = 'custom'

        # Prepare the response
        result = {
            'template_id': template_id,
            'name': template_config['name'],
            'description': template_config['description'],
            'category': category,
            'variables': template_config['variables'],
            'output_fields': template_config['output_fields'],
            'prompt_text': prompt_text,
            'output_schema': output_schema
        }

        logger.info(f"✅ Successfully generated template: {result['name']}")

        return jsonify({
            'status': 'success',
            'data': result
        }), 200

    except Exception as e:
        logger.error(f"❌ Error generating prompt template: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Failed to generate template: {str(e)}'
        }), 500


@prompt_template_bp.route('/<template_id>', methods=['GET'])
def get_prompt_template(template_id):
    """Get a single prompt template by ID"""
    try:
        customer_id = request.headers.get('X-Customer-ID', 'default')
        
        # Try to find by ObjectId first, then by template_id string
        template = None
        try:
            template = prompt_template_bp.prompt_templates_collection.find_one({
                '_id': ObjectId(template_id)
            })
        except:
            pass
        
        if not template:
            # Try by template_id field
            template = prompt_template_bp.prompt_templates_collection.find_one({
                'template_id': template_id,
                '$or': [
                    {'customer_id': customer_id},
                    {'customer_id': 'customer_system', 'is_system_default': True}
                ]
            })
        
        if not template:
            return jsonify({
                'status': 'error',
                'message': 'Prompt template not found'
            }), 404
        
        serialize_document(template)
        
        return jsonify({
            'status': 'success',
            'template': template
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting prompt template: {str(e)}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500


@prompt_template_bp.route('', methods=['POST'])
def create_prompt_template():
    """Create a new prompt template"""
    try:
        customer_id = request.headers.get('X-Customer-ID', 'default')
        user_id = request.headers.get('X-User-ID', 'default')
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['template_id', 'name', 'category', 'prompt_text', 'output_schema']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'status': 'error',
                    'message': f'{field} is required'
                }), 400
        
        # Validate output_schema is valid JSON schema
        try:
            jsonschema.Draft7Validator.check_schema(data['output_schema'])
        except jsonschema.SchemaError as e:
            return jsonify({
                'status': 'error',
                'message': f'Invalid JSON schema: {str(e)}'
            }), 400
        
        # Normalize category to lowercase to match database schema
        category = data['category'].lower().replace(' ', '_').replace('&', 'and')
        # Map common variations to valid categories
        category_mapping = {
            'e-commerce': 'ecommerce',
            'e_commerce': 'ecommerce',
            'socialmedia': 'social_media',
            'newsandmedia': 'news',
            'news_and_media': 'news',
            'productsummary': 'product_summary',
            'sectioncontent': 'section_content',
        }
        category = category_mapping.get(category, category)

        # Validate category is in allowed list
        valid_categories = ['ecommerce', 'social_media', 'news', 'marketing', 'product_summary', 'section_content', 'custom']
        if category not in valid_categories:
            logger.warning(f"⚠️ Invalid category '{category}', defaulting to 'custom'")
            category = 'custom'

        # Check if template_id already exists for this customer
        existing = prompt_template_bp.prompt_templates_collection.find_one({
            'template_id': data['template_id'],
            'customer_id': customer_id
        })

        if existing:
            return jsonify({
                'status': 'error',
                'message': 'Template ID already exists'
            }), 400

        # Create template document
        template_doc = {
            'customer_id': customer_id,
            'template_id': data['template_id'],
            'name': data['name'],
            'description': data.get('description', ''),
            'category': category,  # Use normalized category
            'prompt_text': data['prompt_text'],
            'output_schema': data['output_schema'],
            'variables': data.get('variables', []),
            'is_system_default': False,
            'is_active': True,
            'metadata': data.get('metadata', {}),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'created_by': user_id
        }

        result = prompt_template_bp.prompt_templates_collection.insert_one(template_doc)
        template_doc['_id'] = result.inserted_id
        serialize_document(template_doc)

        logger.info(f"Created prompt template: {data['template_id']}")

        return jsonify({
            'status': 'success',
            'message': 'Prompt template created successfully',
            'template': template_doc
        }), 201

    except Exception as e:
        logger.error(f"Error creating prompt template: {str(e)}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500


@prompt_template_bp.route('/<template_id>', methods=['PUT'])
def update_prompt_template(template_id):
    """Update an existing prompt template"""
    try:
        customer_id = request.headers.get('X-Customer-ID', 'default')

        data = request.get_json()

        # Validate output_schema if provided
        if 'output_schema' in data:
            try:
                jsonschema.Draft7Validator.check_schema(data['output_schema'])
            except jsonschema.SchemaError as e:
                return jsonify({
                    'status': 'error',
                    'message': f'Invalid JSON schema: {str(e)}'
                }), 400

        # Build update document
        update_doc = {'updated_at': datetime.utcnow()}

        allowed_fields = ['name', 'description', 'category', 'prompt_text', 'output_schema', 'variables', 'is_active', 'metadata']
        for field in allowed_fields:
            if field in data:
                # Normalize category if it's being updated
                if field == 'category':
                    category = data['category'].lower().replace(' ', '_').replace('&', 'and')
                    # Map common variations to valid categories
                    category_mapping = {
                        'e-commerce': 'ecommerce',
                        'e_commerce': 'ecommerce',
                        'socialmedia': 'social_media',
                        'newsandmedia': 'news',
                        'news_and_media': 'news',
                        'productsummary': 'product_summary',
                        'sectioncontent': 'section_content',
                    }
                    category = category_mapping.get(category, category)

                    # Validate category is in allowed list
                    valid_categories = ['ecommerce', 'social_media', 'news', 'marketing', 'product_summary', 'section_content', 'custom']
                    if category not in valid_categories:
                        logger.warning(f"⚠️ Invalid category '{category}', defaulting to 'custom'")
                        category = 'custom'

                    update_doc[field] = category
                else:
                    update_doc[field] = data[field]

        # Update template (only customer's own templates, not system templates)
        result = prompt_template_bp.prompt_templates_collection.update_one(
            {
                'template_id': template_id,
                'customer_id': customer_id,
                'is_system_default': False
            },
            {'$set': update_doc}
        )

        if result.matched_count == 0:
            return jsonify({
                'status': 'error',
                'message': 'Prompt template not found or cannot be modified'
            }), 404

        # Get updated template
        template = prompt_template_bp.prompt_templates_collection.find_one({
            'template_id': template_id,
            'customer_id': customer_id
        })
        serialize_document(template)

        return jsonify({
            'status': 'success',
            'message': 'Prompt template updated successfully',
            'template': template
        }), 200

    except Exception as e:
        logger.error(f"Error updating prompt template: {str(e)}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500


@prompt_template_bp.route('/<template_id>', methods=['DELETE'])
def delete_prompt_template(template_id):
    """Delete a prompt template (soft delete by setting is_active=False)"""
    try:
        customer_id = request.headers.get('X-Customer-ID', 'default')

        # Soft delete (only customer's own templates, not system templates)
        result = prompt_template_bp.prompt_templates_collection.update_one(
            {
                'template_id': template_id,
                'customer_id': customer_id,
                'is_system_default': False
            },
            {
                '$set': {
                    'is_active': False,
                    'updated_at': datetime.utcnow()
                }
            }
        )

        if result.matched_count == 0:
            return jsonify({
                'status': 'error',
                'message': 'Prompt template not found or cannot be deleted'
            }), 404

        return jsonify({
            'status': 'success',
            'message': 'Prompt template deleted successfully'
        }), 200

    except Exception as e:
        logger.error(f"Error deleting prompt template: {str(e)}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500

