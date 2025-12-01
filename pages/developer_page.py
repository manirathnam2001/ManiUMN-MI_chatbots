"""
Developer Page - Testing Utilities for Developers

This Streamlit page provides testing utilities for developers with authenticated
Developer role access. It allows testing of:
- Email sending functionality
- PDF report generation
- Google Sheets code marking

Requirements:
- User must be authenticated via secret code portal
- User must have DEVELOPER role (st.session_state.user_role == "DEVELOPER")

Usage:
    Access via the secret code portal with a Developer access code
"""

import io
import streamlit as st

# Page configuration
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

# Check if user has DEVELOPER role
user_role = st.session_state.get('user_role', '')
if user_role != 'DEVELOPER':
    st.error("⚠️ Access Denied: This page requires Developer access.")
    st.info(f"Your current role is: {user_role or 'Unknown'}")
    if st.button("← Return to Portal"):
        st.switch_page("secret_code_portal.py")
    st.stop()

# --- Page Content ---
st.title("🛠️ Developer Tools")
st.markdown("""
Welcome to the **Developer Tools** page. This page provides testing utilities
for verifying system functionality.

Use the buttons below to test various system components.
""")

st.markdown("---")

# --- Test Email Section ---
st.subheader("📧 Send Test Email")
st.markdown("Test the email sending functionality by sending a test email.")

with st.expander("Email Test Options", expanded=False):
    test_recipient = st.text_input(
        "Test Recipient Email",
        placeholder="test@example.com",
        help="Enter an email address to receive the test email"
    )
    
    if st.button("Send test email", key="btn_test_email"):
        if not test_recipient:
            st.warning("Please enter a recipient email address.")
        else:
            with st.spinner("Sending test email..."):
                try:
                    from email_utils import SecureEmailSender
                    import json
                    
                    # Load config
                    try:
                        with open('config.json', 'r') as f:
                            config = json.load(f)
                    except FileNotFoundError:
                        config = {}
                    
                    sender = SecureEmailSender(config)
                    result = sender.test_connection()
                    
                    if result['status'] == 'success':
                        st.success(f"✅ Email connection test successful!")
                        st.json(result)
                    else:
                        st.warning(f"⚠️ Email connection test returned: {result['status']}")
                        st.json(result)
                        
                except ImportError as e:
                    st.error(f"❌ Email utilities not available: {e}")
                except Exception as e:
                    st.error(f"❌ Error testing email: {e}")

st.markdown("---")

# --- Test PDF Section ---
st.subheader("📄 Generate Test PDF")
st.markdown("Generate a sample PDF report to test the PDF generation functionality.")

if st.button("Generate test PDF", key="btn_test_pdf"):
    with st.spinner("Generating test PDF..."):
        try:
            from pdf_utils import generate_pdf_report
            from feedback_template import FeedbackFormatter
            
            # Create sample feedback content
            sample_feedback = """Session Feedback
            
Evaluation Timestamp (Minnesota): 2025-01-01 12:00:00 CST

**Collaboration (7/9 points)**
The interviewer demonstrated good collaborative skills...

**Evocation (5/6 points)**
Good use of open-ended questions...

**Acceptance (5/6 points)**
Showed respect for patient autonomy...

**Compassion (5/6 points)**
Demonstrated empathy and understanding...

**Summary (2/3 points)**
Provided a basic summary...

**Response Factor (8/10 points)**
Maintained appropriate response length...

Total Score: 32/40 (80%)
Performance Band: Proficient

Improvement Suggestions:
- Continue building on reflective listening skills
- Try more complex reflections to deepen the conversation
"""
            
            sample_chat_history = [
                {"role": "assistant", "content": "Hello! I'm a test patient. How can I help you today?"},
                {"role": "user", "content": "I'm here to practice my motivational interviewing skills."},
                {"role": "assistant", "content": "I see. Well, I've been thinking about my health lately."},
                {"role": "user", "content": "Tell me more about what's been on your mind."},
            ]
            
            # Generate PDF
            pdf_buffer = generate_pdf_report(
                student_name="Test Developer",
                raw_feedback=sample_feedback,
                chat_history=sample_chat_history,
                session_type="Test Session"
            )
            
            # Generate filename
            download_filename = FeedbackFormatter.create_download_filename(
                "Test_Developer", "Test", "SamplePersona"
            )
            
            st.success("✅ Test PDF generated successfully!")
            
            # Download button
            st.download_button(
                label="📥 Download Test PDF",
                data=pdf_buffer.getvalue(),
                file_name=download_filename,
                mime="application/pdf",
                help="Download the generated test PDF"
            )
            
        except ImportError as e:
            st.error(f"❌ PDF utilities not available: {e}")
        except Exception as e:
            st.error(f"❌ Error generating PDF: {e}")
            import traceback
            st.code(traceback.format_exc())

st.markdown("---")

# --- Mark Code Used Section ---
st.subheader("📋 Mark Code Used in Sheet")
st.markdown("Test the Google Sheets integration by marking a code as used.")

with st.expander("Sheet Test Options", expanded=False):
    code_to_mark = st.text_input(
        "Secret Code to Mark",
        placeholder="Enter a secret code",
        help="Enter the secret code you want to mark as used in the sheet"
    )
    
    st.warning("⚠️ This will actually mark the code as used in the Google Sheet!")
    
    if st.button("Mark code used in Sheet", key="btn_mark_code"):
        if not code_to_mark:
            st.warning("Please enter a code to mark.")
        else:
            with st.spinner("Marking code as used..."):
                try:
                    from utils.access_control import get_sheet_client, find_code_row, mark_row_used
                    
                    # Get the sheet
                    client = get_sheet_client()
                    sheet = client.open_by_key("1x_MA3MqvyxN3p7v_mQ3xYB9SmEGPn1EspO0fUsYayFY")
                    worksheet = sheet.worksheet("Sheet1")
                    
                    # Find the code
                    result = find_code_row(worksheet, code_to_mark)
                    
                    if result is None:
                        st.warning(f"⚠️ Code '{code_to_mark}' not found in the sheet.")
                    else:
                        row_index, row_data = result
                        st.info(f"Found code in row {row_index}")
                        st.json(row_data)
                        
                        # Mark as used
                        success = mark_row_used(worksheet, row_index)
                        
                        if success:
                            st.success(f"✅ Successfully marked code in row {row_index} as used!")
                        else:
                            st.error("❌ Failed to mark code as used.")
                            
                except ImportError as e:
                    st.error(f"❌ Access control utilities not available: {e}")
                except Exception as e:
                    st.error(f"❌ Error accessing sheet: {e}")
                    import traceback
                    st.code(traceback.format_exc())

st.markdown("---")

# --- Session Info ---
st.subheader("ℹ️ Session Information")
with st.expander("View Session State", expanded=False):
    safe_session = {
        'authenticated': st.session_state.get('authenticated', False),
        'user_role': st.session_state.get('user_role', 'Unknown'),
        'student_name': st.session_state.get('student_name', 'Unknown'),
        'redirect_info': st.session_state.get('redirect_info', {}),
        # Don't show sensitive info like API keys
    }
    st.json(safe_session)

# --- Navigation ---
st.markdown("---")
col1, col2 = st.columns(2)
with col1:
    if st.button("← Return to Portal"):
        st.switch_page("secret_code_portal.py")
with col2:
    st.markdown("*Developer access does not expire*")
