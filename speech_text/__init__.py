"""
Speech-to-Text and Text-to-Speech Module

This module provides voice interaction capabilities for the MI Chatbot assessment platform.
It enables dental students to practice Motivational Interviewing skills through natural
voice conversation with patient personas.

Features:
- Text-to-Speech (TTS): Convert bot responses to speech
- Speech-to-Text (STT): Convert student speech to text
- Audio device testing before conversation
- Toggle control for voice mode
- Graceful fallback for unsupported browsers

Module Structure:
- speech_config.py: Configuration and constants
- tts_handler.py: Text-to-Speech logic
- stt_handler.py: Speech-to-Text logic
- audio_test_ui.py: Pre-session audio device testing
- speech_components.py: Streamlit UI components
- speech_utils.py: Utility functions
"""

from .speech_config import SpeechConfig
from .tts_handler import TTSHandler
from .stt_handler import STTHandler
from .speech_utils import (
    check_browser_support,
    handle_audio_permission_error,
    log_speech_event
)
from .speech_components import (
    render_voice_toggle,
    render_tts_playback,
    render_stt_input,
    render_audio_test
)
from .audio_test_ui import run_audio_test

__all__ = [
    'SpeechConfig',
    'TTSHandler',
    'STTHandler',
    'check_browser_support',
    'handle_audio_permission_error',
    'log_speech_event',
    'render_voice_toggle',
    'render_tts_playback',
    'render_stt_input',
    'render_audio_test',
    'run_audio_test',
]

__version__ = '1.0.0'
