# Box Integration for PDF Storage

This document describes the Box integration feature that allows automated upload of MI assessment PDF reports to Box via email.

## Overview

The Box integration enables the MI Chatbots system to automatically upload generated PDF reports to Box cloud storage by sending them as email attachments to a Box upload email address. This provides secure, centralized storage for all assessment reports.

## Features

- **Automated PDF Upload**: Send PDFs directly to Box via email
- **Configurable Settings**: Customize Box email, SMTP settings, and retry behavior
- **Retry Logic**: Automatic retry with exponential backoff for transient failures
- **Error Handling**: Comprehensive error handling for authentication, network, and configuration issues
- **Email Customization**: Customize email subject and body for uploads

## Configuration

### Environment Variables

The Box integration can be configured using environment variables:

```bash
# Required Settings
export SMTP_USERNAME="your-email@example.com"
export SMTP_PASSWORD="your-app-password"
export SENDER_EMAIL="your-email@example.com"  # Optional, defaults to SMTP_USERNAME

# Optional Settings (with defaults)
export SMTP_HOST="smtp.gmail.com"  # Default: smtp.gmail.com
export SMTP_PORT="587"             # Default: 587
export SMTP_USE_TLS="True"         # Default: True
export BOX_MAX_RETRY_ATTEMPTS="3"  # Default: 3
export BOX_RETRY_DELAY_SECONDS="2" # Default: 2
export BOX_RETRY_BACKOFF_MULTIPLIER="2.0"  # Default: 2.0
```

### Box Upload Email

The default Box upload email address is: `App_upl.yqz3brxlhcurhp2l@u.box.com`

This can be customized by passing a different email to the `BoxConfig` class.

### SMTP Configuration

For Gmail users:
1. Enable 2-factor authentication on your Google account
2. Generate an App Password: https://myaccount.google.com/apppasswords
3. Use the App Password as your `SMTP_PASSWORD`

For other email providers, adjust `SMTP_HOST` and `SMTP_PORT` accordingly.

## Usage

### Basic Usage

```python
from pdf_utils import generate_pdf_report, upload_pdf_to_box
from box_config import BoxConfig

# Generate PDF
pdf_buffer = generate_pdf_report(
    student_name="John Doe",
    raw_feedback=feedback_text,
    chat_history=chat_messages,
    session_type="HPV Vaccine"
)

# Upload to Box (uses environment variable configuration)
try:
    success, message = upload_pdf_to_box(
        pdf_buffer,
        filename="HPV_MI_Report_John_Doe.pdf"
    )
    if success:
        print(f"Success: {message}")
    else:
        print(f"Failed: {message}")
except BoxUploadError as e:
    print(f"Upload error: {e}")
```

### Advanced Usage with Custom Configuration

```python
from pdf_utils import upload_pdf_to_box, BoxUploadError
from box_config import BoxConfig

# Create custom configuration
config = BoxConfig(
    box_email="custom_upload@box.com",
    smtp_host="smtp.office365.com",
    smtp_port=587,
    smtp_username="user@company.com",
    smtp_password="secure_password",
    sender_email="reports@company.com",
    max_retry_attempts=5,
    retry_delay=3,
    retry_backoff=1.5
)

# Upload with custom config and email content
try:
    success, message = upload_pdf_to_box(
        pdf_buffer,
        filename="report.pdf",
        config=config,
        subject="MI Assessment Report - Student XYZ",
        body="Attached is the MI assessment report for the HPV session."
    )
except BoxUploadError as e:
    print(f"Upload failed: {e}")
```

### Integration with Streamlit Apps

Add Box upload to your Streamlit app (e.g., HPV.py or OHI.py):

```python
import streamlit as st
from pdf_utils import generate_pdf_report, upload_pdf_to_box, BoxUploadError
from box_config import BoxConfig

# In your PDF download section:
if st.session_state.feedback is not None:
    # Generate PDF
    pdf_buffer = generate_pdf_report(
        student_name=st.session_state.student_name,
        raw_feedback=feedback_text,
        chat_history=st.session_state.messages,
        session_type="HPV Vaccine"
    )
    
    # Offer download button
    st.download_button(
        label="📥 Download PDF Report",
        data=pdf_buffer,
        file_name=f"HPV_Report_{st.session_state.student_name}.pdf",
        mime="application/pdf"
    )
    
    # Add Box upload button
    if st.button("📤 Upload to Box"):
        try:
            # Check if Box is configured
            config = BoxConfig()
            if config.is_configured():
                with st.spinner("Uploading to Box..."):
                    success, message = upload_pdf_to_box(
                        pdf_buffer,
                        f"HPV_Report_{st.session_state.student_name}.pdf"
                    )
                    if success:
                        st.success(message)
                    else:
                        st.error(f"Upload failed: {message}")
            else:
                missing = config.get_missing_settings()
                st.warning(f"Box upload not configured. Missing: {', '.join(missing)}")
                st.info("Please set SMTP_USERNAME and SMTP_PASSWORD environment variables.")
        except BoxUploadError as e:
            st.error(f"Upload error: {e}")
```

## API Reference

### BoxConfig Class

Configuration class for Box integration settings.

```python
BoxConfig(
    box_email: Optional[str] = None,
    smtp_host: Optional[str] = None,
    smtp_port: Optional[int] = None,
    smtp_username: Optional[str] = None,
    smtp_password: Optional[str] = None,
    sender_email: Optional[str] = None,
    max_retry_attempts: Optional[int] = None,
    retry_delay: Optional[int] = None,
    retry_backoff: Optional[float] = None
)
```

