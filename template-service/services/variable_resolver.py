"""
Variable Resolver Service
Handles variable substitution and merging for templates
"""
import json
import re
import copy
from typing import Dict, Any, Optional, List
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

        # Step 2: Expand layers for array variables (multiple images/videos)
        template = self._expand_layers_for_arrays(template, variables)

        # Step 3: Convert template to JSON string for substitution
        template_str = json.dumps(template)

        # Step 4: Substitute all {{variable}} placeholders
        resolved_str = substitute_variables(template_str, variables)

        # Step 5: Parse back to dictionary
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

    def _expand_layers_for_arrays(
        self,
        template: Dict[str, Any],
        variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Expand layers when variables contain arrays (multiple images/videos)

        For example, if product_images = [img1.jpg, img2.jpg], this will:
        1. Find layers using {{product_images}}
        2. Create multiple sequential layers, one for each image
        3. Adjust timing so they appear one after another

        Args:
            template: Template definition
            variables: Variable values (may contain arrays)

        Returns:
            Template with expanded layers
        """
        if 'layers' not in template:
            return template

        # Find array variables (images and videos only)
        array_vars = {}
        for var_name, var_value in variables.items():
            if isinstance(var_value, list) and len(var_value) > 0:
                # Check if this is an image or video array
                var_config = template.get('variables', {}).get(var_name, {})
                var_type = var_config.get('type', '')
                if var_type in ['image', 'video']:
                    array_vars[var_name] = var_value
                    if self.logger:
                        self.logger.info(f"Found array variable: {var_name} with {len(var_value)} items")

        if not array_vars:
            # No array variables, return template as-is
            return template

        # Create a copy to avoid modifying original
        expanded_template = copy.deepcopy(template)
        new_layers = []
        total_duration = 0

        # Process each layer
        for layer in expanded_template.get('layers', []):
            layer_expanded = False

            # Check if this layer uses any array variable
            layer_str = json.dumps(layer)
            for var_name, var_values in array_vars.items():
                placeholder = f"{{{{{var_name}}}}}"

                if placeholder in layer_str:
                    # This layer uses an array variable - expand it
                    layer_expanded = True
                    duration_per_item = layer.get('duration', 5)

                    # Calculate duration for each item
                    # If original template duration exists, divide it among items
                    if 'duration' in template:
                        template_duration = template['duration']
                        duration_per_item = template_duration / len(var_values)

                    for idx, var_value in enumerate(var_values):
                        # Create a new layer for each item
                        new_layer = copy.deepcopy(layer)

                        # Update layer ID to be unique
                        original_id = new_layer.get('id', 'layer')
                        new_layer['id'] = f"{original_id}_{idx}"

                        # Set timing for this segment
                        new_layer['start_time'] = idx * duration_per_item
                        new_layer['duration'] = duration_per_item

                        # Replace the placeholder with indexed variable
                        # We'll use a special syntax: {{var_name[0]}}, {{var_name[1]}}, etc.
                        new_layer_str = json.dumps(new_layer)
                        new_layer_str = new_layer_str.replace(
                            placeholder,
                            f"{{{{{var_name}[{idx}]}}}}"
                        )
                        new_layer = json.loads(new_layer_str)

                        # Adjust effects timing if present
                        if 'effects' in new_layer:
                            for effect in new_layer['effects']:
                                if 'start_time' in effect:
                                    # Make effect start times relative to layer start
                                    effect['start_time'] = effect['start_time']

                        new_layers.append(new_layer)

                        if self.logger:
                            self.logger.debug(
                                f"Expanded layer {original_id} -> {new_layer['id']} "
                                f"(start: {idx * duration_per_item}s, duration: {duration_per_item}s)"
                            )

                    # Update total duration after processing all items
                    total_duration = len(var_values) * duration_per_item
                    break  # Only expand for first matching array variable

            if not layer_expanded:
                # Layer doesn't use array variables, keep as-is
                # But adjust duration for background/static layers if we have sequential content
                if total_duration > 0 and layer.get('type') in ['color', 'gradient']:
                    # Background layers should span entire duration
                    layer['start_time'] = 0
                    layer['duration'] = total_duration
                new_layers.append(layer)

        # Update template with expanded layers
        expanded_template['layers'] = new_layers

        # Update total template duration
        if total_duration > 0:
            expanded_template['duration'] = total_duration

        if self.logger:
            self.logger.info(
                f"Expanded template: {len(template.get('layers', []))} layers -> "
                f"{len(new_layers)} layers, duration: {total_duration}s"
            )

        return expanded_template

