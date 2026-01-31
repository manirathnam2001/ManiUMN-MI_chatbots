"""
Unit tests for speech_config.py

Tests configuration validation and settings.
"""

import unittest
from speech_text.speech_config import SpeechConfig


class TestSpeechConfig(unittest.TestCase):
    """Test cases for SpeechConfig class."""
    
    def test_default_tts_config(self):
        """Test default TTS configuration values."""
        self.assertTrue(SpeechConfig.TTS_ENABLED)
        self.assertTrue(SpeechConfig.TTS_FALLBACK_ENABLED)
        self.assertEqual(SpeechConfig.TTS_LANGUAGE, 'en')
        self.assertEqual(SpeechConfig.TTS_VOICE_RATE, 1.0)
        self.assertEqual(SpeechConfig.TTS_VOICE_PITCH, 1.0)
    
    def test_default_stt_config(self):
        """Test default STT configuration values."""
        self.assertTrue(SpeechConfig.STT_ENABLED)
        self.assertEqual(SpeechConfig.STT_LANGUAGE, 'en-US')
        self.assertFalse(SpeechConfig.STT_CONTINUOUS)
        self.assertTrue(SpeechConfig.STT_INTERIM_RESULTS)
    
    def test_audio_test_config(self):
        """Test audio test configuration values."""
        self.assertEqual(SpeechConfig.TEST_AUDIO_DURATION, 3)
        self.assertEqual(SpeechConfig.TEST_PLAYBACK_DELAY, 1)
        self.assertGreater(SpeechConfig.TEST_AUDIO_DURATION, 0)
        self.assertGreater(SpeechConfig.TEST_PLAYBACK_DELAY, 0)
    
    def test_ui_config(self):
        """Test UI configuration values."""
        self.assertEqual(SpeechConfig.REPEAT_BUTTON_TEXT, "🔊 Repeat")
        self.assertEqual(SpeechConfig.CONFIRM_BUTTON_TEXT, "✅ Confirm")
        self.assertEqual(SpeechConfig.RERECORD_BUTTON_TEXT, "🔄 Re-record")
        self.assertEqual(SpeechConfig.HEARD_CLEARLY_TEXT, "Did you hear that clearly?")
    
    def test_logging_config(self):
        """Test logging configuration."""
        self.assertTrue(SpeechConfig.LOG_SPEECH_EVENTS)
        self.assertIn(SpeechConfig.LOG_LEVEL, ['INFO', 'DEBUG', 'WARNING', 'ERROR'])
    
    def test_error_messages(self):
        """Test error messages are defined."""
        self.assertIsNotNone(SpeechConfig.BROWSER_NOT_SUPPORTED_MSG)
        self.assertIsNotNone(SpeechConfig.MICROPHONE_PERMISSION_DENIED_MSG)
        self.assertIsNotNone(SpeechConfig.NO_AUDIO_DEVICE_MSG)
        self.assertGreater(len(SpeechConfig.BROWSER_NOT_SUPPORTED_MSG), 0)
        self.assertGreater(len(SpeechConfig.MICROPHONE_PERMISSION_DENIED_MSG), 0)
        self.assertGreater(len(SpeechConfig.NO_AUDIO_DEVICE_MSG), 0)
    
    def test_get_config(self):
        """Test get_config returns complete configuration dictionary."""
        config = SpeechConfig.get_config()
        
        # Check top-level keys
        self.assertIn('tts', config)
        self.assertIn('stt', config)
        self.assertIn('audio_test', config)
        self.assertIn('ui', config)
        self.assertIn('logging', config)
        
        # Check TTS config
        self.assertIn('enabled', config['tts'])
        self.assertIn('language', config['tts'])
        self.assertIn('rate', config['tts'])
        self.assertIn('pitch', config['tts'])
        
        # Check STT config
        self.assertIn('enabled', config['stt'])
        self.assertIn('language', config['stt'])
        self.assertIn('continuous', config['stt'])
        
        # Check audio test config
        self.assertIn('duration', config['audio_test'])
        self.assertIn('playback_delay', config['audio_test'])
    
    def test_validate_config(self):
        """Test configuration validation."""
        self.assertTrue(SpeechConfig.validate_config())
    
    def test_config_types(self):
        """Test configuration value types."""
        self.assertIsInstance(SpeechConfig.TTS_ENABLED, bool)
        self.assertIsInstance(SpeechConfig.STT_ENABLED, bool)
        self.assertIsInstance(SpeechConfig.TTS_LANGUAGE, str)
        self.assertIsInstance(SpeechConfig.TTS_VOICE_RATE, (int, float))
        self.assertIsInstance(SpeechConfig.TTS_VOICE_PITCH, (int, float))
        self.assertIsInstance(SpeechConfig.TEST_AUDIO_DURATION, (int, float))
    
    def test_valid_language_codes(self):
        """Test language codes are valid."""
        valid_languages = ['en', 'en-US', 'en-GB']
        self.assertIn(SpeechConfig.TTS_LANGUAGE, valid_languages)
        self.assertTrue(SpeechConfig.STT_LANGUAGE.startswith('en'))


if __name__ == '__main__':
    unittest.main()
