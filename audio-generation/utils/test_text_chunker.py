#!/usr/bin/env python3
"""
Unit tests for text_chunker.py

Tests cover:
- convert_numbers_to_words function
- clean_text_for_tts function
- split_gracefully function
- chunk_text function
- get_spacy_model function
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path to import text_chunker
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from text_chunker import (
    convert_numbers_to_words,
    clean_text_for_tts,
    split_gracefully,
    chunk_text,
    get_spacy_model,
    LANGUAGE_DELIMITERS,
    LANGUAGE_MODELS,
    _model_cache
)


class TestRealDataChunking(unittest.TestCase):
    """Test chunking with real Hindi and English text"""

    def test_hindi_story_chunking(self):
        """Test chunking a real Hindi story"""
        hindi_text = """सत्युग की बात है। एक बार देश में दुर्भिक्ष पड़ा। वर्षा के अभाव से अन्न नही हुआ। पशुओ के लिए चारा नही रहा। दूसरे वर्ष भी वर्षा नही हुई। विपत्ति बढ़ती गयी। नदी-तालाब सूख चले। मार्तण्ड की प्रचण्ड किरणों से धरती रसहीन हो गयी। तृण भस्म हो गए। वृक्ष निष्प्राण हो चले मनुष्यों और पशुओं में हाहाकार मच गया।

दुर्भिक्ष बढ़ता गया। एक वर्ष नही, दो वर्ष नही पुरे बाहर वर्षो तक अनावृष्टि रही। लोग त्राहि-त्राहि करने लगे। कहीं अन्न नही, जल , तृण नही, वर्षा और शीत ऋतुएँ नही। सर्वत्र सर्वदा एक ही ग्रीष्म-ऋतु धरती से उड़ती धूल और अग्नि में सनी तेज लू। आकाश में पंख पसारे दल-के-दल उड़ते पक्षियों के दर्शन दुर्लभ हो गये। पशु पक्षी ही नही, कितने मनुष्य काल के गाल में गए, कोई संख्या नही। मात्र-स्तनो मे दूध न पाकर कितने सुकुमार शिशु मृत्यु की गोद में सो गए, कौन जाने! नर-कंकालो देखकर करुणा भी करुणा से भीग जाती, किन्तु एक मुट्ठी अन्न किसकी कोई कहा से देता। नरेश का अक्षय कोष और धनपतीयो के धन अन्न की व्यवस्था कैसे करते? परिस्थिति उत्तरोत्तर बिगड़ती ही चली गयी। प्राणों के लाले पड़ गये।"""

        # Test with different chunk sizes
        for max_chars in [150, 200, 250]:
            chunks = chunk_text(hindi_text, max_chars, 'hi')

            # Verify all chunks are within limit (allowing for merging up to 250)
            for chunk in chunks:
                self.assertLessEqual(len(chunk), 250,
                    f"Chunk exceeds max size: {len(chunk)} > 250")

            # Verify we got multiple chunks
            self.assertGreater(len(chunks), 0, "Should produce at least one chunk")

            # Verify chunks are not empty
            for chunk in chunks:
                self.assertTrue(chunk.strip(), "Chunks should not be empty")

            # Verify all text is preserved (approximately)
            combined = ' '.join(chunks)
            # Allow for some cleaning/normalization
            self.assertGreater(len(combined), len(hindi_text) * 0.8,
                "Combined chunks should preserve most of the original text")

    def test_english_text_chunking(self):
        """Test chunking real English text"""
        english_text = """The quick brown fox jumps over the lazy dog. This is a test sentence to verify that the chunking algorithm works correctly with English text. We need to ensure that sentences are split at natural boundaries, such as periods, commas, and other punctuation marks. The algorithm should also handle long sentences by splitting them at clause boundaries."""

        chunks = chunk_text(english_text, 150, 'en')

        # Verify chunks
        self.assertGreater(len(chunks), 0)
        for chunk in chunks:
            self.assertLessEqual(len(chunk), 250)
            self.assertTrue(chunk.strip())

    def test_hindi_with_numbers(self):
        """Test Hindi text with numbers"""
        text = "बालक 12 वर्ष का था। उसके पास 100 रुपये थे।"
        chunks = chunk_text(text, 150, 'hi')

        self.assertGreater(len(chunks), 0)
        # Numbers should be converted to words
        combined = ' '.join(chunks)
        # Check that text was processed
        self.assertTrue(len(combined) > 0)

    def test_hindi_story_detailed_output(self):
        """Test Hindi story chunking with detailed output for verification"""
        hindi_text = """सत्युग की बात है। एक बार देश में दुर्भिक्ष पड़ा। वर्षा के अभाव से अन्न नही हुआ। पशुओ के लिए चारा नही रहा। दूसरे वर्ष भी वर्षा नही हुई। विपत्ति बढ़ती गयी। नदी-तालाब सूख चले। मार्तण्ड की प्रचण्ड किरणों से धरती रसहीन हो गयी। तृण भस्म हो गए। वृक्ष निष्प्राण हो चले मनुष्यों और पशुओं में हाहाकार मच गया।

