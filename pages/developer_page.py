"""
Developer Page - Test Utilities for MI Chatbot Portal

This page provides test utilities for developers to:
- Send test emails
- Generate test PDFs
- Mark codes as used in the sheet
- Test sheet connectivity

Access requires DEVELOPER role from the secret code portal.

Usage:
    This page is part of a multipage app. Access via the portal with a Developer role code.

Requirements:
    - Authentication via secret code portal with DEVELOPER role
    - Groq API key and student name from session state
"""

import os
import logging
import streamlit as st

# Import from centralized access control module
from utils.access_control import (
    get_sheet_client,
    check_sheet_permission,
    ROLE_DEVELOPER,
    ROLE_INSTRUCTOR,
    SheetAccessError,
    CredentialError,
)

# Configure logging
logger = logging.getLogger(__name__)

# --- Streamlit page configuration ---
st.set_page_config(
    page_title="Developer Tools",
    page_icon="🛠️",
    layout="centered"
)

# --- AUTHENTICATION GUARD ---
# Check if user is authenticated
if not st.session_state.get('authenticated', False):
    st.error("⚠️ Access Denied: You must enter through the secret code portal.")
    st.info("Please go back to the main portal and enter your secret code.")
    if st.button("← Return to Portal"):
        st.switch_page("secret_code_portal.py")
    st.stop()

# Check if user has Developer role
user_role = st.session_state.get('user_role', 'STUDENT')
redirect_info = st.session_state.get('redirect_info', {})

# Allow both DEVELOPER and INSTRUCTOR roles to access developer tools
if user_role not in (ROLE_DEVELOPER, ROLE_INSTRUCTOR):
    st.error("⚠️ Access Denied: This page requires Developer or Instructor access.")
    st.info(f"Your current role: {user_role}")
    if st.button("← Return to Portal"):
        st.switch_page("secret_code_portal.py")
    st.stop()

# Check if credentials are available
if 'groq_api_key' not in st.session_state or 'student_name' not in st.session_state:
    st.error("⚠️ Session Error: Missing credentials.")
    st.info("Please go back to the portal and re-enter your information.")
    if st.button("← Return to Portal"):
        st.switch_page("secret_code_portal.py")
    st.stop()

# --- UI: Title ---
st.title("🛠️ Developer Tools")

st.markdown(f"""
Welcome to the **Developer Tools** page!

**Current User:** {st.session_state.get('student_name', 'Unknown')}  
**Role:** {user_role}

This page provides test utilities for developers and instructors to:
- Test sheet connectivity
- Send test emails
- Generate test PDFs
- Manually mark codes as used
""")

st.markdown("---")

# --- Sheet Connection Test ---
st.header("📊 Google Sheets Connection Test")

if st.button("Test Sheet Connection"):
    with st.spinner("Testing connection to Google Sheets..."):
        try:
            client, creds_source, service_email = get_sheet_client(st.secrets)
            st.success(f"✅ Successfully connected to Google Sheets!")
            st.info(f"Credentials source: {creds_source}")
            if service_email:
                st.info(f"Service account: {service_email}")
            
            # Try to access the sheet
            SHEET_ID = "1x_MA3MqvyxN3p7v_mQ3xYB9SmEGPn1EspO0fUsYayFY"
            try:
                sheet = check_sheet_permission(client, SHEET_ID, service_email)
                st.success(f"✅ Successfully accessed the access codes spreadsheet!")
                worksheets = sheet.worksheets()
                st.info(f"Available worksheets: {[ws.title for ws in worksheets]}")
            except SheetAccessError as e:
                st.error(f"Permission error: {str(e)}")
                
        except (SheetAccessError, CredentialError) as e:
            st.error(f"Connection failed: {str(e)}")
        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")

st.markdown("---")

# --- Test Email ---
st.header("📧 Test Email")

st.markdown("""
Test the email functionality by sending a test email to the Box backup address.
""")

test_email_recipient = st.text_input(
    "Test Email Recipient (optional)",
    placeholder="Leave blank to use default Box email",
    help="Enter an email address to receive the test email"
)

if st.button("Send Test Email"):
    with st.spinner("Sending test email..."):
        try:
            from pdf_utils import send_pdf_to_box
            from io import BytesIO
            from reportlab.pdfgen import canvas
            
            # Create a simple test PDF
            pdf_buffer = BytesIO()
            c = canvas.Canvas(pdf_buffer)
            c.drawString(100, 750, "MI Chatbot Portal - Test Email")
            c.drawString(100, 700, f"Sent by: {st.session_state.get('student_name', 'Developer')}")
            c.drawString(100, 650, "This is a test email from the Developer Tools page.")
            c.save()
            pdf_buffer.seek(0)
            
            result = send_pdf_to_box(
                pdf_buffer=pdf_buffer,
                filename="test_email.pdf",
                student_name=st.session_state.get('student_name', 'Developer'),
                session_type="Developer Test"
            )
            
            if result['success']:
                st.success("✅ Test email sent successfully!")
            else:
                st.error(f"❌ Failed to send test email: {result.get('error', 'Unknown error')}")
                
        except ImportError as e:
            st.error(f"Import error: {str(e)}")
            st.info("Email functionality may not be configured. Check pdf_utils.py and email_utils.py")
        except Exception as e:
            st.error(f"Error sending test email: {str(e)}")

st.markdown("---")

# --- Test PDF Generation ---
st.header("📄 Test PDF Generation")

st.markdown("""
Test the PDF generation functionality by creating a sample feedback report.
""")

