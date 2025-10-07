#!/usr/bin/env python3
"""
Example: Using Secure Email Configuration with Box Integration

This example demonstrates how to use the new secure email configuration
to send PDF reports to Box with proper SSL/TLS encryption and error handling.
"""

import io
import json
from box_integration import BoxUploader
from email_utils import SecureEmailSender


def example_basic_usage():
    """Example: Basic usage with new email_config."""
    print("=" * 60)
    print("Example 1: Basic Usage with Secure Email Config")
    print("=" * 60)
    
    # Initialize Box uploader (automatically uses email_config if available)
    uploader = BoxUploader("OHI")
    
    # Check connection
    test_results = uploader.test_connection()
    print(f"\nConnection Test Results:")
    print(f"  Box Upload Enabled: {test_results['box_upload_enabled']}")
    print(f"  Using email_config: {test_results.get('using_email_config', False)}")
    print(f"  Box Email: {test_results['box_email']}")
    print(f"  Connection Status: {test_results['connection_test']}")
    print(f"  Message: {test_results['message']}")
    
    # If you want to enable Box upload, set enabled to true in config.json:
    # "box_upload": {
    #     "enabled": true
    # }
    
    print("\n✅ Basic usage example completed")


def example_direct_email_sender():
    """Example: Using SecureEmailSender directly."""
    print("\n" + "=" * 60)
    print("Example 2: Using SecureEmailSender Directly")
    print("=" * 60)
    
    # Load configuration
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    email_config = config.get('email_config', {})
    
    if not email_config:
        print("❌ No email_config found in config.json")
        return
    
    # Create secure email sender
    sender = SecureEmailSender(email_config)
    
    print(f"\n✅ SecureEmailSender initialized")
    print(f"   SMTP Server: {email_config['smtp_server']}")
    print(f"   SMTP Port: {email_config['smtp_port']}")
    print(f"   Use SSL/TLS: {email_config.get('use_ssl', True)}")
    print(f"   From Email: {email_config['from_email']}")
    
    # Test connection
    print("\nTesting connection...")
    test_results = sender.test_connection()
    
    print(f"  Connection: {test_results['connection']}")
    print(f"  Authentication: {test_results['authentication']}")
    print(f"  Message: {test_results['message']}")
    
    # Example: Send email with attachment (commented out to avoid sending)
    # pdf_buffer = io.BytesIO(b'%PDF-1.4\nTest PDF content')
    # success = sender.send_email_with_attachment(
    #     recipient='test@example.com',
    #     subject='Test Report',
    #     body='This is a test report.',
    #     attachment_buffer=pdf_buffer,
    #     attachment_filename='test_report.pdf',
    #     attachment_type='application/pdf'
    # )
    
    print("\n✅ Direct email sender example completed")


def example_upload_pdf():
    """Example: Upload PDF to Box with retry logic."""
    print("\n" + "=" * 60)
    print("Example 3: Upload PDF to Box (Simulated)")
    print("=" * 60)
    
    # Initialize uploader
    uploader = BoxUploader("OHI")
    
    # Create a sample PDF buffer
    pdf_buffer = io.BytesIO(b'%PDF-1.4\n%Test PDF content for demonstration\nSample data...')
    
    # Note: This will only work if box_upload is enabled in config.json
    # and email credentials are properly configured
    
    print("\nSimulating PDF upload...")
    print(f"  Student: John Doe")
    print(f"  Filename: feedback_report.pdf")
    print(f"  Box Email: {uploader._get_box_email()}")
    print(f"  Max Retries: 3")
    
    # The actual upload (commented out to avoid sending real emails)
    # success = uploader.upload_pdf_to_box(
    #     student_name="John Doe",
    #     pdf_buffer=pdf_buffer,
    #     filename="feedback_report.pdf",
    #     max_retries=3,
    #     retry_delay=2
    # )
    
    # if success:
    #     print("\n✅ PDF uploaded successfully!")
    # else:
    #     print("\n❌ PDF upload failed (see logs for details)")
    
    print("\n✅ Upload example completed (simulated)")


