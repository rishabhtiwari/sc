#!/usr/bin/env python3
"""
V2: Simplified text chunker using semantic_text_splitter library

This is a cleaner, more reliable alternative to the spaCy-based chunker.
Uses semantic_text_splitter which handles:
- Natural sentence boundaries
- Character-level splitting with capacity ranges
- No word duplication (guaranteed by the library)

Advantages over V1:
- Simpler code (no manual splitting logic)
- Better performance (Rust-based library)
- No duplication issues
- Works well for all languages
"""

import sys
import json
import re
import unicodedata

try:
    from semantic_text_splitter import CharacterTextSplitter
except ImportError:
    print(json.dumps({
        'success': False,
        'error': 'semantic_text_splitter not installed. Install with: pip install semantic-text-splitter'
    }))
    sys.exit(1)


def clean_text_for_tts(text, language_code='en'):
    """
    Clean problematic punctuation and characters for XTTS v2
    
    Args:
        text: Input text
        language_code: Language code ('en', 'hi', etc.)
    
    Returns:
        Cleaned text optimized for XTTS v2
    """
    if not text:
        return ""

    if language_code == 'hi':
        # Unicode Normalization (Essential for Devanagari)
        text = unicodedata.normalize('NFC', text)

        # Remove invisible Unicode characters
        text = text.replace('\u200d', '')  # Zero-width joiner
        text = text.replace('\u200c', '')  # Zero-width non-joiner
        text = text.replace('\u200b', '')  # Zero-width space
        text = text.replace('\ufeff', '')  # Zero-width no-break space (BOM)

        # Punctuation Stabilization - Replace problematic punctuation
        text = text.replace("!!", "।")
        text = text.replace("!", "।")
        text = text.replace("??", "।")
        text = text.replace("?", "।")
        text = re.sub(r'\.{2,}', '।', text)  # Replace .. or ...
        text = text.replace("…", "।")  # Ellipsis

        # Remove quotation marks
        text = text.replace('"', '')
        text = text.replace('"', '')
        text = text.replace('"', '')
        text = text.replace("'", '')
        text = text.replace("'", '')
        text = text.replace("'", '')

        # Normalize dashes
        text = text.replace('—', '-')
        text = text.replace('–', '-')

        # Remove non-Hindi/non-English noise
        text = re.sub(r'[^\u0900-\u097F\sA-Za-z0-9।,.\-]', '', text)

        # Normalize spacing around Hindi punctuation
        text = re.sub(r'\s+([।॥,;])', r'\1', text)
        text = re.sub(r'([।॥,;])([^\s])', r'\1 \2', text)

        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()

    elif language_code == 'en':
        # Unicode normalization
        text = unicodedata.normalize('NFC', text)

        # Remove invisible Unicode characters
        text = text.replace('\u200d', '')
        text = text.replace('\u200c', '')
        text = text.replace('\u200b', '')
        text = text.replace('\ufeff', '')

        # Normalize multiples
        text = re.sub(r'!{2,}', '!', text)
        text = re.sub(r'\?{2,}', '?', text)
        text = re.sub(r'\.{3,}', '.', text)

        # Normalize spacing
        text = re.sub(r'\s+([,.;!?])', r'\1', text)
        text = re.sub(r'([,.;!?])([^\s])', r'\1 \2', text)

        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()

    return text


def chunk_text_v2(text, min_chars=150, max_chars=200, language_code='en'):
    """
    Split text into chunks using semantic_text_splitter
    
    This library uses a Rust-based implementation that:
    - Respects sentence boundaries
    - Ensures chunks are within the specified range
    - Guarantees no word duplication
    - Works efficiently for all languages
    
    Args:
        text: Text to split
        min_chars: Minimum characters per chunk (default: 150)
        max_chars: Maximum characters per chunk (default: 200)
        language_code: Language code ('en', 'hi', etc.)
    
    Returns:
        List of text chunks
    """
    print(f"📝 V2 Chunker: Splitting text for language: {language_code}", file=sys.stderr)
    print(f"   Min chars: {min_chars}, Max chars: {max_chars}", file=sys.stderr)
    print(f"   Input text length: {len(text)} chars", file=sys.stderr)

    # Initialize the splitter with trim_chunks to remove extra whitespace
    splitter = CharacterTextSplitter(trim_chunks=True)

    # Generate chunks with capacity range
    # The library will try to fill up to max_chars while staying above min_chars
    chunks = list(splitter.chunks(text, chunk_capacity=(min_chars, max_chars)))

    print(f"✅ Created {len(chunks)} chunks", file=sys.stderr)

    # Clean each chunk for TTS
    print(f"🔧 Cleaning chunks for TTS model...", file=sys.stderr)
    cleaned_chunks = []
    for i, chunk in enumerate(chunks):
        cleaned = clean_text_for_tts(chunk, language_code)
        chunk_len = len(cleaned)
        print(f"   Chunk {i+1}: {chunk_len} chars - '{cleaned[:60]}...'", file=sys.stderr)
        cleaned_chunks.append(cleaned)

    return cleaned_chunks


def main():
    """Main function for CLI usage"""
    if len(sys.argv) < 3:
        print(json.dumps({
            'error': 'Usage: text_chunker_v2.py <max_chars> <language_code> [text from stdin]'
        }))
        sys.exit(1)
    
    max_chars = int(sys.argv[1])
    language_code = sys.argv[2]
    
    # Calculate min_chars as 75% of max_chars for good quality chunks
    min_chars = int(max_chars * 0.75)
    
    # Read text from stdin
    text = sys.stdin.read().strip()
    
    if not text:
        print(json.dumps({'error': 'No text provided'}))
        sys.exit(1)
    
    try:
        chunks = chunk_text_v2(text, min_chars, max_chars, language_code)
        print(json.dumps({
            'success': True,
            'chunks': chunks,
            'chunk_count': len(chunks)
        }))
    except Exception as e:
        print(json.dumps({
            'success': False,
            'error': str(e)
        }))
        sys.exit(1)


if __name__ == '__main__':
    main()

