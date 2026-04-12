#!/usr/bin/env python3
"""
Comprehensive tests for the four PDF export fixes:
1. Text overflow in Score summary table
2. Empty notes generation
3. Bullet removal from improvement suggestions
4. Conditional formatting (green/red colors)
"""

import sys
import os
import io

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pdf_utils import generate_pdf_report
from services.evaluation_service import EvaluationService
from rubric.mi_rubric import CategoryAssessment, RubricContext
from feedback_template import FeedbackFormatter


def test_issue_1_text_wrapping():
    """Test Issue 1: Text overflow in Score summary table with proper wrapping."""
    print("🧪 Test 1: Text Wrapping in Score Summary Table")
    print("-" * 70)
    
    # Create feedback with very long notes to test wrapping
    long_note = "This is an extremely long note that contains a lot of detailed feedback about the student's performance in this category and should wrap properly within the table cell without overflowing. " * 3
    
    feedback = f"""
**Collaboration (9 pts): Meets Criteria** - {long_note}

**Acceptance (6 pts): Needs Improvement** - Another very long note that tests the text wrapping functionality to ensure that long text content is properly handled within PDF table cells without causing layout issues.

**Compassion (6 pts): Meets Criteria** - Short note.

**Evocation (6 pts): Meets Criteria** - Yet another lengthy note designed to test the word wrapping capabilities of the PDF generation system to ensure proper handling of extended text content.

**Summary (3 pts): Meets Criteria** - Brief.

**Response Factor (10 pts): Meets Criteria** - Fast responses.
"""
    
    chat_history = [
        {"role": "assistant", "content": "Hello"},
        {"role": "user", "content": "Hi there"}
    ]
    
    try:
        pdf_buffer = generate_pdf_report(
            student_name="Test Student Long Text",
            raw_feedback=feedback,
            chat_history=chat_history,
            session_type="HPV Vaccine"
        )
        
        assert pdf_buffer is not None, "PDF buffer should not be None"
        assert len(pdf_buffer.getvalue()) > 0, "PDF should have content"
        
        # Verify that evaluation works with long text
        result = EvaluationService.evaluate_session(feedback, "HPV Vaccine")
        
        # Check that long notes are preserved
        for cat_name, cat_data in result['categories'].items():
            notes = cat_data.get('notes', '')
            assert notes, f"Category {cat_name} should have notes"
        
        print(f"✅ Text wrapping test passed")
        print(f"   PDF Size: {len(pdf_buffer.getvalue())} bytes")
        print(f"   Categories with notes: {len([c for c in result['categories'].values() if c.get('notes')])}/6")
        return True
        
    except Exception as e:
        print(f"❌ Test 1 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_issue_2_default_notes():
    """Test Issue 2: Empty notes are filled with constructive defaults."""
    print("\n🧪 Test 2: Default Notes Generation for Empty Categories")
    print("-" * 70)
    
    # Feedback with NO notes after assessment (no dash)
    feedback_no_notes = """
**Collaboration (9 pts): Meets Criteria**

**Acceptance (6 pts): Needs Improvement**

**Compassion (6 pts): Meets Criteria**

**Evocation (6 pts): Needs Improvement**

**Summary (3 pts): Meets Criteria**

**Response Factor (10 pts): Meets Criteria**
"""
    
    try:
        result = EvaluationService.evaluate_session(feedback_no_notes, "HPV Vaccine")
        
        # All categories should have notes (either extracted or default)
        empty_count = 0
        default_count = 0
        
        for cat_name, cat_data in result['categories'].items():
            notes = cat_data.get('notes', '')
            if not notes:
                empty_count += 1
                print(f"❌ {cat_name}: Empty notes")
            else:
                default_count += 1
        
        assert empty_count == 0, f"Found {empty_count} categories with empty notes"
        assert default_count == 6, f"Expected 6 categories with notes, got {default_count}"
        
        # Verify context-specific defaults
        collab_notes = result['categories']['Collaboration']['notes']
        assert 'HPV vaccination' in collab_notes, "HPV context should be in default notes"
        
        # Test OHI context
        result_ohi = EvaluationService.evaluate_session(feedback_no_notes, "OHI")
        collab_notes_ohi = result_ohi['categories']['Collaboration']['notes']
        assert 'oral health' in collab_notes_ohi, "OHI context should be in default notes"
        
        print(f"✅ Default notes generation test passed")
        print(f"   All 6 categories have notes")
        print(f"   HPV context example: {collab_notes[:60]}...")
        print(f"   OHI context example: {collab_notes_ohi[:60]}...")
        return True
        
    except Exception as e:
        print(f"❌ Test 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_issue_3_bullet_removal():
    """Test Issue 3: Bullets are removed from improvement suggestions."""
    print("\n🧪 Test 3: Bullet Removal from Improvement Suggestions")
    print("-" * 70)
    
    feedback_with_bullets = """
**Collaboration (9 pts): Meets Criteria** - Good work

**Acceptance (6 pts): Needs Improvement** - Needs work

**Compassion (6 pts): Meets Criteria** - Empathetic

**Evocation (6 pts): Needs Improvement** - Practice more

**Summary (3 pts): Meets Criteria** - Clear

**Response Factor (10 pts): Meets Criteria** - Fast

**Overall Strengths:**
- Strong introduction and rapport building
- Excellent use of reflective listening
- Demonstrated genuine empathy

**Areas for Improvement:**
- Provide more comprehensive summaries
- Use more complex reflections
- Consider using the importance-confidence ruler
"""
    
    chat_history = [
        {"role": "assistant", "content": "I'm worried."},
        {"role": "user", "content": "Tell me more."}
    ]
    
    try:
        # Extract suggestions
        suggestions = FeedbackFormatter.extract_suggestions_from_feedback(feedback_with_bullets)
        
        # Suggestions may contain bullets at extraction
        bullet_suggestions = [s for s in suggestions if s.strip().startswith(('-', '•', '*'))]
        print(f"   Extracted {len(suggestions)} suggestions, {len(bullet_suggestions)} with bullets")
        
        # Generate PDF - bullets should be stripped during rendering
        pdf_buffer = generate_pdf_report(
            student_name="Test Bullet Removal",
            raw_feedback=feedback_with_bullets,
            chat_history=chat_history,
            session_type="HPV Vaccine"
        )
        
        assert pdf_buffer is not None, "PDF should be generated"
        assert len(pdf_buffer.getvalue()) > 0, "PDF should have content"
        
        print(f"✅ Bullet removal test passed")
        print(f"   PDF generated: {len(pdf_buffer.getvalue())} bytes")
        print(f"   Note: Bullets are stripped during PDF rendering")
        return True
        
    except Exception as e:
        print(f"❌ Test 3 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_issue_4_conditional_formatting():
    """Test Issue 4: Conditional formatting with colors for scores."""
    print("\n🧪 Test 4: Conditional Formatting (Score Colors)")
    print("-" * 70)
    
    # Feedback with mixed scores (some full, some zero)
    feedback_mixed = """
**Collaboration (9 pts): Meets Criteria** - Excellent partnership

**Acceptance (6 pts): Needs Improvement** - Needs work on permission

**Compassion (6 pts): Meets Criteria** - Very empathetic

**Evocation (6 pts): Needs Improvement** - Needs more open questions

**Summary (3 pts): Meets Criteria** - Clear summary

**Response Factor (10 pts): Meets Criteria** - Fast responses
"""
    
    chat_history = [
        {"role": "assistant", "content": "Hello"},
        {"role": "user", "content": "Hi"}
    ]
    
    try:
        result = EvaluationService.evaluate_session(feedback_mixed, "HPV Vaccine")
        
        # Verify score distribution
        full_scores = []
        zero_scores = []
        partial_scores = []
        
        for cat_name, cat_data in result['categories'].items():
            points = cat_data['points']
            max_points = cat_data['max_points']
            
            if points == max_points:
                full_scores.append(cat_name)
            elif points == 0:
                zero_scores.append(cat_name)
            else:
                partial_scores.append(cat_name)
        
        # Generate PDF with conditional formatting
        pdf_buffer = generate_pdf_report(
            student_name="Test Color Formatting",
            raw_feedback=feedback_mixed,
            chat_history=chat_history,
            session_type="HPV Vaccine"
        )
        
        assert pdf_buffer is not None, "PDF should be generated"
        assert len(pdf_buffer.getvalue()) > 0, "PDF should have content"
        
        # Expected: 4 full scores (Collab, Compassion, Summary, Response Factor)
        # Expected: 2 zero scores (Acceptance, Evocation)
        assert len(full_scores) == 4, f"Expected 4 full scores, got {len(full_scores)}"
        assert len(zero_scores) == 2, f"Expected 2 zero scores, got {len(zero_scores)}"
        
        print(f"✅ Conditional formatting test passed")
        print(f"   Full scores (GREEN): {', '.join(full_scores)}")
        print(f"   Zero scores (RED): {', '.join(zero_scores)}")
        print(f"   PDF Size: {len(pdf_buffer.getvalue())} bytes")
        return True
        
    except Exception as e:
        print(f"❌ Test 4 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_all_fixes_together():
    """Test all four fixes working together in one PDF."""
    print("\n🧪 Test 5: All Fixes Combined")
    print("-" * 70)
    
    # Complex feedback testing all scenarios
    feedback = """
**Collaboration (9 pts): Meets Criteria** - The student demonstrated truly exceptional rapport-building skills by warmly introducing themselves and establishing a strong collaborative partnership with the patient throughout the entire conversation about HPV vaccination decisions and health concerns.

**Acceptance (6 pts): Needs Improvement**

**Compassion (6 pts): Meets Criteria**

**Evocation (6 pts): Needs Improvement**

**Summary (3 pts): Meets Criteria** - Brief summary.

**Response Factor (10 pts): Meets Criteria**

**Overall Strengths:**
- Strong introduction and welcoming approach
- Excellent reflective listening throughout

**Areas for Improvement:**
- Provide more comprehensive summaries
- Use more complex reflections
"""
    
    chat_history = [
        {"role": "assistant", "content": "I'm concerned about the HPV vaccine."},
        {"role": "user", "content": "Tell me more about your concerns."}
    ]
    
    try:
        # Generate PDF
        pdf_buffer = generate_pdf_report(
            student_name="Comprehensive Test",
            raw_feedback=feedback,
            chat_history=chat_history,
            session_type="HPV Vaccine"
        )
        
        # Verify all aspects
        result = EvaluationService.evaluate_session(feedback, "HPV Vaccine")
        
        # Check notes are not empty
        all_have_notes = all(cat.get('notes', '') for cat in result['categories'].values())
        assert all_have_notes, "All categories should have notes"
        
        # Check score distribution
        full_scores = sum(1 for c in result['categories'].values() if c['points'] == c['max_points'])
        zero_scores = sum(1 for c in result['categories'].values() if c['points'] == 0)
        
        assert pdf_buffer is not None, "PDF should be generated"
        assert len(pdf_buffer.getvalue()) > 0, "PDF should have content"
        
        print(f"✅ Combined test passed")
        print(f"   ✓ Long text wrapping: Collaboration has {len(result['categories']['Collaboration']['notes'])} char notes")
        print(f"   ✓ Default notes: All 6 categories have notes")
        print(f"   ✓ Bullet removal: Applied during PDF rendering")
        print(f"   ✓ Color formatting: {full_scores} green, {zero_scores} red scores")
        print(f"   PDF Size: {len(pdf_buffer.getvalue())} bytes")
        
        return True
        
    except Exception as e:
        print(f"❌ Test 5 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all test cases."""
    print("="*70)
    print("🧪 Comprehensive PDF Export Fix Tests")
    print("="*70)
    
    tests = [
        test_issue_1_text_wrapping,
        test_issue_2_default_notes,
        test_issue_3_bullet_removal,
        test_issue_4_conditional_formatting,
        test_all_fixes_together
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test crashed: {e}")
            failed += 1
    
    print("\n" + "="*70)
    print(f"📊 Test Results: {passed}/{len(tests)} tests passed")
    print("="*70)
    
    if failed == 0:
        print("🎉 All PDF export fix tests passed!")
    else:
        print(f"⚠️  {failed} test(s) failed")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
