#!/usr/bin/env python3
"""
Tests for the new 40-point MI Rubric system.

Tests include:
- Perfect score (40/40)
- Zero score (0/40)
- Mixed scoring
- Context substitution (HPV vs OHI)
- Response Factor threshold behavior
- Integration with EvaluationService
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rubric.mi_rubric import (
    MIRubric, MIEvaluator, CategoryAssessment, RubricContext
)
from services.evaluation_service import EvaluationService


def test_perfect_score():
    """Test perfect score of 40/40."""
    print("🧪 Testing Perfect Score (40/40)")
    
    assessments = {
        'Collaboration': CategoryAssessment.MEETS_CRITERIA,
        'Acceptance': CategoryAssessment.MEETS_CRITERIA,
        'Compassion': CategoryAssessment.MEETS_CRITERIA,
        'Evocation': CategoryAssessment.MEETS_CRITERIA,
        'Summary': CategoryAssessment.MEETS_CRITERIA,
        'Response Factor': CategoryAssessment.MEETS_CRITERIA
    }
    
    result = MIEvaluator.evaluate(assessments, RubricContext.HPV)
    
    assert result['total_score'] == 40, f"Expected 40, got {result['total_score']}"
    assert result['max_possible_score'] == 40
    assert result['percentage'] == 100.0
    assert 'Excellent' in result['performance_band']
    
    # Verify all categories have full points
    for category_name in ['Collaboration', 'Acceptance', 'Compassion', 'Evocation', 'Summary', 'Response Factor']:
        cat_data = result['categories'][category_name]
        assert cat_data['points'] == cat_data['max_points'], f"{category_name} should have full points"
        assert cat_data['assessment'] == 'Meets Criteria'
    
    print(f"✅ Perfect score: {result['total_score']}/40 ({result['percentage']:.1f}%)")
    print(f"   Performance: {result['performance_band']}")
    return True


def test_zero_score():
    """Test zero score (0/40)."""
    print("\n🧪 Testing Zero Score (0/40)")
    
    assessments = {
        'Collaboration': CategoryAssessment.NEEDS_IMPROVEMENT,
        'Acceptance': CategoryAssessment.NEEDS_IMPROVEMENT,
        'Compassion': CategoryAssessment.NEEDS_IMPROVEMENT,
        'Evocation': CategoryAssessment.NEEDS_IMPROVEMENT,
        'Summary': CategoryAssessment.NEEDS_IMPROVEMENT,
        'Response Factor': CategoryAssessment.NEEDS_IMPROVEMENT
    }
    
    result = MIEvaluator.evaluate(assessments, RubricContext.HPV)
    
    assert result['total_score'] == 0, f"Expected 0, got {result['total_score']}"
    assert result['max_possible_score'] == 40
    assert result['percentage'] == 0.0
    assert 'Significant improvement' in result['performance_band']
    
    # Verify all categories have 0 points
    for category_name in ['Collaboration', 'Acceptance', 'Compassion', 'Evocation', 'Summary', 'Response Factor']:
        cat_data = result['categories'][category_name]
        assert cat_data['points'] == 0, f"{category_name} should have 0 points"
        assert cat_data['assessment'] == 'Needs Improvement'
    
    print(f"✅ Zero score: {result['total_score']}/40 ({result['percentage']:.1f}%)")
    print(f"   Performance: {result['performance_band']}")
    return True


def test_mixed_scoring():
    """Test mixed scoring scenario."""
    print("\n🧪 Testing Mixed Scoring")
    
    # Collaboration (9) + Acceptance (6) + Evocation (6) = 21/40
    assessments = {
        'Collaboration': CategoryAssessment.MEETS_CRITERIA,  # 9
        'Acceptance': CategoryAssessment.MEETS_CRITERIA,     # 6
        'Compassion': CategoryAssessment.NEEDS_IMPROVEMENT,  # 0
        'Evocation': CategoryAssessment.MEETS_CRITERIA,      # 6
        'Summary': CategoryAssessment.NEEDS_IMPROVEMENT,     # 0
        'Response Factor': CategoryAssessment.NEEDS_IMPROVEMENT  # 0
    }
    
    result = MIEvaluator.evaluate(assessments, RubricContext.HPV)
    
    expected_score = 9 + 6 + 0 + 6 + 0 + 0
    assert result['total_score'] == expected_score, f"Expected {expected_score}, got {result['total_score']}"
    assert result['percentage'] == (expected_score / 40) * 100
    
    # Verify specific categories
    assert result['categories']['Collaboration']['points'] == 9
    assert result['categories']['Acceptance']['points'] == 6
    assert result['categories']['Compassion']['points'] == 0
    assert result['categories']['Evocation']['points'] == 6
    assert result['categories']['Summary']['points'] == 0
    assert result['categories']['Response Factor']['points'] == 0
    
    print(f"✅ Mixed score: {result['total_score']}/40 ({result['percentage']:.1f}%)")
    print(f"   Performance: {result['performance_band']}")
    return True


def test_context_substitution():
    """Test HPV vs OHI context substitution in criteria text."""
    print("\n🧪 Testing Context Substitution")
    
    assessments = {
        'Collaboration': CategoryAssessment.MEETS_CRITERIA,
        'Acceptance': CategoryAssessment.MEETS_CRITERIA,
        'Compassion': CategoryAssessment.MEETS_CRITERIA,
        'Evocation': CategoryAssessment.MEETS_CRITERIA,
        'Summary': CategoryAssessment.MEETS_CRITERIA,
        'Response Factor': CategoryAssessment.MEETS_CRITERIA
    }
    
    # Test HPV context
    result_hpv = MIEvaluator.evaluate(assessments, RubricContext.HPV)
    collab_criteria_hpv = result_hpv['categories']['Collaboration']['criteria_text']
    
    # Should contain "HPV vaccination"
    found_hpv = any('HPV vaccination' in c for c in collab_criteria_hpv)
    assert found_hpv, "HPV context should contain 'HPV vaccination'"
    
    # Test OHI context
    result_ohi = MIEvaluator.evaluate(assessments, RubricContext.OHI)
    collab_criteria_ohi = result_ohi['categories']['Collaboration']['criteria_text']
    
    # Should contain "oral health"
    found_ohi = any('oral health' in c for c in collab_criteria_ohi)
    assert found_ohi, "OHI context should contain 'oral health'"
    
    # Should NOT contain "HPV vaccination"
    no_hpv_in_ohi = not any('HPV vaccination' in c for c in collab_criteria_ohi)
    assert no_hpv_in_ohi, "OHI context should not contain 'HPV vaccination'"
    
    print(f"✅ HPV context: Contains 'HPV vaccination'")
    print(f"✅ OHI context: Contains 'oral health' (not 'HPV vaccination')")
    return True


def test_response_factor_threshold():
    """Test Response Factor threshold behavior."""
    print("\n🧪 Testing Response Factor Threshold")
    
    assessments = {
        'Collaboration': CategoryAssessment.MEETS_CRITERIA,
        'Acceptance': CategoryAssessment.MEETS_CRITERIA,
        'Compassion': CategoryAssessment.MEETS_CRITERIA,
        'Evocation': CategoryAssessment.MEETS_CRITERIA,
        'Summary': CategoryAssessment.MEETS_CRITERIA,
        # Response Factor will be auto-determined from latency
    }
    
    # Test latency below threshold (should meet criteria)
    result_fast = MIEvaluator.evaluate(
        assessments, 
        RubricContext.HPV,
        response_factor_latency=2.0,  # Below 2.5s threshold
        response_factor_threshold=2.5
    )
    assert result_fast['categories']['Response Factor']['points'] == 10, "Fast response should get 10 points"
    assert result_fast['total_score'] == 40
    
    # Test latency above threshold (should need improvement)
    result_slow = MIEvaluator.evaluate(
        assessments,
        RubricContext.HPV,
        response_factor_latency=3.5,  # Above 2.5s threshold
        response_factor_threshold=2.5
    )
    assert result_slow['categories']['Response Factor']['points'] == 0, "Slow response should get 0 points"
    assert result_slow['total_score'] == 30  # 40 - 10
    
    # Test boundary case (exactly at threshold)
    result_boundary = MIEvaluator.evaluate(
        assessments,
        RubricContext.HPV,
        response_factor_latency=2.5,  # Exactly at threshold
        response_factor_threshold=2.5
    )
    assert result_boundary['categories']['Response Factor']['points'] == 10, "Boundary should meet criteria"
    
    print(f"✅ Fast response (2.0s): {result_fast['categories']['Response Factor']['points']}/10")
    print(f"✅ Slow response (3.5s): {result_slow['categories']['Response Factor']['points']}/10")
    print(f"✅ Boundary (2.5s): {result_boundary['categories']['Response Factor']['points']}/10")
    return True


def test_performance_bands():
    """Test all performance band thresholds."""
    print("\n🧪 Testing Performance Bands")
    
    test_cases = [
        (40, "Excellent"),      # 100% - Excellent
        (36, "Excellent"),      # 90% - Excellent
        (35, "Strong"),         # 87.5% - Strong
        (30, "Strong"),         # 75% - Strong
        (29, "Satisfactory"),   # 72.5% - Satisfactory
        (24, "Satisfactory"),   # 60% - Satisfactory
        (23, "Basic"),          # 57.5% - Basic
        (16, "Basic"),          # 40% - Basic
        (15, "Significant"),    # 37.5% - Significant improvement
        (0, "Significant")      # 0% - Significant improvement
    ]
    
    for score, expected_keyword in test_cases:
        # Calculate percentage
        percentage = (score / 40) * 100
        band = MIRubric.get_performance_band(score)
        
        # Check that expected keyword is in band message
        assert expected_keyword.lower() in band.lower(), \
            f"Score {score} ({percentage:.1f}%) should contain '{expected_keyword}', got '{band}'"
    
    print(f"✅ All performance band thresholds correct")
    return True


def test_evaluation_service_parsing():
    """Test EvaluationService parsing of LLM feedback."""
    print("\n🧪 Testing EvaluationService Parsing")
    
    # Simulate LLM feedback
    feedback = """
