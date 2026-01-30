"""
Streamlit UI Components for Speech Features

This module provides reusable Streamlit components for:
- Voice mode toggle
- TTS playback with repeat button
- STT input with confirm/re-record
- Audio device testing
"""

import streamlit as st
import streamlit.components.v1 as components
from typing import Optional, Callable

from .speech_config import SpeechConfig
from .tts_handler import TTSHandler
from .stt_handler import STTHandler
from .speech_utils import log_speech_event, handle_audio_permission_error


def render_voice_toggle(key: str = "voice_mode_enabled") -> bool:
    """
    Render a toggle for enabling/disabling voice mode.
    
    Args:
        key: Session state key for the toggle
    
    Returns:
        True if voice mode is enabled
    """
    # Initialize session state if needed
    if key not in st.session_state:
        st.session_state[key] = False
    
    st.markdown("### 🎙️ Voice Mode")
    st.markdown("""
    Enable voice mode to practice with spoken conversation:
    - **Hear** bot responses spoken aloud
    - **Speak** your responses instead of typing
    """)
    
    voice_enabled = st.toggle(
        "Enable Voice Mode",
        value=st.session_state[key],
        key=f"{key}_toggle",
        help="Turn on to use speech features. Requires microphone and speaker."
    )
    
    # Update session state
    st.session_state[key] = voice_enabled
    
    if voice_enabled:
        st.info("✅ Voice mode enabled! You'll be able to speak and hear during the conversation.")
        log_speech_event('voice_mode_enabled')
    else:
        st.info("ℹ️ Voice mode disabled. You'll use text input/output.")
    
    return voice_enabled


def render_tts_playback(text: str, key: str = "tts_playback") -> None:
    """
    Render TTS playback with repeat button.
    
    Args:
        text: Text to convert to speech
        key: Unique key for this component
    """
    if not text:
        return
    
    tts_handler = TTSHandler()
    
    # Container for TTS controls
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Show the text
        st.markdown(f"**Bot says:** {text}")
    
    with col2:
        # Repeat button
        if st.button(SpeechConfig.REPEAT_BUTTON_TEXT, key=f"{key}_repeat"):
            log_speech_event('tts_repeat_requested', {'key': key})
            # Generate TTS HTML
            tts_html = tts_handler.generate_browser_tts_html(text, auto_play=True)
            components.html(tts_html, height=0)
    
    # Auto-play on first render
    if f"{key}_played" not in st.session_state:
        st.session_state[f"{key}_played"] = True
        tts_html = tts_handler.generate_browser_tts_html(text, auto_play=True)
        components.html(tts_html, height=0)
    
    # Confirmation prompt
    st.caption(SpeechConfig.HEARD_CLEARLY_TEXT)


def render_stt_input(
    key: str = "stt_input",
    on_confirm: Optional[Callable[[str], None]] = None
) -> Optional[str]:
    """
    Render STT input with confirm/re-record buttons.
    
    Args:
        key: Unique key for this component
        on_confirm: Callback function when user confirms transcript
    
    Returns:
        Confirmed transcript or None
    """
    stt_handler = STTHandler()
    
    # Initialize session state
    if f"{key}_transcript" not in st.session_state:
        st.session_state[f"{key}_transcript"] = ""
    if f"{key}_confirmed" not in st.session_state:
        st.session_state[f"{key}_confirmed"] = False
    
    st.markdown("### 🎤 Your Response")
    
    # Render STT interface
    stt_html = stt_handler.generate_browser_stt_html(session_key=key)
    components.html(stt_html, height=250)
    
    # Show transcript if available
    if st.session_state[f"{key}_transcript"]:
        st.markdown("**Your transcript:**")
        st.info(st.session_state[f"{key}_transcript"])
        
        # Confirm and Re-record buttons
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button(SpeechConfig.CONFIRM_BUTTON_TEXT, key=f"{key}_confirm", type="primary"):
                st.session_state[f"{key}_confirmed"] = True
                transcript = st.session_state[f"{key}_transcript"]
                log_speech_event('stt_confirmed', {'transcript_length': len(transcript)})
                
                # Call callback if provided
                if on_confirm:
                    on_confirm(transcript)
                
                # Clear for next input
                st.session_state[f"{key}_transcript"] = ""
                return transcript
        
        with col2:
            if st.button(SpeechConfig.RERECORD_BUTTON_TEXT, key=f"{key}_rerecord"):
                st.session_state[f"{key}_transcript"] = ""
                st.session_state[f"{key}_confirmed"] = False
                log_speech_event('stt_rerecord_requested')
                st.rerun()
    
    return None


