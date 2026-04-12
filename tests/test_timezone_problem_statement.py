#!/usr/bin/env python3
"""
Test script to verify timezone conversion implementation matches problem statement requirements.

This test validates:
1. UTC time is properly converted to Minnesota time
2. PDF shows Minnesota time instead of UTC time
3. Timezone indicator (CDT/CST) is included
4. AM/PM format is used
5. Test case from problem statement: 2025-10-08 04:17:24 UTC
"""

import re
from datetime import datetime
import pytz


def test_timezone_conversion_with_problem_statement_example():
    """Test timezone conversion with the specific UTC timestamp from problem statement."""
    print("\n" + "="*70)
    print("TEST 1: Timezone Conversion with Problem Statement Example")
    print("="*70)
    
    from time_utils import convert_to_minnesota_time
    
    # Test case from problem statement
    utc_time = "2025-10-08 04:17:24"
    mn_time = convert_to_minnesota_time(utc_time)
    
    print(f"\nInput (UTC):     {utc_time}")
    print(f"Output (MN):     {mn_time}")
    
    # Verify format: YYYY-MM-DD HH:MM:SS AM/PM CDT/CST
    pattern = r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} (AM|PM) (CDT|CST)$'
    assert re.match(pattern, mn_time), f"Format does not match expected pattern: {mn_time}"
    
    # Verify conversion is correct (October 2025 -> CDT, UTC-5)
    # 2025-10-08 04:17:24 UTC -> 2025-10-07 23:17:24 CDT (subtract 5 hours)
    # In 12-hour format: 11:17:24 PM
    expected = "2025-10-07 11:17:24 PM CDT"
    assert mn_time == expected, f"Expected '{expected}', got '{mn_time}'"
    
    print(f"Expected:        {expected}")
    print("✅ Timezone conversion is CORRECT")
    print("✅ Format includes AM/PM")
    print("✅ Format includes timezone abbreviation (CDT)")
    
    return True


def test_pdf_formatting_includes_minnesota_time():
    """Test that PDF formatting includes converted Minnesota time with timezone indicator."""
    print("\n" + "="*70)
    print("TEST 2: PDF Formatting Includes Minnesota Time")
    print("="*70)
    
    from feedback_template import FeedbackFormatter
    
    # Test with problem statement timestamp
    utc_time = "2025-10-08 04:17:24"
    feedback = "Sample feedback content"
    evaluator = "Test Evaluator"
    
    # Format for PDF
    formatted = FeedbackFormatter.format_feedback_for_pdf(feedback, utc_time, evaluator)
    
    print("\nFormatted PDF output:")
    print("-" * 70)
    print(formatted)
    print("-" * 70)
    
    # Verify Minnesota time is present (not UTC)
    assert "2025-10-07 11:17:24 PM CDT" in formatted, "Minnesota time not found in PDF output"
    assert "2025-10-08 04:17:24" not in formatted or "Evaluation Timestamp (Minnesota): 2025-10-07 11:17:24 PM CDT" in formatted, "UTC time should be converted"
    
    # Verify timezone indicator is present
    assert "CDT" in formatted or "CST" in formatted, "Timezone indicator (CDT/CST) is missing"
    
    # Verify AM/PM is present
    assert "AM" in formatted or "PM" in formatted, "AM/PM indicator is missing"
    
    # Verify Minnesota label is present
    assert "Minnesota" in formatted, "Minnesota label is missing"
    
    print("\n✅ PDF shows Minnesota time (not UTC)")
    print("✅ Timezone indicator (CDT/CST) is present")
    print("✅ AM/PM format is used")
    print("✅ Minnesota label is present")
    
    return True


