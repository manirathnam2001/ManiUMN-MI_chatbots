"""
Text-to-Speech (TTS) Handler

This module handles converting bot text responses to speech using:
1. Primary: Web Speech API (browser-based, zero server compute)
2. Fallback: gTTS library (server-side Google TTS)

The handler provides a unified interface for TTS with automatic fallback.
"""

import logging
import base64
from typing import Optional, Tuple
from io import BytesIO

from .speech_config import SpeechConfig
from .speech_utils import sanitize_text_for_speech, validate_audio_text, log_speech_event

logger = logging.getLogger(__name__)


class TTSHandler:
    """Handle Text-to-Speech conversion."""
    
    def __init__(self):
        """Initialize TTS handler."""
        self.config = SpeechConfig.get_config()['tts']
        self.fallback_available = False
        
        # Check if gTTS is available for fallback
        try:
            import gtts
            self.fallback_available = True
            logger.info("gTTS fallback is available")
        except ImportError:
            logger.warning("gTTS not installed - fallback TTS not available")
    
    def generate_browser_tts_html(self, text: str, auto_play: bool = True) -> str:
        """
        Generate HTML/JavaScript for browser-based TTS using Web Speech API.
        
        Args:
            text: Text to convert to speech
            auto_play: Whether to play automatically
        
        Returns:
            HTML string with embedded JavaScript for TTS
        """
        if not validate_audio_text(text):
            logger.warning("Invalid text for TTS")
            return ""
        
        # Sanitize text for speech
        clean_text = sanitize_text_for_speech(text)
        
        # Escape text for JavaScript using JSON encoding for safety
        import json
        # JSON.stringify will properly escape all special characters
        escaped_text = json.dumps(clean_text)[1:-1]  # Remove surrounding quotes added by dumps
        
        auto_play_code = "speakText();" if auto_play else ""
        
        html = f"""
        <div id="tts-container">
            <script>
                function speakText() {{
                    // Check if browser supports Speech Synthesis
                    if (!('speechSynthesis' in window)) {{
                        console.error('Speech Synthesis not supported');
                        window.parent.postMessage({{
                            type: 'tts_error',
                            error: 'not_supported'
                        }}, '*');
                        return;
                    }}
                    
                    // Cancel any ongoing speech
                    window.speechSynthesis.cancel();
                    
                    // Create utterance
                    const utterance = new SpeechSynthesisUtterance("{escaped_text}");
                    utterance.lang = '{self.config["language"]}';
                    utterance.rate = {self.config["rate"]};
                    utterance.pitch = {self.config["pitch"]};
                    
                    // Event handlers
                    utterance.onstart = function() {{
                        console.log('TTS started');
                        window.parent.postMessage({{
                            type: 'tts_started'
                        }}, '*');
                    }};
                    
                    utterance.onend = function() {{
                        console.log('TTS ended');
                        window.parent.postMessage({{
                            type: 'tts_ended'
                        }}, '*');
                    }};
                    
                    utterance.onerror = function(event) {{
                        console.error('TTS error:', event);
                        window.parent.postMessage({{
                            type: 'tts_error',
                            error: event.error
                        }}, '*');
                    }};
                    
                    // Speak
                    window.speechSynthesis.speak(utterance);
                }}
                
                // Auto-play if configured
                {auto_play_code}
            </script>
        </div>
        """
        
        log_speech_event('tts_html_generated', {'text_length': len(clean_text)})
        return html
    
    def generate_fallback_audio(self, text: str) -> Optional[Tuple[bytes, str]]:
        """
        Generate audio using gTTS fallback.
        
        Args:
            text: Text to convert to speech
        
        Returns:
            Tuple of (audio_bytes, mime_type) or None if failed
        """
        if not self.fallback_available:
            logger.error("Fallback TTS not available - gTTS not installed")
            return None
        
        if not validate_audio_text(text):
            logger.warning("Invalid text for TTS")
            return None
        
        try:
            from gtts import gTTS
            
            # Sanitize text for speech
            clean_text = sanitize_text_for_speech(text)
            
            # Generate TTS
            tts = gTTS(text=clean_text, lang=self.config['language'], slow=False)
            
            # Save to BytesIO
            audio_buffer = BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)
            
            audio_bytes = audio_buffer.read()
            
            log_speech_event('tts_fallback_generated', {
                'text_length': len(clean_text),
                'audio_size': len(audio_bytes)
            })
            
            return (audio_bytes, 'audio/mp3')
            
        except Exception as e:
            logger.error(f"Fallback TTS generation failed: {e}")
            return None
    
    def get_audio_data_uri(self, audio_bytes: bytes, mime_type: str) -> str:
        """
        Convert audio bytes to data URI for embedding.
        
        Args:
            audio_bytes: Audio file bytes
            mime_type: MIME type of audio
        
        Returns:
            Data URI string
        """
        base64_audio = base64.b64encode(audio_bytes).decode('utf-8')
        return f"data:{mime_type};base64,{base64_audio}"
    
    def stop_speech(self) -> str:
        """
        Generate JavaScript to stop ongoing speech.
        
        Returns:
            HTML string with JavaScript to stop speech
        """
        html = """
        <script>
            if ('speechSynthesis' in window) {
                window.speechSynthesis.cancel();
            }
        </script>
        """
        return html
