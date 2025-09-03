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
    table_data = [[
        Paragraph("<b>MI Component</b>", small_style),
        Paragraph("<b>Meets Criteria</b>", small_style),
        Paragraph("<b>Feedback</b>", small_style),
        Paragraph("<b>Needs Improvement</b>", small_style),
        Paragraph("<b>Score</b>", small_style)
    ]]
    
    components = ['Collaboration', 'Acceptance', 'Compassion', 'Evocation']
   for idx, component in enumerate(components):
        data = mi_data[component]
        table_data.append([
            Paragraph(component, small_style),
            Paragraph(data['meets_criteria'], small_style),
            Paragraph(data['feedback'], small_style),
            Paragraph(data['needs_improvement'], small_style),
            Paragraph(f"{data['score']}/7.5", small_style)
        ])

    # Total score row
    total_score = sum(mi_data[component]['score'] for component in components)
    table_data.append([
        Paragraph("<b>Total</b>", small_style),
        '', '', '',
        Paragraph(f"<b>{total_score}/30</b>", small_style)
    ])

    # Table
    table = Table(table_data, colWidths=[90, 70, 150, 100, 60])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -2), colors.HexColor('#f2f6fa')),  # alternate row color
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#eaf0fb')]),
        ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#d1e7dd')),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#0f5132')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 24))

    # Summary section
    elements.append(Paragraph("Summary", styles['Heading2']))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(f"Total Score: <b>{total_score}/30</b>", styles['Normal']))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("<b>Key Strengths:</b>", styles['Normal']))
    elements.append(Paragraph(mi_data['summary']['strengths'], normal_style))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("<b>Areas for Improvement:</b>", styles['Normal']))
    elements.append(Paragraph(mi_data['summary']['improvements'], normal_style))

    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer
