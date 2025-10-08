#!/usr/bin/env python3
"""
Test script to validate enhanced timezone conversion with AM/PM format.
"""

import re
from datetime import datetime
import pytz


def test_time_conversion_with_ampm():
    """Test that convert_to_minnesota_time includes AM/PM and timezone."""
    print("\nTesting enhanced time conversion with AM/PM format...")
    
    from time_utils import convert_to_minnesota_time
    
    # Test morning time (should show AM)
    utc_time_morning = "2025-01-15 14:30:00"  # 2:30 PM UTC = 8:30 AM CST
    mn_time_morning = convert_to_minnesota_time(utc_time_morning)
    print(f"  UTC time (morning): {utc_time_morning}")
    print(f"  MN time (morning):  {mn_time_morning}")
    
    # Verify format: YYYY-MM-DD HH:MM:SS AM/PM TZ
    pattern = r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} (AM|PM) (CST|CDT)$'
    assert re.match(pattern, mn_time_morning), f"Format incorrect: {mn_time_morning}"
    assert "08:30:00 AM" in mn_time_morning, f"Expected 08:30:00 AM, got {mn_time_morning}"
    assert "CST" in mn_time_morning, f"Expected CST timezone, got {mn_time_morning}"
    
    # Test evening time (should show PM)
    utc_time_evening = "2025-01-15 23:45:00"  # 11:45 PM UTC = 5:45 PM CST
    mn_time_evening = convert_to_minnesota_time(utc_time_evening)
    print(f"  UTC time (evening): {utc_time_evening}")
    print(f"  MN time (evening):  {mn_time_evening}")
    
    assert "05:45:00 PM" in mn_time_evening, f"Expected 05:45:00 PM, got {mn_time_evening}"
    assert "CST" in mn_time_evening, f"Expected CST timezone, got {mn_time_evening}"
    
    # Test summer time (should show CDT)
    utc_time_summer = "2025-07-15 18:00:00"  # 6 PM UTC = 1 PM CDT
    mn_time_summer = convert_to_minnesota_time(utc_time_summer)
    print(f"  UTC time (summer):  {utc_time_summer}")
    print(f"  MN time (summer):   {mn_time_summer}")
    
    assert "01:00:00 PM" in mn_time_summer, f"Expected 01:00:00 PM, got {mn_time_summer}"
    assert "CDT" in mn_time_summer, f"Expected CDT timezone, got {mn_time_summer}"
    
    print("  ✅ Enhanced time conversion works correctly with AM/PM and timezone")
    return True


def test_error_handling():
    """Test error handling for invalid time strings."""
    print("\nTesting error handling for invalid inputs...")
    
    from time_utils import convert_to_minnesota_time
    
    # Test with invalid format
    invalid_time = "invalid-time-string"
    result = convert_to_minnesota_time(invalid_time)
    print(f"  Invalid input: {invalid_time}")
    print(f"  Result: {result}")
    
    # Should return original string on error
    assert result == invalid_time, f"Expected original string on error, got {result}"
    
    # Test with empty string
    empty_time = ""
    result_empty = convert_to_minnesota_time(empty_time)
    print(f"  Empty input: '{empty_time}'")
    print(f"  Result: '{result_empty}'")
    
    assert result_empty == empty_time, f"Expected empty string on error, got {result_empty}"
    
    print("  ✅ Error handling works correctly")
    return True


def test_noon_and_midnight():
    """Test correct handling of noon and midnight."""
    print("\nTesting noon and midnight conversion...")
    
    from time_utils import convert_to_minnesota_time
    
    # Test noon UTC (should be 6 AM CST in January)
    utc_noon = "2025-01-15 12:00:00"
    mn_from_noon = convert_to_minnesota_time(utc_noon)
    print(f"  UTC noon: {utc_noon}")
    print(f"  MN time:  {mn_from_noon}")
    
    assert "06:00:00 AM" in mn_from_noon, f"Expected 06:00:00 AM, got {mn_from_noon}"
    
    # Test midnight UTC (should be 6 PM CST previous day in January)
    utc_midnight = "2025-01-15 00:00:00"
    mn_from_midnight = convert_to_minnesota_time(utc_midnight)
    print(f"  UTC midnight: {utc_midnight}")
    print(f"  MN time:      {mn_from_midnight}")
    
    assert "06:00:00 PM" in mn_from_midnight, f"Expected 06:00:00 PM, got {mn_from_midnight}"
    assert "2025-01-14" in mn_from_midnight, f"Expected date 2025-01-14, got {mn_from_midnight}"
    
    print("  ✅ Noon and midnight conversion works correctly")
    return True


def main():
    """Run all enhanced time conversion tests."""
    print("🧪 Running Enhanced Time Conversion Tests\n")
    print("="*60)
    
    tests = [
        ("Time Conversion with AM/PM", test_time_conversion_with_ampm),
        ("Error Handling", test_error_handling),
        ("Noon and Midnight", test_noon_and_midnight),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*60}")
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All enhanced time conversion tests passed!")
        return 0
    else:
        print(f"⚠️  {total - passed} tests failed.")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
