"""
Access Control Utilities for MI Chatbots

This module provides robust Google Sheets client creation and management
for the secret code portal and access control functionality.

Features:
- Multiple authentication method support (Streamlit secrets, env vars, file)
- gspread version compatibility (uses service_account_from_dict when available)
- Clear, actionable error messages for admins
- Automatic retry with exponential backoff for transient errors
"""

import os
import json
import base64
import logging
import time
from typing import Optional, Dict, Any, Tuple

import gspread

logger = logging.getLogger(__name__)


class AccessControlError(Exception):
    """Base exception for access control errors."""
    pass


class CredentialError(AccessControlError):
    """Exception raised when credentials are missing or malformed."""
    
    def __init__(self, message: str, admin_hint: str = None):
        super().__init__(message)
        self.admin_hint = admin_hint or message


class SheetAccessError(AccessControlError):
    """Exception raised when sheet access fails (permissions, not found, etc.)."""
    
    def __init__(self, message: str, admin_hint: str = None, service_account_email: str = None):
        super().__init__(message)
        self.admin_hint = admin_hint or message
        self.service_account_email = service_account_email


class NetworkError(AccessControlError):
    """Exception raised for transient network errors."""
    pass


def _decode_credentials(source_name: str, value: str, is_base64: bool = False) -> Dict[str, Any]:
    """
    Decode credential value to a dictionary.
    
    Args:
        source_name: Name of the credential source (for error messages)
        value: The raw credential value (JSON string or base64-encoded JSON)
        is_base64: Whether the value is base64-encoded
        
    Returns:
        Dictionary containing service account credentials
        
    Raises:
        CredentialError: If decoding fails
    """
    try:
        if is_base64:
            try:
                decoded = base64.b64decode(value).decode('utf-8')
            except (base64.binascii.Error, UnicodeDecodeError) as e:
                raise CredentialError(
                    f"Failed to decode {source_name}: {str(e)}",
                    admin_hint=f"The value in {source_name} is not valid base64. "
                               f"To encode your service account JSON, run:\n\n"
                               f"    cat service-account.json | base64 -w 0\n\n"
                               f"Then paste the output as the value for {source_name}."
                )
            value = decoded
        
        try:
            creds_dict = json.loads(value)
        except json.JSONDecodeError as e:
            hint = (
                f"The value in {source_name} is not valid JSON. "
                f"Error: {str(e)}\n\n"
            )
            if not is_base64:
                hint += (
                    "If your JSON contains special characters, consider using base64 encoding:\n"
                    "  1. Set GOOGLESA_B64 instead of GOOGLESA\n"
                    "  2. Encode with: cat service-account.json | base64 -w 0\n"
                )
            raise CredentialError(
                f"Failed to parse {source_name} as JSON: {str(e)}",
                admin_hint=hint
            )
        
        return creds_dict
        
    except CredentialError:
        raise
    except Exception as e:
        raise CredentialError(
            f"Unexpected error processing {source_name}: {str(e)}",
            admin_hint=f"Please verify that {source_name} contains valid service account credentials."
        )


def _get_service_account_email(creds_dict: Dict[str, Any]) -> Optional[str]:
    """Extract service account email from credentials dictionary."""
    return creds_dict.get('client_email')


