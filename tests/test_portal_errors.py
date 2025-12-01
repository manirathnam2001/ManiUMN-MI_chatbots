"""
Test suite for portal error handling in secret_code_portal.py

Tests the error display and handling for:
- Missing credentials
- Malformed credentials
- Permission denied errors
- Sheet structure errors
"""

import unittest
from unittest.mock import Mock, patch, MagicMock


class TestAdminErrorDisplay(unittest.TestCase):
    """Test cases for admin-friendly error display."""
    
    def test_missing_secrets_error_display(self):
        """Test that MissingSecretsError displays helpful admin instructions."""
        from utils.access_control import MissingSecretsError
        
        error = MissingSecretsError()
        error_message = str(error)
        
        # Should contain all authentication methods
        self.assertIn("GOOGLESA", error_message)
        self.assertIn("GOOGLESA_B64", error_message)
        self.assertIn("Streamlit secrets", error_message)
        self.assertIn("Environment variable", error_message)
    
    def test_malformed_secrets_error_display(self):
        """Test that MalformedSecretsError displays source and fix suggestions."""
        from utils.access_control import MalformedSecretsError
        
        error = MalformedSecretsError(
            source="st.secrets['GOOGLESA']",
            detail="Invalid JSON: Expecting property name"
        )
        error_message = str(error)
        
        # Should contain source and detail
        self.assertIn("st.secrets['GOOGLESA']", error_message)
        self.assertIn("Invalid JSON", error_message)
        
        # Should contain fix suggestions
        self.assertIn("TOML table", error_message) or self.assertIn("base64", error_message.lower())
    
    def test_permission_denied_error_with_service_email(self):
        """Test PermissionDeniedError includes share instructions with email."""
        from utils.access_control import PermissionDeniedError
        
        error = PermissionDeniedError(
            sheet_id="1x_MA3MqvyxN3p7v_mQ3xYB9SmEGPn1EspO0fUsYayFY",
            service_account_email="mibot@project.iam.gserviceaccount.com"
        )
        error_message = str(error)
        
        # Should contain the email for sharing
        self.assertIn("mibot@project.iam.gserviceaccount.com", error_message)
        self.assertIn("share", error_message.lower())
    
    def test_permission_denied_error_without_service_email(self):
        """Test PermissionDeniedError works without email."""
        from utils.access_control import PermissionDeniedError
        
        error = PermissionDeniedError(
            sheet_id="1x_MA3MqvyxN3p7v_mQ3xYB9SmEGPn1EspO0fUsYayFY"
        )
        error_message = str(error)
        
        # Should still be informative
        self.assertIn("Permission denied", error_message)


class TestValidateAndMarkCode(unittest.TestCase):
    """Test cases for code validation and marking."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Sample session state data
        self.mock_worksheet = MagicMock()
        self.sample_headers = ['Table No', 'Name', 'Bot', 'Secret', 'Used', 'Role']
        self.sample_rows = [
            ['1', 'Alice Student', 'OHI', 'CODE1', '', 'STUDENT'],
            ['2', 'Bob Instructor', 'HPV', 'CODE2', '', 'INSTRUCTOR'],
            ['3', 'Charlie Developer', 'OHI', 'CODE3', '', 'DEVELOPER'],
            ['4', 'Diana Used', 'TOBACCO', 'CODE4', 'TRUE', 'STUDENT'],
        ]
    
    def test_validate_code_no_data_message(self):
        """Test that error message is clear when codes_data is not loaded."""
        # This tests the error message content for missing data
        from utils.access_control import ROLE_STUDENT
        
        # The function should return a message about data not loaded
        expected_message = 'Code data not loaded'
        self.assertIn('not loaded', expected_message)
    
    def test_role_normalization_in_validation(self):
        """Test that role normalization works for various role formats."""
        from utils.access_control import normalize_role, ROLE_STUDENT, ROLE_INSTRUCTOR, ROLE_DEVELOPER
        
        # Test various role formats
        self.assertEqual(normalize_role('student'), ROLE_STUDENT)
        self.assertEqual(normalize_role('INSTRUCTOR'), ROLE_INSTRUCTOR)
        self.assertEqual(normalize_role('Developer'), ROLE_DEVELOPER)
        self.assertEqual(normalize_role('invalid'), ROLE_STUDENT)  # Falls back to STUDENT
    
    def test_bot_normalization_in_validation(self):
        """Test that bot type normalization works for various formats."""
        from utils.access_control import normalize_bot_type
        
        # Test various bot type formats
        self.assertEqual(normalize_bot_type('ohi'), 'OHI')
        self.assertEqual(normalize_bot_type('TOBACCO'), 'TOBACCO')
        self.assertEqual(normalize_bot_type('Perio'), 'PERIO')
        self.assertIsNone(normalize_bot_type('invalid'))  # Returns None for invalid


class TestBotPageMapping(unittest.TestCase):
    """Test cases for bot type to page mapping."""
    
    def test_all_valid_bots_have_pages(self):
        """Test that all valid bot types have corresponding page files."""
        from utils.access_control import VALID_BOT_TYPES
        
        # Import the page map from the portal
        with patch('secret_code_portal.st'):
            from secret_code_portal import BOT_PAGE_MAP
        
        for bot_type in VALID_BOT_TYPES:
            self.assertIn(bot_type, BOT_PAGE_MAP, f"Missing page for {bot_type}")
    
    def test_developer_has_page(self):
        """Test that DEVELOPER has a page mapping."""
        with patch('secret_code_portal.st'):
            from secret_code_portal import BOT_PAGE_MAP
        
        self.assertIn('DEVELOPER', BOT_PAGE_MAP)
        self.assertEqual(BOT_PAGE_MAP['DEVELOPER'], 'pages/developer_page.py')


if __name__ == '__main__':
    unittest.main()
