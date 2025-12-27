"""
Base class for all content generation workflows

This provides a reusable foundation for:
- AI summary generation
- Summary parsing
- Audio generation for sections
- Template selection
- Video generation orchestration

Specific workflows (Product, Social Media, Blog, etc.) inherit from this class
and override methods as needed.
"""

import logging
import os
import requests
import subprocess
import tempfile
from datetime import datetime
from abc import ABC, abstractmethod
from bson import ObjectId

from .utils import (
    parse_ai_summary_to_sections,
    get_smart_audio_config,
    strip_markdown_for_tts,
    convert_audio_url_to_proxy,
    distribute_media_across_sections
)
from .prompt_template_handler import PromptTemplateHandler

logger = logging.getLogger(__name__)


class BaseContentGenerator(ABC):
    """
    Abstract base class for content generation workflows
    
    Provides default implementations for common operations:
    - AI summary generation via LLM service
    - Summary parsing into sections
    - Audio generation for each section
    - Template selection
    - Video generation orchestration
    
    Subclasses must implement:
    - get_default_prompt_template(): Return the default prompt template
    - get_content_type(): Return content type identifier (e.g., 'product_video')
    - build_prompt_context(): Build context data for prompt formatting
    """
    
    def __init__(self, db_collection, config=None, prompt_templates_collection=None):
        """
        Initialize the content generator

        Args:
            db_collection: MongoDB collection for storing content
            config: Optional configuration dict with service URLs
            prompt_templates_collection: Optional MongoDB collection for prompt templates
        """
        self.collection = db_collection
        self.config = config or {}

        # Service URLs
        self.llm_service_url = self.config.get(
            'llm_service_url',
            os.getenv('LLM_SERVICE_URL', 'http://ichat-llm-service:8083')
        )
        self.audio_service_url = self.config.get(
            'audio_service_url',
            os.getenv('AUDIO_GENERATION_URL', 'http://audio-generation-factory:3000')
        )
        self.template_service_url = self.config.get(
            'template_service_url',
            os.getenv('TEMPLATE_SERVICE_URL', 'http://ichat-template-service:5000')
        )
        self.video_generator_url = self.config.get(
            'video_generator_url',
            os.getenv('VIDEO_GENERATOR_URL', 'http://ichat-video-generator:8095')
        )

        # Initialize prompt template handler if collection provided
        self.prompt_template_handler = None
        if prompt_templates_collection is not None:
            self.prompt_template_handler = PromptTemplateHandler(
                prompt_templates_collection,
                self.llm_service_url
            )

        logger.info(f"Initialized {self.__class__.__name__} with LLM: {self.llm_service_url}")
    
    # ========== Abstract Methods (Must Override) ==========
    
    @abstractmethod
    def get_default_prompt_template(self):
        """
        Get the default prompt template for this content type
        
        Returns:
            str: Prompt template with placeholders like {product_name}, {description}, etc.
        """
        raise NotImplementedError("Subclasses must implement get_default_prompt_template()")
    
    @abstractmethod
    def get_content_type(self):
        """
        Get the content type identifier
        
        Returns:
            str: Content type (e.g., 'product_video', 'social_post', 'blog_article')
        """
        raise NotImplementedError("Subclasses must implement get_content_type()")
    
    @abstractmethod
    def build_prompt_context(self, content_id):
        """
        Build context data for prompt formatting
        
        Args:
            content_id: ID of the content item
            
        Returns:
            dict: Context data to format the prompt template
        """
        raise NotImplementedError("Subclasses must implement build_prompt_context()")
    
    # ========== Default Implementations (Can Override) ==========
    
    def parse_summary_to_sections(self, summary_text):
        """
        Parse AI summary into structured sections
        
        Default implementation uses markdown heading parsing.
        Override if you need custom parsing logic.
        
        Args:
            summary_text: AI-generated summary text
            
        Returns:
            list: List of section dictionaries
        """
        return parse_ai_summary_to_sections(summary_text)
    
    def get_audio_config_for_section(self, section_title, section_index, total_sections):
        """
        Get audio configuration for a section
        
        Default implementation uses smart audio config based on section title.
        Override for custom audio configuration logic.
        
        Args:
            section_title: Title of the section
            section_index: 0-based index
            total_sections: Total number of sections
            
        Returns:
            dict: Audio config with 'speed' and 'description'
        """
        return get_smart_audio_config(section_title, section_index, total_sections)

    # ========== Core Workflow Methods ==========

    def generate_ai_summary_with_template(
        self,
        content_id,
        template_id='product_summary_default_v1',
        customer_id='default',
        regenerate=False
    ):
        """
        Generate AI summary using a prompt template with structured JSON output

        This is the new method that uses the prompt template system.
        It generates structured JSON output that's validated against a schema.

        Args:
            content_id: ID of the content item
            template_id: ID of the prompt template to use
            customer_id: Customer ID for multi-tenancy
            regenerate: Force regeneration even if summary exists

        Returns:
            dict: Result with status, message, and ai_summary
        """
        try:
            if not self.prompt_template_handler:
                logger.warning("Prompt template handler not initialized, falling back to legacy method")
                return self.generate_ai_summary(content_id, regenerate=regenerate)

            logger.info(f"Generating AI summary with template {template_id} for {self.get_content_type()} {content_id}")

            # Get content from database
            content = self.collection.find_one({'_id': ObjectId(content_id)})
            if not content:
                return {
                    'status': 'error',
                    'message': 'Content not found'
                }

            # Check if summary already exists
            if content.get('ai_summary') and not regenerate:
                logger.info(f"AI summary already exists for {content_id}")
                return {
                    'status': 'success',
                    'message': 'AI summary already exists',
                    'ai_summary': content['ai_summary']
                }

            # Get prompt template
            template = self.prompt_template_handler.get_template(template_id, customer_id)
            if not template:
                logger.error(f"Template {template_id} not found")
                return {
                    'status': 'error',
                    'message': f'Template {template_id} not found'
                }

            # Build context for prompt formatting
            context = self.build_prompt_context(content_id)

            # Generate with JSON output
            result = self.prompt_template_handler.generate_with_json_output(
                template=template,
                context=context,
                max_retries=3,
                temperature=0.7,
                max_tokens=2000
            )

            if result['status'] != 'success':
                logger.error(f"Failed to generate summary: {result.get('message')}")
                return result

            # Extract structured data
            json_data = result['data']

            # Convert JSON structure to sections format
            sections = self._convert_json_to_sections(json_data, template)

            # Create structured AI summary object
            structured_summary = {
                'sections': sections,
                'json_data': json_data,  # Store the raw JSON data
                'full_text': result.get('raw_response', ''),
                'generated_at': datetime.utcnow(),
                'version': '3.0',  # New version for template-based generation
                'content_type': self.get_content_type(),
                'template_id': template_id
            }

            # Update content with AI summary
            self.collection.update_one(
                {'_id': ObjectId(content_id)},
                {
                    '$set': {
                        'ai_summary': structured_summary,
                        'updated_at': datetime.utcnow()
                    }
                }
            )

            logger.info(f"✅ Generated AI summary with template for {self.get_content_type()} {content_id}")

            return {
                'status': 'success',
                'message': 'AI summary generated successfully',
                'ai_summary': structured_summary
            }

        except Exception as e:
            logger.error(f"Error generating AI summary with template: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'message': str(e)
            }

    def _convert_json_to_sections(self, json_data: dict, template: dict) -> list:
        """
        Convert JSON data to sections format for backward compatibility

        Args:
            json_data: Structured JSON data from LLM
            template: Template document with output schema

        Returns:
            list: Sections in the format [{'title': ..., 'content': ...}, ...]
        """
        sections = []

        # Get the expected fields from the schema
        schema_properties = template['output_schema'].get('properties', {})

        # Convert each field to a section
        for field_name, field_schema in schema_properties.items():
            if field_name in json_data:
                # Convert field name to title (e.g., 'opening_hook' -> 'Opening Hook')
                title = field_name.replace('_', ' ').title()
                content = json_data[field_name]

                # Handle arrays (like key_features)
                if isinstance(content, list):
                    content = '\n'.join(f"• {item}" for item in content)

                sections.append({
                    'title': title,
                    'content': content
                })

        return sections

    def generate_ai_summary(self, content_id, custom_prompt=None, regenerate=False):
        """
        Generate AI summary for content

        This is the main method that orchestrates AI summary generation.
        It can be called by subclasses or used directly.

        Args:
            content_id: ID of the content item
            custom_prompt: Optional custom prompt (overrides default)
            regenerate: Force regeneration even if summary exists

        Returns:
            dict: Result with status, message, and ai_summary
        """
        try:
            logger.info(f"Generating AI summary for {self.get_content_type()} {content_id}")

            # Get content from database
            content = self.collection.find_one({'_id': ObjectId(content_id)})
            if not content:
                return {
                    'status': 'error',
                    'message': 'Content not found'
                }

            # Check if summary already exists
            if content.get('ai_summary') and not regenerate:
                logger.info(f"AI summary already exists for {content_id}")
                return {
                    'status': 'success',
                    'message': 'AI summary already exists',
                    'ai_summary': content['ai_summary']
                }

            # Build prompt
            if custom_prompt:
                prompt = custom_prompt
            else:
                # Get default template and format with context
                template = self.get_default_prompt_template()
                context = self.build_prompt_context(content_id)
                prompt = template.format(**context)

            logger.info(f"Calling LLM service with prompt length: {len(prompt)}")

            # Call LLM service
            response = requests.post(
                f"{self.llm_service_url}/llm/generate",
                json={
                    "query": prompt,
                    "use_rag": False,
                    "detect_code": False,
                    "temperature": 0.7,
                    "max_tokens": 1000
                },
                timeout=60
            )

            if response.status_code != 200:
                error_msg = f"LLM service returned {response.status_code}: {response.text}"
                logger.error(error_msg)
                return {
                    'status': 'error',
                    'message': 'Failed to generate summary',
                    'details': error_msg
                }

            summary_text = response.json().get('response', '')
            logger.info(f"Generated summary: {summary_text[:100]}...")

            # Parse summary into sections
            sections = self.parse_summary_to_sections(summary_text)
            logger.info(f"Parsed {len(sections)} sections from AI summary")

            # Create structured AI summary object
            structured_summary = {
                'sections': sections,
                'full_text': summary_text,
                'generated_at': datetime.utcnow(),
                'version': '2.0',
                'content_type': self.get_content_type()
            }

            # Update content with AI summary
            self.collection.update_one(
                {'_id': ObjectId(content_id)},
                {
                    '$set': {
                        'ai_summary': structured_summary,
                        'updated_at': datetime.utcnow()
                    }
                }
            )

            logger.info(f"✅ Generated AI summary for {self.get_content_type()} {content_id}")

            return {
                'status': 'success',
                'message': 'Summary generated successfully',
                'ai_summary': structured_summary
            }

        except Exception as e:
            logger.error(f"Error generating AI summary: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'message': str(e)
            }

    def generate_audio_for_sections(self, content_id, audio_config=None):
        """
        Generate audio for each section of the AI summary

        Args:
            content_id: ID of the content item
            audio_config: Optional audio configuration dict with:
                - voice: Voice ID (default: 'am_adam')
                - model: TTS model (default: 'kokoro-82m')
                - language: Language code (default: 'en')
                - section_pitches: Dict mapping section titles to speed overrides

        Returns:
            dict: Result with status, section_audio_urls, and total_duration
        """
        try:
            logger.info(f"Generating audio for {self.get_content_type()} {content_id}")

            # Get content from database
            content = self.collection.find_one({'_id': ObjectId(content_id)})
            if not content:
                return {
                    'status': 'error',
                    'message': 'Content not found'
                }

            # Get AI summary
            ai_summary = content.get('ai_summary')
            if not ai_summary:
                return {
                    'status': 'error',
                    'message': 'No AI summary found. Generate summary first.'
                }

            # Extract sections
            if isinstance(ai_summary, dict):
                sections = ai_summary.get('sections', [])
            else:
                # Legacy format - parse from text
                sections = self.parse_summary_to_sections(ai_summary)

            if not sections:
                return {
                    'status': 'error',
                    'message': 'Could not parse AI summary into sections'
                }

            # Get audio configuration
            config = audio_config or {}
            voice = config.get('voice', 'am_adam')
            model = config.get('model', 'kokoro-82m')
            language = config.get('language', 'en')
            section_pitches = config.get('sectionPitches', {})

            # Generate audio for each section
            section_audio_urls = []
            total_duration = 0

            for idx, section in enumerate(sections):
                section_title = section.get('title', f'Section {idx + 1}')
                section_content = section.get('content', '')

                if not section_content:
                    logger.warning(f"Section '{section_title}' has no content, skipping")
                    continue

                # Get smart audio configuration
                smart_config = self.get_audio_config_for_section(
                    section_title, idx, len(sections)
                )

                # Get speed (user override or smart default)
                speed = section_pitches.get(section_title, smart_config['speed'])

                logger.info(f"🎙️ Section {idx + 1}/{len(sections)}: '{section_title}'")
                logger.info(f"   {smart_config['description']}")
                logger.info(f"   Speed: {speed}x")

                # Strip markdown before TTS
                clean_text = strip_markdown_for_tts(section_content)

                # Call audio generation service
                try:
                    # Generate filename for this section
                    section_filename = f"{content_id}_section_{idx+1}_{section_title.lower().replace(' ', '_')}.wav"

                    response = requests.post(
                        f"{self.audio_service_url}/tts",
                        json={
                            "text": clean_text,
                            "voice": voice,
                            "model": model,
                            "speed": speed,
                            "format": "wav",
                            "product_id": content_id,  # Pass product_id to save in product folder
                            "filename": section_filename
                        },
                        timeout=600  # 10 minutes for model initialization
                    )

                    if response.status_code != 200:
                        logger.error(f"Audio generation failed for '{section_title}': {response.text}")
                        return {
                            'status': 'error',
                            'message': f'Failed to generate audio for section: {section_title}'
                        }

                    result = response.json()
                    # Use direct audio-generation-factory URL (not proxy)
                    # This will be accessible from template service via Docker network
                    internal_audio_url = f"{self.audio_service_url}{result.get('audio_url', '')}"
                    duration = result.get('audio_info', {}).get('duration', 0)

                    section_audio_urls.append(internal_audio_url)
                    total_duration += duration

                    # Update section with audio info
                    section['audio_path'] = internal_audio_url
                    section['audio_config'] = {
                        'speed': speed,
                        'voice': voice,
                        'duration': duration
                    }

                    logger.info(f"✅ Generated audio for '{section_title}': {duration:.2f}s")

                except requests.exceptions.Timeout:
                    logger.error(f"Timeout generating audio for '{section_title}'")
                    return {
                        'status': 'error',
                        'message': f'Timeout generating audio for section: {section_title}'
                    }
                except Exception as e:
                    logger.error(f"Error generating audio for '{section_title}': {str(e)}")
                    return {
                        'status': 'error',
                        'message': f'Error generating audio: {str(e)}'
                    }

            logger.info(f"✅ Generated {len(section_audio_urls)} audio files, total: {total_duration:.2f}s")

            # Concatenate all section audio files into a single file
            combined_audio_url = None
            try:
                combined_audio_url = self._concatenate_section_audio(
                    content_id, section_audio_urls
                )
                logger.info(f"✅ Concatenated audio URL: {combined_audio_url}")
            except Exception as e:
                logger.error(f"Failed to concatenate audio files: {str(e)}")
                # Continue without combined audio - sections still work

            # Update content with audio information
            self.collection.update_one(
                {'_id': ObjectId(content_id)},
                {
                    '$set': {
                        'ai_summary.sections': sections,
                        'audio_url': combined_audio_url,
                        'section_audio_urls': section_audio_urls,
                        'updated_at': datetime.utcnow()
                    }
                }
            )

            return {
                'status': 'success',
                'message': f'Audio generated for {len(section_audio_urls)} sections',
                'audio_url': combined_audio_url,
                'section_audio_urls': section_audio_urls,
                'total_duration': total_duration,
                'audio_config': {
                    'voice': voice,
                    'model': model,
                    'language': language,
                    'section_count': len(section_audio_urls)
                }
            }

        except Exception as e:
            logger.error(f"Error generating audio: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'message': str(e)
            }

    def _concatenate_section_audio(self, content_id, section_audio_urls):
        """
        Concatenate multiple section audio files into a single audio file

        Args:
            content_id: Content ID for naming the output file
            section_audio_urls: List of audio URLs (proxy URLs)

        Returns:
            str: URL of the concatenated audio file
        """
        if not section_audio_urls:
            return None

        logger.info(f"🔗 Concatenating {len(section_audio_urls)} audio files...")

        # Download all section audio files to temp directory
        temp_files = []
        try:
            for idx, audio_url in enumerate(section_audio_urls):
                # audio_url is already the direct internal URL (e.g., http://audio-generation-factory:3000/product/{id}/file.wav)
                # No conversion needed
                response = requests.get(audio_url, timeout=30)
                if response.status_code != 200:
                    raise Exception(f"Failed to download audio {idx}: {response.status_code}")

                # Save to temp file
                temp_file = tempfile.NamedTemporaryFile(
                    delete=False, suffix=f'_section_{idx}.wav'
                )
                temp_file.write(response.content)
                temp_file.close()
                temp_files.append(temp_file.name)
                logger.info(f"  Downloaded section {idx+1}/{len(section_audio_urls)}")

            # Create output filename
            output_filename = f"{content_id}_combined.wav"
            output_path = f"/tmp/{output_filename}"

            # Use ffmpeg to concatenate audio files
            # Create concat file list
            concat_list_path = tempfile.NamedTemporaryFile(
                mode='w', delete=False, suffix='.txt'
            )
            for temp_file in temp_files:
                concat_list_path.write(f"file '{temp_file}'\n")
            concat_list_path.close()

            # Run ffmpeg concat
            cmd = [
                'ffmpeg', '-y',
                '-f', 'concat',
                '-safe', '0',
                '-i', concat_list_path.name,
                '-c', 'copy',
                output_path
            ]

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=60
            )

            if result.returncode != 0:
                logger.error(f"FFmpeg error: {result.stderr}")
                raise Exception(f"FFmpeg concatenation failed: {result.stderr}")

            # Upload concatenated file to audio service
            with open(output_path, 'rb') as f:
                files = {'file': (output_filename, f, 'audio/wav')}
                # Pass product_id to save in product folder
                data = {'product_id': content_id}
                upload_response = requests.post(
                    f"{self.audio_service_url}/upload",
                    files=files,
                    data=data,
                    timeout=60
                )

                if upload_response.status_code != 200:
                    raise Exception(f"Failed to upload combined audio: {upload_response.status_code}")

                result = upload_response.json()
                # Use direct audio-generation-factory URL (not proxy)
                # This will be accessible from template service via Docker network
                internal_url = f"{self.audio_service_url}{result.get('audio_url', '')}"

                logger.info(f"✅ Combined audio uploaded: {internal_url}")
                return internal_url

        finally:
            # Clean up temp files
            for temp_file in temp_files:
                try:
                    os.unlink(temp_file)
                except:
                    pass
            try:
                os.unlink(concat_list_path.name)
            except:
                pass
            try:
                os.unlink(output_path)
            except:
                pass

    def generate_video(self, content_id, template_id, template_variables=None,
                      distribution_mode='auto', section_mapping=None):
        """
        Generate video using template service

        Args:
            content_id: ID of the content (product, blog, etc.)
            template_id: Template ID to use
            template_variables: Dict of template variables
            distribution_mode: 'auto' or 'manual' for media distribution
            section_mapping: Manual section-to-media mapping

        Returns:
            Dict with status and video URL or error message
        """
        try:
            logger.info(f"🎬 Generating video for content {content_id}")

            # Get content
            content = self.collection.find_one({'_id': ObjectId(content_id)})
            if not content:
                return {
                    'status': 'error',
                    'message': 'Content not found'
                }

            # Validate required fields
            if not content.get('ai_summary'):
                return {
                    'status': 'error',
                    'message': 'No AI summary found. Generate summary first.'
                }

            if not content.get('audio_url'):
                return {
                    'status': 'error',
                    'message': 'No audio found. Generate audio first.'
                }

            # Get AI summary sections
            ai_summary = content.get('ai_summary', {})
            sections = []
            if isinstance(ai_summary, dict) and 'sections' in ai_summary:
                sections = ai_summary['sections']

            # If template_id not provided or is 'default', use the one from product
            if not template_id or template_id == 'default':
                if content.get('template_id'):
                    template_id = content['template_id']
                    logger.info(f"📦 Using template_id from product: {template_id}")
                else:
                    logger.warning(f"⚠️ No template_id in product, using 'default'")
                    template_id = 'default'

            # If template_variables not provided, build from product data
            if not template_variables:
                logger.info(f"📦 No template_variables provided, building from product data")

                # Get template_variables from product if available
                template_variables = content.get('template_variables', {})

                if template_variables:
                    logger.info(f"  ✅ Loaded template_variables from product")
                    logger.info(f"  📋 Keys: {list(template_variables.keys())}")
                else:
                    logger.warning(f"  ⚠️ No template_variables found in product")
                    template_variables = {}

                # Add audio URL if not in template_variables
                if not template_variables.get('audio_url') and content.get('audio_url'):
                    template_variables['audio_url'] = content['audio_url']
                    logger.info(f"  ✅ Added audio URL from product")

            # Extract media from template_variables
            media_files = []

            # Debug: Log template_variables keys
            logger.info(f"📋 Template variables keys: {list(template_variables.keys())}")

            # Log the actual values for debugging
            for key, value in template_variables.items():
                if isinstance(value, list):
                    logger.info(f"  📋 {key}: {len(value)} items")
                    if len(value) > 0:
                        logger.info(f"     First item: {value[0]}")

            for key, value in template_variables.items():
                if key.endswith('_timings') or not isinstance(value, list):
                    continue

                if key.endswith('_images') or 'image' in key.lower():
                    logger.info(f"  ✅ Found image key: {key} with {len(value) if isinstance(value, list) else 0} items")
                    media_files.extend([
                        {'url': url, 'type': 'image'}
                        for url in value if isinstance(url, str)
                    ])
                elif key.endswith('_videos') or 'video' in key.lower():
                    logger.info(f"  ✅ Found video key: {key} with {len(value) if isinstance(value, list) else 0} items")
                    media_files.extend([
                        {'url': url, 'type': 'video'}
                        for url in value if isinstance(url, str)
                    ])

            logger.info(f"📦 Extracted {len(media_files)} media files from template_variables")

            # Log the extracted media files
            if media_files:
                logger.info(f"📋 Extracted media files:")
                for i, media in enumerate(media_files[:5]):  # Log first 5
                    logger.info(f"  {i+1}. {media['type']}: {media['url']}")

            # If section_mapping not provided, try to get from product
            if not section_mapping and content.get('section_mapping'):
                section_mapping = content['section_mapping']
                distribution_mode = 'manual'
                logger.info(f"📦 Using section_mapping from product data (manual mode)")

            # Distribute media across sections
            if media_files and sections:
                logger.info(f"🎬 Calculating timings for {len(media_files)} media files across {len(sections)} sections")

                # Debug: Log section structure
                logger.info(f"📋 Section structure check:")
                for i, section in enumerate(sections):
                    section_title = section.get('title', 'Unknown')
                    audio_config = section.get('audio_config', {})
                    duration = audio_config.get('duration', 'N/A')
                    logger.info(f"  Section {i+1}: {section_title} - duration: {duration}s")

                logger.info(f"🔧 Calling distribute_media_across_sections with:")
                logger.info(f"  - media_files count: {len(media_files)}")
                logger.info(f"  - sections count: {len(sections)}")
                logger.info(f"  - distribution_mode: {distribution_mode}")
                logger.info(f"  - section_mapping: {section_mapping}")

                result = distribute_media_across_sections(
                    media_files,
                    sections,
                    distribution_mode,
                    section_mapping
                )

                media_list = result['media_list']
                images_list = result['images_list']
                videos_list = result['videos_list']

                logger.info(f"📊 Distribution result:")
                logger.info(f"  - media_list count: {len(media_list)}")
                logger.info(f"  - images_list count: {len(images_list)}")
                logger.info(f"  - videos_list count: {len(videos_list)}")

                # Log media sequence
                logger.info(f"⏱️ Media sequence:")
                for i, item in enumerate(media_list):
                    media_type_icon = '🖼️' if item.get('type') == 'image' else '🎥'
                    logger.info(f"  {media_type_icon} Media {i+1}: {item['duration']:.2f}s ({item['type']})")

                # Send as dynamic_media (single merged array with timing info)
                # Template service will create clips and concatenate
                template_variables['dynamic_media'] = media_list

                # Also keep the old format for backward compatibility
                template_variables['product_images'] = images_list
                template_variables['product_videos'] = videos_list

                logger.info(f"✅ Prepared {len(media_list)} media items for template service")
            else:
                logger.info(f"ℹ️ Skipping timing calculation (media: {len(media_files) if media_files else 0}, sections: {len(sections) if sections else 0})")

            # Add audio URL
            template_variables['audio_url'] = content.get('audio_url')

            # Call video generator service
            video_url = self._call_video_generator(
                template_id,
                template_variables,
                content.get('customer_id')
            )

            if not video_url:
                return {
                    'status': 'error',
                    'message': 'Failed to generate video'
                }

            # Update content with video URL
            self.collection.update_one(
                {'_id': ObjectId(content_id)},
                {
                    '$set': {
                        'video_url': video_url,  # Also save at top level for easy access
                        'generated_video': {
                            'video_url': video_url,  # Changed from 'url' to 'video_url' for frontend compatibility
                            'status': 'completed',
                            'template_id': template_id,
                            'generated_at': datetime.utcnow()
                        },
                        'updated_at': datetime.utcnow()
                    }
                }
            )

            return {
                'status': 'success',
                'message': 'Video generated successfully',
                'video_url': video_url
            }

        except Exception as e:
            logger.error(f"Error generating video: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'message': str(e)
            }

    def _call_video_generator(
        self, template_id, template_variables, customer_id=None
    ):
        """
        Call template service to generate video

        This method follows the same approach as ecommerce service:
        1. Fetch the full template object
        2. Call /api/templates/preview with template, sample_data,
           and audio_url

        Args:
            template_id: Template ID
            template_variables: Template variables dict
                               (must include 'audio_url')
            customer_id: Customer ID for multi-tenant context

        Returns:
            Video URL or None
        """
        try:
            # Prepare headers with customer context
            headers = {'Content-Type': 'application/json'}
            if customer_id:
                headers['X-Customer-ID'] = customer_id

            # Step 1: Fetch the full template object
            logger.info(f"🎬 Fetching template {template_id}")
            template_response = requests.get(
                f"{self.template_service_url}/api/templates/{template_id}",
                headers=headers,
                timeout=30
            )

            if template_response.status_code != 200:
                logger.error(
                    f"Failed to fetch template {template_id}: "
                    f"{template_response.text}"
                )
                return None

            template = template_response.json().get('template', {})
            template_name = template.get('name', 'unnamed')
            logger.info(f"✅ Fetched template: {template_name}")

            # Step 2: Extract audio_url from template_variables
            audio_url = template_variables.get('audio_url')
            if not audio_url:
                logger.error(
                    "No audio_url provided in template_variables"
                )
                return None

            logger.info(f"🎵 Using audio URL: {audio_url}")

            # Log what we're sending to template service
            logger.info(f"📤 Sending to template service:")
            logger.info(f"  - template_id: {template_id}")
            logger.info(f"  - template_name: {template_name}")
            logger.info(f"  - sample_data keys: {list(template_variables.keys())}")

            # Log dynamic_media if present
            if 'dynamic_media' in template_variables:
                logger.info(f"  - dynamic_media: {len(template_variables['dynamic_media'])} items")
                for i, item in enumerate(template_variables['dynamic_media'][:3]):
                    logger.info(f"    {i+1}. {item.get('type')}: {item.get('url')} ({item.get('duration')}s)")

            # Log dynamic_images and dynamic_videos if present
            if 'dynamic_images' in template_variables:
                logger.info(f"  - dynamic_images: {len(template_variables['dynamic_images'])} items")
            if 'dynamic_videos' in template_variables:
                logger.info(f"  - dynamic_videos: {len(template_variables['dynamic_videos'])} items")

            # Step 3: Call template service preview endpoint
            # This is the same endpoint ecommerce service uses
            response = requests.post(
                f"{self.template_service_url}/api/templates/preview",
                json={
                    'template': template,
                    'sample_data': template_variables,
                    'is_initial': False,
                    'audio_url': audio_url,
                    'output_path': f"videos/content_{template_id}.mp4"
                },
                headers=headers,
                timeout=600  # Increased to 10 minutes for complex videos with many assets
            )

            if response.status_code == 200:
                data = response.json()
                video_url = data.get('preview_url')
                logger.info(f"✅ Video generated: {video_url}")
                return video_url
            else:
                logger.error(
                    f"Video generator error: {response.status_code} - "
                    f"{response.text}"
                )
                return None

        except Exception as e:
            logger.error(
                f"Error calling video generator: {str(e)}",
                exc_info=True
            )
            return None