def get_sheet_client(
    streamlit_secrets: Optional[Any] = None,
    scopes: list = None
) -> Tuple[gspread.Client, str, Optional[str]]:
    """
    Create and return a gspread client using available credentials.
    
    This function tries multiple credential sources in priority order and uses
    the most compatible gspread client creation method available.
    
    Authentication methods (in priority order):
    1. Streamlit secrets: st.secrets["GOOGLESA"] (TOML table or JSON string)
    2. Streamlit secrets: st.secrets["GOOGLESA_B64"] (base64-encoded JSON)
    3. Environment variable: GOOGLESA_B64 (base64-encoded JSON)
    4. Environment variable: GOOGLESA (JSON string)
    5. Service account file: umnsod-mibot-ea3154b145f1.json (for local/dev)
    
    Args:
        streamlit_secrets: Optional st.secrets object. If None, will try to import streamlit.
        scopes: Optional list of OAuth scopes. Defaults to Sheets and Drive access.
        
    Returns:
        Tuple of (gspread.Client, credential_source_name, service_account_email)
        
    Raises:
        CredentialError: If no valid credentials are found or credentials are malformed
    """
    if scopes is None:
        scopes = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
    
    creds_dict = None
    creds_source = None
    service_account_email = None
    service_account_file = "umnsod-mibot-ea3154b145f1.json"
    
    # Get streamlit secrets if not provided
    if streamlit_secrets is None:
        try:
            import streamlit as st
            streamlit_secrets = st.secrets
        except Exception:
            streamlit_secrets = {}
    
    # Method 1: Streamlit secrets GOOGLESA (TOML table or JSON string)
    try:
        if hasattr(streamlit_secrets, '__contains__') and "GOOGLESA" in streamlit_secrets:
            googlesa_secret = streamlit_secrets["GOOGLESA"]
            
            if isinstance(googlesa_secret, str):
                # It's a JSON string
                creds_dict = _decode_credentials("st.secrets['GOOGLESA']", googlesa_secret)
                creds_source = "Streamlit secrets (JSON string)"
            elif hasattr(googlesa_secret, 'keys'):
                # It's a mapping (TOML table)
                creds_dict = dict(googlesa_secret)
                creds_source = "Streamlit secrets (TOML table)"
            else:
                # Try to convert to dict
                try:
                    creds_dict = dict(googlesa_secret)
                    creds_source = "Streamlit secrets (TOML table)"
                except (TypeError, ValueError):
                    pass
    except CredentialError:
        raise
    except Exception as e:
        logger.debug(f"GOOGLESA secret not available: {e}")
    
    # Method 2: Streamlit secrets GOOGLESA_B64 (base64-encoded)
    if creds_dict is None:
        try:
            if hasattr(streamlit_secrets, '__contains__') and "GOOGLESA_B64" in streamlit_secrets:
                b64_value = streamlit_secrets["GOOGLESA_B64"]
                creds_dict = _decode_credentials(
                    "st.secrets['GOOGLESA_B64']", b64_value, is_base64=True
                )
                creds_source = "Streamlit secrets (GOOGLESA_B64)"
        except CredentialError:
            raise
        except Exception as e:
            logger.debug(f"GOOGLESA_B64 secret not available: {e}")
    
    # Method 3: Environment variable GOOGLESA_B64
    if creds_dict is None:
        googlesa_b64 = os.environ.get('GOOGLESA_B64')
        if googlesa_b64:
            creds_dict = _decode_credentials(
                "GOOGLESA_B64 environment variable", googlesa_b64, is_base64=True
            )
            creds_source = "Environment variable (GOOGLESA_B64)"
    
    # Method 4: Environment variable GOOGLESA
    if creds_dict is None:
        googlesa_env = os.environ.get('GOOGLESA')
        if googlesa_env:
            creds_dict = _decode_credentials(
                "GOOGLESA environment variable", googlesa_env
            )
            creds_source = "Environment variable (GOOGLESA)"
    
    # Method 5: Service account file
    if creds_dict is None:
        if os.path.exists(service_account_file):
            try:
                with open(service_account_file, 'r') as f:
                    creds_dict = json.load(f)
                creds_source = f"Service account file ({service_account_file})"
            except json.JSONDecodeError as e:
                raise CredentialError(
                    f"Failed to parse service account file: {str(e)}",
                    admin_hint=f"The file '{service_account_file}' is not valid JSON. "
                               "Please verify it contains valid service account credentials."
                )
            except Exception as e:
                raise CredentialError(
                    f"Failed to read service account file: {str(e)}",
                    admin_hint=f"Could not read '{service_account_file}'. Check file permissions."
                )
    
    # No credentials found
    if creds_dict is None:
        raise CredentialError(
            "No Google service account credentials found.",
            admin_hint=(
                "No credentials found. Please configure one of the following:\n\n"
                "1. Streamlit secrets (recommended for Streamlit Cloud):\n"
                "   - Set st.secrets['GOOGLESA'] as a TOML table or JSON string\n"
                "   - Or set st.secrets['GOOGLESA_B64'] with base64-encoded JSON\n\n"
                "2. Environment variables:\n"
                "   - GOOGLESA_B64 (base64-encoded JSON, recommended)\n"
                "   - GOOGLESA (JSON string)\n\n"
                "3. Service account file:\n"
                f"   - Place '{service_account_file}' in the application directory\n\n"
                "To create base64-encoded credentials:\n"
                "    cat service-account.json | base64 -w 0"
            )
        )
    
    # Extract service account email for error messages
    service_account_email = _get_service_account_email(creds_dict)
    
    # Create gspread client - prefer service_account_from_dict when available
    try:
        if hasattr(gspread, 'service_account_from_dict'):
            # gspread >= 5.0: Use service_account_from_dict
            client = gspread.service_account_from_dict(creds_dict, scopes=scopes)
            logger.debug(f"Created gspread client using service_account_from_dict from {creds_source}")
        else:
            # Fallback for older gspread versions
            from google.oauth2.service_account import Credentials
            creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
            client = gspread.authorize(creds)
            logger.debug(f"Created gspread client using gspread.authorize from {creds_source}")
        
        return client, creds_source, service_account_email
        
    except Exception as e:
        error_msg = str(e).lower()
        
        if 'invalid_grant' in error_msg or 'invalid key' in error_msg:
            raise CredentialError(
                f"Invalid service account credentials: {str(e)}",
                admin_hint=(
                    "The service account credentials appear to be invalid or expired.\n\n"
                    "Please verify:\n"
                    "1. The service account exists in Google Cloud Console\n"
                    "2. The JSON file is the correct, complete service account key\n"
                    "3. The service account has not been deleted or disabled\n\n"
                    f"Service account email: {service_account_email or 'unknown'}"
                )
            )
        else:
            raise CredentialError(
                f"Failed to create Google Sheets client: {str(e)}",
                admin_hint=(
                    f"Could not authenticate with Google Sheets API.\n\n"
                    f"Error: {str(e)}\n\n"
                    f"Credential source: {creds_source}\n"
                    f"Service account: {service_account_email or 'unknown'}"
                )
            )


