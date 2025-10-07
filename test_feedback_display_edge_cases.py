#!/usr/bin/env python3
"""
Edge case tests for feedback display formatting.
"""

from feedback_template import FeedbackFormatter


def test_feedback_without_collaboration_marker():
    """Test feedback that doesn't start with '1. COLLABORATION' marker."""
    print("\nTesting feedback without collaboration marker...")
    
    # Feedback without standard markers
    feedback = """This is some general feedback about the student's performance.

The student did well overall but needs improvement in several areas."""
    
    timestamp = "2025-01-06 14:30:00"
    evaluator = "test_user"
    
    # Test display format - should return full feedback if no marker found
    display_output = FeedbackFormatter.format_feedback_for_display(feedback, timestamp, evaluator)
    
    # Since no marker is found, it should return the full feedback content
    assert "This is some general feedback" in display_output, "Display should contain the feedback"
    assert "MI Performance Report" not in display_output, "Display should not add headers"
    
    print("  ✅ Feedback without markers handled correctly")
    print(f"  Display output: {display_output[:100]}...")
    return True


def test_empty_feedback():
    """Test empty feedback string."""
    print("\nTesting empty feedback...")
    
    feedback = ""
    timestamp = "2025-01-06 14:30:00"
    evaluator = "test_user"
    
    # Test display format
    display_output = FeedbackFormatter.format_feedback_for_display(feedback, timestamp, evaluator)
    
    # Should return empty string
    assert display_output == "", "Display should be empty for empty feedback"
    
    print("  ✅ Empty feedback handled correctly")
    return True


def test_feedback_with_header_already_removed():
    """Test that feedback already formatted for display works correctly."""
    print("\nTesting feedback already formatted for display...")
    
    # Feedback that's already been cleaned (no headers)
    feedback = """1. COLLABORATION (7.5 pts): Met - Good partnership.

2. EVOCATION (7.5 pts): Met - Strong motivation exploration."""
    
    timestamp = "2025-01-06 14:30:00"
    evaluator = "test_user"
    
    # Test display format - should work with already-clean feedback
    display_output = FeedbackFormatter.format_feedback_for_display(feedback, timestamp, evaluator)
    
    # Should return the same content
    assert "1. COLLABORATION" in display_output, "Display should contain collaboration"
    assert "MI Performance Report" not in display_output, "Display should not add headers"
    
    print("  ✅ Already-formatted feedback handled correctly")
    return True


def main():
    """Run all edge case tests."""
    print("🧪 Testing Feedback Display Edge Cases\n")
    
    tests = [
        ("Feedback Without Collaboration Marker", test_feedback_without_collaboration_marker),
        ("Empty Feedback", test_empty_feedback),
        ("Already-Formatted Feedback", test_feedback_with_header_already_removed),
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
        print("🎉 All edge case tests passed!")
        return 0
    else:
        print(f"⚠️  {total - passed} tests failed.")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