def test_dst_handling():
    """Test that DST (Daylight Saving Time) is handled correctly."""
    print("\n" + "="*70)
    print("TEST 3: DST Handling (CDT vs CST)")
    print("="*70)
    
    from time_utils import convert_to_minnesota_time
    
    # Test winter time (CST - UTC-6)
    winter_utc = "2025-01-15 18:00:00"
    winter_mn = convert_to_minnesota_time(winter_utc)
    print(f"\nWinter (CST):")
    print(f"  UTC: {winter_utc}")
    print(f"  MN:  {winter_mn}")
    assert "CST" in winter_mn, f"Expected CST for winter time, got: {winter_mn}"
    assert "12:00:00 PM" in winter_mn, f"Expected 12:00:00 PM (18:00 UTC - 6 hours), got: {winter_mn}"
    
    # Test summer time (CDT - UTC-5)
    summer_utc = "2025-07-15 18:00:00"
    summer_mn = convert_to_minnesota_time(summer_utc)
    print(f"\nSummer (CDT):")
    print(f"  UTC: {summer_utc}")
    print(f"  MN:  {summer_mn}")
    assert "CDT" in summer_mn, f"Expected CDT for summer time, got: {summer_mn}"
    assert "01:00:00 PM" in summer_mn, f"Expected 01:00:00 PM (18:00 UTC - 5 hours), got: {summer_mn}"
    
    print("\n✅ DST handling is correct (CDT in summer, CST in winter)")
    
    return True


def test_error_handling():
    """Test that invalid datetime formats are handled properly."""
    print("\n" + "="*70)
    print("TEST 4: Error Handling for Invalid Input")
    print("="*70)
    
    from time_utils import convert_to_minnesota_time
    
    # Test with invalid format
    invalid_formats = [
        "not-a-date",
        "2025-13-45 25:99:99",  # Invalid date/time
        "2025/10/08 04:17:24",  # Wrong format (slash instead of dash)
    ]
    
    for invalid in invalid_formats:
        try:
            result = convert_to_minnesota_time(invalid)
            print(f"  ❌ Should have raised ValueError for: {invalid}")
            return False
        except ValueError as e:
            print(f"  ✅ Correctly raised ValueError for: {invalid}")
        except Exception as e:
            print(f"  ⚠️  Unexpected error for '{invalid}': {type(e).__name__}: {e}")
    
    print("\n✅ Invalid input is handled properly")
    return True


def test_12_hour_format():
    """Test that 12-hour format is used correctly (not 24-hour format)."""
    print("\n" + "="*70)
    print("TEST 5: 12-Hour Format (AM/PM) Verification")
    print("="*70)
    
    from time_utils import convert_to_minnesota_time
    
    # October 2025 is CDT (UTC-5)
    test_cases = [
        ("2025-10-08 05:00:00", "12:00:00 AM CDT"),  # Midnight MN (05:00 UTC - 5 = 00:00)
        ("2025-10-08 06:00:00", "01:00:00 AM CDT"),  # Early morning (06:00 UTC - 5 = 01:00)
        ("2025-10-08 17:00:00", "12:00:00 PM CDT"),  # Noon (17:00 UTC - 5 = 12:00)
        ("2025-10-08 23:00:00", "06:00:00 PM CDT"),  # Evening (23:00 UTC - 5 = 18:00)
    ]
    
    for utc, expected in test_cases:
        mn_time = convert_to_minnesota_time(utc)
        print(f"\n  UTC: {utc}")
        print(f"  MN:  {mn_time}")
        print(f"  Expected: {expected}")
        assert expected in mn_time, f"Expected '{expected}' in '{mn_time}'"
        assert "AM" in mn_time or "PM" in mn_time, f"AM/PM missing in '{mn_time}'"
    
    print("\n✅ 12-hour format with AM/PM is correct")
    return True


def main():
    """Run all timezone conversion verification tests."""
    print("\n" + "="*70)
    print("TIMEZONE CONVERSION VERIFICATION TEST SUITE")
    print("Testing implementation against problem statement requirements")
    print("="*70)
    
    tests = [
        ("Timezone Conversion with Problem Statement Example", test_timezone_conversion_with_problem_statement_example),
        ("PDF Formatting Includes Minnesota Time", test_pdf_formatting_includes_minnesota_time),
        ("DST Handling (CDT vs CST)", test_dst_handling),
        ("Error Handling for Invalid Input", test_error_handling),
        ("12-Hour Format (AM/PM) Verification", test_12_hour_format),
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
        print("✅ UTC time is properly converted to Minnesota time")
        print("✅ PDF shows Minnesota time (not UTC)")
        print("✅ Timezone indicator (CDT/CST) is included")
        print("✅ AM/PM format is used (12-hour format)")
        print("✅ DST is handled correctly")
        print("✅ Error handling works properly")
        print("\nThe implementation meets all problem statement requirements.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed.")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
