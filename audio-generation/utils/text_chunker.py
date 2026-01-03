#!/usr/bin/env python3
"""
Clean text chunker using spaCy for natural sentence boundaries
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

def chunk_text(text, max_chars, language_code='en'):
    """
    Split text into chunks at natural sentence boundaries
    
    Args:
        text: Text to split
        max_chars: Maximum characters per chunk (default: 175)
        language_code: Language code (e.g., 'en', 'hi', 'es')
    
    Returns:
        List of text chunks
    """
    # Load appropriate spaCy model
    nlp = get_spacy_model(language_code)
    
    # Process text to get sentences
    doc = nlp(text)
    
    # Group sentences into chunks
    chunks = []
    temp = ""
    
    for sent in doc.sents:
        sentence_text = sent.text.strip()
        
        # If adding this sentence would exceed limit, save current chunk
        if len(temp) + len(sentence_text) + 1 < max_chars:
            temp += sentence_text + " "
        else:
            if temp:
                chunks.append(temp.strip())
            temp = sentence_text + " "
    
    # Add the last chunk
    if temp:
        chunks.append(temp.strip())
    
    return chunks

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