def render_audio_test(key: str = "audio_test") -> bool:
    """
    Render audio device test interface.
    
    Args:
        key: Unique key for this component
    
    Returns:
        True if tests passed
    """
    st.markdown("### 🔊 Audio Device Test")
    st.markdown("""
    Before we start, let's make sure your audio devices are working properly.
    This helps ensure a smooth conversation experience.
    """)
    
    # Initialize test state
    if f"{key}_speaker_passed" not in st.session_state:
        st.session_state[f"{key}_speaker_passed"] = False
    if f"{key}_mic_passed" not in st.session_state:
        st.session_state[f"{key}_mic_passed"] = False
    
    # Speaker Test
    st.markdown("#### 1️⃣ Speaker Test")
    st.markdown("Click the button below to hear a test sound.")
    
    if st.button("🔊 Play Test Sound", key=f"{key}_speaker_test"):
        tts_handler = TTSHandler()
        test_text = "Hello! If you can hear this clearly, your speakers are working properly."
        tts_html = tts_handler.generate_browser_tts_html(test_text, auto_play=True)
        components.html(tts_html, height=0)
    
    speaker_result = st.radio(
        "Can you hear the test sound clearly?",
        ["Select an option", "Yes, I can hear it", "No, I cannot hear it"],
        key=f"{key}_speaker_result"
    )
    
    if speaker_result == "Yes, I can hear it":
        st.session_state[f"{key}_speaker_passed"] = True
        st.success("✅ Speaker test passed!")
    elif speaker_result == "No, I cannot hear it":
        st.session_state[f"{key}_speaker_passed"] = False
        st.error("❌ Speaker test failed. Please check your audio output device.")
        st.info("Make sure your volume is turned up and speakers/headphones are connected.")
    
    # Microphone Test (only if speaker test passed)
    if st.session_state[f"{key}_speaker_passed"]:
        st.markdown("#### 2️⃣ Microphone Test")
        st.markdown("Record a short message and play it back to verify your microphone.")
        
        # Simple mic test using STT
        stt_handler = STTHandler()
        stt_html = stt_handler.generate_browser_stt_html(session_key=f"{key}_mic")
        components.html(stt_html, height=250)
        
        mic_result = st.radio(
            "Can you hear yourself in the playback?",
            ["Select an option", "Yes, I can hear myself", "No, I cannot hear myself"],
            key=f"{key}_mic_result"
        )
        
        if mic_result == "Yes, I can hear myself":
            st.session_state[f"{key}_mic_passed"] = True
            st.success("✅ Microphone test passed!")
        elif mic_result == "No, I cannot hear myself":
            st.session_state[f"{key}_mic_passed"] = False
            st.error("❌ Microphone test failed. Please check your audio input device.")
            st.info("Make sure your microphone is connected and permissions are granted.")
    
    # Return overall test result
    tests_passed = (
        st.session_state[f"{key}_speaker_passed"] and
        st.session_state[f"{key}_mic_passed"]
    )
    
    if tests_passed:
        st.success("🎉 All audio tests passed! You're ready to start the conversation.")
        log_speech_event('audio_tests_passed')
    
    return tests_passed


def show_browser_compatibility_warning():
    """Show browser compatibility warning for Web Speech API."""
    st.warning(SpeechConfig.BROWSER_NOT_SUPPORTED_MSG)
    log_speech_event('browser_not_supported')


def show_permission_error(error_type: str):
    """
    Show appropriate error message for permission issues.
    
    Args:
        error_type: Type of permission error
    """
    error_message = handle_audio_permission_error(error_type)
    st.error(error_message)
    log_speech_event('permission_error', {'error_type': error_type})
