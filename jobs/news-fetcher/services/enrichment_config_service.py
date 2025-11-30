"""
Enrichment Configuration Service - Manages enrichment prompt configuration
"""

from datetime import datetime
from typing import Dict, Any, Optional
from pymongo import MongoClient


class EnrichmentConfigService:
    """Service to manage enrichment configuration settings"""

    # Default prompt template
    DEFAULT_PROMPT_TEMPLATE = """You are a professional news editor. Create a news summary following these STRICT requirements:

CRITICAL REQUIREMENTS:
1. Write EXACTLY 40-75 words - this is MANDATORY
2. Count every single word to ensure you meet this requirement
3. If your summary is less than 40 words, ADD MORE DETAILS
4. If your summary is more than 75 words, REMOVE LESS IMPORTANT DETAILS

CONTENT RULES:
- Write in plain, everyday English
- Use complete, grammatically correct sentences
- Include key facts: who, what, when, where, why
- Write ONLY the summary - no titles, labels, or explanations
- Never use code, markdown, bullets, or special formatting

Article to summarize:
{content}

Write your 40-75 word summary now:"""

    DEFAULT_RETRY_PROMPT_TEMPLATE = """IMPORTANT: Your previous summary was not in the correct range. You MUST write between 40-75 words.

COUNT YOUR WORDS CAREFULLY:
- Each word separated by space counts as 1 word
- Aim for 45-70 words to be safe
- Include ALL key facts from the article

Article to summarize:
{content}

Write your 45-70 word detailed summary:"""

    def __init__(self, config, logger=None):
        self.config = config
        self.logger = logger

        # MongoDB connection for news database
        self.news_client = MongoClient(config.NEWS_MONGODB_URL)
        self.news_db = self.news_client[config.NEWS_MONGODB_DATABASE]
        self.config_collection = self.news_db['enrichment_config']

        # Ensure configuration exists
        self._initialize_config()

    def _initialize_config(self):
        """Initialize configuration with defaults if not exists"""
        try:
            existing_config = self.config_collection.find_one({'config_type': 'enrichment'})
            
            if not existing_config:
                default_config = {
                    'config_type': 'enrichment',
                    'prompt_template': self.DEFAULT_PROMPT_TEMPLATE,
                    'retry_prompt_template': self.DEFAULT_RETRY_PROMPT_TEMPLATE,
                    'min_word_count': 30,
                    'max_word_count': 100,
                    'target_min_words': 40,
                    'target_max_words': 75,
                    'max_retries': 2,
                    'temperature': 0.6,
                    'retry_temperature': 0.7,
                    'max_tokens': 200,
                    'content_max_chars': 2000,
                    'created_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow()
                }
                
                self.config_collection.insert_one(default_config)
                if self.logger:
                    self.logger.info("✅ Initialized enrichment configuration with defaults")
            else:
                if self.logger:
                    self.logger.info("✅ Enrichment configuration already exists")
                    
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Error initializing enrichment config: {str(e)}")
            raise

    def get_config(self) -> Dict[str, Any]:
        """
        Get current enrichment configuration
        
        Returns:
            Dictionary with configuration settings
        """
        try:
            config = self.config_collection.find_one({'config_type': 'enrichment'})
            
            if not config:
                # Reinitialize if somehow deleted
                self._initialize_config()
                config = self.config_collection.find_one({'config_type': 'enrichment'})
            
            # Remove MongoDB _id for cleaner response
            if config and '_id' in config:
                del config['_id']
            
            return {
                'status': 'success',
                'config': config
            }
            
        except Exception as e:
            error_msg = f"Error fetching enrichment config: {str(e)}"
            if self.logger:
                self.logger.error(f"❌ {error_msg}")
            return {
                'status': 'error',
                'error': error_msg,
                'config': None
            }

    def update_config(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update enrichment configuration
        
        Args:
            updates: Dictionary with fields to update
            
        Returns:
            Dictionary with update result
        """
        try:
            # Validate updates
            allowed_fields = {
                'prompt_template',
                'retry_prompt_template',
                'min_word_count',
                'max_word_count',
                'target_min_words',
                'target_max_words',
                'max_retries',
                'temperature',
                'retry_temperature',
                'max_tokens',
                'content_max_chars'
            }
            
            # Filter out non-allowed fields
            filtered_updates = {k: v for k, v in updates.items() if k in allowed_fields}
            
            if not filtered_updates:
                return {
                    'status': 'error',
                    'error': 'No valid fields to update'
                }
            
            # Add updated timestamp
            filtered_updates['updated_at'] = datetime.utcnow()
            
            # Update configuration
            result = self.config_collection.update_one(
                {'config_type': 'enrichment'},
                {'$set': filtered_updates}
            )
            
            if result.modified_count > 0:
                if self.logger:
                    self.logger.info(f"✅ Updated enrichment configuration: {list(filtered_updates.keys())}")
                
                # Return updated config
                return self.get_config()
            else:
                return {
                    'status': 'success',
                    'message': 'No changes made (values already match)',
                    'config': self.get_config().get('config')
                }
                
        except Exception as e:
            error_msg = f"Error updating enrichment config: {str(e)}"
            if self.logger:
                self.logger.error(f"❌ {error_msg}")
            return {
                'status': 'error',
                'error': error_msg
            }

    def reset_to_defaults(self) -> Dict[str, Any]:
        """
        Reset configuration to default values
        
        Returns:
            Dictionary with reset result
        """
        try:
            default_updates = {
                'prompt_template': self.DEFAULT_PROMPT_TEMPLATE,
                'retry_prompt_template': self.DEFAULT_RETRY_PROMPT_TEMPLATE,
                'min_word_count': 30,
                'max_word_count': 100,
                'target_min_words': 40,
                'target_max_words': 75,
                'max_retries': 2,
                'temperature': 0.6,
                'retry_temperature': 0.7,
                'max_tokens': 200,
                'content_max_chars': 2000,
                'updated_at': datetime.utcnow()
            }
            
            result = self.config_collection.update_one(
                {'config_type': 'enrichment'},
                {'$set': default_updates}
            )
            
            if self.logger:
                self.logger.info("✅ Reset enrichment configuration to defaults")
            
            return self.get_config()
            
        except Exception as e:
            error_msg = f"Error resetting enrichment config: {str(e)}"
            if self.logger:
                self.logger.error(f"❌ {error_msg}")
            return {
                'status': 'error',
                'error': error_msg
            }

