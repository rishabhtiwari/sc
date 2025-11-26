"""
YouTube Metadata Builder
Factory pattern for building optimized YouTube video metadata
"""
import logging
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
from zoneinfo import ZoneInfo
from .description_generator import DescriptionGenerator

# Try to import spaCy for keyword extraction
try:
    import spacy
    nlp = spacy.load("en_core_web_sm")
except Exception as e:
    nlp = None
    logging.warning(f"⚠️ spaCy not available for keyword extraction: {e}")


class YouTubeMetadataBuilder:
    """Builder for creating optimized YouTube video metadata"""

    def __init__(self, llm_service_url: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        # LLM service is optional - only used for description generation if provided
        self.description_generator = DescriptionGenerator(llm_service_url) if llm_service_url else None

        # High-traffic search keywords for Indian news
        self.trending_keywords = [
            "breaking news",
            "latest news",
            "news today",
            "india news",
            "current affairs",
            "news update",
            "Politics",
            "Donald Trump",
            "Kamala Harris",
            "Pete Hegseth",
            "James Comey",
            "Narendra Modi",
            "Fact Check",
            "Viral Videos",
        ]

        # Category-specific hashtags
        self.category_hashtags = {
            'general': ['#News', '#BreakingNews', '#IndiaNews', '#EnglishNews', '#WorldNews'],
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
            '#EnglishNews',
            '#WorldNews',
            '#HindiNews',
            '#India',
            '#NewsToday',
            '#CurrentAffairs',
            '#IndianNews',
            '#GlobalNews',
            '#WorldNews',
            '#TopStories',
            '#DailyNews',
            '#NewsUpdate',
            '#VideoNews',
            '#Exclusive',
            '#Report',
            '#Journalism'
        ]

    def _extract_keywords_from_title(self, title: str, max_keywords: int = 5) -> List[str]:
        """
        Extract relevant keywords from a news title

        Args:
            title: News title string
            max_keywords: Maximum number of keywords to extract

        Returns:
            List of extracted keywords
        """
        # Common stop words to filter out
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'should', 'could', 'may', 'might', 'must', 'can', 'this',
            'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
            'what', 'which', 'who', 'when', 'where', 'why', 'how', 'all', 'each',
            'every', 'both', 'few', 'more', 'most', 'other', 'some', 'such', 'no',
            'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's',
            't', 'just', 'don', 'now', 'says', 'over', 'after', 'amid', 'his', 'her'
        }

        # Extract words from title
        words = re.findall(r'\b[a-zA-Z][a-zA-Z0-9]*\b', title.lower())

        # Filter out stop words and short words
        keywords = [word for word in words if len(word) >= 3 and word not in stop_words]

        # Return top keywords (unique)
        seen = set()
        unique_keywords = []
        for keyword in keywords:
            if keyword not in seen and len(unique_keywords) < max_keywords:
                seen.add(keyword)
                unique_keywords.append(keyword)

        return unique_keywords

    def _extract_keywords_from_title_spacy(self, title: str, keywords_count: int = 5) -> List[str]:
        """
        Extract keywords from a single title using spaCy NLP

        Args:
            title: News title string
            keywords_count: Number of keywords to extract (default: 5)

        Returns:
            List of extracted keywords
        """
        if not nlp:
            self.logger.warning("⚠️ spaCy model not loaded, falling back to simple extraction")
            return self._extract_keywords_from_title(title, max_keywords=keywords_count)

        # Stop words to filter out
        stop_words = {
            'and', 'or', 'but', 'for', 'with', 'from', 'into', 'during', 'including',
            'said', 'says', 'according', 'new', 'old', 'big', 'small', 'good', 'best',
            'after', 'before', 'while', 'when', 'where', 'how', 'why', 'what', 'who',
            'this', 'that', 'these', 'those', 'here', 'there', 'now', 'then',
            'study', 'reveals', 'claims', 'report', 'reports', 'video', 'watch',
            '2024', '2025', 'day', 'days', 'time', 'times', 'year', 'years',
            'amid', 'over', 'under', 'about', 'against', 'between', 'through'
        }

        keywords = []

        # Use spaCy to analyze the title
        doc = nlp(title)

        # Priority 1: Multi-word named entities (PERSON, ORG, GPE, PRODUCT, EVENT)
        for ent in doc.ents:
            if ent.label_ in ['PERSON', 'ORG', 'GPE', 'PRODUCT', 'EVENT', 'NORP', 'FAC', 'LOC']:
                phrase = ent.text.strip()
                # Remove possessive 's from names
                if phrase.endswith("'s"):
                    phrase = phrase[:-2]
                elif phrase.endswith("'"):
                    phrase = phrase[:-1]
                if len(phrase) > 2 and phrase.lower() not in stop_words:
                    keywords.append(('high', phrase.lower()))

        # Priority 2: Consecutive proper nouns (multi-word phrases like "iPhone 16")
        propn_sequence = []
        for token in doc:
            if token.pos_ == 'PROPN' and token.text.lower() not in stop_words:
                propn_sequence.append(token.text)
            elif token.pos_ == 'NUM' and len(propn_sequence) > 0:
                propn_sequence.append(token.text)
            else:
                if len(propn_sequence) >= 2:
                    phrase = ' '.join(propn_sequence)
                    keywords.append(('high', phrase.lower()))
                elif len(propn_sequence) == 1 and len(propn_sequence[0]) > 2:
                    keywords.append(('medium', propn_sequence[0].lower()))
                propn_sequence = []

        # Don't forget the last sequence
        if len(propn_sequence) >= 2:
            phrase = ' '.join(propn_sequence)
            keywords.append(('high', phrase.lower()))
        elif len(propn_sequence) == 1 and len(propn_sequence[0]) > 2:
            keywords.append(('medium', propn_sequence[0].lower()))

        # Priority 3: Important common nouns
        for token in doc:
            if token.pos_ == 'NOUN':
                word = token.text.lower()
                if (word not in stop_words and len(word) > 3 and
                    word not in {'home', 'sale', 'update', 'updates', 'news', 'headline', 'headlines'}):
                    keywords.append(('low', word))

        # Sort by priority and take top keywords_count
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        keywords.sort(key=lambda x: priority_order[x[0]])

        # Remove duplicates while preserving priority order
        seen = set()
        unique_keywords = []
        for priority, keyword in keywords:
            if keyword not in seen:
                seen.add(keyword)
                unique_keywords.append(keyword)
                if len(unique_keywords) >= keywords_count:
                    break

        return unique_keywords

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
            'english news',
            'world news',
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

        # 4. Time-based tags (using India timezone)
        india_tz = ZoneInfo("Asia/Kolkata")
        india_time = datetime.now(india_tz)
        current_year = india_time.year
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

    def build_shorts_metadata(self, title: str, description: str) -> Dict[str, Any]:
        """
        Build YouTube Shorts metadata

        YouTube Shorts best practices:
        - Title: 60 characters or less for mobile
        - Description: Keep it concise, first 2 lines visible
        - Tags: Focus on #Shorts and trending tags
        - Vertical format (9:16 aspect ratio)

        Args:
            title: Original news title
            description: Short summary or description

        Returns:
            Dictionary with title, description, and tags
        """
        # Optimize title for Shorts (max 60 chars for mobile)
        shorts_title = title
        if len(shorts_title) > 60:
            shorts_title = shorts_title[:57] + '...'

        # Add Shorts indicator emoji
        shorts_title = f"📱 {shorts_title}"

        # Build concise description for Shorts
        parts = []

        # Main content (keep it short)
        if description:
            # Limit description to 150 chars for better mobile visibility
            short_desc = description[:150] + '...' if len(description) > 150 else description
            parts.append(short_desc)
        else:
            parts.append("Watch this quick news update!")

        parts.append("")
        parts.append("🔔 Subscribe for more news shorts!")
        parts.append("")

        # Comprehensive Shorts hashtags (first 3 appear above title)
        shorts_hashtags = [
            '#Shorts',
            '#YouTubeShorts',
            '#News',
            '@CNI-News24',
            '#BreakingNews',
            '#LatestNews',
            '#EnglishNews',
            '#WorldNews',
            '#IndiaNews',
            '#NewsUpdate',
            '#ShortNews',
            '#QuickNews',
            '#NewsToday',
            '#CurrentAffairs',
            '#TrendingNews'
        ]
        parts.append(" ".join(shorts_hashtags))
        parts.append("")

        # Add keywords section for better SEO
        parts.append("🔍 KEYWORDS:")

        # Base keywords for Shorts
        base_shorts_keywords = [
            "shorts",
            "news shorts",
            "breaking news",
            "latest news",
            "english news",
            "world news",
            "india news",
            "news today",
            "quick news",
            "trending news"
        ]

        # Extract content-specific keywords from title using spaCy
        content_keywords = self._extract_keywords_from_title_spacy(title, keywords_count=5)

        # Combine base and content-specific keywords
        all_shorts_keywords = base_shorts_keywords + content_keywords

        parts.append(", ".join(all_shorts_keywords))

        final_description = "\n".join(parts)

        # Build comprehensive tags for Shorts
        base_shorts_tags = [
            'shorts',
            'youtube shorts',
            'news shorts',
            'breaking news',
            'latest news',
            'english news',
            'world news',
            'india news',
            'news update',
            'quick news',
            'short news',
            'news today',
            'current affairs',
            'trending news',
            'viral news',
            'news headlines',
            'top news'
        ]

        # Filter content keywords: remove phrases with more than 2 words and invalid characters
        clean_content_keywords = []
        for kw in content_keywords:
            # Convert tuple to string if needed
            if isinstance(kw, tuple):
                keyword_str = kw[1] if len(kw) > 1 else str(kw[0])
            else:
                keyword_str = str(kw)

            # Filter out phrases with more than 2 words
            word_count = len(keyword_str.split())
            if word_count > 2:
                continue

            # Filter out non-ASCII characters (YouTube doesn't accept them in tags)
            if not keyword_str.isascii():
                continue

            # Filter out tags that are too short (less than 2 characters)
            if len(keyword_str) < 2:
                continue

            # Filter out tags with special characters (only allow alphanumeric, space, hyphen)
            import re
            if not re.match(r'^[a-zA-Z0-9\s\-]+$', keyword_str):
                continue

            clean_content_keywords.append(keyword_str)

        # Combine base tags with content keywords
        all_tags = base_shorts_tags + clean_content_keywords

        # Ensure total tag size is less than 450 characters and each tag is max 30 chars
        shorts_tags = []
        total_size = 0
        for tag in all_tags:
            # Skip tags longer than 30 characters (YouTube limit per tag)
            if len(tag) > 30:
                continue

            tag_size = len(tag)
            if total_size + tag_size + len(shorts_tags) <= 450:  # +len(shorts_tags) accounts for commas
                shorts_tags.append(tag)
                total_size += tag_size
            else:
                break

        self.logger.info(f"🏷️ Shorts tags: {len(shorts_tags)} tags, total size: {total_size} chars")

        return {
            'title': shorts_title,
            'description': final_description,
            'tags': shorts_tags
        }
