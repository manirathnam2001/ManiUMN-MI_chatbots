# Box Integration and Logging System

This document describes the Box upload integration and comprehensive logging system for MI Chatbots.

## Overview

The Box integration system provides the ability to automatically upload PDF reports to Box storage via email upload addresses. The system includes comprehensive logging, monitoring, and error handling capabilities.

## Components

### 1. upload_logs.py

Core logging module that provides structured JSON logging for Box upload activities.

**Key Classes:**
- `BoxUploadLogger`: Main logger for tracking upload events
- `LogAnalyzer`: Analytics and reporting tools for log data
- `BoxUploadMonitor`: Real-time monitoring and health checks

**Features:**
- Separate logs for OHI and HPV bots
- UTC timestamps for all entries
- JSON structured format for easy parsing
- Automatic log rotation (10MB per file, 5 backups)
- Error tracking and statistics
- Log cleanup utilities

**Log Format:**
```json
{
  "timestamp": "2025-01-07 16:41:34",
  "bot_type": "OHI",
  "level": "INFO",
  "event_type": "upload_success",
  "message": "Successfully uploaded feedback_report.pdf for John Doe",
  "metadata": {
    "student_name": "John Doe",
    "filename": "feedback_report.pdf",
    "box_email": "OHI_dir.zcdwwmukjr9ab546@u.box.com",
    "status": "success",
    "delivery_time_seconds": 1.5
  }
}
```

### 2. box_integration.py

Box upload functionality with email-based file transfer.

**Key Classes:**
- `BoxUploader`: Handles PDF uploads to Box via email
- Custom exceptions for different error scenarios

**Features:**
- Separate Box email addresses for OHI and HPV bots
- PDF format validation
- Retry logic with exponential backoff
- Network timeout handling
- Integration with logging system

**Box Upload Addresses:**
- OHI Bot: `OHI_dir.zcdwwmukjr9ab546@u.box.com`
- HPV Bot: `HPV_Dir.yqz3brxlhcurhp2l@u.box.com`

### 3. config.json

Configuration file with Box and logging settings.

```json
{
  "box_upload": {
    "ohi_email": "OHI_dir.zcdwwmukjr9ab546@u.box.com",
    "hpv_email": "HPV_Dir.yqz3brxlhcurhp2l@u.box.com",
    "enabled": false
  },
  "logging": {
    "log_directory": "git_logs",
    "max_log_size_mb": 10,
    "backup_count": 5,
    "cleanup_days": 90,
    "enable_monitoring": true
  },
  "email": {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "",
    "sender_password": "",
    "use_tls": true
  }
}
```

## Usage

### Basic Logging

```python
from upload_logs import BoxUploadLogger

# Initialize logger for OHI bot
logger = BoxUploadLogger("OHI")

# Log upload attempt
logger.log_upload_attempt("John Doe", "feedback.pdf", 
                          "OHI_dir.zcdwwmukjr9ab546@u.box.com", 
                          file_size=52000)

# Log success
logger.log_upload_success("John Doe", "feedback.pdf",
                         "OHI_dir.zcdwwmukjr9ab546@u.box.com",
                         delivery_time=1.5)

# Log failure
logger.log_upload_failure("John Doe", "feedback.pdf",
                         "OHI_dir.zcdwwmukjr9ab546@u.box.com",
                         "Network timeout", "NETWORK_ERROR")

# Log email delivery status
logger.log_email_delivery_status("OHI_dir.zcdwwmukjr9ab546@u.box.com", 
                                "sent", message_id="msg123")

# Log errors and warnings
logger.log_error("NETWORK_ERROR", "Connection timed out")
logger.log_warning("STORAGE_WARNING", "Storage quota at 90%")
logger.log_critical("CRITICAL_ERROR", "System failure")
```

### Analytics and Monitoring

```python
from upload_logs import LogAnalyzer, BoxUploadMonitor

# Get upload statistics
analyzer = LogAnalyzer()
stats = analyzer.get_upload_statistics("OHI", days=7)
print(f"Success rate: {stats['success_rate']}%")
print(f"Total attempts: {stats['total_attempts']}")

# Get error summary
errors = analyzer.get_error_summary("OHI", limit=10)
for error in errors:
    print(f"[{error['timestamp']}] {error['message']}")

# Get recent uploads
uploads = analyzer.get_recent_uploads("HPV", limit=20)

# Monitor health
monitor = BoxUploadMonitor()
health = monitor.check_health("OHI", threshold=80.0)
print(f"Status: {health['status']}")
print(f"Success rate: {health['success_rate']}%")

# Generate status report
report = monitor.generate_status_report("HPV")
print(report)

# Cleanup old logs (keep last 90 days)
cleanup_results = analyzer.cleanup_old_logs(days=90)
print(f"Removed {cleanup_results['OHI']} old OHI log entries")
```

