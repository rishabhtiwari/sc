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
    from semantic_text_splitter import TextSplitter
except ImportError:
    print(json.dumps({
        'success': False,
        'error': 'semantic_text_splitter not installed. Install with: pip install semantic-text-splitter'
    }))
    sys.exit(1)


def convert_numbers_to_words(text, language_code='en'):
    """
    Convert numbers to words in the respective language for better TTS pronunciation

    Args:
        text: Input text with numbers
        language_code: Language code ('en', 'hi', 'es', 'fr', etc.)

    Returns:
        Text with numbers converted to words
    """
    if not text:
        return ""

    # Try to import required libraries
    num2words_available = False
    indic_num2words_available = False

    try:
        from num2words import num2words
        num2words_available = True
    except ImportError:
        pass

    try:
        from indic_numtowords import num2words as indic_num2words
        indic_num2words_available = True
    except ImportError:
        pass

    # If no libraries available, skip conversion
    if not num2words_available and not indic_num2words_available:
        print("⚠️ num2words and indic-numtowords not installed, skipping number conversion", file=sys.stderr)
        return text

    # Handle Hindi with indic-numtowords
    if language_code == 'hi':
        if not indic_num2words_available:
            print("⚠️ indic-numtowords not installed, skipping Hindi number conversion", file=sys.stderr)
            return text

        def replace_hindi_number(match):
            """Replace a number with its Hindi word representation"""
            number_str = match.group(0)
            try:
                # indic_num2words expects language as 'hi' for Hindi
                # It returns Devanagari text (e.g., "एक सौ तेईस" for 123)
                return indic_num2words(int(number_str), lang='hi')
            except Exception as e:
                print(f"⚠️ Could not convert Hindi number '{number_str}': {e}", file=sys.stderr)
                return number_str

        # Replace standalone numbers (not part of words)
        text = re.sub(r'\b\d+\b', replace_hindi_number, text)
        return text

    # Handle other languages with num2words
    if not num2words_available:
        print(f"⚠️ num2words not installed, skipping number conversion for '{language_code}'", file=sys.stderr)
        return text

    # Map language codes to num2words language codes
    lang_map = {
        'en': 'en',
        'es': 'es',  # Spanish
        'fr': 'fr',  # French
        'de': 'de',  # German
        'it': 'it',  # Italian
        'pt': 'pt',  # Portuguese
        'pl': 'pl',  # Polish
        'tr': 'tr',  # Turkish
        'ru': 'ru',  # Russian
        'nl': 'nl',  # Dutch
        'cs': 'cs',  # Czech
        'ar': 'ar',  # Arabic
        'zh': 'zh',  # Chinese
        'ja': 'ja',  # Japanese
        'ko': 'ko',  # Korean
    }

    num2words_lang = lang_map.get(language_code)

    # Skip number conversion for unsupported languages
    if not num2words_lang:
        print(f"⚠️ Number conversion not supported for language '{language_code}', skipping", file=sys.stderr)
        return text

    def replace_number(match):
        """Replace a number with its word representation"""
        number_str = match.group(0)
        try:
            # Handle integers and decimals
            if '.' in number_str:
                # For decimals, convert integer part and decimal part separately
                parts = number_str.split('.')
                integer_part = num2words(int(parts[0]), lang=num2words_lang)
                decimal_part = ' '.join([num2words(int(d), lang=num2words_lang) for d in parts[1]])
                return f"{integer_part} point {decimal_part}"
            else:
                return num2words(int(number_str), lang=num2words_lang)
        except Exception as e:
            print(f"⚠️ Could not convert number '{number_str}': {e}", file=sys.stderr)
            return number_str

    # Replace standalone numbers (not part of words)
    # Match numbers with optional decimal points
    text = re.sub(r'\b\d+\.?\d*\b', replace_number, text)

    return text


