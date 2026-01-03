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
    1. Uses language-specific spaCy models for accurate sentence detection
    2. Splits long sentences at natural pauses (commas, Hindi punctuation, etc.)
    3. Groups sentences into chunks without exceeding max_chars
    4. Strips whitespace to prevent empty audio segments

    Args:
        text: Text to split
        max_chars: Maximum characters per chunk (default: 175)
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
        print(f"  Chunk {i+1}: {len(chunk)} chars", file=sys.stderr)

    # Smart merging: Merge chunks < 100 chars with previous chunk if combined size <= 250
    MIN_CHUNK_SIZE = 100
    MAX_COMBINED_SIZE = 250

    if len(final_chunks) > 1:
        print(f"\n🔄 Merging small chunks (< {MIN_CHUNK_SIZE} chars) with previous chunks...", file=sys.stderr)
        merged_chunks = []
        i = 0

        while i < len(final_chunks):
            current_chunk = final_chunks[i]

            # Check if next chunk exists and is too small
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
                else:
                    print(f"  ⚠️  Cannot merge chunk {i+1} ({len(current_chunk)} chars) + chunk {i+2} ({len(next_chunk)} chars) - would exceed {MAX_COMBINED_SIZE} chars", file=sys.stderr)

            # If current chunk itself is too small and there's a previous chunk, try merging backwards
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
        print(f"  {status} Chunk {i+1}: {len(chunk)} chars", file=sys.stderr)

    return final_chunks

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

