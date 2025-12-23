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
import logging
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors

# Import new rubric system
try:
    from services.evaluation_service import EvaluationService
    from rubric.mi_rubric import MIRubric
    NEW_RUBRIC_AVAILABLE = True
except ImportError:
    NEW_RUBRIC_AVAILABLE = False

# Keep old imports for backward compatibility
try:
    from scoring_utils import MIScorer, validate_student_name
    OLD_SCORER_AVAILABLE = True
except ImportError:
    OLD_SCORER_AVAILABLE = False
    # Provide fallback for validate_student_name
    def validate_student_name(name: str) -> str:
        """Fallback student name validation."""
        if not name or not name.strip():
            raise ValueError("Student name cannot be empty")
        return name.strip()

from feedback_template import FeedbackValidator, FeedbackFormatter


def _soft_wrap_long_tokens(text: str, max_len: int = 30) -> str:
    """
    Insert zero-width spaces into very long tokens to enable wrapping.
    
    This helps prevent long unbreakable strings (like URLs or concatenated words)
    from overflowing table cells by inserting Unicode zero-width spaces that
    allow line breaks without changing the visual appearance.
    
    Args:
        text: Text that may contain long tokens
        max_len: Maximum token length before inserting break opportunities
        
    Returns:
        Text with zero-width spaces inserted for better wrapping
    """
    if not text:
        return text
    
    words = text.split()
    result = []
    
    for word in words:
        if len(word) > max_len:
            # Insert zero-width space every max_len characters
            broken = ''
            for i, char in enumerate(word):
                broken += char
                if (i + 1) % max_len == 0 and i < len(word) - 1:
                    broken += '\u200b'  # Zero-width space
            result.append(broken)
        else:
            result.append(word)
    
    return ' '.join(result)


def _make_para(text: str, style: ParagraphStyle) -> Paragraph:
    """
    Create a Paragraph with proper text sanitization and formatting.
    
    This helper ensures consistent handling of:
    - Special character sanitization
    - Markdown bold to HTML bold conversion
    - Soft-wrapping of long tokens
    - Paragraph creation with the specified style
    
    Args:
        text: Raw text that may contain markdown, special chars, or long tokens
        style: ParagraphStyle to apply
        
    Returns:
        Paragraph object ready for use in tables or document flow
    """
    if not text:
        text = ''
    
    # Sanitize special characters
    clean_text = FeedbackValidator.sanitize_special_characters(str(text))
    
    # Convert markdown bold to HTML bold
    html_text = _format_markdown_to_html(clean_text)
    
    # Apply soft-wrapping for very long tokens
    wrapped_text = _soft_wrap_long_tokens(html_text, max_len=30)
    
    return Paragraph(wrapped_text, style)


def _build_wrapped_table(data: list, content_width: float = 6.5 * inch) -> Table:
    """
    Build a table with proper text wrapping for all cells.
    
    This helper creates a table where:
    - All cells (including headers) use Paragraph objects for wrapping
    - Column widths sum to the specified content width
    - Default proportions: [1.1in, 1.5in, 0.6in, 0.6in, 2.7in] = 6.5in
    
    Args:
        data: List of lists containing table data (already converted to Paragraphs)
        content_width: Total width available for the table (default: 6.5 inches)
        
    Returns:
        Table object with configured column widths
    """
    # Column width proportions that sum to content_width
    # Category/Component: 1.1", Assessment/Status: 1.5", Score: 0.6", Max: 0.6", Notes/Feedback: 2.7"
    col_proportions = [1.1, 1.5, 0.6, 0.6, 2.7]
    total_proportion = sum(col_proportions)
    
    # Scale proportions to match content_width
    colWidths = [(p / total_proportion) * content_width for p in col_proportions]
    
    return Table(data, colWidths=colWidths)


