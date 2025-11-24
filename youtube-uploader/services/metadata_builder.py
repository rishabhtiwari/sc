"""
YouTube Metadata Builder
Factory pattern for building optimized YouTube video metadata
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from .description_generator import DescriptionGenerator


class YouTubeMetadataBuilder:
    """Builder for creating optimized YouTube video metadata"""

    def __init__(self, llm_service_url: str = "http://ichat-llm-service:8083"):
        self.logger = logging.getLogger(__name__)
        self.description_generator = DescriptionGenerator(llm_service_url)
        
        # High-traffic search keywords for Indian news
        self.trending_keywords = [
            "breaking news",
            "latest news",
            "news today",
            "hindi news",
            "india news",
            "current affairs",
            "news update",
            "aaj ki khabar",
            "ताज़ा खबर",
            "समाचार"
        ]
        
        # Category-specific hashtags
        self.category_hashtags = {
            'general': ['#News', '#BreakingNews', '#IndiaNews'],
            'business': ['#Business', '#Economy', '#Finance', '#StockMarket', '#BusinessNews'],
            'entertainment': ['#Entertainment', '#Bollywood', '#Celebrity', '#Movies', '#Entertainment'],
            'health': ['#Health', '#Healthcare', '#Wellness', '#Medical', '#HealthNews'],
            'science': ['#Science', '#Research', '#Innovation', '#Discovery', '#ScienceNews'],
            'sports': ['#Sports', '#Cricket', '#Football', '#IPL', '#SportsNews'],
            'technology': ['#Technology', '#Tech', '#Innovation', '#Gadgets', '#TechNews'],
            'politics': ['#Politics', '#Election', '#Government', '#PoliticalNews', '#India']
        }
        
        # Common high-traffic hashtags (first 3 appear above video title)
        self.common_hashtags = [
            '#News',
            '#BreakingNews', 
            '#LatestNews',
            '#HindiNews',
            '#India',
            '#NewsToday',
            '#CurrentAffairs',
            '#IndianNews'
        ]
    
    def build_title(self, news_doc: Dict[str, Any]) -> str:
        """
        Build optimized YouTube title
        
        YouTube title best practices:
        - Max 100 characters (60-70 optimal for mobile)
        - Front-load important keywords
        - Include emotional triggers
        - Add year/date for freshness
        
        Args:
            news_doc: MongoDB news document
            
        Returns:
            Optimized title string
        """
        original_title = news_doc.get('title', 'Untitled')
        category = news_doc.get('category', 'general')
        
        # Truncate if too long (leave room for prefix)
        max_title_length = 90
        if len(original_title) > max_title_length:
            original_title = original_title[:max_title_length] + '...'
        
        # Add category prefix for better categorization
        category_prefixes = {
            'business': '💼 Business:',
            'entertainment': '🎬 Entertainment:',
            'health': '🏥 Health:',
            'science': '🔬 Science:',
            'sports': '⚽ Sports:',
            'technology': '💻 Tech:',
            'politics': '🏛️ Politics:'
        }
        
        prefix = category_prefixes.get(category, '📰')
        
        # Build final title
        final_title = f"{prefix} {original_title}"
        
        # Ensure within YouTube's 100 char limit
        if len(final_title) > 100:
            final_title = final_title[:97] + '...'
        
        return final_title
    
    def build_description(self, news_doc: Dict[str, Any]) -> str:
        """
        Build comprehensive YouTube description with SEO optimization

        YouTube description best practices:
        - First 2-3 lines are most important (appear in search)
        - Include keywords naturally
        - Add timestamps if applicable
        - Include call-to-action
        - Max 5000 characters

        Args:
            news_doc: MongoDB news document

        Returns:
            Optimized description string
        """
        parts = []

        # 1. LLM-Generated Main Description (200 words, SEO-optimized)
        self.logger.info("Generating LLM-based description...")
        llm_description = self.description_generator.generate_description(news_doc)
        parts.append(llm_description)
        parts.append("")  # Empty line
        
        # 2. Separator before call-to-action
        parts.append("━━━━━━━━━━━━━━━━━━━━━━━━━━")
        parts.append("")

        # 3. Call to action (important for engagement)
        parts.append("━━━━━━━━━━━━━━━━━━━━━━━━━━")
        parts.append("🔔 SUBSCRIBE for Daily News Updates!")
        parts.append("👍 LIKE if you found this informative")
        parts.append("💬 COMMENT your thoughts below")
        parts.append("🔗 SHARE with friends and family")
        parts.append("━━━━━━━━━━━━━━━━━━━━━━━━━━")
        parts.append("")

        # 4. Hashtags (first 3 appear above title, max 15 total)
        hashtags = self._build_hashtags(news_doc)
        parts.append(" ".join(hashtags[:15]))
        parts.append("")

        # 5. SEO Keywords section (helps with search)
        parts.append("━━━━━━━━━━━━━━━━━━━━━━━━━━")
        parts.append("🔍 KEYWORDS:")
        keywords = self._build_keywords(news_doc)
        parts.append(", ".join(keywords))
        parts.append("")

        # 6. About section
        parts.append("━━━━━━━━━━━━━━━━━━━━━━━━━━")
        parts.append("📢 About This Channel:")
        parts.append("Stay updated with the latest news from India and around the world.")
        parts.append("We bring you breaking news, current affairs, and in-depth analysis.")
        parts.append("")

        # 7. Disclaimer
        parts.append("⚠️ Disclaimer:")
        parts.append("This content is for informational purposes only.")
        
        final_description = "\n".join(parts)
        
        # Ensure within YouTube's 5000 char limit
        if len(final_description) > 5000:
            final_description = final_description[:4997] + '...'
        
        return final_description
    
    def build_tags(self, news_doc: Dict[str, Any]) -> List[str]:
        """
        Build optimized tags for YouTube video
        
        YouTube tags best practices:
        - Max 500 characters total
        - Use 5-15 tags
        - Mix broad and specific tags
        - Include common misspellings
        - Use multi-word phrases
        
        Args:
            news_doc: MongoDB news document
            
        Returns:
            List of tag strings
        """
        tags = []
        category = news_doc.get('category', 'general')
        
        # 1. Generic high-traffic tags
        tags.extend([
            'news',
            'breaking news',
            'latest news',
            'hindi news',
            'india news',
            'news today',
            'current affairs'
        ])
        
        # 2. Category-specific tags
        category_tags = {
            'business': ['business news', 'economy', 'finance', 'stock market', 'business'],
            'entertainment': ['entertainment news', 'bollywood', 'celebrity', 'movies', 'entertainment'],
            'health': ['health news', 'healthcare', 'medical', 'wellness', 'health'],
            'science': ['science news', 'research', 'innovation', 'discovery', 'science'],
            'sports': ['sports news', 'cricket', 'football', 'ipl', 'sports'],
            'technology': ['tech news', 'technology', 'gadgets', 'innovation', 'tech'],
            'politics': ['political news', 'politics', 'election', 'government', 'political']
        }
        
        if category in category_tags:
            tags.extend(category_tags[category])
        
        # 3. Hindi/Hinglish variations (important for Indian audience)
        tags.extend([
            'aaj ki khabar',
            'taza khabar',
            'samachar',
            'khabar'
        ])
        
        # 4. Time-based tags
        current_year = datetime.now().year
        tags.extend([
            f'news {current_year}',
            'today news',
            'latest update'
        ])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_tags = []
        for tag in tags:
            if tag.lower() not in seen:
                seen.add(tag.lower())
                unique_tags.append(tag)
        
        # Limit to 15 tags and ensure total length < 500 chars
        final_tags = []
        total_length = 0
        for tag in unique_tags[:15]:
            if total_length + len(tag) + 1 < 500:  # +1 for comma
                final_tags.append(tag)
                total_length += len(tag) + 1
            else:
                break
        
        return final_tags
    
    def _build_hashtags(self, news_doc: Dict[str, Any]) -> List[str]:
        """Build hashtags for description"""
        hashtags = []
        category = news_doc.get('category', 'general')
        
        # Add common hashtags (first 3 appear above title)
        hashtags.extend(self.common_hashtags[:3])
        
        # Add category-specific hashtags
        if category in self.category_hashtags:
            hashtags.extend(self.category_hashtags[category][:5])
        
        # Add generic hashtags
        hashtags.extend(self.common_hashtags[3:8])
        
        # Remove duplicates
        return list(dict.fromkeys(hashtags))
    
    def _build_keywords(self, news_doc: Dict[str, Any]) -> List[str]:
        """Build SEO keywords"""
        keywords = []
        category = news_doc.get('category', 'general')
        
        # Add trending keywords
        keywords.extend(self.trending_keywords)
        
        # Add category-specific keywords
        if category != 'general':
            keywords.append(f'{category} news')
            keywords.append(category)
        
        return keywords
    
    def build_metadata(self, news_doc: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build complete YouTube metadata package
        
        Args:
            news_doc: MongoDB news document
            
        Returns:
            Dictionary with title, description, and tags
        """
        return {
            'title': self.build_title(news_doc),
            'description': self.build_description(news_doc),
            'tags': self.build_tags(news_doc)
        }

