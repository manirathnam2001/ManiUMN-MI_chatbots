"""
Secret Code Portal - Student Access Gateway

This Streamlit application provides a secure entry point for students to access
the MI chatbots (OHI, HPV, TOBACCO, or PERIO) using secret codes distributed by instructors.

Features:
- Code validation against Google Sheets database
- Automatic marking of codes as used (except for Instructor/Developer roles)
- Redirect to appropriate bot (OHI, HPV, Tobacco, or Perio)
- Real-time data refresh capability
- Clear error messages for invalid or used codes
- Robust error handling with admin-friendly messages

Google Sheet Structure:
- Sheet ID: 1x_MA3MqvyxN3p7v_mQ3xYB9SmEGPn1EspO0fUsYayFY
- Sheet Name: Sheet1
- Columns: Table No, Name, Bot, Secret, Used, Role (optional)

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
import logging
import streamlit as st
from streamlit.errors import StreamlitAPIException

from utils.access_control import (
    get_sheet_client,
    open_sheet_with_retry,
    get_sheet_data_with_retry,
    update_cell_with_retry,
    CredentialError,
    SheetAccessError,
    NetworkError,
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
    'PERIO': 'pages/Perio.py',
    'DEVELOPER': 'pages/developer_page.py'
}

SHEET_ID = "1x_MA3MqvyxN3p7v_mQ3xYB9SmEGPn1EspO0fUsYayFY"
SHEET_NAME = "Sheet1"

# --- Streamlit page configuration ---
st.set_page_config(
    page_title="MI Chatbot Access Portal",
    page_icon="🔐",
    layout="centered"
)


def _get_cached_client():
    """
    Get the cached Google Sheets client using the centralized access control module.
    This wrapper handles caching at the Streamlit level.
    
    Returns:
        Tuple of (client, creds_source, service_account_email)
    """
    return get_sheet_client(st.secrets)


@st.cache_resource
def get_google_sheets_client():
    """
    Initialize and return Google Sheets client using service account credentials.
    Cached to avoid repeated authentication.
    
    Uses the robust get_sheet_client from utils.access_control which:
    - Tries multiple credential sources in priority order
    - Uses gspread.service_account_from_dict when available (gspread >= 5.0)
    - Provides clear, actionable error messages for administrators
    
    Returns:
        tuple: (gspread.Client, credential_source, service_account_email)
        
    Raises:
        CredentialError: If no valid credentials are found or credentials are malformed
    """
    client, creds_source, service_account_email = get_sheet_client(st.secrets)
    
    # Store metadata for debugging (non-secret indicators)
    st.session_state["googlesa_source"] = creds_source
    if service_account_email:
        st.session_state["service_account_email"] = service_account_email
    
    return client, creds_source, service_account_email


def _display_credential_error(error: CredentialError):
    """Display a credential error with admin-friendly guidance."""
    st.error("⚠️ **Configuration Error: Missing or Invalid Credentials**")
    st.markdown(f"""
**Error:** {str(error)}

---

**Admin Guidance:**

{error.admin_hint}
""")
    
    # Add expandable section with technical details
    with st.expander("📋 Quick Setup Guide"):
        st.markdown("""
**Option 1: Streamlit Cloud (Recommended)**
1. Go to your Streamlit Cloud dashboard
2. Navigate to your app's settings → Secrets
3. Add your service account JSON as a TOML table:
```toml
[GOOGLESA]
type = "service_account"
project_id = "your-project"
# ... rest of service account fields
```

**Option 2: Base64-Encoded (Works everywhere)**
1. Encode your service account JSON:
   ```bash
   cat service-account.json | base64 -w 0
   ```
2. Set as `GOOGLESA_B64` secret or environment variable

**Option 3: Local Development**
1. Place `umnsod-mibot-ea3154b145f1.json` in the application directory
""")


def _display_sheet_access_error(error: SheetAccessError):
    """Display a sheet access error with admin-friendly guidance."""
    st.error("⚠️ **Spreadsheet Access Error**")
    st.markdown(f"""
**Error:** {str(error)}

---

**Admin Guidance:**

