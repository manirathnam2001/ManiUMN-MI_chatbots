# Box Integration Setup Guide

Quick start guide for setting up Box upload and logging for MI Chatbots.

## 🚀 Quick Setup

### 1. Prerequisites

The Box integration is already installed and ready to use. No additional packages are required.

### 2. Enable Box Upload

Edit `config.json` to enable Box upload:

```json
{
  "box_upload": {
    "ohi_email": "OHI_dir.zcdwwmukjr9ab546@u.box.com",
    "hpv_email": "HPV_Dir.yqz3brxlhcurhp2l@u.box.com",
    "enabled": true  // Change this to true
  }
}
```

### 3. Configure Email Settings

Add your SMTP credentials to `config.json`:

```json
{
  "email": {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "your-email@gmail.com",
    "sender_password": "your-app-password",
    "use_tls": true
  }
}
```

**For Gmail:**
1. Enable 2-factor authentication
2. Generate an [App Password](https://myaccount.google.com/apppasswords)
3. Use the App Password as `sender_password`

### 4. Test the Setup

Run the test suite to verify everything works:

```bash
python3 test_box_integration.py
```

## 📝 Basic Usage

### Test Box Connection

```python
from box_integration import BoxUploader

# Initialize uploader
uploader = BoxUploader("HPV")  # or "OHI"

# Test connection
result = uploader.test_connection()
print(result)
```

### Upload a PDF

```python
import io
from box_integration import BoxUploader

uploader = BoxUploader("HPV")

# Create or load PDF buffer
with open("report.pdf", "rb") as f:
    pdf_buffer = io.BytesIO(f.read())

# Upload to Box
success = uploader.upload_pdf_to_box(
    student_name="John Doe",
    pdf_buffer=pdf_buffer,
    filename="feedback_report.pdf"
)

if success:
    print("✅ Upload successful!")
else:
    print("❌ Upload failed")
```

### View Upload Logs

```python
from upload_logs import LogAnalyzer

analyzer = LogAnalyzer()

# Get statistics
stats = analyzer.get_upload_statistics("HPV", days=7)
print(f"Success rate: {stats['success_rate']}%")
print(f"Total uploads: {stats['total_attempts']}")

# View recent errors
errors = analyzer.get_error_summary("HPV", limit=5)
for error in errors:
    print(f"[{error['timestamp']}] {error['message']}")
```

## 🎯 Integration into HPV.py/OHI.py

### Minimal Integration

Add these lines to your existing app:

```python
# At the top of your file
from box_integration import BoxUploader

# Initialize at app startup
BOT_TYPE = "HPV"  # or "OHI"
if 'box_uploader' not in st.session_state:
    try:
        st.session_state.box_uploader = BoxUploader(BOT_TYPE)
    except Exception as e:
        st.session_state.box_uploader = None
        st.warning(f"Box upload unavailable: {e}")

# After generating PDF
if st.session_state.box_uploader and st.button("Upload to Box"):
    with st.spinner("Uploading..."):
        # Create a copy of buffer for upload
        upload_buffer = io.BytesIO(pdf_buffer.getvalue())
        
        success = st.session_state.box_uploader.upload_pdf_to_box(
            student_name=student_name,
            pdf_buffer=upload_buffer,
            filename=filename
        )
        
        if success:
            st.success("✅ Uploaded to Box!")
        else:
            st.error("❌ Upload failed")
```

### Full Integration with Monitoring

See `box_integration_example.py` for complete examples including:
- Monitoring dashboard
- Admin panel
- Sidebar widgets
- Error handling

## 📊 Monitoring

### Check System Health

```python
from upload_logs import BoxUploadMonitor

monitor = BoxUploadMonitor()
health = monitor.check_health("HPV", threshold=80.0)

print(f"Status: {health['status']}")
print(f"Success Rate: {health['success_rate']}%")
```

### Generate Status Report

```python
monitor = BoxUploadMonitor()
report = monitor.generate_status_report("HPV")
print(report)
```

### View Upload Statistics

```python
from upload_logs import LogAnalyzer

analyzer = LogAnalyzer()

# Last 7 days
stats_week = analyzer.get_upload_statistics("HPV", days=7)

# All time
stats_all = analyzer.get_upload_statistics("HPV")

print(f"7-day success rate: {stats_week['success_rate']}%")
print(f"All-time success rate: {stats_all['success_rate']}%")
```

## 🔧 Configuration Options

### Box Upload Settings

```json
{
  "box_upload": {
    "ohi_email": "OHI_dir.zcdwwmukjr9ab546@u.box.com",
    "hpv_email": "HPV_Dir.yqz3brxlhcurhp2l@u.box.com",
    "enabled": true
  }
}
```

### Logging Settings

```json
{
  "logging": {
    "log_directory": "logs",
    "max_log_size_mb": 10,
    "backup_count": 5,
    "cleanup_days": 90,
    "enable_monitoring": true
  }
}
```

### Email Settings

```json
{
  "email": {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "your-email@gmail.com",
    "sender_password": "your-app-password",
    "use_tls": true
  }
}
```

## 📁 Log Files

Logs are stored in the `logs/` directory:
- `logs/box_uploads_ohi.log` - OHI bot logs
- `logs/box_uploads_hpv.log` - HPV bot logs

Each log entry is in JSON format:
```json
{
  "timestamp": "2025-01-07 16:41:34",
  "bot_type": "HPV",
  "level": "INFO",
  "event_type": "upload_success",
  "message": "Successfully uploaded report.pdf for John Doe",
  "metadata": {
    "student_name": "John Doe",
    "filename": "report.pdf",
    "box_email": "HPV_Dir.yqz3brxlhcurhp2l@u.box.com",
    "status": "success"
  }
}
```

## 🧹 Maintenance

### Clean Up Old Logs

```python
from upload_logs import LogAnalyzer

analyzer = LogAnalyzer()
results = analyzer.cleanup_old_logs(days=90)

print(f"Removed {results['OHI']} old OHI log entries")
print(f"Removed {results['HPV']} old HPV log entries")
```

### Monitor Disk Space

```bash
# Check log directory size
du -sh logs/

# Check individual log files
ls -lh logs/
```

## 🐛 Troubleshooting

### "Box upload is disabled"

Enable in `config.json`:
```json
{
  "box_upload": {
    "enabled": true
  }
}
```

### "SMTP connection failed"

Check your email settings:
1. Verify SMTP server and port
2. Check username/password
3. For Gmail, use an [App Password](https://myaccount.google.com/apppasswords)
4. Check firewall settings

### "Permission denied: /logs"

The log directory is relative. Should work without special permissions.
If issues persist, change in `config.json`:
```json
{
  "logging": {
    "log_directory": "./logs"
  }
}
```

### "Invalid PDF format"

Ensure your PDF buffer is valid:
```python
# Check PDF header
pdf_buffer.seek(0)
header = pdf_buffer.read(5)
print(header)  # Should be b'%PDF-'
pdf_buffer.seek(0)  # Reset
```

## 📚 Additional Resources

- **Full Documentation**: See `BOX_INTEGRATION.md`
- **Integration Examples**: See `box_integration_example.py`
- **Test Suite**: Run `python3 test_box_integration.py`

## 🔒 Security Notes

1. **Never commit credentials** to git
2. Use environment variables for sensitive data
3. Enable 2FA on email accounts
4. Use App Passwords instead of account passwords
5. Restrict log file permissions if needed

## ❓ FAQ

### Q: Is Box upload required?
A: No, it's optional. The app works fine without it.

### Q: Can I use a different email provider?
A: Yes, just update the SMTP settings in `config.json`.

### Q: How do I disable Box upload?
A: Set `"enabled": false` in `config.json`.

### Q: Where are the logs stored?
A: In the `logs/` directory, separate files for OHI and HPV.

### Q: How do I view logs?
A: Use the LogAnalyzer class or open log files directly (JSON format).

### Q: What if upload fails?
A: Users can still download the PDF. Failures are logged for troubleshooting.

## 📞 Support

For issues:
1. Check this guide
2. Run tests: `python3 test_box_integration.py`
3. Check logs in `logs/` directory
4. Review `BOX_INTEGRATION.md` for detailed documentation

## ✅ Checklist

Before deploying:
- [ ] Enable Box upload in `config.json`
- [ ] Configure email settings
- [ ] Test connection with `test_box_integration.py`
- [ ] Verify Box email addresses are correct
- [ ] Test upload with sample PDF
- [ ] Check logs are being created
- [ ] Set up log rotation/cleanup schedule
- [ ] Document any customizations

---

**Note**: Box upload is disabled by default for safety. Enable it only after configuring email settings.
