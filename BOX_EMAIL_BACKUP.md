# Box Email Backup Feature - Implementation Documentation

## Overview

This document describes the Box email backup feature implemented for the OHI and HPV MI Practice chatbots. The feature automatically emails generated PDF feedback reports to specific Box email addresses for backup and archival purposes.

## Features

### 1. Automatic Email Backup
- PDFs are automatically backed up to Box after generation
- Fail-safe design: PDF download works even if email fails
- User-friendly notifications for success/failure

### 2. Retry Mechanism
- 3 automatic retry attempts on failure
- 5-second delay between retries
- Detailed logging of each attempt

### 3. Comprehensive Logging
- Daily rotating logs in "SMTP logs" directory
- 30-day log retention
- Structured log format with timestamp, student name, operation, and details
- Both file and console logging

### 4. Secure Configuration
- SMTP credentials stored in config.json
- Support for environment variables
- SSL/TLS encryption for all email transmission

## Configuration

### config.json Settings

```json
{
  "email_config": {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "smtp_use_ssl": true,
    "smtp_username": "mogan014@umn.edu",
    "smtp_app_password": "ynpx zorq rmof wssy",
    "connection_timeout": 30,
    "retry_attempts": 3,
    "retry_delay": 5,
    "ohi_box_email": "OHI_dir.zcdwwmukjr9ab546@u.box.com",
    "hpv_box_email": "HPV_Dir.yqz3brxlhcurhp2l@u.box.com"
  },
  "logging": {
    "smtp_log_directory": "SMTP logs",
    "smtp_log_file": "SMTP logs/email_backup.log",
    "smtp_max_log_size_mb": 10,
    "smtp_backup_count": 30
  }
}
```

### Box Email Addresses
- **OHI**: OHI_dir.zcdwwmukjr9ab546@u.box.com
- **HPV**: HPV_Dir.yqz3brxlhcurhp2l@u.box.com

## Architecture

### Module Structure

#### 1. email_utils.py
Core email functionality with the following components:

**Classes:**
- `EmailConfigError`: Exception for configuration errors
- `EmailSendError`: Exception for email sending failures
- `SecureEmailSender`: Main class for secure email operations

**Key Methods:**
- `setup_smtp_logger()`: Sets up rotating file logger
- `send_email_with_attachment()`: Basic email sending
- `send_email_with_retry()`: Email sending with retry logic
- `test_connection()`: Test SMTP connection without sending

**Helper Functions:**
- `send_box_backup_email()`: Convenience function for Box backup

#### 2. pdf_utils.py
Enhanced with email backup integration:

**New Functions:**
- `send_pdf_to_box()`: Send PDF to Box email with error handling

#### 3. OHI.py & HPV.py
Integrated email backup after PDF generation:
- Automatic backup attempt after PDF is generated
- User feedback via Streamlit UI
- Session state tracking to prevent duplicate sends
- Fail-safe error handling

## Usage

### In Applications (Automatic)

The email backup happens automatically when a student completes a session and generates a PDF:

1. Student completes MI practice session
2. Clicks "Finish Session & Get Feedback"
3. PDF is generated
4. Email backup is automatically attempted
5. User sees success/warning message
6. PDF download button is always available

### User Experience

**Success:**
```
✅ Report successfully backed up to Box!
📥 Download OHI MI Performance Report (PDF)
```

**Failure (Fail-Safe):**
```
⚠️ Box backup failed after 3 attempts. Your PDF is still available for download below.
Details: [error message]
📥 Download OHI MI Performance Report (PDF)
```

### Testing

Run the test suite to verify functionality:

```bash
python3 test_box_email_backup.py
```

Tests include:
- Configuration loading
- Logging system
- PDF generation
- Email preparation
- SMTP connection

## Log Format

Logs are written to `SMTP logs/email_backup.log` with the following format:

```
YYYY-MM-DD HH:MM:SS | LEVEL | Student: NAME | Session: TYPE | Operation: STATUS | Details: MESSAGE
```

**Example Log Entries:**

