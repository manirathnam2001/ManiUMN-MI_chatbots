def generate_pdf_report(student_name, raw_feedback, chat_history, session_type="HPV Vaccine"):
    """
    Generate a PDF report with exact MI feedback formatting.
    
    Args:
        student_name (str): Name of the student
        raw_feedback (str): The exact feedback text displayed in the app
        chat_history (list): List of conversation messages
        session_type (str): Type of session (e.g., "HPV Vaccine")
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72,
                          topMargin=72, bottomMargin=18)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Title style
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1  # Center alignment
    )
    
    # Header
    elements.append(Paragraph(f"MI Performance Report - {session_type}", title_style))
    elements.append(Spacer(1, 12))
    
    # Student info style
    info_style = ParagraphStyle('Info', parent=styles['Normal'], fontSize=12, spaceAfter=6)
    elements.append(Paragraph(f"<b>Student Name:</b> {student_name}", info_style))
    
    # Add horizontal line
    elements.append(Paragraph("<hr/>", styles['Normal']))
    elements.append(Spacer(1, 12))
    
    # Feedback content style
    feedback_style = ParagraphStyle(
        'Feedback',
        parent=styles['Normal'],
        fontSize=11,
        leading=14,
        spaceAfter=8
    )
    
    # Add the raw feedback exactly as displayed in the app
    feedback_paragraphs = raw_feedback.split('\n')
    for para in feedback_paragraphs:
        if para.strip():
            elements.append(Paragraph(para, feedback_style))
    
    # Add spacing before conversation
    elements.append(Spacer(1, 20))
    
    # Conversation section
    elements.append(Paragraph("Conversation Transcript", styles['Heading2']))
    elements.append(Spacer(1, 12))
    
    # Format each message in the conversation
    conversation_style = ParagraphStyle(
        'Conversation',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        leftIndent=10
    )
    
    for message in chat_history:
        role = message.get("role", "user").title()
        content = message.get("content", "")
        elements.append(Paragraph(
            f"<b>{role}:</b> {content}",
            conversation_style
        ))
        elements.append(Spacer(1, 6))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer
