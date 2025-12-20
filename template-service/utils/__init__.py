"""Utility functions for template service"""

from .logger import setup_logger
from .helpers import (
    hex_to_rgb,
    rgb_to_hex,
    resolve_position,
    deep_merge,
    substitute_variables,
    validate_color,
    validate_url
)

__all__ = [
    'setup_logger',
    'hex_to_rgb',
    'rgb_to_hex',
    'resolve_position',
    'deep_merge',
    'substitute_variables',
    'validate_color',
    'validate_url'
]

