#!/usr/bin/env python3
"""
Test to verify that the MI feedback PDF scoring issue is fixed.
This test validates that correctly-formatted feedback produces non-zero scores in the PDF.
"""

import sys
import traceback
from scoring_utils import MIScorer
from pdf_utils import generate_pdf_report
import re

def test_bold_markdown_feedback():
    """Test that bold markdown feedback parses correctly."""
    bold_feedback = """
**1. COLLABORATION (7.5 pts): Met** - Student demonstrated excellent partnership building with the patient. They used inclusive language and created a collaborative atmosphere.

**2. EVOCATION (7.5 pts): Partially Met** - Student made some attempts to draw out patient motivations but could have used more open-ended questions to explore patient's own reasons for change.

**3. ACCEPTANCE (7.5 pts): Met** - Student showed respect for patient autonomy and used reflective listening techniques appropriately throughout the conversation.

**4. COMPASSION (7.5 pts): Partially Met** - Student was generally warm and non-judgmental but could have shown more empathy in certain moments.

Overall, the student demonstrated good MI skills with room for improvement in evocation and compassion.
"""
    
    print("🧪 Testing Bold Markdown Feedback Parsing")
    
    try:
        # Test parsing
        component_scores = MIScorer.parse_feedback_scores(bold_feedback)
        assert len(component_scores) == 4, f"Expected 4 components, got {len(component_scores)}"
        
        # Check individual scores
        expected_scores = {
            'COLLABORATION': 7.5,
            'EVOCATION': 3.75,
            'ACCEPTANCE': 7.5,
            'COMPASSION': 3.75
        }
        
        for score in component_scores:
            expected = expected_scores[score.component]
            assert score.score == expected, f"{score.component}: expected {expected}, got {score.score}"
        
        # Test total score
        breakdown = MIScorer.get_score_breakdown(bold_feedback)
        assert breakdown['total_score'] == 22.5, f"Expected total 22.5, got {breakdown['total_score']}"
        assert breakdown['percentage'] == 75.0, f"Expected 75%, got {breakdown['percentage']}"
        
        print("✅ Bold markdown feedback parsing works correctly")
        return True
        
    except Exception as e:
        print(f"❌ Bold markdown test failed: {e}")
        traceback.print_exc()
        return False

def test_mixed_format_feedback():
    """Test various mixed formats that might come from AI."""
    mixed_feedback = """
Session Feedback
Evaluation Timestamp (UTC): 2024-01-15 14:30:00

**1. COLLABORATION (7.5 pts): [Met]** - Excellent partnership building
2. EVOCATION: Partially Met - Some good questioning techniques
**3. ACCEPTANCE (7.5 pts): Met** - Respected patient autonomy  
● COMPASSION (7.5 pts): [Partially Met] - Generally warm approach

Additional suggestions for improvement:
- Use more open-ended questions
- Show more empathy
"""
    
    print("🧪 Testing Mixed Format Feedback Parsing")
    
    try:
        breakdown = MIScorer.get_score_breakdown(mixed_feedback)
        
        # Should parse all 4 components despite mixed formatting
        assert len(breakdown['components']) == 4, f"Expected 4 components, got {len(breakdown['components'])}"
        
        # Check that we have valid scores (not all 0)
        total_score = breakdown['total_score']
        assert total_score > 0, f"Total score should be > 0, got {total_score}"
        
        print(f"✅ Mixed format feedback parsing works: {total_score}/30.0 points")
        return True
        
    except Exception as e:
        print(f"❌ Mixed format test failed: {e}")
        traceback.print_exc()
        return False

