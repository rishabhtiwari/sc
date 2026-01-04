#!/usr/bin/env python3
"""
Language-aware text chunker using spaCy for natural sentence boundaries

Supports:
- English: en_core_web_sm model with English-specific clause detection
- Hindi: hi_core_news_sm model with Devanagari punctuation awareness
"""

import sys
import json
import spacy

# ============================================================================
# LANGUAGE-SPECIFIC CONFIGURATIONS
# ============================================================================

# Language code to spaCy model mapping
LANGUAGE_MODELS = {
    'en': 'en_core_web_sm',      # English: Best for English sentence detection
    'hi': 'xx_sent_ud_sm',       # Hindi: Multi-language model with statistical sentence boundary detection
}

# Language-specific delimiters for natural pause detection
# Order matters: Earlier delimiters are tried first
LANGUAGE_DELIMITERS = {
    'hi': [
        "।",        # Purna Viram (primary Hindi sentence boundary)
        "॥",        # Double Purna Viram (verse/section boundary)
        ",",        # Comma (clause separator)
        ";",        # Semicolon
        "—",        # Em dash
        " - ",      # Hyphen with spaces
        " और ",    # "and" in Hindi
        " लेकिन ", # "but" in Hindi
        " परंतु ",  # "but" (formal)
        " तो ",     # "then/so" in Hindi
        " या ",     # "or" in Hindi
    ],
    'en': [
        ",",        # Comma (most common clause separator)
        ";",        # Semicolon
        ":",        # Colon
        "—",        # Em dash
        " - ",      # Hyphen with spaces
        " and ",    # Coordinating conjunction
        " but ",    # Coordinating conjunction
        " or ",     # Coordinating conjunction
        " while ",  # Subordinating conjunction
        " though ", # Subordinating conjunction
    ],
}

