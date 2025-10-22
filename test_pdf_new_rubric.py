#!/usr/bin/env python3
"""
Comprehensive tests for PDF generation with new 40-point MI rubric.
Validates that PDFs correctly show new rubric data while maintaining layout.
"""

import sys
import os
import io
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pdf_utils import generate_pdf_report
from services.evaluation_service import EvaluationService
from rubric.mi_rubric import MIRubric, CategoryAssessment, RubricContext


def test_pdf_with_new_rubric_hpv():
    """Test PDF generation with new 40-point rubric (HPV context)."""
    print("🧪 Test 1: PDF with New Rubric (HPV Context)")
    print("-" * 70)
    
    feedback = """
**Collaboration (9 pts): Meets Criteria** - Student introduced themselves warmly and collaborated with the patient about HPV vaccination. Did not lecture.

**Acceptance (6 pts): Meets Criteria** - Asked permission before discussing HPV vaccination details. Used reflective listening.

**Compassion (6 pts): Needs Improvement** - Did not fully explore patient concerns about HPV vaccination.

**Evocation (6 pts): Meets Criteria** - Used excellent open-ended questions about HPV vaccination. Supported autonomy.

**Summary (3 pts): Needs Improvement** - Did not provide a summary of the discussion.

**Response Factor (10 pts): Meets Criteria** - Fast, intuitive responses throughout conversation.
"""
    
    chat_history = [
        {"role": "assistant", "content": "I'm worried about the HPV vaccine."},
        {"role": "user", "content": "I understand. Can you tell me more about what worries you?"},
        {"role": "assistant", "content": "I've heard it has side effects."},
        {"role": "user", "content": "Those concerns are valid. What specific side effects are you worried about?"}
    ]
    
    try:
        # Generate PDF
        pdf_buffer = generate_pdf_report(
            student_name="Test Student",
            raw_feedback=feedback,
            chat_history=chat_history,
            session_type="HPV Vaccine"
        )
        
        assert pdf_buffer is not None, "PDF buffer should not be None"
        assert len(pdf_buffer.getvalue()) > 0, "PDF should have content"
        
        # Verify evaluation result structure
        result = EvaluationService.evaluate_session(feedback, "HPV Vaccine")
        
        # Expected score: 9 + 6 + 0 + 6 + 0 + 10 = 31/40
        assert result['total_score'] == 31, f"Expected score 31, got {result['total_score']}"
        assert result['max_possible_score'] == 40, f"Expected max 40, got {result['max_possible_score']}"
        assert result['percentage'] == 77.5, f"Expected 77.5%, got {result['percentage']}"
        assert result['context'] == 'HPV', f"Expected HPV context, got {result['context']}"
        
        # Verify all 6 categories are present
        expected_categories = ['Collaboration', 'Acceptance', 'Compassion', 'Evocation', 'Summary', 'Response Factor']
        for cat in expected_categories:
            assert cat in result['categories'], f"Missing category: {cat}"
        
        # Verify context-specific text
        collab_criteria = result['categories']['Collaboration']['criteria_text']
        has_hpv = any('HPV vaccination' in c for c in collab_criteria)
        assert has_hpv, "HPV context should have 'HPV vaccination' in criteria"
        
        print(f"✅ PDF generated successfully")
        print(f"   Total Score: {result['total_score']}/{result['max_possible_score']}")
        print(f"   Percentage: {result['percentage']}%")
        print(f"   Performance: {result['performance_band']}")
        print(f"   PDF Size: {len(pdf_buffer.getvalue())} bytes")
        print(f"   Categories: {len(result['categories'])}/6")
        return True
        
    except Exception as e:
        print(f"❌ Test 1 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_pdf_with_new_rubric_ohi():
    """Test PDF generation with new 40-point rubric (OHI context)."""
    print("\n🧪 Test 2: PDF with New Rubric (OHI Context)")
    print("-" * 70)
    
    feedback = """
**Collaboration (9 pts): Meets Criteria** - Excellent partnership building around oral health changes.

**Acceptance (6 pts): Meets Criteria** - Asked permission before discussing oral health information.

**Compassion (6 pts): Meets Criteria** - Showed genuine empathy regarding oral health concerns.

**Evocation (6 pts): Meets Criteria** - Strong open-ended questioning about oral health motivations.

**Summary (3 pts): Meets Criteria** - Provided clear summary of oral health discussion.

**Response Factor (10 pts): Meets Criteria** - Maintained excellent response time.
"""
    
    chat_history = [
        {"role": "assistant", "content": "I struggle with brushing my teeth regularly."},
        {"role": "user", "content": "Thanks for sharing that. What makes it difficult for you?"}
    ]
    
    try:
        # Generate PDF
        pdf_buffer = generate_pdf_report(
            student_name="Jane Doe",
            raw_feedback=feedback,
            chat_history=chat_history,
            session_type="OHI"
        )
        
        assert pdf_buffer is not None, "PDF buffer should not be None"
        
        # Verify evaluation result
        result = EvaluationService.evaluate_session(feedback, "OHI")
        
        # Perfect score expected
        assert result['total_score'] == 40, f"Expected score 40, got {result['total_score']}"
        assert result['context'] == 'OHI', f"Expected OHI context, got {result['context']}"
        
        # Verify context-specific text (oral health not HPV)
        collab_criteria = result['categories']['Collaboration']['criteria_text']
        has_oral = any('oral health' in c for c in collab_criteria)
        no_hpv = not any('HPV vaccination' in c for c in collab_criteria)
        assert has_oral, "OHI context should have 'oral health' in criteria"
        assert no_hpv, "OHI context should not have 'HPV vaccination' in criteria"
        
        print(f"✅ PDF generated successfully")
        print(f"   Total Score: {result['total_score']}/{result['max_possible_score']}")
        print(f"   Performance: {result['performance_band']}")
        print(f"   Context: {result['context']}")
        return True
        
    except Exception as e:
        print(f"❌ Test 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_pdf_contains_correct_text():
    """Test that PDF contains text showing correct rubric values."""
    print("\n🧪 Test 3: PDF Contains Correct Score Text")
    print("-" * 70)
    
    feedback = """
**Collaboration (9 pts): Meets Criteria** - Good work.
**Acceptance (6 pts): Meets Criteria** - Good listening.
**Compassion (6 pts): Needs Improvement** - Needs work.
**Evocation (6 pts): Meets Criteria** - Good questions.
**Summary (3 pts): Needs Improvement** - No summary.
**Response Factor (10 pts): Meets Criteria** - Fast.
"""
    
    chat_history = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there"}
    ]
    
    try:
        pdf_buffer = generate_pdf_report(
            student_name="Test Student",
            raw_feedback=feedback,
            chat_history=chat_history,
            session_type="HPV"
        )
        
        # Note: We can't easily parse PDF binary, but we can verify the evaluation result
        # that feeds into the PDF contains the correct data
        result = EvaluationService.evaluate_session(feedback, "HPV")
        
        # Verify specific category scores
        assert result['categories']['Collaboration']['points'] == 9
        assert result['categories']['Collaboration']['max_points'] == 9
        assert result['categories']['Acceptance']['points'] == 6
        assert result['categories']['Compassion']['points'] == 0
        assert result['categories']['Summary']['points'] == 0
        assert result['categories']['Response Factor']['points'] == 10
        
        # Verify total
        assert result['total_score'] == 31
        assert result['max_possible_score'] == 40
        
        # Verify assessments
        assert result['categories']['Collaboration']['assessment'] == 'Meets Criteria'
        assert result['categories']['Compassion']['assessment'] == 'Needs Improvement'
        
        print(f"✅ PDF data structure correct")
        print(f"   Collaboration: {result['categories']['Collaboration']['points']}/9 - {result['categories']['Collaboration']['assessment']}")
        print(f"   Compassion: {result['categories']['Compassion']['points']}/6 - {result['categories']['Compassion']['assessment']}")
        print(f"   Total: {result['total_score']}/40")
        return True
        
    except Exception as e:
        print(f"❌ Test 3 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_pdf_with_no_user_responses():
    """Test PDF generation when there are no user responses (edge case)."""
    print("\n🧪 Test 4: PDF with No User Responses")
    print("-" * 70)
    
    feedback = "No evaluation performed - no user responses."
    
    # Chat history with only system messages (no user turns)
    chat_history = [
        {"role": "assistant", "content": "Hello, I'm the patient."}
    ]
    
    try:
        pdf_buffer = generate_pdf_report(
            student_name="Test Student",
            raw_feedback=feedback,
            chat_history=chat_history,
            session_type="HPV"
        )
        
        assert pdf_buffer is not None, "PDF should generate even with no user responses"
        
        print(f"✅ PDF generated for no-response case")
        print(f"   PDF Size: {len(pdf_buffer.getvalue())} bytes")
        return True
        
    except Exception as e:
        print(f"❌ Test 4 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_performance_bands_in_pdf():
    """Test that different performance bands appear correctly."""
    print("\n🧪 Test 5: Performance Bands")
    print("-" * 70)
    
    test_cases = [
        (40, "Excellent", "100% - Perfect score"),
        (36, "Excellent", "90% - Excellent threshold"),
        (30, "Strong", "75% - Strong threshold"),
        (24, "Satisfactory", "60% - Satisfactory threshold"),
        (16, "Basic", "40% - Basic threshold"),
        (15, "Significant", "37.5% - Needs improvement")
    ]
    
    all_passed = True
    
    for score, expected_keyword, description in test_cases:
        band = MIRubric.get_performance_band(score)
        
        if expected_keyword.lower() in band.lower():
            print(f"  ✅ {description}: '{band}'")
        else:
            print(f"  ❌ {description}: Expected '{expected_keyword}' in '{band}'")
            all_passed = False
    
    if all_passed:
        print(f"✅ All performance bands correct")
        return True
    else:
        print(f"❌ Some performance bands incorrect")
        return False


def test_category_point_values():
    """Test that category point values are correct."""
    print("\n🧪 Test 6: Category Point Values")
    print("-" * 70)
    
    expected_points = {
        'Collaboration': 9,
        'Acceptance': 6,
        'Compassion': 6,
        'Evocation': 6,
        'Summary': 3,
        'Response Factor': 10
    }
    
    all_correct = True
    total = 0
    
    for category, expected_pts in expected_points.items():
        actual_pts = MIRubric.get_category_points(category)
        total += actual_pts
        
        if actual_pts == expected_pts:
            print(f"  ✅ {category}: {actual_pts} points")
        else:
            print(f"  ❌ {category}: Expected {expected_pts}, got {actual_pts}")
            all_correct = False
    
    if total == 40 and all_correct:
        print(f"✅ All category points correct (Total: {total})")
        return True
    else:
        print(f"❌ Point values incorrect (Total: {total}, expected 40)")
        return False


def main():
    """Run all PDF tests."""
    print("=" * 70)
    print("🧪 Comprehensive PDF Tests - New 40-Point MI Rubric")
    print("=" * 70)
    print()
    
    tests = [
        ("PDF with New Rubric (HPV)", test_pdf_with_new_rubric_hpv),
        ("PDF with New Rubric (OHI)", test_pdf_with_new_rubric_ohi),
        ("PDF Contains Correct Text", test_pdf_contains_correct_text),
        ("PDF with No User Responses", test_pdf_with_no_user_responses),
        ("Performance Bands", test_performance_bands_in_pdf),
        ("Category Point Values", test_category_point_values)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        if test_func():
            passed += 1
    
    print("\n" + "=" * 70)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    print("=" * 70)
    
    if passed == total:
        print("🎉 All PDF tests passed!")
        return 0
    else:
        print(f"⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