### Box Upload

```python
from box_integration import BoxUploader
import io

# Initialize uploader
uploader = BoxUploader("OHI")

# Test connection
test_result = uploader.test_connection()
print(f"Connection status: {test_result['connection_test']}")

# Upload PDF
pdf_buffer = io.BytesIO(pdf_data)
success = uploader.upload_pdf_to_box(
    student_name="John Doe",
    pdf_buffer=pdf_buffer,
    filename="feedback_report.pdf",
    max_retries=3,
    retry_delay=2
)

if success:
    print("Upload successful!")
else:
    print("Upload failed - check logs for details")
```

## Error Handling

The system handles various error scenarios:

### 1. Email Delivery Failures
- SMTP connection errors
- Authentication failures
- Server disconnections
- Retry logic with exponential backoff

### 2. Network Timeouts
- Configurable timeout (default: 30 seconds)
- Automatic retry on timeout
- Logging of timeout events

### 3. Invalid File Formats
- PDF magic number validation
- InvalidFileFormatError exception
- Detailed error logging

### 4. Storage Quota Issues
- StorageQuotaError exception for quota exceeded
- Warning logs for approaching quota limits

### 5. Configuration Errors
- BoxIntegrationError for missing config
- Validation on startup
- Graceful degradation when disabled

## Log Files

Log files are stored in the `git_logs/` directory (configurable):

- `git_logs/box_uploads_ohi_{YYYY-MM-DD}.log` - OHI bot daily upload logs
- `git_logs/box_uploads_hpv_{YYYY-MM-DD}.log` - HPV bot daily upload logs

Each log file:
- Created daily based on UTC date
- Named with format: `box_uploads_{bot_type}_{YYYY-MM-DD}.log`
- Uses JSON format for structured logging
- Contains UTC timestamps
- Tracked in git (rotated files with .log.* extension are ignored)

## Monitoring

### Health Checks

```python
monitor = BoxUploadMonitor()

# Check if success rate is above 80%
health = monitor.check_health("OHI", threshold=80.0)

if health['status'] == 'unhealthy':
    print(f"⚠️ Warning: Success rate is {health['success_rate']}%")
    print(f"Recent errors: {health['recent_errors']}")
    print(f"Critical errors: {health['recent_critical']}")
```

### Statistics

```python
analyzer = LogAnalyzer()

# Last 7 days
stats_week = analyzer.get_upload_statistics("HPV", days=7)

# All time
stats_all = analyzer.get_upload_statistics("HPV")

print(f"7-day success rate: {stats_week['success_rate']}%")
print(f"All-time success rate: {stats_all['success_rate']}%")
```

### Status Reports

```python
monitor = BoxUploadMonitor()
report = monitor.generate_status_report("OHI")
print(report)
```

Output:
```
Box Upload Status Report - OHI Bot
============================================================

Last 7 Days:
  - Total Attempts: 145
  - Successes: 142
  - Failures: 3
  - Success Rate: 97.93%
  - Errors: 3
  - Warnings: 1
  - Critical: 0

All Time:
  - Total Attempts: 1250
  - Successes: 1235
  - Failures: 15
  - Success Rate: 98.8%

Recent Errors (Last 5):
  1. [2025-01-07 10:15:23] Failed to upload report.pdf: Network timeout
  2. [2025-01-06 14:30:12] Failed to upload assessment.pdf: SMTP error
  ...

============================================================
```

## Configuration

### Enable Box Upload

1. Edit `config.json`:
```json
{
  "box_upload": {
    "enabled": true
  }
}
```

2. Configure email settings:
```json
{
  "email": {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "your-email@example.com",
    "sender_password": "your-app-password",
    "use_tls": true
  }
}
```

### Customize Logging

```json
{
  "logging": {
    "log_directory": "git_logs",
    "max_log_size_mb": 10,
    "backup_count": 5,
    "cleanup_days": 90,
    "enable_monitoring": true
  }
}
```

