# End-Control Middleware Documentation

## Overview

The end-control middleware hardens conversation ending logic for the OHI/HPV Motivational Interviewing (MI) chatbots to prevent premature session termination. The system ensures conversations only conclude when explicit policy conditions are met, while keeping the existing user experience otherwise unchanged.

## Problem Statement

The OHI/HPV chatbots occasionally "naturally" ended sessions midway before students completed their MI practice. This was caused by:
- Ambiguous phrases like "thanks", "okay" triggering premature endings
- Early model closure before all MI components were demonstrated
- Lack of explicit confirmation from students

## Solution Architecture

### Core Components

1. **end_control_middleware.py** - Main middleware module implementing:
   - `should_continue()` - Guard function that checks all policy conditions
   - MI component detection (open-ended questions, reflections, autonomy, summary)
   - Student confirmation detection
   - End token detection
   - Detailed conversation tracing for diagnostics

2. **Integration with chat_utils.py** - Modified `handle_chat_input()` to:
   - Use end-control middleware to determine conversation state
   - Prevent ambiguous phrases from triggering endings
   - Log all decision points for diagnostics
   - Maintain backward compatibility with legacy ending detection

3. **Updated Personas** - All personas in OHI.py and HPV.py now include:
   - Guidance on when to use the end token `<<END>>`
   - Instructions to only end after all MI components are demonstrated
   - Examples of natural ending messages with the token

## Policy Conditions for Ending

A conversation can ONLY end when ALL of the following conditions are met:

### 1. Minimum Turn Threshold
- Default: 10 student turns (configurable via `MI_MIN_TURN_THRESHOLD` env variable)
- Ensures adequate conversation length for MI practice

### 2. MI Coverage Requirements
All four MI components must be present in assistant messages:
- **Open-ended questions**: "What brings you here?", "How do you feel about..."
- **Reflections**: "It sounds like...", "So you're feeling..."
- **Autonomy support**: "You can decide...", "What would work for you?"
- **Summary**: "To summarize...", "We've discussed..."

### 3. Student Explicit Confirmation
Student must explicitly confirm they want to end:
- Acceptable: "Yes, let's end", "No more questions", "I'm done", "Let's wrap up"
- NOT acceptable: "thanks", "okay", "thank you" (ambiguous)

### 4. End Token Present
The assistant must emit the explicit end token: `<<END>>`
- Token can be configured via `MI_END_TOKEN` env variable
- Default: `<<END>>`

## Configuration

Environment variables:
```bash
MI_MIN_TURN_THRESHOLD=10    # Minimum number of student turns required
MI_END_TOKEN="<<END>>"       # Token that signifies conversation can end
```

## Usage

### For Developers

The middleware is automatically integrated into the conversation flow. No additional code is needed in OHI.py or HPV.py beyond the imports already added.

Example of middleware decision:
```python
from end_control_middleware import should_continue

conversation_state = {
    'chat_history': [...],  # List of messages
    'turn_count': 12        # Number of student turns
}

decision = should_continue(
    conversation_state,
    last_assistant_text="Thank you! <<END>>",
    last_user_text="Yes, let's end the session"
)

if decision['continue']:
    # Continue conversation
    print(f"Reason: {decision['reason']}")
else:
    # Allow ending
    print("All conditions met - conversation can end")
```

### For Students

The system is transparent to students. They will:
1. See informative messages about minimum turn requirements
2. Be able to request feedback after minimum threshold is reached
3. Experience natural conversation flow until all conditions are met

### For AI Personas

Personas should:
1. Continue the conversation naturally for at least 10-15 exchanges
2. Demonstrate all MI components (open-ended Q, reflection, autonomy, summary)
3. Wait for student to express readiness to end
4. Include `<<END>>` token only when ready to conclude

Example final message:
```
"Thank you for taking the time to discuss this with me. I feel much more informed about my options now. <<END>>"
```

## Diagnostic Tracing

The middleware provides detailed logging for debugging:
- Every call to `should_continue()` is logged with timestamp
- MI coverage status is logged for each check
- Student confirmation attempts are logged
- Full decision trace includes all conditions checked

Logs can be found in the application logs with the following format:
```
[2025-10-23T03:53:19] Evaluating should_continue: turn_count=12
[2025-10-23T03:53:19] MI Coverage check: {'open_ended_question': True, 'reflection': True, 'autonomy': True, 'summary': True}
[2025-10-23T03:53:19] Student confirmation detected: 'Yes, let's end the session'
[2025-10-23T03:53:19] End token '<<END>>' detected in assistant message
[2025-10-23T03:53:19] All end conditions met: min turns, MI coverage, student confirmation, end token
```

## Testing

Three comprehensive test suites are provided:

1. **test_end_control_middleware.py** (9 tests)
   - Tests individual middleware components
   - MI component detection
   - Student confirmation detection
   - End token detection
   - Configuration validation

2. **test_end_control_integration.py** (7 tests)
   - Tests full conversation flow integration
   - Complete conversation scenarios
   - Premature ending prevention
   - All policy conditions enforcement

3. **test_conversation_improvements.py** (5 tests)
   - Tests existing conversation improvements
   - Role validation
   - Session state management
   - Persona updates

Run all tests:
```bash
python test_end_control_middleware.py
python test_end_control_integration.py
python test_conversation_improvements.py
```

## Backward Compatibility

The system maintains backward compatibility:
- Legacy `detect_conversation_ending()` is still used as a fallback
- Feedback button is enabled after minimum threshold OR when conversation ends
- Existing conversation logic is preserved
- No breaking changes to user interface

## Benefits

1. **Prevents Premature Endings**: Students complete full MI sessions
2. **Ensures Quality Practice**: All MI components must be demonstrated
3. **Explicit Intent**: Requires clear confirmation, avoiding ambiguous phrases
4. **Diagnostic Visibility**: Detailed tracing for investigating issues
5. **Configurable**: Thresholds and tokens can be adjusted via environment variables
6. **Well-Tested**: 21 automated tests ensure correct behavior

## Future Enhancements

Potential improvements:
- Dashboard showing conversation statistics and ending patterns
- ML-based MI component detection for better accuracy
- Adaptive thresholds based on conversation quality
- Student feedback on conversation ending experience
- Admin interface for viewing conversation traces

## Security Considerations

- No sensitive data is logged (only conversation structure)
- Configuration via environment variables (not hardcoded)
- All inputs are validated before processing
- No SQL injection or XSS vulnerabilities (CodeQL verified)

## Support

For issues or questions:
1. Check the diagnostic logs for decision traces
2. Review test files for usage examples
3. Adjust `MIN_TURN_THRESHOLD` if needed
4. Contact development team for assistance
