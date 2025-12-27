"""
Prompt Template Handler - Manages prompt template loading and LLM generation with JSON output

This module handles:
- Loading prompt templates from database
- Formatting prompts with context variables
- Calling LLM service with JSON mode
- Validating JSON output against schema
- Retry logic for malformed responses
"""

import logging
import json
import re
import requests
import jsonschema
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class PromptTemplateHandler:
    """
    Handles prompt template-based content generation with structured JSON output
    """
    
    def __init__(self, prompt_templates_collection, llm_service_url):
        """
        Initialize the handler
        
        Args:
            prompt_templates_collection: MongoDB collection for prompt templates
            llm_service_url: URL of the LLM service
        """
        self.prompt_templates_collection = prompt_templates_collection
        self.llm_service_url = llm_service_url
    
    def get_template(self, template_id: str, customer_id: str = 'default') -> Optional[Dict]:
        """
        Get a prompt template by ID
        
        Args:
            template_id: Template ID to fetch
            customer_id: Customer ID for multi-tenancy
            
        Returns:
            dict: Template document or None if not found
        """
        template = self.prompt_templates_collection.find_one({
            'template_id': template_id,
            '$or': [
                {'customer_id': customer_id},
                {'customer_id': 'customer_system', 'is_system_default': True}
            ],
            'is_active': True
        })
        
        if not template:
            logger.warning(f"Template {template_id} not found for customer {customer_id}")
        
        return template
    
    def format_prompt(self, template: Dict, context: Dict) -> str:
        """
        Format a prompt template with context variables

        This method uses a safe substitution approach that only replaces
        template variables defined in the template's 'variables' list,
        leaving other curly braces (like JSON structures) untouched.

        Args:
            template: Template document with prompt_text
            context: Dict of variables to substitute

        Returns:
            str: Formatted prompt with output schema appended
        """
        prompt_text = template['prompt_text']

        # Build a complete context with all template variables
        # Start with an empty dict for all variables
        complete_context = {}

        # Get all variables defined in the template
        template_vars = template.get('variables', [])

        # First, fill in defaults for all variables
        for var in template_vars:
            var_name = var['name']
            if var.get('default'):
                complete_context[var_name] = var['default']
            else:
                # Use empty string as fallback for missing variables
                complete_context[var_name] = ''

        # Then override with provided context values
        complete_context.update(context)

        # Check for required variables that are still empty
        required_vars = [
            var['name'] for var in template_vars
            if var.get('required', False)
        ]

        missing_required = [
            var for var in required_vars
            if not complete_context.get(var)
        ]

        if missing_required:
            logger.warning(f"Missing required variables: {missing_required}")
            # For required variables without values, we'll still proceed
            # but log a warning. The LLM might still generate good output.

        # Safe substitution: Only replace template variables, not all {placeholders}
        # This prevents issues with JSON structures in the prompt text
        formatted_prompt = prompt_text

        # Get list of variable names from template definition
        var_names = [var['name'] for var in template_vars]

        # Only replace placeholders that match defined template variables
        for var_name in var_names:
            placeholder = '{' + var_name + '}'
            value = str(complete_context.get(var_name, ''))
            formatted_prompt = formatted_prompt.replace(placeholder, value)

        # Check if there are any remaining {variable} patterns that look like
        # template variables but weren't in the variables list
        # Pattern: {word_characters} but not JSON-like patterns
        remaining_vars = re.findall(r'\{([a-zA-Z_][a-zA-Z0-9_]*)\}', formatted_prompt)

        if remaining_vars:
            logger.warning(
                f"Prompt text contains placeholders not in template variables: {remaining_vars}"
            )
            logger.warning(
                f"Defined template variables: {var_names}"
            )
            # Don't raise an error - these might be intentional (e.g., examples in the prompt)

        # Append output schema to the prompt so LLM knows what JSON structure to generate
        output_schema = template.get('output_schema', {})
        if output_schema:
            # Generate a JSON example from the schema
            schema_example = self._generate_schema_example(output_schema)
            formatted_prompt += f"\n\n**IMPORTANT: You must respond with ONLY valid JSON matching this exact structure:**\n\n```json\n{schema_example}\n```\n\nGenerate the JSON response now (no additional text, just the JSON):"

        return formatted_prompt

    def _generate_schema_example(self, schema: Dict) -> str:
        """
        Generate a JSON example from a JSON schema

        Args:
            schema: JSON schema object

        Returns:
            str: JSON string example
        """
        import json

        def generate_value(prop_schema):
            """Generate example value based on schema type"""
            prop_type = prop_schema.get('type', 'string')

            if prop_type == 'string':
                # Use description or a placeholder
                desc = prop_schema.get('description', 'string value')
                return f"<{desc}>"
            elif prop_type == 'number' or prop_type == 'integer':
                return 0
            elif prop_type == 'boolean':
                return True
            elif prop_type == 'array':
                items_schema = prop_schema.get('items', {})
                # Generate one example item
                example_item = generate_value(items_schema)
                return [example_item]
            elif prop_type == 'object':
                # Recursively generate object
                return generate_object(prop_schema)
            else:
                return None

        def generate_object(obj_schema):
            """Generate example object from schema"""
            result = {}
            properties = obj_schema.get('properties', {})

            for prop_name, prop_schema in properties.items():
                result[prop_name] = generate_value(prop_schema)

            return result

        # Generate the example
        example = generate_object(schema)

        # Convert to formatted JSON string
        return json.dumps(example, indent=2)

    def generate_with_json_output(
        self,
        template: Dict,
        context: Dict,
        max_retries: int = 3,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """
        Generate content using LLM with JSON output validation
        
        Args:
            template: Template document
            context: Context variables for prompt formatting
            max_retries: Maximum number of retry attempts
            temperature: LLM temperature parameter
            max_tokens: Maximum tokens to generate
            
        Returns:
            dict: Result with status, data (parsed JSON), and raw_response
        """
        # Format the prompt
        prompt = self.format_prompt(template, context)
        output_schema = template['output_schema']
        
        logger.info(f"Generating content with template: {template['template_id']}")
        logger.info(f"Prompt length: {len(prompt)} characters")
        
        for attempt in range(max_retries):
            try:
                # Call LLM service
                response = requests.post(
                    f"{self.llm_service_url}/llm/generate",
                    json={
                        "query": prompt,
                        "use_rag": False,
                        "detect_code": False,
                        "temperature": temperature,
                        "max_tokens": max_tokens
                    },
                    timeout=120
                )
                
                if response.status_code != 200:
                    logger.error(f"LLM service returned {response.status_code}: {response.text}")
                    if attempt < max_retries - 1:
                        continue
                    return {
                        'status': 'error',
                        'message': f'LLM service error: {response.status_code}',
                        'details': response.text
                    }
                
                result = response.json()
                raw_response = result.get('response', '').strip()
                
                logger.info(f"LLM response length: {len(raw_response)} characters")
                
                # Try to extract JSON from the response
                parsed_json = self._extract_json(raw_response)
                
                if not parsed_json:
                    logger.warning(f"Attempt {attempt + 1}: Failed to extract JSON from response")
                    if attempt < max_retries - 1:
                        continue
                    return {
                        'status': 'error',
                        'message': 'Failed to extract valid JSON from LLM response',
                        'raw_response': raw_response
                    }

                # Validate against schema
                try:
                    jsonschema.validate(instance=parsed_json, schema=output_schema)
                    logger.info("✅ JSON output validated successfully against schema")

                    return {
                        'status': 'success',
                        'data': parsed_json,
                        'raw_response': raw_response,
                        'template_id': template['template_id']
                    }

                except jsonschema.ValidationError as e:
                    logger.warning(f"Attempt {attempt + 1}: JSON validation failed: {e.message}")
                    if attempt < max_retries - 1:
                        continue
                    return {
                        'status': 'error',
                        'message': f'JSON validation failed: {e.message}',
                        'data': parsed_json,
                        'raw_response': raw_response
                    }

            except requests.exceptions.RequestException as e:
                logger.error(f"Attempt {attempt + 1}: Request failed: {str(e)}")
                if attempt < max_retries - 1:
                    continue
                return {
                    'status': 'error',
                    'message': f'Request failed: {str(e)}'
                }
            except Exception as e:
                logger.error(f"Attempt {attempt + 1}: Unexpected error: {str(e)}", exc_info=True)
                if attempt < max_retries - 1:
                    continue
                return {
                    'status': 'error',
                    'message': f'Unexpected error: {str(e)}'
                }

        return {
            'status': 'error',
            'message': 'Max retries exceeded'
        }

    def _extract_json(self, text: str) -> Optional[Dict]:
        """
        Extract JSON from LLM response text

        Tries multiple strategies:
        1. Direct JSON parsing
        2. Extract from markdown code blocks
        3. Find JSON object in text

        Args:
            text: Raw text from LLM

        Returns:
            dict: Parsed JSON or None
        """
        # Strategy 1: Try direct parsing
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Strategy 2: Extract from markdown code blocks
        code_block_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
        matches = re.findall(code_block_pattern, text, re.DOTALL)
        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue

        # Strategy 3: Find JSON object in text
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, text, re.DOTALL)
        for match in matches:
            try:
                parsed = json.loads(match)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                continue

        return None

    def convert_json_to_text(self, json_data: Dict) -> str:
        """
        Convert structured JSON output to formatted text with section headings

        This handles common JSON structures from prompt templates and converts them
        to human-readable text format with proper headings.

        Args:
            json_data: Parsed JSON object from LLM

        Returns:
            str: Formatted text representation with headings
        """
        if not isinstance(json_data, dict):
            # If it's not a dict, just convert to string
            return str(json_data)

        # Check for common section-based structures
        section_fields = [
            'opening_hook',
            'product_introduction',
            'key_features',
            'social_proof',
            'call_to_action',
            'introduction',
            'features',
            'benefits',
            'conclusion',
            'body',
            'summary'
        ]

        # Build text from sections with headings
        section_texts = []

        for field in section_fields:
            if field in json_data:
                value = json_data[field]
                section_text = self._format_value_to_text(value)
                if section_text:
                    # Convert field name to readable heading
                    heading = self._field_name_to_heading(field)
                    # Add heading and content
                    section_texts.append(f"## {heading}\n\n{section_text}")

        # If we found sections, join them with double newlines
        if section_texts:
            return '\n\n'.join(section_texts)

        # Fallback: If no known sections found, format all fields with headings
        all_texts = []
        for key, value in json_data.items():
            text = self._format_value_to_text(value)
            if text:
                heading = self._field_name_to_heading(key)
                all_texts.append(f"## {heading}\n\n{text}")

        return '\n\n'.join(all_texts) if all_texts else str(json_data)

    def _field_name_to_heading(self, field_name: str) -> str:
        """
        Convert a field name to a readable heading

        Examples:
            'opening_hook' -> 'Opening Hook'
            'product_introduction' -> 'Product Introduction'
            'key_features' -> 'Key Features'

        Args:
            field_name: Field name from JSON

        Returns:
            str: Formatted heading
        """
        # Replace underscores with spaces and title case
        return field_name.replace('_', ' ').title()

    def _format_value_to_text(self, value: Any) -> str:
        """
        Format a single value (string, array, or object) to text

        Args:
            value: Value to format

        Returns:
            str: Formatted text
        """
        if isinstance(value, str):
            return value

        elif isinstance(value, list):
            # Handle array of items
            item_texts = []
            for item in value:
                if isinstance(item, str):
                    item_texts.append(item)
                elif isinstance(item, dict):
                    # Handle objects in array (e.g., key_features with feature_name and description)
                    if 'feature_name' in item and 'description' in item:
                        item_texts.append(f"{item['feature_name']}: {item['description']}")
                    elif 'name' in item and 'description' in item:
                        item_texts.append(f"{item['name']}: {item['description']}")
                    elif 'title' in item and 'content' in item:
                        item_texts.append(f"{item['title']}: {item['content']}")
                    else:
                        # Generic object: join all string values
                        obj_values = [str(v) for v in item.values() if v]
                        if obj_values:
                            item_texts.append(': '.join(obj_values))

            return '\n'.join(item_texts) if item_texts else ''

        elif isinstance(value, dict):
            # Handle nested objects
            obj_texts = []
            for k, v in value.items():
                text = self._format_value_to_text(v)
                if text:
                    obj_texts.append(text)
            return '\n'.join(obj_texts) if obj_texts else ''

        else:
            # For other types (numbers, booleans, etc.), convert to string
            return str(value) if value is not None else ''

