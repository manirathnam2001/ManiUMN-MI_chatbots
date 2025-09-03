from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import io

def generate_feedback_pdf(student_name, evaluation_date, mi_data):
    """Generate PDF with MI feedback with 30-point scoring system"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
    elements = []
    styles = getSampleStyleSheet()
    normal_style = styles["Normal"]
    
    # Header
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30
    )
    elements.append(Paragraph(f"MI Performance Feedback", header_style))
    elements.append(Paragraph(f"Student: {student_name}", styles['Normal']))
    elements.append(Paragraph(f"Date: {evaluation_date}", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # MI Components table
    table_data = [
        [[Paragraph("MI Component", normal_style), Paragraph(component_feedback["MI Component"],normal_style)], [Paragraph("Meets Criteria", normal_style), Paragraph(component_feedback["Meets Criteria"],normal_style)], [Paragraph("Feedback", normal_style), Paragraph(component_feedback["Feedback"],normal_style)], [Paragraph("Needs Improvement", normal_style), Paragraph(component_feedback["Needs Improvement"],normal_style)], [Paragraph("Score", normal_style), Paragraph(component_feedback["Score"],normal_style)]]
    ]
    
    components = ['Collaboration', 'Acceptance', 'Compassion', 'Evocation']
    for component in components:
        data = mi_data[component]
        table_data.append([
            component,
            data['meets_criteria'],
            data['feedback'],
            data['needs_improvement'],
            f"{data['score']}/7.5"
        ])
    
    # Calculate total
    total_score = sum(mi_data[component]['score'] for component in components)
    
    table = Table(table_data, colWidths=[120, 320])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 20))
    
    # Summary section
    elements.append(Paragraph("Summary", styles['Heading2']))
    elements.append(Paragraph(f"Total Score: {total_score}/30", styles['Normal']))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("Key Strengths:", styles['Normal']))
    elements.append(Paragraph(mi_data['summary']['strengths'], styles['Normal']))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("Areas for Improvement:", styles['Normal']))
    elements.append(Paragraph(mi_data['summary']['improvements'], styles['Normal']))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer
