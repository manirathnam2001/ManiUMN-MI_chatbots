#!/usr/bin/env python3
"""
Test script to validate the timestamp parsing fix for the issue:
"ValueError: unconverted data remains: PM CST" when finishing feedback flow.

This test validates that convert_to_minnesota_time() can handle:
1. 24-hour UTC format: YYYY-MM-DD HH:MM:SS
2. 12-hour with AM/PM: YYYY-MM-DD hh:MM:SS AM/PM
3. 12-hour with AM/PM and TZ: YYYY-MM-DD hh:MM:SS AM/PM TZ
4. ISO format: YYYY-MM-DDTHH:MM:SSZ
5. Already formatted Minnesota time (pass-through)
"""

from time_utils import convert_to_minnesota_time


def test_original_error_case():
    """Test the exact error case from the problem statement."""
    print("\n" + "="*70)
    print("TEST 1: Original Error Case - '2025-12-24 12:50:24 PM CST'")
    print("="*70)
    
    test_input = "2025-12-24 12:50:24 PM CST"
    print(f"Input:  {test_input}")
    
    try:
        result = convert_to_minnesota_time(test_input)
        print(f"Output: {result}")
        assert result == test_input, f"Expected pass-through, got: {result}"
        print("✅ SUCCESS - Already formatted timestamp passed through correctly")
        return True
    except ValueError as e:
        print(f"❌ FAILED - ValueError: {e}")
        return False


def test_24hour_utc_format():
    """Test standard 24-hour UTC format."""
    print("\n" + "="*70)
    print("TEST 2: 24-hour UTC format - 'YYYY-MM-DD HH:MM:SS'")
    print("="*70)
    
    test_cases = [
        ("2025-12-24 18:50:24", "2025-12-24 12:50:24 PM CST"),  # Winter CST
        ("2025-07-15 18:00:00", "2025-07-15 01:00:00 PM CDT"),  # Summer CDT
        ("2025-10-08 04:17:24", "2025-10-07 11:17:24 PM CDT"),  # From problem statement test
    ]
    
    all_passed = True
    for input_ts, expected_ts in test_cases:
        print(f"\nInput:    {input_ts}")
        print(f"Expected: {expected_ts}")
        
        try:
            result = convert_to_minnesota_time(input_ts)
            print(f"Output:   {result}")
            
            if result == expected_ts:
                print("✅ PASS")
            else:
                print(f"❌ FAIL - Expected '{expected_ts}', got '{result}'")
                all_passed = False
        except Exception as e:
            print(f"❌ FAIL - Exception: {e}")
            all_passed = False
    
    return all_passed


def test_12hour_am_pm_format():
    """Test 12-hour format with AM/PM but no timezone."""
    print("\n" + "="*70)
    print("TEST 3: 12-hour with AM/PM - 'YYYY-MM-DD hh:MM:SS AM/PM'")
    print("="*70)
    
    test_cases = [
        ("2025-12-24 12:50:24 PM", "2025-12-24 06:50:24 AM CST"),  # Noon -> Morning CST
        ("2025-12-24 06:50:24 AM", "2025-12-24 12:50:24 AM CST"),  # Morning -> Midnight CST
    ]
    
    all_passed = True
    for input_ts, expected_ts in test_cases:
        print(f"\nInput:    {input_ts}")
        print(f"Expected: {expected_ts}")
        
        try:
            result = convert_to_minnesota_time(input_ts)
            print(f"Output:   {result}")
            
            if result == expected_ts:
                print("✅ PASS")
            else:
                print(f"❌ FAIL - Expected '{expected_ts}', got '{result}'")
                all_passed = False
        except Exception as e:
            print(f"❌ FAIL - Exception: {e}")
            all_passed = False
    
    return all_passed


def test_12hour_am_pm_with_timezone():
    """Test 12-hour format with AM/PM and timezone suffix."""
    print("\n" + "="*70)
    print("TEST 4: 12-hour with AM/PM and TZ - 'YYYY-MM-DD hh:MM:SS AM/PM TZ'")
    print("="*70)
    
    test_cases = [
        ("2025-12-24 12:50:24 PM CST", "2025-12-24 12:50:24 PM CST"),  # Winter
        ("2025-07-15 01:00:00 PM CDT", "2025-07-15 01:00:00 PM CDT"),  # Summer
        ("2025-12-24 12:50:24 AM CST", "2025-12-24 12:50:24 AM CST"),  # Midnight
    ]
    
    all_passed = True
    for input_ts, expected_ts in test_cases:
        print(f"\nInput:    {input_ts}")
        print(f"Expected: {expected_ts}")
        
        try:
            result = convert_to_minnesota_time(input_ts)
            print(f"Output:   {result}")
            
            if result == expected_ts:
                print("✅ PASS (Pass-through)")
            else:
                print(f"❌ FAIL - Expected '{expected_ts}', got '{result}'")
                all_passed = False
        except Exception as e:
            print(f"❌ FAIL - Exception: {e}")
            all_passed = False
    
    return all_passed


