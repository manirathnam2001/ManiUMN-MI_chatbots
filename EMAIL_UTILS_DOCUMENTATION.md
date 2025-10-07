# Email Utilities Documentation

## Overview

The `email_utils.py` module provides secure SMTP email sending functionality for the MI Chatbots Box integration system. It includes support for environment variables, SSL/TLS connections, comprehensive error handling, and logging.

## Features

- **Secure Credential Management**: Support for environment variables (preferred) and config file credentials
- **SSL/TLS Support**: Encrypted SMTP connections with proper certificate validation
- **Comprehensive Error Handling**: Specific exceptions for configuration and sending errors
- **Flexible Configuration**: Multiple configuration sources with priority order
- **Logging Integration**: Built-in logging for all operations
- **Connection Testing**: Test SMTP connection without sending emails
- **PDF Attachments**: Specialized support for PDF file attachments

## Installation

No additional dependencies are required beyond the standard Python library and existing project dependencies.

## Configuration

### Priority Order

The module checks for credentials in this order:

1. **Environment Variables** (most secure, recommended)
2. **Config File `email_config` section**
3. **Config File `email` section** (legacy)

### Method 1: Environment Variables (Recommended)

Create a `.env` file (or set system environment variables):

```bash
# SMTP Server Settings
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_SSL=true

# SMTP Credentials
SMTP_USERNAME=your-email@umn.edu
SMTP_APP_PASSWORD=your-app-password-here
```

