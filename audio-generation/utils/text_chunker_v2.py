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

        # Fix acronym pronunciation: "US" (uppercase) = country, "us" (lowercase) = pronoun
        # Replace uppercase "US" with phonetic spelling to ensure correct pronunciation
        text = re.sub(r'\bUS\b', 'U.S.', text)  # US → U.S. (pronounced as "you-ess")

        # XTTS-SPECIFIC IMPROVEMENTS:

        # 1. Expand symbols that cause stuttering/hallucinations
        text = text.replace('%', ' percent')
        text = text.replace('&', ' and')
        text = text.replace('@', ' at')
        text = text.replace('$', ' dollars')
        text = text.replace('€', ' euros')
        text = text.replace('£', ' pounds')
        text = text.replace('#', ' number')
        text = text.replace('+', ' plus')
        text = text.replace('=', ' equals')

        # 2. THE ELLIPSIS TRAP - Critical fix!
        # Ellipsis causes hissing, awkward pauses, or weird trailing sounds
        text = re.sub(r'\.\.\.+', '.', text)  # ... → .
        text = text.replace('…', '.')  # Unicode ellipsis → period

        # 3. Normalize multiple punctuation
        text = re.sub(r'!{2,}', '!', text)  # !! → !
        text = re.sub(r'\?{2,}', '?', text)  # ?? → ?

        # 4. Normalize spacing
        text = re.sub(r'\s+([,.;!?])', r'\1', text)  # Remove space before punctuation
        text = re.sub(r'([,.;!?])([^\s])', r'\1 \2', text)  # Add space after punctuation

        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()

        # CRITICAL FIX: Ensure text ends with punctuation to prevent XTTS-v2 hallucinations
        # XTTS-v2 adds weird sounds ("aah", "yee", breathing) when text doesn't end with punctuation
        # This is a known issue: https://github.com/coqui-ai/TTS/issues/3277
        if text and not text.endswith(('.', '!', '?', '_')):
            text = text + '.'  # Add period if missing

    return text


