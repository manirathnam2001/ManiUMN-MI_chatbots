#!/usr/bin/env python3
"""
Test to verify feedback filename convention.
Validates that filenames follow the format: [Student]-[Bot]-[Persona] Feedback.pdf
"""

import sys
import traceback
from pdf_utils import construct_feedback_filename
from feedback_template import FeedbackFormatter


def test_basic_filename_construction():
    """Test basic filename construction with all parameters."""
    print("🧪 Testing Basic Filename Construction")
    
    test_cases = [
        # (student, bot, persona, expected)
        ("Mani", "OHI", "Charles", "Mani-OHI-Charles Feedback.pdf"),
        ("John Doe", "HPV", "Diana", "John_Doe-HPV-Diana Feedback.pdf"),
        ("Jane Smith", "Perio", "Alex", "Jane_Smith-Perio-Alex Feedback.pdf"),
        ("Bob", "Tobacco", "Sam", "Bob-Tobacco-Sam Feedback.pdf"),
    ]
    
    try:
        for student, bot, persona, expected in test_cases:
            result = construct_feedback_filename(student, bot, persona)
            assert result == expected, f"Expected '{expected}', got '{result}'"
        
        print(f"✅ All basic filename construction tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Basic filename construction test failed: {e}")
        traceback.print_exc()
        return False


def test_filename_without_persona():
    """Test filename construction without persona."""
    print("🧪 Testing Filename Without Persona")
    
    test_cases = [
        # (student, bot, expected)
        ("Alice", "OHI", "Alice-OHI Feedback.pdf"),
        ("Bob Smith", "HPV", "Bob_Smith-HPV Feedback.pdf"),
        ("Charlie", "Perio", "Charlie-Perio Feedback.pdf"),
    ]
    
    try:
        for student, bot, expected in test_cases:
            result = construct_feedback_filename(student, bot, None)
            assert result == expected, f"Expected '{expected}', got '{result}'"
        
        print(f"✅ Filename without persona tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Filename without persona test failed: {e}")
        traceback.print_exc()
        return False


def test_special_character_sanitization():
    """Test that special characters are properly sanitized."""
    print("🧪 Testing Special Character Sanitization")
    
    test_cases = [
        # (student, bot, persona, expected)
        ("John@Doe", "OHI", "Charles", "JohnDoe-OHI-Charles Feedback.pdf"),
        ("Jane/Smith", "HPV", "Diana#1", "JaneSmith-HPV-Diana1 Feedback.pdf"),
        ("Bob (Test)", "Perio", "Alex*", "Bob_Test-Perio-Alex Feedback.pdf"),
        ("Alice's Test", "Tobacco", "Sam", "Alices_Test-Tobacco-Sam Feedback.pdf"),
    ]
    
    try:
        for student, bot, persona, expected in test_cases:
            result = construct_feedback_filename(student, bot, persona)
            assert result == expected, f"Expected '{expected}', got '{result}'"
        
        print(f"✅ Special character sanitization tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Special character sanitization test failed: {e}")
        traceback.print_exc()
        return False


def test_space_handling():
    """Test that spaces are converted to underscores."""
    print("🧪 Testing Space Handling")
    
    test_cases = [
        # (student, bot, persona, expected)
        ("John   Doe", "OHI", "Charles", "John_Doe-OHI-Charles Feedback.pdf"),
        ("Jane  Smith  Jr", "HPV", "Diana Ray", "Jane_Smith_Jr-HPV-Diana_Ray Feedback.pdf"),
        ("Multiple   Spaces", "Perio", None, "Multiple_Spaces-Perio Feedback.pdf"),
    ]
    
    try:
        for student, bot, persona, expected in test_cases:
            result = construct_feedback_filename(student, bot, persona)
            assert result == expected, f"Expected '{expected}', got '{result}'"
        
        print(f"✅ Space handling tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Space handling test failed: {e}")
        traceback.print_exc()
        return False


def test_empty_inputs():
    """Test that empty inputs raise appropriate errors."""
    print("🧪 Testing Empty Input Validation")
    
    try:
        # Empty student name should raise ValueError
        try:
            construct_feedback_filename("", "OHI", "Charles")
            assert False, "Empty student name should raise ValueError"
        except ValueError:
            pass
        
        # Empty bot name should raise ValueError
        try:
            construct_feedback_filename("John", "", "Charles")
            assert False, "Empty bot name should raise ValueError"
        except ValueError:
            pass
        
        # Empty persona should be acceptable (optional parameter)
        result = construct_feedback_filename("John", "OHI", "")
        assert result == "John-OHI Feedback.pdf", f"Empty persona should work, got '{result}'"
        
        print(f"✅ Empty input validation tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Empty input validation test failed: {e}")
        traceback.print_exc()
        return False


def test_formatter_integration():
    """Test FeedbackFormatter.create_download_filename integration."""
    print("🧪 Testing FeedbackFormatter Integration")
    
    test_cases = [
        # (student, session_type, persona, expected_pattern)
        ("Mani", "HPV Vaccine", "Diana", "Mani-HPV-Diana Feedback.pdf"),
        ("John", "OHI Session", "Charles", "John-OHI-Charles Feedback.pdf"),
        ("Jane", "Oral Health", "Alex", "Jane-OHI-Alex Feedback.pdf"),
        ("Bob", "Perio Session", "Sam", "Bob-Perio-Sam Feedback.pdf"),
        ("Alice", "Tobacco Cessation", "Chris", "Alice-Tobacco-Chris Feedback.pdf"),
    ]
    
    try:
        for student, session_type, persona, expected in test_cases:
            result = FeedbackFormatter.create_download_filename(student, session_type, persona)
            assert result == expected, f"Expected '{expected}', got '{result}'"
        
        print(f"✅ FeedbackFormatter integration tests passed")
        return True
        
    except Exception as e:
        print(f"❌ FeedbackFormatter integration test failed: {e}")
        traceback.print_exc()
        return False


def test_filesystem_safety():
    """Test that filenames are safe for filesystem use."""
    print("🧪 Testing Filesystem Safety")
    
    import os
    
    # Characters that are problematic in filenames on various OS
    problematic_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|', '\0']
    
    try:
        # Test that problematic characters are removed
        for char in problematic_chars:
            student = f"Test{char}Name"
            result = construct_feedback_filename(student, "OHI", "Persona")
            
            # Verify no problematic characters in result
            for prob_char in problematic_chars:
                assert prob_char not in result, f"Problematic character '{prob_char}' found in '{result}'"
        
        print(f"✅ Filesystem safety tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Filesystem safety test failed: {e}")
        traceback.print_exc()
        return False


def main():
    """Run all filename convention tests."""
    print("🧪 Testing Feedback Filename Convention\n")
    
    tests = [
        ("Basic Filename Construction", test_basic_filename_construction),
        ("Filename Without Persona", test_filename_without_persona),
        ("Special Character Sanitization", test_special_character_sanitization),
        ("Space Handling", test_space_handling),
        ("Empty Input Validation", test_empty_inputs),
        ("FeedbackFormatter Integration", test_formatter_integration),
        ("Filesystem Safety", test_filesystem_safety),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}:")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} failed")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All feedback filename convention tests passed!")
        return 0
    else:
        print(f"⚠️  {total - passed} tests failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
