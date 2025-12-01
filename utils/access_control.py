"""
Access Control Module for MI Chatbot Portal

This module provides:
1. Robust Google Sheets client construction with version compatibility
2. Role and bot type normalization utilities
3. Code finding and marking functions
4. Clear error handling with admin-friendly messages

The gspread client construction supports multiple environments by:
- Trying gspread.service_account_from_dict first (newer gspread versions)
- Falling back to google.oauth2 Credentials + gspread.authorize (older versions)
- Avoiding internal attributes like client.auth.session

Supported roles:
- STUDENT: Regular access, codes are marked as used
- INSTRUCTOR: Infinite access, codes are NOT marked as used
- DEVELOPER: Access to developer page with test utilities, codes NOT auto-marked

Usage:
    from utils.access_control import get_sheet_client, find_code_row, mark_row_used
    
    client = get_sheet_client()  # May raise SheetClientError subclasses
    row_data = find_code_row(worksheet, "secret123")
    mark_row_used(worksheet, row_index)
"""

import os
import json
import base64
import binascii
import logging
from typing import Optional, Dict, Any, Tuple, Union

# Configure logging
logger = logging.getLogger(__name__)

# --- Constants ---
VALID_BOT_TYPES = ['OHI', 'HPV', 'TOBACCO', 'PERIO']
VALID_ROLES = ['STUDENT', 'INSTRUCTOR', 'DEVELOPER']
ROLE_STUDENT = 'STUDENT'
ROLE_INSTRUCTOR = 'INSTRUCTOR'
ROLE_DEVELOPER = 'DEVELOPER'

SERVICE_ACCOUNT_FILE = "umnsod-mibot-ea3154b145f1.json"

# Google Sheets API scopes
SCOPES = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/drive'
]


# --- Custom Exceptions ---
class SheetClientError(Exception):
    """Base exception for sheet client errors."""
    pass


class MissingSecretsError(SheetClientError):
    """Raised when no credentials are found."""
    
    def __init__(self, service_account_email: Optional[str] = None):
        self.service_account_email = service_account_email
        message = (
            "No Google Sheets credentials found.\n\n"
            "Administrators: Please configure one of the following:\n"
            "1. Streamlit secrets: st.secrets['GOOGLESA'] (TOML table or JSON string)\n"
            "2. Streamlit secrets: st.secrets['GOOGLESA_B64'] (base64-encoded JSON)\n"
            "3. Environment variable: GOOGLESA_B64 (base64-encoded JSON)\n"
            "4. Environment variable: GOOGLESA (single-line JSON)\n"
            f"5. Service account file: {SERVICE_ACCOUNT_FILE}"
        )
        super().__init__(message)


class MalformedSecretsError(SheetClientError):
    """Raised when credentials are found but malformed."""
    
    def __init__(self, source: str, detail: str, service_account_email: Optional[str] = None):
        self.source = source
        self.detail = detail
        self.service_account_email = service_account_email
        message = (
            f"Malformed credentials in {source}.\n\n"
            f"Error: {detail}\n\n"
            "Administrators: Please verify the credential format:\n"
            "- For GOOGLESA: Ensure valid JSON or TOML table format\n"
            "- For GOOGLESA_B64: Ensure valid base64-encoded JSON\n"
            "- Newlines in private_key must be escaped as \\n in JSON strings\n"
            "- Consider using GOOGLESA_B64 to avoid escaping issues"
        )
        super().__init__(message)


class PermissionDeniedError(SheetClientError):
    """Raised when service account lacks permission to access the sheet."""
    
    def __init__(self, sheet_id: str, service_account_email: Optional[str] = None):
        self.sheet_id = sheet_id
        self.service_account_email = service_account_email
        email_instruction = ""
        if service_account_email:
            email_instruction = (
                f"\n\nPlease share the spreadsheet with: {service_account_email}\n"
                "Grant 'Editor' access for the service account to read and update codes."
            )
        message = (
            f"Permission denied when accessing spreadsheet.\n\n"
            f"Sheet ID: {sheet_id}\n"
            f"Administrators: The service account does not have access to this spreadsheet."
            f"{email_instruction}"
        )
        super().__init__(message)


