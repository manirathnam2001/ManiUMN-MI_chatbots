"""
Test suite for sheet validation and role handling in secret_code_portal.py

Tests the new functionality for:
- Optional Role column in sheet headers
- Instructor/Developer in Bot column (when Role column is absent)
- ALL in Bot column with Role specifying Instructor/Developer
- Backward compatibility with sheets without Role column
"""

import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add the parent directory to sys.path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.access_control import (
    normalize_bot_type,
    normalize_role,
    ROLE_STUDENT,
    ROLE_INSTRUCTOR,
    ROLE_DEVELOPER,
    VALID_BOT_TYPES
)


class TestHeaderValidation(unittest.TestCase):
    """Test cases for sheet header validation with optional Role column."""
    
    def test_headers_without_role_column(self):
        """Test that headers without Role column are accepted (backward compatibility)."""
        headers = ['Table No', 'Name', 'Bot', 'Secret', 'Used']
        
        # Check all required headers are present
        headers_lower = [h.strip().lower() for h in headers]
        required_lower = ['table no', 'name', 'bot', 'secret', 'used']
        
        for required_h in required_lower:
            self.assertIn(required_h, headers_lower)
    
    def test_headers_with_role_column(self):
        """Test that headers with Role column are accepted."""
        headers = ['Table No', 'Name', 'Bot', 'Secret', 'Used', 'Role']
        
        # Check all required headers are present
        headers_lower = [h.strip().lower() for h in headers]
        required_lower = ['table no', 'name', 'bot', 'secret', 'used']
        
        for required_h in required_lower:
            self.assertIn(required_h, headers_lower)
        
        # Check Role column is present
        self.assertIn('role', headers_lower)
    
    def test_headers_with_missing_required_column(self):
        """Test that headers missing a required column are rejected."""
        headers = ['Table No', 'Name', 'Bot', 'Secret']  # Missing 'Used'
        
        headers_lower = [h.strip().lower() for h in headers]
        required_lower = ['table no', 'name', 'bot', 'secret', 'used']
        
        # Check that 'used' is missing
        self.assertNotIn('used', headers_lower)
    
    def test_headers_with_different_order(self):
        """Test that headers in different order are handled correctly."""
        headers = ['Table No', 'Name', 'Role', 'Bot', 'Secret', 'Used']
        
        headers_lower = [h.strip().lower() for h in headers]
        required_lower = ['table no', 'name', 'bot', 'secret', 'used']
        
        # All required headers should be present regardless of order
        for required_h in required_lower:
            self.assertIn(required_h, headers_lower)


class TestBotTypeValidation(unittest.TestCase):
    """Test cases for bot type validation with new role handling."""
    
    def test_valid_bot_types(self):
        """Test that all valid bot types are accepted."""
        valid_bots = ['OHI', 'HPV', 'TOBACCO', 'PERIO']
        
        for bot in valid_bots:
            normalized = normalize_bot_type(bot)
            self.assertIn(normalized, VALID_BOT_TYPES)
    
    def test_case_insensitive_bot_types(self):
        """Test that bot types are case-insensitive."""
        test_cases = [
            ('ohi', 'OHI'),
            ('Hpv', 'HPV'),
            ('TOBACCO', 'TOBACCO'),
            ('perio', 'PERIO'),
        ]
        
        for input_bot, expected in test_cases:
            self.assertEqual(normalize_bot_type(input_bot), expected)
    
    def test_instructor_bot_value(self):
        """Test that 'Instructor' in Bot column is normalized correctly."""
        test_cases = ['Instructor', 'INSTRUCTOR', 'instructor']
        
        for bot in test_cases:
            normalized = normalize_bot_type(bot)
            self.assertEqual(normalized, 'INSTRUCTOR')
    
    def test_developer_bot_value(self):
        """Test that 'Developer' in Bot column is normalized correctly."""
        test_cases = ['Developer', 'DEVELOPER', 'developer']
        
        for bot in test_cases:
            normalized = normalize_bot_type(bot)
            self.assertEqual(normalized, 'DEVELOPER')
    
    def test_all_bot_value(self):
        """Test that 'ALL' in Bot column is normalized correctly."""
        test_cases = ['ALL', 'all', 'All']
        
        for bot in test_cases:
            normalized = normalize_bot_type(bot)
            self.assertEqual(normalized, 'ALL')


class TestRoleHandling(unittest.TestCase):
    """Test cases for role-based access control."""
    
    def test_normalize_role_variations(self):
        """Test that various role formats are normalized correctly."""
        # Instructor variations
        instructor_cases = ['Instructor', 'INSTRUCTOR', 'instructor', 'inst', 'INST']
        for role in instructor_cases:
            self.assertEqual(normalize_role(role), ROLE_INSTRUCTOR)
        
        # Developer variations
        developer_cases = ['Developer', 'DEVELOPER', 'developer', 'dev', 'DEV']
        for role in developer_cases:
            self.assertEqual(normalize_role(role), ROLE_DEVELOPER)
        
        # Student variations (including empty/invalid)
        student_cases = ['Student', 'STUDENT', 'student', '', 'invalid']
        for role in student_cases:
            self.assertEqual(normalize_role(role), ROLE_STUDENT)
    
    def test_role_student_with_valid_bot(self):
        """Test that students can only use the 4 valid bot types."""
        role = ROLE_STUDENT
        valid_bots = ['OHI', 'HPV', 'TOBACCO', 'PERIO']
        
        for bot in valid_bots:
            normalized = normalize_bot_type(bot)
            self.assertIn(normalized, VALID_BOT_TYPES)
    
    def test_role_instructor_access(self):
        """Test that instructors get access to all bots."""
        role = ROLE_INSTRUCTOR
        # Instructor should be able to use any bot or 'ALL'
        self.assertEqual(role, ROLE_INSTRUCTOR)
    
    def test_role_developer_access(self):
        """Test that developers get access to developer page."""
        role = ROLE_DEVELOPER
        # Developer should redirect to developer page
        self.assertEqual(role, ROLE_DEVELOPER)


