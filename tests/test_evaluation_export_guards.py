import io

from feedback_template import FeedbackValidator
from services.evaluation_service import EvaluationService
from pdf_utils import generate_pdf_report
from persona_guard import detect_persona_drift


PARTIAL_FEEDBACK_WITH_NARRATIVE = """
Collaboration: Fully Met - Strong partnership building.
Acceptance: Fully Met - Excellent reflections.
Compassion: Fully Met - Clear empathy.
Overall Score: 23/40
"""

COMPLETE_FEEDBACK = """
Collaboration: Fully Met - Strong partnership building.
Acceptance: Partially Met - Some missed permission checks.
Compassion: Fully Met - Clear empathy.
Evocation: Partially Met - Good open-ended questions with room for more.
Summary: Fully Met - Excellent summary at close.
Response Factor: Fully Met - Fast and intuitive responses.
"""


def test_evaluation_status_blocks_incomplete_evaluator():
    status = EvaluationService.get_evaluation_status(PARTIAL_FEEDBACK_WITH_NARRATIVE, "HPV")
    assert status["evaluator_complete"] is False
    assert status["pdf_export_allowed"] is False


def test_pdf_validation_detects_zero_score_contradiction():
    contradiction_feedback = """
    Overall strengths: Student demonstrated excellent summary skills.
    """
    result = FeedbackValidator.validate_pdf_payload(contradiction_feedback, "HPV")
    assert result["partial_report"] is True
    assert any("manual review required" in error.lower() or "contradiction" in error.lower() for error in result["errors"])


def test_pdf_diagnostic_mode_removes_numeric_grading_for_partial():
    chat_history = [
        {"role": "assistant", "content": "Hello, I am worried about HPV."},
        {"role": "user", "content": "Can you tell me more?"},
    ]
    pdf_buffer = generate_pdf_report("Test Student", PARTIAL_FEEDBACK_WITH_NARRATIVE, chat_history, "HPV")
    payload = pdf_buffer.getvalue()
    assert len(payload) > 0
    validation = FeedbackValidator.validate_pdf_payload(PARTIAL_FEEDBACK_WITH_NARRATIVE, "HPV")
    assert validation["partial_report"] is True
    assert validation["evaluation_status"]["pdf_export_allowed"] is False


def test_single_source_total_validation_for_complete_result():
    normalized = EvaluationService.build_normalized_result(COMPLETE_FEEDBACK, "HPV")
    assert abs(sum(normalized["category_scores"].values()) - normalized["total_score"]) < 1e-6


def test_provider_style_closure_detected_as_drift():
    has_drift, _ = detect_persona_drift("Anything else I can help with today as your provider?")
    assert has_drift is True