# --- Helper Functions ---
def normalize_role(role: Optional[str]) -> str:
    """
    Normalize role string to uppercase and stripped.
    
    Args:
        role: The role string to normalize
        
    Returns:
        Normalized role string, defaults to STUDENT if invalid
    """
    if role is None:
        return ROLE_STUDENT
    normalized = role.strip().upper()
    if normalized in VALID_ROLES:
        return normalized
    return ROLE_STUDENT


def normalize_bot_type(bot: Optional[str]) -> Optional[str]:
    """
    Normalize bot type string to uppercase and stripped.
    
    Args:
        bot: The bot type string to normalize
        
    Returns:
        Normalized bot type or None if invalid
    """
    if bot is None:
        return None
    normalized = bot.strip().upper()
    if normalized in VALID_BOT_TYPES:
        return normalized
    return None


def get_service_account_email(creds_dict: Dict[str, Any]) -> Optional[str]:
    """
    Extract service account email from credentials dictionary.
    
    Args:
        creds_dict: Credentials dictionary
        
    Returns:
        Service account email or None
    """
    return creds_dict.get('client_email')


def _parse_credentials_from_secrets(st_secrets) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Parse credentials from Streamlit secrets.
    
    Args:
        st_secrets: Streamlit secrets object
        
    Returns:
        Tuple of (credentials dict, source string) or (None, None)
        
    Raises:
        MalformedSecretsError: If secrets are found but malformed
    """
    # Method 1: Try GOOGLESA (TOML table or JSON string)
    try:
        if "GOOGLESA" in st_secrets:
            googlesa_secret = st_secrets["GOOGLESA"]
            
            if isinstance(googlesa_secret, str):
                # JSON string format
                try:
                    creds_dict = json.loads(googlesa_secret)
                    return creds_dict, "Streamlit secrets (JSON string)"
                except json.JSONDecodeError as e:
                    raise MalformedSecretsError(
                        "st.secrets['GOOGLESA']",
                        f"Invalid JSON: {str(e)}"
                    )
            else:
                # TOML table (mapping) format
                creds_dict = dict(googlesa_secret)
                return creds_dict, "Streamlit secrets (TOML table)"
    except MalformedSecretsError:
        raise
    except Exception:
        pass
    
    # Method 2: Try GOOGLESA_B64 (base64-encoded JSON)
    try:
        if "GOOGLESA_B64" in st_secrets:
            b64_secret = st_secrets["GOOGLESA_B64"]
            try:
                decoded = base64.b64decode(b64_secret).decode('utf-8')
                creds_dict = json.loads(decoded)
                return creds_dict, "Streamlit secrets (GOOGLESA_B64)"
            except (binascii.Error, UnicodeDecodeError) as e:
                raise MalformedSecretsError(
                    "st.secrets['GOOGLESA_B64']",
                    f"Invalid base64: {str(e)}"
                )
            except json.JSONDecodeError as e:
                raise MalformedSecretsError(
                    "st.secrets['GOOGLESA_B64']",
                    f"Decoded content is not valid JSON: {str(e)}"
                )
    except MalformedSecretsError:
        raise
    except Exception:
        pass
    
    return None, None


def _parse_credentials_from_env() -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Parse credentials from environment variables.
    
    Returns:
        Tuple of (credentials dict, source string) or (None, None)
        
    Raises:
        MalformedSecretsError: If env vars are found but malformed
    """
    # Method 3: Try GOOGLESA_B64 env var
    googlesa_b64 = os.environ.get('GOOGLESA_B64')
    if googlesa_b64:
        try:
            decoded = base64.b64decode(googlesa_b64).decode('utf-8')
            creds_dict = json.loads(decoded)
            return creds_dict, "Environment variable (GOOGLESA_B64)"
        except (binascii.Error, UnicodeDecodeError) as e:
            raise MalformedSecretsError(
                "GOOGLESA_B64 environment variable",
                f"Invalid base64: {str(e)}"
            )
        except json.JSONDecodeError as e:
            raise MalformedSecretsError(
                "GOOGLESA_B64 environment variable",
                f"Decoded content is not valid JSON: {str(e)}"
            )
    
    # Method 4: Try GOOGLESA env var
    googlesa_env = os.environ.get('GOOGLESA')
    if googlesa_env:
        try:
            creds_dict = json.loads(googlesa_env)
            return creds_dict, "Environment variable (GOOGLESA)"
        except json.JSONDecodeError as e:
            raise MalformedSecretsError(
                "GOOGLESA environment variable",
                f"Invalid JSON: {str(e)}. Ensure newlines are escaped as \\n"
            )
    
    return None, None


