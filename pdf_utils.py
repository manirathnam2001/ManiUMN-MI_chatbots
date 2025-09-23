import io
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Import our standardized utilities
from scoring_utils import MIScorer, validate_student_name
from feedback_template import FeedbackFormatter, FeedbackValidator

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
    timestamp_pattern = r'Evaluation Timestamp \(UTC\): ([^\n]+)'
    import re
    timestamp_match = re.search(timestamp_pattern, clean_feedback)
    if timestamp_match:
        timestamp = timestamp_match.group(1)
        elements.append(Paragraph(f"<b>Evaluation Date:</b> {timestamp}", info_style))
    
    # Add horizontal line with better styling
    line_style = ParagraphStyle('Line', parent=styles['Normal'], spaceBefore=10, spaceAfter=10)
    elements.append(Paragraph("<para align='center'>" + "─" * 60 + "</para>", line_style))
    
    # Score Summary Section
    elements.append(Paragraph("Score Summary", section_style))
    
    # Generate comprehensive score breakdown
    try:
        score_breakdown = MIScorer.get_score_breakdown(clean_feedback)
        
        # Create enhanced table with score data
        headers = ['MI Component', 'Status', 'Score', 'Max Score', 'Feedback']
        data = [headers]
        
        # Create paragraph style for feedback column with word wrapping
        feedback_style = ParagraphStyle(
            'FeedbackCell',
            parent=styles['Normal'],
            fontSize=9,
            leading=11,
            wordWrap='LTR',
            alignment=0,  # Left alignment
            spaceAfter=2
        )
        
        # Add component data with improved formatting
        for component, details in score_breakdown['components'].items():
            # Create Paragraph object for feedback column to enable word wrapping
            feedback_paragraph = Paragraph(details['feedback'], feedback_style)
            
            data.append([
                component.title(),
                details['status'],
                f"{details['score']:.1f}",
                f"{details['max_score']:.1f}",
                feedback_paragraph  # Use Paragraph instead of plain string
            ])
        
        # Add total score row
        performance_paragraph = Paragraph(
            f"Overall Performance: {_get_performance_level(score_breakdown['percentage'])}", 
            feedback_style
        )
        
        data.append([
            'TOTAL SCORE',
            f"{score_breakdown['percentage']:.1f}%",
            f"{score_breakdown['total_score']:.1f}",
            f"{score_breakdown['total_possible']:.1f}",
            performance_paragraph
        ])
        
        # Create and style the enhanced table
        table = Table(data, colWidths=[1.2*inch, 1*inch, 0.7*inch, 0.7*inch, 3.4*inch])
        
        # Enhanced table styling
        table.setStyle(TableStyle([
            # Header row styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            
            # Data rows styling
            ('BACKGROUND', (0, 1), (-1, -2), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -2), colors.black),
            ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -2), 10),
            ('ALIGN', (0, 1), (2, -2), 'LEFT'),
            ('ALIGN', (3, 1), (3, -2), 'CENTER'),
            
            # Total row styling
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 11),
            
            # General table styling
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.lightgrey]),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(table)
        
    except Exception as e:
        # Fallback to simple display if score parsing fails
        print(f"Warning: Could not parse scores: {e}")
        feedback_style = ParagraphStyle(
            'Feedback',
            parent=styles['Normal'],
            fontSize=11,
            leading=14,
            spaceAfter=8
        )
        elements.append(Paragraph("Score parsing unavailable. Raw feedback:", feedback_style))
        
    elements.append(Spacer(1, 20))
    
    # Improvement Suggestions Section with enhanced formatting
    elements.append(Paragraph("Improvement Suggestions", section_style))
    
    # Extract and format suggestions using the new template utility
    suggestions = FeedbackFormatter.extract_suggestions_from_feedback(clean_feedback)
    
    suggestion_style = ParagraphStyle(
        'Suggestion',
        parent=styles['Normal'],
        fontSize=11,
        leading=14,
        spaceAfter=8,
        leftIndent=20,
        bulletIndent=10
    )
    
    if suggestions:
        for suggestion in suggestions:
            # Clean and format each suggestion
            clean_suggestion = FeedbackValidator.sanitize_special_characters(suggestion)
            elements.append(Paragraph(f"• {clean_suggestion}", suggestion_style))
    else:
        # Fallback: show raw feedback content after component analysis
        feedback_lines = clean_feedback.split('\n')
        for line in feedback_lines:
            line = line.strip()
            if line and not any(comp in line.upper() for comp in MIScorer.COMPONENTS.keys()):
                if not line.startswith('Session Feedback') and not line.startswith('Evaluation Timestamp'):
                    elements.append(Paragraph(line, suggestion_style))
    
    elements.append(Spacer(1, 20))
    
    # Conversation Transcript Section with improved formatting
    elements.append(Paragraph("Conversation Transcript", section_style))
    
    # Enhanced conversation styling
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
    
    # Format conversation with better role distinction
    for i, message in enumerate(chat_history):
        role = message.get("role", "user").title()
        content = message.get("content", "")
        
        # Sanitize content for special characters
        clean_content = FeedbackValidator.sanitize_special_characters(content)
        
        # Alternate background colors for better readability
        bg_color = colors.lightgrey if i % 2 == 0 else colors.white
        
        # Role header
        elements.append(Paragraph(f"<b>{role}:</b>", role_style))
        
        # Message content with word wrapping
        if len(clean_content) > 100:
            # Break long messages into smaller paragraphs
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
    
    # Build PDF with error handling
    try:
        doc.build(elements)
    except Exception as e:
        # If PDF build fails, try with simplified content
        print(f"Warning: PDF build failed, attempting simplified version: {e}")
        elements = []
        elements.append(Paragraph(f"MI Performance Report - {session_type}", title_style))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(f"Student: {validated_name}", info_style))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph("Feedback Content", section_style))
        
        # Add simplified feedback content
        simple_style = ParagraphStyle('Simple', parent=styles['Normal'], fontSize=11)
        for line in clean_feedback.split('\n')[:20]:  # Limit lines to prevent issues
            if line.strip():
                elements.append(Paragraph(line.strip(), simple_style))
        
        doc.build(elements)
    
    buffer.seek(0)
    return buffer


def _get_performance_level(percentage: float) -> str:
    """Get performance level description based on percentage score."""
    if percentage >= 90:
        return "Excellent"
    elif percentage >= 80:
        return "Proficient"
    elif percentage >= 70:
        return "Developing"
    elif percentage >= 60:
        return "Beginning"
    else:
        return "Needs Improvement"
