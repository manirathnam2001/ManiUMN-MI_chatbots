# Mutual-Intent End Condition Implementation Summary

## Overview

This implementation adds a mutual-intent end condition to the MI chatbot system, allowing conversations to end when both the student and bot signal their intent to finish, without requiring turn thresholds or MI rubric coverage.

## Changes Made

### 1. end_control_middleware.py

#### New Pattern Definitions
- **USER_END_INTENT_PATTERNS**: Detects when the student signals they want to end
  - Examples: "bye", "goodbye", "thanks", "done", "finished", "that's all"
- **BOT_END_ACK_PATTERNS**: Detects when the bot provides closing acknowledgment
  - Examples: "goodbye", "you're welcome", "glad I could help", "take care"

#### New Functions
- **detect_user_end_intent(user_message)**: Checks if user message contains end intent
- **detect_bot_end_ack(bot_message)**: Checks if bot message contains closing acknowledgment
- **check_mutual_intent(conversation_context, last_assistant_text, last_user_text)**: 
  - Early-exit check that runs BEFORE other strict checks
  - Returns immediate ending decision when both flags are set
  - Bypasses turn threshold and MI coverage requirements

#### Updated Configuration
- **MIN_TURN_THRESHOLD**: Changed default from '10' to '0'
  - Allows conversations to end without turn minimum when using mutual intent
  - Can still be set via environment variable for strict mode
  - Removed duplicate definition

#### Integration with should_continue_v4
- Added mutual intent check as early exit in should_continue_v4
- Runs immediately after ENDED/PARKED state checks
- If mutual intent detected, conversation ends without further validation
- Otherwise, falls through to existing semantic-based logic

### 2. chat_utils.py

#### Session State Initialization
Added two new flags in `initialize_session_state()`:
- **user_end_intent**: Tracks if student has signaled end intent (default: False)
- **bot_end_ack**: Tracks if bot has provided closing acknowledgment (default: False)

#### Conversation Context Updates
Modified `handle_chat_input()` to:
- Pass mutual intent flags to conversation_context
- Update session state with flag values after decision
- Ensure flags persist across conversation turns

#### Feedback Button Logic
Updated `should_enable_feedback_button()`:
- **Removed**: Turn-based gating (previously required MIN_TURN_THRESHOLD turns)
- **Reduced**: Minimum exchanges from 8 to 4 (minimal sanity check)
- **Added**: Enable button when mutual intent flags are both set
- **Kept**: Enable button when conversation_state=="ended"

#### Flag Reset
Updated `handle_new_conversation_button()`:
- Resets user_end_intent to False
- Resets bot_end_ack to False
- Ensures clean state for new conversations

### 3. Test Updates

#### New Test Files
- **test_mutual_intent.py**: Comprehensive tests for mutual intent logic
  - User end intent detection
  - Bot end acknowledgment detection
  - Mutual intent allowing ending without requirements
  - Partial intent not allowing ending
  - Integration with should_continue_v4
  - MIN_TURN_THRESHOLD default value

- **test_e2e_mutual_intent.py**: End-to-end validation tests
  - Minimal conversation ending with mutual intent
  - Feedback button enablement logic
  - Flag initialization and reset

#### Updated Test Files
- **test_end_control_middleware.py**: 
  - Updated configuration test to accept MIN_TURN_THRESHOLD >= 0
  - Added skip logic for turn threshold test when MIN_TURN_THRESHOLD=0

- **test_end_control_integration.py**:
  - Added skip logic for premature ending test in mutual-intent mode

- **test_end_confirmation_v3.py**:
  - Updated test fixtures to include semantic signals
  - Added doctor closure signals and patient satisfaction
  - Updated turn count to use max(6, MIN_TURN_THRESHOLD + 1) for sufficient conversation

## Behavior Changes

### Before
- Conversations required:
  1. MIN_TURN_THRESHOLD turns (default 10)
  2. MI coverage (open-ended questions, reflection, autonomy, summary)
  3. Doctor closure signals AND patient satisfaction
  4. Explicit confirmation flow
- Feedback button enabled only after meeting turn threshold OR conversation_state=="ended"

### After
- Conversations can end via TWO paths:

  **Path 1: Mutual Intent (NEW - No Requirements)**
  - User says bye/thanks/done → user_end_intent = True
  - Bot says goodbye/you're welcome → bot_end_ack = True
  - Both flags set → conversation ends immediately
  - No turn minimum, no MI coverage required

  **Path 2: Semantic-Based (EXISTING - With Requirements)**
  - MIN_TURN_THRESHOLD met (default 0, configurable)
  - MI coverage complete
  - Doctor closure + patient satisfaction detected
  - Confirmation flow completes
  
- Feedback button enables when:
  1. conversation_state=="ended", OR
  2. Both user_end_intent AND bot_end_ack flags are set

## Configuration

### Environment Variables
- **MI_MIN_TURN_THRESHOLD**: Set to override default (default: 0)
  - `export MI_MIN_TURN_THRESHOLD=10` for strict mode with turn minimum
  - `export MI_MIN_TURN_THRESHOLD=0` for mutual-intent only mode

### Feature Flags (config.json)
- **require_end_confirmation**: Controls confirmation flow (default: true)
  - When true, uses confirmation prompts in semantic-based path
  - Does not affect mutual-intent path (always allows immediate ending)

## Testing

All tests pass successfully:
- ✅ test_mutual_intent.py (6/6 tests)
- ✅ test_semantic_ending.py (6/6 tests)
- ✅ test_end_control_middleware.py (9/9 tests)
- ✅ test_end_control_integration.py (7/7 tests)
- ✅ test_end_confirmation_v3.py (11/11 tests)
- ✅ test_e2e_mutual_intent.py (3/3 tests)

## Migration Guide

### For Existing Deployments
1. No code changes needed in page files (HPV.py, OHI.py, etc.)
2. No database migration required
3. Backward compatible with existing conversations
4. To maintain old behavior:
   ```bash
   export MI_MIN_TURN_THRESHOLD=10
   ```

### For New Deployments
- Default configuration enables mutual-intent mode
- Conversations can end quickly and naturally
- Students can say "thanks, bye" and get immediate feedback

## Example Conversations

### Mutual Intent Path (Quick)
```
Bot: Hello! I'm Alex, nice to meet you.
Student: Hi, thanks for your time. Goodbye!
Bot: You're welcome! Have a great day!
[Conversation ends - both flags set]
```

### Semantic Path (Traditional)
```
Bot: Hello! I'm Alex.
Student: Hi, what brings you here?
Bot: What brings you here today? [open-ended]
Student: I have concerns about vaccines.
Bot: It sounds like you're worried. [reflection]
[... more MI interactions ...]
Student: Any other questions?
Bot: No, that helps. Thank you!
[MI coverage complete + semantic signals detected]
Bot: Before we wrap up, doctor, is there anything more you'd like to discuss?
Student: No, we're done.
[Confirmation received - conversation ends]
```

## Benefits

1. **Flexibility**: Supports both quick and thorough conversations
2. **Natural Endings**: Students can end naturally without artificial constraints
3. **Pedagogically Sound**: Doesn't force minimum turns when student is ready to finish
4. **Backward Compatible**: Existing confirmation flow still works
5. **Configurable**: Can restore strict mode via environment variables
6. **Well-Tested**: Comprehensive test coverage ensures reliability

## Future Enhancements

Potential improvements:
- Add analytics to track mutual-intent vs semantic-based endings
- Customize intent patterns per bot/domain
- Add warning messages if ending too quickly (optional coaching)
- Track average conversation lengths with new system