**For Gmail:**
1. Enable 2-factor authentication on your Google account
2. Generate an [App Password](https://myaccount.google.com/apppasswords)
3. Use the App Password as `SMTP_APP_PASSWORD`

### Method 2: Configuration File

Update `config.json`:

```json
{
  "email_config": {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "smtp_use_ssl": true,
    "smtp_username": "your-email@umn.edu",
    "smtp_app_password": "your-app-password",
    "ohi_box_email": "OHI_dir.zcdwwmukjr9ab546@u.box.com",
    "hpv_box_email": "HPV_Dir.yqz3brxlhcurhp2l@u.box.com"
  }
}
```

**Note:** Environment variables are more secure as they don't commit credentials to version control.

## Usage

### Basic Email Sending

```python
from email_utils import SecureEmailSender
import io

# Load configuration
config = {...}  # Your config dictionary

# Initialize sender
sender = SecureEmailSender(config)

# Create PDF buffer
pdf_buffer = io.BytesIO(b'PDF content here')

# Send email with attachment
success = sender.send_email_with_attachment(
    recipient='recipient@example.com',
    subject='Test Email',
    body='This is a test email',
    attachment_buffer=pdf_buffer,
    attachment_filename='document.pdf',
    attachment_type='application/pdf'
)

if success:
    print("Email sent successfully!")
```

### Box Upload Email (Convenience Function)

```python
from email_utils import send_box_upload_email
import io

# Send PDF to Box
success = send_box_upload_email(
    config=config,
    bot_type='OHI',  # or 'HPV'
    student_name='John Doe',
    pdf_buffer=pdf_buffer,
    filename='assessment_report.pdf'
)
```

### Testing Connection

```python
from email_utils import SecureEmailSender

sender = SecureEmailSender(config)
result = sender.test_connection()

print(f"Status: {result['status']}")
print(f"Message: {result['message']}")
print(f"Authentication: {result['authentication']}")
```

## API Reference

### SecureEmailSender Class

#### `__init__(config=None, logger=None)`

Initialize the secure email sender.

**Parameters:**
- `config` (dict, optional): Email configuration dictionary
- `logger` (logging.Logger, optional): Logger instance for operations

#### `get_smtp_credentials()`

Get SMTP credentials from environment variables or config.

**Returns:** Dictionary with 'username' and 'password'

**Raises:** `EmailConfigError` if credentials not found

#### `get_smtp_settings()`

Get SMTP server settings from config or environment variables.

**Returns:** Dictionary with smtp_server, smtp_port, and use_ssl settings

#### `send_email_with_attachment(recipient, subject, body, attachment_buffer, attachment_filename, ...)`

Send an email with an attachment using secure SMTP.

**Parameters:**
- `recipient` (str): Email recipient address
- `subject` (str): Email subject
- `body` (str): Email body text
- `attachment_buffer` (io.BytesIO): Buffer containing attachment data
- `attachment_filename` (str): Filename for the attachment
- `attachment_type` (str, optional): MIME type (default: 'application/pdf')
- `sender_email` (str, optional): Sender email override
- `timeout` (int, optional): Connection timeout in seconds (default: 30)

**Returns:** `True` if successful, `False` otherwise

**Raises:** `EmailSendError` if sending fails

#### `test_connection()`

Test the SMTP connection without sending an email.

**Returns:** Dictionary with test results:
- `status`: 'success', 'config_error', 'auth_failed', 'smtp_error', or 'error'
- `message`: Human-readable status message
- `smtp_server`: SMTP server address
- `smtp_port`: SMTP port number
- `authentication`: Boolean indicating if authentication succeeded

### Convenience Functions

#### `send_box_upload_email(config, bot_type, student_name, pdf_buffer, filename, logger=None)`

Send a Box upload email for assessment reports.

**Parameters:**
- `config` (dict): Configuration dictionary
- `bot_type` (str): Type of bot ('OHI' or 'HPV')
- `student_name` (str): Name of the student
- `pdf_buffer` (io.BytesIO): PDF data buffer
- `filename` (str): PDF filename
- `logger` (logging.Logger, optional): Logger instance

**Returns:** `True` if successful, `False` otherwise

## Error Handling

### Exception Types

- **`EmailConfigError`**: Raised when configuration is invalid or incomplete
- **`EmailSendError`**: Raised when email sending fails

### Example Error Handling

```python
from email_utils import SecureEmailSender, EmailSendError, EmailConfigError

try:
    sender = SecureEmailSender(config)
    sender.send_email_with_attachment(...)
except EmailConfigError as e:
    print(f"Configuration error: {e}")
    # Check credentials and settings
except EmailSendError as e:
    print(f"Failed to send email: {e}")
    # Retry or log the failure
```

## Security Best Practices

1. **Use Environment Variables**: Store credentials in environment variables, not in code
2. **Never Commit Credentials**: Add `.env` to `.gitignore`
3. **Use App Passwords**: For Gmail, use App Passwords instead of account passwords
4. **Enable 2FA**: Enable two-factor authentication on email accounts
5. **Restrict Permissions**: Limit file permissions on `.env` files
6. **Rotate Credentials**: Regularly update passwords and app passwords
7. **Use TLS**: Always enable SSL/TLS for SMTP connections

## Testing

Run the test suite:

```bash
python3 test_email_utils.py
```

Test coverage includes:
- Configuration loading from multiple sources
- Environment variable priority
- SMTP connection and authentication
- Email sending with attachments
- Error handling scenarios
- Connection testing

## Integration with Box Upload

The `email_utils.py` module is integrated with `box_integration.py`:

```python
from box_integration import BoxUploader

# Initialize uploader (automatically uses email_utils)
uploader = BoxUploader('OHI')

# Upload PDF to Box
success = uploader.upload_pdf_to_box(
    student_name='John Doe',
    pdf_buffer=pdf_buffer,
    filename='report.pdf'
)
```

The `BoxUploader` class automatically uses `SecureEmailSender` for all email operations, providing:
- Secure credential handling
- SSL/TLS connections
- Comprehensive logging
- Retry logic
- Error handling

## Troubleshooting

### "SMTP credentials not found"

**Solution:** Set environment variables or configure credentials in `config.json`:
```bash
export SMTP_USERNAME="your-email@umn.edu"
export SMTP_APP_PASSWORD="your-app-password"
```

### "SMTP authentication failed"

**Solutions:**
1. Verify credentials are correct
2. For Gmail, ensure you're using an App Password, not your account password
3. Check that 2FA is enabled on your account
4. Verify the App Password hasn't expired

### "Connection timeout"

**Solutions:**
1. Check network connectivity
2. Verify firewall isn't blocking SMTP ports (587, 465)
3. Test with a longer timeout value
4. Check SMTP server status

### "TLS/SSL error"

**Solutions:**
1. Ensure `smtp_use_ssl` is set to `true`
2. Update Python's SSL certificates: `pip install --upgrade certifi`
3. Check that your Python version supports TLS 1.2+

## Examples

### Example 1: Simple Email Test

```python
from email_utils import SecureEmailSender
import json

# Load config
with open('config.json') as f:
    config = json.load(f)

# Test connection
sender = SecureEmailSender(config)
result = sender.test_connection()

if result['status'] == 'success':
    print("✅ Email configuration is working!")
else:
    print(f"❌ Error: {result['message']}")
```

### Example 2: Send PDF Report

```python
from email_utils import send_box_upload_email
from pdf_utils import generate_pdf_report
import json

# Generate PDF
pdf_buffer = generate_pdf_report(student_name, transcript, scores)

# Load config
with open('config.json') as f:
    config = json.load(f)

# Send to Box
success = send_box_upload_email(
    config=config,
    bot_type='OHI',
    student_name='John Doe',
    pdf_buffer=pdf_buffer,
    filename='john_doe_report.pdf'
)

if success:
    print("Report uploaded to Box!")
```

### Example 3: Using Environment Variables

```python
import os
from email_utils import SecureEmailSender

# Set credentials via environment
os.environ['SMTP_USERNAME'] = 'user@umn.edu'
os.environ['SMTP_APP_PASSWORD'] = 'app-password'

# Initialize sender (will use env vars)
sender = SecureEmailSender()

# Test connection
result = sender.test_connection()
print(f"Connection status: {result['status']}")
```

## Related Documentation

- [Box Integration Setup Guide](BOX_SETUP.md)
- [Box Integration Documentation](BOX_INTEGRATION.md)
- [Main README](README.md)

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review existing documentation
3. Check logs for detailed error messages
4. Verify configuration and credentials

## Version History

- **v1.0** (2025): Initial release with secure SMTP support, environment variables, and comprehensive testing
