"""
Test suite for utils/access_control.py

Tests the access control module including:
- gspread client construction with version compatibility
- Role and bot type normalization
- Credential parsing from various sources
- Error handling with admin-friendly messages
"""

import unittest
import os
import json
import base64
import tempfile
from unittest.mock import Mock, patch, MagicMock


class TestRoleNormalization(unittest.TestCase):
    """Test cases for role normalization."""
    
    def test_normalize_role_student(self):
        """Test normalizing student role."""
        from utils.access_control import normalize_role, ROLE_STUDENT
        
        self.assertEqual(normalize_role('student'), ROLE_STUDENT)
        self.assertEqual(normalize_role('STUDENT'), ROLE_STUDENT)
        self.assertEqual(normalize_role('  Student  '), ROLE_STUDENT)
    
    def test_normalize_role_instructor(self):
        """Test normalizing instructor role."""
        from utils.access_control import normalize_role, ROLE_INSTRUCTOR
        
        self.assertEqual(normalize_role('instructor'), ROLE_INSTRUCTOR)
        self.assertEqual(normalize_role('INSTRUCTOR'), ROLE_INSTRUCTOR)
        self.assertEqual(normalize_role('  Instructor  '), ROLE_INSTRUCTOR)
    
    def test_normalize_role_developer(self):
        """Test normalizing developer role."""
        from utils.access_control import normalize_role, ROLE_DEVELOPER
        
        self.assertEqual(normalize_role('developer'), ROLE_DEVELOPER)
        self.assertEqual(normalize_role('DEVELOPER'), ROLE_DEVELOPER)
        self.assertEqual(normalize_role('  Developer  '), ROLE_DEVELOPER)
    
    def test_normalize_role_invalid(self):
        """Test normalizing invalid role returns STUDENT."""
        from utils.access_control import normalize_role, ROLE_STUDENT
        
        self.assertEqual(normalize_role('admin'), ROLE_STUDENT)
        self.assertEqual(normalize_role(''), ROLE_STUDENT)
        self.assertEqual(normalize_role(None), ROLE_STUDENT)


class TestBotTypeNormalization(unittest.TestCase):
    """Test cases for bot type normalization."""
    
    def test_normalize_bot_type_ohi(self):
        """Test normalizing OHI bot type."""
        from utils.access_control import normalize_bot_type
        
        self.assertEqual(normalize_bot_type('ohi'), 'OHI')
        self.assertEqual(normalize_bot_type('OHI'), 'OHI')
        self.assertEqual(normalize_bot_type('  Ohi  '), 'OHI')
    
    def test_normalize_bot_type_hpv(self):
        """Test normalizing HPV bot type."""
        from utils.access_control import normalize_bot_type
        
        self.assertEqual(normalize_bot_type('hpv'), 'HPV')
        self.assertEqual(normalize_bot_type('HPV'), 'HPV')
        self.assertEqual(normalize_bot_type('  Hpv  '), 'HPV')
    
    def test_normalize_bot_type_tobacco(self):
        """Test normalizing Tobacco bot type."""
        from utils.access_control import normalize_bot_type
        
        self.assertEqual(normalize_bot_type('tobacco'), 'TOBACCO')
        self.assertEqual(normalize_bot_type('TOBACCO'), 'TOBACCO')
        self.assertEqual(normalize_bot_type('  Tobacco  '), 'TOBACCO')
    
    def test_normalize_bot_type_perio(self):
        """Test normalizing Perio bot type."""
        from utils.access_control import normalize_bot_type
        
        self.assertEqual(normalize_bot_type('perio'), 'PERIO')
        self.assertEqual(normalize_bot_type('PERIO'), 'PERIO')
        self.assertEqual(normalize_bot_type('  Perio  '), 'PERIO')
    
    def test_normalize_bot_type_invalid(self):
        """Test normalizing invalid bot type returns None."""
        from utils.access_control import normalize_bot_type
        
        self.assertIsNone(normalize_bot_type('unknown'))
        self.assertIsNone(normalize_bot_type(''))
        self.assertIsNone(normalize_bot_type(None))


