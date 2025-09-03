"""
Utility functions for generating PDF reports for MI performance feedback.
"""
import io
import re
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch


def parse_feedback_response(feedback_text):
    """
    Parse the AI-generated feedback response to extract structured data for each MI component.
    
    Args:
        feedback_text (str): The raw feedback response from the AI
        
    Returns:
        dict: Structured feedback data with scores and comments for each MI component
    """
    # Default structure for MI components
    components = {
        'collaboration': {'score': 'Not Assessed', 'feedback': '', 'improvement': ''},
        'evocation': {'score': 'Not Assessed', 'feedback': '', 'improvement': ''},
        'acceptance': {'score': 'Not Assessed', 'feedback': '', 'improvement': ''},
        'compassion': {'score': 'Not Assessed', 'feedback': '', 'improvement': ''},
        'summary': {'score': 'Not Assessed', 'feedback': '', 'improvement': ''}
    }
    
    # Split feedback into lines for structured parsing
    lines = feedback_text.split('\n')
    text = feedback_text.lower()
    
    # Enhanced score patterns - more specific matching
    score_patterns = [
        (r'\bpartially met\b', 'Partially Met'),
        (r'\bnot met\b', 'Not Met'),
        (r'\bmet\b(?!\s+(criteria|standards|expectations))', 'Met'),
        (r'\bnot yet\b', 'Not Yet'),
        (r'\bneeds improvement\b', 'Needs Improvement'),
        (r'\bexceeds\b', 'Exceeds Expectations')
    ]
    
    # Look for numbered structure first (1. COLLABORATION: ...)
    numbered_pattern = r'(\d+)\.\s*(collaboration|evocation|acceptance|compassion|summary):\s*(.*)'
    matches = re.findall(numbered_pattern, feedback_text, re.IGNORECASE | re.MULTILINE)
    
    for match in matches:
        component = match[1].lower()
        content = match[2].strip()
        
        if component in components:
            # Extract score from the beginning of content
            score = 'Not Assessed'
            for pattern, score_value in score_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    score = score_value
                    break
            
            # Extract feedback (everything after the score until suggestions)
            feedback_content = re.sub(r'^(met|partially met|not met|not yet|needs improvement|exceeds)\s*[-–]\s*', '', content, flags=re.IGNORECASE)
            
            # Split into feedback and improvement if there are improvement keywords
            improvement_keywords = ['suggest', 'improve', 'next time', 'better', 'could', 'should', 'try', 'practice', 'focus on']
            sentences = re.split(r'[.!?]+', feedback_content)
            
            feedback_sentences = []
            improvement_sentences = []
            
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) < 10:
                    continue
                    
                if any(keyword in sentence.lower() for keyword in improvement_keywords):
                    improvement_sentences.append(sentence)
                elif len(feedback_sentences) < 2:
                    feedback_sentences.append(sentence)
            
            components[component]['score'] = score
            components[component]['feedback'] = ('. '.join(feedback_sentences)[:200] + '.') if feedback_sentences else f"Assessment of {component} skills completed."
            components[component]['improvement'] = ('. '.join(improvement_sentences[:1])[:200] + '.') if improvement_sentences else f"Continue practicing {component} techniques."
    
    # Fallback: look for section headers if numbered format not found
    if all(comp['score'] == 'Not Assessed' for comp in components.values()):
        for component in components.keys():
            # Look for section headers like "### Collaboration:" or "**Collaboration:**"
            patterns = [
                rf'#{1,3}\s*{component}:\s*(.*?)(?=#{1,3}|\*\*|$)',
                rf'\*\*{component}:\*\*\s*(.*?)(?=\*\*|$)',
                rf'{component}:\s*(.*?)(?=\n\s*[A-Z]|$)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, feedback_text, re.IGNORECASE | re.DOTALL)
                if match:
                    content = match.group(1).strip()
                    
                    # Extract score
                    score = 'Not Assessed'
                    for score_pattern, score_value in score_patterns:
                        if re.search(score_pattern, content, re.IGNORECASE):
                            score = score_value
                            break
                    
                    # Clean content
                    content = re.sub(r'^(met|partially met|not met|not yet|needs improvement|exceeds)\s*[-–]\s*', '', content, flags=re.IGNORECASE)
                    content = content.split('\n')[0]  # Take first line for feedback
                    
                    components[component]['score'] = score
                    components[component]['feedback'] = content[:200] + ('.' if content and not content.endswith('.') else '')
                    components[component]['improvement'] = f"Continue practicing {component} techniques to strengthen MI skills."
                    break
    
    # Final fallback: provide generic feedback based on overall tone
    if all(comp['score'] == 'Not Assessed' for comp in components.values()):
        # Try to infer general performance level from text
        if any(phrase in text for phrase in ['excellent', 'outstanding', 'strong', 'good']):
            default_score = 'Met'
        elif any(phrase in text for phrase in ['some', 'partial', 'room for improvement']):
            default_score = 'Partially Met'
        else:
            default_score = 'Not Met'
        
        for component in components.keys():
            components[component]['score'] = default_score
            components[component]['feedback'] = f"General assessment suggests {default_score.lower()} performance in {component} skills."
            components[component]['improvement'] = f"Focus on strengthening {component} techniques in future MI sessions."
    
    return components


def calculate_total_score(components):
    """
    Calculate total score out of 30 points (6 points per component).
    
    Args:
        components (dict): Structured feedback data for MI components
        
    Returns:
        tuple: (total_score, max_score)
    """
    score_values = {
        'Met': 6,
        'Exceeds Expectations': 6,
        'Partially Met': 3,
        'Not Met': 0,
        'Not Yet': 0,
        'Needs Improvement': 1,
        'Not Assessed': 0
    }
    
    total_score = 0
    max_score = 30  # 6 points × 5 components
    
    for component_data in components.values():
        score = component_data.get('score', 'Not Assessed')
        total_score += score_values.get(score, 0)
    
    return total_score, max_score


def generate_pdf_report(student_name, components, session_type="MI Practice"):
    """
    Generate a PDF report with MI performance feedback in structured table format.
    
    Args:
        student_name (str): Name of the student
        components (dict): Structured feedback data for MI components
        session_type (str): Type of MI session (e.g., "HPV", "Oral Hygiene")
        
    Returns:
        io.BytesIO: PDF file as bytes
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=18)
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1  # Center alignment
    )
    
    # Title
    title = Paragraph(f"Motivational Interviewing Performance Report<br/>{session_type} Session", title_style)
    elements.append(title)
    
    # Student information
    eval_date = datetime.now().strftime("%B %d, %Y")
    total_score, max_score = calculate_total_score(components)
    
    info_style = ParagraphStyle('Info', parent=styles['Normal'], fontSize=12, spaceAfter=6)
    elements.append(Paragraph(f"<b>Student Name:</b> {student_name}", info_style))
    elements.append(Paragraph(f"<b>Evaluation Date:</b> {eval_date}", info_style))
    elements.append(Paragraph(f"<b>Total Score:</b> {total_score}/{max_score} points", info_style))
    elements.append(Spacer(1, 20))
    
    # Feedback table
    table_data = [
        ["MI Component", "Score", "Feedback", "Areas for Improvement"]
    ]
    
    component_names = {
        'collaboration': 'Collaboration',
        'evocation': 'Evocation',
        'acceptance': 'Acceptance',
        'compassion': 'Compassion',
        'summary': 'Summary & Closure'
    }
    
    for component_key, component_name in component_names.items():
        component_data = components.get(component_key, {})
        score = component_data.get('score', 'Not Assessed')
        feedback = component_data.get('feedback', 'No specific feedback provided')
        improvement = component_data.get('improvement', 'Continue practicing MI skills')
        
        # Wrap long text for better table formatting
        if len(feedback) > 100:
            feedback = feedback[:97] + "..."
        if len(improvement) > 100:
            improvement = improvement[:97] + "..."
            
        table_data.append([
            component_name,
            score,
            feedback,
            improvement
        ])
    
    # Create table
    table = Table(table_data, colWidths=[1.5*inch, 1.2*inch, 2.5*inch, 2.5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
    ]))
    
    elements.append(table)
    
    # Scoring guide
    elements.append(Spacer(1, 30))
    scoring_title = Paragraph("<b>Scoring Guide:</b>", styles['Heading3'])
    elements.append(scoring_title)
    
    scoring_info = """
    <b>Met (6 points):</b> Demonstrates proficient use of MI skills<br/>
    <b>Partially Met (3 points):</b> Shows some evidence of MI skills with room for improvement<br/>
    <b>Not Met (0 points):</b> Minimal or no evidence of MI skills<br/>
    <b>Total Possible Score:</b> 30 points (6 points per component)
    """
    scoring_paragraph = Paragraph(scoring_info, styles['Normal'])
    elements.append(scoring_paragraph)
    
    # Build PDF
    doc.build(elements)
    
    buffer.seek(0)
    return buffer