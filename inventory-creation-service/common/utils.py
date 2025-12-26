"""
Shared utility functions for content generation workflows
"""

import re
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Service URLs - can be overridden by environment variables
AUDIO_GENERATION_URL = os.getenv('AUDIO_GENERATION_URL', 'http://audio-generation-factory:3000')
API_SERVER_URL = os.getenv('API_SERVER_EXTERNAL_URL', 'http://localhost:8080')


def serialize_document(doc):
    """
    Convert MongoDB document to JSON-serializable dict
    
    Args:
        doc: MongoDB document
        
    Returns:
        dict: JSON-serializable dictionary
    """
    if doc:
        doc['_id'] = str(doc['_id'])
        if 'created_at' in doc and isinstance(doc['created_at'], datetime):
            doc['created_at'] = doc['created_at'].isoformat()
        if 'updated_at' in doc and isinstance(doc['updated_at'], datetime):
            doc['updated_at'] = doc['updated_at'].isoformat()
        # Backward compatibility: provide both 'name' and 'product_name' for products
        if 'name' in doc:
            doc['product_name'] = doc['name']
    return doc


def strip_markdown_for_tts(text):
    """
    Strip markdown syntax from text for TTS (Text-to-Speech)
    
    Removes:
    - ### headings
    - ** bold markers
    - * italic markers
    - Other markdown syntax that shouldn't be spoken
    
    Args:
        text: Text with markdown
        
    Returns:
        str: Clean text for TTS
    """
    if not text:
        return text

    # Remove markdown headings (###, ##, #)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    
    # Remove bold markers (**text** or __text__)
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'__(.+?)__', r'\1', text)
    
    # Remove italic markers (*text* or _text_)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'_(.+?)_', r'\1', text)
    
    # Remove inline code markers (`code`)
    text = re.sub(r'`(.+?)`', r'\1', text)
    
    # Remove links [text](url) -> text
    text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)
    
    # Remove bullet points
    text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
    
    # Remove numbered lists
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
    
    return text.strip()


def convert_audio_url_to_proxy(audio_url):
    """
    Convert internal audio-generation-factory URL to API server proxy URL
    
    Args:
        audio_url: Internal URL like http://audio-generation-factory:3000/temp/file.wav
        
    Returns:
        str: Proxy URL like http://localhost:8080/api/audio/proxy/temp/file.wav
    """
    if not audio_url:
        return audio_url

    # Extract the path after the audio-generation-factory domain
    if AUDIO_GENERATION_URL in audio_url:
        relative_path = audio_url.replace(AUDIO_GENERATION_URL, '').lstrip('/')
        proxy_url = f"{API_SERVER_URL}/api/audio/proxy/{relative_path}"
        logger.debug(f"Converted audio URL: {audio_url} -> {proxy_url}")
        return proxy_url

    # If it's already a proxy URL or some other format, return as-is
    return audio_url


def parse_ai_summary_to_sections(ai_summary_text):
    """
    Parse AI summary text into structured sections
    
    Expected format:
    ## Opening Hook
    Content here...
    
    ## Product Introduction
    Content here...
    
    ## Key Features & Benefits
    **Feature 1:** Description
    **Feature 2:** Description
    
    ## Social Proof & Trust
    Content here...
    
    ## Call-to-Action
    Content here...
    
    Args:
        ai_summary_text: AI-generated summary text
        
    Returns:
        list: List of section dictionaries with title, content, order, etc.
    """
    if not ai_summary_text:
        return []

    sections = []

    # First, try to split by markdown headings (## Section Name)
    normalized_text = ai_summary_text
    if ai_summary_text.strip().startswith('##'):
        normalized_text = '\n' + ai_summary_text

    parts = re.split(r'\n##\s+', normalized_text)

    # Check if we found any sections with ##
    has_markdown_headers = len(parts) > 1

    if has_markdown_headers:
        # First part might be empty now (if we added \n at start)
        if not parts[0].strip():
            parts = parts[1:]

        order = 1
        for part in parts:
            if not part.strip():
                continue

            # Split into title and content
            lines = part.strip().split('\n', 1)
            title = lines[0].strip()

            # Remove ## prefix if it exists
            if title.startswith('##'):
                title = title[2:].strip()

            content = lines[1].strip() if len(lines) > 1 else ""

            sections.append({
                "title": title,
                "content": content,
                "order": order,
                "audio_path": None,
                "video_path": None,
                "audio_config": {
                    "speed": 1.0,
                    "voice": None,
                    "duration": 0
                }
            })
            order += 1
    else:
        # Fallback: Try to detect sections by common section titles
        common_sections = [
            'Opening Hook',
            'Product Introduction',
            'Key Features & Benefits',
            'Social Proof & Trust',
            'Call-to-Action',
            'Introduction',
            'Features',
            'Benefits',
            'Conclusion'
        ]

        # Build regex pattern to match section titles
        section_pattern = re.compile(
            r'^(' + '|'.join(re.escape(s) for s in common_sections) + r')\s*$',
            re.MULTILINE | re.IGNORECASE
        )

        # Find all section title matches
        matches = list(section_pattern.finditer(ai_summary_text))

        if matches:
            order = 1
            for i, match in enumerate(matches):
                title = match.group(1).strip()
                start_pos = match.end()

                # Content is from end of title to start of next title
                if i < len(matches) - 1:
                    end_pos = matches[i + 1].start()
                else:
                    end_pos = len(ai_summary_text)

                content = ai_summary_text[start_pos:end_pos].strip()

                sections.append({
                    "title": title,
                    "content": content,
                    "order": order,
                    "audio_path": None,
                    "video_path": None,
                    "audio_config": {
                        "speed": 1.0,
                        "voice": None,
                        "duration": 0
                    }
                })
                order += 1

    return sections


