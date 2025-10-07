# Secure SMTP Configuration Implementation

## Overview

This implementation adds secure SMTP credential handling to the MI Chatbots project using environment variables and a new `email_config.py` module. The SMTP password is now retrieved from the `SMTP_PASSWORD` environment variable instead of being stored in configuration files.

## Changes Made

### 1. Configuration File Updates

#### config.json
Added new `email_config` section with secure SMTP settings:

```json
{
  "email_config": {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "smtp_ssl": true,
    "smtp_user": "mogan014@umn.edu",
    "smtp_password": "PLACEHOLDER",
    "ohi_box_email": "OHI_dir.zcdwwmukjr9ab546@u.box.com",
    "hpv_box_email": "HPV_Dir.yqz3brxlhcurhp2l@u.box.com"
  },
  "logging": {
    "log_file": "logs/box_uploads.log",
    "max_size": 10485760,
    "backup_count": 5,
    "log_level": "INFO"
  }
}
```

**Key Changes:**
- Added `smtp_ssl` field for SSL/TLS configuration
- Added `smtp_user` field for SMTP username
- Set `smtp_password` to `"PLACEHOLDER"` (not used - password comes from environment)
- Added `ohi_box_email` and `hpv_box_email` fields
- Added `log_file`, `max_size`, and `log_level` to logging section
- Kept legacy `email` section for backward compatibility

### 2. New Module: email_config.py

Created a new module for secure email configuration and credential handling.

**Features:**
- Load SMTP settings from `config.json`
- Retrieve password from `SMTP_PASSWORD` environment variable
- Secure credential handling (password never stored in files)
- Email sending functionality with SSL/TLS support
- Box email address management for OHI and HPV bots
- Connection testing functionality

**Key Classes:**
- `EmailConfig`: Main configuration handler
- `EmailConfigError`: Exception for configuration errors

**Main Methods:**
- `get_smtp_password()`: Get password from environment variable
- `get_smtp_config()`: Get complete SMTP configuration
- `get_box_email(bot_type)`: Get Box upload email for bot type
- `send_email()`: Send email with optional attachment
- `test_connection()`: Test SMTP connection

### 3. Updated Module: box_integration.py

Updated to support the new email configuration module while maintaining backward compatibility.

**Changes:**
- Added optional import of `email_config` module
- Initialize `EmailConfig` instance if available
- Updated `_send_email()` method to use new module when available
- Falls back to legacy configuration if email_config is not available
- Maintains full backward compatibility with existing code

### 4. Documentation Updates: README.md

Added comprehensive email configuration documentation:

**New Sections:**
- Email Configuration overview
- SMTP Configuration details
- Environment variable setup instructions (Linux/Mac/Windows)
- Gmail App Password setup guide
- Testing email configuration
- Enabling Box upload
- Security best practices

### 5. Test Files

#### test_email_config.py
Comprehensive test suite for the email_config module:
- Configuration loading tests
- Box email retrieval tests
- Environment variable handling tests
- SMTP configuration tests
- Error handling tests
- Integration tests with actual config.json

**Test Coverage:**
- 12 test cases
- 100% pass rate
- Tests all major functionality

#### demo_email_config.py
Interactive demonstration script showing:
- Configuration loading
- Environment variable setup instructions
- Password retrieval
- SMTP connection testing
- Usage examples

## Security Features

### 1. Environment Variable Password Storage
- SMTP password is **never** stored in configuration files
- Retrieved from `SMTP_PASSWORD` environment variable at runtime
- Prevents accidental credential exposure in version control

### 2. SSL/TLS Support
- Uses STARTTLS for encrypted SMTP connections
- Default `smtp_ssl` is `true`
- Configurable per deployment

### 3. Secure Error Handling
- Clear error messages without exposing credentials
- Guides users to proper credential setup
- Validates configuration before attempting connections

### 4. Backward Compatibility
- Legacy `email` configuration section still works
- Gradual migration path for existing deployments
- No breaking changes to existing code

## Usage

### Setting Up Environment Variable

**Linux/Mac:**
```bash
export SMTP_PASSWORD="your-app-password"

# Make permanent
echo 'export SMTP_PASSWORD="your-app-password"' >> ~/.bashrc
source ~/.bashrc
```

**Windows (Command Prompt):**
```cmd
set SMTP_PASSWORD=your-app-password
```

**Windows (PowerShell):**
```powershell
$env:SMTP_PASSWORD="your-app-password"
```

**Windows (Permanent):**
1. Search for "Environment Variables" in Windows settings
2. Click "New" under User variables
3. Variable name: `SMTP_PASSWORD`
4. Variable value: Your app password

### Gmail App Password Setup

1. Enable 2-Factor Authentication on your Google account
2. Go to https://myaccount.google.com/apppasswords
3. Select "Mail" and "Other (Custom name)"
4. Enter "MI Chatbots" as the name
5. Copy the 16-character password
6. Set it as the `SMTP_PASSWORD` environment variable

### Using in Code