def open_sheet_with_retry(
    client: gspread.Client,
    sheet_id: str,
    worksheet_name: str = "Sheet1",
    max_retries: int = 3,
    base_delay: float = 1.0,
    service_account_email: str = None
) -> gspread.Worksheet:
    """
    Open a Google Sheet worksheet with retry logic for transient errors.
    
    Args:
        client: gspread.Client instance
        sheet_id: The Google Sheet ID
        worksheet_name: Name of the worksheet to open
        max_retries: Maximum number of retry attempts
        base_delay: Base delay for exponential backoff (seconds)
        service_account_email: Service account email for error messages
        
    Returns:
        gspread.Worksheet instance
        
    Raises:
        SheetAccessError: If the sheet cannot be opened (permissions, not found)
        NetworkError: If a network error persists after retries
    """
    last_error = None
    
    for attempt in range(max_retries + 1):
        try:
            sheet = client.open_by_key(sheet_id)
            worksheet = sheet.worksheet(worksheet_name)
            return worksheet
            
        except gspread.exceptions.SpreadsheetNotFound:
            raise SheetAccessError(
                f"Spreadsheet not found: {sheet_id}",
                admin_hint=(
                    f"The spreadsheet with ID '{sheet_id}' was not found.\n\n"
                    "Please verify:\n"
                    "1. The SHEET_KEY/SHEET_ID is correct\n"
                    "2. The spreadsheet exists and has not been deleted\n"
                    "3. The service account has been granted access to the spreadsheet\n\n"
                    f"To share the sheet, add: {service_account_email or 'your-service-account@project.iam.gserviceaccount.com'}"
                ),
                service_account_email=service_account_email
            )
            
        except gspread.exceptions.WorksheetNotFound:
            raise SheetAccessError(
                f"Worksheet '{worksheet_name}' not found in spreadsheet",
                admin_hint=(
                    f"The worksheet named '{worksheet_name}' was not found in the spreadsheet.\n\n"
                    "Please verify the worksheet name or create it in the spreadsheet."
                ),
                service_account_email=service_account_email
            )
            
        except gspread.exceptions.APIError as e:
            # Get error code from multiple possible sources
            error_code = getattr(e, 'code', None)
            if error_code is None and hasattr(e, 'response') and e.response is not None:
                error_code = getattr(e.response, 'status_code', None)
            error_msg = str(e).lower()
            
            if error_code == 403 or 'permission' in error_msg or 'forbidden' in error_msg:
                raise SheetAccessError(
                    f"Permission denied accessing spreadsheet: {sheet_id}",
                    admin_hint=(
                        f"The service account does not have permission to access this spreadsheet.\n\n"
                        f"To fix this, share the spreadsheet with:\n"
                        f"    {service_account_email or 'your-service-account@project.iam.gserviceaccount.com'}\n\n"
                        "Grant 'Editor' access if the app needs to update values (mark codes as used)."
                    ),
                    service_account_email=service_account_email
                )
            
            elif error_code == 404:
                raise SheetAccessError(
                    f"Spreadsheet not found: {sheet_id}",
                    admin_hint=(
                        f"The spreadsheet with ID '{sheet_id}' was not found.\n\n"
                        "Please verify the SHEET_KEY/SHEET_ID configuration."
                    ),
                    service_account_email=service_account_email
                )
            
            elif error_code == 429 or 'quota' in error_msg or 'rate' in error_msg:
                # Rate limiting - retry with backoff
                last_error = e
                if attempt < max_retries:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"Rate limited, retrying in {delay}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(delay)
                    continue
                raise NetworkError(
                    "Google Sheets API rate limit exceeded. Please try again in a few moments."
                )
            
            else:
                # Other API errors - retry for potentially transient issues
                last_error = e
                if attempt < max_retries:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"API error, retrying in {delay}s: {e}")
                    time.sleep(delay)
                    continue
                raise SheetAccessError(
                    f"Google Sheets API error: {str(e)}",
                    admin_hint=f"An error occurred accessing the spreadsheet: {str(e)}",
                    service_account_email=service_account_email
                )
                
        except Exception as e:
            error_msg = str(e).lower()
            
            # Check for network-related errors
            if any(x in error_msg for x in ['timeout', 'connection', 'network', 'unreachable']):
                last_error = e
                if attempt < max_retries:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"Network error, retrying in {delay}s: {e}")
                    time.sleep(delay)
                    continue
                raise NetworkError(
                    f"Network error accessing Google Sheets: {str(e)}. "
                    "Please check your internet connection and try again."
                )
            
            # Unknown error - don't retry
            raise SheetAccessError(
                f"Error opening spreadsheet: {str(e)}",
                admin_hint=f"An unexpected error occurred: {str(e)}",
                service_account_email=service_account_email
            )
    
    # Should not reach here, but just in case
    raise NetworkError(f"Failed after {max_retries} retries: {last_error}")


