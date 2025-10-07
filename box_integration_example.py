"""
Example integration of Box upload and logging into MI chatbot applications.

This file demonstrates how to integrate the Box upload functionality and logging
system into HPV.py and OHI.py applications.

Usage:
1. Import required modules
2. Initialize uploader at app startup
3. Add upload option after PDF generation
4. Handle success/failure appropriately
"""

import streamlit as st
import io
from box_integration import BoxUploader
from upload_logs import BoxUploadLogger, LogAnalyzer, BoxUploadMonitor


def initialize_box_integration(bot_type="HPV"):
    """
    Initialize Box integration for the chatbot.
    
    Args:
        bot_type: Type of bot ('OHI' or 'HPV')
        
    Returns:
        BoxUploader instance
    """
    try:
        uploader = BoxUploader(bot_type)
        return uploader
    except Exception as e:
        st.warning(f"Box upload feature unavailable: {e}")
        return None


def upload_to_box_with_logging(uploader, student_name, pdf_buffer, filename):
    """
    Upload PDF to Box with comprehensive logging and user feedback.
    
    Args:
        uploader: BoxUploader instance
        student_name: Name of the student
        pdf_buffer: BytesIO buffer containing PDF data
        filename: Name for the PDF file
        
    Returns:
        bool: True if upload successful, False otherwise
    """
    if uploader is None:
        return False
    
    try:
        # Create a copy of the buffer for upload (original is used for download)
        upload_buffer = io.BytesIO(pdf_buffer.getvalue())
        
        # Attempt upload
        success = uploader.upload_pdf_to_box(
            student_name=student_name,
            pdf_buffer=upload_buffer,
            filename=filename,
            max_retries=3,
            retry_delay=2
        )
        
        return success
        
    except Exception as e:
        st.error(f"Upload error: {e}")
        return False


def show_monitoring_dashboard(bot_type="HPV"):
    """
    Display Box upload monitoring dashboard in Streamlit.
    
    Args:
        bot_type: Type of bot ('OHI' or 'HPV')
    """
    st.subheader("📊 Box Upload Monitoring")
    
    analyzer = LogAnalyzer()
    monitor = BoxUploadMonitor()
    
    # Get statistics
    stats_week = analyzer.get_upload_statistics(bot_type, days=7)
    stats_all = analyzer.get_upload_statistics(bot_type)
    
    # Display metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("7-Day Success Rate", f"{stats_week['success_rate']:.1f}%")
        st.metric("7-Day Uploads", stats_week['total_attempts'])
    
    with col2:
        st.metric("All-Time Success Rate", f"{stats_all['success_rate']:.1f}%")
        st.metric("Total Uploads", stats_all['total_attempts'])
    
    with col3:
        st.metric("Recent Errors", stats_week['total_errors'])
        st.metric("Recent Warnings", stats_week['total_warnings'])
    
    # Health check
    health = monitor.check_health(bot_type, threshold=80.0)
    
    if health['status'] == 'healthy':
        st.success(f"✅ System Health: {health['status'].upper()}")
    else:
        st.warning(f"⚠️ System Health: {health['status'].upper()}")
    
    st.info(health['message'])
    
    # Recent errors
    if stats_week['total_errors'] > 0:
        st.subheader("Recent Errors")
        errors = analyzer.get_error_summary(bot_type, limit=5)
        
        for error in errors:
            with st.expander(f"[{error['timestamp']}] {error['event_type']}"):
                st.code(error['message'])


# =====================================
# Example Integration into HPV.py/OHI.py
# =====================================

def example_integration_in_app():
    """
    Example of how to integrate Box upload into HPV.py or OHI.py.
    
    Add this code to your Streamlit application.
    """
    
    # === Step 1: Initialize at startup (add near top of file) ===
    # Determine bot type based on which file this is
    BOT_TYPE = "HPV"  # or "OHI" for OHI.py
    
    # Initialize Box uploader (do this once at app startup)
    if 'box_uploader' not in st.session_state:
        st.session_state.box_uploader = initialize_box_integration(BOT_TYPE)
    
    # === Step 2: Add upload option after PDF generation ===
    # This code would go in your PDF generation section
    
    # Example: After generating PDF in your app
    if st.button("📥 Generate Feedback PDF"):
        try:
            # Your existing PDF generation code
            from pdf_utils import generate_pdf_report
            from time_utils import get_formatted_utc_time
            
            # Generate timestamp and filename
            timestamp = get_formatted_utc_time().replace(" ", "_").replace(":", "-")
            filename = f"MI_Feedback_{BOT_TYPE}_{student_name}_{timestamp}.pdf"
            
            # Generate PDF buffer
            pdf_buffer = generate_pdf_report(
                student_name, 
                feedback, 
                chat_history, 
                session_type=f"{BOT_TYPE} Vaccine"
            )
            
            # Display success message
            st.success("✅ PDF report generated successfully!")
            
            # Offer download to user
            st.download_button(
                label="📥 Download PDF Report",
                data=pdf_buffer,
                file_name=filename,
                mime="application/pdf",
                key="download_pdf"
            )
            
            # === Step 3: Optional Box upload ===
            if st.session_state.box_uploader is not None:
                st.divider()
                st.subheader("📤 Upload to Box")
                
                if st.button("Upload to Box", key="upload_box"):
                    with st.spinner("Uploading to Box..."):
                        success = upload_to_box_with_logging(
                            st.session_state.box_uploader,
                            student_name,
                            pdf_buffer,
                            filename
                        )
                        
                        if success:
                            st.success("✅ Report uploaded to Box successfully!")
                            st.info(f"📧 Sent to: {st.session_state.box_uploader._get_box_email()}")
                        else:
                            st.warning("⚠️ Upload to Box failed. Report is still available for download.")
                            st.info("Check logs for details or try again later.")
            else:
                # Box upload not available
                st.info("ℹ️ Box upload feature is currently disabled.")
                
        except Exception as e:
            st.error(f"Error generating or uploading PDF: {e}")


