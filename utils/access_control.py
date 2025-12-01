"""
Access Control Module for MI Chatbot Portal

This module provides centralized access-control logic for:
- Bot name and role normalization
- Instructor and Developer role detection
- Google Sheets client management with caching
- Code lookup and marking in the sheet

Usage:
    from utils.access_control import (
        normalize_bot, normalize_role, is_instructor_role, is_developer_role,
        get_sheet_client, find_code_row, mark_row_used
    )
"""

import os
import json
import base64
import logging
from typing import Optional, Tuple, Any

import gspread
from google.oauth2.service_account import Credentials

# Configure logging
logger = logging.getLogger(__name__)

# Valid bot types (normalized uppercase)
VALID_BOT_TYPES = ['OHI', 'HPV', 'TOBACCO', 'PERIO']

# Display names for bots (Title Case for user-facing messages)
BOT_DISPLAY_NAMES = {
    'OHI': 'OHI',
    'HPV': 'HPV',
    'TOBACCO': 'TOBACCO',
    'PERIO': 'PERIO'
}

# Role constants
ROLE_STUDENT = 'STUDENT'
ROLE_INSTRUCTOR = 'INSTRUCTOR'
ROLE_DEVELOPER = 'DEVELOPER'


def normalize_bot(bot_str: str) -> str:
    """
    Normalize a bot name string to uppercase.
    
    Args:
        bot_str: Bot name string (e.g., 'tobacco', 'Perio', 'OHI')
        
    Returns:
        Normalized uppercase bot name (e.g., 'TOBACCO', 'PERIO', 'OHI')
    """
    if not bot_str:
        return ''
    return bot_str.strip().upper()


def normalize_role(role_str: str) -> str:
    """
    Normalize a role name string to uppercase.
    
    Args:
        role_str: Role name string (e.g., 'instructor', 'Developer', 'student')
        
    Returns:
        Normalized uppercase role name (e.g., 'INSTRUCTOR', 'DEVELOPER', 'STUDENT')
    """
    if not role_str:
        return ROLE_STUDENT  # Default to student if not specified
    
    normalized = role_str.strip().upper()
    
    # Handle common variations
    if normalized in ('DEV', 'DEVELOPER'):
        return ROLE_DEVELOPER
    elif normalized in ('INSTRUCTOR', 'INST', 'TEACHER', 'ADMIN'):
        return ROLE_INSTRUCTOR
    elif normalized in ('STUDENT', 'STU', ''):
        return ROLE_STUDENT
    
    return normalized


def is_instructor_role(role: str) -> bool:
    """
    Check if a role indicates instructor access.
    
    Args:
        role: Role string (will be normalized)
        
    Returns:
        True if the role is instructor, False otherwise
    """
    return normalize_role(role) == ROLE_INSTRUCTOR


def is_developer_role(role: str) -> bool:
    """
    Check if a role indicates developer access.
    
    Args:
        role: Role string (will be normalized)
        
    Returns:
        True if the role is developer, False otherwise
    """
    return normalize_role(role) == ROLE_DEVELOPER


def get_bot_display_name(bot: str) -> str:
    """
    Get the display name for a bot (for user-facing messages).
    
    Args:
        bot: Bot name (will be normalized)
        
    Returns:
        Display name for the bot
    """
    normalized = normalize_bot(bot)
    return BOT_DISPLAY_NAMES.get(normalized, normalized)


def get_sheet_client(google_sa_b64: Optional[str] = None) -> gspread.Client:
    """
    Initialize and return a Google Sheets client using service account credentials.
    
    Args:
        google_sa_b64: Optional base64-encoded service account JSON.
                      If not provided, will try environment variables and Streamlit secrets.
    
    Returns:
        gspread.Client: Authorized Google Sheets client
        
    Raises:
        Exception: If authentication fails or credentials are not available
    """
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]
    
    creds = None
    
    # Method 1: Use provided base64-encoded credentials
    if google_sa_b64:
        try:
            googlesa_json = base64.b64decode(google_sa_b64).decode('utf-8')
            creds_dict = json.loads(googlesa_json)
            creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
            logger.debug("Using provided base64-encoded credentials")
        except Exception as e:
            logger.error(f"Failed to decode provided credentials: {e}")
            raise
    
    # Method 2: Try Streamlit secrets
    if creds is None:
        try:
            import streamlit as st
            if "GOOGLESA" in st.secrets:
                googlesa_secret = st.secrets["GOOGLESA"]
                if isinstance(googlesa_secret, str):
                    creds_dict = json.loads(googlesa_secret)
                else:
                    creds_dict = dict(googlesa_secret)
                creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
                logger.debug("Using Streamlit secrets (GOOGLESA)")
        except Exception:
            pass
    
    # Method 3: Try Streamlit GOOGLESA_B64 secret
    if creds is None:
        try:
            import streamlit as st
            if "GOOGLESA_B64" in st.secrets:
                googlesa_json = base64.b64decode(st.secrets["GOOGLESA_B64"]).decode('utf-8')
                creds_dict = json.loads(googlesa_json)
                creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
                logger.debug("Using Streamlit secrets (GOOGLESA_B64)")
        except Exception:
            pass
    
    # Method 4: Try GOOGLESA_B64 environment variable
    if creds is None:
        googlesa_b64_env = os.environ.get('GOOGLESA_B64')
        if googlesa_b64_env:
            try:
                googlesa_json = base64.b64decode(googlesa_b64_env).decode('utf-8')
                creds_dict = json.loads(googlesa_json)
                creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
                logger.debug("Using GOOGLESA_B64 environment variable")
            except Exception as e:
                logger.error(f"Failed to decode GOOGLESA_B64 env var: {e}")
    
    # Method 5: Try GOOGLESA environment variable
    if creds is None:
        googlesa_env = os.environ.get('GOOGLESA')
        if googlesa_env:
            try:
                creds_dict = json.loads(googlesa_env)
                creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
                logger.debug("Using GOOGLESA environment variable")
            except Exception as e:
                logger.error(f"Failed to parse GOOGLESA env var: {e}")
    
    # Method 6: Fallback to service account file
    if creds is None:
        service_account_file = "umnsod-mibot-ea3154b145f1.json"
        if os.path.exists(service_account_file):
            creds = Credentials.from_service_account_file(service_account_file, scopes=scope)
            logger.debug(f"Using service account file: {service_account_file}")
    
    if creds is None:
        raise Exception(
            "No credentials found. Tried:\n"
            "1. Provided base64 credentials\n"
            "2. Streamlit secrets (GOOGLESA)\n"
            "3. Streamlit secrets (GOOGLESA_B64)\n"
            "4. Environment variable (GOOGLESA_B64)\n"
            "5. Environment variable (GOOGLESA)\n"
            "6. Service account file\n"
            "Please configure at least one authentication method."
        )
    
    # Use gspread.authorize with credentials
    client = gspread.authorize(creds)
    return client


