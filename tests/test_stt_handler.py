"""
Unit tests for stt_handler.py

Tests Speech-to-Text functionality.
"""

import unittest
from speech_text.stt_handler import STTHandler


class TestSTTHandler(unittest.TestCase):
    """Test cases for STTHandler class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.handler = STTHandler()
    
    def test_initialization(self):
        """Test STTHandler initializes correctly."""
        self.assertIsNotNone(self.handler)
        self.assertIsNotNone(self.handler.config)
        self.assertIn('enabled', self.handler.config)
        self.assertIn('language', self.handler.config)
    
    def test_generate_browser_stt_html(self):
        """Test generation of browser STT HTML."""
        html = self.handler.generate_browser_stt_html()
        
        self.assertIsNotNone(html)
        self.assertIn('SpeechRecognition', html)
        self.assertIn('webkitSpeechRecognition', html)
        self.assertIn('Start Recording', html)
        self.assertIn('Stop Recording', html)
    
    def test_generate_browser_stt_html_with_session_key(self):
        """Test STT HTML generation with custom session key."""
        session_key = "custom_stt_key"
        html = self.handler.generate_browser_stt_html(session_key=session_key)
        
        self.assertIsNotNone(html)
        self.assertIn('SpeechRecognition', html)
    
    def test_stt_html_has_controls(self):
        """Test STT HTML includes control buttons."""
        html = self.handler.generate_browser_stt_html()
        
        self.assertIn('start-recording', html)
        self.assertIn('stop-recording', html)
        self.assertIn('onclick', html)
    
    def test_stt_html_has_transcript_display(self):
        """Test STT HTML includes transcript display area."""
        html = self.handler.generate_browser_stt_html()
        
        self.assertIn('stt-transcript', html)
        self.assertIn('transcript will appear', html.lower())
    
    def test_stt_html_has_event_handlers(self):
        """Test STT HTML includes necessary event handlers."""
        html = self.handler.generate_browser_stt_html()
        
        # Check for key event handlers
        self.assertIn('onstart', html)
        self.assertIn('onresult', html)
        self.assertIn('onend', html)
        self.assertIn('onerror', html)
    
    def test_stt_html_uses_config_language(self):
        """Test STT HTML uses configured language."""
        html = self.handler.generate_browser_stt_html()
        
        # Should include the language setting
        self.assertIn(self.handler.config['language'], html)
    
    def test_get_browser_check_html(self):
        """Test browser support check HTML generation."""
        html = self.handler.get_browser_check_html()
        
        self.assertIsNotNone(html)
        self.assertIn('SpeechRecognition', html)
        self.assertIn('webkitSpeechRecognition', html)
        self.assertIn('stt_support_check', html)
    
    def test_validate_transcript_empty(self):
        """Test validation of empty transcript."""
        result = self.handler.validate_transcript("")
        
        self.assertFalse(result['valid'])
        self.assertGreater(len(result['errors']), 0)
        self.assertIn('empty', result['errors'][0].lower())
    
    def test_validate_transcript_whitespace(self):
        """Test validation of whitespace-only transcript."""
        result = self.handler.validate_transcript("   ")
        
        self.assertFalse(result['valid'])
        self.assertGreater(len(result['errors']), 0)
    
    def test_validate_transcript_too_short(self):
        """Test validation of very short transcript."""
        result = self.handler.validate_transcript("Hi")
        
        # Should be valid but may have warnings
        self.assertTrue(result['valid'])
        # Short text may trigger warnings
        if result['warnings']:
            self.assertIn('short', result['warnings'][0].lower())
    
    def test_validate_transcript_filler_words(self):
        """Test validation of filler word transcripts."""
        result = self.handler.validate_transcript("um")
        
        # Should be valid but with warnings (may be about short length or filler words)
        self.assertTrue(result['valid'])
        # Should have at least some warning
        self.assertGreater(len(result['warnings']), 0)
    
    def test_validate_transcript_valid(self):
        """Test validation of valid transcript."""
        result = self.handler.validate_transcript("This is a valid transcript of speech.")
        
        self.assertTrue(result['valid'])
        self.assertEqual(len(result['errors']), 0)
    
    def test_validate_transcript_returns_dict(self):
        """Test validate_transcript returns proper structure."""
        result = self.handler.validate_transcript("Test")
        
        self.assertIsInstance(result, dict)
        self.assertIn('valid', result)
        self.assertIn('errors', result)
        self.assertIn('warnings', result)
        self.assertIsInstance(result['valid'], bool)
        self.assertIsInstance(result['errors'], list)
        self.assertIsInstance(result['warnings'], list)


if __name__ == '__main__':
    unittest.main()