def example_error_handling():
    """Example: Error handling with secure email."""
    print("\n" + "=" * 60)
    print("Example 4: Error Handling")
    print("=" * 60)
    
    from email_utils import EmailAuthenticationError, EmailConnectionError, EmailSendError
    
    print("\nThe email_utils module provides specific exceptions:")
    print("  - EmailAuthenticationError: For authentication failures")
    print("  - EmailConnectionError: For connection issues")
    print("  - EmailSendError: For sending failures")
    
    print("\nExample error handling in upload_pdf_to_box:")
    print("""
    try:
        uploader.upload_pdf_to_box(student_name, pdf_buffer, filename)
    except EmailAuthenticationError as e:
        # Handle authentication failure
        print(f"Authentication failed: {e}")
        # Check credentials in config.json
    except EmailConnectionError as e:
        # Handle connection failure
        print(f"Connection failed: {e}")
        # Check network, firewall, SMTP server
    except EmailSendError as e:
        # Handle send failure
        print(f"Send failed: {e}")
        # Check recipient address, attachment size
    """)
    
    print("\n✅ Error handling example completed")


def example_security_features():
    """Example: Security features."""
    print("\n" + "=" * 60)
    print("Example 5: Security Features")
    print("=" * 60)
    
    print("\n🔒 Security Features Implemented:")
    print("\n1. SSL/TLS Encryption:")
    print("   - Port 587: Uses STARTTLS for encrypted connection")
    print("   - Port 465: Uses SSL from the start")
    print("   - Creates secure context with ssl.create_default_context()")
    
    print("\n2. Secure Password Handling:")
    print("   - Passwords stored in config.json (not hardcoded)")
    print("   - Should use app-specific passwords for Gmail")
    print("   - Recommendation: Use environment variables in production")
    
    print("\n3. Authentication Error Handling:")
    print("   - Specific exception for authentication failures")
    print("   - Clear error messages for debugging")
    print("   - Logged for monitoring")
    
    print("\n4. Comprehensive Logging:")
    print("   - All email attempts are logged")
    print("   - Success/failure tracking")
    print("   - Detailed error messages")
    print("   - Integration with BoxUploadLogger")
    
    print("\n5. Connection Timeout:")
    print("   - Default 30-second timeout for sending")
    print("   - Configurable timeout for connection tests")
    print("   - Prevents hanging on network issues")
    
    print("\n6. Backward Compatibility:")
    print("   - Falls back to old 'email' config if 'email_config' not found")
    print("   - Existing code continues to work")
    
    print("\n✅ Security features example completed")


def example_configuration():
    """Example: Configuration options."""
    print("\n" + "=" * 60)
    print("Example 6: Configuration Options")
    print("=" * 60)
    
    print("\nNew email_config structure in config.json:")
    print("""
{
  "email_config": {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "smtp_username": "your-email@umn.edu",
    "smtp_password": "your-app-password",
    "use_ssl": true,
    "from_email": "your-email@umn.edu",
    "ohi_box_email": "OHI_dir.zcdwwmukjr9ab546@u.box.com",
    "hpv_box_email": "HPV_Dir.yqz3brxlhcurhp2l@u.box.com"
  }
}
    """)
    
    print("\nConfiguration notes:")
    print("  - smtp_server: SMTP server address (e.g., smtp.gmail.com)")
    print("  - smtp_port: 587 for STARTTLS, 465 for SSL")
    print("  - smtp_username: Your email username")
    print("  - smtp_password: App-specific password (NOT your regular password)")
    print("  - use_ssl: true for SSL/TLS encryption (recommended)")
    print("  - from_email: Email address to send from")
    print("  - ohi_box_email/hpv_box_email: Box upload addresses")
    
    print("\n✅ Configuration example completed")


def main():
    """Run all examples."""
    print("\n🚀 Secure Email Configuration Examples\n")
    
    try:
        example_basic_usage()
        example_direct_email_sender()
        example_upload_pdf()
        example_error_handling()
        example_security_features()
        example_configuration()
        
        print("\n" + "=" * 60)
        print("✅ All examples completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
