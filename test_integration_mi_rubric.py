#!/usr/bin/env python3
"""
Integration tests for the new 40-point MI Rubric system.

Tests end-to-end evaluation flow including:
- LLM feedback parsing
- Score calculation
- PDF generation compatibility
- Feedback template integration
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.evaluation_service import EvaluationService
from rubric.mi_rubric import MIRubric, CategoryAssessment, RubricContext
from feedback_template import FeedbackFormatter, FeedbackValidator


def test_hpv_context_evaluation():
    """Test complete HPV evaluation flow."""
    print("🧪 Testing HPV Context Evaluation")
    
    # Simulate realistic LLM feedback for HPV context
    feedback = """
**Collaboration (9 pts): Meets Criteria** - The student introduced themselves warmly and effectively collaborated with the patient by exploring their concerns about HPV vaccination. Did not attempt to "fix" the patient or lecture.

**Acceptance (6 pts): Meets Criteria** - Asked permission before discussing HPV vaccination details and used reflective listening throughout: "It sounds like you're worried about side effects."

**Compassion (6 pts): Meets Criteria** - Demonstrated genuine understanding of the patient's concerns about HPV vaccination. No judgment was shown when the patient expressed hesitation.

**Evocation (6 pts): Meets Criteria** - Used excellent open-ended questions: "What are your thoughts about HPV vaccination?" Supported autonomy and rolled with resistance appropriately.

**Summary (3 pts): Meets Criteria** - Provided a clear summary: "So we've discussed the benefits and your concerns. What would be the next step that feels right for you?"

**Response Factor (10 pts): Meets Criteria** - Responses were timely and showed good understanding throughout the conversation.
"""
    
    # Evaluate the feedback
    result = EvaluationService.evaluate_session(feedback, "HPV Vaccine")
    
    # Verify total score
    assert result['total_score'] == 40, f"Expected 40, got {result['total_score']}"
    assert result['context'] == 'HPV', f"Expected HPV context, got {result['context']}"
    assert result['percentage'] == 100.0
    
    # Verify all categories are present
    expected_categories = ['Collaboration', 'Acceptance', 'Compassion', 'Evocation', 'Summary', 'Response Factor']
    for cat in expected_categories:
        assert cat in result['categories'], f"Missing category: {cat}"
        assert result['categories'][cat]['points'] == result['categories'][cat]['max_points']
    
    # Verify criteria text contains "HPV vaccination" not "oral health"
    collab_criteria = result['categories']['Collaboration']['criteria_text']
    has_hpv = any('HPV vaccination' in c for c in collab_criteria)
    no_oral = not any('oral health' in c for c in collab_criteria)
    
    assert has_hpv, "HPV context should have 'HPV vaccination' in criteria"
    assert no_oral, "HPV context should not have 'oral health' in criteria"
    
    print(f"✅ HPV evaluation: {result['total_score']}/40 - {result['performance_band']}")
    return True


def test_ohi_context_evaluation():
    """Test complete OHI evaluation flow."""
    print("\n🧪 Testing OHI Context Evaluation")
    
    # Simulate realistic LLM feedback for OHI context
    feedback = """
**Collaboration (9 pts): Needs Improvement** - The student introduced themselves but did not effectively build partnership around oral health changes. Tended to lecture rather than collaborate.

**Acceptance (6 pts): Meets Criteria** - Asked permission before discussing oral health details and demonstrated listening with reflections.

**Compassion (6 pts): Meets Criteria** - Showed empathy when discussing the patient's oral health concerns. No judgment was expressed.

**Evocation (6 pts): Needs Improvement** - Used mostly closed-ended questions about oral health. Did not adequately support patient autonomy.

**Summary (3 pts): Needs Improvement** - Did not provide a summary of the conversation or check for accuracy.

