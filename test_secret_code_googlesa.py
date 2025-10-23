"""
Test suite for Google Sheets authentication in secret_code_portal.py

Tests the enhanced credential loading with support for:
- st.secrets as TOML table or JSON string
- GOOGLESA_B64 environment variable (base64-encoded JSON)
- GOOGLESA environment variable (JSON string)
- Service account file fallback
"""

import unittest
import os
import json
import base64
import tempfile
import sys
from unittest.mock import Mock, patch, MagicMock


class TestGoogleSheetsAuthentication(unittest.TestCase):
    """Test cases for Google Sheets authentication methods."""
    
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
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/test%40test.iam.gserviceaccount.com"
        }
        
        # Save original environment variables
        self.original_env = {}
        for var in ['GOOGLESA', 'GOOGLESA_B64']:
            self.original_env[var] = os.environ.get(var)
            if var in os.environ:
                del os.environ[var]
        
        # Create a temporary service account file
        self.temp_dir = tempfile.mkdtemp()
        self.service_account_file = os.path.join(self.temp_dir, 'test-service-account.json')
        with open(self.service_account_file, 'w') as f:
            json.dump(self.test_creds, f)
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Restore original environment variables
        for var, value in self.original_env.items():
            if value is None:
                if var in os.environ:
                    del os.environ[var]
            else:
                os.environ[var] = value
        
        # Clean up temporary files
        if os.path.exists(self.service_account_file):
            os.remove(self.service_account_file)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)
    
    def test_googlesa_b64_valid(self):
        """Test GOOGLESA_B64 with valid base64-encoded JSON."""
        # Encode the test credentials as base64
        json_str = json.dumps(self.test_creds)
        b64_str = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
        
        # Set the environment variable
        os.environ['GOOGLESA_B64'] = b64_str
        
        # Import and test (mocking Streamlit and gspread)
        with patch('secret_code_portal.st') as mock_st, \
             patch('secret_code_portal.gspread') as mock_gspread, \
             patch('secret_code_portal.Credentials') as mock_creds:
            
            # Configure mocks
            mock_st.secrets = {}
            mock_st.session_state = {}
            mock_creds_instance = MagicMock()
            mock_creds.from_service_account_info.return_value = mock_creds_instance
            mock_client = MagicMock()
            mock_gspread.authorize.return_value = mock_client
            
            # Import the function
            from secret_code_portal import get_google_sheets_client
            
            # Call the function
            client = get_google_sheets_client()
            
            # Verify
            self.assertEqual(client, mock_client)
            mock_creds.from_service_account_info.assert_called_once()
            self.assertEqual(mock_st.session_state["googlesa_source"], "Environment variable (GOOGLESA_B64)")
    
    def test_googlesa_b64_invalid_base64(self):
        """Test GOOGLESA_B64 with invalid base64."""
        # Set invalid base64
        os.environ['GOOGLESA_B64'] = "not-valid-base64!!!"
        
        with patch('secret_code_portal.st') as mock_st, \
             patch('secret_code_portal.gspread') as mock_gspread:
            
            mock_st.secrets = {}
            mock_st.session_state = {}
            
            from secret_code_portal import get_google_sheets_client
            
            # Should raise an exception about invalid base64
            with self.assertRaises(Exception) as context:
                get_google_sheets_client()
            
            self.assertIn("Failed to decode GOOGLESA_B64", str(context.exception))
    
    def test_googlesa_b64_invalid_json(self):
        """Test GOOGLESA_B64 with valid base64 but invalid JSON."""
        # Encode invalid JSON as base64
        invalid_json = "not valid json"
        b64_str = base64.b64encode(invalid_json.encode('utf-8')).decode('utf-8')
        os.environ['GOOGLESA_B64'] = b64_str
        
        with patch('secret_code_portal.st') as mock_st, \
             patch('secret_code_portal.gspread') as mock_gspread:
            
            mock_st.secrets = {}
            mock_st.session_state = {}
            
            from secret_code_portal import get_google_sheets_client
            
            # Should raise an exception about invalid JSON
            with self.assertRaises(Exception) as context:
                get_google_sheets_client()
            
            self.assertIn("Failed to parse decoded GOOGLESA_B64 as JSON", str(context.exception))
    
    def test_googlesa_json_valid(self):
        """Test GOOGLESA with valid JSON string."""
        json_str = json.dumps(self.test_creds)
        os.environ['GOOGLESA'] = json_str
        
        with patch('secret_code_portal.st') as mock_st, \
             patch('secret_code_portal.gspread') as mock_gspread, \
             patch('secret_code_portal.Credentials') as mock_creds:
            
            mock_st.secrets = {}
            mock_st.session_state = {}
            mock_creds_instance = MagicMock()
            mock_creds.from_service_account_info.return_value = mock_creds_instance
            mock_client = MagicMock()
            mock_gspread.authorize.return_value = mock_client
            
            from secret_code_portal import get_google_sheets_client
            
            client = get_google_sheets_client()
            
            self.assertEqual(client, mock_client)
            self.assertEqual(mock_st.session_state["googlesa_source"], "Environment variable (GOOGLESA)")
    
    def test_googlesa_json_invalid_with_newlines(self):
        """Test GOOGLESA with unescaped newlines (common error case)."""
        # Simulate the problem: JSON with actual newlines instead of \n
        invalid_json = '{"type": "service_account", "private_key": "-----BEGIN PRIVATE KEY-----\nactual newline here\n-----END PRIVATE KEY-----\n"}'
        os.environ['GOOGLESA'] = invalid_json
        
        with patch('secret_code_portal.st') as mock_st, \
             patch('secret_code_portal.gspread') as mock_gspread:
            
            mock_st.secrets = {}
            mock_st.session_state = {}
            
            from secret_code_portal import get_google_sheets_client
            
            # Should raise an exception with helpful guidance
            with self.assertRaises(Exception) as context:
                get_google_sheets_client()
            
            error_msg = str(context.exception)
            self.assertIn("Failed to parse GOOGLESA environment variable as JSON", error_msg)
            self.assertIn("Use Streamlit secrets", error_msg)
            self.assertIn("Use GOOGLESA_B64", error_msg)
    
    def test_streamlit_secrets_toml_table(self):
        """Test st.secrets with TOML table format (mapping)."""
        with patch('secret_code_portal.st') as mock_st, \
             patch('secret_code_portal.gspread') as mock_gspread, \
             patch('secret_code_portal.Credentials') as mock_creds:
            
            # Mock st.secrets as a mapping (TOML table)
            mock_secrets_mapping = MagicMock()
            mock_secrets_mapping.__contains__ = lambda self, key: key == "GOOGLESA"
            mock_secrets_mapping.__getitem__ = lambda self, key: self.test_creds if key == "GOOGLESA" else None
            mock_secrets_mapping.test_creds = self.test_creds
            mock_st.secrets = {"GOOGLESA": mock_secrets_mapping.test_creds}
            mock_st.session_state = {}
            
            mock_creds_instance = MagicMock()
            mock_creds.from_service_account_info.return_value = mock_creds_instance
            mock_client = MagicMock()
            mock_gspread.authorize.return_value = mock_client
            
            from secret_code_portal import get_google_sheets_client
            
            client = get_google_sheets_client()
            
            self.assertEqual(client, mock_client)
            self.assertEqual(mock_st.session_state["googlesa_source"], "Streamlit secrets (TOML table)")
    
    def test_streamlit_secrets_json_string(self):
        """Test st.secrets with JSON string format."""
        json_str = json.dumps(self.test_creds)
        
        with patch('secret_code_portal.st') as mock_st, \
             patch('secret_code_portal.gspread') as mock_gspread, \
             patch('secret_code_portal.Credentials') as mock_creds:
            
            # Mock st.secrets as a string (JSON)
            mock_st.secrets = {"GOOGLESA": json_str}
            mock_st.session_state = {}
            
            mock_creds_instance = MagicMock()
            mock_creds.from_service_account_info.return_value = mock_creds_instance
            mock_client = MagicMock()
            mock_gspread.authorize.return_value = mock_client
            
            from secret_code_portal import get_google_sheets_client
            
            client = get_google_sheets_client()
            
            self.assertEqual(client, mock_client)
            self.assertEqual(mock_st.session_state["googlesa_source"], "Streamlit secrets (JSON string)")
    
    def test_streamlit_secrets_invalid_json_string(self):
        """Test st.secrets with invalid JSON string format."""
        invalid_json = "not valid json"
        
        with patch('secret_code_portal.st') as mock_st, \
             patch('secret_code_portal.gspread') as mock_gspread:
            
            mock_st.secrets = {"GOOGLESA": invalid_json}
            mock_st.session_state = {}
            
            from secret_code_portal import get_google_sheets_client
            
            # Should raise an exception about invalid JSON
            with self.assertRaises(Exception) as context:
                get_google_sheets_client()
            
            error_msg = str(context.exception)
            self.assertIn("Failed to parse st.secrets['GOOGLESA'] as JSON", error_msg)
            self.assertIn("ensure it's valid JSON", error_msg)
    
    def test_priority_order(self):
        """Test that credential sources are tried in correct priority order."""
        # Set both GOOGLESA and GOOGLESA_B64
        json_str = json.dumps(self.test_creds)
        b64_str = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
        
        os.environ['GOOGLESA'] = json_str
        os.environ['GOOGLESA_B64'] = b64_str
        
        with patch('secret_code_portal.st') as mock_st, \
             patch('secret_code_portal.gspread') as mock_gspread, \
             patch('secret_code_portal.Credentials') as mock_creds:
            
            # Set st.secrets (highest priority)
            mock_st.secrets = {"GOOGLESA": self.test_creds}
            mock_st.session_state = {}
            
            mock_creds_instance = MagicMock()
            mock_creds.from_service_account_info.return_value = mock_creds_instance
            mock_client = MagicMock()
            mock_gspread.authorize.return_value = mock_client
            
            from secret_code_portal import get_google_sheets_client
            
            client = get_google_sheets_client()
            
            # Should use st.secrets (highest priority)
            self.assertEqual(mock_st.session_state["googlesa_source"], "Streamlit secrets (TOML table)")
    
    def test_no_credentials_error(self):
        """Test error message when no credentials are available."""
        with patch('secret_code_portal.st') as mock_st, \
             patch('secret_code_portal.gspread') as mock_gspread, \
             patch('secret_code_portal.os.path.exists') as mock_exists:
            
            mock_st.secrets = {}
            mock_st.session_state = {}
            mock_exists.return_value = False  # No file exists
            
            from secret_code_portal import get_google_sheets_client
            
            # Should raise FileNotFoundError with all methods listed
            with self.assertRaises(Exception) as context:
                get_google_sheets_client()
            
            error_msg = str(context.exception)
            self.assertIn("No credentials found", error_msg)
            self.assertIn("st.secrets['GOOGLESA']", error_msg)
            self.assertIn("GOOGLESA_B64", error_msg)
            self.assertIn("GOOGLESA", error_msg)


if __name__ == '__main__':
    unittest.main()
