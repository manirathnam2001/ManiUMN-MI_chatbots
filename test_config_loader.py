"""
Test suite for config_loader.py
"""

import unittest
import os
import json
import tempfile
import shutil
from config_loader import ConfigLoader


class TestConfigLoader(unittest.TestCase):
    """Test cases for ConfigLoader class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory
        self.test_dir = tempfile.mkdtemp()
        
        # Create a test config file
        self.config_path = os.path.join(self.test_dir, 'test_config.json')
        self.test_config = {
            "box_upload": {
                "enabled": False
            },
            "email_config": {
                "smtp_server": "smtp.test.com",
                "smtp_port": 587,
                "smtp_use_ssl": True,
                "smtp_username": "test@test.com",
                "smtp_app_password": "test_password",
                "ohi_box_email": "ohi_test@box.com",
                "hpv_box_email": "hpv_test@box.com"
            },
            "logging": {
                "log_level": "INFO"
            }
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(self.test_config, f)
        
        # Save original environment variables
        self.original_env = {}
        env_vars = ['GROQ_API_KEY', 'SMTP_USERNAME', 'SMTP_APP_PASSWORD',
                   'OHI_BOX_EMAIL', 'HPV_BOX_EMAIL', 'SMTP_SERVER', 'SMTP_PORT']
        for var in env_vars:
            self.original_env[var] = os.environ.get(var)
            if var in os.environ:
                del os.environ[var]
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Restore original environment variables
        for var, value in self.original_env.items():
            if value is not None:
                os.environ[var] = value
            elif var in os.environ:
                del os.environ[var]
        
        # Remove temporary directory
        shutil.rmtree(self.test_dir)
    
    def test_initialization(self):
        """Test ConfigLoader initialization."""
        loader = ConfigLoader(self.config_path, load_dotenv_file=False)
        self.assertIsNotNone(loader)
        self.assertEqual(loader.config_path, self.config_path)
    
    def test_load_config_file(self):
        """Test loading configuration from file."""
        loader = ConfigLoader(self.config_path, load_dotenv_file=False)
        self.assertEqual(loader.config, self.test_config)
    
    def test_get_groq_api_key_from_env(self):
        """Test getting GROQ API key from environment variable."""
        os.environ['GROQ_API_KEY'] = 'test_groq_key'
        loader = ConfigLoader(self.config_path, load_dotenv_file=False)
        api_key = loader.get_groq_api_key()
        self.assertEqual(api_key, 'test_groq_key')
    
    def test_get_groq_api_key_not_set(self):
        """Test getting GROQ API key when not set."""
        loader = ConfigLoader(self.config_path, load_dotenv_file=False)
        api_key = loader.get_groq_api_key()
        self.assertIsNone(api_key)
    
    def test_get_smtp_config_from_env(self):
        """Test getting SMTP config from environment variables."""
        os.environ['SMTP_USERNAME'] = 'env_user@test.com'
        os.environ['SMTP_APP_PASSWORD'] = 'env_password'
        os.environ['SMTP_SERVER'] = 'smtp.env.com'
        os.environ['SMTP_PORT'] = '465'
        
        loader = ConfigLoader(self.config_path, load_dotenv_file=False)
        smtp_config = loader.get_smtp_config()
        
        self.assertEqual(smtp_config['smtp_username'], 'env_user@test.com')
        self.assertEqual(smtp_config['smtp_app_password'], 'env_password')
        self.assertEqual(smtp_config['smtp_server'], 'smtp.env.com')
        self.assertEqual(smtp_config['smtp_port'], 465)
    
    def test_get_smtp_config_from_file(self):
        """Test getting SMTP config from config file."""
        loader = ConfigLoader(self.config_path, load_dotenv_file=False)
        smtp_config = loader.get_smtp_config()
        
        # Should get defaults since env vars not set
        self.assertEqual(smtp_config['smtp_server'], 'smtp.gmail.com')
        self.assertEqual(smtp_config['smtp_port'], 587)
    
    def test_get_box_email_from_env(self):
        """Test getting Box email from environment variables."""
        os.environ['OHI_BOX_EMAIL'] = 'env_ohi@box.com'
        os.environ['HPV_BOX_EMAIL'] = 'env_hpv@box.com'
        
        loader = ConfigLoader(self.config_path, load_dotenv_file=False)
        
        ohi_email = loader.get_box_email('OHI')
        hpv_email = loader.get_box_email('HPV')
        
        self.assertEqual(ohi_email, 'env_ohi@box.com')
        self.assertEqual(hpv_email, 'env_hpv@box.com')
    
    def test_get_box_email_from_config(self):
        """Test getting Box email from config file."""
        loader = ConfigLoader(self.config_path, load_dotenv_file=False)
        
        ohi_email = loader.get_box_email('OHI')
        hpv_email = loader.get_box_email('HPV')
        
        self.assertEqual(ohi_email, 'ohi_test@box.com')
        self.assertEqual(hpv_email, 'hpv_test@box.com')
    
    def test_get_box_email_invalid_type(self):
        """Test error with invalid bot type."""
        loader = ConfigLoader(self.config_path, load_dotenv_file=False)
        
        with self.assertRaises(ValueError):
            loader.get_box_email('INVALID')
    
    def test_validate_required_env_vars(self):
        """Test validation of required environment variables."""
        os.environ['GROQ_API_KEY'] = 'test_key'
        # SMTP_USERNAME not set
        
        loader = ConfigLoader(self.config_path, load_dotenv_file=False)
        validation = loader.validate_required_env_vars(['GROQ_API_KEY', 'SMTP_USERNAME'])
        
        self.assertTrue(validation['GROQ_API_KEY'])
        self.assertFalse(validation['SMTP_USERNAME'])
    
    def test_get_missing_env_vars(self):
        """Test getting list of missing environment variables."""
        os.environ['GROQ_API_KEY'] = 'test_key'
        # SMTP_USERNAME and SMTP_APP_PASSWORD not set
        
        loader = ConfigLoader(self.config_path, load_dotenv_file=False)
        missing = loader.get_missing_env_vars(['GROQ_API_KEY', 'SMTP_USERNAME', 'SMTP_APP_PASSWORD'])
        
        self.assertIn('SMTP_USERNAME', missing)
        self.assertIn('SMTP_APP_PASSWORD', missing)
        self.assertNotIn('GROQ_API_KEY', missing)
    
    def test_config_file_not_found(self):
        """Test handling of missing config file."""
        loader = ConfigLoader('/nonexistent/config.json', load_dotenv_file=False)
        self.assertEqual(loader.config, {})
    
    def test_get_config(self):
        """Test getting full configuration dictionary."""
        loader = ConfigLoader(self.config_path, load_dotenv_file=False)
        config = loader.get_config()
        self.assertEqual(config, self.test_config)


if __name__ == '__main__':
    print("🧪 Running Config Loader Tests\n")
    print("=" * 60)
    
    # Run tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestConfigLoader)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {result.testsRun} tests")
    if result.wasSuccessful():
        print(f"✅ Passed: {result.testsRun}")
        print("\n🎉 All config loader tests passed!")
    else:
        print(f"✅ Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
        print(f"❌ Failed: {len(result.failures)}")
        print(f"⚠️  Errors: {len(result.errors)}")
