"""
Utility functions for speech features.

This module provides helper functions for browser support checking,
error handling, and logging.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

# Configure module logger
logger = logging.getLogger(__name__)


def check_browser_support() -> Dict[str, bool]:
    """
    Check browser support for Web Speech API features.
    
    Note: This is a Python-side placeholder. Actual detection happens
    in JavaScript via Streamlit components.
    
    Returns:
        Dict with support flags (tts, stt)
    """
    # Browser detection happens on client side in JavaScript
    # This function is a placeholder for server-side reference
    return {
        'tts': True,  # Assume supported unless JS reports otherwise
        'stt': True,  # Assume supported unless JS reports otherwise
        'client_side_check_required': True
    }


def handle_audio_permission_error(error_type: str) -> str:
    """
    Generate appropriate error message for audio permission errors.
    
    Args:
        error_type: Type of error ('denied', 'not_found', 'not_allowed', 'other')
    
    Returns:
        User-friendly error message
    """
    from .speech_config import SpeechConfig
    
    error_messages = {
        'denied': SpeechConfig.MICROPHONE_PERMISSION_DENIED_MSG,
        'not_found': SpeechConfig.NO_AUDIO_DEVICE_MSG,
        'not_allowed': SpeechConfig.MICROPHONE_PERMISSION_DENIED_MSG,
        'not_supported': SpeechConfig.BROWSER_NOT_SUPPORTED_MSG,
        'other': """
        ⚠️ An unexpected error occurred with audio features.
        
        Please try:
        1. Refreshing the page
        2. Checking your audio device connections
        3. Using a different browser (Chrome recommended)
        
        You can continue using text mode without voice features.
        """
    }
    
    return error_messages.get(error_type, error_messages['other'])


def log_speech_event(event_type: str, details: Optional[Dict[str, Any]] = None) -> None:
    """
    Log speech-related events for debugging and monitoring.
    
    Args:
        event_type: Type of event (e.g., 'tts_started', 'stt_completed')
        details: Additional event details
    """
    from .speech_config import SpeechConfig
    
    if not SpeechConfig.LOG_SPEECH_EVENTS:
        return
    
    timestamp = datetime.utcnow().isoformat()
    log_message = f"[Speech Event] {event_type} at {timestamp}"
    
    if details:
        log_message += f" - Details: {details}"
    
    if SpeechConfig.LOG_LEVEL == 'INFO':
        logger.info(log_message)
    elif SpeechConfig.LOG_LEVEL == 'DEBUG':
        logger.debug(log_message)


def sanitize_text_for_speech(text: str) -> str:
    """
    Sanitize text for speech output.
    
    Removes or replaces elements that don't work well with TTS:
    - Markdown formatting
    - Special characters
    - URLs
    
    Args:
        text: Original text
    
    Returns:
        Sanitized text suitable for TTS
    """
    import re
    
    # Remove markdown bold/italic
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    
    # Remove markdown headers
    text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
    
    # Remove URLs but keep the domain name
    text = re.sub(r'https?://([^\s]+)', r'\1', text)
    
    # Remove special tokens/markers
    text = re.sub(r'[END_CONVERSATION]', '', text)
    
    # Clean up extra whitespace
    text = ' '.join(text.split())
    
    return text


def validate_audio_text(text: str) -> bool:
    """
    Validate text before processing for audio.
    
    Args:
        text: Text to validate
    
    Returns:
        True if text is valid for audio processing
    """
    if not text or not text.strip():
        return False
    
    # Check minimum length
    if len(text.strip()) < 2:
        return False
    
    # Check maximum length (very long texts might cause issues)
    if len(text) > 5000:
        logger.warning(f"Text exceeds maximum length for audio: {len(text)} characters")
        return False
    
    return True


def format_speech_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable format.
    
    Args:
        seconds: Duration in seconds
    
    Returns:
        Formatted duration string
    """
    if seconds < 1:
        return f"{int(seconds * 1000)}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    else:
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds:.0f}s"
