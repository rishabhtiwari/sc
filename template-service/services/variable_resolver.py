"""
Variable Resolver Service
Handles variable substitution and merging for templates
"""
import json
import re
from typing import Dict, Any, Optional
from utils.helpers import deep_merge, substitute_variables


class VariableResolver:
    """Service for resolving template variables"""
    
    def __init__(self, logger=None):
        self.logger = logger
    
    def resolve_template(
        self,
        template: Dict[str, Any],
        variables: Dict[str, Any],
        customer_overrides: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Resolve template with variables and customer overrides
        
        Args:
            template: Template definition with {{placeholders}}
            variables: Variable values to substitute
            customer_overrides: Customer-specific overrides
        
        Returns:
            Resolved template with all variables substituted
        """
        # Step 1: Merge customer overrides into template
        if customer_overrides:
            template = deep_merge(template, customer_overrides)
        
        # Step 2: Convert template to JSON string for substitution
        template_str = json.dumps(template)
        
        # Step 3: Substitute all {{variable}} placeholders
        resolved_str = substitute_variables(template_str, variables)
        
        # Step 4: Parse back to dictionary
        try:
            resolved_template = json.loads(resolved_str)
        except json.JSONDecodeError as e:
            if self.logger:
                self.logger.error(f"Error parsing resolved template: {e}")
            raise ValueError(f"Failed to parse resolved template: {e}")
        
        return resolved_template
    
    def validate_required_variables(
        self,
        template: Dict[str, Any],
        variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate that all required variables are provided
        
        Args:
            template: Template definition
            variables: Provided variables
        
        Returns:
            Dictionary with validation result
        """
        template_variables = template.get('variables', {})
        missing_variables = []
        
        for var_name, var_config in template_variables.items():
            is_required = var_config.get('required', False)
            has_default = 'default' in var_config
            is_provided = var_name in variables
            
            if is_required and not is_provided and not has_default:
                missing_variables.append(var_name)
        
        return {
            'valid': len(missing_variables) == 0,
            'missing_variables': missing_variables
        }
    
    def apply_defaults(
        self,
        template: Dict[str, Any],
        variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply default values for missing variables
        
        Args:
            template: Template definition
            variables: Provided variables
        
        Returns:
            Variables with defaults applied
        """
        template_variables = template.get('variables', {})
        result = variables.copy()
        
        for var_name, var_config in template_variables.items():
            if var_name not in result and 'default' in var_config:
                result[var_name] = var_config['default']
                if self.logger:
                    self.logger.debug(f"Applied default for {var_name}: {var_config['default']}")
        
        return result
    
    def extract_placeholders(self, template: Dict[str, Any]) -> list:
        """
        Extract all {{placeholder}} variables from template
        
        Args:
            template: Template definition
        
        Returns:
            List of placeholder variable names
        """
        template_str = json.dumps(template)
        placeholders = re.findall(r'\{\{(\w+)\}\}', template_str)
        return list(set(placeholders))  # Remove duplicates
    
    def merge_customer_config(
        self,
        template: Dict[str, Any],
        customer_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge customer-specific configuration into template
        
        Args:
            template: Base template
            customer_config: Customer configuration
        
        Returns:
            Merged template
        """
        # Get template-specific overrides
        template_id = template.get('template_id')
        template_overrides = customer_config.get('template_overrides', {}).get(template_id, {})
        
        # Merge template overrides
        merged = deep_merge(template, template_overrides)
        
        # Add customer assets as variables
        assets = customer_config.get('assets', {})
        if 'variables' not in merged:
            merged['variables'] = {}
        
        # Inject customer assets into variables defaults
        for asset_key, asset_value in assets.items():
            if asset_key in merged.get('variables', {}):
                merged['variables'][asset_key]['default'] = asset_value
        
        return merged

