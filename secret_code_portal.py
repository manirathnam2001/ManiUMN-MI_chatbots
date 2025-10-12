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

Requirements:
    - umnsod-mibot-ea3154b145f1.json service account file
    - Service account must have access to the Google Sheet
    - Internet connection for Google Sheets API calls
"""

import os
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
    
    Returns:
        gspread.Client: Authorized Google Sheets client
        
    Raises:
        Exception: If authentication fails or service account file is missing
    """
    try:
        # Check if service account file exists
        if not os.path.exists(SERVICE_ACCOUNT_FILE):
            raise FileNotFoundError(
                f"Service account file '{SERVICE_ACCOUNT_FILE}' not found. "
                "Please ensure the file is in the same directory as this script."
            )
        
        # Setup credentials with required scopes
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scope)
        
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
