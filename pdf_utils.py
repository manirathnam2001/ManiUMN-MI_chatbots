"""
PDF report generation utilities for MI assessment feedback.

This module handles the creation of professional PDF reports containing:
- Standardized MI feedback with component scores
- Detailed score breakdowns with performance levels
- Conversation transcripts with proper formatting
- Improvement suggestions and recommendations
- Email backup to Box integration

The PDF generator ensures consistent formatting across OHI and HPV assessments
and handles special character sanitization for proper PDF rendering.
"""

import io
import re
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors

from scoring_utils import MIScorer, validate_student_name
from feedback_template import FeedbackValidator, FeedbackFormatter


def _get_performance_level(percentage: float) -> str:
    """Get performance level description based on percentage score."""
    if percentage >= 90:
        return "Excellent"
    elif percentage >= 80:
        return "Very Good"
    elif percentage >= 70:
        return "Good"
    elif percentage >= 60:
        return "Satisfactory"
    else:
        return "Needs Improvement"


def generate_pdf_report(student_name, raw_feedback, chat_history, session_type="HPV Vaccine"):
    """
    Generate a standardized PDF report with consistent MI feedback formatting.
    
    Args:
        student_name (str): Name of the student
        raw_feedback (str): The exact feedback text displayed in the app
        chat_history (list): List of conversation messages
        session_type (str): Type of session (e.g., "HPV Vaccine", "OHI")
        
    Returns:
        io.BytesIO: PDF buffer ready for download
    """
    # Input validation
    try:
        validated_name = validate_student_name(student_name)
    except ValueError as e:
        raise ValueError(f"Invalid student name: {e}")

    # Sanitize feedback text for special characters
    clean_feedback = FeedbackValidator.sanitize_special_characters(raw_feedback)

    # Validate feedback completeness
    validation = FeedbackValidator.validate_feedback_completeness(clean_feedback)
    if not validation['is_valid']:
        print(f"Warning: Feedback may be incomplete - missing: {validation['missing_components']}")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter, 
        rightMargin=72, 
        leftMargin=72,
        topMargin=72, 
        bottomMargin=72,
        title=f"MI Performance Report - {session_type}",
        author="MI Assessment System"
    )

    elements = []
    styles = getSampleStyleSheet()

    # Enhanced title style with consistent formatting
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        spaceAfter=20,
        alignment=1,  # Center alignment
        textColor=colors.darkblue,
        fontName='Helvetica-Bold'
    )

    # Enhanced section heading style
    section_style = ParagraphStyle(
        'Section',
        parent=styles['Heading2'],
        fontSize=16,
        spaceBefore=20,
        spaceAfter=10,
        textColor=colors.darkblue,
        fontName='Helvetica-Bold'
    )

    # Header with improved styling
    elements.append(Paragraph(f"MI Performance Report - {session_type}", title_style))
    elements.append(Spacer(1, 20))

    # Student info with enhanced styling
    info_style = ParagraphStyle(
        'Info', 
        parent=styles['Normal'], 
        fontSize=14, 
        spaceAfter=6,
        fontName='Helvetica-Bold'
    )
    elements.append(Paragraph(f"<b>Student:</b> {validated_name}", info_style))

    # Add evaluation timestamp if available
    timestamp_pattern = r'Evaluation Timestamp \(Minnesota\): ([^\n]+)'
    import re
    timestamp_match = re.search(timestamp_pattern, clean_feedback)
    if timestamp_match:
        timestamp = timestamp_match.group(1)
        elements.append(Paragraph(f"<b>Evaluation Date:</b> {timestamp}", info_style))

    # Add horizontal line with better styling
    line_style = ParagraphStyle('Line', parent=styles['Normal'], spaceBefore=10, spaceAfter=10)
    elements.append(Paragraph("<para align='center'>" + "─" * 60 + "</para>", line_style))

    # --- New: Check if chat_history contains any user responses ---
    has_user_turns = any(msg.get("role", "").lower() == "user" for msg in chat_history)

    # Score Summary Section
    elements.append(Paragraph("Score Summary", section_style))

    # --- Only try to parse scores if there was a real user response ---
    if has_user_turns:
        try:
            score_breakdown = MIScorer.get_score_breakdown(clean_feedback)

            # Create style for table cell text wrapping
            cell_style = ParagraphStyle(
                'TableCell',
                parent=styles['Normal'],
                fontSize=10,
                leading=12,
                wordWrap='CJK'
            )
            
            # Table construction with improved wrapping
            headers = ['MI Component', 'Status', 'Score', 'Max Score', 'Feedback']
            data = [headers]
            for component, details in score_breakdown['components'].items():
                # Wrap feedback text in Paragraph for proper word wrapping
                feedback_text = details['feedback']
                feedback_para = Paragraph(feedback_text, cell_style)
                
                data.append([
                    component.title(),
                    details['status'],
                    f"{details['score']:.1f}",
                    f"{details['max_score']:.1f}",
                    feedback_para
                ])
            
            # Add total row with wrapped text
            total_feedback = f"Overall Performance: {_get_performance_level(score_breakdown['percentage'])}"
            total_feedback_para = Paragraph(total_feedback, cell_style)
            
            data.append([
                'TOTAL SCORE',
                f"{score_breakdown['percentage']:.1f}%",
                f"{score_breakdown['total_score']:.1f}",
                f"{score_breakdown['total_possible']:.1f}",
                total_feedback_para
            ])
            
            # Adjusted column widths for better display
            table = Table(data, colWidths=[1.2*inch, 1*inch, 0.7*inch, 0.8*inch, 3.3*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('TOPPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -2), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -2), colors.black),
                ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -2), 10),
                ('ALIGN', (0, 1), (2, -2), 'LEFT'),
                ('ALIGN', (3, 1), (3, -2), 'CENTER'),
                ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
                ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, -1), (-1, -1), 11),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.lightgrey]),
                ('PADDING', (0, 0), (-1, -1), 8),  # Increased padding
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ]))
            elements.append(table)
        except Exception as e:
            elements.append(Paragraph("Score parsing unavailable. Raw feedback:", styles['Normal']))
    else:
        # No user input: show zeros and a clear no-evaluation message
        # Create style for table cell text wrapping
        cell_style = ParagraphStyle(
            'TableCell',
            parent=styles['Normal'],
            fontSize=10,
            leading=12,
            wordWrap='CJK'
        )
        
        zero_data = [
            ['MI Component', 'Status', 'Score', 'Max Score', 'Feedback'],
            ['Collaboration', 'Not Evaluated', '0.0', '7.5', Paragraph('No feedback, no user response', cell_style)],
            ['Evocation', 'Not Evaluated', '0.0', '7.5', Paragraph('No feedback, no user response', cell_style)],
            ['Acceptance', 'Not Evaluated', '0.0', '7.5', Paragraph('No feedback, no user response', cell_style)],
            ['Compassion', 'Not Evaluated', '0.0', '7.5', Paragraph('No feedback, no user response', cell_style)],
            ['TOTAL SCORE', '0.0%', '0.0', '30.0', Paragraph('No evaluation performed (no user responses)', cell_style)]
        ]
        table = Table(zero_data, colWidths=[1.2*inch, 1*inch, 0.7*inch, 0.8*inch, 3.3*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -2), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -2), colors.black),
            ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -2), 10),
            ('ALIGN', (0, 1), (2, -2), 'LEFT'),
            ('ALIGN', (3, 1), (3, -2), 'CENTER'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 11),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.lightgrey]),
            ('PADDING', (0, 0), (-1, -1), 8),  # Increased padding
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        elements.append(table)

    elements.append(Spacer(1, 20))

    # Improvement Suggestions Section with enhanced formatting
    elements.append(Paragraph("Improvement Suggestions", section_style))
    if has_user_turns:
        suggestions = FeedbackFormatter.extract_suggestions_from_feedback(clean_feedback)
        
        # Define styles for different suggestion types
        suggestion_heading_style = ParagraphStyle(
            'SuggestionHeading', 
            parent=styles['Heading3'],
            fontSize=13, 
            leading=16, 
            spaceAfter=10,
            spaceBefore=10,
            textColor=colors.darkblue,
            fontName='Helvetica-Bold'
        )
        
        suggestion_item_style = ParagraphStyle(
            'SuggestionItem', 
            parent=styles['Normal'],
            fontSize=11, 
            leading=14, 
            spaceAfter=10, 
            leftIndent=20,
            bulletIndent=10,
            fontName='Helvetica'
        )
        
        suggestion_paragraph_style = ParagraphStyle(
            'SuggestionParagraph', 
            parent=styles['Normal'],
            fontSize=11, 
            leading=14, 
            spaceAfter=8, 
            leftIndent=20
        )
        
        if suggestions:
            for suggestion in suggestions:
                clean_content = FeedbackValidator.sanitize_special_characters(suggestion['content'])
                clean_title = FeedbackValidator.sanitize_special_characters(suggestion['title'])
                
                if suggestion['type'] == 'heading':
                    elements.append(Paragraph(clean_title, suggestion_heading_style))
                elif suggestion['type'] == 'item':
                    # Format as numbered item with bold number
                    item_text = f"<b>{clean_title}</b> {clean_content}"
                    elements.append(Paragraph(item_text, suggestion_item_style))
                elif suggestion['type'] == 'paragraph':
                    elements.append(Paragraph(clean_content, suggestion_paragraph_style))
        else:
            # Fallback: show raw feedback content after component analysis
            feedback_lines = clean_feedback.split('\n')
            fallback_style = ParagraphStyle(
                'Fallback', parent=styles['Normal'],
                fontSize=11, leading=14, spaceAfter=8, leftIndent=20
            )
            for line in feedback_lines:
                line = line.strip()
                if line and not any(comp in line.upper() for comp in MIScorer.COMPONENTS.keys()):
                    if not line.startswith('Session Feedback') and not line.startswith('Evaluation Timestamp'):
                        # Remove asterisks from fallback content too
                        clean_line = re.sub(r'\*\*([^*]+)\*\*', r'\1', line)
                        clean_line = clean_line.replace('*', '').strip()
                        clean_line = FeedbackValidator.sanitize_special_characters(clean_line)
                        elements.append(Paragraph(clean_line, fallback_style))
    else:
        elements.append(Paragraph("No suggestions available (no user responses were given, so no evaluation was performed).", styles['Normal']))

    elements.append(Spacer(1, 20))

    # Conversation Transcript Section with improved formatting (unchanged)
    elements.append(Paragraph("Conversation Transcript", section_style))
    conversation_style = ParagraphStyle(
        'Conversation',
        parent=styles['Normal'],
        fontSize=10,
        leading=13,
        leftIndent=10,
        rightIndent=10,
        spaceAfter=4
    )
    role_style = ParagraphStyle(
        'ConversationRole',
        parent=styles['Normal'],
        fontSize=10,
        leading=13,
        leftIndent=10,
        rightIndent=10,
        spaceAfter=4,
        fontName='Helvetica-Bold'
    )
    for i, message in enumerate(chat_history):
        role = message.get("role", "user").title()
        content = message.get("content", "")
        clean_content = FeedbackValidator.sanitize_special_characters(content)
        bg_color = colors.lightgrey if i % 2 == 0 else colors.white
        elements.append(Paragraph(f"<b>{role}:</b>", role_style))
        if len(clean_content) > 100:
            words = clean_content.split()
            chunks = []
            current_chunk = []
            for word in words:
                current_chunk.append(word)
                if len(' '.join(current_chunk)) > 80:
                    chunks.append(' '.join(current_chunk))
                    current_chunk = []
            if current_chunk:
                chunks.append(' '.join(current_chunk))
            for chunk in chunks:
                elements.append(Paragraph(chunk, conversation_style))
        else:
            elements.append(Paragraph(clean_content, conversation_style))
        elements.append(Spacer(1, 8))
    try:
        doc.build(elements)
    except Exception as e:
        elements = []
        elements.append(Paragraph(f"MI Performance Report - {session_type}", title_style))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(f"Student: {validated_name}", info_style))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph("Feedback Content", section_style))
        simple_style = ParagraphStyle('Simple', parent=styles['Normal'], fontSize=11)
        for line in clean_feedback.split('\n')[:20]:
            if line.strip():
                elements.append(Paragraph(line.strip(), simple_style))
        doc.build(elements)
    buffer.seek(0)
    return buffer


