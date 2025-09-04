import io
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

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
    
    # Section heading style
    section_style = ParagraphStyle(
        'Section',
        parent=styles['Heading2'],
        fontSize=14,
        spaceBefore=20,
        spaceAfter=12
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
    
    # Feedback section
    elements.append(Paragraph("Feedback Summary", section_style))
    
    # Create table headers and data for MI components
    headers = ['MI Component', 'Status', 'Score', 'Feedback']
    data = []
    
    # Parse the raw feedback to extract component information
    components = ['COLLABORATION:', 'EVOCATION:', 'ACCEPTANCE:', 'COMPASSION:']
    current_component = None
    component_data = {}
    
    for line in raw_feedback.split('\n'):
        line = line.strip()
        if any(comp in line for comp in components):
            # Extract component name and status
            for comp in components:
                if comp in line:
                    current_component = comp.replace(':', '')
                    # Extract [Met/Partially Met/Not Met] from the line
                    status_start = line.find('[') + 1
                    status_end = line.find(']')
                    if status_start > 0 and status_end > status_start:
                        status = line[status_start:status_end]
                        # Extract feedback after the second dash
                        parts = line.split('-')
                        if len(parts) > 2:
                            feedback = parts[2].strip()
                            # Calculate score based on status
                            score = '7.5' if status == 'Met' else '3.75' if status == 'Partially Met' else '0'
                            data.append([current_component, status, score, feedback])
    
    # Create and style the table
    if data:
        table = Table([headers] + data, colWidths=[1.5*inch, inch, 0.75*inch, 3.75*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('WORDWRAP', (0, 0), (-1, -1), True),
        ]))
        elements.append(table)
    
    # Add spacing before suggestions
    elements.append(Spacer(1, 20))
    
    # Overall suggestions section
    elements.append(Paragraph("Improvement Suggestions", section_style))
    
    # Feedback content style
    feedback_style = ParagraphStyle(
        'Feedback',
        parent=styles['Normal'],
        fontSize=11,
        leading=14,
        spaceAfter=8
    )
    
    # Add detailed suggestions from the raw feedback
    in_suggestions = False
    suggestions = []
    for line in raw_feedback.split('\n'):
        if 'suggestions' in line.lower() or 'next steps' in line.lower():
            in_suggestions = True
            suggestions.append(line)
        elif in_suggestions and line.strip():
            suggestions.append(line)
    
    for suggestion in suggestions:
        elements.append(Paragraph(suggestion, feedback_style))
    
    # Add spacing before conversation
    elements.append(Spacer(1, 20))
    
    # Conversation transcript section
    elements.append(Paragraph("Conversation Transcript", section_style))
    
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
