"""
Secret Code Portal - Student Access Gateway

This Streamlit application provides a secure entry point for students to access
the MI chatbots (OHI or HPV) using secret codes distributed by instructors.

Features:
- Code validation against Google Sheets database
- Automatic marking of codes as used
- Redirect to appropriate bot (OHI or HPV)
- Real-time data refresh capability
- Clear error messages for invalid or used codes

Google Sheet Structure:
- Sheet ID: 1x_MA3MqvyxN3p7v_mQ3xYB9SmEGPn1EspO0fUsYayFY
- Sheet Name: Sheet1
- Columns: Table No, Name, Bot, Secret, Used

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
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# --- Configuration ---
SHEET_ID = "1x_MA3MqvyxN3p7v_mQ3xYB9SmEGPn1EspO0fUsYayFY"
SHEET_NAME = "Sheet1"
SERVICE_ACCOUNT_FILE = "umnsod-mibot-ea3154b145f1.json"

# Bot URLs (update these with actual deployment URLs)
BOT_URLS = {
    "OHI": "https://ohimiapp.streamlit.app/",
    "HPV": "https://hpvmiapp.streamlit.app/"
}

# --- Streamlit page configuration ---
st.set_page_config(
    page_title="MI Chatbot Access Portal",
    page_icon="🔐",
    layout="centered"
)


def get_google_sheets_client():
    """
    Initialize and return Google Sheets client using service account credentials.
    
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


def load_codes_from_sheet(force_refresh=False):
    """
    Load secret codes from Google Sheet into session state.
    
    Args:
        force_refresh (bool): If True, force reload from Google Sheets even if data exists
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Use cached data if available and not forcing refresh
    if not force_refresh and 'codes_data' in st.session_state:
        return True
    
    try:
        # Get Google Sheets client
        client = get_google_sheets_client()
        
        # Open the spreadsheet
        sheet = client.open_by_key(SHEET_ID)
        worksheet = sheet.worksheet(SHEET_NAME)
        
        # Get all values from the sheet
        all_values = worksheet.get_all_values()
        
        if len(all_values) < 2:
            st.error("The Google Sheet appears to be empty or has no data rows.")
            return False
        
        # Parse the data (first row is headers)
        headers = all_values[0]
        data = all_values[1:]
        
        # Validate headers
        expected_headers = ['Table No', 'Name', 'Bot', 'Secret', 'Used']
        if headers != expected_headers:
            st.error(
                f"Invalid sheet format. Expected headers: {expected_headers}, "
                f"but found: {headers}"
            )
            return False
        
        # Store data in session state
        st.session_state.codes_data = {
            'worksheet': worksheet,
            'headers': headers,
            'rows': data
        }
        st.session_state.last_refresh = None
        
        return True
        
    except Exception as e:
        st.error(f"Error loading data from Google Sheets: {str(e)}")
        return False


def validate_and_mark_code(secret_code):
    """
    Validate a secret code and mark it as used if valid and unused.
    
    Args:
        secret_code (str): The secret code entered by the student
        
    Returns:
        dict: Result dictionary with keys:
            - success (bool): Whether the code was valid and successfully marked
            - message (str): User-friendly message
            - bot (str): Bot type (OHI or HPV) if successful
            - name (str): Student name if successful
    """
    if 'codes_data' not in st.session_state:
        return {
            'success': False,
            'message': 'Code data not loaded. Please refresh the data.',
            'bot': None,
            'name': None
        }
    
    worksheet = st.session_state.codes_data['worksheet']
    rows = st.session_state.codes_data['rows']
    
    # Search for the code in the data
    for row_idx, row in enumerate(rows):
        if len(row) < 5:
            continue
            
        table_no, name, bot, secret, used = row[0], row[1], row[2], row[3], row[4]
        
        # Check if this is the matching code
        if secret.strip() == secret_code.strip():
            # Check if already used
            if used.strip().upper() == 'TRUE' or used.strip().upper() == 'YES' or used.strip() == '1':
                return {
                    'success': False,
                    'message': 'This code has already been used. Please contact your instructor if you need a new code.',
                    'bot': None,
                    'name': None
                }
            
            # Validate bot type
            bot = bot.strip().upper()
            if bot not in ['OHI', 'HPV']:
                return {
                    'success': False,
                    'message': f'Invalid bot type "{bot}" in the sheet. Please contact your instructor.',
                    'bot': None,
                    'name': None
                }
            
            # Mark the code as used (row_idx + 2 because of 0-indexing and header row)
            try:
                # Update the "Used" column (column E, index 5)
                cell_row = row_idx + 2
                cell_col = 5
                worksheet.update_cell(cell_row, cell_col, 'TRUE')
                
                return {
                    'success': True,
                    'message': f'Welcome, {name}! Redirecting you to the {bot} chatbot...',
                    'bot': bot,
                    'name': name
                }
            except Exception as e:
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
        'name': None
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
        1. Enter your secret code in the box below
        2. Click "Submit Code" to verify your access
        3. You will be redirected to your assigned chatbot (OHI or HPV)
        
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
    
    # Refresh button
    st.markdown("---")
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        if st.button("🔄 Refresh Data", help="Reload codes from Google Sheets"):
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
            st.subheader("Enter Your Secret Code")
            
            secret_code = st.text_input(
                "Secret Code",
                type="password",
                placeholder="Enter your secret code here",
                help="The secret code provided by your instructor"
            )
            
            submit_button = st.form_submit_button("Submit Code", type="primary")
            
            if submit_button:
                if not secret_code:
                    st.error("Please enter a secret code.")
                else:
                    with st.spinner("Verifying your code..."):
                        result = validate_and_mark_code(secret_code)
                        
                        if result['success']:
                            st.session_state.authenticated = True
                            st.session_state.redirect_info = {
                                'bot': result['bot'],
                                'name': result['name']
                            }
                            st.success(result['message'])
                            st.rerun()
                        else:
                            st.error(result['message'])
    
    # Show redirect information and button
    if st.session_state.authenticated and st.session_state.redirect_info:
        redirect_info = st.session_state.redirect_info
        bot_type = redirect_info['bot']
        student_name = redirect_info['name']
        bot_url = BOT_URLS.get(bot_type)
        
        st.success(f"✅ Access granted for {student_name}!")
        
        st.markdown(f"### You have been assigned to the **{bot_type}** chatbot")
        
        st.info(
            f"""
            **Ready to start your practice session?**
            
            Click the button below to access the {bot_type} Motivational Interviewing practice chatbot.
            """
        )
        
        # Redirect button
        if bot_url:
            st.markdown(
                f'<a href="{bot_url}" target="_self"><button style="'
                f'background-color: #FF4B4B; color: white; padding: 12px 24px; '
                f'border: none; border-radius: 4px; font-size: 16px; cursor: pointer; '
                f'font-weight: bold;">Go to {bot_type} Chatbot →</button></a>',
                unsafe_allow_html=True
            )
            
            st.markdown("---")
            st.markdown(
                f"**Alternative:** If the button doesn't work, copy and paste this URL into your browser:\n\n"
                f"`{bot_url}`"
            )
        else:
            st.error(f"Bot URL not configured for {bot_type}. Please contact support.")
    
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