```
2024-10-08 01:30:15 | INFO | Student: John Doe | Session: OHI | Operation: Email Backup Attempt 1/3 | Recipient: OHI_dir.zcdwwmukjr9ab546@u.box.com | File: OHI_Report_John_Doe_Alex_2024-10-08.pdf
2024-10-08 01:30:18 | INFO | Student: John Doe | Session: OHI | Operation: SUCCESS | Details: Email backup completed successfully on attempt 1
```

**Retry Example:**

```
2024-10-08 01:35:20 | INFO | Student: Jane Smith | Session: HPV Vaccine | Operation: Email Backup Attempt 1/3 | Recipient: HPV_Dir.yqz3brxlhcurhp2l@u.box.com | File: HPV_Report_Jane_Smith_Diana_2024-10-08.pdf
2024-10-08 01:35:23 | WARNING | Student: Jane Smith | Session: HPV Vaccine | Operation: WARNING | Details: Email send failed on attempt 1/3 - SMTP error
2024-10-08 01:35:23 | INFO | Student: Jane Smith | Session: HPV Vaccine | Operation: RETRY | Details: Waiting 5 seconds before retry 2
2024-10-08 01:35:29 | INFO | Student: Jane Smith | Session: HPV Vaccine | Operation: Email Backup Attempt 2/3 | Recipient: HPV_Dir.yqz3brxlhcurhp2l@u.box.com | File: HPV_Report_Jane_Smith_Diana_2024-10-08.pdf
2024-10-08 01:35:32 | INFO | Student: Jane Smith | Session: HPV Vaccine | Operation: SUCCESS | Details: Email backup completed successfully on attempt 2
```

## Error Handling

### Fail-Safe Design

The implementation is designed to never block PDF downloads:

1. **Email failure doesn't prevent PDF generation**
2. **Users always see the download button**
3. **Clear messaging about backup status**
4. **Technical errors logged but not shown to users**

### Error Types

1. **Configuration Errors**: Missing credentials or Box emails
2. **Authentication Errors**: Invalid SMTP credentials
3. **Network Errors**: Connection timeout or network issues
4. **SMTP Errors**: Server-side issues

All errors are logged with full details for troubleshooting.

## Security

### Credential Management

- SMTP password stored in config.json (should be protected)
- Support for environment variables (more secure)
- SSL/TLS encryption for all email transmission
- No credentials logged

### Best Practices

1. **Protect config.json**: Ensure proper file permissions
2. **Use environment variables**: For production deployments
3. **Rotate credentials**: Regularly update SMTP password
4. **Monitor logs**: Review SMTP logs for suspicious activity

## Maintenance

### Log Rotation

- Logs rotate daily at midnight
- 30 days of logs retained
- Old logs automatically deleted
- Log directory: `SMTP logs/`

### Monitoring

Check logs regularly for:
- Failed backup attempts
- Authentication issues
- Unusual patterns

### Troubleshooting

**Email not sending:**
1. Check SMTP credentials in config.json
2. Verify Box email addresses
3. Test connection: `python3 email_utils.py`
4. Review SMTP logs for errors

**Logs not created:**
1. Verify "SMTP logs" directory exists
2. Check write permissions
3. Review console output for errors

## Files Modified

- `config.json` - Added email configuration
- `email_utils.py` - Enhanced with logging and retry
- `pdf_utils.py` - Added Box backup function
- `OHI.py` - Integrated email backup
- `HPV.py` - Integrated email backup
- `.gitignore` - Exclude log files

## Files Created

- `SMTP logs/.gitkeep` - Track log directory
- `test_box_email_backup.py` - Test suite
- `BOX_EMAIL_BACKUP.md` - This documentation

## Future Enhancements

Potential improvements:
1. Email delivery confirmation
2. Configurable retry delays
3. Dashboard for monitoring backups
4. Support for multiple recipients
5. Email templates
6. Backup to multiple cloud services

## Support

For issues or questions:
1. Review logs in `SMTP logs/`
2. Run test suite: `python3 test_box_email_backup.py`
3. Check configuration in `config.json`
4. Verify SMTP connection

## Changelog

### Version 1.0 (2024-10-08)
- Initial implementation
- Email backup with retry mechanism
- Daily rotating logs
- Integration with OHI and HPV applications
- Comprehensive error handling
- Test suite