**Methods:**

- `is_configured() -> bool`: Check if all required settings are configured
- `get_missing_settings() -> list`: Get list of missing required settings

### upload_pdf_to_box Function

```python
upload_pdf_to_box(
    pdf_buffer: io.BytesIO,
    filename: str,
    config: Optional[BoxConfig] = None,
    subject: Optional[str] = None,
    body: Optional[str] = None
) -> Tuple[bool, str]
```

Upload a PDF to Box by emailing it to the Box upload email address.

**Parameters:**

- `pdf_buffer`: BytesIO buffer containing the PDF data
- `filename`: Name for the PDF file (`.pdf` extension added automatically if missing)
- `config`: BoxConfig instance (if None, uses default configuration)
- `subject`: Email subject (if None, uses default: "MI Assessment PDF Report")
- `body`: Email body text (if None, uses default template)

**Returns:**

- `Tuple[bool, str]`: (success, message) where success is True if upload succeeded

**Raises:**

- `BoxUploadError`: If configuration is invalid or max retries exceeded

## Error Handling

The Box integration includes comprehensive error handling:

### Configuration Errors

```python
try:
    upload_pdf_to_box(pdf_buffer, "report.pdf")
except BoxUploadError as e:
    if "not properly configured" in str(e):
        print("Please configure SMTP settings")
```

### Authentication Errors

```python
try:
    upload_pdf_to_box(pdf_buffer, "report.pdf")
except BoxUploadError as e:
    if "authentication" in str(e).lower():
        print("Check your SMTP username and password")
```

### Network Errors with Retry

The system automatically retries on transient network failures:

- Default: 3 retry attempts
- Exponential backoff (default: 2x multiplier)
- Configurable retry delay (default: 2 seconds)

```python
# Configure retry behavior
config = BoxConfig(
    max_retry_attempts=5,    # Try up to 5 times
    retry_delay=3,            # Wait 3 seconds initially
    retry_backoff=1.5         # Increase wait by 1.5x each time
)
```

## Security Considerations

1. **Never commit credentials**: Use environment variables for SMTP credentials
2. **Use App Passwords**: For Gmail, use App Passwords instead of your main password
3. **Secure storage**: Environment variables should be set securely in production
4. **TLS encryption**: Connections use TLS by default (configurable)

## Testing

Run the test suite to verify Box integration:

```bash
python test_box_integration.py
```

The test suite includes:

- Configuration validation tests
- Successful upload tests
- Authentication failure handling
- Retry logic verification
- Max retries exceeded scenarios
- Custom email content tests
- Integration tests with PDF generation

## Troubleshooting

### "Box integration not properly configured" Error

**Solution**: Set required environment variables:
```bash
export SMTP_USERNAME="your-email@example.com"
export SMTP_PASSWORD="your-app-password"
```

### "SMTP authentication failed" Error

**Solutions**:
1. Verify username and password are correct
2. For Gmail: Use an App Password, not your regular password
3. Check if 2-factor authentication is enabled (required for Gmail)

### Connection Timeout

**Solutions**:
1. Check firewall settings (port 587 must be open)
2. Verify SMTP host and port are correct
3. Increase timeout in code if needed

### Retries Exhausted

**Solutions**:
1. Check network connectivity
2. Verify Box upload email is correct
3. Increase max_retry_attempts in configuration

## Examples

### Example 1: Simple Upload

```python
from pdf_utils import generate_pdf_report, upload_pdf_to_box

# Generate report
pdf = generate_pdf_report("Jane Smith", feedback, chat, "HPV Vaccine")

# Upload to Box
success, msg = upload_pdf_to_box(pdf, "Jane_Smith_Report.pdf")
print(msg)
```

### Example 2: Upload with Error Handling

```python
from pdf_utils import upload_pdf_to_box, BoxUploadError
from box_config import BoxConfig

config = BoxConfig()

if not config.is_configured():
    print(f"Please configure: {config.get_missing_settings()}")
else:
    try:
        success, msg = upload_pdf_to_box(pdf, "report.pdf", config=config)
        if success:
            print(f"✓ {msg}")
    except BoxUploadError as e:
        print(f"✗ Upload failed: {e}")
```

### Example 3: Batch Upload

```python
from pdf_utils import upload_pdf_to_box, BoxUploadError

reports = [
    (pdf1, "student1_report.pdf"),
    (pdf2, "student2_report.pdf"),
    (pdf3, "student3_report.pdf"),
]

results = []
for pdf, filename in reports:
    try:
        success, msg = upload_pdf_to_box(pdf, filename)
        results.append((filename, success, msg))
    except BoxUploadError as e:
        results.append((filename, False, str(e)))

# Print summary
for filename, success, msg in results:
    status = "✓" if success else "✗"
    print(f"{status} {filename}: {msg}")
```

## Support

For issues or questions:

1. Check this documentation
2. Run the test suite: `python test_box_integration.py`
3. Review error messages for specific guidance
4. Check environment variable configuration

## Changelog

### Version 1.0.0 (Initial Release)

- Box email integration for PDF uploads
- Configurable SMTP settings
- Retry logic with exponential backoff
- Comprehensive error handling
- Full test suite
- Documentation and examples
