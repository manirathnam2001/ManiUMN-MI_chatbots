#!/usr/bin/env python3
"""
Demonstration of secure SMTP configuration

This script demonstrates how to use the new email_config.py module
for secure credential handling with environment variables.
"""

import os
import sys
from email_config import EmailConfig, EmailConfigError


def main():
    """Demonstrate email configuration usage."""
    print("=" * 70)
    print("Secure SMTP Configuration Demo")
    print("=" * 70)
    print()
    
    # Check if SMTP_PASSWORD is set
    if not os.environ.get('SMTP_PASSWORD'):
        print("⚠️  SMTP_PASSWORD environment variable is not set")
        print()
        print("To use the email functionality, you need to set the SMTP_PASSWORD")
        print("environment variable. Here's how:")
        print()
        print("Linux/Mac:")
        print("  export SMTP_PASSWORD='your-app-password'")
        print()
        print("Windows (Command Prompt):")
        print("  set SMTP_PASSWORD=your-app-password")
        print()
        print("Windows (PowerShell):")
        print("  $env:SMTP_PASSWORD='your-app-password'")
        print()
        print("For Gmail, you need to generate an App Password:")
        print("  1. Enable 2-Factor Authentication")
        print("  2. Go to https://myaccount.google.com/apppasswords")
        print("  3. Generate an App Password for 'Mail'")
        print("  4. Use that password in the SMTP_PASSWORD variable")
        print()
        return 1
    
    print("✅ SMTP_PASSWORD environment variable is set")
    print()
    
    try:
        # Load configuration
        print("Loading email configuration from config.json...")
        email_config = EmailConfig('config.json')
        print("✅ Configuration loaded successfully")
        print()
        
        # Display configuration (without password)
        print("Configuration Details:")
        print("-" * 70)
        print(f"  SMTP Server: {email_config.config.get('smtp_server')}")
        print(f"  SMTP Port: {email_config.config.get('smtp_port')}")
        print(f"  SMTP SSL/TLS: {email_config.config.get('smtp_ssl')}")
        print(f"  SMTP User: {email_config.config.get('smtp_user')}")
        print(f"  Password Source: Environment variable (SMTP_PASSWORD)")
        print()
        
        # Display Box email addresses
        print("Box Upload Email Addresses:")
        print("-" * 70)
        try:
            ohi_email = email_config.get_box_email('OHI')
            print(f"  OHI Bot: {ohi_email}")
        except EmailConfigError as e:
            print(f"  ⚠️  OHI Bot: {e}")
        
        try:
            hpv_email = email_config.get_box_email('HPV')
            print(f"  HPV Bot: {hpv_email}")
        except EmailConfigError as e:
            print(f"  ⚠️  HPV Bot: {e}")
        print()
        
        # Test password retrieval
        print("Testing Environment Variable Retrieval:")
        print("-" * 70)
        try:
            password = email_config.get_smtp_password()
            print(f"  ✅ Password retrieved successfully")
            print(f"  Password length: {len(password)} characters")
            print(f"  Password value: {'*' * len(password)} (hidden for security)")
        except EmailConfigError as e:
            print(f"  ❌ {e}")
        print()
        
        # Test SMTP connection
        print("Testing SMTP Connection:")
        print("-" * 70)
        print("  Attempting to connect to SMTP server...")
        test_result = email_config.test_connection()
        
        if test_result['success']:
            print(f"  ✅ Connection successful!")
            print(f"     {test_result['message']}")
        else:
            print(f"  ❌ Connection failed")
            print(f"     {test_result['message']}")
            print()
            print("  Common issues:")
            print("  - Invalid credentials (check username/password)")
            print("  - Network/firewall blocking SMTP traffic")
            print("  - SMTP server requires app password (e.g., Gmail)")
            print("  - 2-Factor authentication not enabled (required for Gmail)")
        print()
        
        # Display usage example
        print("Usage Example:")
        print("-" * 70)
        print("""
from box_integration import BoxUploader

# Initialize uploader (will automatically use email_config if available)
uploader = BoxUploader('OHI')

# Upload a PDF to Box
success = uploader.upload_pdf_to_box(
    student_name='John Doe',
    pdf_buffer=pdf_buffer,
    filename='john_doe_report.pdf'
)

if success:
    print('Upload successful!')
else:
    print('Upload failed - check logs for details')
""")
        print()
        
        print("=" * 70)
        print("Demo completed successfully!")
        print("=" * 70)
        return 0
        
    except EmailConfigError as e:
        print(f"❌ Configuration error: {e}")
        print()
        print("Please check your config.json file and ensure it has the correct")
        print("email_config section with all required fields.")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
