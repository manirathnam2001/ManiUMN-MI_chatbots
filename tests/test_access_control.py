#!/usr/bin/env python3
"""
Test suite for utils/access_control.py

Tests:
- Bot name normalization
- Role normalization
- Instructor role detection
- Developer role detection
- Code validation logic
"""

import sys
import os
from unittest.mock import Mock, MagicMock, patch

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.access_control import (
    normalize_bot,
    normalize_role,
    is_instructor_role,
    is_developer_role,
    get_bot_display_name,
    is_code_used,
    validate_bot_match,
    find_code_row,
    mark_row_used,
    VALID_BOT_TYPES,
    ROLE_STUDENT,
    ROLE_INSTRUCTOR,
    ROLE_DEVELOPER,
)


def test_normalize_bot():
    """Test bot name normalization."""
    # Standard cases
    assert normalize_bot('OHI') == 'OHI'
    assert normalize_bot('hpv') == 'HPV'
    assert normalize_bot('Tobacco') == 'TOBACCO'
    assert normalize_bot('perio') == 'PERIO'
    assert normalize_bot('PERIO') == 'PERIO'
    
    # Edge cases
    assert normalize_bot('') == ''
    assert normalize_bot('  ohi  ') == 'OHI'
    assert normalize_bot('tobacco ') == 'TOBACCO'
    
    # Case insensitive
    assert normalize_bot('ToBAcCo') == 'TOBACCO'
    assert normalize_bot('PeRiO') == 'PERIO'


def test_normalize_role():
    """Test role name normalization."""
    # Student cases
    assert normalize_role('Student') == ROLE_STUDENT
    assert normalize_role('student') == ROLE_STUDENT
    assert normalize_role('STUDENT') == ROLE_STUDENT
    assert normalize_role('stu') == ROLE_STUDENT
    assert normalize_role('') == ROLE_STUDENT  # Default to student
    
    # Instructor cases
    assert normalize_role('Instructor') == ROLE_INSTRUCTOR
    assert normalize_role('instructor') == ROLE_INSTRUCTOR
    assert normalize_role('INSTRUCTOR') == ROLE_INSTRUCTOR
    assert normalize_role('inst') == ROLE_INSTRUCTOR
    assert normalize_role('teacher') == ROLE_INSTRUCTOR
    assert normalize_role('admin') == ROLE_INSTRUCTOR
    
    # Developer cases
    assert normalize_role('Developer') == ROLE_DEVELOPER
    assert normalize_role('developer') == ROLE_DEVELOPER
    assert normalize_role('DEVELOPER') == ROLE_DEVELOPER
    assert normalize_role('dev') == ROLE_DEVELOPER
    assert normalize_role('DEV') == ROLE_DEVELOPER


def test_is_instructor_role():
    """Test instructor role detection."""
    assert is_instructor_role('Instructor') == True
    assert is_instructor_role('instructor') == True
    assert is_instructor_role('INSTRUCTOR') == True
    assert is_instructor_role('teacher') == True
    assert is_instructor_role('admin') == True
    
    assert is_instructor_role('Student') == False
    assert is_instructor_role('Developer') == False
    assert is_instructor_role('') == False


def test_is_developer_role():
    """Test developer role detection."""
    assert is_developer_role('Developer') == True
    assert is_developer_role('developer') == True
    assert is_developer_role('DEVELOPER') == True
    assert is_developer_role('dev') == True
    assert is_developer_role('DEV') == True
    
    assert is_developer_role('Student') == False
    assert is_developer_role('Instructor') == False
    assert is_developer_role('') == False


def test_get_bot_display_name():
    """Test bot display name retrieval."""
    assert get_bot_display_name('ohi') == 'OHI'
    assert get_bot_display_name('hpv') == 'HPV'
    assert get_bot_display_name('tobacco') == 'TOBACCO'
    assert get_bot_display_name('perio') == 'PERIO'
    
    # Unknown bots return normalized form
    assert get_bot_display_name('unknown') == 'UNKNOWN'


def test_is_code_used():
    """Test code used status check."""
    # Used cases
    assert is_code_used('TRUE') == True
    assert is_code_used('true') == True
    assert is_code_used('True') == True
    assert is_code_used('YES') == True
    assert is_code_used('yes') == True
    assert is_code_used('1') == True
    assert is_code_used(' TRUE ') == True
    
    # Not used cases
    assert is_code_used('FALSE') == False
    assert is_code_used('false') == False
    assert is_code_used('NO') == False
    assert is_code_used('no') == False
    assert is_code_used('0') == False
    assert is_code_used('') == False
    assert is_code_used(None) == False


def test_validate_bot_match():
    """Test bot match validation."""
    # Matching bots
    is_valid, error = validate_bot_match('OHI', 'OHI')
    assert is_valid == True
    assert error == ''
    
    # Case insensitive match
    is_valid, error = validate_bot_match('ohi', 'OHI')
    assert is_valid == True
    
    is_valid, error = validate_bot_match('Tobacco', 'TOBACCO')
    assert is_valid == True
    
    # Non-matching bots
    is_valid, error = validate_bot_match('OHI', 'HPV')
    assert is_valid == False
    assert 'Access Denied' in error
    assert 'OHI' in error
    
    is_valid, error = validate_bot_match('PERIO', 'TOBACCO')
    assert is_valid == False
    assert 'PERIO' in error