def test_iso_format():
    """Test ISO format timestamps."""
    print("\n" + "="*70)
    print("TEST 5: ISO format - 'YYYY-MM-DDTHH:MM:SSZ'")
    print("="*70)
    
    test_cases = [
        ("2025-12-24T18:50:24Z", "2025-12-24 12:50:24 PM CST"),
        ("2025-07-15T18:00:00Z", "2025-07-15 01:00:00 PM CDT"),
    ]
    
    all_passed = True
    for input_ts, expected_ts in test_cases:
        print(f"\nInput:    {input_ts}")
        print(f"Expected: {expected_ts}")
        
        try:
            result = convert_to_minnesota_time(input_ts)
            print(f"Output:   {result}")
            
            if result == expected_ts:
                print("✅ PASS")
            else:
                print(f"❌ FAIL - Expected '{expected_ts}', got '{result}'")
                all_passed = False
        except Exception as e:
            print(f"❌ FAIL - Exception: {e}")
            all_passed = False
    
    return all_passed


def test_feedback_template_integration():
    """Test integration with feedback_template.py"""
    print("\n" + "="*70)
    print("TEST 6: Integration with feedback_template.py")
    print("="*70)
    
    from feedback_template import FeedbackFormatter
    
    # Test with the problematic timestamp format
    timestamp = "2025-12-24 12:50:24 PM CST"
    feedback = "Test feedback content"
    evaluator = "Test Evaluator"
    
    print(f"Timestamp: {timestamp}")
    
    try:
        result = FeedbackFormatter.format_feedback_for_pdf(feedback, timestamp, evaluator)
        print("\nFormatted PDF output:")
        print("-" * 70)
        print(result)
        print("-" * 70)
        
        # Verify the timestamp appears in the output
        assert "2025-12-24 12:50:24 PM CST" in result
        print("\n✅ SUCCESS - No ValueError raised in feedback template")
        return True
    except ValueError as e:
        print(f"\n❌ FAILED - ValueError in feedback template: {e}")
        return False
    except Exception as e:
        print(f"\n❌ FAILED - Unexpected error: {e}")
        return False


def main():
    """Run all timestamp parsing tests."""
    print("\n" + "="*70)
    print("TIMESTAMP PARSING FIX VALIDATION TEST SUITE")
    print("Testing fix for: 'ValueError: unconverted data remains: PM CST'")
    print("="*70)
    
    tests = [
        ("Original Error Case", test_original_error_case),
        ("24-hour UTC format", test_24hour_utc_format),
        ("12-hour with AM/PM", test_12hour_am_pm_format),
        ("12-hour with AM/PM and TZ", test_12hour_am_pm_with_timezone),
        ("ISO format", test_iso_format),
        ("Feedback Template Integration", test_feedback_template_integration),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"\n❌ {test_name} FAILED")
        except Exception as e:
            print(f"\n❌ {test_name} FAILED with exception:")
            print(f"   {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*70)
    print(f"TEST RESULTS: {passed}/{total} tests passed")
    print("="*70)
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("\nVERIFICATION SUMMARY:")
        print("✅ Original error case fixed - no more 'ValueError: unconverted data remains: PM CST'")
        print("✅ Supports 24-hour UTC format: YYYY-MM-DD HH:MM:SS")
        print("✅ Supports 12-hour with AM/PM: YYYY-MM-DD hh:MM:SS AM/PM")
        print("✅ Supports 12-hour with AM/PM and TZ: YYYY-MM-DD hh:MM:SS AM/PM TZ")
        print("✅ Supports ISO format: YYYY-MM-DDTHH:MM:SSZ")
        print("✅ Already formatted Minnesota time passed through correctly")
        print("✅ Integration with feedback_template.py works correctly")
        print("\nThe fix meets all requirements from the problem statement.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed.")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