def send_pdf_to_box(pdf_buffer: io.BytesIO, 
                   filename: str,
                   student_name: str,
                   session_type: str) -> dict:
    """
    Send generated PDF to Box email for backup.
    
    This function attempts to email the PDF to the appropriate Box email address
    with retry logic and comprehensive logging. It's designed to be fail-safe -
    if the email fails, the user can still download the PDF.
    
    Args:
        pdf_buffer: BytesIO buffer containing the PDF data
        filename: Name of the PDF file
        student_name: Name of the student
        session_type: Type of session ('OHI' or 'HPV Vaccine')
        
    Returns:
        Dictionary with:
            - success: Boolean indicating if email was sent
            - attempts: Number of attempts made
            - error: Error message if failed (None if successful)
    """
    try:
        from email_utils import send_box_backup_email
        
        # Create a copy of the buffer for email (to avoid affecting downloads)
        email_buffer = io.BytesIO(pdf_buffer.getvalue())
        
        # Send email with retry
        result = send_box_backup_email(
            pdf_buffer=email_buffer,
            filename=filename,
            student_name=student_name,
            session_type=session_type
        )
        
        return result
        
    except ImportError as e:
        return {
            'success': False,
            'error': f"Email utilities not available: {e}",
            'attempts': 0
        }
    except Exception as e:
        return {
            'success': False,
            'error': f"Unexpected error during email backup: {e}",
            'attempts': 0
        }
