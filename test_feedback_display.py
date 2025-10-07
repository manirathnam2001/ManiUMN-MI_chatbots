#!/usr/bin/env python3
"""
Test script to validate feedback display vs PDF formatting.
"""

from feedback_template import FeedbackFormatter


def test_display_format_removes_headers():
    """Test that display format removes headers and shows only core feedback."""
    print("\nTesting display format removes headers...")
    
    # Sample feedback with typical structure
    feedback = """1. COLLABORATION (7.5 pts): Met - Student demonstrated excellent partnership building and rapport development.

2. EVOCATION (7.5 pts): Partially Met - Good exploration of motivations but could go deeper.

3. ACCEPTANCE (7.5 pts): Met - Strong respect for autonomy and reflective listening.

4. COMPASSION (7.5 pts): Met - Demonstrated warmth and non-judgmental approach."""
    
    timestamp = "2025-01-06 14:30:00"
    evaluator = "test_user"
    
    # Test display format
    display_output = FeedbackFormatter.format_feedback_for_display(feedback, timestamp, evaluator)
    
    # Verify display output does NOT contain headers
    assert "MI Performance Report" not in display_output, "Display should not contain 'MI Performance Report' header"
    assert "Evaluation Timestamp" not in display_output, "Display should not contain timestamp header"
    assert "Evaluator:" not in display_output, "Display should not contain evaluator info"
    assert "---" not in display_output, "Display should not contain separator"
    
    # Verify display output DOES contain core feedback
    assert "1. COLLABORATION" in display_output, "Display should contain collaboration feedback"
    assert "2. EVOCATION" in display_output, "Display should contain evocation feedback"
    assert "3. ACCEPTANCE" in display_output, "Display should contain acceptance feedback"
    assert "4. COMPASSION" in display_output, "Display should contain compassion feedback"
    
    print("  ✅ Display format correctly removes headers")
    print(f"  Display output preview:\n{display_output[:150]}...")
    return True


def test_pdf_format_includes_headers():
    """Test that PDF format includes full headers and metadata."""
    print("\nTesting PDF format includes headers...")
    
    # Sample feedback
    feedback = """1. COLLABORATION (7.5 pts): Met - Student demonstrated excellent partnership building.

2. EVOCATION (7.5 pts): Partially Met - Good exploration of motivations."""
    
    timestamp = "2025-01-06 14:30:00"
    evaluator = "test_user"
    
    # Test PDF format
    pdf_output = FeedbackFormatter.format_feedback_for_pdf(feedback, timestamp, evaluator)
    
    # Verify PDF output DOES contain headers
    assert "MI Performance Report" in pdf_output, "PDF should contain 'MI Performance Report' header"
    assert "Evaluation Timestamp (Minnesota):" in pdf_output, "PDF should contain timestamp header"
    assert "Evaluator: test_user" in pdf_output, "PDF should contain evaluator info"
    assert "---" in pdf_output, "PDF should contain separator"
    
    # Verify PDF output also contains the feedback
    assert "1. COLLABORATION" in pdf_output, "PDF should contain collaboration feedback"
    assert "2. EVOCATION" in pdf_output, "PDF should contain evocation feedback"
    
    print("  ✅ PDF format correctly includes headers")
    print(f"  PDF output preview:\n{pdf_output[:200]}...")
    return True


def test_bold_markdown_feedback():
    """Test that feedback with bold markdown formatting is handled correctly."""
    print("\nTesting feedback with bold markdown formatting...")
    
    # Feedback with bold markdown (as produced by AI)
    feedback = """**1. COLLABORATION (7.5 pts): Met** - Student demonstrated excellent partnership building and rapport development.

**2. EVOCATION (7.5 pts): Partially Met** - Good exploration of motivations but could go deeper.

**3. ACCEPTANCE (7.5 pts): Met** - Strong respect for autonomy and reflective listening.

**4. COMPASSION (7.5 pts): Met** - Demonstrated warmth and non-judgmental approach."""
    
    timestamp = "2025-01-06 14:30:00"
    evaluator = "test_user"
    
    # Test display format with bold markdown
    display_output = FeedbackFormatter.format_feedback_for_display(feedback, timestamp, evaluator)
    
    # Verify it starts with the first component
    assert display_output.startswith("**1. COLLABORATION"), "Display should start with first component"
    assert "MI Performance Report" not in display_output, "Display should not contain headers"
    
    print("  ✅ Bold markdown feedback handled correctly")
    return True


def main():
    """Run all tests."""
    print("🧪 Testing Feedback Display Cleanup\n")
    
    tests = [
        ("Display Format Removes Headers", test_display_format_removes_headers),
        ("PDF Format Includes Headers", test_pdf_format_includes_headers),
        ("Bold Markdown Feedback", test_bold_markdown_feedback),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Testing {test_name}:")
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Feedback display cleanup is working correctly.")
        return 0
    else:
        print(f"⚠️  {total - passed} tests failed.")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