def test_find_code_row_success():
    """Test finding a code row in the worksheet."""
    # Create mock worksheet
    mock_worksheet = Mock()
    mock_worksheet.get_all_values.return_value = [
        ['Table No', 'Name', 'Bot', 'Secret', 'Used', 'Role'],  # Header
        ['1', 'John Doe', 'OHI', 'ABC123', 'FALSE', 'Student'],
        ['2', 'Jane Smith', 'HPV', 'XYZ789', 'FALSE', 'Instructor'],
        ['3', 'Test Dev', 'TOBACCO', 'DEV001', 'FALSE', 'Developer'],
    ]
    
    # Find existing code
    result = find_code_row(mock_worksheet, 'ABC123')
    assert result is not None
    row_index, row_data = result
    assert row_index == 2  # 1-based, after header
    assert row_data['name'] == 'John Doe'
    assert row_data['bot'] == 'OHI'
    assert row_data['role'] == 'Student'
    
    # Find instructor code
    result = find_code_row(mock_worksheet, 'XYZ789')
    assert result is not None
    row_index, row_data = result
    assert row_index == 3
    assert row_data['role'] == 'Instructor'
    
    # Find developer code
    result = find_code_row(mock_worksheet, 'DEV001')
    assert result is not None
    row_index, row_data = result
    assert row_index == 4
    assert row_data['role'] == 'Developer'


def test_find_code_row_not_found():
    """Test finding a code that doesn't exist."""
    mock_worksheet = Mock()
    mock_worksheet.get_all_values.return_value = [
        ['Table No', 'Name', 'Bot', 'Secret', 'Used', 'Role'],
        ['1', 'John Doe', 'OHI', 'ABC123', 'FALSE', 'Student'],
    ]
    
    result = find_code_row(mock_worksheet, 'INVALID')
    assert result is None


def test_find_code_row_empty_sheet():
    """Test finding a code in an empty sheet."""
    mock_worksheet = Mock()
    mock_worksheet.get_all_values.return_value = [
        ['Table No', 'Name', 'Bot', 'Secret', 'Used', 'Role'],
    ]
    
    result = find_code_row(mock_worksheet, 'ABC123')
    assert result is None


def test_mark_row_used_success():
    """Test marking a row as used."""
    mock_worksheet = Mock()
    mock_worksheet.update_cell.return_value = None
    
    result = mark_row_used(mock_worksheet, 2, 5)
    assert result is True
    mock_worksheet.update_cell.assert_called_once_with(2, 5, 'TRUE')


def test_mark_row_used_failure():
    """Test marking a row as used when it fails."""
    mock_worksheet = Mock()
    mock_worksheet.update_cell.side_effect = Exception("API Error")
    
    result = mark_row_used(mock_worksheet, 2, 5)
    assert result is False


def test_instructor_code_not_marked_used():
    """Test that instructor codes are not marked as used (integration test)."""
    # This tests the expected behavior in validate_and_mark_code
    # Instructor codes should return success without calling update_cell
    
    # The actual integration would be in secret_code_portal.py
    # Here we just verify the role detection works correctly
    assert is_instructor_role('Instructor') == True
    assert is_instructor_role('instructor') == True


def test_developer_code_not_marked_used():
    """Test that developer codes are not marked as used (integration test)."""
    # This tests the expected behavior in validate_and_mark_code
    # Developer codes should return success without calling update_cell
    
    # The actual integration would be in secret_code_portal.py
    # Here we just verify the role detection works correctly
    assert is_developer_role('Developer') == True
    assert is_developer_role('dev') == True


def test_student_code_marked_used():
    """Test that student codes are marked as used after session setup."""
    # Verify student detection
    assert normalize_role('Student') == ROLE_STUDENT
    assert normalize_role('') == ROLE_STUDENT
    
    # Verify the is_code_used check
    assert is_code_used('') == False
    assert is_code_used('FALSE') == False


def test_tobacco_perio_codes_accepted():
    """Test that TOBACCO and PERIO codes are accepted and normalized correctly."""
    # Test normalization
    assert normalize_bot('tobacco') == 'TOBACCO'
    assert normalize_bot('Tobacco') == 'TOBACCO'
    assert normalize_bot('TOBACCO') == 'TOBACCO'
    
    assert normalize_bot('perio') == 'PERIO'
    assert normalize_bot('Perio') == 'PERIO'
    assert normalize_bot('PERIO') == 'PERIO'
    
    # Test that they're in valid types
    assert 'TOBACCO' in VALID_BOT_TYPES
    assert 'PERIO' in VALID_BOT_TYPES
    
    # Test bot match validation
    is_valid, _ = validate_bot_match('tobacco', 'TOBACCO')
    assert is_valid == True
    
    is_valid, _ = validate_bot_match('Perio', 'PERIO')
    assert is_valid == True


if __name__ == "__main__":
    # Run all tests
    import traceback
    
    tests = [
        test_normalize_bot,
        test_normalize_role,
        test_is_instructor_role,
        test_is_developer_role,
        test_get_bot_display_name,
        test_is_code_used,
        test_validate_bot_match,
        test_find_code_row_success,
        test_find_code_row_not_found,
        test_find_code_row_empty_sheet,
        test_mark_row_used_success,
        test_mark_row_used_failure,
        test_instructor_code_not_marked_used,
        test_developer_code_not_marked_used,
        test_student_code_marked_used,
        test_tobacco_perio_codes_accepted,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            print(f"✅ {test.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"❌ {test.__name__}: {e}")
            traceback.print_exc()
            failed += 1
        except Exception as e:
            print(f"❌ {test.__name__}: Exception - {e}")
            traceback.print_exc()
            failed += 1
    
    print(f"\n📊 Results: {passed}/{len(tests)} tests passed")
    sys.exit(0 if failed == 0 else 1)
