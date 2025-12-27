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
        
        Args:
            template: Template document with prompt_text
            context: Dict of variables to substitute
            
        Returns:
            str: Formatted prompt
        """
        prompt_text = template['prompt_text']
        
        # Validate that all required variables are provided
        required_vars = [
            var['name'] for var in template.get('variables', [])
            if var.get('required', False)
        ]
        
        missing_vars = [var for var in required_vars if var not in context]
        if missing_vars:
            logger.warning(f"Missing required variables: {missing_vars}")
            # Fill with defaults or empty strings
            for var in missing_vars:
                var_def = next((v for v in template['variables'] if v['name'] == var), None)
                if var_def and var_def.get('default'):
                    context[var] = var_def['default']
                else:
                    context[var] = ''
        
        # Format the prompt
        try:
            formatted_prompt = prompt_text.format(**context)
            return formatted_prompt
        except KeyError as e:
            logger.error(f"Error formatting prompt: missing variable {e}")
            raise ValueError(f"Missing required variable: {e}")
    
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

