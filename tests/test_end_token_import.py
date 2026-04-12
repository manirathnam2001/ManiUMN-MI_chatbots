#!/usr/bin/env python3
"""
Test suite to verify END_TOKEN import in chat_utils.py

This test ensures that END_TOKEN is properly imported and can be used
in chat_utils.py without NameError.
"""

import sys
import ast
import traceback


def test_end_token_in_import_statement():
    """Test that END_TOKEN is included in the import statement."""
    try:
        # Read the chat_utils.py file
        with open('chat_utils.py', 'r') as f:
            content = f.read()
        
        # Parse the file as an AST
        tree = ast.parse(content)
        
        # Look for the import from end_control_middleware
        found_end_token = False
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == 'end_control_middleware':
                # Check if END_TOKEN is in the imported names
                for alias in node.names:
                    if alias.name == 'END_TOKEN':
                        found_end_token = True
                        break
        
        assert found_end_token, "END_TOKEN should be imported from end_control_middleware"
        print("✓ test_end_token_in_import_statement passed")
        return True
        
    except Exception as e:
        print(f"✗ test_end_token_in_import_statement failed with error: {e}")
        traceback.print_exc()
        return False


def test_end_token_import():
    """Test that END_TOKEN can be imported from end_control_middleware."""
    try:
        # Import END_TOKEN from end_control_middleware
        from end_control_middleware import END_TOKEN
        
        # Create a test f-string similar to the one in chat_utils.py line 346
        test_string = f"include the end token: {END_TOKEN}"
        
        assert END_TOKEN in test_string, "END_TOKEN should be in the formatted string"
        assert "<<END>>" in test_string or END_TOKEN == test_string.split(": ")[1], \
            "END_TOKEN should have a value (default: '<<END>>')"
        
        print("✓ test_end_token_import passed")
        print(f"  END_TOKEN value: {END_TOKEN}")
        return True
        
    except NameError as e:
        print(f"✗ test_end_token_import failed with NameError: {e}")
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"✗ test_end_token_import failed with error: {e}")
        traceback.print_exc()
        return False


def test_end_token_usage_in_file():
    """Test that END_TOKEN is used in an f-string in chat_utils.py."""
    try:
        # Read the chat_utils.py file
        with open('chat_utils.py', 'r') as f:
            content = f.read()
        
        # Check that END_TOKEN is used in an f-string
        assert '{END_TOKEN}' in content, "END_TOKEN should be used in an f-string"
        
        # Check that the line we're looking for exists
        expected_line = "include the end token: {END_TOKEN}"
        assert expected_line in content, "The expected f-string usage should be present"
        
        print("✓ test_end_token_usage_in_file passed")
        return True
        
    except Exception as e:
        print(f"✗ test_end_token_usage_in_file failed with error: {e}")
        traceback.print_exc()
        return False


def main():
    """Run all tests and report results."""
    print("=" * 60)
    print("Testing END_TOKEN import in chat_utils.py")
    print("=" * 60)
    
    all_passed = True
    
    # Run tests
    all_passed &= test_end_token_in_import_statement()
    all_passed &= test_end_token_import()
    all_passed &= test_end_token_usage_in_file()
    
    print("=" * 60)
    if all_passed:
        print("✓ All tests passed!")
        print("=" * 60)
        return 0
    else:
        print("✗ Some tests failed")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
