#!/usr/bin/env python3
"""
Test script to validate the timezone conversion fix for the specific timestamp
from the problem statement.

Problem Statement Test Case:
- UTC time: 2025-10-08 04:15:16
- Expected MN time: 2025-10-07 11:15:16 PM CDT (corrected from problem statement)
"""

import sys
from time_utils import get_current_utc_time, convert_to_minnesota_time
from feedback_template import FeedbackFormatter


def test_problem_statement_timestamp():
    """Test the specific timestamp from the problem statement."""
    print("\n" + "=" * 70)
    print("PROBLEM STATEMENT TIMESTAMP TEST")
    print("=" * 70)
    
    # Test with exact timestamp from problem statement
    utc_time = "2025-10-08 04:15:16"
    mn_time = convert_to_minnesota_time(utc_time)
    
    print(f"\nInput UTC time:     {utc_time}")
    print(f"Converted MN time:  {mn_time}")
    
    # The correct conversion (CDT is UTC-5)
    # 2025-10-08 04:15:16 UTC - 5 hours = 2025-10-07 23:15:16 (Oct 7, 11:15:16 PM)
    expected = "2025-10-07 11:15:16 PM CDT"
    print(f"Expected MN time:   {expected}")
    
    if mn_time == expected:
        print("\n✅ PASS: Timestamp conversion is correct!")
        return True
    else:
        print(f"\n❌ FAIL: Expected '{expected}', got '{mn_time}'")
        return False


def test_current_utc_to_mn_conversion():
    """Test the full flow: get UTC time and convert to MN time."""
    print("\n" + "=" * 70)
    print("FULL CONVERSION FLOW TEST")
    print("=" * 70)
    
    # Get actual UTC time
    utc_time = get_current_utc_time()
    print(f"\nStep 1: Get UTC time")
    print(f"        UTC: {utc_time}")
    
    # Convert to Minnesota time
    mn_time = convert_to_minnesota_time(utc_time)
    print(f"\nStep 2: Convert to Minnesota time")
    print(f"        MN:  {mn_time}")
    
    # Verify format
    has_am_pm = " AM " in mn_time or " PM " in mn_time
    has_timezone = mn_time.endswith("CDT") or mn_time.endswith("CST")
    
    print(f"\nFormat checks:")
    print(f"  - Contains AM/PM: {has_am_pm} {'✅' if has_am_pm else '❌'}")
    print(f"  - Contains timezone: {has_timezone} {'✅' if has_timezone else '❌'}")
    
    if has_am_pm and has_timezone:
        print("\n✅ PASS: Format is correct!")
        return True
    else:
        print("\n❌ FAIL: Format is incorrect")
        return False


def test_feedback_formatter_integration():
    """Test the feedback formatter with the problem statement timestamp."""
    print("\n" + "=" * 70)
    print("FEEDBACK FORMATTER INTEGRATION TEST")
    print("=" * 70)
    
    # Use the problem statement timestamp
    utc_time = "2025-10-08 04:15:16"
    feedback = "**1. COLLABORATION (7.5 pts): Met** - Good rapport building."
    bot_name = "OHI Assessment Bot"
    
    # Format for PDF
    formatted = FeedbackFormatter.format_feedback_for_pdf(
        feedback, utc_time, bot_name
    )
    
    print("\nFormatted output:")
    print("-" * 70)
    lines = formatted.split('\n')
    for line in lines[:5]:
        print(line)
    print("-" * 70)
    
    # Verify key elements
    checks = {
        "MI Performance Report": "MI Performance Report" in formatted,
        "Minnesota timestamp": "2025-10-07 11:15:16 PM CDT" in formatted,
        "Bot name": bot_name in formatted,
        "Feedback content": "COLLABORATION" in formatted,
    }
    
    print("\nVerification checks:")
    all_pass = True
    for check_name, result in checks.items():
        status = "✅" if result else "❌"
        print(f"  {status} {check_name}")
        if not result:
            all_pass = False
    
    if all_pass:
        print("\n✅ PASS: All checks passed!")
        return True
    else:
        print("\n❌ FAIL: Some checks failed")
        return False


def test_error_handling():
    """Test error handling in convert_to_minnesota_time."""
    print("\n" + "=" * 70)
    print("ERROR HANDLING TEST")
    print("=" * 70)
    
    tests = [
        ("Invalid format", "invalid format", ValueError),
        ("Wrong type", 12345, TypeError),
        ("Empty string", "", ValueError),
    ]
    
    passed = 0
    for test_name, input_value, expected_exception in tests:
        try:
            result = convert_to_minnesota_time(input_value)
            print(f"\n❌ {test_name}: Expected {expected_exception.__name__} but got result: {result}")
        except expected_exception as e:
            print(f"\n✅ {test_name}: Correctly raised {expected_exception.__name__}")
            print(f"   Message: {str(e)[:60]}...")
            passed += 1
        except Exception as e:
            print(f"\n❌ {test_name}: Expected {expected_exception.__name__} but got {type(e).__name__}")
    
    if passed == len(tests):
        print(f"\n✅ PASS: All {passed}/{len(tests)} error handling tests passed!")
        return True
    else:
        print(f"\n❌ FAIL: Only {passed}/{len(tests)} error handling tests passed")
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("MINNESOTA TIMEZONE CONVERSION FIX - VALIDATION SUITE")
    print("=" * 70)
    
    tests = [
        ("Problem Statement Timestamp", test_problem_statement_timestamp),
        ("Current UTC to MN Conversion", test_current_utc_to_mn_conversion),
        ("Feedback Formatter Integration", test_feedback_formatter_integration),
        ("Error Handling", test_error_handling),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            results.append((test_name, test_func()))
        except Exception as e:
            print(f"\n❌ {test_name} failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print("\n" + "=" * 70)
    print(f"FINAL RESULT: {passed}/{total} tests passed")
    print("=" * 70)
    
    if passed == total:
        print("\n🎉 All tests passed! The timezone conversion fix is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
