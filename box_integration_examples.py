"""
Example: How to integrate Box upload into HPV.py and OHI.py

This file demonstrates how to add Box upload functionality to the existing
Streamlit MI chatbot applications with minimal code changes.
"""

# ============================================================================
# EXAMPLE 1: Simple Integration - Add to PDF Download Section
# ============================================================================
# Add this import at the top of HPV.py or OHI.py:

from box_streamlit_helpers import add_box_upload_button

# Then in the PDF download section (after st.download_button), add:
"""
# After the download button, add Box upload option
if pdf_buffer:
    add_box_upload_button(
        pdf_buffer=pdf_buffer,
        filename=f"{session_type}_Report_{student_name}",
        student_name=student_name,
        session_type=session_type
    )
"""

# ============================================================================
# EXAMPLE 2: Complete Integration in PDF Section
# ============================================================================
# Replace the PDF download section in HPV.py with:

"""
# PDF Generation section
if st.session_state.feedback is not None:
    feedback_data = st.session_state.feedback
    
    # Format feedback for PDF using standardized template
    formatted_feedback = FeedbackFormatter.format_feedback_for_pdf(
        feedback_data['content'],
        feedback_data['timestamp'],
        feedback_data['evaluator']
    )
    
    try:
        # Generate PDF
        pdf_buffer = generate_pdf_report(
            student_name=st.session_state.student_name,
            raw_feedback=formatted_feedback,
            chat_history=st.session_state.messages,
            session_type="HPV Vaccine"
        )
        
        # Download button
        st.download_button(
            label="📥 Download PDF Report",
            data=pdf_buffer,
            file_name=f"HPV_MI_Feedback_Report_{st.session_state.student_name}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
        
        # Box upload button (NEW)
        from box_streamlit_helpers import add_box_upload_button
        add_box_upload_button(
            pdf_buffer=pdf_buffer,
            filename=f"HPV_MI_Report_{st.session_state.student_name}",
            student_name=st.session_state.student_name,
            session_type="HPV Vaccine"
        )
        
    except ValueError as e:
        st.error(f"Error generating PDF: {e}")
        st.info("Please check your student name and try again.")
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        st.info("There was an issue generating the PDF. Please try again.")
"""

# ============================================================================
# EXAMPLE 3: Show Box Status in Sidebar
# ============================================================================
# Add this to the sidebar section of your app:

"""
from box_streamlit_helpers import show_box_upload_in_sidebar

# At the beginning of your app, after st.set_page_config():
show_box_upload_in_sidebar()
"""

# ============================================================================
# EXAMPLE 4: Direct Upload (Without Streamlit Helpers)
# ============================================================================
# For non-Streamlit scripts or custom integrations:

"""
from pdf_utils import generate_pdf_report, upload_pdf_to_box, BoxUploadError
from box_config import BoxConfig

# Generate PDF
pdf_buffer = generate_pdf_report(
    student_name="John Doe",
    raw_feedback=feedback_text,
    chat_history=chat_history,
    session_type="HPV Vaccine"
)

# Upload to Box
try:
    config = BoxConfig()
    if config.is_configured():
        success, message = upload_pdf_to_box(
            pdf_buffer,
            filename="HPV_Report_John_Doe.pdf",
            config=config
        )
        if success:
            print(f"Success: {message}")
        else:
            print(f"Failed: {message}")
    else:
        print(f"Box not configured. Missing: {config.get_missing_settings()}")
except BoxUploadError as e:
    print(f"Upload error: {e}")
"""

# ============================================================================
# EXAMPLE 5: Batch Upload for Multiple Reports
# ============================================================================

