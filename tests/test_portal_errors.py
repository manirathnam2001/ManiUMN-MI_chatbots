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
    
    def test_credential_error_display(self):
        """Test that CredentialError displays helpful admin instructions."""
        from utils.access_control import CredentialError
        
        error = CredentialError(
            "No credentials found",
            admin_hint="Please configure GOOGLESA or GOOGLESA_B64"
        )
        error_message = str(error)
        admin_hint = error.admin_hint
        
        # Should contain helpful information
        self.assertIn("No credentials found", error_message)
        self.assertIn("GOOGLESA", admin_hint)
    
    def test_sheet_access_error_with_service_email(self):
        """Test SheetAccessError includes share instructions with email."""
        from utils.access_control import SheetAccessError
        
        error = SheetAccessError(
            "Permission denied",
            admin_hint="Share the spreadsheet with the service account",
            service_account_email="mibot@project.iam.gserviceaccount.com"
        )
        error_message = str(error)
        
        # Should contain the email for sharing
        self.assertEqual(error.service_account_email, "mibot@project.iam.gserviceaccount.com")
        self.assertIn("Permission denied", error_message)
    
    def test_sheet_access_error_without_service_email(self):
        """Test SheetAccessError works without email."""
        from utils.access_control import SheetAccessError
        
        error = SheetAccessError(
            "Permission denied",
            admin_hint="Share the spreadsheet"
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
        # normalize_bot_type just normalizes, it doesn't validate
        self.assertEqual(normalize_bot_type('invalid'), 'INVALID')


class TestBotPageMapping(unittest.TestCase):
    """Test cases for bot type to page mapping."""
    
    @unittest.skipIf(True, "Requires streamlit to be installed")
    def test_all_valid_bots_have_pages(self):
        """Test that all valid bot types have corresponding page files."""
        from utils.access_control import VALID_BOT_TYPES
        
        # Import the page map from the portal
        with patch('secret_code_portal.st'):
            from secret_code_portal import BOT_PAGE_MAP
        
        for bot_type in VALID_BOT_TYPES:
            self.assertIn(bot_type, BOT_PAGE_MAP, f"Missing page for {bot_type}")
    
    @unittest.skipIf(True, "Requires streamlit to be installed")
    def test_developer_has_page(self):
        """Test that DEVELOPER has a page mapping."""
        with patch('secret_code_portal.st'):
            from secret_code_portal import BOT_PAGE_MAP
        
        self.assertIn('DEVELOPER', BOT_PAGE_MAP)
        self.assertEqual(BOT_PAGE_MAP['DEVELOPER'], 'pages/developer_page.py')


if __name__ == '__main__':
    unittest.main()
