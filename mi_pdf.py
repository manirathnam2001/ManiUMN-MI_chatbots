"""PDF report generation for MI evaluation results.

Replaces ``pdf_utils.py``. Key behavioral differences from the legacy module:

* No ``try/except Exception`` around the scoring section. The input is a
  fully-validated :class:`mi_evaluation.EvaluationResult`, so there is no
  parser to crash. This is the bug that previously caused the table,
  rationales, and recommendations to silently disappear.
* ``EvaluationResult.partial=True`` triggers a clearly-marked **PARTIAL
  REPORT** banner plus a raw-evaluator-response appendix. Whatever was
  successfully scored still renders.
* Empty recommendations + non-partial = "No improvement recommendations —
  performance met all scored criteria." Empty + partial = nothing rendered in
  that section (banner already explains the situation).

Public surface:

* :func:`construct_feedback_filename` — port of the legacy filename helper.
* :func:`generate_pdf_report` — single ReportLab pipeline producing ``bytes``.
"""

from __future__ import annotations

import io
import logging
import re
from typing import Dict, Iterable, List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from mi_evaluation import EvaluationResult, REQUIRED_CATEGORIES


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Filename construction (ported from legacy pdf_utils.construct_feedback_filename)
# ---------------------------------------------------------------------------


def construct_feedback_filename(
    student_name: str,
    bot_name: str,
    persona_name: Optional[str] = None,
) -> str:
    """Return ``[Student]-[Bot]-[Persona] Feedback.pdf``.

    Examples::

        >>> construct_feedback_filename("Mani", "OHI", "Charles")
        'Mani-OHI-Charles Feedback.pdf'
        >>> construct_feedback_filename("John Doe", "HPV", "Diana")
        'John_Doe-HPV-Diana Feedback.pdf'
        >>> construct_feedback_filename("Jane", "Perio", None)
        'Jane-Perio Feedback.pdf'
    """
    if not student_name or not student_name.strip():
        raise ValueError("Student name cannot be empty")
    if not bot_name or not bot_name.strip():
        raise ValueError("Bot name cannot be empty")

    parts = [_sanitize_for_filename(student_name), _sanitize_for_filename(bot_name)]
    if persona_name and persona_name.strip():
        parts.append(_sanitize_for_filename(persona_name))
    return "-".join(parts) + " Feedback.pdf"


def _sanitize_for_filename(value: str) -> str:
    safe = re.sub(r"[^\w\s-]", "", value.strip())
    return re.sub(r"\s+", "_", safe)


# ---------------------------------------------------------------------------
# Text helpers (ported verbatim — these were not the source of the bug)
# ---------------------------------------------------------------------------


def _soft_wrap_long_tokens(text: str, max_len: int = 30) -> str:
    if not text:
        return text
    out: List[str] = []
    for word in text.split():
        if len(word) <= max_len:
            out.append(word)
            continue
        broken = ""
        for i, ch in enumerate(word):
            broken += ch
            if (i + 1) % max_len == 0 and i < len(word) - 1:
                broken += "\u200b"  # zero-width space
        out.append(broken)
    return " ".join(out)


_SAFE_CHAR_REPLACEMENTS = {
    "\u201c": '"', "\u201d": '"',
    "\u2018": "'", "\u2019": "'",
    "\u2013": "-", "\u2014": "--",
    "\u2026": "...",
}


def _sanitize_for_pdf(text: str) -> str:
    if not text:
        return ""
    for old, new in _SAFE_CHAR_REPLACEMENTS.items():
        text = text.replace(old, new)
    return re.sub(r"[^\x20-\x7E\n\r\t]", "", text)


def _markdown_bold_to_html(text: str) -> str:
    return re.sub(r"\*\*([^\*]+?)\*\*", r"<b>\1</b>", text)


def _make_para(text: str, style: ParagraphStyle) -> Paragraph:
    clean = _sanitize_for_pdf(str(text or ""))
    html = _markdown_bold_to_html(clean)
    return Paragraph(_soft_wrap_long_tokens(html, max_len=30), style)


def _build_wrapped_table(data: list, content_width: float = 6.5 * inch) -> Table:
    # Column widths sum to content_width.
    # Category, Assessment, Score, Max, Notes
    col_proportions = [1.1, 1.5, 0.6, 0.6, 2.7]
    total = sum(col_proportions)
    col_widths = [(p / total) * content_width for p in col_proportions]
    return Table(data, colWidths=col_widths)


