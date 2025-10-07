#!/usr/bin/env python3
"""
Test script for email_utils secure email functionality.

Tests:
- SecureEmailSender initialization
- Configuration validation
- Connection testing
- Error handling
"""

import json
import os
import sys
import io
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from email_utils import (
    SecureEmailSender,
    EmailError,
    EmailAuthenticationError,
    EmailConnectionError,
    EmailSendError
)


def test_secure_email_sender_init():
    """Test SecureEmailSender initialization."""
    print("Testing SecureEmailSender initialization...")
    
    try:
        # Test with valid config
        config = {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'smtp_username': 'test@example.com',
            'smtp_password': 'password',
            'use_ssl': True,
            'from_email': 'test@example.com'
        }
        
        sender = SecureEmailSender(config)
        assert sender.config == config, "Config should be stored"
        
        print("  ✅ SecureEmailSender initialization tests passed")
        return True
        
    except AssertionError as e:
        print(f"  ❌ SecureEmailSender initialization test failed: {e}")
        return False
    except Exception as e:
        print(f"  ❌ SecureEmailSender initialization test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_validation():
    """Test configuration validation."""
    print("Testing configuration validation...")
    
    try:
        # Test missing required field
        invalid_config = {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            # Missing smtp_username and from_email
        }
        
        try:
            sender = SecureEmailSender(invalid_config)
            assert False, "Should raise EmailError for missing config"
        except EmailError as e:
            assert "Missing required email configuration" in str(e), \
                "Error message should mention missing config"
        
        # Test valid config
        valid_config = {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'smtp_username': 'test@example.com',
            'smtp_password': 'password',
            'use_ssl': True,
            'from_email': 'test@example.com'
        }
        
        sender = SecureEmailSender(valid_config)
        assert sender is not None, "Should create sender with valid config"
        
        print("  ✅ Configuration validation tests passed")
        return True
        
    except AssertionError as e:
        print(f"  ❌ Configuration validation test failed: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Configuration validation test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_message_creation():
    """Test email message creation."""
    print("Testing email message creation...")
    
    try:
        config = {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'smtp_username': 'test@example.com',
            'smtp_password': 'password',
            'use_ssl': True,
            'from_email': 'test@example.com'
        }
        
        sender = SecureEmailSender(config)
        
        # Create a message
        msg = sender._create_message(
            recipient='recipient@example.com',
            subject='Test Subject',
            body='Test Body'
        )
        
        assert msg['From'] == 'test@example.com', "From address should match config"
        assert msg['To'] == 'recipient@example.com', "To address should match parameter"
        assert msg['Subject'] == 'Test Subject', "Subject should match parameter"
        
        print("  ✅ Message creation tests passed")
        return True
        
    except AssertionError as e:
        print(f"  ❌ Message creation test failed: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Message creation test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_file_attachment():
    """Test file attachment functionality."""
    print("Testing file attachment...")
    
    try:
        config = {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'smtp_username': 'test@example.com',
            'smtp_password': 'password',
            'use_ssl': True,
            'from_email': 'test@example.com'
        }
        
        sender = SecureEmailSender(config)
        
        # Create a message
        msg = sender._create_message(
            recipient='recipient@example.com',
            subject='Test Subject',
            body='Test Body'
        )
        
        # Create a test PDF buffer
        pdf_buffer = io.BytesIO(b'%PDF-1.4\nTest PDF content')
        
        # Attach file
        sender._attach_file(msg, pdf_buffer, 'test.pdf', 'application/pdf')
        
        # Check that attachment was added
        assert len(msg.get_payload()) > 1, "Message should have attachment"
        
        print("  ✅ File attachment tests passed")
        return True
        
    except AssertionError as e:
        print(f"  ❌ File attachment test failed: {e}")
        return False
    except Exception as e:
        print(f"  ❌ File attachment test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_connection_with_real_config():
    """Test connection with real config from config.json."""
    print("Testing connection with real config...")
    
    try:
        # Load configuration
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        email_config = config.get('email_config', {})
        
        if not email_config:
            print("  ⚠️  No email_config found - skipping test")
            return True
        
        # Create sender
        sender = SecureEmailSender(email_config)
        
        # Test connection
        results = sender.test_connection()
        
        assert 'connection' in results, "Results should contain connection status"
        assert results['connection'] in ['success', 'failed'], \
            "Connection status should be success or failed"
        
        if results['connection'] == 'success':
            print(f"  ✅ Connection test passed: {results['message']}")
        else:
            print(f"  ⚠️  Connection test failed (expected): {results['message']}")
        
        return True
        
    except FileNotFoundError:
        print("  ⚠️  config.json not found - skipping test")
        return True
    except Exception as e:
        print(f"  ❌ Connection test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_error_handling():
    """Test error handling."""
    print("Testing error handling...")
    
    try:
        # Test with invalid SMTP server
        config = {
            'smtp_server': 'invalid.smtp.server.example.com',
            'smtp_port': 587,
            'smtp_username': 'test@example.com',
            'smtp_password': 'password',
            'use_ssl': True,
            'from_email': 'test@example.com'
        }
        
        sender = SecureEmailSender(config)
        
        # Test connection should fail gracefully
        results = sender.test_connection(timeout=5)
        
        assert results['connection'] == 'failed', "Connection should fail with invalid server"
        assert 'message' in results, "Results should contain error message"
        
        print("  ✅ Error handling tests passed")
        return True
        
    except AssertionError as e:
        print(f"  ❌ Error handling test failed: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Error handling test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("🧪 Running Email Utils Tests\n")
    print("=" * 60)
    
    tests = [
        ("SecureEmailSender Initialization", test_secure_email_sender_init),
        ("Configuration Validation", test_config_validation),
        ("Message Creation", test_message_creation),
        ("File Attachment", test_file_attachment),
        ("Connection with Real Config", test_connection_with_real_config),
        ("Error Handling", test_error_handling),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"  ❌ {test_name} failed with exception: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All email utils tests passed!")
        return 0
    else:
        print(f"⚠️  {total - passed} test(s) failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