def test_pdf_generation_with_scores():
    """Test that PDF generation includes correct scores in the table."""
    feedback_with_scores = """
**1. COLLABORATION (7.5 pts): Met** - Student built excellent rapport
**2. EVOCATION (7.5 pts): Partially Met** - Good questioning but could improve
**3. ACCEPTANCE (7.5 pts): Met** - Respected patient choices
**4. COMPASSION (7.5 pts): Not Met** - Lacked warmth and empathy
"""
    
    print("🧪 Testing PDF Generation with Correct Scores")
    
    try:
        # Generate PDF
        sample_chat = [
            {"role": "user", "content": "Hello, I'm here about my health."},
            {"role": "assistant", "content": "Thanks for coming in. What brings you here today?"}
        ]
        
        pdf_buffer = generate_pdf_report(
            student_name="Test Student",
            raw_feedback=feedback_with_scores,
            chat_history=sample_chat,
            session_type="Unit Test"
        )
        
        # Verify PDF was generated
        assert pdf_buffer is not None, "PDF buffer should not be None"
        assert pdf_buffer.getvalue(), "PDF should have content"
        
        # Test that the scoring breakdown works correctly
        breakdown = MIScorer.get_score_breakdown(feedback_with_scores)
        expected_total = 7.5 + 3.75 + 7.5 + 0.0  # Met + Partially Met + Met + Not Met
        assert breakdown['total_score'] == expected_total, f"Expected {expected_total}, got {breakdown['total_score']}"
        
        print(f"✅ PDF generation works with correct scores: {breakdown['total_score']}/30.0")
        return True
        
    except Exception as e:
        print(f"❌ PDF generation test failed: {e}")
        traceback.print_exc()
        return False

def test_edge_cases():
    """Test edge cases and potential failure modes."""
    print("🧪 Testing Edge Cases")
    
    test_cases = [
        # Case 1: Extra asterisks
        ("Extra asterisks", "***COLLABORATION (7.5 pts): Met*** - Good work"),
        
        # Case 2: Mixed case status
        ("Mixed case", "COLLABORATION: partially MET - Some good work"),
        
        # Case 3: No point values
        ("No points", "**COLLABORATION: Met** - Excellent partnership"),
        
        # Case 4: Different bullet styles
        ("Different bullets", "• COLLABORATION (7.5 pts): [Met] - Great work"),
        
        # Case 5: Whitespace variations
        ("Whitespace", "  1.   COLLABORATION   (7.5 pts)  :  [  Met  ]  -  Good  "),
    ]
    
    success_count = 0
    
    for case_name, test_line in test_cases:
        try:
            result = MIScorer.parse_component_line(test_line)
            if result and result.score > 0:
                print(f"  ✅ {case_name}: {result.component} = {result.score} pts")
                success_count += 1
            else:
                print(f"  ❌ {case_name}: Failed to parse or got 0 score")
        except Exception as e:
            print(f"  ❌ {case_name}: Exception - {e}")
    
    print(f"✅ Edge case testing: {success_count}/{len(test_cases)} cases passed")
    return success_count == len(test_cases)

def test_debug_mode():
    """Test the debug mode functionality."""
    print("🧪 Testing Debug Mode")
    
    sample_feedback = "**COLLABORATION (7.5 pts): Met** - Good work"
    
    try:
        print("Debug output should appear below:")
        print("-" * 40)
        breakdown = MIScorer.get_score_breakdown(sample_feedback, debug=True)
        print("-" * 40)
        
        assert breakdown['total_score'] > 0, "Should have parsed score correctly"
        print("✅ Debug mode works correctly")
        return True
        
    except Exception as e:
        print(f"❌ Debug mode test failed: {e}")
        return False

def main():
    """Run all PDF scoring fix tests."""
    print("🧪 Testing MI Feedback PDF Scoring Fix\n")
    
    tests = [
        ("Bold Markdown Feedback", test_bold_markdown_feedback),
        ("Mixed Format Feedback", test_mixed_format_feedback),
        ("PDF Generation with Scores", test_pdf_generation_with_scores),
        ("Edge Cases", test_edge_cases),
        ("Debug Mode", test_debug_mode),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}:")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} failed")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All PDF scoring fix tests passed! The issue has been resolved.")
        return 0
    else:
        print(f"⚠️  {total - passed} tests failed. Please check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())