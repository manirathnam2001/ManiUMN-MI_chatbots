#!/usr/bin/env python3
"""
Test script to validate timestamp formatting and evaluator name fixes.

Tests:
1. Timestamp conversion includes AM/PM and timezone abbreviation
2. Feedback formatter uses bot name as evaluator
3. Integration test with both OHI and HPV bot names
"""

import sys
from time_utils import convert_to_minnesota_time
from feedback_template import FeedbackFormatter


def test_timestamp_format_with_am_pm():
    """Test that timestamp includes AM/PM and timezone abbreviation."""
    print("\n1. Testing Timestamp Format with AM/PM and Timezone...")
    
    # Test with the specified UTC time from problem statement
    utc_time = "2025-10-08 03:50:21"
    mn_time = convert_to_minnesota_time(utc_time)
    
    print(f"   UTC time: {utc_time}")
    print(f"   Minnesota time: {mn_time}")
    
    # In October 2025, Minnesota is in CDT (UTC-5)
    # 03:50:21 UTC should be 10:50:21 PM CDT (22:50:21 - 12 = 10:50:21 PM)
    expected = "2025-10-07 10:50:21 PM CDT"
    assert mn_time == expected, f"Expected '{expected}', got '{mn_time}'"
    
    # Verify format includes AM/PM
    assert " AM " in mn_time or " PM " in mn_time, "Timestamp should include AM/PM"
    
    # Verify format includes timezone abbreviation
    assert mn_time.endswith("CDT") or mn_time.endswith("CST"), "Timestamp should include timezone abbreviation"
    
    print("   ✅ Timestamp correctly formatted with AM/PM and timezone")
    return True


def test_feedback_format_with_bot_name():
    """Test that feedback formatter uses bot name as evaluator."""
    print("\n2. Testing Feedback Format with Bot Name...")
    
    feedback_content = "Test feedback content"
    timestamp = "2025-10-08 03:50:21"
    bot_name = "OHI Assessment Bot"
    
    # Test PDF format
    pdf_format = FeedbackFormatter.format_feedback_for_pdf(
        feedback_content, timestamp, bot_name
    )
    
    print(f"   PDF Format sample:\n{pdf_format[:200]}...")
    
    # Verify bot name is in the output
    assert bot_name in pdf_format, f"Bot name '{bot_name}' should be in PDF format"
    
    # Verify timestamp is formatted correctly
    assert "10:50:21 PM CDT" in pdf_format, "Timestamp should be formatted with AM/PM and timezone"
    
    # Verify header structure
    assert "MI Performance Report" in pdf_format, "Should include header"
    assert "Evaluation Timestamp (Minnesota):" in pdf_format, "Should include timestamp label"
    assert "Evaluator:" in pdf_format, "Should include evaluator label"
    
    print("   ✅ Feedback correctly formatted with bot name as evaluator")
    return True


def test_ohi_bot_name():
    """Test OHI Assessment Bot name in feedback."""
    print("\n3. Testing OHI Assessment Bot Name...")
    
    feedback = "Test feedback"
    timestamp = "2025-10-08 03:50:21"
    ohi_bot = "OHI Assessment Bot"
    
    formatted = FeedbackFormatter.format_feedback_for_pdf(feedback, timestamp, ohi_bot)
    
    assert ohi_bot in formatted, "OHI bot name should appear in formatted feedback"
    print(f"   ✅ OHI bot name '{ohi_bot}' correctly used")
    return True


def test_hpv_bot_name():
    """Test HPV Assessment Bot name in feedback."""
    print("\n4. Testing HPV Assessment Bot Name...")
    
    feedback = "Test feedback"
    timestamp = "2025-10-08 03:50:21"
    hpv_bot = "HPV Assessment Bot"
    
    formatted = FeedbackFormatter.format_feedback_for_pdf(feedback, timestamp, hpv_bot)
    
    assert hpv_bot in formatted, "HPV bot name should appear in formatted feedback"
    print(f"   ✅ HPV bot name '{hpv_bot}' correctly used")
    return True


def test_integration():
    """Integration test with realistic feedback data."""
    print("\n5. Integration Test...")
    
    # Simulate realistic feedback
    feedback = """
**1. COLLABORATION (7.5 pts): Met** - The student demonstrated excellent partnership building.

**2. EVOCATION (7.5 pts): Partially Met** - Good use of open-ended questions.

**3. ACCEPTANCE (7.5 pts): Met** - Respectful and reflective listening.

**4. COMPASSION (7.5 pts): Met** - Warm and non-judgmental approach.
"""
    
    timestamp = "2025-10-08 03:50:21"
    bot_name = "OHI Assessment Bot"
    
    formatted = FeedbackFormatter.format_feedback_for_pdf(feedback, timestamp, bot_name)
    
    # Verify all key elements are present
    assert "MI Performance Report" in formatted
    assert "2025-10-07 10:50:21 PM CDT" in formatted
    assert bot_name in formatted
    assert "COLLABORATION" in formatted
    assert "EVOCATION" in formatted
    
    print("   Sample output:")
    lines = formatted.split('\n')
    for line in lines[:6]:  # Print first 6 lines
        print(f"     {line}")
    
    print("   ✅ Integration test passed")
    return True


def main():
    """Run all tests."""
    print("=" * 70)
    print("TIMESTAMP AND EVALUATOR NAME FIXES - TEST SUITE")
    print("=" * 70)
    
    tests = [
        ("Timestamp Format with AM/PM", test_timestamp_format_with_am_pm),
        ("Feedback Format with Bot Name", test_feedback_format_with_bot_name),
        ("OHI Bot Name", test_ohi_bot_name),
        ("HPV Bot Name", test_hpv_bot_name),
        ("Integration Test", test_integration),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"   ❌ {test_name} failed")
        except Exception as e:
            print(f"   ❌ {test_name} failed with exception: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 70)
    print(f"TEST RESULTS: {passed}/{total} tests passed")
    print("=" * 70)
    
    if passed == total:
        print("✅ All tests passed!")
        return 0
    else:
        print(f"❌ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
