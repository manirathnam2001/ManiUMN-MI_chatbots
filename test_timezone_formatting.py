#!/usr/bin/env python3
"""
Test script to validate timezone conversion and formatting consistency.
"""

import re
from datetime import datetime
import pytz


def test_timestamp_format():
    """Test that timestamps are in YYYY-MM-DD HH:MM:SS format."""
    print("Testing timestamp format...")
    
    from time_utils import get_formatted_utc_time
    
    timestamp = get_formatted_utc_time()
    print(f"  Generated timestamp: {timestamp}")
    
    # Verify format matches YYYY-MM-DD HH:MM:SS
    pattern = r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$'
    assert re.match(pattern, timestamp), f"Timestamp format incorrect: {timestamp}"
    
    # Verify it's parseable as datetime
    try:
        dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
        print(f"  ✅ Timestamp format is correct: {timestamp}")
        return True
    except ValueError as e:
        print(f"  ❌ Timestamp format error: {e}")
        return False


def test_minnesota_timezone():
    """Test that timestamps are in Minnesota timezone (America/Chicago)."""
    print("\nTesting Minnesota timezone conversion...")
    
    from time_utils import get_formatted_utc_time, convert_to_minnesota_time
    
    # Test with a known UTC time
    utc_time = "2025-01-15 18:00:00"  # 6 PM UTC in January (CST)
    mn_time = convert_to_minnesota_time(utc_time)
    print(f"  UTC time: {utc_time}")
    print(f"  MN time:  {mn_time}")
    
    # In January, Minnesota is CST (UTC-6)
    # So 18:00 UTC should be 12:00 CST
    assert mn_time == "2025-01-15 12:00:00", f"Expected 12:00:00, got {mn_time}"
    
    # Test with a summer time (CDT - UTC-5)
    utc_time_summer = "2025-07-15 18:00:00"  # 6 PM UTC in July (CDT)
    mn_time_summer = convert_to_minnesota_time(utc_time_summer)
    print(f"  UTC time (summer): {utc_time_summer}")
    print(f"  MN time (summer):  {mn_time_summer}")
    
    # In July, Minnesota is CDT (UTC-5)
    # So 18:00 UTC should be 13:00 CDT
    assert mn_time_summer == "2025-07-15 13:00:00", f"Expected 13:00:00, got {mn_time_summer}"
    
    print("  ✅ Minnesota timezone conversion is correct (handles DST)")
    return True


def test_feedback_formatting_consistency():
    """Test that display and PDF formatting are consistent."""
    print("\nTesting feedback formatting consistency...")
    
    from feedback_template import FeedbackFormatter
    
    feedback = "**1. COLLABORATION (7.5 pts): Met** - Great job building rapport."
    timestamp = "2025-10-06 14:30:00"
    evaluator = "test_evaluator"
    
    # Test display format
    display_format = FeedbackFormatter.format_feedback_for_display(feedback, timestamp, evaluator)
    print("  Display format:")
    for key, value in display_format.items():
        print(f"    {key}: {value}")
    
    # Test PDF format
    pdf_format = FeedbackFormatter.format_feedback_for_pdf(feedback, timestamp, evaluator)
    print("\n  PDF format:")
    print("    " + pdf_format.replace("\n", "\n    "))
    
    # Verify both formats contain the same information
    # Check that timestamp labels match (without UTC)
    assert "Evaluation Timestamp:" in display_format['timestamp'], "Display format missing timestamp label"
    assert "Evaluation Timestamp:" in pdf_format, "PDF format missing timestamp label"
    assert "(UTC)" not in display_format['timestamp'], "Display format should not contain '(UTC)'"
    assert "(UTC)" not in pdf_format, "PDF format should not contain '(UTC)'"
    
    # Check that both formats have the same timestamp value
    assert timestamp in display_format['timestamp'], "Display format timestamp mismatch"
    assert timestamp in pdf_format, "PDF format timestamp mismatch"
    
    # Check that evaluator is present in both
    assert evaluator in display_format['evaluator'], "Display format evaluator mismatch"
    assert evaluator in pdf_format, "PDF format evaluator mismatch"
    
    # Check that feedback content is present in both
    assert display_format['content'] == feedback, "Display format feedback mismatch"
    assert feedback in pdf_format, "PDF format feedback mismatch"
    
    print("\n  ✅ Feedback formatting is consistent between display and PDF")
    return True


def test_pdf_timestamp_extraction():
    """Test that PDF generation can extract the new timestamp format."""
    print("\nTesting PDF timestamp extraction...")
    
    from feedback_template import FeedbackFormatter
    import re
    
    timestamp = "2025-10-06 14:30:00"
    feedback = "Test feedback"
    evaluator = "test_user"
    
    # Generate formatted feedback as it would be passed to PDF generation
    formatted_feedback = FeedbackFormatter.format_feedback_for_pdf(feedback, timestamp, evaluator)
    
    # Test the timestamp extraction pattern used in pdf_utils.py
    timestamp_pattern = r'Evaluation Timestamp: ([^\n]+)'
    timestamp_match = re.search(timestamp_pattern, formatted_feedback)
    
    assert timestamp_match is not None, "Timestamp pattern not found in formatted feedback"
    extracted_timestamp = timestamp_match.group(1)
    
    print(f"  Formatted feedback:\n    {formatted_feedback.replace(chr(10), chr(10) + '    ')}")
    print(f"  Extracted timestamp: {extracted_timestamp}")
    
    assert extracted_timestamp == timestamp, f"Extracted timestamp mismatch: {extracted_timestamp} != {timestamp}"
    
    print("  ✅ PDF timestamp extraction works correctly")
    return True


def test_no_utc_label_in_output():
    """Verify that UTC labels are removed from all outputs."""
    print("\nTesting that UTC labels are removed...")
    
    from feedback_template import FeedbackFormatter
    
    feedback = "Test feedback"
    timestamp = "2025-10-06 14:30:00"
    evaluator = "test_user"
    
    # Check display format
    display_format = FeedbackFormatter.format_feedback_for_display(feedback, timestamp, evaluator)
    display_text = str(display_format)
    assert "(UTC)" not in display_text, "Display format should not contain '(UTC)' label"
    
    # Check PDF format
    pdf_format = FeedbackFormatter.format_feedback_for_pdf(feedback, timestamp, evaluator)
    assert "(UTC)" not in pdf_format, "PDF format should not contain '(UTC)' label"
    
    print("  ✅ UTC labels successfully removed from outputs")
    return True


def main():
    """Run all timezone and formatting tests."""
    print("🧪 Running Timezone and Formatting Consistency Tests\n")
    
    tests = [
        ("Timestamp Format", test_timestamp_format),
        ("Minnesota Timezone", test_minnesota_timezone),
        ("Feedback Formatting Consistency", test_feedback_formatting_consistency),
        ("PDF Timestamp Extraction", test_pdf_timestamp_extraction),
        ("No UTC Labels", test_no_utc_label_in_output),
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
        print("🎉 All timezone and formatting tests passed!")
        return 0
    else:
        print(f"⚠️  {total - passed} tests failed.")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
