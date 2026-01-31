"""
Speech-to-Text (STT) Handler

This module handles converting student speech to text using:
1. Primary: Web Speech API (browser-based, zero server compute)
2. Fallback: Display message to use supported browser

The handler provides a unified interface for STT.
"""

import logging
from typing import Optional, Dict, Any

from .speech_config import SpeechConfig
from .speech_utils import log_speech_event

logger = logging.getLogger(__name__)


class STTHandler:
    """Handle Speech-to-Text conversion."""
    
    def __init__(self):
        """Initialize STT handler."""
        self.config = SpeechConfig.get_config()['stt']
    
    def generate_browser_stt_html(self, session_key: str = "stt_result") -> str:
        """
        Generate HTML/JavaScript for browser-based STT using Web Speech API.
        
        Args:
            session_key: Session state key to store the transcription result
        
        Returns:
            HTML string with embedded JavaScript for STT
        """
        html = f"""
        <div id="stt-container">
            <div id="stt-status" style="margin-bottom: 10px;">
                <span id="status-text">Ready to record</span>
            </div>
            <div id="stt-controls">
                <button id="start-recording" onclick="startRecording()" 
                        style="padding: 10px 20px; font-size: 16px; cursor: pointer; background-color: #4CAF50; color: white; border: none; border-radius: 4px; margin-right: 10px;">
                    🎤 Start Recording
                </button>
                <button id="stop-recording" onclick="stopRecording()" disabled
                        style="padding: 10px 20px; font-size: 16px; cursor: pointer; background-color: #f44336; color: white; border: none; border-radius: 4px;">
                    ⏹ Stop Recording
                </button>
            </div>
            <div id="stt-transcript" style="margin-top: 15px; padding: 10px; border: 1px solid #ddd; border-radius: 4px; min-height: 50px; background-color: #f9f9f9;">
                <em>Your transcript will appear here...</em>
            </div>
            
            <script>
                let recognition = null;
                let finalTranscript = '';
                let interimTranscript = '';
                
                function initRecognition() {{
                    // Check browser support
                    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                    
                    if (!SpeechRecognition) {{
                        document.getElementById('status-text').innerText = 'Speech recognition not supported';
                        document.getElementById('start-recording').disabled = true;
                        window.parent.postMessage({{
                            type: 'stt_error',
                            error: 'not_supported'
                        }}, '*');
                        return null;
                    }}
                    
                    recognition = new SpeechRecognition();
                    recognition.lang = '{self.config["language"]}';
                    recognition.continuous = {str(self.config["continuous"]).lower()};
                    recognition.interimResults = {str(self.config["interim_results"]).lower()};
                    
                    recognition.onstart = function() {{
                        document.getElementById('status-text').innerText = '🎤 Listening...';
                        document.getElementById('start-recording').disabled = true;
                        document.getElementById('stop-recording').disabled = false;
                        window.parent.postMessage({{
                            type: 'stt_started'
                        }}, '*');
                    }};
                    
                    recognition.onresult = function(event) {{
                        interimTranscript = '';
                        
                        for (let i = event.resultIndex; i < event.results.length; i++) {{
                            const transcript = event.results[i][0].transcript;
                            
                            if (event.results[i].isFinal) {{
                                finalTranscript += transcript + ' ';
                            }} else {{
                                interimTranscript += transcript;
                            }}
                        }}
                        
                        // Display transcript
                        const transcriptDiv = document.getElementById('stt-transcript');
                        transcriptDiv.innerHTML = '<strong>Final:</strong> ' + finalTranscript + 
                                                '<br><em>Interim:</em> ' + interimTranscript;
                        
                        // Send update to parent
                        window.parent.postMessage({{
                            type: 'stt_result',
                            transcript: finalTranscript,
                            interim: interimTranscript,
                            is_final: false
                        }}, '*');
                    }};
                    
                    recognition.onend = function() {{
                        document.getElementById('status-text').innerText = 'Recording stopped';
                        document.getElementById('start-recording').disabled = false;
                        document.getElementById('stop-recording').disabled = true;
                        
                        // Send final result
                        window.parent.postMessage({{
                            type: 'stt_completed',
                            transcript: finalTranscript.trim(),
                            is_final: true
                        }}, '*');
                    }};
                    
                    recognition.onerror = function(event) {{
                        console.error('Speech recognition error:', event.error);
                        document.getElementById('status-text').innerText = 'Error: ' + event.error;
                        document.getElementById('start-recording').disabled = false;
                        document.getElementById('stop-recording').disabled = true;
                        
                        window.parent.postMessage({{
                            type: 'stt_error',
                            error: event.error
                        }}, '*');
                    }};
                    
                    return recognition;
                }}
                
                function startRecording() {{
                    if (!recognition) {{
                        recognition = initRecognition();
                        if (!recognition) {{
                            return;
                        }}
                    }}
                    
                    finalTranscript = '';
                    interimTranscript = '';
                    document.getElementById('stt-transcript').innerHTML = '<em>Listening...</em>';
                    
                    try {{
                        recognition.start();
                    }} catch (e) {{
                        console.error('Error starting recognition:', e);
                        document.getElementById('status-text').innerText = 'Error starting recording';
                    }}
                }}
                
                function stopRecording() {{
                    if (recognition) {{
                        recognition.stop();
                    }}
                }}
                
                // Initialize on load
                window.addEventListener('load', function() {{
                    initRecognition();
                }});
            </script>
        </div>
        """
        
        log_speech_event('stt_html_generated', {'session_key': session_key})
        return html
    
    def get_browser_check_html(self) -> str:
        """
        Generate HTML to check browser support for STT.
        
        Returns:
            HTML string to check browser support
        """
        html = """
        <script>
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            const supported = !!SpeechRecognition;
            
            window.parent.postMessage({
                type: 'stt_support_check',
                supported: supported
            }, '*');
        </script>
        """
        return html
    
    def validate_transcript(self, transcript: str) -> Dict[str, Any]:
        """
        Validate a transcript for quality and completeness.
        
        Args:
            transcript: The transcribed text
        
        Returns:
            Dict with validation results
        """
        result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Check if empty
        if not transcript or not transcript.strip():
            result['valid'] = False
            result['errors'].append('Transcript is empty')
            return result
        
        # Check minimum length
        if len(transcript.strip()) < 3:
            result['warnings'].append('Transcript is very short')
        
        # Check for common recognition errors
        if transcript.strip().lower() in ['um', 'uh', 'er']:
            result['warnings'].append('Transcript contains only filler words')
        
        return result