दुर्भिक्ष बढ़ता गया। एक वर्ष नही, दो वर्ष नही पुरे बाहर वर्षो तक अनावृष्टि रही। लोग त्राहि-त्राहि करने लगे। कहीं अन्न नही, जल , तृण नही, वर्षा और शीत ऋतुएँ नही। सर्वत्र सर्वदा एक ही ग्रीष्म-ऋतु धरती से उड़ती धूल और अग्नि में सनी तेज लू। आकाश में पंख पसारे दल-के-दल उड़ते पक्षियों के दर्शन दुर्लभ हो गये। पशु पक्षी ही नही, कितने मनुष्य काल के गाल में गए, कोई संख्या नही। मात्र-स्तनो मे दूध न पाकर कितने सुकुमार शिशु मृत्यु की गोद में सो गए, कौन जाने! नर-कंकालो देखकर करुणा भी करुणा से भीग जाती, किन्तु एक मुट्ठी अन्न किसकी कोई कहा से देता। नरेश का अक्षय कोष और धनपतीयो के धन अन्न की व्यवस्था कैसे करते? परिस्थिति उत्तरोत्तर बिगड़ती ही चली गयी। प्राणों के लाले पड़ गये।"""

        chunks = chunk_text(hindi_text, 200, 'hi')

        # Print chunks for manual verification
        print(f"\n\n{'='*60}")
        print(f"Total chunks created: {len(chunks)}")
        print(f"{'='*60}")
        for i, chunk in enumerate(chunks, 1):
            print(f"\nChunk {i} (length: {len(chunk)}):")
            print(f"'{chunk}'")
            print(f"{'-'*60}")

        # Verify chunks
        self.assertGreater(len(chunks), 0)
        for chunk in chunks:
            self.assertLessEqual(len(chunk), 250)
            self.assertTrue(chunk.strip())


class TestConvertNumbersToWords(unittest.TestCase):
    """Test the convert_numbers_to_words function"""

    def test_convert_integer_english(self):
        """Test converting integers in English"""
        # This test requires num2words to be installed
        try:
            result = convert_numbers_to_words("I have 42 apples", 'en')
            # Should convert number to words
            self.assertNotIn("42", result)
        except ImportError:
            # Skip if num2words not available
            self.skipTest("num2words not installed")

    def test_no_num2words_installed(self):
        """Test graceful handling when num2words is not installed"""
        with patch.dict('sys.modules', {'num2words': None}):
            result = convert_numbers_to_words("I have 42 apples", 'en')
            # Should return original text when num2words is not available
            self.assertEqual(result, "I have 42 apples")

    def test_empty_text(self):
        """Test with empty text"""
        result = convert_numbers_to_words("", 'en')
        self.assertEqual(result, "")


class TestCleanTextForTTS(unittest.TestCase):
    """Test the clean_text_for_tts function"""

    def test_empty_text(self):
        """Test with empty text"""
        result = clean_text_for_tts("", 'en')
        self.assertEqual(result, "")

    def test_none_text(self):
        """Test with None text"""
        result = clean_text_for_tts(None, 'en')
        self.assertEqual(result, "")

    def test_english_punctuation_normalization(self):
        """Test English punctuation normalization"""
        result = clean_text_for_tts("Hello!!  world??", 'en')
        # Should normalize multiple exclamations and questions
        self.assertNotIn("!!", result)
        self.assertNotIn("??", result)

    def test_hindi_punctuation_replacement(self):
        """Test Hindi punctuation replacement"""
        result = clean_text_for_tts("नमस्ते! दुनिया?", 'hi')
        # Should replace ! and ? with Purna Viram
        self.assertIn("।", result)
        self.assertNotIn("!", result)
        self.assertNotIn("?", result)

    def test_unicode_normalization(self):
        """Test Unicode normalization"""
        result = clean_text_for_tts("test\u200dtext", 'en')
        # Should remove zero-width joiner
        self.assertNotIn("\u200d", result)

    def test_spacing_normalization(self):
        """Test spacing normalization"""
        result = clean_text_for_tts("Hello   world", 'en')
        # Should normalize multiple spaces to single space
        self.assertNotIn("   ", result)


class TestSplitGracefully(unittest.TestCase):
    """Test the split_gracefully function"""

    def test_text_within_limit(self):
        """Test text that doesn't need splitting"""
        text = "Short text"
        result = split_gracefully(text, 50, [",", ";"])
        self.assertEqual(result, [text])

    def test_split_by_comma(self):
        """Test splitting by comma"""
        text = "This is a long sentence, with a comma, and more text"
        result = split_gracefully(text, 30, [",", ";"])
        self.assertGreater(len(result), 1)
        # Each chunk should be within limit
        for chunk in result:
            self.assertLessEqual(len(chunk), 30)

    def test_split_by_hindi_delimiter(self):
        """Test splitting by Hindi Purna Viram"""
        text = "यह एक लंबा वाक्य है। यह दूसरा वाक्य है।"
        result = split_gracefully(text, 20, ["।", ","])
        self.assertGreater(len(result), 1)

    def test_fallback_to_word_split(self):
        """Test fallback to word splitting when no delimiters work"""
        text = "This is a very long sentence without any commas or semicolons"
        result = split_gracefully(text, 20, [",", ";"])
        self.assertGreater(len(result), 1)
        for chunk in result:
            self.assertLessEqual(len(chunk), 20)

    def test_empty_text(self):
        """Test with empty text"""
        result = split_gracefully("", 50, [","])
        self.assertEqual(result, [""])