def clean_text_for_tts(text, language_code='en'):
    """
    Clean problematic punctuation and characters for XTTS v2

    This is applied AFTER chunking, before sending each chunk to TTS.
    Includes:
    1. Number to words conversion
    2. Unicode normalization
    3. Punctuation stabilization
    4. Pronunciation fixes (for Hindi)

    Args:
        text: Input text
        language_code: Language code ('en', 'hi', etc.)

    Returns:
        Cleaned text optimized for XTTS v2
    """
    if not text:
        return ""

    # Step 1: Convert numbers to words FIRST (before any other cleaning)
    text = convert_numbers_to_words(text, language_code)

    if language_code == 'hi':
        # 1. Unicode Normalization (Essential for Devanagari)
        # This fixes issues where 'matras' (vowel marks) are separate from base characters
        # NFC = Canonical Decomposition, followed by Canonical Composition
        text = unicodedata.normalize('NFC', text)

        # 2. Remove invisible Unicode characters that break TTS
        text = text.replace('\u200d', '')  # Zero-width joiner
        text = text.replace('\u200c', '')  # Zero-width non-joiner
        text = text.replace('\u200b', '')  # Zero-width space
        text = text.replace('\ufeff', '')  # Zero-width no-break space (BOM)

        # 3. Punctuation Stabilization
        # Replace '!' and '?' which cause 'looping' or 'glitches' in XTTS-v2
        text = text.replace("!!", "।")  # Replace !! first
        text = text.replace("!", "।")   # Then replace single !
        text = text.replace("??", "।")  # Replace ?? first
        text = text.replace("?", "।")   # Then replace single ?

        # Replace ellipsis (causes hallucinations)
        text = re.sub(r'\.{2,}', '।', text)  # Replace .. or ... with Purna Viram
        text = text.replace("…", "।")  # Ellipsis character

        # 4. Generic Conjunct & Pronunciation Fixes
        # Fix common 'half-letter' clusters that models struggle to 'blend'
        pronunciation_map = {
            "त्य": "तय",    # Fixes Satyug (सत्युग → सतयुग), Tyag, etc.
            "श्र": "श‍र",    # Adds a hidden joiner to smooth out 'Shra'
            "ज्ञ": "ग्या",   # Fixes 'Gya' (common mispronunciation of Jna)
            "क्ष": "क‍्षा",  # Fixes 'Ksha' pronunciation
            "द्ध": "दध",    # Fixes 'ddha' clusters
        }

        for pattern, replacement in pronunciation_map.items():
            text = text.replace(pattern, replacement)

        # 5. Remove or normalize quotation marks (can cause issues)
        text = text.replace('"', '')  # Remove double quotes
        text = text.replace('"', '')  # Remove smart quotes
        text = text.replace('"', '')  # Remove smart quotes
        text = text.replace("'", '')  # Remove single quotes
        text = text.replace("'", '')  # Remove smart quotes
        text = text.replace("'", '')  # Remove smart quotes

        # 6. Normalize dashes and hyphens
        text = text.replace('—', '-')  # Em dash to hyphen
        text = text.replace('–', '-')  # En dash to hyphen

        # 7. Remove non-Hindi/non-English noise (Emojis, special symbols)
        # Keep only: Devanagari (U+0900-U+097F), spaces, A-Z, a-z, 0-9, basic punctuation
        text = re.sub(r'[^\u0900-\u097F\sA-Za-z0-9।,.\-]', '', text)

        # 8. Normalize spacing around Hindi punctuation
        text = re.sub(r'\s+([।॥,;])', r'\1', text)  # Remove space before punctuation
        text = re.sub(r'([।॥,;])([^\s])', r'\1 \2', text)  # Add space after punctuation

        # 9. Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)

        # 10. Clean up any trailing/leading whitespace
        text = text.strip()

    elif language_code == 'en':
        # Unicode normalization for English
        text = unicodedata.normalize('NFC', text)

        # Remove invisible Unicode characters
        text = text.replace('\u200d', '')
        text = text.replace('\u200c', '')
        text = text.replace('\u200b', '')
        text = text.replace('\ufeff', '')

        # For English, keep exclamations but normalize multiples
        text = re.sub(r'!{2,}', '!', text)  # !! → !
        text = re.sub(r'\?{2,}', '?', text)  # ?? → ?
        text = re.sub(r'\.{3,}', '.', text)  # ... → .

        # Normalize spacing
        text = re.sub(r'\s+([,.;!?])', r'\1', text)  # Remove space before punctuation
        text = re.sub(r'([,.;!?])([^\s])', r'\1 \2', text)  # Add space after punctuation

        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()

    return text


def chunk_text_v2(text, min_chars=150, max_chars=230, language_code='en'):
    """
    Split text into chunks using semantic_text_splitter

    This library uses a Rust-based implementation that:
    - Respects sentence boundaries
    - Ensures chunks are within the specified range (150-230 chars optimal for XTTS)
    - Guarantees no word duplication
    - Works efficiently for all languages

    Args:
        text: Text to split
        min_chars: Minimum characters per chunk (default: 150)
        max_chars: Maximum characters per chunk (default: 230)
        language_code: Language code ('en', 'hi', etc.)

    Returns:
        List of text chunks
    """
    print(f"📝 V2 Chunker: Splitting text for language: {language_code}", file=sys.stderr)
    print(f"   Min chars: {min_chars}, Max chars: {max_chars}", file=sys.stderr)
    print(f"   Input text length: {len(text)} chars", file=sys.stderr)

    # Initialize the splitter (default uses character count)
    splitter = TextSplitter()

    # Generate chunks with capacity range (150-230 is optimal for XTTS stability)
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

    # For XTTS optimal range: 150-230 characters
    # Calculate min_chars to ensure chunks are substantial
    # If max_chars is 230, min_chars will be ~150 (65% of max)
    # If max_chars is 200, min_chars will be ~130 (65% of max)
    min_chars = max(100, int(max_chars * 0.65))

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