**Collaboration (9 pts): Meets Criteria** - Excellent partnership building and rapport.

**Acceptance (6 pts): Meets Criteria** - Asked permission and used reflections well.

**Compassion (6 pts): Needs Improvement** - Some judgment detected in tone.

**Evocation (6 pts): Meets Criteria** - Good open-ended questions and autonomy support.

**Summary (3 pts): Needs Improvement** - Did not provide adequate summary.

**Response Factor (10 pts): Meets Criteria** - Responses were timely and appropriate.
"""
    
    # Parse assessments
    assessments = EvaluationService.parse_llm_feedback(feedback)
    
    assert assessments['Collaboration'] == CategoryAssessment.MEETS_CRITERIA
    assert assessments['Acceptance'] == CategoryAssessment.MEETS_CRITERIA
    assert assessments['Compassion'] == CategoryAssessment.NEEDS_IMPROVEMENT
    assert assessments['Evocation'] == CategoryAssessment.MEETS_CRITERIA
    assert assessments['Summary'] == CategoryAssessment.NEEDS_IMPROVEMENT
    assert assessments['Response Factor'] == CategoryAssessment.MEETS_CRITERIA
    
    # Test full evaluation
    result = EvaluationService.evaluate_session(feedback, "HPV")
    
    # Expected: 9 + 6 + 0 + 6 + 0 + 10 = 31
    assert result['total_score'] == 31, f"Expected 31, got {result['total_score']}"
    
    print(f"✅ Parsed LLM feedback correctly")
    print(f"   Total score: {result['total_score']}/40")
    return True


def test_context_determination():
    """Test automatic context determination from session type."""
    print("\n🧪 Testing Context Determination")
    
    hpv_variations = ["HPV", "hpv", "HPV Vaccine", "HPV vaccination"]
    ohi_variations = ["OHI", "ohi", "Oral Health", "oral hygiene"]
    
    for session_type in hpv_variations:
        context = EvaluationService.determine_context(session_type)
        assert context == RubricContext.HPV, f"'{session_type}' should be HPV context"
    
    for session_type in ohi_variations:
        context = EvaluationService.determine_context(session_type)
        assert context == RubricContext.OHI, f"'{session_type}' should be OHI context"
    
    print(f"✅ Context determination works for all variations")
    return True


def run_all_tests():
    """Run all tests and report results."""
    print("=" * 60)
    print("🔬 Testing New 40-Point MI Rubric System")
    print("=" * 60)
    
    tests = [
        test_perfect_score,
        test_zero_score,
        test_mixed_scoring,
        test_context_substitution,
        test_response_factor_threshold,
        test_performance_bands,
        test_evaluation_service_parsing,
        test_context_determination
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
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{len(tests)} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("🎉 All tests passed!")
        return True
    else:
        print(f"❌ {failed} test(s) failed")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