# Text preprocessing rules for better TTS quality
# XTTS v2 struggles with certain punctuation, so we normalize them BEFORE chunking
def convert_numbers_to_words(text, language_code='en'):
    """
    Convert numbers to words in the respective language for better TTS pronunciation

    Args:
        text: Input text with numbers
        language_code: Language code ('en', 'hi', 'es', 'fr', 'de', 'it', 'pt', etc.)

    Returns:
        Text with numbers converted to words
    """
    import re

    try:
        from num2words import num2words
    except ImportError:
        print("⚠️ num2words not installed, skipping number conversion", file=sys.stderr)
        return text

    # Map language codes to num2words language codes
    lang_map = {
        'en': 'en',
        'hi': 'hi',  # Hindi
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

    num2words_lang = lang_map.get(language_code, 'en')

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
    Clean problematic punctuation and characters that cause XTTS v2 to generate poor audio

    This is applied AFTER chunking, before sending each chunk to TTS.
    Includes comprehensive Unicode normalization and pronunciation fixes for Hindi.

    Args:
        text: Input text
        language_code: Language code ('en', 'hi', etc.)

    Returns:
        Cleaned text optimized for XTTS v2
    """
    import re
    import unicodedata

    if not text:
        return ""

    # Step 1: Convert numbers to words FIRST (before any other cleaning)
    text = convert_numbers_to_words(text, language_code)

    if language_code == 'hi':
        # 1. Unicode Normalization (Essential for Devanagari)
        # This fixes issues where 'matras' (vowel marks) are separate from their base characters
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
        # Keep only: Devanagari (U+0900-U+097F), spaces, A-Z, a-z, 0-9, and basic punctuation
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

        # Clean up any trailing/leading whitespace
        text = text.strip()

    return text

# Cache loaded models to avoid reloading
_model_cache = {}

# ============================================================================
# MODEL LOADING
# ============================================================================

def get_spacy_model(language_code):
    """
    Load and cache spaCy model for the given language

    Args:
        language_code: Language code (e.g., 'en', 'hi')

    Returns:
        Loaded spaCy model

    Raises:
        OSError: If the required model is not installed
    """
    if language_code not in _model_cache:
        model_name = LANGUAGE_MODELS.get(language_code)

        if not model_name:
            raise ValueError(
                f"Unsupported language: {language_code}. "
                f"Supported languages: {', '.join(LANGUAGE_MODELS.keys())}"
            )

        try:
            print(f"Loading spaCy model: {model_name} for language: {language_code}", file=sys.stderr)
            _model_cache[language_code] = spacy.load(model_name)
            print(f"✓ Model loaded successfully", file=sys.stderr)
        except OSError as e:
            raise OSError(
                f"Failed to load spaCy model '{model_name}' for language '{language_code}'. "
                f"Please install it with: python -m spacy download {model_name}"
            ) from e

    return _model_cache[language_code]

# ============================================================================
# TEXT SPLITTING FUNCTIONS
# ============================================================================

def split_gracefully(text, max_chars, delimiters):
    """
    Split long sentences by natural pauses (clauses) before resorting to word boundaries

    This creates more natural-sounding audio by splitting at commas, semicolons,
    and Hindi punctuation (Purna Viram) rather than arbitrary word boundaries.

    Args:
        text: Text to split
        max_chars: Maximum characters per chunk
        delimiters: List of delimiters to try, in priority order

    Returns:
        List of text parts
    """
    if len(text) <= max_chars:
        return [text]

    # Try splitting by natural pauses first (commas, Hindi punctuation, etc.)
    for delimiter in delimiters:
        if delimiter in text:
            parts = text.split(delimiter)
            chunks = []
            current = ""

            for i, part in enumerate(parts):
                part = part.strip()
                # Re-add delimiter except for last part
                if i < len(parts) - 1:
                    part = part + delimiter

                potential_len = len(current) + len(part) + (1 if current else 0)

                if potential_len <= max_chars:
                    current += (" " if current else "") + part
                else:
                    if current:
                        chunks.append(current.strip())
                    current = part

            if current:
                chunks.append(current.strip())

            # If this delimiter successfully split the text into valid chunks, return it
            if len(chunks) > 1 and all(len(c) <= max_chars for c in chunks):
                return chunks

    # Fallback: Split by words if no natural delimiters work
    words = text.split()
    chunks = []
    current = ""

    for word in words:
        potential_len = len(current) + len(word) + (1 if current else 0)

        if potential_len <= max_chars:
            current += (" " if current else "") + word
        else:
            if current:
                chunks.append(current.strip())
            current = word

    if current:
        chunks.append(current.strip())

    return chunks

def chunk_text(text, max_chars, language_code='en'):
    """
    Split text into chunks at natural sentence boundaries with linguistic awareness

    This function:
    1. Preprocesses text for better TTS quality
    2. Uses language-specific spaCy models for accurate sentence detection
    3. Splits long sentences at natural pauses (commas, Hindi punctuation, etc.)
    4. Groups sentences into chunks without exceeding max_chars
    5. Strips whitespace to prevent empty audio segments

    Args:
        text: Text to split
        max_chars: Maximum characters per chunk (default: 150)
        language_code: Language code ('en' or 'hi')

    Returns:
        List of text chunks, each ≤ max_chars

    Example:
        >>> chunk_text("This is a test. Another sentence.", 20, 'en')
        ['This is a test.', 'Another sentence.']
    """
    print(f"Chunking text for language: {language_code}", file=sys.stderr)
    print(f"Max chars per chunk: {max_chars}", file=sys.stderr)
    print(f"Input text length: {len(text)} chars", file=sys.stderr)

    # Load appropriate spaCy model
    nlp = get_spacy_model(language_code)

    # Get language-specific delimiters
    delimiters = LANGUAGE_DELIMITERS.get(language_code, [",", ";", "—", " - "])
    print(f"Using delimiters: {delimiters[:3]}...", file=sys.stderr)

    # Process text to get sentences
    doc = nlp(text)
    sentences = list(doc.sents)
    print(f"Detected {len(sentences)} sentences", file=sys.stderr)

    # Group sentences into chunks
    final_chunks = []
    buffer = ""

    for i, sent in enumerate(sentences):
        sentence_text = sent.text.strip()

        # Skip empty sentences
        if not sentence_text:
            continue

        print(f"  Sentence {i+1}/{len(sentences)}: {len(sentence_text)} chars", file=sys.stderr)

        # If sentence itself is too long, split it gracefully
        if len(sentence_text) > max_chars:
            print(f"    ⚠️  Sentence exceeds limit, splitting at natural pauses...", file=sys.stderr)

            # Save current buffer first
            if buffer:
                final_chunks.append(buffer.strip())
                print(f"    ✓ Saved buffer chunk: {len(buffer)} chars", file=sys.stderr)
                buffer = ""

            # Split the long sentence at natural pauses
            sentence_parts = split_gracefully(sentence_text, max_chars, delimiters)
            print(f"    ✓ Split into {len(sentence_parts)} parts", file=sys.stderr)

            for j, part in enumerate(sentence_parts):
                part = part.strip()
                if part:  # Only add non-empty parts
                    final_chunks.append(part)
                    print(f"      Part {j+1}: {len(part)} chars", file=sys.stderr)
        else:
            # Check if adding this sentence would exceed limit
            potential_len = len(buffer) + len(sentence_text) + (1 if buffer else 0)

            if potential_len <= max_chars:
                buffer += (" " if buffer else "") + sentence_text
                print(f"    ✓ Added to buffer (now {len(buffer)} chars)", file=sys.stderr)
            else:
                # Save current buffer and start new one
                if buffer:
                    final_chunks.append(buffer.strip())
                    print(f"    ✓ Saved buffer chunk: {len(buffer)} chars", file=sys.stderr)
                buffer = sentence_text
                print(f"    ✓ Started new buffer: {len(buffer)} chars", file=sys.stderr)

    # Add the last buffer
    if buffer:
        final_chunks.append(buffer.strip())
        print(f"  ✓ Saved final buffer: {len(buffer)} chars", file=sys.stderr)

    # Final cleanup: Remove any empty chunks
    final_chunks = [chunk for chunk in final_chunks if chunk.strip()]

    print(f"\n✓ Created {len(final_chunks)} chunks (before merging small chunks)", file=sys.stderr)
    for i, chunk in enumerate(final_chunks):
        print(f"  Chunk {i+1}: {len(chunk)} chars - '{chunk[:50]}...'", file=sys.stderr)

    # Smart merging: Merge chunks < 100 chars with adjacent chunks if combined size <= 250
    MIN_CHUNK_SIZE = 100
    MAX_COMBINED_SIZE = 250

    if len(final_chunks) > 1:
        print(f"\n🔄 Merging small chunks (< {MIN_CHUNK_SIZE} chars) with adjacent chunks...", file=sys.stderr)
        merged_chunks = []
        i = 0

        while i < len(final_chunks):
            current_chunk = final_chunks[i]

            # PRIORITY 1: If current chunk is too small, try merging with next chunk first
            if len(current_chunk) < MIN_CHUNK_SIZE and i + 1 < len(final_chunks):
                next_chunk = final_chunks[i + 1]
                combined_length = len(current_chunk) + len(next_chunk) + 1  # +1 for space

                # Merge forward if combined size doesn't exceed limit
                if combined_length <= MAX_COMBINED_SIZE:
                    merged = current_chunk + " " + next_chunk
                    merged_chunks.append(merged)
                    print(f"  ✓ Merged chunk {i+1} ({len(current_chunk)} chars) + chunk {i+2} ({len(next_chunk)} chars) = {len(merged)} chars", file=sys.stderr)
                    i += 2  # Skip both chunks
                    continue
                else:
                    print(f"  ⚠️  Cannot merge chunk {i+1} ({len(current_chunk)} chars) forward - would exceed {MAX_COMBINED_SIZE} chars", file=sys.stderr)

            # PRIORITY 2: If current chunk is still too small, try merging backwards with previous chunk
            if len(current_chunk) < MIN_CHUNK_SIZE and len(merged_chunks) > 0:
                prev_chunk = merged_chunks[-1]
                combined_length = len(prev_chunk) + len(current_chunk) + 1

                if combined_length <= MAX_COMBINED_SIZE:
                    merged = prev_chunk + " " + current_chunk
                    merged_chunks[-1] = merged
                    print(f"  ✓ Merged chunk {i+1} ({len(current_chunk)} chars) backwards with previous chunk = {len(merged)} chars", file=sys.stderr)
                    i += 1
                    continue
                else:
                    print(f"  ⚠️  Chunk {i+1} is small ({len(current_chunk)} chars) but cannot merge - would exceed limit", file=sys.stderr)

            # PRIORITY 3: Check if next chunk is too small (even if current is OK)
            if i + 1 < len(final_chunks) and len(final_chunks[i + 1]) < MIN_CHUNK_SIZE:
                next_chunk = final_chunks[i + 1]
                combined_length = len(current_chunk) + len(next_chunk) + 1  # +1 for space

                # Merge if combined size doesn't exceed limit
                if combined_length <= MAX_COMBINED_SIZE:
                    merged = current_chunk + " " + next_chunk
                    merged_chunks.append(merged)
                    print(f"  ✓ Merged chunk {i+1} ({len(current_chunk)} chars) + chunk {i+2} ({len(next_chunk)} chars) = {len(merged)} chars", file=sys.stderr)
                    i += 2  # Skip both chunks
                    continue

            # No merging needed or possible
            merged_chunks.append(current_chunk)
            i += 1

        final_chunks = merged_chunks
        print(f"\n✅ Final result: {len(final_chunks)} chunks (after smart merging)", file=sys.stderr)
    else:
        print(f"\n✅ Only 1 chunk, no merging needed", file=sys.stderr)

    # Final report
    for i, chunk in enumerate(final_chunks):
        status = "✓" if len(chunk) >= MIN_CHUNK_SIZE else "⚠️ "
        preview = chunk[:80] + "..." if len(chunk) > 80 else chunk
        print(f"  {status} Chunk {i+1}: {len(chunk)} chars - '{preview}'", file=sys.stderr)

    # Clean each chunk for TTS AFTER chunking is complete
    # This replaces problematic punctuation that XTTS v2 struggles with
    print(f"\n🔧 Cleaning chunks for TTS model...", file=sys.stderr)
    cleaned_chunks = []
    for i, chunk in enumerate(final_chunks):
        cleaned = clean_text_for_tts(chunk, language_code)
        if cleaned != chunk:
            print(f"  ✓ Chunk {i+1}: Cleaned (replaced problematic punctuation)", file=sys.stderr)
        cleaned_chunks.append(cleaned)

    return cleaned_chunks

def main():
    """Main function for CLI usage"""
    if len(sys.argv) < 3:
        print(json.dumps({
            'error': 'Usage: text_chunker.py <max_chars> <language_code> [text from stdin]'
        }))
        sys.exit(1)
    
    max_chars = int(sys.argv[1])
    language_code = sys.argv[2]
    
    # Read text from stdin
    text = sys.stdin.read().strip()
    
    if not text:
        print(json.dumps({'error': 'No text provided'}))
        sys.exit(1)
    
    try:
        chunks = chunk_text(text, max_chars, language_code)
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

