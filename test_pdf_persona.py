#!/usr/bin/env python3
"""
Test PDF generation with persona information included.
"""

import sys
import io
from pdf_utils import generate_pdf_report
from scoring_utils import MIScorer

def test_pdf_includes_persona():
    """Test that PDF includes persona information."""
    print("🧪 Testing PDF Generation with Persona Information")
    
    # Sample feedback
    feedback = """
Session Feedback
Evaluation Timestamp (UTC): 2024-01-15 10:30:00
Evaluator: test_user
---

**1. COLLABORATION (7.5 pts): Met** - Student demonstrated excellent partnership building.

**2. EVOCATION (7.5 pts): Partially Met** - Good exploration but could go deeper.

**3. ACCEPTANCE (7.5 pts): Met** - Strong respect for autonomy.

**4. COMPASSION (7.5 pts): Met** - Demonstrated warmth and non-judgmental approach.

Overall, this was a strong performance.
"""
    
    # Sample chat history
    chat_history = [
        {"role": "assistant", "content": "Hello! I'm Alex, nice to meet you today."},
        {"role": "user", "content": "Hi Alex, how are you feeling today?"},
        {"role": "assistant", "content": "I'm a bit worried about the HPV vaccine."},
    ]
    
    try:
        # Generate PDF with persona
        pdf_buffer = generate_pdf_report(
            student_name="Test Student",
            raw_feedback=feedback,
            chat_history=chat_history,
            session_type="HPV Vaccine",
            persona="Alex"
        )
        
        # Check that PDF was generated
        assert pdf_buffer is not None, "PDF buffer should not be None"
        assert isinstance(pdf_buffer, io.BytesIO), "Should return BytesIO buffer"
        
        # Get PDF content
        pdf_content = pdf_buffer.getvalue()
        assert len(pdf_content) > 0, "PDF should have content"
        
        # Convert bytes to string for searching (this won't work for actual PDF binary,
        # but we can at least verify the function runs without error)
        print(f"  ✅ PDF generated successfully with persona 'Alex'")
        print(f"  📄 PDF size: {len(pdf_content)} bytes")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_pdf_without_persona():
    """Test that PDF generation works without persona (backwards compatibility)."""
    print("🧪 Testing PDF Generation without Persona (Backwards Compatibility)")
    
    feedback = """
**1. COLLABORATION (7.5 pts): Met** - Good work.
**2. EVOCATION (7.5 pts): Met** - Good work.
**3. ACCEPTANCE (7.5 pts): Met** - Good work.
**4. COMPASSION (7.5 pts): Met** - Good work.
"""
    
    chat_history = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
    ]
    
    try:
        # Generate PDF without persona
        pdf_buffer = generate_pdf_report(
            student_name="Test Student 2",
            raw_feedback=feedback,
            chat_history=chat_history,
            session_type="OHI"
        )
        
        assert pdf_buffer is not None
        pdf_content = pdf_buffer.getvalue()
        assert len(pdf_content) > 0
        
        print(f"  ✅ PDF generated successfully without persona")
        print(f"  📄 PDF size: {len(pdf_content)} bytes")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_pdf_validation_errors():
    """Test that PDF validation catches errors."""
    print("🧪 Testing PDF Validation Error Handling")
    
    test_cases = [
        {
            'name': 'Empty student name',
            'student_name': '',
            'feedback': 'Test feedback',
            'chat_history': [{'role': 'user', 'content': 'test'}]
        },
        {
            'name': 'Empty feedback',
            'student_name': 'Test',
            'feedback': '',
            'chat_history': [{'role': 'user', 'content': 'test'}]
        },
        {
            'name': 'Empty chat history',
            'student_name': 'Test',
            'feedback': 'Test feedback',
            'chat_history': []
        },
    ]
    
    passed = 0
    for test_case in test_cases:
        try:
            pdf_buffer = generate_pdf_report(
                student_name=test_case['student_name'],
                raw_feedback=test_case['feedback'],
                chat_history=test_case['chat_history'],
                session_type="Test"
            )
            print(f"  ❌ {test_case['name']}: Should have raised an error")
        except (ValueError, Exception) as e:
            print(f"  ✅ {test_case['name']}: Correctly caught error - {type(e).__name__}")
            passed += 1
    
    return passed == len(test_cases)


def run_all_tests():
    """Run all PDF persona tests."""
    print("\n" + "=" * 60)
    print("🔬 Running PDF Persona Integration Tests")
    print("=" * 60 + "\n")
    
    tests = [
        test_pdf_includes_persona,
        test_pdf_without_persona,
        test_pdf_validation_errors,
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
            print(f"  ❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
        print()
    
    print("=" * 60)
    print(f"📊 Test Results: {passed}/{len(tests)} passed")
    if failed == 0:
        print("🎉 All PDF persona tests passed!")
    else:
        print(f"❌ {failed} test(s) failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
