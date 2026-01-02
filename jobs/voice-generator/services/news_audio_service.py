"""
News Audio Service - Generate audio for news articles using audio-generation service
"""

import os
import sys
import logging
import requests
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from pymongo import MongoClient
from config.settings import Config

# Add parent directory to path for common utilities
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'common'))

from common.utils.multi_tenant_db import (
    build_multi_tenant_query,
    prepare_update_document
)


class NewsAudioService:
    """Service for generating audio from news articles"""

    def __init__(self, logger: logging.Logger = None):
        """
        Initialize NewsAudioService
        
        Args:
            logger: Logger instance for logging
        """
        self.logger = logger or logging.getLogger(__name__)
        self.config = Config

        # Initialize MongoDB connection for news database
        self.news_client = MongoClient(Config.NEWS_MONGODB_URL)
        self.news_db = self.news_client.get_database()
        self.news_collection = self.news_db.news_document

        # Test connection
        self.news_client.admin.command('ping')
        self.logger.info("🔧 NewsAudioService initialized successfully")

    def get_articles_needing_audio(self, limit: int = None, customer_id: str = None) -> List[Dict[str, Any]]:
        """
        Get articles that need audio generation (audio_path is null)

        Args:
            limit: Maximum number of articles to return
            customer_id: Customer ID for multi-tenant filtering (uses SYSTEM_CUSTOMER_ID if None)

        Returns:
            List of news articles needing audio generation
        """
        try:
            # Query for articles with no audio_paths and have short_summary
            # Comprehensive check for articles without audio generation:
            # 1. audio_paths field doesn't exist
            # 2. audio_paths is null
            # 3. audio_paths is empty object {}
            # 4. audio_paths exists but is missing short_summary field
            base_query = {
                '$and': [
                    {
                        '$or': [
                            {'audio_paths': {'$exists': False}},  # Field doesn't exist
                            {'audio_paths': None},  # Field is null
                            {'audio_paths': {}},  # Field is empty object
                            {'audio_paths': {'$in': [None, {}]}},  # Field is null or empty
                            # Check if short_summary audio is missing
                            {'audio_paths.short_summary': {'$exists': False}}
                        ]
                    },
                    {'status': {'$in': ['completed', 'published']}},  # Only completed articles
                    {'short_summary': {'$exists': True, '$ne': '', '$ne': None}}  # Must have short_summary
                ]
            }

            # Apply multi-tenant filter
            query = build_multi_tenant_query(base_query, customer_id=customer_id)

            cursor = self.news_collection.find(query).sort('created_at', -1)
            if limit:
                cursor = cursor.limit(limit)

            articles = list(cursor)
            self.logger.info(f"📰 Found {len(articles)} articles needing audio generation")
            return articles

        except Exception as e:
            self.logger.error(f"❌ Error getting articles needing audio: {str(e)}")
            return []

    def generate_audio_for_article(self, article: Dict[str, Any], voice: str = None, customer_id: str = None) -> Dict[str, Any]:
        """
        Generate audio for a single article (short_summary only)

        Args:
            article: News article document
            voice: Optional voice to use for audio generation (e.g., 'am_adam', 'af_bella', 'male', 'female')
            customer_id: Customer ID for loading voice configuration

        Returns:
            Dictionary with generation results
        """
        result = {
            'article_id': article.get('id', 'unknown'),
            'success': False,
            'audio_paths': {},
            'error': None,
            'generation_time_ms': 0,
            'voice_used': None
        }

        try:
            article_id = article.get('id', 'unknown')
            self.logger.info(f"🎵 Generating audio for article: {article_id}")

            # Get customer_id from article if not provided
            if not customer_id:
                customer_id = article.get('customer_id')

            # Determine language and model (pass customer_id to load their model config)
            language = article.get('lang', 'en')
            model = self._get_audio_model_for_language(language, customer_id=customer_id)
            self.logger.info(f"🌍 Article language: {language}, Selected model: {model}")
            self.logger.info(f"🔧 DEFAULT_AUDIO_MODEL: {self.config.DEFAULT_AUDIO_MODEL}")
            self.logger.info(f"🔧 HINDI_AUDIO_MODEL: {self.config.HINDI_AUDIO_MODEL}")

            # Determine voice to use (pass customer_id to load their config)
            voice_to_use = self._determine_voice(voice, language, customer_id=customer_id)
            self.logger.info(f"🎭 Voice selected: {voice_to_use}")
            result['voice_used'] = voice_to_use

            # Create public directory structure
            import os
            public_dir = "/app/public"
            article_dir = os.path.join(public_dir, str(article_id))
            os.makedirs(article_dir, exist_ok=True)

            # Fields to generate audio for (only short_summary)
            audio_fields = {
                'short_summary': article.get('short_summary', '')
            }

            total_start_time = time.time()
            generated_paths = {}

            # Generate audio for each field
            for field_name, text_content in audio_fields.items():
                if not text_content or not text_content.strip():
                    self.logger.warning(f"⚠️ No {field_name} content found for article {article_id}")
                    continue

                self.logger.info(f"🔊 Generating {field_name} audio for article {article_id}")

                # Generate audio via audio-generation service with voice
                audio_result = self._call_audio_generation_service(text_content.strip(), model, voice_to_use)

                if audio_result['success']:
                    # Move generated file to our structure
                    source_path = audio_result['audio_url']
                    target_filename = f"{field_name}.wav"
                    target_path = os.path.join(article_dir, target_filename)

                    # Copy file from TTS service location to our public structure
                    if self._move_audio_file(source_path, target_path):
                        generated_paths[field_name] = f"/public/{article_id}/{target_filename}"
                        self.logger.info(f"✅ {field_name.title()} audio saved: {target_path}")
                    else:
                        self.logger.error(f"❌ Failed to move {field_name} audio file")
                else:
                    self.logger.error(
                        f"❌ Failed to generate {field_name} audio: {audio_result.get('error', 'Unknown error')}")

            generation_time = int((time.time() - total_start_time) * 1000)

            if generated_paths:
                # Prepare update data with audit tracking
                update_data = {
                    'audio_paths': generated_paths,
                    'voice': voice_to_use,
                    'voice_updated_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow()
                }
                prepare_update_document(update_data, user_id='system')

                # Update article with audio paths and voice used
                update_result = self.news_collection.update_one(
                    {'id': article_id},
                    {'$set': update_data}
                )

                if update_result.modified_count > 0:
                    result['success'] = True
                    result['audio_paths'] = generated_paths
                    result['generation_time_ms'] = generation_time
                    self.logger.info(
                        f"✅ All audio files generated for article {article_id}: {list(generated_paths.keys())}")
                else:
                    result['error'] = "Failed to update article with audio paths"
            else:
                result['error'] = "No audio files were successfully generated"

        except Exception as e:
            result['error'] = f"Exception during audio generation: {str(e)}"
            self.logger.error(f"❌ Error generating audio for article {result['article_id']}: {str(e)}")

        return result

    def _move_audio_file(self, source_path: str, target_path: str) -> bool:
        """
        Move audio file from TTS service location to our public structure

        Args:
            source_path: Source file path from TTS service
            target_path: Target file path in our public structure

        Returns:
            True if file was moved successfully, False otherwise
        """
        try:
            import shutil
            import os

            # Ensure target directory exists
            os.makedirs(os.path.dirname(target_path), exist_ok=True)

            # Handle different source path formats
            # TTS service returns paths like "/tts_mms-tts-hin_1762711899384.wav" or "/temp/kokoro_xxx.wav"
            if source_path.startswith('/temp/'):
                # Kokoro model temp files are in audio-generation service's /app/public/temp/ directory
                # which is mounted as /app/tts_data/temp/ in voice generator container
                filename = source_path.replace('/temp/', '')
                actual_source = f"/app/tts_data/temp/{filename}"
            elif source_path.startswith('/tts_'):
                # TTS service path format - remove leading slash and add TTS data directory
                actual_source = f"/app/tts_data{source_path}"
            elif source_path.startswith('/'):
                # Other absolute path from TTS service
                actual_source = source_path
            else:
                # Relative path, assume it's in TTS service directory
                actual_source = f"/app/tts_data/{source_path}"

            self.logger.info(f"🔍 Looking for audio file at: {actual_source}")

            if os.path.exists(actual_source):
                shutil.copy2(actual_source, target_path)
                self.logger.info(f"📁 Moved audio file: {actual_source} → {target_path}")
                return True
            else:
                self.logger.error(f"❌ Source audio file not found: {actual_source}")
                # List files in TTS data directory for debugging
                try:
                    tts_data_files = os.listdir("/app/tts_data")
                    self.logger.info(f"📂 Files in /app/tts_data: {tts_data_files}")
                except Exception as list_e:
                    self.logger.error(f"❌ Could not list TTS data directory: {str(list_e)}")
                return False

        except Exception as e:
            self.logger.error(f"❌ Error moving audio file: {str(e)}")
            return False

    def _prepare_text_for_tts(self, article: Dict[str, Any]) -> Optional[str]:
        """
        Prepare text content for TTS generation
        
        Args:
            article: News article document
            
        Returns:
            Text content suitable for TTS or None if no suitable content
        """
        # Priority: short_summary > description > content (truncated)
        text_content = None

        # First try short_summary (usually 40-70 words, perfect for TTS)
        if article.get('short_summary'):
            text_content = article['short_summary'].strip()

        # Fallback to description
        elif article.get('description'):
            text_content = article['description'].strip()

        # Last resort: use full content without truncation
        elif article.get('content'):
            text_content = article['content'].strip()

        return text_content if text_content else None

    def _get_audio_model_for_language(self, language: str, customer_id: str = None) -> str:
        """
        Get appropriate audio model for language from customer's voice config

        Args:
            language: Language code (e.g., 'en', 'hi')
            customer_id: Customer ID for loading their model configuration

        Returns:
            Model name for audio generation
        """
        # Load customer's voice config from database
        voice_config = self._get_voice_config(customer_id=customer_id)
        models = voice_config.get('models', {})

        # Normalize language code
        lang_code = language.lower()
        if lang_code in ['hin']:
            lang_code = 'hi'
        elif lang_code in ['eng']:
            lang_code = 'en'

        # Get model from config, fallback to defaults
        if lang_code in models:
            return models[lang_code]

        # Fetch default model from audio generation service (API-driven)
        try:
            config_url = f"{self.config.AUDIO_GENERATION_SERVICE_URL}/config"
            response = requests.get(config_url, timeout=10)
            if response.status_code == 200:
                audio_config = response.json()
                default_model = audio_config.get('default_model')
                if default_model:
                    self.logger.info(f"✅ Using API-driven default model: {default_model}")
                    return default_model
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to fetch audio config from API: {str(e)}, using fallback")

        # Fallback to hardcoded defaults if API call fails
        if lang_code == 'hi':
            return self.config.HINDI_AUDIO_MODEL
        else:
            return self.config.DEFAULT_AUDIO_MODEL

    def _get_voice_config(self, customer_id: str = None) -> Dict[str, Any]:
        """
        Get voice configuration for customer from database

        Args:
            customer_id: Customer ID for multi-tenant filtering

        Returns:
            Voice configuration dictionary with new structure:
            {
                'language': 'en',
                'models': {'en': 'kokoro-82m', 'hi': 'mms-tts-hin'},
                'voices': {
                    'en': {'defaultVoice': '...', 'enableAlternation': True, ...},
                    'hi': {'defaultVoice': '...', 'enableAlternation': True, ...}
                }
            }
        """
        try:
            base_query = {}
            query = build_multi_tenant_query(base_query, customer_id=customer_id)

            voice_config_collection = self.news_db['voice_config']
            config = voice_config_collection.find_one(query)

            if not config:
                # Return default config if not found
                self.logger.warning(
                    f"No voice config found for customer {customer_id}, using defaults")
                return {
                    'language': 'en',
                    'models': {
                        'en': 'kokoro-82m',
                        'hi': 'mms-tts-hin'
                    },
                    'voices': {
                        'en': {
                            'defaultVoice': 'am_adam',
                            'enableAlternation': True,
                            'maleVoices': ['am_adam', 'am_michael'],
                            'femaleVoices': ['af_bella', 'af_sarah']
                        },
                        'hi': {
                            'defaultVoice': 'hi_default',
                            'enableAlternation': False,  # MMS Hindi only has one voice
                            'maleVoices': [],
                            'femaleVoices': []
                        }
                    }
                }

            return config
        except Exception as e:
            self.logger.error(f"Error loading voice config: {e}")
            # Return default config on error
            return {
                'language': 'en',
                'models': {
                    'en': 'kokoro-82m',
                    'hi': 'mms-tts-hin'
                },
                'voices': {
                    'en': {
                        'defaultVoice': 'am_adam',
                        'enableAlternation': True,
                        'maleVoices': ['am_adam', 'am_michael'],
                        'femaleVoices': ['af_bella', 'af_sarah']
                    },
                    'hi': {
                        'defaultVoice': 'hi_default',
                        'enableAlternation': False,  # MMS Hindi only has one voice
                        'maleVoices': [],
                        'femaleVoices': []
                    }
                }
            }

    def _determine_voice(self, voice: str = None, language: str = 'en', customer_id: str = None) -> str:
        """
        Determine which voice to use based on language and customer config

        Args:
            voice: Requested voice ('male', 'female', or specific voice name)
            language: Article language code (e.g., 'en', 'hi')
            customer_id: Customer ID for loading config

        Returns:
            Voice name to use for generation
        """
        # Load customer's voice config from database
        voice_config = self._get_voice_config(customer_id=customer_id)
        voices = voice_config.get('voices', {})

        # Normalize language code
        lang_code = language.lower()
        if lang_code in ['hin']:
            lang_code = 'hi'
        elif lang_code in ['eng']:
            lang_code = 'en'

        # Get voice config for this language
        lang_voice_config = voices.get(lang_code, {})

        if not lang_voice_config:
            # Fallback to default language config
            self.logger.warning(f"No voice config for language {lang_code}, using defaults")
            if lang_code == 'hi':
                lang_voice_config = {
                    'defaultVoice': 'hi_default',
                    'maleVoices': [],
                    'femaleVoices': []
                }
            else:
                lang_voice_config = {
                    'defaultVoice': 'am_adam',
                    'maleVoices': ['am_adam', 'am_michael'],
                    'femaleVoices': ['af_bella', 'af_sarah']
                }

        # Determine voice based on request
        if not voice:
            # No specific voice requested, use default
            return lang_voice_config.get('defaultVoice', 'am_adam')

        # Handle generic 'male' or 'female'
        if voice.lower() == 'male':
            male_voices = lang_voice_config.get('maleVoices', ['am_adam'])
            return male_voices[0] if male_voices else 'am_adam'
        elif voice.lower() == 'female':
            female_voices = lang_voice_config.get('femaleVoices', ['af_bella'])
            return female_voices[0] if female_voices else 'af_bella'

        # Return specific voice name as-is
        return voice

    def _get_next_alternating_voice(self, customer_id: str = None, language: str = 'en') -> str:
        """
        Get the next voice in alternating male/female pattern based on last used voice
        Uses customer's voice configuration from database

        Args:
            customer_id: Customer ID for multi-tenant filtering (uses SYSTEM_CUSTOMER_ID if None)
            language: Language code to get voices for (e.g., 'en', 'hi')

        Returns:
            Voice name to use (alternates between male and female)
        """
        # Load voice config from database
        voice_config = self._get_voice_config(customer_id=customer_id)
        voices = voice_config.get('voices', {})

        # Normalize language code
        lang_code = language.lower()
        if lang_code in ['hin']:
            lang_code = 'hi'
        elif lang_code in ['eng']:
            lang_code = 'en'

        # Get voice config for this language
        lang_voice_config = voices.get(lang_code, {})

        if not lang_voice_config:
            # Fallback to defaults
            if lang_code == 'hi':
                lang_voice_config = {
                    'defaultVoice': 'hi_default',
                    'enableAlternation': False,  # MMS Hindi only has one voice
                    'maleVoices': [],
                    'femaleVoices': []
                }
            else:
                lang_voice_config = {
                    'defaultVoice': 'am_adam',
                    'enableAlternation': True,
                    'maleVoices': ['am_adam', 'am_michael'],
                    'femaleVoices': ['af_bella', 'af_sarah']
                }

        # Check if alternation is enabled for this language
        if not lang_voice_config.get('enableAlternation', True):
            default_voice = lang_voice_config.get('defaultVoice', 'am_adam')
            self.logger.info(f"🎭 Voice alternation disabled for {lang_code}, using default: {default_voice}")
            return default_voice

        try:
            # Get voice lists from language config
            male_voices = lang_voice_config.get('maleVoices', ['am_adam'])
            female_voices = lang_voice_config.get('femaleVoices', ['af_bella'])

            # Build query with multi-tenant filter
            base_query = {
                'voice': {'$ne': None, '$exists': True},
                'voice_updated_at': {'$exists': True},
                'lang': lang_code  # Filter by language
            }
            query = build_multi_tenant_query(base_query, customer_id=customer_id)

            # Get the last article with a voice assigned, sorted by voice_updated_at
            last_article = self.news_collection.find_one(query, sort=[('voice_updated_at', -1)])

            if not last_article or not last_article.get('voice'):
                # No previous voice, start with first male voice from config
                first_male = male_voices[0] if male_voices else 'am_adam'
                self.logger.info(
                    f"🎭 No previous voice found for {lang_code}, starting with male voice: {first_male}")
                return first_male

            last_voice = last_article['voice']
            self.logger.info(f"🎭 Last voice used for {lang_code}: {last_voice}")

            # Check if last voice was male or female
            if last_voice in male_voices:
                # Last was male, use female
                next_voice = female_voices[0] if female_voices else 'af_bella'
                self.logger.info(f"🎭 Last was male, switching to female: {next_voice}")
                return next_voice
            else:
                # Last was female (or unknown), use male
                next_voice = male_voices[0] if male_voices else 'am_adam'
                self.logger.info(f"🎭 Last was female, switching to male: {next_voice}")
                return next_voice

        except Exception as e:
            self.logger.warning(f"⚠️ Error determining alternating voice: {str(e)}, using default")
            return lang_voice_config.get('defaultVoice', 'am_adam')

    def _call_audio_generation_service(self, text: str, model: str, voice: str = None) -> Dict[str, Any]:
        """
        Call the audio-generation service to generate TTS

        Args:
            text: Text to convert to speech
            model: TTS model to use
            voice: Voice to use for generation (optional)

        Returns:
            Dictionary with generation results
        """
        try:
            url = f"{self.config.AUDIO_GENERATION_SERVICE_URL}/tts"
            payload = {
                'text': text,
                'model': model,
                'format': 'wav',
                'voice': voice or self.config.DEFAULT_MALE_VOICE  # Use provided voice or default
            }

            self.logger.info(f"🔊 Calling audio generation service: {url}")
            self.logger.info(f"📝 Text length: {len(text)} chars, Model: {model}")
            self.logger.info(f"📦 Payload: {payload}")

            # Use extended timeout for CPU-based models (10 minutes) as they take longer to generate
            # Kokoro on CPU is slow, Bark on GPU is fast
            timeout = 600 if model in ['kokoro-82m', 'mms-tts-hin'] else self.config.AUDIO_GENERATION_TIMEOUT
            self.logger.info(f"⏱️ Using timeout: {timeout}s for model: {model}")

            response = requests.post(
                url,
                json=payload,
                timeout=timeout
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    self.logger.info(f"✅ Audio generation successful in {result.get('generation_time_ms', 0)}ms")
                    return {
                        'success': True,
                        'audio_url': result.get('audio_url'),
                        'generation_time_ms': result.get('generation_time_ms', 0)
                    }
                else:
                    self.logger.error(f"❌ Audio generation failed: {result.get('error', 'Unknown error')}")
                    return {
                        'success': False,
                        'error': result.get('error', 'Unknown error from audio service')
                    }
            else:
                self.logger.error(f"❌ HTTP error {response.status_code}: {response.text}")
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}"
                }

        except requests.exceptions.Timeout:
            self.logger.error(f"❌ Audio generation timeout after {timeout}s")
            return {
                'success': False,
                'error': f"Audio generation timeout after {timeout}s"
            }
        except Exception as e:
            self.logger.error(f"❌ Audio generation exception: {str(e)}")
            return {
                'success': False,
                'error': f"Audio generation service error: {str(e)}"
            }

    def process_news_audio_generation(self, job_id: str = None, is_on_demand: bool = False, customer_id: str = None) -> Dict[str, Any]:
        """
        Process audio generation for multiple news articles

        For scheduled jobs: Processes ONE batch per customer to ensure fair distribution
        For on-demand jobs: Processes ALL batches until completion

        Args:
            job_id: Job ID for tracking
            is_on_demand: Whether this is an on-demand job execution
            customer_id: Customer ID for multi-tenant filtering (uses SYSTEM_CUSTOMER_ID if None)

        Returns:
            Dictionary with processing results
        """
        results = {
            'total_articles_found': 0,
            'total_articles_processed': 0,
            'total_articles_success': 0,
            'total_articles_failed': 0,
            'errors': [],
            'processing_time_ms': 0,
            'batches_processed': 0
        }

        start_time = time.time()
        customer_info = f" for customer {customer_id}" if customer_id else ""

        try:
            # For scheduled jobs: process only ONE batch per customer
            # For on-demand jobs: process ALL batches until completion
            max_batches = None if is_on_demand else 1

            if is_on_demand:
                self.logger.info(f"🎵 On-demand job{customer_info}: Processing ALL batches until completion")
            else:
                self.logger.info(f"🎵 Scheduled job{customer_info}: Processing ONE batch (max {self.config.AUDIO_BATCH_SIZE} articles)")

            # Continue processing until no more articles need audio OR max_batches reached
            while True:
                # Check if we've reached the batch limit for scheduled jobs
                if max_batches is not None and results['batches_processed'] >= max_batches:
                    self.logger.info(f"✅ Reached batch limit ({max_batches}) for scheduled job{customer_info}")
                    break

                # Get articles needing audio generation (batch processing) with customer filter
                articles = self.get_articles_needing_audio(limit=self.config.AUDIO_BATCH_SIZE, customer_id=customer_id)

                if not articles:
                    self.logger.info(f"✅ No more articles found needing audio generation{customer_info}")
                    break

                results['batches_processed'] += 1
                batch_articles_found = len(articles)
                results['total_articles_found'] += batch_articles_found

                self.logger.info(
                    f"🎵 Processing batch {results['batches_processed']}: {batch_articles_found} articles for audio generation{customer_info}")

                # Process each article in the current batch
                for article in articles:
                    try:
                        # Get customer_id and language from article
                        article_customer_id = customer_id or article.get('customer_id')
                        article_language = article.get('lang', 'en')

                        # Load voice config from database for this customer
                        voice_config = self._get_voice_config(customer_id=article_customer_id)
                        voices = voice_config.get('voices', {})

                        # Normalize language code
                        lang_code = article_language.lower()
                        if lang_code in ['hin']:
                            lang_code = 'hi'
                        elif lang_code in ['eng']:
                            lang_code = 'en'

                        # Get voice config for this language
                        lang_voice_config = voices.get(lang_code, {})

                        # Determine voice based on customer's configuration for this language
                        if lang_voice_config.get('enableAlternation', True):
                            # Use alternating voice pattern for this language
                            voice = self._get_next_alternating_voice(
                                customer_id=article_customer_id,
                                language=article_language
                            )
                        else:
                            # Use default voice from config for this language
                            voice = lang_voice_config.get('defaultVoice', 'am_adam')

                        self.logger.info(
                            f"🎭 Using voice '{voice}' for article {article.get('id')} "
                            f"(customer: {article_customer_id}, lang: {lang_code}, "
                            f"alternation: {lang_voice_config.get('enableAlternation')})")

                        # Generate audio for article with selected voice
                        audio_result = self.generate_audio_for_article(
                            article,
                            voice=voice,
                            customer_id=article_customer_id
                        )
                        results['total_articles_processed'] += 1

                        if audio_result['success']:
                            results['total_articles_success'] += 1
                        else:
                            results['total_articles_failed'] += 1
                            results['errors'].append({
                                'article_id': audio_result['article_id'],
                                'error': audio_result['error']
                            })

                        # Add delay between generations to avoid overwhelming the service
                        if self.config.AUDIO_GENERATION_DELAY > 0:
                            time.sleep(self.config.AUDIO_GENERATION_DELAY)

                    except Exception as e:
                        results['total_articles_failed'] += 1
                        results['errors'].append({
                            'article_id': article.get('id', 'unknown'),
                            'error': f"Processing exception: {str(e)}"
                        })
                        self.logger.error(f"❌ Error processing article {article.get('id', 'unknown')}: {str(e)}")

                # Add delay between batches to avoid overwhelming the service
                if self.config.AUDIO_GENERATION_DELAY > 0:
                    self.logger.info(f"⏳ Waiting {self.config.AUDIO_GENERATION_DELAY}s before next batch...")
                    time.sleep(self.config.AUDIO_GENERATION_DELAY)

            results['processing_time_ms'] = int((time.time() - start_time) * 1000)

            job_type = "on-demand" if is_on_demand else "scheduled"
            self.logger.info(f"✅ Audio generation completed ({job_type}){customer_info}: "
                             f"{results['batches_processed']} batch(es), "
                             f"{results['total_articles_success']} success, "
                             f"{results['total_articles_failed']} failed")

        except Exception as e:
            results['errors'].append(f"Service error: {str(e)}")
            self.logger.error(f"❌ Error in news audio generation service: {str(e)}")

        return results