# =====================================
# Sidebar Monitoring Widget (Optional)
# =====================================

def add_monitoring_sidebar(bot_type="HPV"):
    """
    Add monitoring information to sidebar.
    
    Args:
        bot_type: Type of bot ('OHI' or 'HPV')
    """
    with st.sidebar:
        st.divider()
        st.subheader("📊 System Status")
        
        try:
            monitor = BoxUploadMonitor()
            health = monitor.check_health(bot_type, threshold=80.0)
            
            if health['status'] == 'healthy':
                st.success(f"✅ Box Upload: Healthy")
            else:
                st.warning(f"⚠️ Box Upload: Issues Detected")
            
            st.caption(f"Success Rate: {health['success_rate']:.1f}%")
            
            # Show details in expander
            with st.expander("View Details"):
                analyzer = LogAnalyzer()
                stats = analyzer.get_upload_statistics(bot_type, days=7)
                
                st.metric("7-Day Uploads", stats['total_attempts'])
                st.metric("Successes", stats['total_successes'])
                st.metric("Failures", stats['total_failures'])
                
                if stats['total_errors'] > 0:
                    st.warning(f"{stats['total_errors']} errors in last 7 days")
                
        except Exception as e:
            st.caption("Monitoring unavailable")


# =====================================
# Admin Panel (Optional)
# =====================================

def create_admin_panel(bot_type="HPV"):
    """
    Create an admin panel for monitoring and management.
    
    This can be a separate page or section of your app.
    
    Args:
        bot_type: Type of bot ('OHI' or 'HPV')
    """
    st.title(f"📊 {bot_type} Bot - Admin Panel")
    
    # Tab layout
    tab1, tab2, tab3 = st.tabs(["Dashboard", "Logs", "Maintenance"])
    
    with tab1:
        show_monitoring_dashboard(bot_type)
    
    with tab2:
        st.subheader("Recent Uploads")
        
        analyzer = LogAnalyzer()
        uploads = analyzer.get_recent_uploads(bot_type, limit=20)
        
        if uploads:
            for upload in uploads:
                status = "✅" if upload['event_type'] == 'upload_success' else "❌"
                
                with st.expander(f"{status} [{upload['timestamp']}] {upload.get('message', 'N/A')}"):
                    st.json(upload)
        else:
            st.info("No recent uploads")
    
    with tab3:
        st.subheader("Maintenance")
        
        # Log cleanup
        st.write("**Log Cleanup**")
        cleanup_days = st.number_input("Keep logs for (days)", min_value=7, max_value=365, value=90)
        
        if st.button("Clean Up Old Logs"):
            analyzer = LogAnalyzer()
            results = analyzer.cleanup_old_logs(days=cleanup_days)
            
            st.success(f"Cleaned up {results.get(bot_type, 0)} old log entries for {bot_type}")
        
        # Connection test
        st.write("**Connection Test**")
        if st.button("Test Box Connection"):
            uploader = BoxUploader(bot_type)
            test_result = uploader.test_connection()
            
            st.json(test_result)


# =====================================
# Main Integration Example
# =====================================

if __name__ == "__main__":
    st.set_page_config(page_title="Box Integration Example", layout="wide")
    
    st.title("Box Integration Example")
    
    st.markdown("""
    This file demonstrates how to integrate Box upload and logging into your
    MI chatbot applications (HPV.py or OHI.py).
    
    ### Key Integration Points:
    
    1. **Initialization**: Add at app startup
    2. **PDF Upload**: Add after PDF generation
    3. **Monitoring**: Optional dashboard and sidebar widgets
    4. **Admin Panel**: Optional management interface
    
    ### Quick Start:
    
    ```python
    # In your HPV.py or OHI.py file:
    from box_integration import BoxUploader
    
    # Initialize at startup
    BOT_TYPE = "HPV"  # or "OHI"
    if 'box_uploader' not in st.session_state:
        st.session_state.box_uploader = BoxUploader(BOT_TYPE)
    
    # After generating PDF:
    if success:
        upload_to_box_with_logging(
            st.session_state.box_uploader,
            student_name,
            pdf_buffer,
            filename
        )
    ```
    
    See the code in this file for complete examples.
    """)
    
    # Show example components
    st.divider()
    
    bot_type = st.selectbox("Select Bot Type", ["HPV", "OHI"])
    
    st.subheader("Example: Monitoring Dashboard")
    show_monitoring_dashboard(bot_type)
    
    st.divider()
    
    st.subheader("Example: Admin Panel")
    create_admin_panel(bot_type)