## Testing

Run the test suite:

```bash
python3 test_box_integration.py
```

Tests include:
- Logger initialization and logging
- Log analysis and statistics
- Monitoring and health checks
- Box uploader initialization
- PDF validation
- Log cleanup functionality

## Integration with Existing Code

### In HPV.py or OHI.py

```python
from box_integration import BoxUploader
from upload_logs import BoxUploadLogger

# Initialize at startup
bot_type = "HPV"  # or "OHI"
box_uploader = BoxUploader(bot_type)

# After generating PDF
if st.button("Download Feedback PDF"):
    pdf_buffer = generate_pdf_report(student_name, feedback, chat_history, session_type)
    
    # Offer download to user
    st.download_button(
        label="📥 Download PDF Report",
        data=pdf_buffer,
        file_name=f"MI_Feedback_{student_name}_{timestamp}.pdf",
        mime="application/pdf"
    )
    
    # Optionally upload to Box
    try:
        success = box_uploader.upload_pdf_to_box(
            student_name=student_name,
            pdf_buffer=pdf_buffer,
            filename=f"MI_Feedback_{student_name}_{timestamp}.pdf"
        )
        if success:
            st.success("✅ Report uploaded to Box successfully!")
        else:
            st.info("ℹ️ Report generated but not uploaded to Box (feature disabled)")
    except Exception as e:
        st.warning(f"⚠️ Report generated but upload to Box failed: {e}")
        # Error already logged by BoxUploader
```

## Security Considerations

1. **Credentials**: Store email credentials securely (environment variables or secure config)
2. **File Validation**: All PDFs are validated before upload
3. **Error Logging**: Sensitive information is not logged
4. **Access Control**: Log files should have appropriate permissions
5. **SMTP Security**: Use TLS encryption for email transmission

## Maintenance

### Regular Tasks

1. **Monitor Health**: Check success rates regularly
```python
monitor = BoxUploadMonitor()
health = monitor.check_health("OHI", threshold=80.0)
```

2. **Review Errors**: Check error summaries
```python
analyzer = LogAnalyzer()
errors = analyzer.get_error_summary("HPV", limit=20)
```

3. **Cleanup Old Logs**: Run periodically (e.g., monthly)
```python
analyzer = LogAnalyzer()
results = analyzer.cleanup_old_logs(days=90)
```

4. **Check Statistics**: Monitor trends
```python
stats = analyzer.get_upload_statistics("OHI", days=30)
```

## Troubleshooting

### Common Issues

1. **"Box upload is disabled"**
   - Enable in `config.json`: `"enabled": true`
   - Configure email settings

2. **"Permission denied: /logs"**
   - Change `log_directory` to relative path in `config.json`
   - Or create directory with proper permissions

3. **"SMTP connection failed"**
   - Check SMTP server and port settings
   - Verify credentials
   - Check firewall/network settings

4. **"Invalid PDF format"**
   - Ensure PDF buffer starts with `%PDF-`
   - Check PDF generation process

5. **"Network timeout"**
   - Check network connectivity
   - Increase timeout in `box_integration.py`
   - Check SMTP server status

## Performance Considerations

- Log files rotate automatically to manage disk space
- JSON parsing is efficient for structured queries
- Log cleanup should be scheduled during off-peak hours
- Monitor disk space for log directory
- Consider archiving old logs to external storage

## Future Enhancements

Potential improvements:
1. Email notifications for critical errors
2. Dashboard for monitoring multiple bots
3. Export logs to external monitoring services
4. Automated log analysis and anomaly detection
5. Integration with cloud logging services (e.g., CloudWatch, Stackdriver)
6. Webhook notifications for failures
7. Batch upload support
8. Progress tracking for large files

## Support

For issues or questions:
1. Check this documentation
2. Review log files for detailed error information
3. Run test suite: `python3 test_box_integration.py`
4. Check configuration in `config.json`

## Changelog

### Version 1.0.0 (2025-01-07)
- Initial implementation
- BoxUploadLogger with JSON logging
- LogAnalyzer for statistics and reporting
- BoxUploadMonitor for health checks
- BoxUploader for email-based uploads
- Separate logs for OHI and HPV bots
- Comprehensive error handling
- Test suite with 100% pass rate
