"""
Secret Code Portal - Student Access Gateway

This Streamlit application provides a secure entry point for students to access
the MI chatbots (OHI, HPV, TOBACCO, or PERIO) using secret codes distributed by instructors.

Features:
- Code validation against Google Sheets database
- Automatic marking of codes as used (for student codes only)
- Support for Instructor codes (infinite access to all bots, never marked used)
- Support for Developer codes (access to Developer page, reusable)
- Redirect to appropriate bot (OHI, HPV, Tobacco, or Perio)
- Real-time data refresh capability
- Clear error messages for invalid or used codes

Google Sheet Structure:
- Sheet ID: 1x_MA3MqvyxN3p7v_mQ3xYB9SmEGPn1EspO0fUsYayFY
- Sheet Name: Sheet1
- Columns: Table No, Name, Bot, Secret, Used, [Role]
  - Role column is optional; if present, supports: Student, Instructor, Developer

Usage:
    streamlit run secret_code_portal.py

Authentication:
    Supports five methods (in priority order):
    1. Streamlit secrets: st.secrets["GOOGLESA"] (TOML table or JSON string)
    2. Streamlit secrets: st.secrets["GOOGLESA_B64"] (base64-encoded JSON)
    3. Environment variable: GOOGLESA_B64 (base64-encoded JSON, recommended)
    4. Environment variable: GOOGLESA (single-line JSON with escaped newlines)
    5. Service account file: umnsod-mibot-ea3154b145f1.json (for local/dev)

Requirements:
    - Service account must have access to the Google Sheet
    - Internet connection for Google Sheets API calls
"""

import os
import json
import base64
import logging
import streamlit as st
from streamlit.errors import StreamlitAPIException
import gspread
from google.oauth2.service_account import Credentials

# Import access control utilities
from utils.access_control import (
    normalize_bot,
    normalize_role,
    is_instructor_role,
    is_developer_role,
    get_bot_display_name,
    is_code_used,
    VALID_BOT_TYPES,
    ROLE_INSTRUCTOR,
    ROLE_DEVELOPER,
    ROLE_STUDENT,
)

# Configure logging for diagnostics
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Mapping from uppercase bot type to page file path
# Note: Page file names use Title Case (e.g., Tobacco.py, Perio.py) per existing convention
BOT_PAGE_MAP = {
    'OHI': 'pages/OHI.py',
    'HPV': 'pages/HPV.py',
    'TOBACCO': 'pages/Tobacco.py',
    'PERIO': 'pages/Perio.py'
}

# Developer page path
DEVELOPER_PAGE = 'pages/developer_page.py'

SHEET_ID = "1x_MA3MqvyxN3p7v_mQ3xYB9SmEGPn1EspO0fUsYayFY"
SHEET_NAME = "Sheet1"
SERVICE_ACCOUNT_FILE = "umnsod-mibot-ea3154b145f1.json"

# --- Streamlit page configuration ---
st.set_page_config(
    page_title="MI Chatbot Access Portal",
    page_icon="🔐",
    layout="centered"
)


