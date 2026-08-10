"""
Integration tests for multipage app structure and authentication flow.

This test validates:
1. Multipage structure exists (pages/ directory with OHI.py and HPV.py)
2. Authentication guards are present in bot pages
3. Portal has credential inputs and internal navigation
4. Caching decorators are properly applied
5. No external URLs are exposed in the portal UI
"""

import os
import ast
import sys


def test_multipage_structure():
    """Test that multipage structure exists."""
    print("Testing multipage structure...")
    
    # Check pages directory exists
    assert os.path.exists('pages'), "pages/ directory should exist"
    
    # Check bot files are in pages directory
    assert os.path.exists('pages/OHI.py'), "pages/OHI.py should exist"
    assert os.path.exists('pages/HPV.py'), "pages/HPV.py should exist"
    
    # Check main portal is at root
    assert os.path.exists('secret_code_portal.py'), "secret_code_portal.py should exist at root"
    
    print("✓ Multipage structure is correct")


def test_bot_pages_delegate_to_the_shared_runner():
    """Every bot page must route through mi_session.run_practice_session.

    The bot pages used to carry their own inline authentication guard. That
    guard now lives in mi_session._auth_guard, and the pages are thin shells
    that call run_practice_session. A page that stopped delegating would
    silently lose authentication, so the delegation is the property worth
    asserting here. The guard itself is tested in
    test_shared_runner_enforces_authentication below.
    """
    print("\nTesting that bot pages delegate to the shared runner...")

    for page in ['pages/OHI.py', 'pages/HPV.py', 'pages/Perio.py', 'pages/Tobacco.py']:
        with open(page, 'r', encoding='utf-8') as f:
            content = f.read()

        assert 'run_practice_session' in content, \
            f"{page} must call run_practice_session, which applies the auth guard"
        assert 'SessionConfig' in content, \
            f"{page} must construct a SessionConfig"

        # The page must not have reintroduced its own API key input.
        assert 'text_input' not in content, \
            f"{page} should not collect credentials; the portal does that"

        print(f"  OK {page} delegates to the shared runner")


def test_shared_runner_enforces_authentication():
    """mi_session._auth_guard must perform the checks the pages used to do.

    Asserted against the source of mi_session rather than the pages, because
    that is where the logic moved.
    """
    print("\nTesting the shared authentication guard...")

    with open('mi_session.py', 'r', encoding='utf-8') as f:
        content = f.read()

    assert 'def _auth_guard' in content, \
        "mi_session must define _auth_guard"
    assert 'st.session_state.get("authenticated"' in content, \
        "_auth_guard must check the authenticated flag"
    assert 'st.switch_page' in content, \
        "_auth_guard must offer a redirect back to the portal"
    assert 'st.stop()' in content, \
        "_auth_guard must halt rendering when a check fails"
    assert 'student_name' in content, \
        "_auth_guard must require student_name in session state"
    assert '_auth_guard(' in content, \
        "run_practice_session must actually invoke _auth_guard"

    print("  OK shared auth guard enforces authentication")


def test_portal_credentials():
    """Test that portal has credential inputs."""
    print("\nTesting portal credential inputs...")
    
    with open('secret_code_portal.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for credential inputs
    assert 'Student Name' in content or 'student_name' in content, \
        "Portal should have student name input"
    assert 'Groq API Key' in content or 'groq_api_key' in content, \
        "Portal should have Groq API key input"
    
    # Check that credentials are stored in session state
    assert 'st.session_state.student_name' in content, \
        "Portal should store student name in session state"
    assert 'st.session_state.groq_api_key' in content, \
        "Portal should store API key in session state"
    
    # Check for internal navigation
    assert 'st.switch_page' in content, \
        "Portal should use st.switch_page for internal navigation"
    
    print("✓ Portal has proper credential inputs and navigation")


def test_caching_decorators():
    """Test that caching decorators are properly applied."""
    print("\nTesting caching decorators...")
    
    with open('secret_code_portal.py', 'r', encoding='utf-8') as f:
        tree = ast.parse(f.read())
    
    # Find functions with cache decorators
    cached_functions = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Attribute):
                    if decorator.attr in ['cache_resource', 'cache_data']:
                        cached_functions.append((node.name, decorator.attr))
                elif isinstance(decorator, ast.Call):
                    if isinstance(decorator.func, ast.Attribute):
                        if decorator.func.attr in ['cache_resource', 'cache_data']:
                            cached_functions.append((node.name, decorator.func.attr))
    
    # Check for at least 2 cached functions (Sheets client and data)
    assert len(cached_functions) >= 2, \
        f"Should have at least 2 cached functions, found {len(cached_functions)}"
    
    # Check that get_google_sheets_client is cached
    client_cached = any(name == 'get_google_sheets_client' for name, _ in cached_functions)
    assert client_cached, "get_google_sheets_client should be cached"
    
    print(f"✓ Found {len(cached_functions)} cached functions")
    for name, cache_type in cached_functions:
        print(f"    {name} uses @st.{cache_type}")


def test_no_external_urls():
    """Test that external bot URLs are not exposed in portal."""
    print("\nTesting that external URLs are not exposed...")
    
    with open('secret_code_portal.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check that BOT_URLS dictionary is removed or not used in UI
    # The URLs might still exist in comments or variable definitions, but shouldn't be displayed
    lines = content.split('\n')
    
    # Look for st.markdown or st.write calls that might display URLs
    url_display_found = False
    for i, line in enumerate(lines):
        if 'bot_url' in line.lower() and ('st.markdown' in line or 'st.write' in line):
            # Check if this is in the old redirect section (should be replaced)
            if 'switch_page' not in '\n'.join(lines[max(0, i-10):min(len(lines), i+10)]):
                url_display_found = True
                break
    
    assert not url_display_found, \
        "Portal should not display external bot URLs in the UI"
    
    print("✓ External URLs are not exposed in portal UI")


def test_compact_button_styling():
    """Test that compact button styling is present."""
    print("\nTesting compact button styling...")
    
    with open('secret_code_portal.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for CSS styling for button
    assert 'stButton' in content or 'button[kind="secondary"]' in content, \
        "Should have button styling CSS"
    
    # Check for type="secondary" on refresh button
    assert 'type="secondary"' in content, \
        "Refresh button should use type='secondary'"
    
    print("✓ Compact button styling is present")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Multipage App Integration Tests")
    print("=" * 60)
    
    try:
        test_multipage_structure()
        test_authentication_guards()
        test_portal_credentials()
        test_caching_decorators()
        test_no_external_urls()
        test_compact_button_styling()
        
        print("\n" + "=" * 60)
        print("✓ All tests passed!")
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
