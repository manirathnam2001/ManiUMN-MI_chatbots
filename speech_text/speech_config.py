"""
Configuration and constants for speech module.

This module defines all configuration settings for the speech-to-text and
text-to-speech features.
"""

import os
from typing import Dict, Any


class SpeechConfig:
    """Configuration class for speech features."""
    
    # TTS Configuration
    TTS_ENABLED = True
    TTS_FALLBACK_ENABLED = True
    TTS_LANGUAGE = 'en'
    TTS_VOICE_RATE = 1.0  # Normal speed
    TTS_VOICE_PITCH = 1.0  # Normal pitch
    
    # STT Configuration
    STT_ENABLED = True
    STT_LANGUAGE = 'en-US'
    STT_CONTINUOUS = False
    STT_INTERIM_RESULTS = True
    
    # Audio Test Configuration
    TEST_AUDIO_DURATION = 3  # seconds for microphone test
    TEST_PLAYBACK_DELAY = 1  # seconds delay before playback
    
    # UI Configuration
    REPEAT_BUTTON_TEXT = "🔊 Repeat"
    CONFIRM_BUTTON_TEXT = "✅ Confirm"
    RERECORD_BUTTON_TEXT = "🔄 Re-record"
    HEARD_CLEARLY_TEXT = "Did you hear that clearly?"
    
    # Logging
    LOG_SPEECH_EVENTS = True
    LOG_LEVEL = 'INFO'
    
    # Fallback messages
    BROWSER_NOT_SUPPORTED_MSG = """
    ⚠️ Your browser doesn't support the Web Speech API.
    
    For the best experience, please use:
    - Google Chrome (recommended)
    - Microsoft Edge
    - Safari (on macOS/iOS)
    
    You can continue using text mode without voice features.
    """
    
    MICROPHONE_PERMISSION_DENIED_MSG = """
    🎤 Microphone access was denied.
    
    To use voice mode:
    1. Click the 🔒 icon in your browser's address bar
    2. Allow microphone access for this site
    3. Refresh the page and enable voice mode again
    
    You can continue using text mode without voice features.
    """
    
    NO_AUDIO_DEVICE_MSG = """
    🎧 No audio input device detected.
    
    Please:
    1. Connect a microphone to your device
    2. Ensure it's properly configured in your system settings
    3. Refresh the page and try again
    
    You can continue using text mode without voice features.
    """
    
    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """Get all configuration as a dictionary."""
        return {
            'tts': {
                'enabled': cls.TTS_ENABLED,
                'fallback_enabled': cls.TTS_FALLBACK_ENABLED,
                'language': cls.TTS_LANGUAGE,
                'rate': cls.TTS_VOICE_RATE,
                'pitch': cls.TTS_VOICE_PITCH,
            },
            'stt': {
                'enabled': cls.STT_ENABLED,
                'language': cls.STT_LANGUAGE,
                'continuous': cls.STT_CONTINUOUS,
                'interim_results': cls.STT_INTERIM_RESULTS,
            },
            'audio_test': {
                'duration': cls.TEST_AUDIO_DURATION,
                'playback_delay': cls.TEST_PLAYBACK_DELAY,
            },
            'ui': {
                'repeat_button': cls.REPEAT_BUTTON_TEXT,
                'confirm_button': cls.CONFIRM_BUTTON_TEXT,
                'rerecord_button': cls.RERECORD_BUTTON_TEXT,
                'heard_clearly': cls.HEARD_CLEARLY_TEXT,
            },
            'logging': {
                'enabled': cls.LOG_SPEECH_EVENTS,
                'level': cls.LOG_LEVEL,
            }
        }
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate configuration settings."""
        try:
            assert isinstance(cls.TTS_ENABLED, bool)
            assert isinstance(cls.STT_ENABLED, bool)
            assert cls.TTS_VOICE_RATE > 0
            assert cls.TTS_VOICE_PITCH > 0
            assert cls.TEST_AUDIO_DURATION > 0
            assert cls.TTS_LANGUAGE in ['en', 'en-US', 'en-GB']
            return True
        except AssertionError:
            return False