@st.cache_resource
def get_google_sheets_client():
    """
    Initialize and return Google Sheets client using service account credentials.
    Cached to avoid repeated authentication.
    
    Supports five authentication methods (in priority order):
    1. Streamlit secrets: st.secrets["GOOGLESA"] (TOML table or JSON string)
    2. Streamlit secrets: st.secrets["GOOGLESA_B64"] (base64-encoded JSON)
    3. Environment variable: GOOGLESA_B64 (base64-encoded JSON)
    4. Environment variable: GOOGLESA (JSON string)
    5. Service account file: umnsod-mibot-ea3154b145f1.json (for local/dev)
    
    Returns:
        gspread.Client: Authorized Google Sheets client
        
    Raises:
        Exception: If authentication fails or credentials are not available
    """
    try:
        # Setup credentials with required scopes
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        
        creds = None
        creds_source = None
        
        # Method 1: Try Streamlit secrets first (for Streamlit Cloud deployment)
        # Supports both TOML table (mapping) and JSON string formats
        try:
            if "GOOGLESA" in st.secrets:
                googlesa_secret = st.secrets["GOOGLESA"]
                
                # Check if it's a string (JSON format) or a mapping (TOML table)
                if isinstance(googlesa_secret, str):
                    # It's a JSON string, parse it
                    try:
                        creds_dict = json.loads(googlesa_secret)
                        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
                        creds_source = "Streamlit secrets (JSON string)"
                    except json.JSONDecodeError as e:
                        raise Exception(
                            f"Failed to parse st.secrets['GOOGLESA'] as JSON: {str(e)}. "
                            f"If using JSON format, ensure it's valid JSON. "
                            f"Alternatively, use TOML table format in Streamlit secrets or "
                            f"use GOOGLESA_B64 with base64-encoded JSON to avoid escaping issues."
                        )
                else:
                    # It's a mapping (TOML table), convert to dict
                    creds_dict = dict(googlesa_secret)
                    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
                    creds_source = "Streamlit secrets (TOML table)"
        except Exception as e:
            # Only re-raise if it's a parsing error we explicitly raised
            if "Failed to parse st.secrets['GOOGLESA']" in str(e):
                raise
            # Otherwise, Streamlit secrets not available or failed for other reasons
            pass
        
        # Method 2: Try Streamlit secrets GOOGLESA_B64 (base64-encoded JSON)
        if creds is None:
            try:
                if "GOOGLESA_B64" in st.secrets:
                    googlesa_b64_secret = st.secrets["GOOGLESA_B64"]
                    try:
                        # Decode base64
                        googlesa_json = base64.b64decode(googlesa_b64_secret).decode('utf-8')
                        creds_dict = json.loads(googlesa_json)
                        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
                        creds_source = "Streamlit secrets (GOOGLESA_B64)"
                    except (base64.binascii.Error, UnicodeDecodeError) as e:
                        raise Exception(
                            f"Failed to decode st.secrets['GOOGLESA_B64']: {str(e)}. "
                            f"Ensure it contains valid base64-encoded JSON. "
                            f"To create base64: cat service-account.json | base64 -w 0"
                        )
                    except json.JSONDecodeError as e:
                        raise Exception(
                            f"Failed to parse decoded st.secrets['GOOGLESA_B64'] as JSON: {str(e)}. "
                            f"Ensure the base64 content decodes to valid service account JSON."
                        )
            except Exception as e:
                # Only re-raise if it's a parsing error we explicitly raised
                if "Failed to decode st.secrets['GOOGLESA_B64']" in str(e) or "Failed to parse decoded st.secrets['GOOGLESA_B64']" in str(e):
                    raise
                # Otherwise, Streamlit secrets not available or failed for other reasons
                pass
        
        # Method 3: Try GOOGLESA_B64 environment variable (base64-encoded JSON)
        if creds is None:
            googlesa_b64 = os.environ.get('GOOGLESA_B64')
            if googlesa_b64:
                try:
                    # Decode base64
                    googlesa_json = base64.b64decode(googlesa_b64).decode('utf-8')
                    creds_dict = json.loads(googlesa_json)
                    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
                    creds_source = "Environment variable (GOOGLESA_B64)"
                except (base64.binascii.Error, UnicodeDecodeError) as e:
                    raise Exception(
                        f"Failed to decode GOOGLESA_B64 environment variable: {str(e)}. "
                        f"Ensure it contains valid base64-encoded JSON."
                    )
                except json.JSONDecodeError as e:
                    raise Exception(
                        f"Failed to parse decoded GOOGLESA_B64 as JSON: {str(e)}. "
                        f"Ensure the base64 content decodes to valid JSON."
                    )
        
        # Method 4: Try GOOGLESA environment variable (JSON string)
        if creds is None:
            googlesa_env = os.environ.get('GOOGLESA')
            if googlesa_env:
                try:
                    creds_dict = json.loads(googlesa_env)
                    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
                    creds_source = "Environment variable (GOOGLESA)"
                except json.JSONDecodeError as e:
                    raise Exception(
                        f"Failed to parse GOOGLESA environment variable as JSON: {str(e)}. "
                        f"Common issue: unescaped newlines in private_key field. "
                        f"Solutions:\n"
                        f"  1. Use Streamlit secrets (recommended for Streamlit Cloud)\n"
                        f"  2. Use GOOGLESA_B64 (env var or Streamlit secret) with base64-encoded JSON\n"
                        f"  3. Ensure GOOGLESA contains single-line JSON with \\n escapes in private_key"
                    )
        
        # Method 5: Fallback to service account file (for local/dev)
        if creds is None:
            if os.path.exists(SERVICE_ACCOUNT_FILE):
                creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scope)
                creds_source = f"Service account file ({SERVICE_ACCOUNT_FILE})"
            else:
                raise FileNotFoundError(
                    f"No credentials found. Tried:\n"
                    f"1. Streamlit secrets (st.secrets['GOOGLESA'])\n"
                    f"2. Streamlit secrets (st.secrets['GOOGLESA_B64'])\n"
                    f"3. Environment variable (GOOGLESA_B64)\n"
                    f"4. Environment variable (GOOGLESA)\n"
                    f"5. Service account file ('{SERVICE_ACCOUNT_FILE}')\n"
                    f"Please configure at least one authentication method."
                )
        
        # Store which credentials source was used for debugging (non-secret indicator)
        if creds_source:
            st.session_state["googlesa_source"] = creds_source
        
        # Authorize and return client
        client = gspread.authorize(creds)
        return client
        
    except Exception as e:
        raise Exception(f"Failed to initialize Google Sheets client: {str(e)}")