def _parse_credentials_from_file() -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Parse credentials from service account file.
    
    Returns:
        Tuple of (credentials dict, source string) or (None, None)
        
    Raises:
        MalformedSecretsError: If file exists but is malformed
    """
    if os.path.exists(SERVICE_ACCOUNT_FILE):
        try:
            with open(SERVICE_ACCOUNT_FILE, 'r') as f:
                creds_dict = json.load(f)
            return creds_dict, f"Service account file ({SERVICE_ACCOUNT_FILE})"
        except json.JSONDecodeError as e:
            raise MalformedSecretsError(
                f"Service account file ({SERVICE_ACCOUNT_FILE})",
                f"Invalid JSON: {str(e)}"
            )
        except IOError as e:
            raise MalformedSecretsError(
                f"Service account file ({SERVICE_ACCOUNT_FILE})",
                f"Could not read file: {str(e)}"
            )
    
    return None, None


def get_sheet_client(st_secrets=None):
    """
    Create and return a Google Sheets client using service account credentials.
    
    This function is compatible with multiple gspread/google-auth versions:
    1. Tries gspread.service_account_from_dict first (gspread >= 5.0)
    2. Falls back to google.oauth2 Credentials + gspread.authorize (older versions)
    
    Args:
        st_secrets: Streamlit secrets object (optional, will be accessed if not provided)
        
    Returns:
        gspread.Client: Authorized Google Sheets client
        
    Raises:
        MissingSecretsError: If no credentials are found
        MalformedSecretsError: If credentials are malformed
    """
    import gspread
    
    creds_dict = None
    creds_source = None
    
    # Try Streamlit secrets first
    if st_secrets is not None:
        creds_dict, creds_source = _parse_credentials_from_secrets(st_secrets)
    else:
        # Try to access st.secrets if available
        try:
            import streamlit as st
            creds_dict, creds_source = _parse_credentials_from_secrets(st.secrets)
        except Exception:
            pass
    
    # Try environment variables
    if creds_dict is None:
        creds_dict, creds_source = _parse_credentials_from_env()
    
    # Try service account file
    if creds_dict is None:
        creds_dict, creds_source = _parse_credentials_from_file()
    
    # Raise error if no credentials found
    if creds_dict is None:
        raise MissingSecretsError()
    
    service_account_email = get_service_account_email(creds_dict)
    logger.info(f"Using credentials from: {creds_source}")
    
    # Method 1: Try gspread.service_account_from_dict (gspread >= 5.0)
    try:
        client = gspread.service_account_from_dict(creds_dict, scopes=SCOPES)
        logger.info("Created client using gspread.service_account_from_dict")
        return client, creds_source, service_account_email
    except AttributeError:
        # gspread.service_account_from_dict not available in older versions
        logger.debug("service_account_from_dict not available, trying fallback")
    except ValueError as e:
        # Invalid credentials format
        raise MalformedSecretsError(
            creds_source or "unknown source",
            f"Invalid credentials format: {str(e)}",
            service_account_email
        )
    except Exception as e:
        # Log and continue to fallback for other errors
        logger.warning(f"service_account_from_dict failed: {e}, trying fallback")
    
    # Method 2: Fall back to google.oauth2 Credentials + gspread.authorize
    try:
        from google.oauth2.service_account import Credentials
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        client = gspread.authorize(creds)
        logger.info("Created client using google.oauth2.Credentials + gspread.authorize")
        return client, creds_source, service_account_email
    except ValueError as e:
        # Invalid credentials content
        raise MalformedSecretsError(
            creds_source or "unknown source",
            f"Invalid service account credentials: {str(e)}",
            service_account_email
        )
    except Exception as e:
        raise MalformedSecretsError(
            creds_source or "unknown source",
            f"Failed to create credentials: {str(e)}",
            service_account_email
        )


def find_code_row(worksheet, secret_code: str, headers: list = None) -> Optional[Dict[str, Any]]:
    """
    Find a row in the worksheet matching the given secret code.
    
    Args:
        worksheet: gspread Worksheet object
        secret_code: The secret code to search for
        headers: Optional list of header names (will be fetched if not provided)
        
    Returns:
        Dictionary with row data and index, or None if not found:
        {
            'row_index': int (1-based, including header),
            'table_no': str,
            'name': str,
            'bot': str (normalized),
            'secret': str,
            'used': bool,
            'role': str (normalized, defaults to STUDENT)
        }
    """
    try:
        all_values = worksheet.get_all_values()
        
        if len(all_values) < 2:
            return None
        
        if headers is None:
            headers = [h.strip().lower() for h in all_values[0]]
        else:
            headers = [h.strip().lower() for h in headers]
        
        # Find column indices
        secret_idx = headers.index('secret') if 'secret' in headers else 3
        name_idx = headers.index('name') if 'name' in headers else 1
        bot_idx = headers.index('bot') if 'bot' in headers else 2
        used_idx = headers.index('used') if 'used' in headers else 4
        table_idx = headers.index('table no') if 'table no' in headers else 0
        role_idx = headers.index('role') if 'role' in headers else None
        
        # Search for matching code
        for row_idx, row in enumerate(all_values[1:], start=2):  # Start at 2 (1-based + skip header)
            if len(row) <= secret_idx:
                continue
            
            if row[secret_idx].strip() == secret_code.strip():
                # Get role if column exists
                role = ROLE_STUDENT
                if role_idx is not None and len(row) > role_idx:
                    role = normalize_role(row[role_idx])
                
                # Parse used status
                used_val = row[used_idx].strip().upper() if len(row) > used_idx else ''
                is_used = used_val in ('TRUE', 'YES', '1')
                
                return {
                    'row_index': row_idx,
                    'table_no': row[table_idx] if len(row) > table_idx else '',
                    'name': row[name_idx] if len(row) > name_idx else '',
                    'bot': normalize_bot_type(row[bot_idx]) if len(row) > bot_idx else None,
                    'secret': row[secret_idx],
                    'used': is_used,
                    'role': role
                }
        
        return None
        
    except Exception as e:
        logger.error(f"Error finding code row: {e}")
        return None


def mark_row_used(worksheet, row_index: int, used_column: int = 5) -> bool:
    """
    Mark a row as used using single-cell update.
    
    Args:
        worksheet: gspread Worksheet object
        row_index: 1-based row index to update
        used_column: 1-based column index for 'Used' column (default: 5 = column E)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Use single-cell update for efficiency
        worksheet.update_cell(row_index, used_column, 'TRUE')
        logger.info(f"Marked row {row_index} as used")
        return True
    except Exception as e:
        logger.error(f"Error marking row {row_index} as used: {e}")
        return False


def check_sheet_permission(client, sheet_id: str, service_account_email: Optional[str] = None):
    """
    Check if the client has permission to access the specified sheet.
    
    Args:
        client: gspread Client object
        sheet_id: Google Sheet ID
        service_account_email: Email for error messages
        
    Returns:
        gspread Spreadsheet object
        
    Raises:
        PermissionDeniedError: If access is denied
    """
    try:
        return client.open_by_key(sheet_id)
    except Exception as e:
        error_msg = str(e).lower()
        if 'permission' in error_msg or '403' in error_msg or 'forbidden' in error_msg:
            raise PermissionDeniedError(sheet_id, service_account_email)
        raise
