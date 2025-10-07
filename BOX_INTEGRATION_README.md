# Box Integration - Quick Start

## Overview

This implementation adds Box cloud storage integration for automated PDF report uploads via email.

## Files Added

1. **`box_config.py`** - Configuration module for Box integration settings
2. **`pdf_utils.py`** - Updated with `upload_pdf_to_box()` function
3. **`box_streamlit_helpers.py`** - Ready-to-use Streamlit UI components
4. **`test_box_integration.py`** - Comprehensive test suite (11 tests)
5. **`test_streamlit_helpers.py`** - Streamlit helper tests (8 tests)
6. **`box_integration_examples.py`** - Usage examples and code snippets
7. **`BOX_INTEGRATION_GUIDE.md`** - Complete documentation

## Quick Setup

### 1. Set Environment Variables

```bash
export SMTP_USERNAME="your-email@example.com"
export SMTP_PASSWORD="your-app-password"
```

For Gmail users:
1. Enable 2-factor authentication
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Use App Password as `SMTP_PASSWORD`

### 2. Add to Your Streamlit App

Add these two lines to HPV.py or OHI.py:

```python
from box_streamlit_helpers import add_box_upload_button

# After generating PDF:
add_box_upload_button(pdf_buffer, filename, student_name, session_type)
```

That's it! The helper handles all UI, error messages, and upload logic.

## Features

✅ **Automated Upload** - Send PDFs to Box via email  
✅ **Retry Logic** - 3 attempts with exponential backoff  
✅ **Error Handling** - Authentication, network, and configuration errors  
✅ **Configurable** - Environment variables or custom config  
✅ **UI Components** - Ready-to-use Streamlit widgets  
✅ **Tested** - 19 tests covering all scenarios  

## Box Upload Email

Default: `App_upl.yqz3brxlhcurhp2l@u.box.com`

## Basic Usage

```python
from pdf_utils import generate_pdf_report, upload_pdf_to_box

# Generate PDF
pdf = generate_pdf_report(student_name, feedback, chat_history, session_type)

# Upload to Box
success, message = upload_pdf_to_box(pdf, "report.pdf")
if success:
    print(f"✓ {message}")
```

## Testing

Run tests to verify everything works:

```bash
# Test Box integration
python test_box_integration.py        # 11/11 tests pass

# Test Streamlit helpers  
python test_streamlit_helpers.py      # 8/8 tests pass

# Verify existing functionality
python test_pdf_scoring_fix.py        # 5/5 tests pass
```

## Configuration Options

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `SMTP_USERNAME` | (required) | Email username |
| `SMTP_PASSWORD` | (required) | Email password |
| `SMTP_HOST` | `smtp.gmail.com` | SMTP server |
| `SMTP_PORT` | `587` | SMTP port |
| `BOX_MAX_RETRY_ATTEMPTS` | `3` | Max retries |
| `BOX_RETRY_DELAY_SECONDS` | `2` | Initial delay |
| `BOX_RETRY_BACKOFF_MULTIPLIER` | `2.0` | Backoff multiplier |

## Error Handling

The integration handles:
- Authentication failures (immediate error)
- Network timeouts (retry with backoff)
- Configuration issues (clear error messages)
- SMTP errors (automatic retry)

## Documentation

- **`BOX_INTEGRATION_GUIDE.md`** - Complete guide with examples
- **`box_integration_examples.py`** - 7 code examples
- Inline documentation in all modules

## Minimal Changes

Implementation follows the "minimal changes" principle:
- New functionality in separate modules
- No changes to existing core functions
- Backward compatible
- Optional feature (doesn't affect existing workflows)

## Security

- Never commit credentials
- Use environment variables
- TLS encryption enabled by default
- App Passwords recommended for Gmail

## Support

Check these in order:
1. Run test suite: `python test_box_integration.py`
2. Review `BOX_INTEGRATION_GUIDE.md`
3. Check environment variables
4. Review error messages (they include helpful tips)

## Summary

✅ Box integration implemented  
✅ All tests passing (19/19)  
✅ Ready to use in HPV.py and OHI.py  
✅ Comprehensive documentation  
✅ Minimal code changes  
