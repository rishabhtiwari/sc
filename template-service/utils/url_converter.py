"""
URL Converter Utility
Converts external URLs to internal service URLs for inter-service communication
"""
import os
import re
from typing import Any, Dict, List, Union


class URLConverter:
    """Converts external URLs to internal service URLs"""
    
    def __init__(self, logger=None):
        self.logger = logger

        # Get API server URLs from environment
        self.api_server_internal = os.getenv('API_SERVER_URL', 'http://ichat-api-server:8080')

        # Map of external URL patterns to internal service URLs
        self.url_mappings = {
            # Inventory/Product service - external URL (localhost:8080)
            # Maps to inventory-creation-service (new unified service)
            r'http://localhost:8080/api/ecommerce': os.getenv(
                'INVENTORY_SERVICE_URL',
                'http://ichat-inventory-creation-service:5001/api/ecommerce'
            ),
            # Inventory/Product service - API server internal URL
            r'http://ichat-api-server:8080/api/ecommerce': os.getenv(
                'INVENTORY_SERVICE_URL',
                'http://ichat-inventory-creation-service:5001/api/ecommerce'
            ),
            # Legacy ecommerce service mapping (for backward compatibility)
            r'http://ichat-ecommerce-service:8099/api/ecommerce': os.getenv(
                'INVENTORY_SERVICE_URL',
                'http://ichat-inventory-creation-service:5001/api/ecommerce'
            ),
            # Audio proxy URLs - convert localhost to internal API server
            r'http://localhost:8080/api/audio': f'{self.api_server_internal}/api/audio',
            # Add more service mappings as needed
        }
    
    def convert_url(self, url: str) -> str:
        """
        Convert a single URL from external to internal format
        
        Args:
            url: External URL (e.g., http://localhost:8080/api/ecommerce/...)
            
        Returns:
            Internal service URL (e.g., http://ichat-ecommerce-service:8099/api/ecommerce/...)
        """
        if not isinstance(url, str):
            return url
        
        # Try each mapping pattern
        for external_pattern, internal_base in self.url_mappings.items():
            if re.match(external_pattern, url):
                # Replace the external base with internal base
                converted_url = re.sub(external_pattern, internal_base, url)
                if self.logger and converted_url != url:
                    self.logger.info(f"🔄 Converted URL: {url} -> {converted_url}")
                return converted_url

        # No conversion needed
        if self.logger and url.startswith('http'):
            self.logger.info(f"ℹ️ No URL conversion needed for: {url}")
        return url
    
    def convert_urls_in_object(self, obj: Any) -> Any:
        """
        Recursively convert URLs in an object (dict, list, or string)
        
        Args:
            obj: Object to process (can be dict, list, string, or primitive)
            
        Returns:
            Object with URLs converted
        """
        if isinstance(obj, dict):
            # Process dictionary recursively
            result = {}
            for key, value in obj.items():
                result[key] = self.convert_urls_in_object(value)
            return result
        elif isinstance(obj, list):
            # Process list recursively
            return [self.convert_urls_in_object(item) for item in obj]
        elif isinstance(obj, str):
            # Convert URL if it matches a pattern
            return self.convert_url(obj)
        else:
            # Return primitives (int, float, bool, None) as-is
            return obj
    
    def convert_variables(self, variables: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert URLs in template variables
        
        Args:
            variables: Template variables dictionary
            
        Returns:
            Variables with URLs converted
        """
        if self.logger:
            self.logger.info(f"🔄 Converting URLs in variables: {list(variables.keys())}")
        
        converted = self.convert_urls_in_object(variables)
        
        if self.logger:
            self.logger.info(f"✅ URL conversion complete")
        
        return converted