"""
from pdf_utils import generate_pdf_report, upload_pdf_to_box, BoxUploadError
from box_config import BoxConfig

# Generate multiple reports
students = ["Alice", "Bob", "Charlie"]
reports = []

for student in students:
    pdf = generate_pdf_report(
        student_name=student,
        raw_feedback=feedback[student],
        chat_history=histories[student],
        session_type="HPV Vaccine"
    )
    reports.append((student, pdf))

# Upload all to Box
config = BoxConfig()
results = []

for student, pdf in reports:
    try:
        success, msg = upload_pdf_to_box(
            pdf,
            f"HPV_Report_{student}.pdf",
            config=config
        )
        results.append((student, success, msg))
    except BoxUploadError as e:
        results.append((student, False, str(e)))

# Show results
for student, success, msg in results:
    status = "✓" if success else "✗"
    print(f"{status} {student}: {msg}")
"""

# ============================================================================
# EXAMPLE 6: Custom Email Content
# ============================================================================

"""
from pdf_utils import upload_pdf_to_box
from box_config import BoxConfig

# Upload with custom email subject and body
config = BoxConfig()
success, msg = upload_pdf_to_box(
    pdf_buffer,
    filename="report.pdf",
    config=config,
    subject="MI Assessment - HPV Session - John Doe",
    body=\"\"\"
    Attached is the MI Assessment PDF Report for John Doe.
    
    Session: HPV Vaccine Discussion
    Date: 2024-01-15
    Score: 85% (Very Good)
    
    This file has been automatically uploaded to Box storage.
    \"\"\"
)
"""

# ============================================================================
# EXAMPLE 7: Error Handling and User Feedback
# ============================================================================

"""
import streamlit as st
from pdf_utils import upload_pdf_to_box, BoxUploadError
from box_config import BoxConfig

# Check configuration first
config = BoxConfig()

if st.button("Upload to Box"):
    if not config.is_configured():
        missing = config.get_missing_settings()
        st.error(f"Box upload not configured. Missing: {', '.join(missing)}")
        with st.expander("How to configure"):
            st.code('''
export SMTP_USERNAME="your-email@example.com"
export SMTP_PASSWORD="your-app-password"
            ''')
    else:
        try:
            with st.spinner("Uploading..."):
                success, msg = upload_pdf_to_box(pdf_buffer, "report.pdf")
                if success:
                    st.success(msg)
                    st.balloons()
                else:
                    st.error(msg)
        except BoxUploadError as e:
            st.error(f"Upload failed: {e}")
            if "authentication" in str(e).lower():
                st.info("Check your SMTP credentials. For Gmail, use an App Password.")
"""

# ============================================================================
# CONFIGURATION EXAMPLES
# ============================================================================

"""
# Example 1: Using environment variables (recommended)
export SMTP_USERNAME="myapp@example.com"
export SMTP_PASSWORD="app-specific-password"
export SMTP_HOST="smtp.gmail.com"
export SMTP_PORT="587"

# Example 2: Using .env file (requires python-dotenv)
# Create a .env file:
SMTP_USERNAME=myapp@example.com
SMTP_PASSWORD=app-specific-password

# Load in your app:
from dotenv import load_dotenv
load_dotenv()

# Example 3: Streamlit secrets (for Streamlit Cloud)
# Create .streamlit/secrets.toml:
[email]
SMTP_USERNAME = "myapp@example.com"
SMTP_PASSWORD = "app-specific-password"

# Access in app:
import os
os.environ["SMTP_USERNAME"] = st.secrets["email"]["SMTP_USERNAME"]
os.environ["SMTP_PASSWORD"] = st.secrets["email"]["SMTP_PASSWORD"]
"""

# ============================================================================
# MINIMAL CHANGES SUMMARY
# ============================================================================
"""
To add Box upload to existing apps, you only need to:

1. Add one import line:
   from box_streamlit_helpers import add_box_upload_button

2. Add one function call after PDF generation:
   add_box_upload_button(pdf_buffer, filename, student_name, session_type)

3. Set environment variables before running:
   export SMTP_USERNAME="your-email@example.com"
   export SMTP_PASSWORD="your-app-password"

That's it! The helper handles all UI, error messages, and upload logic.
"""

print(__doc__)
