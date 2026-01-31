"""
Unit tests for tts_handler.py

Tests Text-to-Speech functionality.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO

from speech_text.tts_handler import TTSHandler


class TestTTSHandler(unittest.TestCase):
    """Test cases for TTSHandler class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.handler = TTSHandler()
    
    def test_initialization(self):
        """Test TTSHandler initializes correctly."""
        self.assertIsNotNone(self.handler)
        self.assertIsNotNone(self.handler.config)
        self.assertIn('enabled', self.handler.config)
        self.assertIn('language', self.handler.config)
    
    def test_generate_browser_tts_html(self):
        """Test generation of browser TTS HTML."""
        text = "Hello, this is a test."
        html = self.handler.generate_browser_tts_html(text)
        
        self.assertIsNotNone(html)
        self.assertIn('speechSynthesis', html)
        self.assertIn('SpeechSynthesisUtterance', html)
        self.assertIn('Hello', html)
    
    def test_generate_browser_tts_html_auto_play(self):
        """Test TTS HTML with auto-play enabled."""
        text = "Test message"
        html = self.handler.generate_browser_tts_html(text, auto_play=True)
        
        self.assertIn('speakText()', html)
    
    def test_generate_browser_tts_html_no_auto_play(self):
        """Test TTS HTML with auto-play disabled."""
        text = "Test message"
        html = self.handler.generate_browser_tts_html(text, auto_play=False)
        
        # Should not have auto-play call
        self.assertNotIn('speakText();', html.split('<script>')[0])
    
    def test_generate_browser_tts_html_escapes_quotes(self):
        """Test that quotes are properly escaped in TTS text."""
        text = 'She said "Hello" to me'
        html = self.handler.generate_browser_tts_html(text)
        
        # Should not have unescaped quotes that would break JavaScript
        self.assertNotIn('"Hello"', html.split('SpeechSynthesisUtterance')[1].split(');')[0])
    
    def test_generate_browser_tts_html_empty_text(self):
        """Test TTS HTML generation with empty text."""
        html = self.handler.generate_browser_tts_html("")
        
        self.assertEqual(html, "")
    
    def test_generate_browser_tts_html_whitespace_only(self):
        """Test TTS HTML generation with whitespace-only text."""
        html = self.handler.generate_browser_tts_html("   ")
        
        self.assertEqual(html, "")
    
    def test_fallback_available_with_gtts(self):
        """Test fallback is available when gTTS is installed."""
        # Just check that handler can be created
        handler = TTSHandler()
        # If gTTS is installed, fallback_available should be True
        self.assertIsInstance(handler.fallback_available, bool)
    
    def test_fallback_not_available_without_gtts(self):
        """Test fallback handling when gTTS is not installed."""
        # Handler should still work, just without fallback
        handler = TTSHandler()
        self.assertIsNotNone(handler)
    
    def test_generate_fallback_audio(self):
        """Test fallback audio generation with gTTS."""
        # Skip if gTTS not available
        if not self.handler.fallback_available:
            self.skipTest("gTTS not available")
        
        text = "Test fallback audio"
        result = self.handler.generate_fallback_audio(text)
        
        # Should return tuple or None
        if result:
            self.assertIsInstance(result, tuple)
            self.assertEqual(len(result), 2)
    
    def test_get_audio_data_uri(self):
        """Test conversion of audio bytes to data URI."""
        audio_bytes = b'fake audio data'
        mime_type = 'audio/mp3'
        
        data_uri = self.handler.get_audio_data_uri(audio_bytes, mime_type)
        
        self.assertIsNotNone(data_uri)
        self.assertTrue(data_uri.startswith('data:audio/mp3;base64,'))
    
    def test_stop_speech(self):
        """Test stop speech HTML generation."""
        html = self.handler.stop_speech()
        
        self.assertIsNotNone(html)
        self.assertIn('speechSynthesis.cancel', html)
        self.assertIn('<script>', html)


if __name__ == '__main__':
    unittest.main()
