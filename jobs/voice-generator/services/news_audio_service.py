"""
News Audio Service - Generate audio for news articles using audio-generation service
"""

import os
import logging
import requests
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from pymongo import MongoClient
from config.settings import Config


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
    
    def get_articles_needing_audio(self, limit: int = None) -> List[Dict[str, Any]]:
        """
        Get articles that need audio generation (audio_path is null)
        
        Args:
            limit: Maximum number of articles to return
            
        Returns:
            List of news articles needing audio generation
        """
        try:
            # Query for articles with no audio_paths and have content
            # Comprehensive check for articles without audio generation:
            # 1. audio_paths field doesn't exist
            # 2. audio_paths is null
            # 3. audio_paths is empty object {}
            # 4. audio_paths exists but is missing required fields (title, description, content)
            query = {
                '$and': [
                    {
                        '$or': [
                            {'audio_paths': {'$exists': False}},  # Field doesn't exist
                            {'audio_paths': None},  # Field is null
                            {'audio_paths': {}},  # Field is empty object
                            {'audio_paths': {'$in': [None, {}]}},  # Field is null or empty
                            # Check if any of the required audio fields are missing
                            {'audio_paths.title': {'$exists': False}},
                            {'audio_paths.description': {'$exists': False}},
                            {'audio_paths.content': {'$exists': False}}
                        ]
                    },
                    {'status': {'$in': ['completed', 'published']}},  # Only completed articles
                    {'$or': [
                        {'content': {'$exists': True, '$ne': '', '$ne': None}},
                        {'description': {'$exists': True, '$ne': '', '$ne': None}}
                    ]}
                ]
            }
            
            cursor = self.news_collection.find(query).sort('created_at', -1)
            if limit:
                cursor = cursor.limit(limit)
                
            articles = list(cursor)
            self.logger.info(f"📰 Found {len(articles)} articles needing audio generation")
            return articles
            
        except Exception as e:
            self.logger.error(f"❌ Error getting articles needing audio: {str(e)}")
            return []
    
    def generate_audio_for_article(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate audio for a single article (title, description, content)

        Args:
            article: News article document

        Returns:
            Dictionary with generation results
        """
        result = {
            'article_id': article.get('id', 'unknown'),
            'success': False,
            'audio_paths': {},
            'error': None,
            'generation_time_ms': 0
        }

        try:
            article_id = article.get('id', 'unknown')
            self.logger.info(f"🎵 Generating audio for article: {article_id}")

            # Determine language and model
            language = article.get('lang', 'en')
            model = self._get_audio_model_for_language(language)
            self.logger.info(f"🌍 Article language: {language}, Selected model: {model}")
            self.logger.info(f"🔧 DEFAULT_AUDIO_MODEL: {self.config.DEFAULT_AUDIO_MODEL}")
            self.logger.info(f"🔧 HINDI_AUDIO_MODEL: {self.config.HINDI_AUDIO_MODEL}")

            # Create public directory structure
            import os
            public_dir = "/app/public"
            article_dir = os.path.join(public_dir, str(article_id))
            os.makedirs(article_dir, exist_ok=True)

            # Fields to generate audio for
            audio_fields = {
                'title': article.get('title', ''),
                'description': article.get('description', ''),
                'content': article.get('content', ''),
                'short_summary': article.get('short_summary', '')
            }

            total_start_time = time.time()
            generated_paths = {}

            # Generate audio for each field
            for field_name, text_content in audio_fields.items():
                if not text_content or not text_content.strip():
                    self.logger.warning(f"⚠️ No {field_name} content found for article {article_id}")
                    continue

                # Truncate content if too long
                if field_name == 'content' and len(text_content) > self.config.MAX_TEXT_LENGTH:
                    text_content = text_content[:self.config.MAX_TEXT_LENGTH].rsplit(' ', 1)[0] + "..."

                self.logger.info(f"🔊 Generating {field_name} audio for article {article_id}")

                # Generate audio via audio-generation service
                audio_result = self._call_audio_generation_service(text_content.strip(), model)

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
                    self.logger.error(f"❌ Failed to generate {field_name} audio: {audio_result.get('error', 'Unknown error')}")

            generation_time = int((time.time() - total_start_time) * 1000)

            if generated_paths:
                # Update article with audio paths
                update_result = self.news_collection.update_one(
                    {'id': article_id},
                    {
                        '$set': {
                            'audio_paths': generated_paths,
                            'updated_at': datetime.utcnow()
                        }
                    }
                )

                if update_result.modified_count > 0:
                    result['success'] = True
                    result['audio_paths'] = generated_paths
                    result['generation_time_ms'] = generation_time
                    self.logger.info(f"✅ All audio files generated for article {article_id}: {list(generated_paths.keys())}")
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
        
        # Last resort: truncated content
        elif article.get('content'):
            content = article['content'].strip()
            if len(content) > self.config.MAX_TEXT_LENGTH:
                # Truncate at word boundary
                text_content = content[:self.config.MAX_TEXT_LENGTH].rsplit(' ', 1)[0] + "..."
            else:
                text_content = content
        
        return text_content if text_content else None
    
    def _get_audio_model_for_language(self, language: str) -> str:
        """
        Get appropriate audio model for language
        
        Args:
            language: Language code (e.g., 'en', 'hi')
            
        Returns:
            Model name for audio generation
        """
        # Map language codes to models
        language_models = {
            'hi': self.config.HINDI_AUDIO_MODEL,  # Hindi
            'hin': self.config.HINDI_AUDIO_MODEL,  # Hindi (alternative code)
            'en': self.config.DEFAULT_AUDIO_MODEL,  # English
            'eng': self.config.DEFAULT_AUDIO_MODEL,  # English (alternative code)
        }
        
        return language_models.get(language.lower(), self.config.DEFAULT_AUDIO_MODEL)
    
    def _call_audio_generation_service(self, text: str, model: str) -> Dict[str, Any]:
        """
        Call the audio-generation service to generate TTS

        Args:
            text: Text to convert to speech
            model: TTS model to use

        Returns:
            Dictionary with generation results
        """
        try:
            url = f"{self.config.AUDIO_GENERATION_SERVICE_URL}/tts"
            payload = {
                'text': text,
                'model': model,
                'format': 'wav',
                'voice': 'am_adam'  # Default male voice for Kokoro model
            }

            self.logger.info(f"🔊 Calling audio generation service: {url}")
            self.logger.info(f"📝 Text length: {len(text)} chars, Model: {model}")
            self.logger.info(f"📦 Payload: {payload}")

            # Use extended timeout for Kokoro model (10 minutes) as it takes longer to generate
            timeout = 600 if model == 'kokoro-82m' else self.config.AUDIO_GENERATION_TIMEOUT
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
    
    def process_news_audio_generation(self, job_id: str = None, is_on_demand: bool = False) -> Dict[str, Any]:
        """
        Process audio generation for multiple news articles
        Continues processing until all articles have audio generated

        Args:
            job_id: Job ID for tracking
            is_on_demand: Whether this is an on-demand job execution

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

        try:
            # Continue processing until no more articles need audio
            while True:
                # Get articles needing audio generation (batch processing)
                articles = self.get_articles_needing_audio(limit=self.config.AUDIO_BATCH_SIZE)

                if not articles:
                    self.logger.info(f"✅ No more articles found needing audio generation for job {job_id}")
                    break

                results['batches_processed'] += 1
                batch_articles_found = len(articles)
                results['total_articles_found'] += batch_articles_found

                self.logger.info(f"🎵 Processing batch {results['batches_processed']}: {batch_articles_found} articles for audio generation in job {job_id}")

                # Process each article in the current batch
                for article in articles:
                    try:
                        # Generate audio for article
                        audio_result = self.generate_audio_for_article(article)
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

            self.logger.info(f"✅ Audio generation completed for job {job_id}: "
                           f"{results['batches_processed']} batches, "
                           f"{results['total_articles_success']} success, "
                           f"{results['total_articles_failed']} failed")

        except Exception as e:
            results['errors'].append(f"Service error: {str(e)}")
            self.logger.error(f"❌ Error in news audio generation service: {str(e)}")

        return results