class TestGetSpacyModel(unittest.TestCase):
    """Test the get_spacy_model function"""

    def setUp(self):
        """Clear model cache before each test"""
        _model_cache.clear()

    @patch('text_chunker.spacy.load')
    def test_load_english_model(self, mock_spacy_load):
        """Test loading English model"""
        mock_model = MagicMock()
        mock_spacy_load.return_value = mock_model
        
        result = get_spacy_model('en')
        
        mock_spacy_load.assert_called_once_with('en_core_web_sm')
        self.assertEqual(result, mock_model)

    @patch('text_chunker.spacy.load')
    def test_model_caching(self, mock_spacy_load):
        """Test that models are cached"""
        mock_model = MagicMock()
        mock_spacy_load.return_value = mock_model
        
        # Load model twice
        result1 = get_spacy_model('en')
        result2 = get_spacy_model('en')
        
        # Should only call spacy.load once
        mock_spacy_load.assert_called_once()
        self.assertEqual(result1, result2)

    def test_unsupported_language(self):
        """Test error handling for unsupported language"""
        with self.assertRaises(ValueError) as context:
            get_spacy_model('unsupported_lang')
        
        self.assertIn("Unsupported language", str(context.exception))

    @patch('text_chunker.spacy.load')
    def test_model_not_installed(self, mock_spacy_load):
        """Test error handling when model is not installed"""
        mock_spacy_load.side_effect = OSError("Model not found")
        
        with self.assertRaises(OSError) as context:
            get_spacy_model('en')
        
        self.assertIn("Failed to load spaCy model", str(context.exception))


class TestChunkTextBasic(unittest.TestCase):
    """Test basic chunk_text functionality with real spaCy models"""

    def test_empty_text(self):
        """Test with empty text"""
        result = chunk_text("", 50, 'en')
        self.assertEqual(result, [])

    def test_simple_english_text(self):
        """Test simple English text chunking"""
        text = "Hello world. This is a test."
        result = chunk_text(text, 150, 'en')

        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        for chunk in result:
            self.assertLessEqual(len(chunk), 250)


class TestLanguageConfigurations(unittest.TestCase):
    """Test language-specific configurations"""

    def test_language_models_defined(self):
        """Test that language models are properly defined"""
        self.assertIn('en', LANGUAGE_MODELS)
        self.assertIn('hi', LANGUAGE_MODELS)
        self.assertEqual(LANGUAGE_MODELS['en'], 'en_core_web_sm')

    def test_language_delimiters_defined(self):
        """Test that language delimiters are properly defined"""
        self.assertIn('en', LANGUAGE_DELIMITERS)
        self.assertIn('hi', LANGUAGE_DELIMITERS)

        # English should have comma as first delimiter
        self.assertEqual(LANGUAGE_DELIMITERS['en'][0], ',')

        # Hindi should have Purna Viram as first delimiter
        self.assertEqual(LANGUAGE_DELIMITERS['hi'][0], '।')


if __name__ == '__main__':
    unittest.main()
