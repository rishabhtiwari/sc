"""
Base parser class for news API responses
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime

class BaseNewsParser(ABC):
    """
    Abstract base class for parsing news API responses
    Each news provider should implement this interface
    """
    
    def __init__(self, partner_name: str):
        self.partner_name = partner_name
    
    @abstractmethod
    def parse_response(self, response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse the API response and return standardized news articles
        
        Args:
            response_data: Raw API response data
            
        Returns:
            List of standardized news articles
        """
        pass
    
    @abstractmethod
    def validate_response(self, response_data: Dict[str, Any]) -> bool:
        """
        Validate if the response is valid and contains news data
        
        Args:
            response_data: Raw API response data
            
        Returns:
            True if response is valid, False otherwise
        """
        pass
    
    def standardize_article(self, raw_article: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert raw article data to standardized format
        This method can be overridden by specific parsers if needed
        
        Args:
            raw_article: Raw article data from API
            
        Returns:
            Standardized article dictionary
        """
        return {
            'id': self.extract_article_id(raw_article),
            'title': self.extract_title(raw_article),
            'description': self.extract_description(raw_article),
            'content': self.extract_content(raw_article),
            'url': self.extract_url(raw_article),
            'image': self.extract_image(raw_article),
            'publishedAt': self.extract_published_date(raw_article),
            'lang': self.extract_language(raw_article),
            'source': self.extract_source(raw_article),
            'status': 'published',
            'short_summary': self.generate_short_summary(raw_article),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
    
    @abstractmethod
    def extract_article_id(self, article: Dict[str, Any]) -> str:
        """Extract unique article identifier"""
        pass
    
    @abstractmethod
    def extract_title(self, article: Dict[str, Any]) -> str:
        """Extract article title"""
        pass
    
    @abstractmethod
    def extract_description(self, article: Dict[str, Any]) -> str:
        """Extract article description"""
        pass
    
    @abstractmethod
    def extract_content(self, article: Dict[str, Any]) -> str:
        """Extract article content"""
        pass
    
    @abstractmethod
    def extract_url(self, article: Dict[str, Any]) -> str:
        """Extract article URL"""
        pass
    
    @abstractmethod
    def extract_image(self, article: Dict[str, Any]) -> Optional[str]:
        """Extract article image URL"""
        pass
    
    @abstractmethod
    def extract_published_date(self, article: Dict[str, Any]) -> str:
        """Extract article published date"""
        pass
    
    @abstractmethod
    def extract_language(self, article: Dict[str, Any]) -> str:
        """Extract article language"""
        pass
    
    @abstractmethod
    def extract_source(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """Extract article source information"""
        pass
    
    def generate_short_summary(self, article: Dict[str, Any]) -> str:
        """
        Generate a short summary of the article
        Default implementation uses description, can be overridden
        """
        description = self.extract_description(article)
        if description and len(description) > 200:
            return description[:197] + "..."
        return description or ""
    
    def get_parser_info(self) -> Dict[str, str]:
        """Get information about this parser"""
        return {
            'partner_name': self.partner_name,
            'parser_class': self.__class__.__name__,
            'version': '1.0'
        }
