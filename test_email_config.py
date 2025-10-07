"""
Test suite for email_config.py module

Tests the secure email configuration and credential handling.
"""

import unittest
import os
import json
import tempfile
from email_config import EmailConfig, EmailConfigError


class TestEmailConfig(unittest.TestCase):
    """Test cases for EmailConfig class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary config file
        self.temp_config = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.config_data = {
            "email_config": {
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "smtp_ssl": True,
                "smtp_user": "test@example.com",
                "smtp_password": "PLACEHOLDER",
                "ohi_box_email": "ohi@box.com",
                "hpv_box_email": "hpv@box.com"
            }
        }
        json.dump(self.config_data, self.temp_config)
        self.temp_config.close()
        
        # Save original environment
        self.original_env = os.environ.get('SMTP_PASSWORD')
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Remove temporary config file
        if os.path.exists(self.temp_config.name):
            os.unlink(self.temp_config.name)
        
        # Restore original environment
        if self.original_env:
            os.environ['SMTP_PASSWORD'] = self.original_env
        elif 'SMTP_PASSWORD' in os.environ:
            del os.environ['SMTP_PASSWORD']
    
    def test_load_config(self):
        """Test configuration loading."""
        email_config = EmailConfig(self.temp_config.name)
        self.assertEqual(email_config.config['smtp_server'], 'smtp.gmail.com')
        self.assertEqual(email_config.config['smtp_port'], 587)
        self.assertEqual(email_config.config['smtp_user'], 'test@example.com')
    
    def test_missing_config_file(self):
        """Test handling of missing configuration file."""
        with self.assertRaises(EmailConfigError):
            EmailConfig('nonexistent_config.json')
    
    def test_get_box_email_ohi(self):
        """Test retrieving OHI Box email."""
        email_config = EmailConfig(self.temp_config.name)
        ohi_email = email_config.get_box_email('OHI')
        self.assertEqual(ohi_email, 'ohi@box.com')
    
    def test_get_box_email_hpv(self):
        """Test retrieving HPV Box email."""
        email_config = EmailConfig(self.temp_config.name)
        hpv_email = email_config.get_box_email('HPV')
        self.assertEqual(hpv_email, 'hpv@box.com')
    
    def test_get_box_email_invalid_type(self):
        """Test handling of invalid bot type."""
        email_config = EmailConfig(self.temp_config.name)
        with self.assertRaises(EmailConfigError):
            email_config.get_box_email('INVALID')
    
    def test_get_smtp_password_set(self):
        """Test retrieving SMTP password from environment."""
        os.environ['SMTP_PASSWORD'] = 'test_password_123'
        email_config = EmailConfig(self.temp_config.name)
        password = email_config.get_smtp_password()
        self.assertEqual(password, 'test_password_123')
    
    def test_get_smtp_password_not_set(self):
        """Test handling of missing SMTP password."""
        if 'SMTP_PASSWORD' in os.environ:
            del os.environ['SMTP_PASSWORD']
        email_config = EmailConfig(self.temp_config.name)
        with self.assertRaises(EmailConfigError):
            email_config.get_smtp_password()
    
    def test_get_smtp_config(self):
        """Test retrieving complete SMTP configuration."""
        os.environ['SMTP_PASSWORD'] = 'test_password_123'
        email_config = EmailConfig(self.temp_config.name)
        smtp_config = email_config.get_smtp_config()
        
        self.assertEqual(smtp_config['smtp_server'], 'smtp.gmail.com')
        self.assertEqual(smtp_config['smtp_port'], 587)
        self.assertEqual(smtp_config['smtp_user'], 'test@example.com')
        self.assertEqual(smtp_config['smtp_password'], 'test_password_123')
        self.assertEqual(smtp_config['smtp_ssl'], True)
    
    def test_missing_email_config_section(self):
        """Test handling of missing email_config section."""
        # Create config without email_config section
        temp_config = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        json.dump({"other_section": {}}, temp_config)
        temp_config.close()
        
        try:
            with self.assertRaises(EmailConfigError):
                EmailConfig(temp_config.name)
        finally:
            os.unlink(temp_config.name)
    
    def test_ssl_default_value(self):
        """Test SSL default value."""
        # Create config without smtp_ssl
        config_no_ssl = {
            "email_config": {
                "smtp_server": "smtp.example.com",
                "smtp_port": 587,
                "smtp_user": "user@example.com",
                "smtp_password": "PLACEHOLDER"
            }
        }
        temp_config = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        json.dump(config_no_ssl, temp_config)
        temp_config.close()
        
        try:
            os.environ['SMTP_PASSWORD'] = 'test_password'
            email_config = EmailConfig(temp_config.name)
            smtp_config = email_config.get_smtp_config()
            self.assertEqual(smtp_config['smtp_ssl'], True)  # Default should be True
        finally:
            os.unlink(temp_config.name)


class TestEmailConfigIntegration(unittest.TestCase):
    """Integration tests with actual config.json."""
    
    def test_load_actual_config(self):
        """Test loading actual config.json if it exists."""
        if not os.path.exists('config.json'):
            self.skipTest('config.json not found')
        
        try:
            email_config = EmailConfig('config.json')
            self.assertIsNotNone(email_config.config)
            self.assertIn('smtp_server', email_config.config)
            self.assertIn('smtp_port', email_config.config)
            self.assertIn('smtp_user', email_config.config)
        except EmailConfigError as e:
            self.fail(f"Failed to load config.json: {e}")
    
    def test_box_emails_configured(self):
        """Test that Box email addresses are configured."""
        if not os.path.exists('config.json'):
            self.skipTest('config.json not found')
        
        email_config = EmailConfig('config.json')
        
        # Check OHI email
        try:
            ohi_email = email_config.get_box_email('OHI')
            self.assertTrue('@' in ohi_email)
        except EmailConfigError:
            self.fail('OHI Box email not configured')
        
        # Check HPV email
        try:
            hpv_email = email_config.get_box_email('HPV')
            self.assertTrue('@' in hpv_email)
        except EmailConfigError:
            self.fail('HPV Box email not configured')


def run_tests():
    """Run all tests and print results."""
    print("🧪 Running Email Configuration Tests\n")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestEmailConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestEmailConfigIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {result.testsRun - len(result.failures) - len(result.errors)}/{result.testsRun} tests passed")
    
    if result.wasSuccessful():
        print("🎉 All email configuration tests passed!")
        return 0
    else:
        if result.failures:
            print(f"⚠️  {len(result.failures)} test(s) failed.")
        if result.errors:
            print(f"❌ {len(result.errors)} test(s) had errors.")
        return 1


if __name__ == '__main__':
    exit(run_tests())
