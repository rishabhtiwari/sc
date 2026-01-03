#!/usr/bin/env python3
"""
Intelligent text splitter using spaCy for natural sentence boundaries
Supports multiple languages
"""

import sys
import json
import spacy

# Language code to spaCy model mapping
LANGUAGE_MODELS = {
    'en': 'en_core_web_sm',
    'hi': 'xx_sent_ud_sm',  # Multi-lingual model for Hindi
    'es': 'xx_sent_ud_sm',
    'fr': 'xx_sent_ud_sm',
    'de': 'xx_sent_ud_sm',
    'it': 'xx_sent_ud_sm',
    'pt': 'xx_sent_ud_sm',
    'pl': 'xx_sent_ud_sm',
    'tr': 'xx_sent_ud_sm',
    'ru': 'xx_sent_ud_sm',
    'nl': 'xx_sent_ud_sm',
    'cs': 'xx_sent_ud_sm',
    'ar': 'xx_sent_ud_sm',
    'zh-cn': 'xx_sent_ud_sm',
    'ja': 'xx_sent_ud_sm',
    'ko': 'xx_sent_ud_sm',
    'hu': 'xx_sent_ud_sm'
}

# Cache loaded models
_model_cache = {}

def get_spacy_model(language_code):
    """Load and cache spaCy model for the given language"""
    if language_code not in _model_cache:
        model_name = LANGUAGE_MODELS.get(language_code, 'xx_sent_ud_sm')
        try:
            _model_cache[language_code] = spacy.load(model_name)
        except OSError:
            # Fallback to multi-lingual model
            _model_cache[language_code] = spacy.load('xx_sent_ud_sm')
    return _model_cache[language_code]

def split_text_into_chunks(text, max_chars, language_code='en'):
    """
    Split text into chunks at natural sentence boundaries

    Args:
        text: Text to split
        max_chars: Maximum characters per chunk
        language_code: Language code (e.g., 'en', 'hi', 'es')

    Returns:
        List of text chunks
    """
    import sys

    # Load appropriate spaCy model
    model_name = LANGUAGE_MODELS.get(language_code, 'xx_sent_ud_sm')
    print(f"🔧 Loading spaCy model: {model_name} for language: {language_code}", file=sys.stderr)
    nlp = get_spacy_model(language_code)

    # Process text to get sentences
    print(f"📝 Processing text ({len(text)} chars) into sentences...", file=sys.stderr)
    doc = nlp(text)
    sentences = [sent.text.strip() for sent in doc.sents]
    print(f"✂️  Found {len(sentences)} sentences", file=sys.stderr)

    # Group sentences into chunks
    chunks = []
    current_chunk = ''
    chunk_num = 0

    for i, sentence in enumerate(sentences, 1):
        sentence_len = len(sentence)
        potential_len = len(current_chunk) + sentence_len + (1 if current_chunk else 0)

        print(f"   Sentence {i}/{len(sentences)}: {sentence_len} chars", file=sys.stderr)

        # If adding this sentence would exceed limit, save current chunk and start new one
        if current_chunk and potential_len > max_chars:
            chunk_num += 1
            chunks.append(current_chunk.strip())
            print(f"   ✅ Chunk {chunk_num} complete: {len(current_chunk)} chars", file=sys.stderr)
            current_chunk = sentence
        else:
            current_chunk += (' ' if current_chunk else '') + sentence
            print(f"   ➕ Added to current chunk (now {len(current_chunk)} chars)", file=sys.stderr)

    # Add the last chunk
    if current_chunk:
        chunk_num += 1
        chunks.append(current_chunk.strip())
        print(f"   ✅ Chunk {chunk_num} complete: {len(current_chunk)} chars", file=sys.stderr)

    print(f"\n📦 Total chunks created: {len(chunks)}", file=sys.stderr)
    for i, chunk in enumerate(chunks, 1):
        print(f"   Chunk {i}: {len(chunk)} chars", file=sys.stderr)

    return chunks

def main():
    """Main function for CLI usage"""
    if len(sys.argv) < 3:
        print(json.dumps({
            'error': 'Usage: text_splitter.py <max_chars> <language_code> [text from stdin]'
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
        chunks = split_text_into_chunks(text, max_chars, language_code)
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

