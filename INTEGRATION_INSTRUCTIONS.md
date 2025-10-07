# Integration Instructions for HPV.py and OHI.py

## How to Add Box Upload to Existing Apps

### Step 1: Add Import (Top of File)

Add this line with the other imports at the top of HPV.py or OHI.py:

```python
from box_streamlit_helpers import add_box_upload_button
```

### Step 2: Add Upload Button (PDF Section)

Find the PDF generation section that looks like this:

```python
# Current code in HPV.py or OHI.py:
if st.session_state.feedback is not None:
    # ... PDF generation code ...
    
    st.download_button(
        label="📥 Download PDF Report",
        data=pdf_buffer,
        file_name=f"HPV_MI_Feedback_Report_{st.session_state.student_name}.pdf",
        mime="application/pdf",
        use_container_width=True
    )
```

Add this AFTER the download button:

```python
    # Box upload button (NEW CODE - ADD THIS)
    add_box_upload_button(
        pdf_buffer=pdf_buffer,
        filename=f"HPV_MI_Report_{st.session_state.student_name}",
        student_name=st.session_state.student_name,
        session_type="HPV Vaccine"  # or "OHI" for OHI.py
    )
```

### Step 3: Set Environment Variables

Before running the app, set these environment variables:

```bash
export SMTP_USERNAME="your-email@example.com"
export SMTP_PASSWORD="your-app-password"
```

For Gmail users:
1. Go to https://myaccount.google.com/apppasswords
2. Generate an App Password
3. Use that as SMTP_PASSWORD

### Complete Example for HPV.py

Here's the complete PDF section with Box upload:

```python
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
```

### Complete Example for OHI.py

Same pattern, just change the session_type:

```python
# Box upload button (NEW)
from box_streamlit_helpers import add_box_upload_button
add_box_upload_button(
    pdf_buffer=pdf_buffer,
    filename=f"OHI_MI_Report_{st.session_state.student_name}",
    student_name=st.session_state.student_name,
    session_type="Oral Hygiene"  # Changed from "HPV Vaccine"
)
```

## What the User Will See

When Box is NOT configured:
- ⚠️ Warning message about missing configuration
- Instructions on how to set up SMTP credentials

When Box IS configured:
- ✅ "Box upload is configured" message
- "📤 Upload PDF to Box" button
- On successful upload: ✅ Success message
- On failed upload: ❌ Error with helpful tips

## Testing

After adding the code, test it:

1. Run the app: `streamlit run HPV.py`
2. Generate a PDF report
3. Click the Box upload button
4. Verify the upload works (or see helpful error messages)

## Optional: Add Sidebar Status

To show Box status in the sidebar, add this near the top of your app:

```python
from box_streamlit_helpers import show_box_upload_in_sidebar

# Add this after st.set_page_config()
show_box_upload_in_sidebar()
```

## Troubleshooting

If you see "Box upload not configured":
- Check that SMTP_USERNAME and SMTP_PASSWORD are set
- For Gmail, make sure you're using an App Password, not your regular password

If you see "Authentication failed":
- Verify your SMTP credentials are correct
- For Gmail, enable 2-factor authentication and use an App Password

If uploads fail with timeout:
- Check your network connection
- Verify port 587 is not blocked by firewall

## Summary

**Minimum required changes:**
1. Add one import line
2. Add one function call after PDF generation
3. Set two environment variables

That's it! The Box integration is now live in your app.
