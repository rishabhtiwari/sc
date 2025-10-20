"""
GNews API response parser
"""

import hashlib
from typing import Dict, List, Any, Optional
from datetime import datetime
from .base_parser import BaseNewsParser

class GNewsParser(BaseNewsParser):
    """
    Parser for GNews API responses
    Handles the specific format of GNews API data
    """
    
    def __init__(self):
        super().__init__("GNews")
    
    def validate_response(self, response_data: Dict[str, Any]) -> bool:
        """
        Validate GNews API response
        
        Args:
            response_data: Raw GNews API response
            
        Returns:
            True if response is valid
        """
        if not isinstance(response_data, dict):
            return False
        
        # Check for required fields in GNews response
        if 'totalArticles' not in response_data:
            return False
        
        if 'articles' not in response_data:
            return False
        
        if not isinstance(response_data['articles'], list):
            return False
        
        return True
    
    def parse_response(self, response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse GNews API response and return standardized articles
        
        Args:
            response_data: Raw GNews API response
            
        Returns:
            List of standardized news articles
        """
        if not self.validate_response(response_data):
            raise ValueError("Invalid GNews API response format")
        
        articles = []
        for raw_article in response_data.get('articles', []):
            try:
                standardized_article = self.standardize_article(raw_article)
                articles.append(standardized_article)
            except Exception as e:
                # Log the error but continue processing other articles
                print(f"Error parsing GNews article: {str(e)}")
                continue
        
        return articles
    
    def extract_article_id(self, article: Dict[str, Any]) -> str:
        """
        Generate unique article ID from URL and title
        GNews doesn't provide unique IDs, so we generate one
        """
        url = article.get('url', '')
        title = article.get('title', '')
        
        # Create a hash from URL and title for unique ID
        content_for_hash = f"{url}_{title}"
        return hashlib.md5(content_for_hash.encode()).hexdigest()
    
    def extract_title(self, article: Dict[str, Any]) -> str:
        """Extract article title from GNews response"""
        return article.get('title', '').strip()
    
    def extract_description(self, article: Dict[str, Any]) -> str:
        """Extract article description from GNews response"""
        return article.get('description', '').strip()
    
    def extract_content(self, article: Dict[str, Any]) -> str:
        """
        Extract article content from GNews response
        GNews provides limited content, usually same as description
        """
        content = article.get('content', '')
        if not content:
            content = article.get('description', '')
        return content.strip()
    
    def extract_url(self, article: Dict[str, Any]) -> str:
        """Extract article URL from GNews response"""
        return article.get('url', '').strip()
    
    def extract_image(self, article: Dict[str, Any]) -> Optional[str]:
        """Extract article image URL from GNews response"""
        image_url = article.get('image')
        return image_url.strip() if image_url else None
    
    def extract_published_date(self, article: Dict[str, Any]) -> str:
        """
        Extract and standardize published date from GNews response
        GNews provides publishedAt in ISO format
        """
        published_at = article.get('publishedAt', '')
        if published_at:
            try:
                # Parse and reformat to ensure consistency
                dt = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                return dt.isoformat()
            except ValueError:
                # If parsing fails, return as-is
                return published_at
        
        # If no published date, use current time
        return datetime.utcnow().isoformat()
    
    def extract_language(self, article: Dict[str, Any]) -> str:
        """
        Extract language from GNews response
        GNews doesn't always provide language, so we use a default
        """
        # GNews doesn't typically include language in article data
        # We could infer from the request parameters or use default
        return 'en'  # Default to English
    
    def extract_source(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract source information from GNews response
        """
        source_data = article.get('source', {})
        
        if isinstance(source_data, dict):
            return {
                'id': source_data.get('name', '').lower().replace(' ', '_'),
                'name': source_data.get('name', ''),
                'url': source_data.get('url', ''),
                'country': 'unknown'  # GNews doesn't provide country in source
            }
        elif isinstance(source_data, str):
            # Sometimes source is just a string
            return {
                'id': source_data.lower().replace(' ', '_'),
                'name': source_data,
                'url': '',
                'country': 'unknown'
            }
        else:
            return {
                'id': 'unknown',
                'name': 'Unknown Source',
                'url': '',
                'country': 'unknown'
            }
    
    def generate_short_summary(self, article: Dict[str, Any]) -> str:
        """
        Generate short summary for GNews article
        Uses description and truncates if too long
        """
        description = self.extract_description(article)
        if not description:
            title = self.extract_title(article)
            return title[:200] + "..." if len(title) > 200 else title
        
        if len(description) > 200:
            return description[:197] + "..."
        
        return description