if st.button("Generate Test PDF"):
    with st.spinner("Generating test PDF..."):
        try:
            from pdf_utils import generate_pdf_report
            from feedback_template import FeedbackFormatter
            
            # Create test data
            test_feedback = """
            ## MI Conversation Feedback (Test)
            
            ### Overall Score: 25/30
            
            **Strengths:**
            - Good use of open-ended questions
            - Demonstrated empathy and active listening
            - Appropriate reflection of patient statements
            
            **Areas for Improvement:**
            - Could explore ambivalence more deeply
            - Consider using more affirmations
            - Work on summarizing key points at the end
            
            This is a test PDF generated from the Developer Tools page.
            """
            
            test_chat_history = [
                {"role": "assistant", "content": "Hello! I'm Alex, nice to meet you today."},
                {"role": "user", "content": "Hi Alex, how are you feeling about your oral hygiene?"},
                {"role": "assistant", "content": "Well, I brush sometimes but I'm not very consistent."},
                {"role": "user", "content": "I understand. What would help you be more consistent?"},
            ]
            
            # Format feedback
            from time_utils import get_formatted_utc_time
            formatted_feedback = FeedbackFormatter.format_feedback_for_pdf(
                test_feedback,
                get_formatted_utc_time(),
                "Developer Test Bot"
            )
            
            # Generate PDF
            pdf_buffer = generate_pdf_report(
                student_name=st.session_state.get('student_name', 'Developer'),
                raw_feedback=formatted_feedback,
                chat_history=test_chat_history,
                session_type="Developer Test"
            )
            
            # Provide download
            download_filename = FeedbackFormatter.create_download_filename(
                st.session_state.get('student_name', 'Developer'),
                "TEST",
                "Developer"
            )
            
            st.success("✅ Test PDF generated successfully!")
            st.download_button(
                label="📥 Download Test PDF",
                data=pdf_buffer.getvalue(),
                file_name=download_filename,
                mime="application/pdf"
            )
            
        except ImportError as e:
            st.error(f"Import error: {str(e)}")
            st.info("Check that pdf_utils.py and feedback_template.py are available.")
        except Exception as e:
            st.error(f"Error generating PDF: {str(e)}")

st.markdown("---")

# --- Manual Code Mark ---
st.header("✏️ Manual Code Operations")

st.markdown("""
Manually mark a specific code as used or unused in the sheet.
**Use with caution!** This directly modifies the access codes database.
""")

with st.form("mark_code_form"):
    row_number = st.number_input(
        "Row Number (1-based, including header)",
        min_value=2,
        value=2,
        help="The row number in the sheet to update (row 1 is header)"
    )
    
    mark_as = st.selectbox(
        "Mark As",
        ["TRUE", "FALSE"],
        help="Set the Used column value"
    )
    
    confirm_mark = st.checkbox("I understand this will modify the sheet")
    
    submit_mark = st.form_submit_button("Update Sheet")
    
    if submit_mark:
        if not confirm_mark:
            st.warning("Please confirm the operation by checking the checkbox.")
        else:
            with st.spinner("Updating sheet..."):
                try:
                    client, _, _ = get_sheet_client(st.secrets)
                    SHEET_ID = "1x_MA3MqvyxN3p7v_mQ3xYB9SmEGPn1EspO0fUsYayFY"
                    sheet = client.open_by_key(SHEET_ID)
                    worksheet = sheet.worksheet("Sheet1")
                    
                    # Update the Used column (column 5)
                    worksheet.update_cell(row_number, 5, mark_as)
                    
                    st.success(f"✅ Row {row_number} updated: Used = {mark_as}")
                    st.info("Note: The cache will be refreshed on the next portal load.")
                    
                except SheetAccessError as e:
                    st.error(f"Sheet access error: {str(e)}")
                except Exception as e:
                    st.error(f"Error updating sheet: {str(e)}")

st.markdown("---")

# --- Bot Access ---
st.header("🤖 Access Chatbots")

st.markdown("""
Quickly navigate to any of the MI practice chatbots for testing.
""")

col1, col2 = st.columns(2)

with col1:
    if st.button("🦷 OHI (Oral Hygiene)", use_container_width=True):
        # Set redirect info to allow access to OHI bot
        st.session_state.redirect_info['bot'] = 'OHI'
        st.switch_page("pages/OHI.py")
    
    if st.button("🧬 HPV (Vaccine Counseling)", use_container_width=True):
        # Set redirect info to allow access to HPV bot
        st.session_state.redirect_info['bot'] = 'HPV'
        st.switch_page("pages/HPV.py")

with col2:
    if st.button("🚭 Tobacco Cessation", use_container_width=True):
        # Set redirect info to allow access to Tobacco bot
        st.session_state.redirect_info['bot'] = 'TOBACCO'
        st.switch_page("pages/Tobacco.py")
    
    if st.button("🦷 Periodontitis", use_container_width=True):
        # Set redirect info to allow access to Perio bot
        st.session_state.redirect_info['bot'] = 'PERIO'
        st.switch_page("pages/Perio.py")

st.markdown("---")

# --- Session Info ---
st.header("ℹ️ Session Information")

with st.expander("View Session State"):
    # Display non-sensitive session state info
    safe_keys = ['authenticated', 'user_role', 'student_name', 'redirect_info', 'googlesa_source']
    for key in safe_keys:
        if key in st.session_state:
            st.write(f"**{key}:** {st.session_state[key]}")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; font-size: 14px;'>
    <p>Developer Tools - For testing and debugging purposes</p>
    <p>© 2025 UMN School of Dentistry - MI Practice Portal</p>
    </div>
    """,
    unsafe_allow_html=True
)

# Return to Portal button
if st.button("← Return to Portal"):
    st.switch_page("secret_code_portal.py")
