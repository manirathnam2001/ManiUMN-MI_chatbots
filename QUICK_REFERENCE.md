# MI Chatbot - Quick Reference Guide

## Quick Start for Developers

### 1. Using the Logger

```python
from logging_utils import get_logger

# Get logger instance
logger = get_logger()

# Log session events
logger.log_session_start("John Doe", "HPV Vaccine", "Alex")
logger.log_session_end("John Doe", "HPV Vaccine", 15, "feedback_requested")

# Log feedback generation
logger.log_feedback_generated("John Doe", "HPV Vaccine", 22.5, 75.0, "Alex")

# Log PDF operations
logger.log_pdf_generation_attempt("John Doe", "HPV Vaccine", "Alex")
logger.log_pdf_generation_success("John Doe", "HPV Vaccine", "report.pdf", 125000, "Alex")
logger.log_pdf_generation_error("John Doe", "HPV Vaccine", "Invalid data", "validation_error", "Alex")
```

### 2. End-of-Conversation Detection

```python
from conversation_utils import ConversationEndDetector, format_closing_response

# Check for end phrases
is_end, detected_phrase = ConversationEndDetector.detect_end_phrase(user_input)

if is_end:
    # Get closing message
    closing_msg = ConversationEndDetector.get_closing_message(0)
    response = format_closing_response(detected_phrase, closing_msg)
    
    # Mark conversation as ended
    st.session_state.conversation_ended = True
```

### 3. Enhanced PDF Generation

```python
from pdf_utils import generate_pdf_report

# Generate PDF with all features
pdf_buffer = generate_pdf_report(
    student_name="John Doe",
    raw_feedback=feedback_text,
    chat_history=messages,
    session_type="HPV Vaccine",
    persona="Alex"  # Optional but recommended
)

# Use the PDF buffer
st.download_button(
    label="Download PDF",
    data=pdf_buffer.getvalue(),
    file_name="report.pdf",
    mime="application/pdf"
)
```

## Common Patterns

### Session Lifecycle

```python
# Session Start (first user message)
if not st.session_state.get('session_logged', False):
    logger.log_session_start(student_name, session_type, persona)
    st.session_state.session_logged = True

# Session End (feedback or new conversation)
logger.log_session_end(student_name, session_type, message_count, reason)
```

### Error Handling

```python
try:
    pdf_buffer = generate_pdf_report(...)
    logger.log_pdf_generation_success(...)
except ValueError as e:
    logger.log_pdf_generation_error(..., str(e), 'validation_error')
    st.error(f"Error: {e}")
except Exception as e:
    logger.log_pdf_generation_error(..., str(e), 'unexpected_error')
    st.error("An unexpected error occurred")
```

## Configuration

### Python Logging

```python
# Default configuration (recommended)
logger = get_logger()  # Uses ./logs/mi_chatbot.log

# Custom configuration
from logging_utils import MIChatbotLogger
logger = MIChatbotLogger(
    log_dir='/custom/path',
    log_file='custom.log'
)
```

### PHP Logging

```php
// Default configuration
$logger = new Logger($storage, true, true, '/var/log/mi_logs', Logger::INFO);

// Custom configuration
$logger = new Logger(
    $storage,
    $logToDatabase = true,
    $logToFile = true,
    $logDirectory = '/custom/path',
    $minLogLevel = Logger::DEBUG
);
```

## Testing

```bash
# Run all tests
python test_pdf_scoring_fix.py      # PDF scoring tests
python test_logging_conversation.py # Logging and conversation tests
python test_pdf_persona.py          # PDF persona tests

# All tests should pass: 15/15
```

## Log Analysis

```bash
# Count events by type
jq -r '.event_type' logs/mi_chatbot.log | sort | uniq -c

# Get all PDF errors
jq 'select(.event_type=="pdf_generation_error")' logs/mi_chatbot.log

# Average feedback scores
jq -r 'select(.event_type=="feedback_generated") | .data.percentage' logs/mi_chatbot.log | \
  awk '{sum+=$1; n++} END {print sum/n}'

# Sessions per persona
jq -r 'select(.event_type=="session_start") | .data.persona' logs/mi_chatbot.log | \
  sort | uniq -c
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Logs not created | Check `./logs/` directory exists and is writable |
| PDF fails | Check logs for detailed error message |
| End phrases not working | Verify phrase matches patterns (case-insensitive) |
| Import errors | Ensure all new modules are in Python path |

## Best Practices

1. **Always log session lifecycle events** (start, end, feedback)
2. **Use persona parameter** when generating PDFs
3. **Handle errors gracefully** with user-friendly messages
4. **Check logs regularly** for system health and debugging
5. **Test end-phrase detection** with various user inputs

## Quick Tips

- Log files rotate daily (auto-appended with date)
- All timestamps are in UTC
- Logs use JSON format for easy parsing
- End phrases are case-insensitive
- PDFs degrade gracefully on errors

For detailed documentation, see `ENHANCEMENTS.md`.
