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
    - Student name in session state
"""

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
from app_env import get_sheet_id, get_sheet_name, render_environment_banner

# Configure logging
logger = logging.getLogger(__name__)

# --- Streamlit page configuration ---
st.set_page_config(
    page_title="Developer Tools",
    page_icon="🛠️",
    layout="centered"
)

render_environment_banner()

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
if 'student_name' not in st.session_state:
    st.error("⚠️ Session Error: Missing student name.")
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
            SHEET_ID = get_sheet_id()
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
            from email_utils import send_box_backup_email
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

            result = send_box_backup_email(
                pdf_buffer=pdf_buffer,
                filename="test_email.pdf",
                student_name=st.session_state.get('student_name', 'Developer'),
                session_type="Developer Test",
            )

            if result.get('success'):
                st.success("✅ Test email sent successfully!")
            else:
                st.error(f"❌ Failed to send test email: {result.get('error', 'Unknown error')}")

        except ImportError as e:
            st.error(f"Import error: {str(e)}")
            st.info("Email functionality may not be configured. Check email_utils.py.")
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
            from mi_evaluation import EvaluationResult, REQUIRED_CATEGORIES
            from mi_pdf import construct_feedback_filename, generate_pdf_report
            from rubric.mi_rubric import MIRubric
            from time_utils import get_formatted_utc_time

            test_chat_history = [
                {"role": "assistant", "content": "Hello! I'm Alex, nice to meet you today."},
                {"role": "user", "content": "Hi Alex, how are you feeling about your oral hygiene?"},
                {"role": "assistant", "content": "Well, I brush sometimes but I'm not very consistent."},
                {"role": "user", "content": "I understand. What would help you be more consistent?"},
            ]

            # Synthesize a fully-Met EvaluationResult so the PDF pipeline runs end-to-end.
            categories = {
                cat: {
                    "assessment": "Fully Met",
                    "points": float(MIRubric.get_category_points(cat)),
                    "max_points": MIRubric.get_category_points(cat),
                    "rationale": "Test rationale.",
                    "evidence_quote": "",
                }
                for cat in REQUIRED_CATEGORIES
            }
            test_result: EvaluationResult = {
                "categories": categories,
                "total_score": float(MIRubric.get_total_possible()),
                "max_possible_score": MIRubric.get_total_possible(),
                "percentage": 100.0,
                "performance_band": MIRubric.get_performance_band(MIRubric.get_total_possible()),
                "recommendations": ["Continue building on these strengths in your next session."],
                "partial": False,
                "notes": "",
            }

            pdf_bytes = generate_pdf_report(
                test_result,
                student_name=st.session_state.get('student_name', 'Developer'),
                session_type="Developer Test",
                transcript=test_chat_history,
                timestamp_cst=get_formatted_utc_time(),
            )
            download_filename = construct_feedback_filename(
                st.session_state.get('student_name', 'Developer'),
                "TEST",
                "Developer",
            )

            st.success("✅ Test PDF generated successfully!")
            st.download_button(
                label="📥 Download Test PDF",
                data=pdf_bytes,
                file_name=download_filename,
                mime="application/pdf",
            )

        except ImportError as e:
            st.error(f"Import error: {str(e)}")
            st.info("Check that mi_pdf.py and mi_evaluation.py are available.")
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
                    SHEET_ID = get_sheet_id()
                    sheet = client.open_by_key(SHEET_ID)
                    worksheet = sheet.worksheet(get_sheet_name())
                    
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
        # Ensure redirect_info exists and set bot for access control
        if 'redirect_info' not in st.session_state:
            st.session_state.redirect_info = {}
        st.session_state.redirect_info['bot'] = 'OHI'
        st.switch_page("pages/OHI.py")
    
    if st.button("🧬 HPV (Vaccine Counseling)", use_container_width=True):
        # Ensure redirect_info exists and set bot for access control
        if 'redirect_info' not in st.session_state:
            st.session_state.redirect_info = {}
        st.session_state.redirect_info['bot'] = 'HPV'
        st.switch_page("pages/HPV.py")

with col2:
    if st.button("🚭 Tobacco Cessation", use_container_width=True):
        # Ensure redirect_info exists and set bot for access control
        if 'redirect_info' not in st.session_state:
            st.session_state.redirect_info = {}
        st.session_state.redirect_info['bot'] = 'TOBACCO'
        st.switch_page("pages/Tobacco.py")
    
    if st.button("🦷 Periodontitis", use_container_width=True):
        # Ensure redirect_info exists and set bot for access control
        if 'redirect_info' not in st.session_state:
            st.session_state.redirect_info = {}
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