def get_smart_audio_config(section_title, section_index, total_sections):
    """
    Get intelligent audio configuration for a section to create engaging storytelling

    This creates a natural narrative arc:
    - Opening: Energetic and attention-grabbing
    - Middle: Clear, informative, slightly varied
    - Closing: Confident and motivating

    Args:
        section_title: Title of the section
        section_index: 0-based index of the section
        total_sections: Total number of sections

    Returns:
        dict: Audio configuration with speed and description
    """
    section_lower = section_title.lower()

    # Default configuration
    config = {
        'speed': 1.0,
        'description': 'Standard narration'
    }

    # 1. OPENING HOOK - Fast, energetic, attention-grabbing
    if 'hook' in section_lower or 'opening' in section_lower or section_index == 0:
        config.update({
            'speed': 1.1,
            'description': '⚡ Energetic opening to grab attention'
        })

    # 2. PRODUCT INTRODUCTION - Warm, welcoming, clear
    elif 'introduction' in section_lower or 'intro' in section_lower or section_index == 1:
        config.update({
            'speed': 1.0,
            'description': '👋 Warm and welcoming introduction'
        })

    # 3. KEY FEATURES & BENEFITS - Slower, clear, informative
    elif 'feature' in section_lower or 'benefit' in section_lower:
        config.update({
            'speed': 0.95,
            'description': '📋 Clear and informative feature presentation'
        })

    # 4. SOCIAL PROOF & TRUST - Confident, steady
    elif 'proof' in section_lower or 'trust' in section_lower or 'testimonial' in section_lower:
        config.update({
            'speed': 1.0,
            'description': '✅ Confident and trustworthy tone'
        })

    # 5. CALL-TO-ACTION - Energetic, motivating
    elif 'call' in section_lower or 'action' in section_lower or 'cta' in section_lower:
        config.update({
            'speed': 1.05,
            'description': '🎯 Energetic and motivating call-to-action'
        })

    # 6. CLOSING/CONCLUSION - Confident, final
    elif 'closing' in section_lower or 'conclusion' in section_lower or section_index == total_sections - 1:
        config.update({
            'speed': 1.0,
            'description': '🎬 Confident closing statement'
        })

    return config


def get_section_speed(section_title, section_pitches, section_index=0, total_sections=5):
    """
    Get speed for a section based on user preferences or smart defaults

    Uses intelligent defaults that create a natural storytelling arc:
    - Opening Hook: 1.1x (energetic)
    - Product Introduction: 1.0x (welcoming)
    - Key Features: 0.95x (clear, informative)
    - Social Proof: 1.0x (confident)
    - Call-to-Action: 1.05x (motivating)

    User can override with custom pitch settings.

    Args:
        section_title: Title of the section
        section_pitches: Dictionary mapping section titles to pitch values (user overrides)
        section_index: Index of the section (for smart defaults)
        total_sections: Total number of sections (for smart defaults)

    Returns:
        float: Speed value for TTS (0.85 to 1.15)
    """
    # Check if user has set a custom pitch for this section (OVERRIDE)
    if section_pitches and section_title in section_pitches:
        pitch = section_pitches.get(section_title, 'normal')

        speed_map = {
            'low': 0.85,
            'normal': 1.0,
            'high': 1.15
        }

        return speed_map.get(pitch, 1.0)

    # Use smart defaults based on section type and position
    smart_config = get_smart_audio_config(section_title, section_index, total_sections)
    return smart_config['speed']