class TestCredentialParsing(unittest.TestCase):
    """Test cases for credential parsing from various sources."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Sample service account credentials (fake, for testing only)
        self.test_creds = {
            "type": "service_account",
            "project_id": "test-project",
            "private_key_id": "test-key-id",
            "private_key": "-----BEGIN PRIVATE KEY-----\ntest-key\n-----END PRIVATE KEY-----\n",
            "client_email": "test@test.iam.gserviceaccount.com",
            "client_id": "12345",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token"
        }
        
        # Save original environment variables
        self.original_env = {}
        for var in ['GOOGLESA', 'GOOGLESA_B64']:
            self.original_env[var] = os.environ.get(var)
            if var in os.environ:
                del os.environ[var]
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Restore original environment variables
        for var, value in self.original_env.items():
            if value is None:
                if var in os.environ:
                    del os.environ[var]
            else:
                os.environ[var] = value
    
    def test_parse_credentials_from_env_b64(self):
        """Test parsing credentials from GOOGLESA_B64 environment variable."""
        from utils.access_control import _parse_credentials_from_env
        
        # Encode credentials as base64
        json_str = json.dumps(self.test_creds)
        b64_str = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
        os.environ['GOOGLESA_B64'] = b64_str
        
        creds_dict, source = _parse_credentials_from_env()
        
        self.assertIsNotNone(creds_dict)
        self.assertEqual(creds_dict['project_id'], 'test-project')
        self.assertEqual(source, "Environment variable (GOOGLESA_B64)")
    
    def test_parse_credentials_from_env_json(self):
        """Test parsing credentials from GOOGLESA environment variable."""
        from utils.access_control import _parse_credentials_from_env
        
        json_str = json.dumps(self.test_creds)
        os.environ['GOOGLESA'] = json_str
        
        creds_dict, source = _parse_credentials_from_env()
        
        self.assertIsNotNone(creds_dict)
        self.assertEqual(creds_dict['project_id'], 'test-project')
        self.assertEqual(source, "Environment variable (GOOGLESA)")
    
    def test_parse_credentials_from_env_invalid_b64(self):
        """Test that invalid base64 raises MalformedSecretsError."""
        from utils.access_control import _parse_credentials_from_env, MalformedSecretsError
        
        os.environ['GOOGLESA_B64'] = "not-valid-base64!!!"
        
        with self.assertRaises(MalformedSecretsError) as context:
            _parse_credentials_from_env()
        
        self.assertIn("Invalid base64", str(context.exception))
    
    def test_parse_credentials_from_env_invalid_json(self):
        """Test that invalid JSON raises MalformedSecretsError."""
        from utils.access_control import _parse_credentials_from_env, MalformedSecretsError
        
        os.environ['GOOGLESA'] = "not valid json"
        
        with self.assertRaises(MalformedSecretsError) as context:
            _parse_credentials_from_env()
        
        self.assertIn("Invalid JSON", str(context.exception))
    
    def test_parse_credentials_from_file(self):
        """Test parsing credentials from service account file."""
        from utils.access_control import _parse_credentials_from_file
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.test_creds, f)
            temp_file = f.name
        
        try:
            # Patch SERVICE_ACCOUNT_FILE to use our temp file
            with patch('utils.access_control.SERVICE_ACCOUNT_FILE', temp_file):
                creds_dict, source = _parse_credentials_from_file()
            
            self.assertIsNotNone(creds_dict)
            self.assertEqual(creds_dict['project_id'], 'test-project')
            self.assertIn("Service account file", source)
        finally:
            os.unlink(temp_file)
    
    def test_parse_credentials_from_file_not_found(self):
        """Test that missing file returns None."""
        from utils.access_control import _parse_credentials_from_file
        
        with patch('utils.access_control.SERVICE_ACCOUNT_FILE', '/nonexistent/file.json'):
            creds_dict, source = _parse_credentials_from_file()
        
        self.assertIsNone(creds_dict)
        self.assertIsNone(source)


class TestServiceAccountEmail(unittest.TestCase):
    """Test cases for extracting service account email."""
    
    def test_get_service_account_email(self):
        """Test extracting service account email from credentials."""
        from utils.access_control import get_service_account_email
        
        creds = {'client_email': 'test@test.iam.gserviceaccount.com'}
        self.assertEqual(
            get_service_account_email(creds),
            'test@test.iam.gserviceaccount.com'
        )
    
    def test_get_service_account_email_missing(self):
        """Test extracting email when key is missing."""
        from utils.access_control import get_service_account_email
        
        creds = {'project_id': 'test-project'}
        self.assertIsNone(get_service_account_email(creds))


class TestSheetClientCreation(unittest.TestCase):
    """Test cases for gspread client creation with version compatibility."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_creds = {
            "type": "service_account",
            "project_id": "test-project",
            "private_key_id": "test-key-id",
            "private_key": "-----BEGIN PRIVATE KEY-----\ntest-key\n-----END PRIVATE KEY-----\n",
            "client_email": "test@test.iam.gserviceaccount.com",
            "client_id": "12345",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token"
        }
        
        # Clear environment variables
        for var in ['GOOGLESA', 'GOOGLESA_B64']:
            if var in os.environ:
                del os.environ[var]
    
    def test_client_creation_with_service_account_from_dict(self):
        """Test client creation using gspread.service_account_from_dict."""
        from utils.access_control import get_sheet_client
        import gspread
        
        json_str = json.dumps(self.test_creds)
        b64_str = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
        os.environ['GOOGLESA_B64'] = b64_str
        
        with patch.object(gspread, 'service_account_from_dict') as mock_sa_from_dict:
            mock_client = MagicMock()
            mock_sa_from_dict.return_value = mock_client
            
            client, source, email = get_sheet_client()
            
            self.assertEqual(client, mock_client)
            mock_sa_from_dict.assert_called_once()
    
    def test_client_creation_fallback_to_authorize(self):
        """Test client creation falling back to gspread.authorize."""
        from utils.access_control import get_sheet_client
        import gspread
        from google.oauth2.service_account import Credentials
        
        json_str = json.dumps(self.test_creds)
        b64_str = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
        os.environ['GOOGLESA_B64'] = b64_str
        
        # Simulate service_account_from_dict not available
        with patch.object(gspread, 'service_account_from_dict', side_effect=AttributeError()), \
             patch.object(Credentials, 'from_service_account_info') as mock_creds_info, \
             patch.object(gspread, 'authorize') as mock_authorize:
            
            mock_creds = MagicMock()
            mock_creds_info.return_value = mock_creds
            mock_client = MagicMock()
            mock_authorize.return_value = mock_client
            
            client, source, email = get_sheet_client()
            
            self.assertEqual(client, mock_client)
            mock_creds_info.assert_called_once()
            mock_authorize.assert_called_once_with(mock_creds)
    
    def test_client_creation_no_credentials(self):
        """Test client creation with no credentials raises MissingSecretsError."""
        from utils.access_control import MissingSecretsError
        
        # Clear all credential sources
        for var in ['GOOGLESA', 'GOOGLESA_B64']:
            if var in os.environ:
                del os.environ[var]
        
        # Need to reload the module to pick up our patched SERVICE_ACCOUNT_FILE
        import utils.access_control as ac
        original_file = ac.SERVICE_ACCOUNT_FILE
        try:
            ac.SERVICE_ACCOUNT_FILE = '/nonexistent/file.json'
            with self.assertRaises(MissingSecretsError):
                ac.get_sheet_client()
        finally:
            ac.SERVICE_ACCOUNT_FILE = original_file


class TestExceptions(unittest.TestCase):
    """Test cases for custom exceptions."""
    
    def test_missing_secrets_error_message(self):
        """Test MissingSecretsError contains helpful message."""
        from utils.access_control import MissingSecretsError
        
        error = MissingSecretsError()
        
        self.assertIn("No Google Sheets credentials found", str(error))
        self.assertIn("st.secrets['GOOGLESA']", str(error))
        self.assertIn("GOOGLESA_B64", str(error))
    
    def test_malformed_secrets_error_message(self):
        """Test MalformedSecretsError contains source and detail."""
        from utils.access_control import MalformedSecretsError
        
        error = MalformedSecretsError(
            source="GOOGLESA_B64 environment variable",
            detail="Invalid base64 encoding"
        )
        
        self.assertIn("Malformed credentials", str(error))
        self.assertIn("GOOGLESA_B64 environment variable", str(error))
        self.assertIn("Invalid base64 encoding", str(error))
    
    def test_permission_denied_error_with_email(self):
        """Test PermissionDeniedError includes share instructions."""
        from utils.access_control import PermissionDeniedError
        
        error = PermissionDeniedError(
            sheet_id="test-sheet-id",
            service_account_email="test@test.iam.gserviceaccount.com"
        )
        
        self.assertIn("Permission denied", str(error))
        self.assertIn("test@test.iam.gserviceaccount.com", str(error))
        self.assertIn("share the spreadsheet", str(error).lower())


if __name__ == '__main__':
    unittest.main()
