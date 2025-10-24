"""
Test for error handling in secret_code_portal.py

This test validates that:
1. StreamlitAPIException is imported
2. st.switch_page calls are wrapped in try/except blocks
3. User-friendly error messages are provided
"""

import ast
import sys


def test_streamlit_api_exception_import():
    """Test that StreamlitAPIException is imported."""
    print("Testing StreamlitAPIException import...")
    
    with open('secret_code_portal.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for the import
    assert 'from streamlit.errors import StreamlitAPIException' in content, \
        "StreamlitAPIException should be imported from streamlit.errors"
    
    print("✓ StreamlitAPIException is properly imported")


def test_switch_page_error_handling():
    """Test that st.switch_page calls are wrapped in try/except blocks."""
    print("\nTesting st.switch_page error handling...")
    
    with open('secret_code_portal.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Parse the AST
    tree = ast.parse(content)
    
    # Find all st.switch_page calls
    switch_page_calls = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                if node.func.attr == 'switch_page':
                    switch_page_calls.append(node)
    
    assert len(switch_page_calls) >= 4, \
        f"Expected at least 4 st.switch_page calls (2 in portal, 2 in guards), found {len(switch_page_calls)}"
    
    # Find all try/except blocks that catch StreamlitAPIException
    try_except_blocks = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Try):
            for handler in node.handlers:
                if handler.type:
                    # Check if it catches StreamlitAPIException
                    if isinstance(handler.type, ast.Name):
                        if handler.type.id == 'StreamlitAPIException':
                            try_except_blocks.append(node)
    
    # We expect at least 2 try/except blocks in the portal (for the two navigation points)
    assert len(try_except_blocks) >= 2, \
        f"Expected at least 2 try/except blocks catching StreamlitAPIException, found {len(try_except_blocks)}"
    
    print(f"✓ Found {len(try_except_blocks)} try/except blocks with StreamlitAPIException handling")


def test_error_messages():
    """Test that user-friendly error messages are present."""
    print("\nTesting user-friendly error messages...")
    
    with open('secret_code_portal.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for error message patterns
    assert 'Navigation Error' in content, \
        "Should have 'Navigation Error' in error messages"
    assert 'Could not find the' in content, \
        "Should explain that the page could not be found"
    assert 'deployment issue' in content, \
        "Should mention deployment issue"
    assert 'contact support' in content, \
        "Should instruct user to contact support"
    
    print("✓ User-friendly error messages are present")


def test_technical_details():
    """Test that technical details are provided for debugging."""
    print("\nTesting technical details in error messages...")
    
    with open('secret_code_portal.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for technical details
    assert 'Technical Details' in content, \
        "Should provide technical details section"
    assert 'missing or misconfigured' in content, \
        "Should mention that page might be missing or misconfigured"
    
    print("✓ Technical details are provided for debugging")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Error Handling Tests")
    print("=" * 60)
    
    try:
        test_streamlit_api_exception_import()
        test_switch_page_error_handling()
        test_error_messages()
        test_technical_details()
        
        print("\n" + "=" * 60)
        print("✓ All error handling tests passed!")
        print("=" * 60)
        return 0
    
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