@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_codes_from_sheet_cached():
    """
    Load secret codes from Google Sheet. Cached to reduce API calls.
    
    Returns:
        dict: Dictionary with 'worksheet', 'headers', 'rows' keys, or None if failed
    """
    try:
        # Get Google Sheets client
        client = get_google_sheets_client()
        
        # Open the spreadsheet
        sheet = client.open_by_key(SHEET_ID)
        worksheet = sheet.worksheet(SHEET_NAME)
        
        # Get all values from the sheet
        all_values = worksheet.get_all_values()
        
        if len(all_values) < 2:
            return None
        
        # Parse the data (first row is headers)
        headers = all_values[0]
        data = all_values[1:]
        
        # Validate headers
        expected_headers = ['Table No', 'Name', 'Bot', 'Secret', 'Used']
        if headers != expected_headers:
            return None
        
        # Return data structure
        return {
            'worksheet': worksheet,
            'headers': headers,
            'rows': data
        }
        
    except Exception as e:
        st.error(f"Error loading data from Google Sheets: {str(e)}")
        return None


def load_codes_from_sheet(force_refresh=False):
    """
    Load secret codes from Google Sheet into session state.
    
    Args:
        force_refresh (bool): If True, force reload from Google Sheets even if data exists
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Clear cache if forcing refresh
    if force_refresh:
        load_codes_from_sheet_cached.clear()
    
    # Use cached data if available and not forcing refresh
    if not force_refresh and 'codes_data' in st.session_state:
        return True
    
    # Load from cached function
    data = load_codes_from_sheet_cached()
    
    if data is None:
        st.error("Failed to load code database. Please refresh the page or contact support.")
        return False
    
    # Store data in session state
    st.session_state.codes_data = data
    st.session_state.last_refresh = None
    
    return True


def validate_code(secret_code):
    """
    Validate a secret code without marking it as used.
    
    This function implements the following logic:
    1. Find the code in the sheet
    2. Check role:
       - INSTRUCTOR: Grant access to all bots, do NOT mark as used
       - DEVELOPER: Grant access to Developer page, do NOT mark as used
       - STUDENT (default): Validate bot type but do NOT mark yet
    
    Marking is done separately by mark_code_used() after session state is set.
    
    Args:
        secret_code (str): The secret code entered by the student
        
    Returns:
        dict: Result dictionary with keys:
            - success (bool): Whether the code is valid and access should be granted
            - message (str): User-friendly message
            - bot (str): Bot type (OHI, HPV, TOBACCO, PERIO, or 'ALL' for instructors) if successful
            - name (str): Student/user name if successful
            - role (str): Role (STUDENT, INSTRUCTOR, DEVELOPER) if successful
            - row_index (int): Sheet row index for marking (only for students)
            - should_mark (bool): Whether this code should be marked as used
    """
    if 'codes_data' not in st.session_state:
        return {
            'success': False,
            'message': 'Code data not loaded. Please refresh the data.',
            'bot': None,
            'name': None,
            'role': None,
            'row_index': None,
            'should_mark': False
        }
    
    rows = st.session_state.codes_data['rows']
    
    # Search for the code in the data
    for row_idx, row in enumerate(rows):
        if len(row) < 5:
            continue
            
        table_no = row[0] if len(row) > 0 else ''
        name = row[1] if len(row) > 1 else ''
        bot = row[2] if len(row) > 2 else ''
        secret = row[3] if len(row) > 3 else ''
        used = row[4] if len(row) > 4 else ''
        role_raw = row[5] if len(row) > 5 else ''  # Role column (optional)
        
        # Check if this is the matching code
        if secret.strip() == secret_code.strip():
            # Normalize the role
            role = normalize_role(role_raw)
            
            # Check if already used (only applies to student codes)
            if role == ROLE_STUDENT and is_code_used(used):
                return {
                    'success': False,
                    'message': 'This code has already been used. Please contact your instructor if you need a new code.',
                    'bot': None,
                    'name': None,
                    'role': None,
                    'row_index': None,
                    'should_mark': False
                }
            
            # Handle INSTRUCTOR role - infinite access to all bots, never marked used
            if is_instructor_role(role):
                return {
                    'success': True,
                    'message': 'Instructor access granted',
                    'bot': 'ALL',  # Special value indicating access to all bots
                    'name': name,
                    'role': ROLE_INSTRUCTOR,
                    'row_index': None,
                    'should_mark': False  # Instructors are never marked
                }
            
            # Handle DEVELOPER role - access to Developer page, never marked used
            if is_developer_role(role):
                return {
                    'success': True,
                    'message': 'Developer access granted',
                    'bot': 'DEVELOPER',  # Special value for developer page
                    'name': name,
                    'role': ROLE_DEVELOPER,
                    'row_index': None,
                    'should_mark': False  # Developers are never marked
                }
            
            # Student role - validate bot type
            bot_normalized = normalize_bot(bot)
            if bot_normalized not in VALID_BOT_TYPES:
                logger.warning(
                    f"Rejected invalid bot type '{bot}' (normalized: '{bot_normalized}') "
                    f"for code row {row_idx + 2}. Valid types: {VALID_BOT_TYPES}"
                )
                return {
                    'success': False,
                    'message': f'Invalid bot type "{bot}" in the sheet. Valid types are: {", ".join(VALID_BOT_TYPES)}. Please contact your instructor.',
                    'bot': None,
                    'name': None,
                    'role': None,
                    'row_index': None,
                    'should_mark': False
                }
            
            # For students: validation passed, return success with mark info
            # Marking happens AFTER session state is set
            cell_row = row_idx + 2  # +2 for 0-indexing and header row
            return {
                'success': True,
                'message': f'Welcome, {name}! Redirecting you to the {bot_normalized} chatbot...',
                'bot': bot_normalized,
                'name': name,
                'role': ROLE_STUDENT,
                'row_index': cell_row,
                'should_mark': True  # Students should be marked after session setup
            }
    
    # Code not found
    return {
        'success': False,
        'message': 'Invalid code. Please check your code and try again.',
        'bot': None,
        'name': None,
        'role': None,
        'row_index': None,
        'should_mark': False
    }


def mark_code_used(row_index):
    """
    Mark a code as used in the Google Sheet.
    
    This should be called AFTER session state is set for student codes.
    
    Args:
        row_index (int): 1-based row index in the sheet
        
    Returns:
        bool: True if successful, False otherwise
    """
    if 'codes_data' not in st.session_state:
        logger.error("Cannot mark code: codes_data not in session state")
        return False
    
    worksheet = st.session_state.codes_data['worksheet']
    
    try:
        # Update the "Used" column (column E, index 5)
        cell_col = 5
        worksheet.update_cell(row_index, cell_col, 'TRUE')
        logger.info(f"Marked row {row_index} as used")
        
        # Clear the cache so next read gets fresh data
        load_codes_from_sheet_cached.clear()
        
        return True
    except Exception as e:
        logger.error(f"Error marking code as used: {e}")
        return False


def main():
    """Main application logic."""
    
    # Title and introduction
    st.title("🔐 MI Chatbot Access Portal")
    
    st.markdown(
        """
        Welcome to the **Motivational Interviewing Practice Portal**!
        
        Enter the secret code provided by your instructor to access your assigned chatbot practice session.
        
        **Instructions:**
        1. Enter your name and Groq API key
        2. Enter your secret code
        3. Click "Submit Code" to verify your access
        4. You will be redirected to your assigned chatbot (OHI, HPV, Tobacco, or Perio)
        
        **Note:** Each code can only be used once. If you encounter any issues, please contact your instructor.
        """
    )
    
    # Initialize session state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'redirect_info' not in st.session_state:
        st.session_state.redirect_info = None
    
    # Load data from Google Sheets on first run
    if 'codes_data' not in st.session_state:
        with st.spinner("Loading access codes from database..."):
            if not load_codes_from_sheet():
                st.error("Failed to load code database. Please refresh the page or contact support.")
                st.stop()
    
    # Compact refresh button with custom CSS
    st.markdown("""
        <style>
        div.stButton > button[kind="secondary"] {
            padding: 0.25rem 0.75rem;
            font-size: 0.875rem;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Refresh button
    st.markdown("---")
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        if st.button("🔄 Refresh Data", type="secondary", help="Reload codes from Google Sheets"):
            with st.spinner("Refreshing data..."):
                if load_codes_from_sheet(force_refresh=True):
                    st.success("Data refreshed successfully!")
                    st.rerun()
                else:
                    st.error("Failed to refresh data. Please try again.")
    
    st.markdown("---")
    
    # Code entry form
    if not st.session_state.authenticated:
        with st.form("code_entry_form"):
            st.subheader("Enter Your Information")
            
            # Student name input
            student_name = st.text_input(
                "👤 Student Name",
                placeholder="Enter your full name",
                help="Your name for the feedback report"
            )
            
            # Groq API key input
            groq_api_key = st.text_input(
                "🔑 Groq API Key",
                type="password",
                placeholder="Enter your Groq API key",
                help="Your Groq API key for accessing the chatbot. Get one at https://console.groq.com/"
            )
            
            # Secret code input
            secret_code = st.text_input(
                "🎫 Secret Code",
                type="password",
                placeholder="Enter your secret code here",
                help="The secret code provided by your instructor"
            )
            
            submit_button = st.form_submit_button("Submit Code", type="primary")
            
            if submit_button:
                # Validate all inputs
                if not student_name:
                    st.error("Please enter your name.")
                elif not groq_api_key:
                    st.error("Please enter your Groq API key.")
                elif not secret_code:
                    st.error("Please enter a secret code.")
                else:
                    with st.spinner("Verifying your code..."):
                        result = validate_code(secret_code)
                        
                        if result['success']:
                            # STEP 1: Set session state FIRST (before marking)
                            st.session_state.authenticated = True
                            st.session_state.redirect_info = {
                                'bot': result['bot'],
                                'name': result['name']
                            }
                            st.session_state.student_name = student_name
                            st.session_state.groq_api_key = groq_api_key
                            st.session_state.user_role = result.get('role', ROLE_STUDENT)
                            
                            # Set environment variable for libraries that need it
                            os.environ["GROQ_API_KEY"] = groq_api_key
                            
                            # STEP 2: Mark code as used AFTER session state is set (for students only)
                            if result.get('should_mark', False) and result.get('row_index'):
                                mark_success = mark_code_used(result['row_index'])
                                if not mark_success:
                                    # Log the error but don't prevent access
                                    # The session is already authorized
                                    logger.warning(f"Failed to mark code as used for row {result['row_index']}")
                            
                            st.success(result['message'])
                            
                            # Handle navigation based on role
                            bot_type = result['bot']
                            user_role = result.get('role', ROLE_STUDENT)
                            
                            try:
                                if user_role == ROLE_INSTRUCTOR:
                                    # Instructor: Show selection page or go to first bot
                                    # For now, redirect to OHI as default (instructors can navigate)
                                    st.info("As an instructor, you have access to all chatbots.")
                                    st.switch_page(BOT_PAGE_MAP['OHI'])
                                elif user_role == ROLE_DEVELOPER:
                                    # Developer: Go to developer page
                                    st.switch_page(DEVELOPER_PAGE)
                                elif bot_type in BOT_PAGE_MAP:
                                    # Student: Go to assigned bot
                                    st.switch_page(BOT_PAGE_MAP[bot_type])
                                else:
                                    logger.error(f"Unexpected bot type '{bot_type}' not in BOT_PAGE_MAP")
                                    st.error(f"⚠️ Configuration Error: Unknown bot type '{bot_type}'.")
                            except StreamlitAPIException as e:
                                if user_role == ROLE_DEVELOPER:
                                    st.error(
                                        "⚠️ Navigation Error: Could not find the Developer page. "
                                        "This may indicate a deployment issue. Please contact support."
                                    )
                                else:
                                    st.error(
                                        f"⚠️ Navigation Error: Could not find the {bot_type} chatbot page. "
                                        f"This may indicate a deployment issue. Please contact support."
                                    )
                                st.info(
                                    "**Technical Details**: The page file is missing or misconfigured. "
                                    "This should be resolved by the system administrator."
                                )
                        else:
                            st.error(result['message'])
    
    # Show success message if already authenticated (shouldn't normally be seen due to switch_page)
    if st.session_state.authenticated and st.session_state.redirect_info:
        redirect_info = st.session_state.redirect_info
        bot_type = redirect_info['bot']
        user_name = redirect_info.get('name', 'User')
        user_role = st.session_state.get('user_role', ROLE_STUDENT)
        
        st.success(f"✅ Access granted for {user_name}!")
        
        if user_role == ROLE_INSTRUCTOR:
            st.info("As an instructor, you have access to all chatbots. Redirecting...")
        elif user_role == ROLE_DEVELOPER:
            st.info("Developer access granted. Redirecting to Developer page...")
        else:
            st.info(f"You have been assigned to the **{bot_type}** chatbot. Redirecting...")
        
        # Navigate based on role
        try:
            if user_role == ROLE_INSTRUCTOR:
                st.switch_page(BOT_PAGE_MAP['OHI'])
            elif user_role == ROLE_DEVELOPER:
                st.switch_page(DEVELOPER_PAGE)
            elif bot_type in BOT_PAGE_MAP:
                st.switch_page(BOT_PAGE_MAP[bot_type])
            else:
                logger.error(f"Unexpected bot type '{bot_type}' not in BOT_PAGE_MAP")
                st.error(f"⚠️ Configuration Error: Unknown bot type '{bot_type}'.")
        except StreamlitAPIException as e:
            st.error(
                f"⚠️ Navigation Error: Could not find the appropriate page. "
                f"This may indicate a deployment issue. Please contact support."
            )
            st.info(
                "**Technical Details**: The page file is missing or misconfigured. "
                "This should be resolved by the system administrator."
            )
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666; font-size: 14px;'>
        <p>Having trouble? Contact your instructor for assistance.</p>
        <p>© 2025 UMN School of Dentistry - MI Practice Portal</p>
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