def find_code_row(worksheet: Any, code: str) -> Optional[Tuple[int, dict]]:
    """
    Find a code in the worksheet and return its row data.
    
    Args:
        worksheet: gspread Worksheet object
        code: Secret code to search for
        
    Returns:
        Tuple of (row_index, row_data) if found, None otherwise.
        row_index is 1-based (as used by gspread).
        row_data is a dict with keys: table_no, name, bot, secret, used, role
    """
    if not code:
        return None
    
    try:
        all_values = worksheet.get_all_values()
        
        if len(all_values) < 2:
            return None
        
        headers = all_values[0]
        data = all_values[1:]
        
        # Find column indices
        # Expected: Table No, Name, Bot, Secret, Used, [Role]
        secret_col = None
        for i, h in enumerate(headers):
            if h.lower().strip() == 'secret':
                secret_col = i
                break
        
        if secret_col is None:
            # Fallback to column 3 (0-indexed)
            secret_col = 3
        
        # Search for the code
        code_clean = code.strip()
        for row_idx, row in enumerate(data):
            if len(row) > secret_col:
                row_secret = row[secret_col].strip()
                if row_secret == code_clean:
                    # Build row data dict
                    row_data = {
                        'table_no': row[0] if len(row) > 0 else '',
                        'name': row[1] if len(row) > 1 else '',
                        'bot': row[2] if len(row) > 2 else '',
                        'secret': row[3] if len(row) > 3 else '',
                        'used': row[4] if len(row) > 4 else '',
                        'role': row[5] if len(row) > 5 else ''  # Role column (optional)
                    }
                    # row_idx + 2 because of 0-indexing and header row
                    return (row_idx + 2, row_data)
        
        return None
        
    except Exception as e:
        logger.error(f"Error searching for code in sheet: {e}")
        return None


def mark_row_used(worksheet: Any, row_index: int, used_col: int = 5) -> bool:
    """
    Mark a row as used in the worksheet using single-cell update.
    
    Args:
        worksheet: gspread Worksheet object
        row_index: 1-based row index
        used_col: 1-based column index for the "Used" column (default: 5)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        worksheet.update_cell(row_index, used_col, 'TRUE')
        logger.info(f"Marked row {row_index} as used")
        return True
    except Exception as e:
        logger.error(f"Error marking row {row_index} as used: {e}")
        return False


def is_code_used(used_value: str) -> bool:
    """
    Check if a "Used" cell value indicates the code is already used.
    
    Args:
        used_value: Value from the "Used" column
        
    Returns:
        True if the code is already used, False otherwise
    """
    if not used_value:
        return False
    
    used_clean = used_value.strip().upper()
    return used_clean in ('TRUE', 'YES', '1')


def validate_bot_match(assigned_bot: str, requested_bot: str) -> Tuple[bool, str]:
    """
    Validate that the assigned bot matches the requested bot.
    
    Args:
        assigned_bot: Bot assigned to the code (from sheet)
        requested_bot: Bot the user is trying to access
        
    Returns:
        Tuple of (is_valid, error_message).
        is_valid is True if bots match, False otherwise.
        error_message is empty if valid, contains error if not.
    """
    assigned_normalized = normalize_bot(assigned_bot)
    requested_normalized = normalize_bot(requested_bot)
    
    if assigned_normalized == requested_normalized:
        return (True, '')
    
    # Generate the exact error message as specified in requirements
    error_msg = (
        f"Access Denied: You are not authorized for this chatbot. "
        f"You are assigned to the {get_bot_display_name(assigned_bot)} chatbot."
    )
    return (False, error_msg)
