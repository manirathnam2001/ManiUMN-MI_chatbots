#!/usr/bin/env python3
"""
Test to verify that imports work correctly with path handling.
"""
import sys
import os

# Add current directory to path to ensure imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Test imports
try:
    from pdf_utils import generate_pdf_report
    from time_utils import convert_to_minnesota_time, get_formatted_utc_time
    from feedback_template import FeedbackFormatter
    from scoring_utils import validate_student_name
    print("✅ All imports work correctly with path handling")
    print(f"   - pdf_utils imported successfully")
    print(f"   - time_utils imported successfully")
    print(f"   - feedback_template imported successfully")
    print(f"   - scoring_utils imported successfully")
    
    # Test a simple function call
    test_time = convert_to_minnesota_time("2025-01-15 18:00:00")
    print(f"\n✅ Function call test successful:")
    print(f"   - convert_to_minnesota_time works: {test_time}")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    sys.exit(1)

print("\n✅ All import tests passed!")
