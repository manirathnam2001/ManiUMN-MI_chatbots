#!/usr/bin/env python3
"""
Test suite for email_utils.py

Tests the secure email sending functionality including:
- Configuration loading from multiple sources
- Environment variable support
- Secure SMTP connection
- Error handling
- Connection testing
"""

import os
import sys
import io
import json
import unittest
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from email_utils import (
    SecureEmailSender, 
    EmailConfigError, 
    EmailSendError,
    send_box_upload_email
)


class TestSecureEmailSender(unittest.TestCase):
    """Test cases for SecureEmailSender class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_config = {
            'email_config': {
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'smtp_use_ssl': True,
                'smtp_username': 'test@example.com',
                'smtp_app_password': 'test_password',
                'ohi_box_email': 'ohi@box.com',
                'hpv_box_email': 'hpv@box.com'
            },
            'email': {
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'sender_email': 'legacy@example.com',
                'sender_password': 'legacy_password',
                'use_tls': True
            },
            'box_upload': {
                'ohi_email': 'ohi@box.com',
                'hpv_email': 'hpv@box.com'
            }
        }
    
    def test_initialization(self):
        """Test SecureEmailSender initialization."""
        sender = SecureEmailSender(self.test_config)
        self.assertIsNotNone(sender)
        self.assertEqual(sender.config, self.test_config)
        self.assertIsNotNone(sender.logger)
    
    def test_initialization_without_config(self):
        """Test initialization without config uses defaults."""
        sender = SecureEmailSender()
        self.assertIsNotNone(sender)
        self.assertEqual(sender.config, {})
    
    def test_get_smtp_credentials_from_config(self):
        """Test getting SMTP credentials from config."""
        sender = SecureEmailSender(self.test_config)
        credentials = sender.get_smtp_credentials()
        
        self.assertEqual(credentials['username'], 'test@example.com')
        self.assertEqual(credentials['password'], 'test_password')
    
    def test_get_smtp_credentials_from_legacy_config(self):
        """Test getting SMTP credentials from legacy email config."""
        config = {
            'email': {
                'sender_email': 'legacy@example.com',
                'sender_password': 'legacy_password'
            }
        }
        sender = SecureEmailSender(config)
        credentials = sender.get_smtp_credentials()
        
        self.assertEqual(credentials['username'], 'legacy@example.com')
        self.assertEqual(credentials['password'], 'legacy_password')
    
    @patch.dict(os.environ, {
        'SMTP_USERNAME': 'env@example.com',
        'SMTP_APP_PASSWORD': 'env_password'
    })
    def test_get_smtp_credentials_from_env(self):
        """Test that environment variables take priority."""
        sender = SecureEmailSender(self.test_config)
        credentials = sender.get_smtp_credentials()
        
        # Env vars should take priority over config
        self.assertEqual(credentials['username'], 'env@example.com')
        self.assertEqual(credentials['password'], 'env_password')
    
    def test_get_smtp_credentials_missing(self):
        """Test error when credentials are missing."""
        sender = SecureEmailSender({})
        
        with self.assertRaises(EmailConfigError):
            sender.get_smtp_credentials()
    
    def test_get_smtp_settings_from_config(self):
        """Test getting SMTP settings from config."""
        sender = SecureEmailSender(self.test_config)
        settings = sender.get_smtp_settings()
        
        self.assertEqual(settings['smtp_server'], 'smtp.gmail.com')
        self.assertEqual(settings['smtp_port'], 587)
        self.assertTrue(settings['use_ssl'])
    
    def test_get_smtp_settings_defaults(self):
        """Test default SMTP settings."""
        sender = SecureEmailSender({})
        settings = sender.get_smtp_settings()
        
        self.assertEqual(settings['smtp_server'], 'smtp.gmail.com')
        self.assertEqual(settings['smtp_port'], 587)
        self.assertTrue(settings['use_ssl'])
    
    @patch.dict(os.environ, {
        'SMTP_SERVER': 'smtp.custom.com',
        'SMTP_PORT': '465',
        'SMTP_USE_SSL': 'false'
    })
    def test_get_smtp_settings_from_env(self):
        """Test SMTP settings from environment variables."""
        sender = SecureEmailSender({})
        settings = sender.get_smtp_settings()
        
        self.assertEqual(settings['smtp_server'], 'smtp.custom.com')
        self.assertEqual(settings['smtp_port'], 465)
        self.assertFalse(settings['use_ssl'])
    
    @patch('email_utils.smtplib.SMTP')
    def test_send_email_with_attachment_success(self, mock_smtp):
        """Test successful email sending with attachment."""
        # Mock SMTP server
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        sender = SecureEmailSender(self.test_config)
        pdf_buffer = io.BytesIO(b'%PDF-1.4 test content')
        
        result = sender.send_email_with_attachment(
            recipient='test@box.com',
            subject='Test Subject',
            body='Test Body',
            attachment_buffer=pdf_buffer,
            attachment_filename='test.pdf'
        )
        
        self.assertTrue(result)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once()
        mock_server.send_message.assert_called_once()
    
    @patch('email_utils.smtplib.SMTP')
    def test_send_email_authentication_error(self, mock_smtp):
        """Test email sending with authentication error."""
        import smtplib
        
        # Mock SMTP server to raise authentication error
        mock_server = MagicMock()
        mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, 'Invalid credentials')
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        sender = SecureEmailSender(self.test_config)
        pdf_buffer = io.BytesIO(b'%PDF-1.4 test content')
        
        with self.assertRaises(EmailSendError):
            sender.send_email_with_attachment(
                recipient='test@box.com',
                subject='Test Subject',
                body='Test Body',
                attachment_buffer=pdf_buffer,
                attachment_filename='test.pdf'
            )
    
    @patch('email_utils.smtplib.SMTP')
    def test_test_connection_success(self, mock_smtp):
        """Test successful connection test."""
        # Mock SMTP server
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        sender = SecureEmailSender(self.test_config)
        result = sender.test_connection()
        
        self.assertEqual(result['status'], 'success')
        self.assertTrue(result['authentication'])
        self.assertIn('successful', result['message'].lower())
    
    @patch('email_utils.smtplib.SMTP')
    def test_test_connection_auth_failure(self, mock_smtp):
        """Test connection test with authentication failure."""
        import smtplib
        
        # Mock SMTP server to raise authentication error
        mock_server = MagicMock()
        mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, 'Invalid credentials')
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        sender = SecureEmailSender(self.test_config)
        result = sender.test_connection()
        
        self.assertEqual(result['status'], 'auth_failed')
        self.assertFalse(result['authentication'])
    
    def test_test_connection_config_error(self):
        """Test connection test with missing configuration."""
        sender = SecureEmailSender({})
        result = sender.test_connection()
        
        self.assertEqual(result['status'], 'config_error')


class TestSendBoxUploadEmail(unittest.TestCase):
    """Test cases for send_box_upload_email convenience function."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_config = {
            'email_config': {
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'smtp_use_ssl': True,
                'smtp_username': 'test@example.com',
                'smtp_app_password': 'test_password',
                'ohi_box_email': 'ohi@box.com',
                'hpv_box_email': 'hpv@box.com'
            },
            'box_upload': {
                'ohi_email': 'ohi@box.com',
                'hpv_email': 'hpv@box.com'
            }
        }
    
    @patch('email_utils.SecureEmailSender.send_email_with_attachment')
    def test_send_box_upload_email_ohi(self, mock_send):
        """Test sending Box upload email for OHI bot."""
        mock_send.return_value = True
        
        pdf_buffer = io.BytesIO(b'%PDF-1.4 test content')
        result = send_box_upload_email(
            config=self.test_config,
            bot_type='OHI',
            student_name='John Doe',
            pdf_buffer=pdf_buffer,
            filename='test.pdf'
        )
        
        self.assertTrue(result)
        mock_send.assert_called_once()
        
        # Check that correct recipient was used
        call_args = mock_send.call_args
        self.assertEqual(call_args[1]['recipient'], 'ohi@box.com')
    
    @patch('email_utils.SecureEmailSender.send_email_with_attachment')
    def test_send_box_upload_email_hpv(self, mock_send):
        """Test sending Box upload email for HPV bot."""
        mock_send.return_value = True
        
        pdf_buffer = io.BytesIO(b'%PDF-1.4 test content')
        result = send_box_upload_email(
            config=self.test_config,
            bot_type='HPV',
            student_name='Jane Smith',
            pdf_buffer=pdf_buffer,
            filename='test.pdf'
        )
        
        self.assertTrue(result)
        
        # Check that correct recipient was used
        call_args = mock_send.call_args
        self.assertEqual(call_args[1]['recipient'], 'hpv@box.com')
    
    def test_send_box_upload_email_invalid_bot_type(self):
        """Test error with invalid bot type."""
        pdf_buffer = io.BytesIO(b'%PDF-1.4 test content')
        
        with self.assertRaises(ValueError):
            send_box_upload_email(
                config=self.test_config,
                bot_type='INVALID',
                student_name='John Doe',
                pdf_buffer=pdf_buffer,
                filename='test.pdf'
            )
    
    def test_send_box_upload_email_missing_config(self):
        """Test error with missing Box email configuration."""
        config = {
            'email_config': {
                'smtp_server': 'smtp.gmail.com',
                'smtp_username': 'test@example.com',
                'smtp_app_password': 'test_password'
            }
        }
        
        pdf_buffer = io.BytesIO(b'%PDF-1.4 test content')
        
        with self.assertRaises(EmailConfigError):
            send_box_upload_email(
                config=config,
                bot_type='OHI',
                student_name='John Doe',
                pdf_buffer=pdf_buffer,
                filename='test.pdf'
            )


def run_tests():
    """Run all tests."""
    print("🧪 Running Email Utils Tests\n")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestSecureEmailSender))
    suite.addTests(loader.loadTestsFromTestCase(TestSendBoxUploadEmail))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {result.testsRun} tests")
    print(f"✅ Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    if result.failures:
        print(f"❌ Failed: {len(result.failures)}")
    if result.errors:
        print(f"💥 Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n🎉 All email utils tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed!")
        return 1


if __name__ == '__main__':
    sys.exit(run_tests())
