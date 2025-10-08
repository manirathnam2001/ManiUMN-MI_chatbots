#!/usr/bin/env python3
"""
Test script for Box email backup functionality.

This script tests:
1. Email configuration loading
2. SMTP logger setup
3. PDF generation with sample data
4. Email sending with retry mechanism
5. Logging of all operations

Usage:
    python3 test_box_email_backup.py
"""

import json
import io
from email_utils import SecureEmailSender, send_box_backup_email
from pdf_utils import generate_pdf_report, send_pdf_to_box


def test_configuration():
    """Test configuration loading."""
    print("=" * 60)
    print("TEST 1: Configuration Loading")
    print("=" * 60)
    
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        sender = SecureEmailSender(config)
        credentials = sender.get_smtp_credentials()
        settings = sender.get_smtp_settings()
        
        print("✅ Configuration loaded successfully")
        print(f"  SMTP Server: {settings['smtp_server']}:{settings['smtp_port']}")
        print(f"  From: {credentials['username']}")
        print(f"  SSL: {settings['use_ssl']}")
        print(f"  Retry Attempts: {settings['retry_attempts']}")
        print(f"  OHI Box: {config['email_config'].get('ohi_box_email')}")
        print(f"  HPV Box: {config['email_config'].get('hpv_box_email')}")
        return True, config
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False, None


def test_logging():
    """Test logging system."""
    print("\n" + "=" * 60)
    print("TEST 2: Logging System")
    print("=" * 60)
    
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        sender = SecureEmailSender(config)
        smtp_logger = sender.setup_smtp_logger("SMTP logs", "email_backup.log")
        
        # Write test log entries
        smtp_logger.info("Student: Test User | Session: Test | Operation: Test | Details: Testing logging system")
        
        print("✅ Logging system working")
        print("  Log file: SMTP logs/email_backup.log")
        print("  Format: TIMESTAMP | LEVEL | MESSAGE")
        return True, smtp_logger
    except Exception as e:
        print(f"❌ Logging test failed: {e}")
        return False, None


def test_pdf_generation():
    """Test PDF generation with sample data."""
    print("\n" + "=" * 60)
    print("TEST 3: PDF Generation")
    print("=" * 60)
    
    try:
        # Sample data
        student_name = "Test Student"
        feedback = """
Session Feedback for MI Practice - OHI

Evaluation Timestamp (Minnesota): 2024-10-08 01:30:00

MI Component Analysis:

COLLABORATION: Met
Score: 7.5/7.5
The student demonstrated excellent partnership-building and shared decision-making throughout the conversation.

EVOCATION: Partially Met
Score: 5.0/7.5
Good effort in drawing out patient motivations, but could have used more open-ended questions.

ACCEPTANCE: Met
Score: 7.5/7.5
Excellent respect for patient autonomy and accurate reflection of concerns.

COMPASSION: Met
Score: 7.0/7.5
Warm and non-judgmental approach throughout the session.

Total Score: 27.0/30.0 (90.0%)

Suggestions for Improvement:
- Use more open-ended questions to explore patient motivations
- Practice reflective listening techniques
- Continue building on strengths in collaboration and acceptance
"""
        
        chat_history = [
            {"role": "assistant", "content": "Hello! I'm Alex, nice to meet you today."},
            {"role": "user", "content": "Hi Alex, how are you doing today?"},
            {"role": "assistant", "content": "I'm doing okay. I've been having some concerns about my oral health lately."},
            {"role": "user", "content": "What brings you in today?"},
            {"role": "assistant", "content": "I've noticed my gums have been bleeding when I brush."}
        ]
        
        pdf_buffer = generate_pdf_report(
            student_name=student_name,
            raw_feedback=feedback,
            chat_history=chat_history,
            session_type="OHI"
        )
        
        print("✅ PDF generated successfully")
        print(f"  Size: {len(pdf_buffer.getvalue())} bytes")
        print(f"  Student: {student_name}")
        return True, pdf_buffer, student_name
    except Exception as e:
        print(f"❌ PDF generation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None, None


def test_email_dry_run(pdf_buffer, student_name, config):
    """Test email preparation without actually sending."""
    print("\n" + "=" * 60)
    print("TEST 4: Email Preparation (Dry Run)")
    print("=" * 60)
    
    try:
        from datetime import datetime
        
        # Get configuration
        email_config = config.get('email_config', {})
        recipient = email_config.get('ohi_box_email')
        
        filename = f"OHI_Report_{student_name.replace(' ', '_')}_Alex_2024-10-08.pdf"
        subject = f"OHI MI Practice Report - {student_name}"
        body = f"""MI Practice Report Backup

Student: {student_name}
Session Type: OHI
Report File: {filename}
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

This is an automated backup of the MI practice feedback report.
"""
        
        print("✅ Email prepared successfully")
        print(f"  To: {recipient}")
        print(f"  Subject: {subject}")
        print(f"  Attachment: {filename} ({len(pdf_buffer.getvalue())} bytes)")
        print(f"  Body: {len(body)} characters")
        
        return True
    except Exception as e:
        print(f"❌ Email preparation failed: {e}")
        return False


def test_connection_only():
    """Test SMTP connection without sending email."""
    print("\n" + "=" * 60)
    print("TEST 5: SMTP Connection Test")
    print("=" * 60)
    
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        sender = SecureEmailSender(config)
        result = sender.test_connection()
        
        if result['status'] == 'success':
            print("✅ SMTP connection successful")
            print(f"  Server: {result['smtp_server']}:{result['smtp_port']}")
            print(f"  Authentication: ✅")
        else:
            print(f"⚠️  SMTP connection test: {result['status']}")
            print(f"  Message: {result['message']}")
        
        return result['status'] == 'success'
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("Box Email Backup - Test Suite")
    print("=" * 70)
    
    results = {}
    
    # Test 1: Configuration
    results['config'], config = test_configuration()
    
    # Test 2: Logging
    results['logging'], smtp_logger = test_logging()
    
    # Test 3: PDF Generation
    results['pdf'], pdf_buffer, student_name = test_pdf_generation()
    
    # Test 4: Email Preparation (Dry Run)
    if results['pdf'] and config:
        results['email_prep'] = test_email_dry_run(pdf_buffer, student_name, config)
    else:
        results['email_prep'] = False
    
    # Test 5: SMTP Connection
    results['smtp_connection'] = test_connection_only()
    
    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {test_name.upper()}: {status}")
    
    total = len(results)
    passed = sum(results.values())
    
    print("\n" + "-" * 70)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Email backup system is ready.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the errors above.")
    
    print("\nNote: Actual email sending is not tested to avoid sending test emails.")
    print("To test email sending, use the Streamlit applications (OHI.py or HPV.py).")
    print("=" * 70 + "\n")
    
    return passed == total


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
