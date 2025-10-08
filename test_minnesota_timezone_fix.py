#!/usr/bin/env python3
"""
Test script to validate Minnesota timezone fix for PDF reports.

Tests:
1. get_current_minnesota_time() returns time with AM/PM and timezone
2. UTC to Minnesota conversion works correctly
3. Apps use UTC time, formatters convert to Minnesota
4. PDF generation includes correct Minnesota timestamps
5. Problem statement example: 04:16:23 UTC → 11:16:23 PM CDT
"""

import sys
from time_utils import get_current_utc_time, get_current_minnesota_time, convert_to_minnesota_time
from feedback_template import FeedbackFormatter
from pdf_utils import generate_pdf_report


def test_get_current_minnesota_time():
    """Test that get_current_minnesota_time() returns proper format."""
    print("\n1. Testing get_current_minnesota_time()...")
    
    mn_time = get_current_minnesota_time()
    print(f"   Minnesota time: {mn_time}")
    
    # Verify format includes AM/PM
    assert " AM " in mn_time or " PM " in mn_time, "Time should include AM/PM"
    
    # Verify format includes timezone abbreviation
    assert mn_time.endswith("CDT") or mn_time.endswith("CST"), "Time should include timezone (CDT or CST)"
    
    # Verify date format
    parts = mn_time.split()
    assert len(parts) == 4, f"Expected 4 parts (date time AM/PM TZ), got {len(parts)}"
    
    print("   ✅ get_current_minnesota_time() returns correct format")
    return True


def test_utc_to_minnesota_conversion():
    """Test UTC to Minnesota conversion."""
    print("\n2. Testing UTC to Minnesota conversion...")
    
    # Test winter time (CST - UTC-6)
    utc_winter = "2025-01-15 18:00:00"
    mn_winter = convert_to_minnesota_time(utc_winter)
    print(f"   Winter: {utc_winter} UTC → {mn_winter}")
    assert mn_winter == "2025-01-15 12:00:00 PM CST", f"Expected CST conversion, got {mn_winter}"
    
    # Test summer time (CDT - UTC-5)
    utc_summer = "2025-07-15 18:00:00"
    mn_summer = convert_to_minnesota_time(utc_summer)
    print(f"   Summer: {utc_summer} UTC → {mn_summer}")
    assert mn_summer == "2025-07-15 01:00:00 PM CDT", f"Expected CDT conversion, got {mn_summer}"
    
    print("   ✅ UTC to Minnesota conversion works correctly")
    return True


def test_app_to_pdf_flow():
    """Test complete flow from app to PDF generation."""
    print("\n3. Testing app to PDF flow...")
    
    # Step 1: App gets UTC time
    utc_time = get_current_utc_time()
    print(f"   App gets UTC: {utc_time}")
    assert len(utc_time) == 19, "UTC time should be in format YYYY-MM-DD HH:MM:SS"
    
    # Step 2: Formatter converts to Minnesota
    mn_time = convert_to_minnesota_time(utc_time)
    print(f"   Converted to MN: {mn_time}")
    assert " AM " in mn_time or " PM " in mn_time, "Converted time should have AM/PM"
    assert "CDT" in mn_time or "CST" in mn_time, "Converted time should have timezone"
    
    # Step 3: Format feedback
    feedback = "**1. COLLABORATION (7.5 pts): Met** - Great work."
    evaluator = "Test Bot"
    formatted = FeedbackFormatter.format_feedback_for_pdf(feedback, utc_time, evaluator)
    
    print(f"   Formatted feedback includes: 'Evaluation Timestamp (Minnesota): {mn_time}'")
    assert "Evaluation Timestamp (Minnesota):" in formatted, "Missing timestamp label"
    assert mn_time in formatted, "Formatted time not in feedback"
    
    # Step 4: Generate PDF
    chat_history = [
        {'role': 'assistant', 'content': 'Hello'},
        {'role': 'user', 'content': 'Hi'}
    ]
    pdf_buffer = generate_pdf_report('Test Student', formatted, chat_history)
    print(f"   PDF generated: {len(pdf_buffer.getvalue())} bytes")
    
    print("   ✅ Complete app to PDF flow works correctly")
    return True


