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
- Robust gspread client with version compatibility
- Admin-friendly error messages with actionable guidance

Roles:
- STUDENT: Regular access, codes are marked as used
- INSTRUCTOR: Infinite access, codes are NOT marked as used
- DEVELOPER: Access to developer page with test utilities, codes NOT auto-marked

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

# Import from centralized access control module
from utils.access_control import (
    get_sheet_client,
    normalize_role,
    normalize_bot_type,
    find_code_row,
    mark_row_used,
    check_sheet_permission,
    VALID_BOT_TYPES,
    ROLE_INSTRUCTOR,
    ROLE_DEVELOPER,
    ROLE_STUDENT,
    SheetClientError,
    MissingSecretsError,
    MalformedSecretsError,
    PermissionDeniedError,
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
    
    Uses the centralized access control module which supports:
    1. gspread.service_account_from_dict (gspread >= 5.0)
    2. google.oauth2 Credentials + gspread.authorize (fallback)
    
    Returns:
        gspread.Client: Authorized Google Sheets client
        
    Raises:
        SheetClientError subclass with admin-friendly messages
    """
    client, creds_source, service_account_email = _get_cached_client()
    
    # Store credentials source for debugging
    if creds_source:
        st.session_state["googlesa_source"] = creds_source
    if service_account_email:
        st.session_state["service_account_email"] = service_account_email
    
    return client


def display_admin_error(error: SheetClientError):
    """
    Display admin-friendly error message with actionable guidance.
    
    Args:
        error: SheetClientError subclass with error details
    """
    st.error("⚠️ Configuration Error")
    
    if isinstance(error, MissingSecretsError):
        st.warning("**No Google Sheets credentials found.**")
        st.markdown("""
        **Administrators:** Please configure one of the following:
        
        1. **Streamlit secrets** (recommended for Streamlit Cloud):
           - `st.secrets["GOOGLESA"]` - TOML table or JSON string
           - `st.secrets["GOOGLESA_B64"]` - base64-encoded JSON
        
        2. **Environment variables**:
           - `GOOGLESA_B64` - base64-encoded JSON (recommended)
           - `GOOGLESA` - JSON string with escaped newlines
        
        3. **Service account file**:
           - `umnsod-mibot-ea3154b145f1.json` (for local development)
        """)
        
    elif isinstance(error, MalformedSecretsError):
        st.warning(f"**Malformed credentials in {error.source}**")
        st.markdown(f"Error: `{error.detail}`")
        st.markdown("""
        **Common fixes:**
        - For JSON strings: Escape newlines in `private_key` as `\\n`
        - For GOOGLESA_B64: Run `cat service-account.json | base64 -w 0`
        - For TOML tables: Use multi-line strings with `'''` for private_key
        """)
        
    elif isinstance(error, PermissionDeniedError):
        st.warning("**Permission denied when accessing spreadsheet.**")
        service_email = getattr(error, 'service_account_email', None)
        if service_email:
            st.markdown(f"""
            **Share the spreadsheet with this service account:**
            
            📧 `{service_email}`
            
            1. Open the spreadsheet in Google Sheets
            2. Click "Share" in the top right
            3. Paste the email above and grant "Editor" access
            4. Click "Share"
            """)
        else:
            st.markdown("""
            Please ensure the service account has access to the spreadsheet.
            Check the ADMIN_GUIDE.md for detailed instructions.
            """)
    
    # Show retry button
    if st.button("🔄 Retry Connection"):
        # Clear the client cache and try again
        get_google_sheets_client.clear()
        st.rerun()


@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_codes_from_sheet_cached(_client):
    """
    Load secret codes from Google Sheet. Cached to reduce API calls.
    
    Args:
        _client: gspread.Client (underscore prefix tells Streamlit not to hash it)
    
    Returns:
        dict: Dictionary with 'worksheet', 'headers', 'rows' keys
        
    Raises:
        PermissionDeniedError: If access is denied
        Exception: For other errors
    """
    # Check permission and open the spreadsheet
    sheet = check_sheet_permission(
        _client, 
        SHEET_ID, 
        st.session_state.get("service_account_email")
    )
    worksheet = sheet.worksheet(SHEET_NAME)
    
    # Get all values from the sheet
    all_values = worksheet.get_all_values()
    
    if len(all_values) < 2:
        raise ValueError("Sheet is empty or has only headers")
    
    # Parse the data (first row is headers)
    headers = all_values[0]
    data = all_values[1:]
    
    # Validate required headers (Role is optional)
    required_headers = ['Table No', 'Name', 'Bot', 'Secret', 'Used']
    header_lower = [h.strip().lower() for h in headers]
    for req in required_headers:
        if req.lower() not in header_lower:
            raise ValueError(f"Missing required column: {req}")
    
    # Return data structure
    return {
        'worksheet': worksheet,
        'headers': headers,
        'rows': data
    }


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
    
    try:
        # Get client first (may raise SheetClientError)
        client = get_google_sheets_client()
        
        # Load from cached function
        data = load_codes_from_sheet_cached(client)
        
        # Store data in session state
        st.session_state.codes_data = data
        st.session_state.last_refresh = None
        
        return True
        
    except SheetClientError as e:
        # Display admin-friendly error for credential/permission issues
        display_admin_error(e)
        return False
        
    except ValueError as e:
        # Sheet structure issues
        st.error(f"⚠️ Sheet Structure Error: {str(e)}")
        st.info("Please verify the sheet has the correct columns: Table No, Name, Bot, Secret, Used, Role (optional)")
        return False
        
    except Exception as e:
        # Generic error
        logger.error(f"Error loading codes: {e}")
        st.error("Failed to load code database.")
        st.info("Please refresh the page or contact support.")
        if st.button("🔄 Retry"):
            get_google_sheets_client.clear()
            load_codes_from_sheet_cached.clear()
            st.rerun()
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
    if 'codes_data' not in st.session_state:
        return {
            'success': False,
            'message': 'Code data not loaded. Please refresh the data.',
            'bot': None,
            'name': None,
            'role': ROLE_STUDENT
        }
    
    worksheet = st.session_state.codes_data['worksheet']
    headers = st.session_state.codes_data['headers']
    rows = st.session_state.codes_data['rows']
    
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
            
            # Mark the code as used ONLY for STUDENT role
            # Instructor and Developer roles do not mark codes as used
            if role == ROLE_STUDENT:
                try:
                    # Update the "Used" column (column E, index 5)
                    cell_row = row_idx + 2  # +2 for 0-index and header
                    if mark_row_used(worksheet, cell_row, used_column=5):
                        # Invalidate cache after successful update
                        load_codes_from_sheet_cached.clear()
                    else:
                        return {
                            'success': False,
                            'message': 'Error marking code as used. Please try again.',
                            'bot': None,
                            'name': None,
                            'role': role
                        }
                except Exception as e:
                    logger.error(f"Error marking code as used: {e}")
                    return {
                        'success': False,
                        'message': f'Error marking code as used: {str(e)}. Please try again.',
                        'bot': None,
                        'name': None,
                        'role': role
                    }
            
            # Store user role in session
            st.session_state.user_role = role
            
            # Success message varies by role
            if role == ROLE_INSTRUCTOR:
                message = f'Welcome, Instructor {name}! Redirecting you to the {bot_normalized} chatbot... (Infinite access enabled)'
            else:
                message = f'Welcome, {name}! Redirecting you to the {bot_normalized} chatbot...'
            
            return {
                'success': True,
                'message': message,
                'bot': bot_normalized,
                'name': name,
                'role': role
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