def _get_performance_level(percentage: float, use_new_rubric: bool = False) -> str:
    """Get performance level description based on percentage score and rubric version."""
    if use_new_rubric:
        # New 40-point rubric performance bands
        if percentage >= 90:
            return "Excellent MI skills demonstrated"
        elif percentage >= 75:
            return "Strong MI performance with minor areas for growth"
        elif percentage >= 60:
            return "Satisfactory MI foundation, continue practicing"
        elif percentage >= 40:
            return "Basic MI awareness, significant practice needed"
        else:
            return "Significant improvement needed in MI techniques"
    else:
        # Old 30-point rubric performance levels
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


def _format_markdown_to_html(text: str) -> str:
    """Convert markdown bold (**text**) to HTML bold (<b>text</b>) for PDF rendering.
    
    Args:
        text: Text with markdown formatting
        
    Returns:
        Text with HTML bold tags suitable for ReportLab Paragraph
    """
    # Replace **text** with <b>text</b>
    # Use regex to handle multiple occurrences
    import re
    # Match **text** but not *** (which might be a separator)
    text = re.sub(r'\*\*([^\*]+?)\*\*', r'<b>\1</b>', text)
    return text


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
            # Try new rubric first
            if NEW_RUBRIC_AVAILABLE:
                evaluation_result = EvaluationService.evaluate_session(clean_feedback, session_type)
                
                # Table construction with new rubric data
                headers = ['MI Category', 'Assessment', 'Score', 'Max Score', 'Notes']
                data = []
                
                # Create style for table cell paragraphs with word wrapping
                cell_style = ParagraphStyle(
                    'TableCell',
                    parent=styles['Normal'],
                    fontSize=9,
                    leading=11,
                    wordWrap='LTR'
                )
                
                # Convert headers to Paragraphs for consistent wrapping
                header_style = ParagraphStyle(
                    'TableHeader',
                    parent=styles['Normal'],
                    fontSize=11,
                    leading=13,
                    fontName='Helvetica-Bold',
                    textColor=colors.whitesmoke,
                    wordWrap='LTR'
                )
                header_row = [_make_para(h, header_style) for h in headers]
                data.append(header_row)
                
                for category_name, category_data in evaluation_result['categories'].items():
                    # Wrap all text fields in Paragraph for word wrapping
                    category_para = _make_para(category_name, cell_style)
                    assessment_para = _make_para(category_data['assessment'], cell_style)
                    notes_para = _make_para(category_data.get('notes', ''), cell_style)
                    
                    # Format scores as integers for user-facing display
                    points_int = int(round(category_data['points']))
                    
                    data.append([
                        category_para,
                        assessment_para,
                        f"{points_int}",
                        f"{category_data['max_points']}",
                        notes_para
                    ])
                
                # Wrap total row text in Paragraphs for consistency
                total_label_para = _make_para('TOTAL SCORE', cell_style)
                total_perf_para = _make_para(f"Overall: {evaluation_result['performance_band']}", cell_style)
                
                # Format total score and percentage as integers for display
                total_score_int = int(round(evaluation_result['total_score']))
                percentage_int = int(round(evaluation_result['percentage']))
                
                data.append([
                    total_label_para,
                    f"{percentage_int}%",
                    f"{total_score_int}",
                    f"{evaluation_result['max_possible_score']}",
                    total_perf_para
                ])
                
                # Build table with proper column widths
                table = _build_wrapped_table(data)
                
                # Base table style
                table_style = TableStyle([
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
                    ('PADDING', (0, 0), (-1, -1), 6),
                    ('WORDWRAP', (0, 0), (-1, -1), 'LTR'),
                ])
                
                # Add conditional formatting for scores (row 1 to -2, column 2 is the Score column)
                for row_idx, (category_name, category_data) in enumerate(evaluation_result['categories'].items(), start=1):
                    # Use integer rounded values for comparison
                    points = int(round(category_data['points']))
                    max_points = category_data['max_points']
                    
                    # Apply color based on score: green for full score, red for zero score
                    if points == max_points:
                        # Full score - green text
                        table_style.add('TEXTCOLOR', (2, row_idx), (2, row_idx), colors.green)
                        table_style.add('FONTNAME', (2, row_idx), (2, row_idx), 'Helvetica-Bold')
                    elif points == 0:
                        # Zero score - red text
                        table_style.add('TEXTCOLOR', (2, row_idx), (2, row_idx), colors.red)
                        table_style.add('FONTNAME', (2, row_idx), (2, row_idx), 'Helvetica-Bold')
                
                table.setStyle(table_style)
                elements.append(table)
            elif OLD_SCORER_AVAILABLE:
                # Fallback to old rubric
                score_breakdown = MIScorer.get_score_breakdown(clean_feedback)

                # Table construction with Paragraph wrapping for all cells
                headers = ['MI Component', 'Status', 'Score', 'Max Score', 'Feedback']
                data = []
                
                # Create style for table cell paragraphs with word wrapping
                cell_style = ParagraphStyle(
                    'TableCell',
                    parent=styles['Normal'],
                    fontSize=9,
                    leading=11,
                    wordWrap='LTR'
                )
                
                # Convert headers to Paragraphs for consistent wrapping
                header_style = ParagraphStyle(
                    'TableHeader',
                    parent=styles['Normal'],
                    fontSize=11,
                    leading=13,
                    fontName='Helvetica-Bold',
                    textColor=colors.whitesmoke,
                    wordWrap='LTR'
                )
                header_row = [_make_para(h, header_style) for h in headers]
                data.append(header_row)
                
                for component, details in score_breakdown['components'].items():
                    # Wrap all text fields in Paragraph for word wrapping
                    component_para = _make_para(component.title(), cell_style)
                    status_para = _make_para(details['status'], cell_style)
                    feedback_para = _make_para(details['feedback'], cell_style)
                    
                    # Format scores as integers for user-facing display
                    from scoring_utils import format_score_for_display
                    score_int = format_score_for_display(details['score'])
                    max_score_int = format_score_for_display(details['max_score'])
                    
                    data.append([
                        component_para,
                        status_para,
                        f"{score_int}",
                        f"{max_score_int}",
                        feedback_para
                    ])
                
                # Total row with Paragraphs
                total_label_para = _make_para('TOTAL SCORE', cell_style)
                total_perf_text = f"Overall Performance: {_get_performance_level(score_breakdown['percentage'], use_new_rubric=False)}"
                total_perf_para = _make_para(total_perf_text, cell_style)
                
                # Format total score and percentage as integers
                total_score_int = format_score_for_display(score_breakdown['total_score'])
                total_possible_int = format_score_for_display(score_breakdown['total_possible'])
                percentage_int = int(round(score_breakdown['percentage']))
                
                data.append([
                    total_label_para,
                    f"{percentage_int}%",
                    f"{total_score_int}",
                    f"{total_possible_int}",
                    total_perf_para
                ])
                
                # Build table with proper column widths
                table = _build_wrapped_table(data)
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
                    ('PADDING', (0, 0), (-1, -1), 6),
                    ('WORDWRAP', (0, 0), (-1, -1), 'LTR'),
                ]))
                elements.append(table)
        except Exception as e:
            elements.append(Paragraph(f"Score parsing unavailable: {e}. Raw feedback shown below.", styles['Normal']))
    else:
        # No user input: show zeros and a clear no-evaluation message
        # Create style for table cell paragraphs with word wrapping
        cell_style = ParagraphStyle(
            'TableCell',
            parent=styles['Normal'],
            fontSize=9,
            leading=11,
            wordWrap='LTR'
        )
        
        # Header style
        header_style = ParagraphStyle(
            'TableHeader',
            parent=styles['Normal'],
            fontSize=11,
            leading=13,
            fontName='Helvetica-Bold',
            textColor=colors.whitesmoke,
            wordWrap='LTR'
        )
        
        if NEW_RUBRIC_AVAILABLE:
            # New 40-point rubric categories
            headers = ['MI Category', 'Assessment', 'Score', 'Max Score', 'Notes']
            header_row = [_make_para(h, header_style) for h in headers]
            
            zero_data = [
                header_row,
                [_make_para('Collaboration', cell_style), _make_para('Not Evaluated', cell_style), '0', '9', _make_para('No feedback, no user response', cell_style)],
                [_make_para('Acceptance', cell_style), _make_para('Not Evaluated', cell_style), '0', '6', _make_para('No feedback, no user response', cell_style)],
                [_make_para('Compassion', cell_style), _make_para('Not Evaluated', cell_style), '0', '6', _make_para('No feedback, no user response', cell_style)],
                [_make_para('Evocation', cell_style), _make_para('Not Evaluated', cell_style), '0', '6', _make_para('No feedback, no user response', cell_style)],
                [_make_para('Summary', cell_style), _make_para('Not Evaluated', cell_style), '0', '3', _make_para('No feedback, no user response', cell_style)],
                [_make_para('Response Factor', cell_style), _make_para('Not Evaluated', cell_style), '0', '10', _make_para('No feedback, no user response', cell_style)],
                [_make_para('TOTAL SCORE', cell_style), '0.0%', '0', '40', _make_para('No evaluation performed (no user responses)', cell_style)]
            ]
        else:
            # Old 30-point rubric components
            headers = ['MI Component', 'Status', 'Score', 'Max Score', 'Feedback']
            header_row = [_make_para(h, header_style) for h in headers]
            
            zero_data = [
                header_row,
                [_make_para('Collaboration', cell_style), _make_para('Not Evaluated', cell_style), '0.0', '7.5', _make_para('No feedback, no user response', cell_style)],
                [_make_para('Evocation', cell_style), _make_para('Not Evaluated', cell_style), '0.0', '7.5', _make_para('No feedback, no user response', cell_style)],
                [_make_para('Acceptance', cell_style), _make_para('Not Evaluated', cell_style), '0.0', '7.5', _make_para('No feedback, no user response', cell_style)],
                [_make_para('Compassion', cell_style), _make_para('Not Evaluated', cell_style), '0.0', '7.5', _make_para('No feedback, no user response', cell_style)],
                [_make_para('TOTAL SCORE', cell_style), '0.0%', '0.0', '30.0', _make_para('No evaluation performed (no user responses)', cell_style)]
            ]
        
        # Build table with proper column widths
        table = _build_wrapped_table(zero_data)
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
            ('PADDING', (0, 0), (-1, -1), 6),
            ('WORDWRAP', (0, 0), (-1, -1), 'LTR'),
        ]))
        elements.append(table)

    elements.append(Spacer(1, 20))

    # Improvement Suggestions Section with enhanced formatting
    elements.append(Paragraph("Improvement Suggestions", section_style))
    if has_user_turns:
        suggestions = FeedbackFormatter.extract_suggestions_from_feedback(clean_feedback)
        suggestion_style = ParagraphStyle(
            'Suggestion', parent=styles['Normal'],
            fontSize=11, leading=14, spaceAfter=8
        )
        if suggestions:
            for suggestion in suggestions:
                clean_suggestion = FeedbackValidator.sanitize_special_characters(suggestion)
                # Convert markdown bold to HTML bold for proper PDF rendering
                formatted_suggestion = _format_markdown_to_html(clean_suggestion)
                # Remove bullet characters (•, -, *) from the start but keep the content
                formatted_suggestion = formatted_suggestion.lstrip('•-* \t')
                # Only add paragraph if there's actual content after removing bullets
                if formatted_suggestion:
                    elements.append(Paragraph(formatted_suggestion, suggestion_style))
        else:
            # Fallback: show raw feedback content after component analysis
            feedback_lines = clean_feedback.split('\n')
            category_keywords = ['Collaboration', 'Acceptance', 'Compassion', 'Evocation', 'Summary', 'Response Factor']
            component_keywords = ['COLLABORATION', 'EVOCATION', 'ACCEPTANCE', 'COMPASSION']
            all_keywords = category_keywords + component_keywords
            
            for line in feedback_lines:
                line = line.strip()
                if line and not any(kw in line for kw in all_keywords):
                    if not line.startswith('Session Feedback') and not line.startswith('Evaluation Timestamp'):
                        formatted_line = _format_markdown_to_html(line)
                        elements.append(Paragraph(formatted_line, suggestion_style))
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