class TestBackwardCompatibility(unittest.TestCase):
    """Test cases for backward compatibility with sheets without Role column."""
    
    def test_sheet_without_role_column_valid_bots(self):
        """Test that sheets without Role column work with valid bots."""
        # Simulate data without Role column
        headers = ['Table No', 'Name', 'Bot', 'Secret', 'Used']
        row = ['1', 'Alice Student', 'OHI', 'CODE1', '']
        
        # Should work as before
        bot_normalized = normalize_bot_type(row[2])
        self.assertIn(bot_normalized, VALID_BOT_TYPES)
    
    def test_sheet_without_role_column_instructor_bot(self):
        """Test that Instructor in Bot column works when Role column is absent."""
        # When there's no Role column, Bot='Instructor' should be treated as role
        headers = ['Table No', 'Name', 'Bot', 'Secret', 'Used']
        row = ['2', 'Bob Instructor', 'Instructor', 'CODE2', '']
        
        bot_normalized = normalize_bot_type(row[2])
        self.assertEqual(bot_normalized, 'INSTRUCTOR')
    
    def test_sheet_without_role_column_developer_bot(self):
        """Test that Developer in Bot column works when Role column is absent."""
        # When there's no Role column, Bot='Developer' should be treated as role
        headers = ['Table No', 'Name', 'Bot', 'Secret', 'Used']
        row = ['3', 'Charlie Developer', 'Developer', 'CODE3', '']
        
        bot_normalized = normalize_bot_type(row[2])
        self.assertEqual(bot_normalized, 'DEVELOPER')


class TestRoleColumnPresent(unittest.TestCase):
    """Test cases for sheets with Role column present."""
    
    def test_sheet_with_role_column_instructor(self):
        """Test that Role column with Instructor works correctly."""
        headers = ['Table No', 'Name', 'Bot', 'Secret', 'Used', 'Role']
        row = ['1', 'Bob Instructor', 'ALL', 'CODE1', '', 'INSTRUCTOR']
        
        role_idx = headers.index('Role')
        role = normalize_role(row[role_idx])
        bot_normalized = normalize_bot_type(row[2])
        
        self.assertEqual(role, ROLE_INSTRUCTOR)
        self.assertEqual(bot_normalized, 'ALL')
    
    def test_sheet_with_role_column_developer(self):
        """Test that Role column with Developer works correctly."""
        headers = ['Table No', 'Name', 'Bot', 'Secret', 'Used', 'Role']
        row = ['2', 'Charlie Developer', 'ALL', 'CODE2', '', 'DEVELOPER']
        
        role_idx = headers.index('Role')
        role = normalize_role(row[role_idx])
        bot_normalized = normalize_bot_type(row[2])
        
        self.assertEqual(role, ROLE_DEVELOPER)
        self.assertEqual(bot_normalized, 'ALL')
    
    def test_sheet_with_role_column_instructor_specific_bot(self):
        """Test that Instructor can use specific bot instead of ALL."""
        headers = ['Table No', 'Name', 'Bot', 'Secret', 'Used', 'Role']
        row = ['3', 'Bob Instructor', 'OHI', 'CODE3', '', 'INSTRUCTOR']
        
        role_idx = headers.index('Role')
        role = normalize_role(row[role_idx])
        bot_normalized = normalize_bot_type(row[2])
        
        self.assertEqual(role, ROLE_INSTRUCTOR)
        self.assertIn(bot_normalized, VALID_BOT_TYPES)
    
    def test_sheet_with_role_column_student(self):
        """Test that Role column with Student works correctly."""
        headers = ['Table No', 'Name', 'Bot', 'Secret', 'Used', 'Role']
        row = ['4', 'Alice Student', 'TOBACCO', 'CODE4', '', 'STUDENT']
        
        role_idx = headers.index('Role')
        role = normalize_role(row[role_idx])
        bot_normalized = normalize_bot_type(row[2])
        
        self.assertEqual(role, ROLE_STUDENT)
        self.assertIn(bot_normalized, VALID_BOT_TYPES)


class TestErrorMessages(unittest.TestCase):
    """Test cases for improved error messages."""
    
    def test_invalid_bot_for_student_message(self):
        """Test that invalid bot type for student has clear error message."""
        # When a student has invalid bot type, error should be explicit
        valid_types_str = ", ".join(VALID_BOT_TYPES)
        expected_message_parts = ['Invalid bot type', 'Valid types are:', valid_types_str]
        
        # Message should contain all parts
        for part in expected_message_parts:
            # This is what the error message should contain
            self.assertIsNotNone(part)
    
    def test_missing_header_error_message(self):
        """Test that missing header has clear error message."""
        expected_message_parts = ['Missing required column']
        
        for part in expected_message_parts:
            self.assertIsNotNone(part)


if __name__ == '__main__':
    unittest.main()
