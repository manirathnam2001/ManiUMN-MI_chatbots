"""
Audio Device Testing UI

This module provides a comprehensive audio test interface that runs
before voice-enabled conversations, similar to Zoom's audio setup.
"""

import streamlit as st
import streamlit.components.v1 as components
from typing import Dict, Any

from .speech_config import SpeechConfig
from .tts_handler import TTSHandler
from .stt_handler import STTHandler
from .speech_utils import log_speech_event


def run_audio_test(key_prefix: str = "pre_session_audio_test") -> Dict[str, Any]:
    """
    Run comprehensive audio device test before starting conversation.
    
    This function creates a full-screen test interface that guides users
    through testing their speakers and microphone.
    
    Args:
        key_prefix: Prefix for session state keys
    
    Returns:
        Dict with test results: {
            'passed': bool,
            'speaker_ok': bool,
            'microphone_ok': bool,
            'ready_to_start': bool
        }
    """
    # Initialize session state for test
    test_state_key = f"{key_prefix}_state"
    if test_state_key not in st.session_state:
        st.session_state[test_state_key] = {
            'step': 'intro',
            'speaker_tested': False,
            'speaker_ok': False,
            'mic_tested': False,
            'mic_ok': False,
            'mic_transcript': '',
            'completed': False
        }
    
    test_state = st.session_state[test_state_key]
    
    # Create test UI
    st.markdown("# 🔊 Audio Setup")
    st.markdown("---")
    
    # Introduction
    if test_state['step'] == 'intro':
        st.markdown("""
        ### Welcome to Voice Mode!
        
        Before we begin, let's test your audio devices to ensure the best experience.
        
        This will take about 1-2 minutes and includes:
        1. **Speaker Test**: Verify you can hear the bot's voice
        2. **Microphone Test**: Verify the bot can hear you
        
        Click **Start Test** when you're ready.
        """)
        
        if st.button("🚀 Start Test", type="primary", key=f"{key_prefix}_start"):
            test_state['step'] = 'speaker_test'
            log_speech_event('audio_test_started')
            st.rerun()
        
        if st.button("⬅️ Skip and Use Text Mode", key=f"{key_prefix}_skip"):
            return {
                'passed': False,
                'speaker_ok': False,
                'microphone_ok': False,
                'ready_to_start': False,
                'skipped': True
            }
    
    # Speaker Test
    elif test_state['step'] == 'speaker_test':
        st.markdown("### 1️⃣ Speaker Test")
        st.markdown("""
        We'll play a test sound. Make sure your volume is turned up.
        """)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if st.button("🔊 Play Test Sound", key=f"{key_prefix}_play_test"):
                tts_handler = TTSHandler()
                test_text = "Hello! This is a test of your speakers. If you can hear this message clearly, your audio output is working properly."
                tts_html = tts_handler.generate_browser_tts_html(test_text, auto_play=True)
                components.html(tts_html, height=0)
                test_state['speaker_tested'] = True
                st.info("🔊 Playing test sound...")
        
        if test_state['speaker_tested']:
            st.markdown("---")
            st.markdown("**Did you hear the test sound clearly?**")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Yes, I heard it", key=f"{key_prefix}_speaker_yes", type="primary"):
                    test_state['speaker_ok'] = True
                    test_state['step'] = 'mic_test'
                    log_speech_event('speaker_test_passed')
                    st.rerun()
            
            with col2:
                if st.button("❌ No, I didn't hear it", key=f"{key_prefix}_speaker_no"):
                    test_state['speaker_ok'] = False
                    test_state['step'] = 'speaker_failed'
                    log_speech_event('speaker_test_failed')
                    st.rerun()
    
    # Speaker Test Failed
    elif test_state['step'] == 'speaker_failed':
        st.error("❌ Speaker Test Failed")
        st.markdown("""
        ### Troubleshooting Steps:
        
        1. **Check Volume**: Make sure your system volume is turned up
        2. **Check Device**: Ensure speakers or headphones are connected
        3. **Check Browser**: Try using Chrome or Edge for best compatibility
        4. **Check Settings**: Verify the correct output device is selected in your system settings
        """)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Try Again", key=f"{key_prefix}_speaker_retry"):
                test_state['step'] = 'speaker_test'
                test_state['speaker_tested'] = False
                st.rerun()
        
        with col2:
            if st.button("⬅️ Use Text Mode Instead", key=f"{key_prefix}_speaker_skip"):
                return {
                    'passed': False,
                    'speaker_ok': False,
                    'microphone_ok': False,
                    'ready_to_start': False,
                    'failed_step': 'speaker'
                }
    
    # Microphone Test
    elif test_state['step'] == 'mic_test':
        st.success("✅ Speaker test passed!")
        st.markdown("### 2️⃣ Microphone Test")
        st.markdown("""
        Now let's test your microphone. Click **Start Recording** and say something like:
        
        > "Hello, this is a microphone test"
        
        Then click **Stop Recording** to finish.
        """)
        
        # STT interface for mic test
        stt_handler = STTHandler()
        stt_html = stt_handler.generate_browser_stt_html(session_key=f"{key_prefix}_mic")
        components.html(stt_html, height=300)
        
        st.markdown("---")
        
        # Manual confirmation
        st.markdown("**Were you able to record and see your speech as text above?**")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Yes, it worked", key=f"{key_prefix}_mic_yes", type="primary"):
                test_state['mic_ok'] = True
                test_state['mic_tested'] = True
                test_state['step'] = 'completed'
                log_speech_event('microphone_test_passed')
                st.rerun()
        
        with col2:
            if st.button("❌ No, it didn't work", key=f"{key_prefix}_mic_no"):
                test_state['mic_ok'] = False
                test_state['mic_tested'] = True
                test_state['step'] = 'mic_failed'
                log_speech_event('microphone_test_failed')
                st.rerun()
    
    # Microphone Test Failed
    elif test_state['step'] == 'mic_failed':
        st.error("❌ Microphone Test Failed")
        st.markdown("""
        ### Troubleshooting Steps:
        
        1. **Grant Permission**: Click the 🔒 icon in your browser's address bar and allow microphone access
        2. **Check Device**: Ensure your microphone is connected and turned on
        3. **Check Browser**: Try using Chrome or Edge for best compatibility
        4. **Check Settings**: Verify the correct input device is selected in your system settings
        """)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Try Again", key=f"{key_prefix}_mic_retry"):
                test_state['step'] = 'mic_test'
                test_state['mic_tested'] = False
                st.rerun()
        
        with col2:
            if st.button("⬅️ Use Text Mode Instead", key=f"{key_prefix}_mic_skip"):
                return {
                    'passed': False,
                    'speaker_ok': test_state['speaker_ok'],
                    'microphone_ok': False,
                    'ready_to_start': False,
                    'failed_step': 'microphone'
                }
    
    # Test Completed
    elif test_state['step'] == 'completed':
        st.success("🎉 All Audio Tests Passed!")
        st.markdown("""
        ### Great! You're all set for voice mode.
        
        ✅ Your speakers are working  
        ✅ Your microphone is working  
        
        You can now start your voice-enabled conversation.
        """)
        
        if st.button("▶️ Start Conversation", type="primary", key=f"{key_prefix}_start_convo"):
            test_state['completed'] = True
            log_speech_event('audio_test_completed')
            return {
                'passed': True,
                'speaker_ok': True,
                'microphone_ok': True,
                'ready_to_start': True
            }
    
    # Return current state
    return {
        'passed': test_state.get('completed', False),
        'speaker_ok': test_state.get('speaker_ok', False),
        'microphone_ok': test_state.get('mic_ok', False),
        'ready_to_start': test_state.get('completed', False)
    }
