# Speech-to-Text and Text-to-Speech Module

## Overview

This module adds voice interaction capabilities to the MI Chatbot assessment platform, enabling dental students to practice Motivational Interviewing (MI) skills through natural voice conversation with patient personas.

## Features

### 🔊 Text-to-Speech (TTS)
- Converts bot responses to natural speech
- Browser-based using Web Speech API (zero server compute)
- Fallback to gTTS for compatibility
- "Repeat" button to replay audio
- Confirmation prompt after each bot response

### 🎤 Speech-to-Text (STT)
- Converts student speech to text
- Real-time transcription display
- Review transcript before submission
- "Confirm" and "Re-record" options
- Handles microphone permissions gracefully

### 🎛️ Voice Mode Toggle
- Simple on/off toggle at conversation start
- Default: OFF (preserves current text-only behavior)
- When enabled: Both TTS and STT activate
- No impact on existing text-mode users

### 🔧 Audio Device Testing
- Pre-session audio test (like Zoom)
- Speaker test with sample audio
- Microphone test with playback
- Clear troubleshooting guidance
- Option to skip and use text mode

## Architecture

### Module Structure

```
speech_text/
├── __init__.py              # Module exports and version
├── speech_config.py         # Configuration and constants
├── tts_handler.py          # Text-to-Speech logic
├── stt_handler.py          # Speech-to-Text logic
├── audio_test_ui.py        # Pre-session audio testing
├── speech_components.py    # Streamlit UI components
├── speech_utils.py         # Utility functions
└── README.md               # This file
```

### Technology Stack

**Primary (Browser-Based):**
- Web Speech API (SpeechSynthesis) for TTS
- Web Speech API (SpeechRecognition) for STT
- JavaScript in Streamlit components
- Zero server compute required

**Fallback (Server-Side):**
- gTTS library for TTS fallback
- Browser compatibility messages for STT

## Usage

### 1. Import the Module

```python
from speech_text import (
    render_voice_toggle,
    run_audio_test,
    render_tts_playback,
    render_stt_input
)
```

### 2. Add Voice Toggle to Your Bot Page

```python
# In your bot page (e.g., HPV.py)
import streamlit as st
from speech_text import render_voice_toggle, run_audio_test

# Render voice mode toggle
voice_enabled = render_voice_toggle(key="voice_mode")

# If voice enabled, run audio test
if voice_enabled:
    test_result = run_audio_test(key_prefix="hpv_audio_test")
    
    if not test_result['ready_to_start']:
        st.stop()  # Wait for test completion
```

### 3. Use TTS for Bot Responses

```python
from speech_text import render_tts_playback

# After generating bot response
if st.session_state.get('voice_mode_enabled', False):
    render_tts_playback(
        text=bot_response,
        key=f"tts_{turn_number}"
    )
```

### 4. Use STT for Student Input

```python
from speech_text import render_stt_input

# In chat input section
if st.session_state.get('voice_mode_enabled', False):
    transcript = render_stt_input(
        key=f"stt_{turn_number}",
        on_confirm=lambda text: handle_user_input(text)
    )
else:
    # Fallback to text input
    user_input = st.chat_input("Your response...")
```

## Configuration

All configuration is in `speech_config.py`:

```python
class SpeechConfig:
    # TTS Configuration
    TTS_ENABLED = True
    TTS_LANGUAGE = 'en'
    TTS_VOICE_RATE = 1.0
    TTS_VOICE_PITCH = 1.0
    
    # STT Configuration
    STT_ENABLED = True
    STT_LANGUAGE = 'en-US'
    STT_CONTINUOUS = False
    STT_INTERIM_RESULTS = True
    
    # Audio Test Configuration
    TEST_AUDIO_DURATION = 3
    TEST_PLAYBACK_DELAY = 1
    
    # UI Text
    REPEAT_BUTTON_TEXT = "🔊 Repeat"
    CONFIRM_BUTTON_TEXT = "✅ Confirm"
    RERECORD_BUTTON_TEXT = "🔄 Re-record"
```

## Browser Compatibility

### Supported Browsers

| Browser | TTS | STT | Notes |
|---------|-----|-----|-------|
| Chrome | ✅ | ✅ | Recommended |
| Edge | ✅ | ✅ | Full support |
| Safari | ✅ | ⚠️ | STT requires iOS 14.5+ / macOS 11+ |
| Firefox | ⚠️ | ❌ | Limited TTS, no STT |

### Fallback Behavior

- **Unsupported TTS**: Falls back to gTTS (server-side)
- **Unsupported STT**: Shows message to use supported browser
- **Permission Denied**: Shows clear instructions to enable
- **No Audio Device**: Shows troubleshooting steps

## Error Handling

The module handles all common error scenarios:

1. **Browser Not Supported**: Clear message with alternatives
2. **Microphone Permission Denied**: Step-by-step fix instructions
3. **No Audio Device Found**: Troubleshooting guidance
4. **Network Issues**: Graceful degradation to text mode
5. **API Errors**: Logged with user-friendly messages

## Testing

Unit tests are in `/tests/` directory:

- `test_speech_config.py`: Configuration validation
- `test_tts_handler.py`: TTS generation tests
- `test_stt_handler.py`: STT processing tests
- `test_speech_utils.py`: Utility function tests

Run tests:
```bash
python -m unittest discover tests/
```

## Performance

- **Browser-based**: Zero server load for speech processing
- **Lightweight**: <10KB of additional code
- **Fast**: No network latency for TTS/STT
- **Scalable**: Compute handled by client browser

## Security

- **No Audio Storage**: Audio never leaves the browser
- **No Transcripts Stored**: Only text is saved (like text mode)
- **Permission-Based**: Requires explicit user permission
- **Privacy-Preserving**: Same privacy level as text input

## Accessibility

- Visual text always visible alongside audio
- Skip option for users who can't use audio
- Clear error messages with alternatives
- Works with screen readers (text fallback)

## Future Enhancements

Potential improvements (out of scope for v1):

- Multi-language support
- Voice emotion detection
- Custom voice selection
- Offline mode with local models
- Real-time feedback on speech clarity

## Troubleshooting

### TTS Not Working

1. Check browser compatibility
2. Ensure volume is up
3. Try different browser (Chrome recommended)
4. Check console for errors

### STT Not Working

1. Grant microphone permission
2. Check microphone is connected
3. Test microphone in system settings
4. Use Chrome or Edge browser

### Audio Test Failing

1. Refresh the page
2. Allow microphone access in browser
3. Check audio devices are connected
4. Try different browser

## Support

For issues or questions:
1. Check browser console for errors
2. Review error messages in UI
3. Check browser compatibility table
4. Enable debug logging in config

## License

Part of the ManiUMN-MI_chatbots project.