**Response Factor (10 pts): Meets Criteria** - Maintained good response time and showed understanding.
"""
    
    # Evaluate the feedback
    result = EvaluationService.evaluate_session(feedback, "OHI")
    
    # Expected: 0 + 6 + 6 + 0 + 0 + 10 = 22
    expected_score = 22
    assert result['total_score'] == expected_score, f"Expected {expected_score}, got {result['total_score']}"
    assert result['context'] == 'OHI', f"Expected OHI context, got {result['context']}"
    
    # Verify specific scores
    assert result['categories']['Collaboration']['points'] == 0
    assert result['categories']['Acceptance']['points'] == 6
    assert result['categories']['Compassion']['points'] == 6
    assert result['categories']['Evocation']['points'] == 0
    assert result['categories']['Summary']['points'] == 0
    assert result['categories']['Response Factor']['points'] == 10
    
    # Verify criteria text contains "oral health" not "HPV vaccination"
    # For Needs Improvement assessments, check "Meets Criteria" text to verify context
    # since "Needs Improvement" criteria don't have the context placeholder
    collab_criteria_meets = MIRubric.get_category_criteria('Collaboration', CategoryAssessment.MEETS_CRITERIA, RubricContext.OHI)
    has_oral = any('oral health' in c for c in collab_criteria_meets)
    no_hpv = not any('HPV vaccination' in c for c in collab_criteria_meets)
    
    assert has_oral, "OHI context should have 'oral health' in criteria"
    assert no_hpv, "OHI context should not have 'HPV vaccination' in criteria"
    
    print(f"✅ OHI evaluation: {result['total_score']}/40 - {result['performance_band']}")
    return True


def test_feedback_template_integration():
    """Test integration with FeedbackFormatter and FeedbackValidator."""
    print("\n🧪 Testing Feedback Template Integration")
    
    feedback = """
**Collaboration (9 pts): Meets Criteria** - Excellent partnership building.

**Acceptance (6 pts): Meets Criteria** - Good reflective listening.

**Compassion (6 pts): Needs Improvement** - Some judgmental language.

**Evocation (6 pts): Meets Criteria** - Strong open-ended questions.

**Summary (3 pts): Needs Improvement** - No summary provided.

**Response Factor (10 pts): Meets Criteria** - Timely responses.
"""
    
    # Test validation
    validation = FeedbackValidator.validate_feedback_completeness(feedback)
    assert validation['is_valid'], "Feedback should be valid"
    assert len(validation['missing_components']) == 0, "No components should be missing"
    
    # Test component breakdown table generation
    table_data = FeedbackFormatter.generate_component_breakdown_table(feedback, "HPV")
    assert len(table_data) == 6, f"Should have 6 categories, got {len(table_data)}"
    
    # Verify table structure
    for row in table_data:
        assert 'component' in row
        assert 'status' in row or 'assessment' in row
        assert 'score' in row
        assert 'feedback' in row or 'notes' in row
    
    print(f"✅ Feedback template integration working correctly")
    return True


def test_evaluation_prompt_format():
    """Test that evaluation prompt has correct format."""
    print("\n🧪 Testing Evaluation Prompt Format")
    
    # Test HPV prompt
    hpv_prompt = FeedbackFormatter.format_evaluation_prompt(
        session_type="HPV Vaccine",
        transcript="Mock transcript",
        rag_context="Mock RAG context"
    )
    
    # Verify new rubric content
    assert "40-point binary" in hpv_prompt, "Prompt should mention 40-point system"
    assert "Collaboration (9 pts)" in hpv_prompt, "Prompt should have Collaboration with 9 pts"
    assert "Response Factor (10 pts)" in hpv_prompt, "Prompt should have Response Factor"
    assert "Meets Criteria" in hpv_prompt and "Needs Improvement" in hpv_prompt
    assert "HPV vaccination" in hpv_prompt, "HPV prompt should have 'HPV vaccination'"
    
    # Test OHI prompt
    ohi_prompt = FeedbackFormatter.format_evaluation_prompt(
        session_type="OHI",
        transcript="Mock transcript",
        rag_context="Mock RAG context"
    )
    
    assert "oral health" in ohi_prompt, "OHI prompt should have 'oral health'"
    assert "HPV vaccination" not in ohi_prompt, "OHI prompt should not have 'HPV vaccination'"
    
    print(f"✅ Evaluation prompts correctly formatted")
    return True


def test_response_factor_with_latency():
    """Test Response Factor automatic assessment from latency."""
    print("\n🧪 Testing Response Factor with Latency Data")
    
    feedback_base = """