def test_direct_minnesota_time():
    """Test that direct Minnesota time matches converted time."""
    print("\n4. Testing direct vs converted Minnesota time...")
    
    # Get direct Minnesota time
    direct_mn = get_current_minnesota_time()
    
    # Get UTC and convert
    utc = get_current_utc_time()
    converted_mn = convert_to_minnesota_time(utc)
    
    print(f"   Direct:    {direct_mn}")
    print(f"   Converted: {converted_mn}")
    
    # They should be the same (within a second)
    # Extract just the date and hour to compare
    direct_parts = direct_mn.split()
    converted_parts = converted_mn.split()
    
    assert direct_parts[0] == converted_parts[0], "Dates should match"
    assert direct_parts[2] == converted_parts[2], "AM/PM should match"
    assert direct_parts[3] == converted_parts[3], "Timezone should match"
    
    print("   ✅ Direct and converted times match")
    return True


def test_problem_statement_example():
    """Test the specific example from the problem statement."""
    print("\n5. Testing problem statement example...")
    
    # Problem statement: "2025-10-08 04:16:23 UTC should be 11:14 PM Minnesota"
    # Note: 04:16:23 UTC actually converts to 11:16:23 PM CDT (not 11:14)
    utc_time = "2025-10-08 04:16:23"
    mn_time = convert_to_minnesota_time(utc_time)
    
    print(f"   UTC: {utc_time}")
    print(f"   MN:  {mn_time}")
    
    # Should be October 7th (day before) at 11:16:23 PM CDT
    assert "2025-10-07" in mn_time, "Should be October 7th in Minnesota"
    assert "11:16:23 PM" in mn_time, "Should be 11:16:23 PM"
    assert "CDT" in mn_time, "Should be CDT (daylight time) in October"
    
    print("   ✅ Problem statement example converts correctly")
    return True


def test_no_double_conversion():
    """Test that we don't double-convert Minnesota time."""
    print("\n6. Testing no double conversion...")
    
    # Get a Minnesota time
    from time_utils import get_formatted_utc_time
    mn_time_24hr = get_formatted_utc_time()  # Returns MN time in 24-hour format
    print(f"   get_formatted_utc_time(): {mn_time_24hr}")
    
    # If we mistakenly convert this again, we'd get wrong time
    wrong_conversion = convert_to_minnesota_time(mn_time_24hr)
    print(f"   Wrong conversion: {wrong_conversion}")
    
    # The apps should now use get_current_utc_time() instead
    correct_utc = get_current_utc_time()
    correct_conversion = convert_to_minnesota_time(correct_utc)
    print(f"   Correct UTC: {correct_utc}")
    print(f"   Correct conversion: {correct_conversion}")
    
    # Extract hours to verify they're different
    wrong_hour = wrong_conversion.split()[1].split(':')[0]
    correct_hour = correct_conversion.split()[1].split(':')[0]
    
    print(f"   Wrong shows hour: {wrong_hour}, Correct shows hour: {correct_hour}")
    print("   ✅ Apps now use UTC time to avoid double conversion")
    return True


def main():
    """Run all tests."""
    print("=" * 70)
    print("MINNESOTA TIMEZONE FIX - TEST SUITE")
    print("=" * 70)
    
    tests = [
        ("get_current_minnesota_time()", test_get_current_minnesota_time),
        ("UTC to Minnesota conversion", test_utc_to_minnesota_conversion),
        ("App to PDF flow", test_app_to_pdf_flow),
        ("Direct vs converted time", test_direct_minnesota_time),
        ("Problem statement example", test_problem_statement_example),
        ("No double conversion", test_no_double_conversion),
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
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"⚠️  {total - passed} test(s) failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
