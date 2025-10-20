"""
Factory pattern for creating news parsers based on partner name
"""

from typing import Dict, Type
from .base_parser import BaseNewsParser
from .gnews_parser import GNewsParser

class ParserFactory:
    """
    Factory class for creating appropriate news parsers based on partner name
    """
    
    # Registry of available parsers
    _parsers: Dict[str, Type[BaseNewsParser]] = {
        'gnews': GNewsParser,
    }
    
    @classmethod
    def create_parser(cls, partner_name: str) -> BaseNewsParser:
        """
        Create a parser instance for the given partner

        Args:
            partner_name: Name of the news partner/provider (case insensitive)

        Returns:
            Parser instance for the specified partner

        Raises:
            ValueError: If no parser is available for the partner
        """
        partner_key = partner_name.lower()
        if partner_key not in cls._parsers:
            raise ValueError(f"No parser available for partner: {partner_name}")

        parser_class = cls._parsers[partner_key]
        return parser_class()
    
    @classmethod
    def register_parser(cls, partner_name: str, parser_class: Type[BaseNewsParser]):
        """
        Register a new parser for a partner

        Args:
            partner_name: Name of the news partner/provider (will be stored as lowercase)
            parser_class: Parser class that extends BaseNewsParser
        """
        if not issubclass(parser_class, BaseNewsParser):
            raise ValueError("Parser class must extend BaseNewsParser")

        cls._parsers[partner_name.lower()] = parser_class
    
    @classmethod
    def get_available_partners(cls) -> list:
        """
        Get list of available partners that have parsers
        
        Returns:
            List of partner names
        """
        return list(cls._parsers.keys())
    
    @classmethod
    def is_partner_supported(cls, partner_name: str) -> bool:
        """
        Check if a partner is supported (has a parser)

        Args:
            partner_name: Name of the news partner/provider (case insensitive)

        Returns:
            True if partner is supported, False otherwise
        """
        return partner_name.lower() in cls._parsers
