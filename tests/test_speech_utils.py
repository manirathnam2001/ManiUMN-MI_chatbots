"""
Unit tests for speech_utils.py

Tests utility functions for speech features.
"""

import unittest
from unittest.mock import patch
from speech_text.speech_utils import (
    check_browser_support,
    handle_audio_permission_error,
    log_speech_event,
    sanitize_text_for_speech,
    validate_audio_text,
    format_speech_duration
)


class TestSpeechUtils(unittest.TestCase):
    """Test cases for speech utility functions."""
    
    def test_check_browser_support(self):
        """Test browser support check function."""
        result = check_browser_support()
        
        self.assertIsInstance(result, dict)
        self.assertIn('tts', result)
        self.assertIn('stt', result)
        self.assertIn('client_side_check_required', result)
    
    def test_handle_audio_permission_error_denied(self):
        """Test error handling for denied permission."""
        msg = handle_audio_permission_error('denied')
        
        self.assertIsNotNone(msg)
        self.assertGreater(len(msg), 0)
        self.assertIn('microphone', msg.lower())
    
    def test_handle_audio_permission_error_not_found(self):
        """Test error handling for device not found."""
        msg = handle_audio_permission_error('not_found')
        
        self.assertIsNotNone(msg)
        self.assertGreater(len(msg), 0)
        self.assertIn('audio', msg.lower())
    
    def test_handle_audio_permission_error_not_supported(self):
        """Test error handling for unsupported browser."""
        msg = handle_audio_permission_error('not_supported')
        
        self.assertIsNotNone(msg)
        self.assertGreater(len(msg), 0)
        self.assertIn('browser', msg.lower())
    
    def test_handle_audio_permission_error_other(self):
        """Test error handling for unknown errors."""
        msg = handle_audio_permission_error('other')
        
        self.assertIsNotNone(msg)
        self.assertGreater(len(msg), 0)
    
    def test_log_speech_event(self):
        """Test speech event logging."""
        # Should not raise any errors
        try:
            log_speech_event('test_event')
            log_speech_event('test_event', {'key': 'value'})
        except Exception as e:
            self.fail(f"log_speech_event raised {e}")
    
    def test_sanitize_text_for_speech_bold(self):
        """Test sanitization removes bold markdown."""
        text = "This is **bold** text"
        result = sanitize_text_for_speech(text)
        
        self.assertNotIn('**', result)
        self.assertIn('bold', result)
    
    def test_sanitize_text_for_speech_italic(self):
        """Test sanitization removes italic markdown."""
        text = "This is *italic* text"
        result = sanitize_text_for_speech(text)
        
        self.assertNotIn('*', result)
        self.assertIn('italic', result)
    
    def test_sanitize_text_for_speech_headers(self):
        """Test sanitization removes markdown headers."""
        text = "## This is a header\nNormal text"
        result = sanitize_text_for_speech(text)
        
        self.assertNotIn('##', result)
        # After sanitization, text should be combined without the header marker
        self.assertIn('This is a header', result)
        self.assertIn('Normal text', result)
    
    def test_sanitize_text_for_speech_urls(self):
        """Test sanitization handles URLs."""
        text = "Visit https://example.com for more"
        result = sanitize_text_for_speech(text)
        
        # Should keep domain but remove protocol
        self.assertNotIn('https://', result)
        self.assertIn('example.com', result)
    
    def test_sanitize_text_for_speech_end_token(self):
        """Test sanitization removes END_CONVERSATION token."""
        text = "Goodbye [END_CONVERSATION]"
        result = sanitize_text_for_speech(text)
        
        self.assertNotIn('[END_CONVERSATION]', result)
        self.assertIn('Goodbye', result)
    
    def test_sanitize_text_for_speech_whitespace(self):
        """Test sanitization cleans up extra whitespace."""
        text = "This   has    extra     spaces"
        result = sanitize_text_for_speech(text)
        
        self.assertNotIn('   ', result)
        self.assertEqual(result.count('  '), 0)
    
    def test_validate_audio_text_empty(self):
        """Test validation rejects empty text."""
        self.assertFalse(validate_audio_text(""))
        self.assertFalse(validate_audio_text("   "))
    
    def test_validate_audio_text_too_short(self):
        """Test validation rejects very short text."""
        self.assertFalse(validate_audio_text("a"))
    
    def test_validate_audio_text_valid(self):
        """Test validation accepts valid text."""
        self.assertTrue(validate_audio_text("Hello, this is valid text."))
    
    def test_validate_audio_text_too_long(self):
        """Test validation rejects very long text."""
        long_text = "a" * 6000
        self.assertFalse(validate_audio_text(long_text))
    
    def test_validate_audio_text_max_length(self):
        """Test validation accepts text at max length."""
        max_text = "a" * 4999
        self.assertTrue(validate_audio_text(max_text))
    
    def test_format_speech_duration_milliseconds(self):
        """Test duration formatting for milliseconds."""
        result = format_speech_duration(0.5)
        
        self.assertIn('ms', result)
    
    def test_format_speech_duration_seconds(self):
        """Test duration formatting for seconds."""
        result = format_speech_duration(5.5)
        
        self.assertIn('s', result)
        self.assertNotIn('m', result)
    
    def test_format_speech_duration_minutes(self):
        """Test duration formatting for minutes."""
        result = format_speech_duration(75)
        
        self.assertIn('m', result)
    
    def test_format_speech_duration_zero(self):
        """Test duration formatting for zero."""
        result = format_speech_duration(0)
        
        self.assertIsNotNone(result)


if __name__ == '__main__':
    unittest.main()
