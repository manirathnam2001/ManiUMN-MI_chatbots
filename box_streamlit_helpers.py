"""
Helper functions for integrating Box upload into Streamlit apps.
"""

import streamlit as st
from pdf_utils import upload_pdf_to_box, BoxUploadError
from box_config import BoxConfig


def add_box_upload_button(pdf_buffer, filename, student_name=None, session_type=None):
    """
    Add a Box upload button to Streamlit UI with proper error handling.
    
    Args:
        pdf_buffer: BytesIO buffer containing the PDF data
        filename: Base filename (without extension if desired)
        student_name: Optional student name for custom messaging
        session_type: Optional session type for custom messaging
        
    Returns:
        bool: True if upload was successful, False otherwise
    """
    # Ensure filename has .pdf extension
    if not filename.lower().endswith('.pdf'):
        filename = f"{filename}.pdf"
    
    # Check if Box is configured
    config = BoxConfig()
    
    # Show configuration status in expander
    with st.expander("📤 Upload to Box", expanded=False):
        if not config.is_configured():
            missing = config.get_missing_settings()
            st.warning(f"⚠️ Box upload not configured")
            st.info(f"Missing settings: {', '.join(missing)}")
            st.markdown("""
            To enable Box upload, set these environment variables:
            - `SMTP_USERNAME`: Your email address
            - `SMTP_PASSWORD`: Your email password (use App Password for Gmail)
            
            See BOX_INTEGRATION_GUIDE.md for detailed instructions.
            """)
            return False
        
        # Show Box configuration info
        st.success("✅ Box upload is configured")
        st.caption(f"Upload destination: {config.box_email}")
        
        # Upload button
        if st.button("📤 Upload PDF to Box", key=f"box_upload_{filename}"):
            with st.spinner("Uploading to Box..."):
                try:
                    # Reset buffer position
                    pdf_buffer.seek(0)
                    
                    # Perform upload
                    success, message = upload_pdf_to_box(
                        pdf_buffer,
                        filename,
                        config=config
                    )
                    
                    if success:
                        st.success(f"✅ {message}")
                        if student_name:
                            st.info(f"Report for {student_name} has been uploaded to Box")
                        return True
                    else:
                        st.error(f"❌ Upload failed: {message}")
                        return False
                        
                except BoxUploadError as e:
                    st.error(f"❌ Upload error: {str(e)}")
                    
                    # Provide helpful guidance based on error type
                    error_str = str(e).lower()
                    if "authentication" in error_str:
                        st.info("💡 Tip: Check your SMTP username and password. For Gmail, use an App Password.")
                    elif "not properly configured" in error_str:
                        st.info("💡 Tip: Set SMTP_USERNAME and SMTP_PASSWORD environment variables.")
                    elif "retry" in error_str or "attempts" in error_str:
                        st.info("💡 Tip: Check your network connection and try again.")
                    
                    return False
                    
                except Exception as e:
                    st.error(f"❌ Unexpected error: {str(e)}")
                    return False
    
    return False


def check_box_configuration_status():
    """
    Check and display Box configuration status in Streamlit.
    Use this in app settings or info sections.
    
    Returns:
        bool: True if Box is configured, False otherwise
    """
    config = BoxConfig()
    
    if config.is_configured():
        st.success("✅ Box integration is configured and ready")
        st.caption(f"Upload email: {config.box_email}")
        st.caption(f"SMTP server: {config.smtp_host}:{config.smtp_port}")
        st.caption(f"Sender: {config.sender_email}")
        st.caption(f"Max retries: {config.max_retry_attempts}")
        return True
    else:
        missing = config.get_missing_settings()
        st.warning("⚠️ Box integration not configured")
        st.caption(f"Missing: {', '.join(missing)}")
        
        with st.expander("How to configure Box upload"):
            st.markdown("""
            ### Configuration Steps:
            
            1. **Set environment variables** before running the app:
               ```bash
               export SMTP_USERNAME="your-email@example.com"
               export SMTP_PASSWORD="your-app-password"
               ```
            
            2. **For Gmail users**:
               - Enable 2-factor authentication
               - Generate an App Password: https://myaccount.google.com/apppasswords
               - Use the App Password as SMTP_PASSWORD
            
            3. **For other email providers**:
               - Set SMTP_HOST and SMTP_PORT if needed
               - Example for Office 365: `smtp.office365.com:587`
            
            See `BOX_INTEGRATION_GUIDE.md` for complete documentation.
            """)
        
        return False


def show_box_upload_in_sidebar():
    """
    Add Box upload status and configuration info to Streamlit sidebar.
    Call this function early in your app to show Box status.
    """
    with st.sidebar:
        st.markdown("---")
        st.subheader("📤 Box Integration")
        
        config = BoxConfig()
        if config.is_configured():
            st.success("✓ Configured")
            st.caption(f"Upload: {config.box_email}")
        else:
            st.warning("✗ Not configured")
            with st.expander("Setup"):
                st.caption("Set SMTP_USERNAME and SMTP_PASSWORD")
