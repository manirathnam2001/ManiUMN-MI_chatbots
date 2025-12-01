"""
Test suite for utils/access_control.py

Tests the robust Google Sheets client creation and error handling:
- Multiple authentication methods
- gspread version compatibility
- Clear error messages for various failure scenarios
- Retry logic with exponential backoff
"""

import unittest
import os
import json
import base64
from unittest.mock import Mock, patch, MagicMock, PropertyMock
import sys

# Add the parent directory to sys.path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.access_control import (
    get_sheet_client,
    open_sheet_with_retry,
    get_sheet_data_with_retry,
    update_cell_with_retry,
    CredentialError,
    SheetAccessError,
    NetworkError,
    _decode_credentials,
    _get_service_account_email,
)


class TestDecodeCredentials(unittest.TestCase):
    """Test cases for the _decode_credentials helper function."""
    
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
    
    def test_decode_json_string(self):
        """Test decoding a valid JSON string."""
        json_str = json.dumps(self.test_creds)
        result = _decode_credentials("test_source", json_str, is_base64=False)
        self.assertEqual(result, self.test_creds)
    
    def test_decode_base64_json(self):
        """Test decoding valid base64-encoded JSON."""
        json_str = json.dumps(self.test_creds)
        b64_str = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
        result = _decode_credentials("test_source", b64_str, is_base64=True)
        self.assertEqual(result, self.test_creds)
    
    def test_decode_invalid_json(self):
        """Test error handling for invalid JSON."""
        with self.assertRaises(CredentialError) as context:
            _decode_credentials("test_source", "not valid json", is_base64=False)
        self.assertIn("not valid JSON", context.exception.admin_hint)
    
    def test_decode_invalid_base64(self):
        """Test error handling for invalid base64."""
        with self.assertRaises(CredentialError) as context:
            _decode_credentials("test_source", "not-valid-base64!!!", is_base64=True)
        self.assertIn("not valid base64", context.exception.admin_hint)
    
    def test_decode_base64_invalid_json(self):
        """Test error handling for valid base64 but invalid JSON content."""
        invalid_json = "not valid json"
        b64_str = base64.b64encode(invalid_json.encode('utf-8')).decode('utf-8')
        with self.assertRaises(CredentialError) as context:
            _decode_credentials("test_source", b64_str, is_base64=True)
        self.assertIn("not valid JSON", context.exception.admin_hint)


class TestGetServiceAccountEmail(unittest.TestCase):
    """Test cases for _get_service_account_email helper."""
    
    def test_extract_email(self):
        """Test extracting email from credentials dict."""
        creds = {"client_email": "test@test.iam.gserviceaccount.com"}
        result = _get_service_account_email(creds)
        self.assertEqual(result, "test@test.iam.gserviceaccount.com")
    
    def test_missing_email(self):
        """Test handling missing email field."""
        creds = {"type": "service_account"}
        result = _get_service_account_email(creds)
        self.assertIsNone(result)