{error.admin_hint}
""")
    
    if error.service_account_email:
        st.info(f"📧 **Service Account Email:** `{error.service_account_email}`\n\nShare your spreadsheet with this email address and grant 'Editor' access.")


def _display_network_error(error: NetworkError):
    """Display a network error with retry option."""
    st.warning("⚠️ **Network Error**")
    st.markdown(f"""
**Error:** {str(error)}

This appears to be a temporary network issue. Please try again.
""")


@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_codes_from_sheet_cached(_client_id: str):
    """
    Load secret codes from Google Sheet. Cached to reduce API calls.
    
    Args:
        _client_id: Cache key based on client identity (prevents stale cache issues)
    
    Returns:
        dict: Dictionary with 'headers', 'rows' keys, or error dict with 'error' and 'error_type' keys
    """
    try:
        # Get Google Sheets client
        client, creds_source, service_account_email = get_google_sheets_client()
        
        # Open the worksheet with retry logic
        worksheet = open_sheet_with_retry(
            client, SHEET_ID, SHEET_NAME,
            service_account_email=service_account_email
        )
        
        # Get all values with retry logic
        all_values = get_sheet_data_with_retry(worksheet)
        
        if len(all_values) < 2:
            return {
                'error': 'Sheet is empty or has only headers',
                'error_type': 'empty_sheet'
            }
        
        # Parse the data (first row is headers)
        headers = all_values[0]
        data = all_values[1:]
        
        # Validate headers
        expected_headers = ['Table No', 'Name', 'Bot', 'Secret', 'Used']
        if headers != expected_headers:
            return {
                'error': f'Invalid sheet headers. Expected: {expected_headers}, Got: {headers}',
                'error_type': 'invalid_headers'
            }
        
        # Return data structure (without worksheet - it will be fetched fresh for writes)
        return {
            'headers': headers,
            'rows': data,
            'service_account_email': service_account_email
        }
        
    except CredentialError as e:
        return {'error': str(e), 'error_type': 'credential', 'admin_hint': e.admin_hint}
    except SheetAccessError as e:
        return {
            'error': str(e), 
            'error_type': 'access', 
            'admin_hint': e.admin_hint,
            'service_account_email': e.service_account_email
        }
    except NetworkError as e:
        return {'error': str(e), 'error_type': 'network'}
    except Exception as e:
        logger.exception("Unexpected error loading sheet data")
        return {'error': str(e), 'error_type': 'unknown'}


def load_codes_from_sheet(force_refresh=False):
    """
    Load secret codes from Google Sheet into session state.
    
    Args:
        force_refresh (bool): If True, force reload from Google Sheets even if data exists
        
    Returns:
        bool: True if successful, False otherwise (errors are displayed to user)
    """
    # Clear cache if forcing refresh
    if force_refresh:
        load_codes_from_sheet_cached.clear()
        # Also clear the client cache to get fresh credentials
        get_google_sheets_client.clear()
    
    # Use cached data if available and not forcing refresh
    if not force_refresh and 'codes_data' in st.session_state and 'error' not in st.session_state.codes_data:
        return True
    
    # Generate a cache key based on current time (for cache invalidation)
    # This ensures the cached function is called with consistent parameters
    try:
        cache_key = st.session_state.get("googlesa_source", "default")
    except Exception:
        cache_key = "default"
    
    # Load from cached function
    data = load_codes_from_sheet_cached(cache_key)
    
    if 'error' in data:
        error_type = data.get('error_type', 'unknown')
        
        if error_type == 'credential':
            _display_credential_error(CredentialError(data['error'], data.get('admin_hint')))
        elif error_type == 'access':
            error = SheetAccessError(data['error'], data.get('admin_hint'))
            error.service_account_email = data.get('service_account_email')
            _display_sheet_access_error(error)
        elif error_type == 'network':
            _display_network_error(NetworkError(data['error']))
        elif error_type == 'empty_sheet':
            st.warning("⚠️ The access codes sheet is empty. Please add codes to the spreadsheet.")
        elif error_type == 'invalid_headers':
            st.error(f"⚠️ **Invalid Sheet Format**\n\n{data['error']}")
        else:
            st.error(f"❌ **Unexpected Error:** {data['error']}\n\nPlease contact support if this persists.")
        
        return False


def validate_and_mark_code(secret_code):
    """
    Validate a secret code and mark it as used if valid and unused.
    
    Supports roles:
    - STUDENT: Regular access, codes are marked as used
    - INSTRUCTOR: Infinite access, codes are NOT marked as used
    - DEVELOPER: Access to developer page, codes NOT auto-marked
    
    Args:
        secret_code (str): The secret code entered by the student
        
    Returns:
        dict: Result dictionary with keys:
            - success (bool): Whether the code was valid and successfully marked
            - message (str): User-friendly message
            - bot (str): Bot type (OHI, HPV, TOBACCO, PERIO, or DEVELOPER) if successful
            - name (str): Student name if successful
            - role (str): User role (STUDENT, INSTRUCTOR, or DEVELOPER)
    """
    if 'codes_data' not in st.session_state or 'error' in st.session_state.codes_data:
        return {
            'success': False,
            'message': 'Code data not loaded. Please refresh the data.',
            'bot': None,
            'name': None,
            'role': ROLE_STUDENT
        }
    
    rows = st.session_state.codes_data['rows']
    service_account_email = st.session_state.codes_data.get('service_account_email')
    
    # Find role column index if it exists
    header_lower = [h.strip().lower() for h in headers]
    role_col_idx = header_lower.index('role') if 'role' in header_lower else None
    
    # Search for the code in the data
    for row_idx, row in enumerate(rows):
        if len(row) < 5:
            continue
            
        table_no, name, bot, secret, used = row[0], row[1], row[2], row[3], row[4]
        
        # Get role if column exists
        role = ROLE_STUDENT
        if role_col_idx is not None and len(row) > role_col_idx:
            role = normalize_role(row[role_col_idx])
        
        # Check if this is the matching code
        if secret.strip() == secret_code.strip():
            # Check if already used (only matters for STUDENT role)
            used_value = used.strip().upper()
            is_used = used_value in ('TRUE', 'YES', '1')
            
            # Instructors and Developers can reuse codes
            if is_used and role == ROLE_STUDENT:
                return {
                    'success': False,
                    'message': 'This code has already been used. Please contact your instructor if you need a new code.',
                    'bot': None,
                    'name': None,
                    'role': role
                }
            
            # Normalize bot type
            bot_normalized = normalize_bot_type(bot)
            
            # Developer role redirects to developer page
            if role == ROLE_DEVELOPER:
                # Store auth info before any updates
                st.session_state.user_role = ROLE_DEVELOPER
                
                return {
                    'success': True,
                    'message': f'Welcome, {name}! Redirecting you to the Developer Tools page...',
                    'bot': 'DEVELOPER',
                    'name': name,
                    'role': ROLE_DEVELOPER
                }
            
            # Validate bot type for non-developer roles
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
                    'role': role
                }
            
            # Mark the code as used (row_idx + 2 because of 0-indexing and header row)
            try:
                # Get fresh worksheet for write operation
                client, _, _ = get_google_sheets_client()
                worksheet = open_sheet_with_retry(
                    client, SHEET_ID, SHEET_NAME,
                    service_account_email=service_account_email
                )
                
                # Update the "Used" column (column E, index 5) with retry logic
                cell_row = row_idx + 2
                cell_col = 5
                update_cell_with_retry(worksheet, cell_row, cell_col, 'TRUE')
                
                # Clear the cached sheet data so next load gets fresh data
                load_codes_from_sheet_cached.clear()
                
                return {
                    'success': True,
                    'message': f'Welcome, {name}! Redirecting you to the {bot_normalized} chatbot...',
                    'bot': bot_normalized,
                    'name': name
                }
            except SheetAccessError as e:
                return {
                    'success': False,
                    'message': f'Error marking code as used: {e.admin_hint or str(e)}',
                    'bot': None,
                    'name': None
                }
            except NetworkError as e:
                return {
                    'success': False,
                    'message': f'Network error marking code as used: {str(e)}. Please try again.',
                    'bot': None,
                    'name': None
                }
            except Exception as e:
                logger.exception("Unexpected error marking code as used")
                return {
                    'success': False,
                    'message': f'Error marking code as used: {str(e)}. Please try again.',
                    'bot': None,
                    'name': None
                }
    
    # Code not found
    return {
        'success': False,
        'message': 'Invalid code. Please check your code and try again.',
        'bot': None,
        'name': None,
        'role': ROLE_STUDENT
    }


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
    if 'load_error' not in st.session_state:
        st.session_state.load_error = False
    
    # Load data from Google Sheets on first run
    if 'codes_data' not in st.session_state or st.session_state.load_error:
        with st.spinner("Loading access codes from database..."):
            if not load_codes_from_sheet():
                st.session_state.load_error = True
                # Add a retry button for failed loads
                st.markdown("---")
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    if st.button("🔄 Retry Loading", type="primary", help="Try loading the database again"):
                        # Clear caches and retry
                        load_codes_from_sheet_cached.clear()
                        get_google_sheets_client.clear()
                        st.rerun()
                st.stop()
            else:
                st.session_state.load_error = False
    
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
                # Error messages are already displayed by load_codes_from_sheet
    
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
                        result = validate_and_mark_code(secret_code)
                        
                        if result['success']:
                            # Set session state for authentication and credentials
                            st.session_state.authenticated = True
                            st.session_state.redirect_info = {
                                'bot': result['bot'],
                                'name': result['name'],
                                'role': result.get('role', ROLE_STUDENT)
                            }
                            st.session_state.student_name = student_name
                            st.session_state.groq_api_key = groq_api_key
                            st.session_state.user_role = result.get('role', ROLE_STUDENT)
                            
                            # Set environment variable for libraries that need it
                            os.environ["GROQ_API_KEY"] = groq_api_key
                            
                            st.success(result['message'])
                            
                            # Navigate internally to the appropriate bot page
                            # Bot types are normalized to uppercase (OHI, HPV, TOBACCO, PERIO, DEVELOPER)
                            bot_type = result['bot']
                            try:
                                if bot_type in BOT_PAGE_MAP:
                                    st.switch_page(BOT_PAGE_MAP[bot_type])
                                else:
                                    # This shouldn't happen as bot_type is validated
                                    logger.error(f"Unexpected bot type '{bot_type}' not in BOT_PAGE_MAP")
                                    st.error(f"⚠️ Configuration Error: Unknown bot type '{bot_type}'.")
                            except StreamlitAPIException as e:
                                st.error(
                                    f"⚠️ Navigation Error: Could not find the {bot_type} chatbot page. "
                                    f"This may indicate a deployment issue. Please contact support."
                                )
                                st.info(
                                    "**Technical Details**: The page file `pages/{bot_type}.py` is missing or misconfigured. "
                                    "This should be resolved by the system administrator."
                                )
                        else:
                            st.error(result['message'])
    
    # Show success message if already authenticated (shouldn't normally be seen due to switch_page)
    if st.session_state.authenticated and st.session_state.redirect_info:
        redirect_info = st.session_state.redirect_info
        bot_type = redirect_info['bot']
        student_name = redirect_info.get('name', 'Student')
        
        st.success(f"✅ Access granted for {student_name}!")
        st.info(f"You have been assigned to the **{bot_type}** chatbot. Redirecting...")
        
        # Navigate internally to the appropriate bot page
        # Bot types are normalized to uppercase (OHI, HPV, TOBACCO, PERIO)
        try:
            if bot_type in BOT_PAGE_MAP:
                st.switch_page(BOT_PAGE_MAP[bot_type])
            else:
                # This shouldn't happen as bot_type is validated
                logger.error(f"Unexpected bot type '{bot_type}' not in BOT_PAGE_MAP")
                st.error(f"⚠️ Configuration Error: Unknown bot type '{bot_type}'.")
        except StreamlitAPIException as e:
            st.error(
                f"⚠️ Navigation Error: Could not find the {bot_type} chatbot page. "
                f"This may indicate a deployment issue. Please contact support."
            )
            st.info(
                "**Technical Details**: The page file `pages/{bot_type}.py` is missing or misconfigured. "
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