**Collaboration (9 pts): Meets Criteria** - Good partnership.
**Acceptance (6 pts): Meets Criteria** - Good listening.
**Compassion (6 pts): Meets Criteria** - Empathetic.
**Evocation (6 pts): Meets Criteria** - Good questions.
**Summary (3 pts): Meets Criteria** - Clear summary.
"""
    
    # Test fast response (should meet criteria)
    fast_feedback = feedback_base + "\n**Response Factor (10 pts): Meets Criteria** - Fast responses."
    fast_result = EvaluationService.evaluate_session(
        fast_feedback,
        "HPV",
        response_latency=2.0,
        response_threshold=2.5
    )
    assert fast_result['categories']['Response Factor']['points'] == 10, "Fast response should get 10 points"
    assert fast_result['total_score'] == 40
    
    # Test slow response (should need improvement)
    slow_feedback = feedback_base + "\n**Response Factor (10 pts): Needs Improvement** - Slow responses."
    slow_result = EvaluationService.evaluate_session(
        slow_feedback,
        "HPV",
        response_latency=3.5,
        response_threshold=2.5
    )
    assert slow_result['categories']['Response Factor']['points'] == 0, "Slow response should get 0 points"
    assert slow_result['total_score'] == 30
    
    print(f"✅ Response Factor latency handling works correctly")
    return True


def test_performance_bands_integration():
    """Test that performance bands are correctly computed."""
    print("\n🧪 Testing Performance Bands")
    
    test_cases = [
        (40, "Excellent", "100% should be Excellent"),
        (36, "Excellent", "90% should be Excellent"),
        (30, "Strong", "75% should be Strong"),
        (24, "Satisfactory", "60% should be Satisfactory"),
        (16, "Basic", "40% should be Basic"),
        (15, "Significant", "37.5% should need Significant improvement")
    ]
    
    for score, expected_keyword, description in test_cases:
        # Calculate percentage and get band
        percentage = (score / 40) * 100
        band = MIRubric.get_performance_band(score)
        
        assert expected_keyword.lower() in band.lower(), \
            f"{description}: expected '{expected_keyword}' in '{band}'"
    
    print(f"✅ All performance bands correct")
    return True


def test_summary_formatting():
    """Test EvaluationService summary formatting."""
    print("\n🧪 Testing Summary Formatting")
    
    feedback = """
**Collaboration (9 pts): Meets Criteria** - Excellent.
**Acceptance (6 pts): Meets Criteria** - Good.
**Compassion (6 pts): Needs Improvement** - Work needed.
**Evocation (6 pts): Meets Criteria** - Strong.
**Summary (3 pts): Needs Improvement** - No summary.
**Response Factor (10 pts): Meets Criteria** - Fast.
"""
    
    result = EvaluationService.evaluate_session(feedback, "HPV")
    summary = EvaluationService.format_evaluation_summary(result)
    
    # Verify summary contains key information
    assert "31/40" in summary or "31" in summary, "Summary should show total score"
    assert "77.5%" in summary or "77" in summary, "Summary should show percentage"
    assert "Category Breakdown" in summary or "Collaboration" in summary, "Summary should show categories"
    
    print(f"✅ Summary formatting works correctly")
    print(f"\nSample Summary:\n{summary}")
    return True


def run_all_integration_tests():
    """Run all integration tests."""
    print("=" * 70)
    print("🔬 Integration Tests: New 40-Point MI Rubric System")
    print("=" * 70)
    
    tests = [
        test_hpv_context_evaluation,
        test_ohi_context_evaluation,
        test_feedback_template_integration,
        test_evaluation_prompt_format,
        test_response_factor_with_latency,
        test_performance_bands_integration,
        test_summary_formatting
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except AssertionError as e:
            print(f"❌ {test.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ {test.__name__} error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"📊 Integration Test Results: {passed}/{len(tests)} passed, {failed} failed")
    print("=" * 70)
    
    if failed == 0:
        print("🎉 All integration tests passed!")
        return True
    else:
        print(f"❌ {failed} integration test(s) failed")
        return False


if __name__ == "__main__":
    success = run_all_integration_tests()
    sys.exit(0 if success else 1)