def chunk_text_v2(text, min_chars=175, max_chars=250, language_code='en', max_iterations=100):
    """
    Split text into chunks using semantic_text_splitter with iterative optimization

    This function tries different capacity parameters to find the best configuration
    where ALL chunks fall within acceptable ranges without any merging logic.

    Strategy:
    1. Try different capacity values (up to 100 iterations for optimal results)
    2. For each iteration, evaluate chunks:
       - Violation: chunk < 150 chars or chunk > max_chars
       - Acceptable: 150 <= chunk < min_chars (below target but OK)
       - Target: min_chars <= chunk <= max_chars (ideal)
    3. If perfect solution found (0 violations), return immediately
    4. Otherwise, return best result (fewest violations) after max_iterations

    Constraints:
    - capacity_min is constrained to [150, 300] range
    - capacity_max is constrained to [150, 300] range
    - These limits ensure optimal TTS quality for XTTS model
    - Chunks >= 150 chars are acceptable (not counted as violations)

    Args:
        text: Text to split
        min_chars: Target minimum characters per chunk (default: 150)
        max_chars: Maximum characters per chunk (default: 240)
        language_code: Language code ('en', 'hi', etc.)
        max_iterations: Maximum optimization iterations (default: 30)

    Returns:
        List of text chunks
    """
    print(f"📝 V2 Chunker: Splitting text for language: {language_code}", file=sys.stderr)
    print(f"   Target range: {min_chars}-{max_chars} chars", file=sys.stderr)
    print(f"   Input text length: {len(text)} chars", file=sys.stderr)
    print(f"   Max optimization iterations: {max_iterations}", file=sys.stderr)

    best_chunks = None
    best_score = float('inf')  # Lower is better (fewer violations)
    best_params = None

    # Try different capacity configurations
    # Strategy: Vary the capacity range to find optimal chunking
    for iteration in range(max_iterations):
        # Generate different capacity values
        # Start with the target range, then adjust
        if iteration == 0:
            # First try: Use exact target range
            capacity_min = min_chars
            capacity_max = max_chars
        else:
            # Subsequent tries: Vary the capacity parameters
            # Adjust min and max slightly to find better boundaries
            offset = (iteration % 10) - 5  # -5 to +4
            capacity_min = min_chars + offset * 5
            capacity_max = max_chars + offset * 5

        # Apply hard constraints
        # capacity_min must be >= 150 (minimum for good TTS quality)
        # capacity_max must be <= 300 (maximum for XTTS model)
        capacity_min = max(150, min(capacity_min, 300))
        capacity_max = max(150, min(capacity_max, 300))

        # Ensure min < max
        if capacity_min >= capacity_max:
            capacity_max = capacity_min + 10

        try:
            # Initialize splitter with current capacity
            splitter = TextSplitter(capacity=(capacity_min, capacity_max), trim=True)

            # Generate chunks
            chunks = [chunk.strip() for chunk in splitter.chunks(text) if chunk.strip()]

            # Evaluate this configuration
            # Only count as violation if chunk is < 150 chars or > max_chars
            # Chunks between 150 and min_chars are acceptable (not violations)
            violations = 0
            too_small = 0  # < 150 chars (actual violation)
            below_target = 0  # 150-175 chars (acceptable but below target)
            too_large = 0  # > max_chars (violation)

            for chunk in chunks:
                chunk_len = len(chunk)
                if chunk_len < 150:
                    violations += 1
                    too_small += 1
                elif chunk_len < min_chars:
                    below_target += 1  # Not a violation, just below target
                elif chunk_len > max_chars:
                    violations += 1
                    too_large += 1

            # Calculate score (lower is better)
            score = violations

            print(f"   Iteration {iteration + 1}/{max_iterations}: capacity=({capacity_min}, {capacity_max}) → {len(chunks)} chunks, {violations} violations (too_small={too_small}, below_target={below_target}, too_large={too_large})", file=sys.stderr)

            # Perfect solution found!
            if violations == 0:
                print(f"✅ Perfect chunking found at iteration {iteration + 1}!", file=sys.stderr)
                print(f"   All {len(chunks)} chunks are within [{min_chars}, {max_chars}] range", file=sys.stderr)
                best_chunks = chunks
                best_params = (capacity_min, capacity_max)
                break

            # Track best result
            if score < best_score:
                best_score = score
                best_chunks = chunks
                best_params = (capacity_min, capacity_max)
                print(f"   ⭐ New best: {violations} violations", file=sys.stderr)

        except Exception as e:
            print(f"   ⚠️  Iteration {iteration + 1} failed: {e}", file=sys.stderr)
            continue

    # Use best result found
    if best_chunks is None:
        # Fallback: Use default parameters with constraints
        print(f"⚠️  No valid chunking found, using fallback", file=sys.stderr)
        fallback_min = max(150, min(min_chars, 300))
        fallback_max = max(150, min(max_chars, 300))
        if fallback_min >= fallback_max:
            fallback_max = fallback_min + 10
        splitter = TextSplitter(capacity=(fallback_min, fallback_max), trim=True)
        best_chunks = [chunk.strip() for chunk in splitter.chunks(text) if chunk.strip()]
        best_params = (fallback_min, fallback_max)

    chunks = best_chunks
    print(f"\n✅ Final result using capacity={best_params}:", file=sys.stderr)
    print(f"   Created {len(chunks)} chunks", file=sys.stderr)

    # Detailed chunk analysis BEFORE cleaning
    in_range = 0  # min_chars to max_chars
    below_target = 0  # 150 to min_chars (acceptable)
    too_small = 0  # < 150 (violation)
    too_large = 0  # > max_chars (violation)

    for i, chunk in enumerate(chunks):
        chunk_len = len(chunk)
        if chunk_len < 150:
            too_small += 1
        elif chunk_len < min_chars:
            below_target += 1
        elif chunk_len > max_chars:
            too_large += 1
        else:
            in_range += 1

    print(f"\n📊 Chunk Statistics (before cleaning):", file=sys.stderr)
    print(f"   ✓ In target range [{min_chars}-{max_chars}]: {in_range}/{len(chunks)} ({in_range*100//len(chunks) if len(chunks) > 0 else 0}%)", file=sys.stderr)
    if below_target > 0:
        print(f"   ℹ️  Below target (150-{min_chars}): {below_target} chunks (acceptable)", file=sys.stderr)
    if too_small > 0:
        print(f"   ⚠️  Too small (< 150): {too_small} chunks (violation)", file=sys.stderr)
    if too_large > 0:
        print(f"   ⚠️  Too large (> {max_chars}): {too_large} chunks (violation)", file=sys.stderr)

    # Clean each chunk for TTS
    print(f"\n🔧 Cleaning chunks for TTS model...", file=sys.stderr)
    print(f"=" * 100, file=sys.stderr)
    cleaned_chunks = []
    for i, chunk in enumerate(chunks):
        cleaned = clean_text_for_tts(chunk, language_code)

        # CRITICAL FIX: Ensure EACH chunk ends with sentence-ending punctuation
        # This prevents XTTS-v2 from adding weird sounds when chunks end mid-sentence
        # Issue: https://github.com/coqui-ai/TTS/issues/3277

        # XTTS-SPECIFIC IMPROVEMENTS:
        # 1. THE "BREATH MARKER" (Space-Period Trick)
        #    Adding a space before the period forces XTTS to finish the word
        #    and trail off naturally into silence (prevents clipping)
        # 2. Strong Stop Signals
        #    Use " ." (space period) for natural breath
        #    Use " _" for hard stop after acronyms

        if cleaned:
            # Remove any trailing whitespace first
            cleaned = cleaned.rstrip()

            # Check if already ends with sentence-ending punctuation
            if cleaned and cleaned[-1] in ('!', '?'):
                # Strong punctuation: Add space before for natural breath
                punc = cleaned[-1]
                cleaned = cleaned[:-1].rstrip() + f" {punc}"

            elif cleaned and cleaned[-1] == '_':
                # Already has underscore stop signal - keep it
                pass

            elif cleaned and cleaned[-1] == '.':
                # Ends with period - check if it's part of an acronym or sentence ending
                tail = cleaned[-10:] if len(cleaned) >= 10 else cleaned

                # Check for acronyms (U.S., U.K., etc.)
                if re.search(r'\b[A-Z]\.$', tail):
                    # Ends with acronym like "U.S." - add hard stop
                    # Use " _" to force XTTS to stop cleanly without adding sounds
                    cleaned = cleaned + " _"
                else:
                    # Regular period: Apply the "Breath Marker" trick
                    # Change "word." to "word ." for natural trailing
                    cleaned = cleaned[:-1].rstrip() + " ."

            else:
                # No punctuation at end - add the "Breath Marker"
                cleaned = cleaned + " ."

        chunk_len = len(cleaned)

        # Status indicator
        if chunk_len < 150:
            status = "⚠️ TOO SMALL"
        elif chunk_len < min_chars:
            status = "ℹ️ BELOW TARGET"
        elif chunk_len > max_chars:
            status = "⚠️ TOO LARGE"
        else:
            status = "✓ IN RANGE"

        # Print full chunk for validation
        print(f"\n📄 Chunk {i+1}/{len(chunks)} | Length: {chunk_len} chars | {status}", file=sys.stderr)
        print(f"─" * 100, file=sys.stderr)
        print(f"{cleaned}", file=sys.stderr)
        print(f"─" * 100, file=sys.stderr)

        cleaned_chunks.append(cleaned)

    print(f"\n" + "=" * 100, file=sys.stderr)
    print(f"✅ Total chunks created: {len(cleaned_chunks)}", file=sys.stderr)

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

    # For XTTS optimal range: 175-250 characters
    # Calculate min_chars to ensure chunks are substantial
    # If max_chars is 250, min_chars will be ~175 (70% of max)
    # If max_chars is 230, min_chars will be ~161 (70% of max)
    min_chars = max(150, int(max_chars * 0.70))

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

