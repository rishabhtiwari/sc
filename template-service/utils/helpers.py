"""
Helper utility functions for template service
"""
import re
from typing import Dict, Any, Tuple


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """
    Convert hex color to RGB tuple
    
    Args:
        hex_color: Hex color string (e.g., "#FF0000" or "FF0000")
    
    Returns:
        RGB tuple (r, g, b)
    """
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    """
    Convert RGB tuple to hex color
    
    Args:
        rgb: RGB tuple (r, g, b)
    
    Returns:
        Hex color string (e.g., "#FF0000")
    """
    return '#{:02x}{:02x}{:02x}'.format(*rgb)


def resolve_position(position: Any) -> Any:
    """
    Resolve position string to coordinates
    
    Args:
        position: Position string ('top-left', 'center', etc.) or dict with x, y
    
    Returns:
        Position tuple or string for MoviePy
    """
    if isinstance(position, dict):
        return (position.get('x', 0), position.get('y', 0))
    
    # Position strings that MoviePy understands
    valid_positions = [
        'center', 'top', 'bottom', 'left', 'right',
        'top-left', 'top-right', 'bottom-left', 'bottom-right'
    ]
    
    if position in valid_positions:
        return position
    
    # Default to center
    return 'center'


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries
    
    Args:
        base: Base dictionary
        override: Override dictionary
    
    Returns:
        Merged dictionary
    """
    result = base.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    
    return result


def substitute_variables(template_str: str, variables: Dict[str, Any]) -> str:
    """
    Substitute {{variable}} placeholders in string
    Supports both simple variables {{var}} and indexed arrays {{var[0]}}

    Args:
        template_str: String with {{placeholders}}
        variables: Dictionary of variable values

    Returns:
        String with substituted values
    """
    def replace_var(match):
        var_name = match.group(1)
        index_str = match.group(2)

        # Handle indexed array access: {{var_name[0]}}
        if index_str:
            try:
                index = int(index_str)
                var_value = variables.get(var_name)
                if isinstance(var_value, list) and 0 <= index < len(var_value):
                    return str(var_value[index])
            except (ValueError, IndexError):
                pass
            return match.group(0)  # Return original if index invalid

        # Handle simple variable: {{var_name}}
        return str(variables.get(var_name, match.group(0)))

    # Match both {{var}} and {{var[0]}} patterns
    # Pattern: {{word}} or {{word[number]}}
    return re.sub(r'\{\{(\w+)(?:\[(\d+)\])?\}\}', replace_var, template_str)


def validate_color(color: str) -> bool:
    """
    Validate hex color format
    
    Args:
        color: Color string
    
    Returns:
        True if valid hex color
    """
    pattern = r'^#?([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$'
    return bool(re.match(pattern, color))


def validate_url(url: str) -> bool:
    """
    Validate URL format
    
    Args:
        url: URL string
    
    Returns:
        True if valid URL
    """
    pattern = r'^(https?://|/)'
    return bool(re.match(pattern, url))