def distribute_media_across_sections(media_files, sections, distribution_mode='auto', section_mapping=None):
    """
    Distribute media (images and videos) across AI summary sections.
    Each asset gets a duration based on the section it belongs to.

    Args:
        media_files: List of media file dicts with 'url', 'type' ('image' or 'video')
        sections: List of AI summary sections with audio_config
        distribution_mode: 'auto' or 'manual'
        section_mapping: Dict mapping section title to list of media objects (for manual mode)
                        Example: {"opening_hook": [{"type": "video", "url": "..."}, ...]}

    Returns:
        Dict with:
        - section_media: Dict mapping section titles to lists of media dicts
        - media_list: List of dicts with 'url', 'duration', 'type' (NO start_time)
        - images_list: List of image URLs in sequence
        - videos_list: List of video URLs in sequence
    """
    if not sections:
        return {
            'section_media': {},
            'media_timings': [],
            'images_list': [],
            'videos_list': []
        }

    section_media = {section['title']: [] for section in sections}

    logger.info(f"🔍 distribute_media_across_sections called:")
    logger.info(f"  - distribution_mode: {distribution_mode}")
    logger.info(f"  - section_mapping: {section_mapping}")
    logger.info(f"  - media_files count: {len(media_files)}")
    logger.info(f"  - sections count: {len(sections)}")

    if distribution_mode == 'manual' and section_mapping:
        # Manual mode: assign media based on section-to-media mapping
        logger.info(f"  ➡️ Using MANUAL mode")

        # Create a mapping from normalized keys to actual section titles
        # section_mapping uses snake_case keys like 'opening_hook'
        # but section titles are like 'Opening Hook'
        def normalize_key(s):
            """Convert 'Opening Hook' to 'opening_hook' for matching"""
            return s.lower().replace(' ', '_').replace('&', 'and').replace('-', '_')

        # Build reverse mapping: normalized_key -> actual_title
        title_mapping = {normalize_key(section['title']): section['title'] for section in sections}

        logger.info(f"  📋 Title mapping: {title_mapping}")
        logger.info(f"  📋 Section mapping keys: {list(section_mapping.keys())}")

        for mapping_key, media_list in section_mapping.items():
            # Normalize the mapping key too (in case it has hyphens like 'call-to-action')
            normalized_mapping_key = normalize_key(mapping_key)

            # Find the actual section title that matches this normalized mapping key
            actual_title = title_mapping.get(normalized_mapping_key)
            if actual_title:
                section_media[actual_title] = media_list
                logger.info(f"  ✅ Mapped '{mapping_key}' (normalized: '{normalized_mapping_key}') -> '{actual_title}' with {len(media_list)} media items")
            else:
                logger.warning(f"  ⚠️ No section found for mapping key: '{mapping_key}' (normalized: '{normalized_mapping_key}')")

        logger.info(f"  📊 Section media counts after manual mapping: {[(k, len(v)) for k, v in section_media.items()]}")
    else:
        # Auto mode: distribute media evenly across sections
        logger.info(f"  ➡️ Using AUTO mode")
        if media_files:
            media_per_section = max(1, len(media_files) // len(sections))
            logger.info(f"  - media_per_section: {media_per_section}")
            media_index = 0

            for section in sections:
                section_title = section['title']
                # Assign media to this section
                for _ in range(media_per_section):
                    if media_index < len(media_files):
                        section_media[section_title].append(media_files[media_index])
                        media_index += 1

            # Distribute remaining media
            section_index = 0
            while media_index < len(media_files):
                section_title = sections[section_index % len(sections)]['title']
                section_media[section_title].append(media_files[media_index])
                media_index += 1
                section_index += 1

            logger.info(f"  - Total media distributed: {media_index}")
            logger.info(f"  - Section media counts: {[(k, len(v)) for k, v in section_media.items()]}")

    # Build media list with durations
    media_list = []
    images_list = []
    videos_list = []

    for section in sections:
        section_title = section['title']
        section_duration = section.get('audio_config', {}).get('duration', 5.0)
        section_media_items = section_media.get(section_title, [])

        if section_media_items:
            # Distribute section duration across media items
            duration_per_item = section_duration / len(section_media_items)

            for media in section_media_items:
                media_dict = {
                    'url': media['url'],
                    'type': media['type'],
                    'duration': duration_per_item
                }
                media_list.append(media_dict)

                if media['type'] == 'image':
                    images_list.append(media['url'])
                elif media['type'] == 'video':
                    videos_list.append(media['url'])

    return {
        'section_media': section_media,
        'media_list': media_list,
        'images_list': images_list,
        'videos_list': videos_list
    }