def _get_performance_level(percentage: float) -> str:
    """Performance band text for the 40-point rubric (matches MIRubric)."""
    if percentage >= 90:
        return "Excellent MI skills demonstrated"
    if percentage >= 75:
        return "Strong MI performance with minor areas for growth"
    if percentage >= 60:
        return "Satisfactory MI foundation, continue practicing"
    if percentage >= 40:
        return "Basic MI awareness, significant practice needed"
    return "Significant improvement needed in MI techniques"


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def generate_pdf_report(
    result: EvaluationResult,
    *,
    student_name: str,
    session_type: str,
    transcript: Iterable[Dict[str, str]],
    timestamp_cst: str,
) -> bytes:
    """Render an :class:`EvaluationResult` as a PDF report.

    ``transcript`` is the chat history (list of ``{"role": ..., "content": ...}``).
    ``timestamp_cst`` is the evaluation timestamp string (already formatted for
    Central Time by :mod:`time_utils`).

    Returns the raw PDF bytes.
    """
    if not student_name or not student_name.strip():
        raise ValueError("Student name cannot be empty")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72,
        title=f"MI Performance Report - {session_type}",
        author="MI Assessment System",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "Title", parent=styles["Heading1"],
        fontSize=20, spaceAfter=20, alignment=1,
        textColor=colors.darkblue, fontName="Helvetica-Bold",
    )
    section_style = ParagraphStyle(
        "Section", parent=styles["Heading2"],
        fontSize=16, spaceBefore=20, spaceAfter=10,
        textColor=colors.darkblue, fontName="Helvetica-Bold",
    )
    info_style = ParagraphStyle(
        "Info", parent=styles["Normal"],
        fontSize=14, spaceAfter=6, fontName="Helvetica-Bold",
    )
    body_style = ParagraphStyle(
        "Body", parent=styles["Normal"],
        fontSize=11, leading=14, spaceAfter=6,
    )
    suggestion_style = ParagraphStyle(
        "Suggestion", parent=styles["Normal"],
        fontSize=11, leading=14, spaceAfter=8,
    )
    cell_style = ParagraphStyle(
        "TableCell", parent=styles["Normal"],
        fontSize=9, leading=11, wordWrap="LTR",
    )
    header_style = ParagraphStyle(
        "TableHeader", parent=styles["Normal"],
        fontSize=11, leading=13, fontName="Helvetica-Bold",
        textColor=colors.whitesmoke, wordWrap="LTR",
    )
    warning_style = ParagraphStyle(
        "Warning", parent=styles["Normal"],
        fontSize=12, textColor=colors.red, spaceAfter=6,
        fontName="Helvetica-Bold",
    )
    convo_style = ParagraphStyle(
        "Convo", parent=styles["Normal"],
        fontSize=10, leading=13, leftIndent=10, rightIndent=10, spaceAfter=4,
    )
    role_style = ParagraphStyle(
        "Role", parent=styles["Normal"],
        fontSize=10, leading=13, leftIndent=10, rightIndent=10, spaceAfter=4,
        fontName="Helvetica-Bold",
    )

    elements: list = []

    # ----- Header -----
    title_text = f"MI Performance Report - {session_type}"
    if result["partial"]:
        title_text += " (PARTIAL)"
    elements.append(Paragraph(title_text, title_style))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph(f"<b>Student:</b> {_sanitize_for_pdf(student_name)}", info_style))
    elements.append(Paragraph(f"<b>Evaluation Date:</b> {_sanitize_for_pdf(timestamp_cst)}", info_style))

    if result["partial"]:
        elements.append(Paragraph(
            "<b>&#9888; PARTIAL REPORT &mdash; MANUAL REVIEW REQUIRED.</b> "
            "The automated evaluator output could not be fully parsed. "
            "Whatever was successfully scored is shown below; raw evaluator response is included as an appendix.",
            warning_style,
        ))

    elements.append(Paragraph("<para align='center'>" + ("\u2500" * 60) + "</para>", body_style))

    # ----- Score Summary table -----
    elements.append(Paragraph("Score Summary", section_style))

    headers = ["MI Category", "Assessment", "Score", "Max", "Notes"]
    table_data: list = [[_make_para(h, header_style) for h in headers]]

    for cat_name in REQUIRED_CATEGORIES:
        cat = result["categories"][cat_name]
        notes_text = cat["rationale"] or "[No rationale provided]"
        if cat["evidence_quote"]:
            notes_text = f"{notes_text}\n\nQuote: \"{cat['evidence_quote']}\""
        table_data.append([
            _make_para(cat_name, cell_style),
            _make_para(cat["assessment"], cell_style),
            f"{int(round(cat['points']))}",
            f"{cat['max_points']}",
            _make_para(notes_text, cell_style),
        ])

    total_score_int = int(round(result["total_score"]))
    pct_int = int(round(result["percentage"]))
    table_data.append([
        _make_para("TOTAL SCORE", cell_style),
        f"{pct_int}%",
        f"{total_score_int}",
        f"{result['max_possible_score']}",
        _make_para(f"Overall: {result['performance_band']}", cell_style),
    ])

    table = _build_wrapped_table(table_data)
    table_style = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 11),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        ("BACKGROUND", (0, 1), (-1, -2), colors.white),
        ("TEXTCOLOR", (0, 1), (-1, -2), colors.black),
        ("FONTNAME", (0, 1), (-1, -2), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -2), 10),
        ("ALIGN", (0, 1), (2, -2), "LEFT"),
        ("ALIGN", (3, 1), (3, -2), "CENTER"),
        ("BACKGROUND", (0, -1), (-1, -1), colors.lightgrey),
        ("TEXTCOLOR", (0, -1), (-1, -1), colors.black),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, -1), (-1, -1), 11),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.lightgrey]),
        ("PADDING", (0, 0), (-1, -1), 6),
        ("WORDWRAP", (0, 0), (-1, -1), "LTR"),
    ])

    # Per-category color coding for the Score column.
    for row_idx, cat_name in enumerate(REQUIRED_CATEGORIES, start=1):
        cat = result["categories"][cat_name]
        pts = int(round(cat["points"]))
        if pts == cat["max_points"]:
            table_style.add("TEXTCOLOR", (2, row_idx), (2, row_idx), colors.green)
            table_style.add("FONTNAME", (2, row_idx), (2, row_idx), "Helvetica-Bold")
        elif pts == 0 and not result["partial"]:
            table_style.add("TEXTCOLOR", (2, row_idx), (2, row_idx), colors.red)
            table_style.add("FONTNAME", (2, row_idx), (2, row_idx), "Helvetica-Bold")

    table.setStyle(table_style)
    elements.append(table)
    elements.append(Spacer(1, 20))

    # ----- Improvement Suggestions -----
    elements.append(Paragraph("Improvement Suggestions", section_style))
    recs = result["recommendations"]
    if recs:
        for rec in recs:
            text = _markdown_bold_to_html(_sanitize_for_pdf(rec)).lstrip("\u2022-* \t")
            if text:
                elements.append(Paragraph(text, suggestion_style))
    elif not result["partial"]:
        elements.append(Paragraph(
            "No improvement recommendations &mdash; performance met all scored criteria.",
            body_style,
        ))
    # If partial AND empty recs, render nothing here (banner already explains).

    elements.append(Spacer(1, 20))

    # ----- Conversation Transcript -----
    elements.append(Paragraph("Conversation Transcript", section_style))
    for msg in transcript or []:
        role = str(msg.get("role", "user")).title()
        content = _sanitize_for_pdf(str(msg.get("content", "")))
        elements.append(Paragraph(f"<b>{role}:</b>", role_style))
        # Wrap long content in 80-char chunks for readability.
        if len(content) > 100:
            words = content.split()
            chunk: List[str] = []
            for word in words:
                chunk.append(word)
                if len(" ".join(chunk)) > 80:
                    elements.append(Paragraph(" ".join(chunk), convo_style))
                    chunk = []
            if chunk:
                elements.append(Paragraph(" ".join(chunk), convo_style))
        else:
            elements.append(Paragraph(content, convo_style))
        elements.append(Spacer(1, 8))

    # ----- Appendix: raw evaluator response (only when partial) -----
    if result["partial"] and result["notes"]:
        elements.append(Spacer(1, 12))
        elements.append(Paragraph("Appendix: Raw Evaluator Response", section_style))
        for line in _sanitize_for_pdf(result["notes"]).splitlines():
            elements.append(Paragraph(line if line.strip() else "&nbsp;", body_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