class TestGetSheetClient(unittest.TestCase):
    """Test cases for get_sheet_client function."""
    
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
        
        # Save original environment variables
        self.original_env = {}
        for var in ['GOOGLESA', 'GOOGLESA_B64']:
            self.original_env[var] = os.environ.get(var)
            if var in os.environ:
                del os.environ[var]
    
    def tearDown(self):
        """Clean up test fixtures."""
        for var, value in self.original_env.items():
            if value is None:
                if var in os.environ:
                    del os.environ[var]
            else:
                os.environ[var] = value
    
    def test_streamlit_secrets_toml_table(self):
        """Test authentication with Streamlit secrets as TOML table."""
        mock_secrets = {"GOOGLESA": self.test_creds}
        
        with patch('utils.access_control.gspread') as mock_gspread:
            mock_client = MagicMock()
            mock_gspread.service_account_from_dict.return_value = mock_client
            
            client, source, email = get_sheet_client(streamlit_secrets=mock_secrets)
            
            self.assertEqual(client, mock_client)
            self.assertEqual(source, "Streamlit secrets (TOML table)")
            self.assertEqual(email, "test@test.iam.gserviceaccount.com")
    
    def test_streamlit_secrets_json_string(self):
        """Test authentication with Streamlit secrets as JSON string."""
        json_str = json.dumps(self.test_creds)
        mock_secrets = {"GOOGLESA": json_str}
        
        with patch('utils.access_control.gspread') as mock_gspread:
            mock_client = MagicMock()
            mock_gspread.service_account_from_dict.return_value = mock_client
            
            client, source, email = get_sheet_client(streamlit_secrets=mock_secrets)
            
            self.assertEqual(client, mock_client)
            self.assertEqual(source, "Streamlit secrets (JSON string)")
    
    def test_streamlit_secrets_b64(self):
        """Test authentication with Streamlit secrets GOOGLESA_B64."""
        json_str = json.dumps(self.test_creds)
        b64_str = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
        mock_secrets = {"GOOGLESA_B64": b64_str}
        
        with patch('utils.access_control.gspread') as mock_gspread:
            mock_client = MagicMock()
            mock_gspread.service_account_from_dict.return_value = mock_client
            
            client, source, email = get_sheet_client(streamlit_secrets=mock_secrets)
            
            self.assertEqual(client, mock_client)
            self.assertEqual(source, "Streamlit secrets (GOOGLESA_B64)")
    
    def test_env_var_b64(self):
        """Test authentication with GOOGLESA_B64 environment variable."""
        json_str = json.dumps(self.test_creds)
        b64_str = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
        os.environ['GOOGLESA_B64'] = b64_str
        
        with patch('utils.access_control.gspread') as mock_gspread:
            mock_client = MagicMock()
            mock_gspread.service_account_from_dict.return_value = mock_client
            
            client, source, email = get_sheet_client(streamlit_secrets={})
            
            self.assertEqual(client, mock_client)
            self.assertEqual(source, "Environment variable (GOOGLESA_B64)")
    
    def test_env_var_json(self):
        """Test authentication with GOOGLESA environment variable."""
        json_str = json.dumps(self.test_creds)
        os.environ['GOOGLESA'] = json_str
        
        with patch('utils.access_control.gspread') as mock_gspread:
            mock_client = MagicMock()
            mock_gspread.service_account_from_dict.return_value = mock_client
            
            client, source, email = get_sheet_client(streamlit_secrets={})
            
            self.assertEqual(client, mock_client)
            self.assertEqual(source, "Environment variable (GOOGLESA)")
    
    def test_no_credentials_error(self):
        """Test error when no credentials are available."""
        with patch('utils.access_control.os.path.exists', return_value=False):
            with self.assertRaises(CredentialError) as context:
                get_sheet_client(streamlit_secrets={})
            
            self.assertIn("No Google service account credentials found", str(context.exception))
            self.assertIn("GOOGLESA", context.exception.admin_hint)
            self.assertIn("GOOGLESA_B64", context.exception.admin_hint)
    
    def test_priority_order_secrets_over_env(self):
        """Test that Streamlit secrets take priority over environment variables."""
        json_str = json.dumps(self.test_creds)
        os.environ['GOOGLESA'] = json_str
        mock_secrets = {"GOOGLESA": self.test_creds}
        
        with patch('utils.access_control.gspread') as mock_gspread:
            mock_client = MagicMock()
            mock_gspread.service_account_from_dict.return_value = mock_client
            
            client, source, email = get_sheet_client(streamlit_secrets=mock_secrets)
            
            # Should use Streamlit secrets, not env var
            self.assertEqual(source, "Streamlit secrets (TOML table)")
    
    def test_fallback_to_authorize_when_service_account_from_dict_missing(self):
        """Test fallback to gspread.authorize when service_account_from_dict is unavailable."""
        mock_secrets = {"GOOGLESA": self.test_creds}
        
        with patch('utils.access_control.gspread') as mock_gspread:
            # Remove service_account_from_dict to simulate older gspread
            del mock_gspread.service_account_from_dict
            mock_gspread.service_account_from_dict = None
            mock_client = MagicMock()
            mock_gspread.authorize.return_value = mock_client
            
            with patch('utils.access_control.hasattr', side_effect=lambda obj, name: name != 'service_account_from_dict'):
                with patch('google.oauth2.service_account.Credentials') as mock_creds:
                    mock_creds_instance = MagicMock()
                    mock_creds.from_service_account_info.return_value = mock_creds_instance
                    
                    client, source, email = get_sheet_client(streamlit_secrets=mock_secrets)
                    
                    mock_gspread.authorize.assert_called_once_with(mock_creds_instance)


class TestOpenSheetWithRetry(unittest.TestCase):
    """Test cases for open_sheet_with_retry function."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_client = MagicMock()
        self.mock_sheet = MagicMock()
        self.mock_worksheet = MagicMock()
        self.mock_client.open_by_key.return_value = self.mock_sheet
        self.mock_sheet.worksheet.return_value = self.mock_worksheet
    
    def test_successful_open(self):
        """Test successful sheet opening."""
        result = open_sheet_with_retry(
            self.mock_client, "test-sheet-id", "Sheet1"
        )
        self.assertEqual(result, self.mock_worksheet)
    
    def test_spreadsheet_not_found(self):
        """Test handling of spreadsheet not found error."""
        import gspread.exceptions
        self.mock_client.open_by_key.side_effect = gspread.exceptions.SpreadsheetNotFound()
        
        with self.assertRaises(SheetAccessError) as context:
            open_sheet_with_retry(self.mock_client, "test-sheet-id", "Sheet1")
        
        self.assertIn("not found", str(context.exception).lower())
    
    def test_worksheet_not_found(self):
        """Test handling of worksheet not found error."""
        import gspread.exceptions
        self.mock_sheet.worksheet.side_effect = gspread.exceptions.WorksheetNotFound()
        
        with self.assertRaises(SheetAccessError) as context:
            open_sheet_with_retry(self.mock_client, "test-sheet-id", "Sheet1")
        
        self.assertIn("worksheet", str(context.exception).lower())
    
    def test_permission_denied(self):
        """Test handling of permission denied error."""
        import gspread.exceptions
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.json.return_value = {"error": {"message": "Permission denied", "code": 403}}
        error = gspread.exceptions.APIError(mock_response)
        # Set the code attribute directly to match the response
        error.code = 403
        self.mock_client.open_by_key.side_effect = error
        
        with self.assertRaises(SheetAccessError) as context:
            open_sheet_with_retry(
                self.mock_client, "test-sheet-id", "Sheet1",
                service_account_email="test@test.iam.gserviceaccount.com",
                max_retries=0  # Skip retries for test speed
            )
        
        self.assertIn("permission", context.exception.admin_hint.lower())
        self.assertEqual(context.exception.service_account_email, "test@test.iam.gserviceaccount.com")


class TestUpdateCellWithRetry(unittest.TestCase):
    """Test cases for update_cell_with_retry function."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_worksheet = MagicMock()
    
    def test_successful_update(self):
        """Test successful cell update."""
        result = update_cell_with_retry(self.mock_worksheet, 1, 1, "test")
        self.assertTrue(result)
        self.mock_worksheet.update_cell.assert_called_once_with(1, 1, "test")
    
    def test_permission_denied(self):
        """Test handling of permission denied on update."""
        import gspread.exceptions
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.json.return_value = {"error": {"message": "Permission denied", "code": 403}}
        error = gspread.exceptions.APIError(mock_response)
        error.code = 403
        self.mock_worksheet.update_cell.side_effect = error
        
        with self.assertRaises(SheetAccessError) as context:
            update_cell_with_retry(self.mock_worksheet, 1, 1, "test", max_retries=0)
        
        self.assertIn("permission", context.exception.admin_hint.lower())


class TestErrorClasses(unittest.TestCase):
    """Test cases for custom exception classes."""
    
    def test_credential_error(self):
        """Test CredentialError exception."""
        error = CredentialError("Test error", admin_hint="Test hint")
        self.assertEqual(str(error), "Test error")
        self.assertEqual(error.admin_hint, "Test hint")
    
    def test_credential_error_default_hint(self):
        """Test CredentialError with default admin_hint."""
        error = CredentialError("Test error")
        self.assertEqual(error.admin_hint, "Test error")
    
    def test_sheet_access_error(self):
        """Test SheetAccessError exception."""
        error = SheetAccessError(
            "Test error",
            admin_hint="Test hint",
            service_account_email="test@test.com"
        )
        self.assertEqual(str(error), "Test error")
        self.assertEqual(error.admin_hint, "Test hint")
        self.assertEqual(error.service_account_email, "test@test.com")
    
    def test_network_error(self):
        """Test NetworkError exception."""
        error = NetworkError("Network failed")
        self.assertEqual(str(error), "Network failed")


if __name__ == '__main__':
    unittest.main()