def get_sheet_data_with_retry(
    worksheet: gspread.Worksheet,
    max_retries: int = 3,
    base_delay: float = 1.0
) -> list:
    """
    Get all values from a worksheet with retry logic.
    
    Args:
        worksheet: gspread.Worksheet instance
        max_retries: Maximum number of retry attempts
        base_delay: Base delay for exponential backoff (seconds)
        
    Returns:
        List of rows (each row is a list of cell values)
        
    Raises:
        NetworkError: If the request fails after retries
    """
    last_error = None
    
    for attempt in range(max_retries + 1):
        try:
            return worksheet.get_all_values()
            
        except gspread.exceptions.APIError as e:
            error_code = getattr(e, 'code', None) or (e.response.status_code if hasattr(e, 'response') else None)
            
            if error_code == 429:
                last_error = e
                if attempt < max_retries:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"Rate limited, retrying in {delay}s")
                    time.sleep(delay)
                    continue
            
            # Other API errors
            last_error = e
            if attempt < max_retries:
                delay = base_delay * (2 ** attempt)
                time.sleep(delay)
                continue
            
            raise NetworkError(f"Failed to read sheet data: {str(e)}")
            
        except Exception as e:
            last_error = e
            if attempt < max_retries:
                delay = base_delay * (2 ** attempt)
                time.sleep(delay)
                continue
            
            raise NetworkError(f"Failed to read sheet data: {str(e)}")
    
    raise NetworkError(f"Failed after {max_retries} retries: {last_error}")


def update_cell_with_retry(
    worksheet: gspread.Worksheet,
    row: int,
    col: int,
    value: str,
    max_retries: int = 3,
    base_delay: float = 1.0
) -> bool:
    """
    Update a single cell with retry logic.
    
    Args:
        worksheet: gspread.Worksheet instance
        row: Row number (1-indexed)
        col: Column number (1-indexed)
        value: Value to write
        max_retries: Maximum number of retry attempts
        base_delay: Base delay for exponential backoff (seconds)
        
    Returns:
        True if successful
        
    Raises:
        SheetAccessError: If the update fails (permissions, etc.)
        NetworkError: If the request fails after retries
    """
    last_error = None
    
    for attempt in range(max_retries + 1):
        try:
            worksheet.update_cell(row, col, value)
            return True
            
        except gspread.exceptions.APIError as e:
            # Get error code from multiple possible sources
            error_code = getattr(e, 'code', None)
            if error_code is None and hasattr(e, 'response') and e.response is not None:
                error_code = getattr(e.response, 'status_code', None)
            error_msg = str(e).lower()
            
            if error_code == 403 or 'permission' in error_msg or 'forbidden' in error_msg:
                raise SheetAccessError(
                    "Permission denied: Cannot update spreadsheet",
                    admin_hint=(
                        "The service account does not have write permission.\n\n"
                        "To fix this, share the spreadsheet with 'Editor' access."
                    )
                )
            
            if error_code == 429:
                last_error = e
                if attempt < max_retries:
                    delay = base_delay * (2 ** attempt)
                    time.sleep(delay)
                    continue
            
            last_error = e
            if attempt < max_retries:
                delay = base_delay * (2 ** attempt)
                time.sleep(delay)
                continue
            
            raise NetworkError(f"Failed to update cell: {str(e)}")
            
        except Exception as e:
            last_error = e
            if attempt < max_retries:
                delay = base_delay * (2 ** attempt)
                time.sleep(delay)
                continue
            
            raise NetworkError(f"Failed to update cell: {str(e)}")
    
    raise NetworkError(f"Failed after {max_retries} retries: {last_error}")