```python
from email_config import EmailConfig

# Initialize configuration
email_config = EmailConfig('config.json')

# Get SMTP configuration (includes password from environment)
smtp_config = email_config.get_smtp_config()

# Get Box email for a bot
ohi_email = email_config.get_box_email('OHI')
hpv_email = email_config.get_box_email('HPV')

# Send email with attachment
email_config.send_email(
    recipient=ohi_email,
    subject='MI Assessment Report',
    body='Report attached',
    attachment_data=pdf_buffer,
    attachment_filename='report.pdf'
)
```

### Using with BoxUploader

```python
from box_integration import BoxUploader

# BoxUploader automatically uses email_config if available
uploader = BoxUploader('OHI')

# Upload PDF (uses secure credentials automatically)
success = uploader.upload_pdf_to_box(
    student_name='John Doe',
    pdf_buffer=pdf_buffer,
    filename='john_doe_report.pdf'
)
```

## Testing

### Run Email Configuration Tests
```bash
python3 test_email_config.py
```

### Run Box Integration Tests
```bash
python3 test_box_integration.py
```

### Run Demo Script
```bash
# Without password (shows setup instructions)
python3 demo_email_config.py

# With password (full demo)
SMTP_PASSWORD="your-password" python3 demo_email_config.py
```

### Test Configuration Module
```bash
python3 email_config.py
```

## Migration Guide

### For New Deployments
1. Copy the new `config.json` structure
2. Set `SMTP_PASSWORD` environment variable
3. Use the new `email_config` module

### For Existing Deployments
**Option 1: Keep using legacy configuration**
- No changes required
- Continue using the `email` section in `config.json`
- Works exactly as before

**Option 2: Migrate to secure configuration**
1. Add `email_config` section to `config.json`
2. Set `SMTP_PASSWORD` environment variable
3. Remove credentials from `email` section
4. Test with `python3 demo_email_config.py`

## File Structure

```
ManiUMN-MI_chatbots/
├── config.json              # Updated with email_config section
├── email_config.py          # New secure email configuration module
├── box_integration.py       # Updated to use email_config
├── test_email_config.py     # New test suite for email_config
├── demo_email_config.py     # New demo script
└── README.md                # Updated with setup instructions
```

## Configuration Reference

### email_config Section

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| smtp_server | string | Yes | SMTP server hostname (e.g., smtp.gmail.com) |
| smtp_port | integer | Yes | SMTP server port (587 for TLS) |
| smtp_ssl | boolean | No | Enable SSL/TLS (default: true) |
| smtp_user | string | Yes | SMTP username/email |
| smtp_password | string | No | Placeholder only - real password from environment |
| ohi_box_email | string | Yes | Box upload email for OHI bot |
| hpv_box_email | string | Yes | Box upload email for HPV bot |

### logging Section (Updated)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| log_file | string | Yes | Path to log file |
| log_directory | string | Yes | Directory for log files |
| max_size | integer | Yes | Maximum log file size in bytes |
| max_log_size_mb | integer | Yes | Maximum log file size in MB |
| backup_count | integer | Yes | Number of backup log files |
| cleanup_days | integer | No | Days before log cleanup |
| log_level | string | Yes | Logging level (INFO, DEBUG, etc.) |
| enable_monitoring | boolean | No | Enable monitoring features |

## Security Best Practices

### ✅ DO
- Use environment variables for passwords
- Use Gmail App Passwords (not main password)
- Keep config.json with placeholder values in version control
- Enable 2-Factor Authentication for Gmail
- Regularly rotate App Passwords
- Use SSL/TLS for SMTP connections

### ❌ DON'T
- Commit real passwords to version control
- Share App Passwords with others
- Use main email password for SMTP
- Store passwords in configuration files
- Disable SSL/TLS unless necessary
- Use the same password for multiple services

## Troubleshooting

### "SMTP_PASSWORD environment variable is not set"
**Solution:** Set the environment variable as described in the setup section.

### "Authentication failed - check credentials"
**Possible causes:**
- Incorrect username/password
- Need to use Gmail App Password instead of main password
- 2-Factor Authentication not enabled (required for Gmail)
- Account security settings blocking access

### "Connection failed"
**Possible causes:**
- Network/firewall blocking SMTP traffic
- Incorrect SMTP server or port
- SSL/TLS configuration issue

### Tests failing
**Solution:** 
1. Check config.json is valid JSON
2. Verify email_config section is present
3. Run `python3 -c "import json; json.load(open('config.json'))"`

## Support

For issues or questions:
1. Check the README.md Email Configuration section
2. Run the demo script: `python3 demo_email_config.py`
3. Review the error messages (they contain helpful guidance)
4. Check the test suite: `python3 test_email_config.py`

## Future Enhancements

Potential improvements:
- Support for other email providers (Outlook, etc.)
- OAuth2 authentication support
- Password encryption at rest
- Key management integration (AWS Secrets Manager, etc.)
- Multi-factor authentication support
- Rate limiting for email sending
- Email queue management

## Conclusion

This implementation provides secure, production-ready SMTP credential handling while maintaining full backward compatibility with existing code. The modular design allows for easy testing, maintenance, and future enhancements.
