"""
Flow simulation test to demonstrate the multipage app navigation flow.

This simulates the complete user journey:
1. Student enters credentials at portal
2. Code is validated and marked as used
3. Session state is set with credentials
4. Internal navigation to bot page
5. Bot page validates session state
6. Student interacts with bot using centralized credentials
"""


def simulate_portal_entry():
    """Simulate student entering credentials at portal."""
    print("\n" + "="*60)
    print("STEP 1: Student visits secret_code_portal.py")
    print("="*60)
    
    # Simulated user inputs
    student_name = "John Doe"
    secret_code = "ABC123"

    print(f"\nStudent enters:")
    print(f"  - Name: {student_name}")
    print(f"  - Secret Code: {secret_code}")
    print(f"\nNo API key is requested. The LLM credential is operator-held.")

    return {
        "student_name": student_name,
        "secret_code": secret_code
    }


def simulate_code_validation(secret_code):
    """Simulate code validation against Google Sheets."""
    print("\n" + "="*60)
    print("STEP 2: Portal validates secret code")
    print("="*60)
    
    # Mock data from Google Sheets
    mock_sheet_data = [
        ["Table No", "Name", "Bot", "Secret", "Used"],
        ["1", "Student A", "OHI", "ABC123", "FALSE"],
        ["2", "Student B", "HPV", "DEF456", "FALSE"],
    ]
    
    print("\nSearching in Google Sheets database...")
    
    # Find the code
    for row in mock_sheet_data[1:]:  # Skip header
        if row[3] == secret_code:
            print(f"✓ Code found!")
            print(f"  - Assigned Name: {row[1]}")
            print(f"  - Bot Type: {row[2]}")
            print(f"  - Used Status: {row[4]}")
            
            if row[4].upper() == "FALSE":
                print(f"\n✓ Code is valid and unused")
                print(f"✓ Marking code as USED in Google Sheets...")
                return {
                    "success": True,
                    "bot": row[2],
                    "name": row[1]
                }
            else:
                print(f"\n✗ Code already used")
                return {"success": False, "message": "Code already used"}
    
    print(f"\n✗ Code not found")
    return {"success": False, "message": "Invalid code"}


def simulate_session_state_setup(credentials, validation_result):
    """Simulate setting up session state."""
    print("\n" + "="*60)
    print("STEP 3: Portal sets up session state")
    print("="*60)
    
    session_state = {
        "authenticated": True,
        "redirect_info": {
            "bot": validation_result["bot"],
            "name": validation_result["name"]
        },
        "student_name": credentials["student_name"]
    }
    
    print("\nSession state configured:")
    print(f"  ✓ authenticated: {session_state['authenticated']}")
    print(f"  ✓ redirect_info.bot: {session_state['redirect_info']['bot']}")
    print(f"  ✓ redirect_info.name: {session_state['redirect_info']['name']}")
    print(f"  ✓ student_name: {session_state['student_name']}")
    print(f"\n✓ No API key in session state, and no process-global env write")

    return session_state


def simulate_internal_navigation(bot_type):
    """Simulate internal navigation using st.switch_page."""
    print("\n" + "="*60)
    print("STEP 4: Portal navigates to bot page")
    print("="*60)
    
    page_path = f"pages/{bot_type}.py"
    
    print(f"\nUsing internal navigation:")
    print(f"  st.switch_page(\"{page_path}\")")
    print(f"\n✓ No external URLs exposed to user")
    print(f"✓ Navigation stays within same Streamlit app")
    print(f"✓ Session state preserved across pages")
    
    return page_path


def simulate_bot_page_guard(session_state, expected_bot):
    """Simulate authentication guard on bot page."""
    print("\n" + "="*60)
    print(f"STEP 5: {expected_bot} bot page validates access")
    print("="*60)
    
    print(f"\nAuthentication guard checks:")
    
    # Check 1: Authenticated
    if not session_state.get('authenticated', False):
        print(f"  ✗ Not authenticated - redirecting to portal")
        return False
    print(f"  ✓ User is authenticated")
    
    # Check 2: Correct bot
    redirect_info = session_state.get('redirect_info', {})
    if redirect_info.get('bot') != expected_bot:
        print(f"  ✗ Wrong bot (expected {expected_bot}, got {redirect_info.get('bot')})")
        print(f"  ✗ Redirecting to portal")
        return False
    print(f"  ✓ User authorized for {expected_bot} bot")
    
    # Check 3: Student name present. The LLM credential is no longer part of
    # session state, so it is not checked here.
    if 'student_name' not in session_state:
        print(f"  ✗ Missing student name - redirecting to portal")
        return False
    print(f"  ✓ Student name available in session state")
    
    print(f"\n✓ All checks passed - granting access to bot")
    return True


def simulate_bot_usage(session_state):
    """Simulate bot using centralized credentials."""
    print("\n" + "="*60)
    print("STEP 6: Bot uses centralized credentials")
    print("="*60)
    
    print(f"\nBot retrieves the student name from session state:")
    print(f"  student_name = st.session_state.student_name")

    print(f"\nThe LLM endpoint and credential come from the environment:")
    print(f"  settings = load_settings()   # MI_LLM_BASE_URL, MI_LLM_API_KEY")
    print(f"  client = make_client(settings)")

    print(f"\n✓ No API key input field shown to student")
    print(f"✓ No student name input field shown to student")
    print(f"✓ Student proceeds directly to conversation")

    print(f"\nBot functionality:")
    print(f"  - Uses one operator-held credential, not a per-student key")
    print(f"  - Uses student name for feedback report")
    print(f"  - Maintains secure session throughout conversation")


def main():
    """Run complete flow simulation."""
    print("\n" + "#"*60)
    print("#  MULTIPAGE APP FLOW SIMULATION")
    print("#"*60)
    print("\nThis demonstrates the complete user journey through")
    print("the production-ready multipage Streamlit app.")
    
    # Step 1: Portal entry
    credentials = simulate_portal_entry()
    
    # Step 2: Code validation
    validation_result = simulate_code_validation(credentials["secret_code"])
    
    if not validation_result["success"]:
        print(f"\n✗ FLOW STOPPED: {validation_result['message']}")
        return
    
    # Step 3: Session state setup
    session_state = simulate_session_state_setup(credentials, validation_result)
    
    # Step 4: Internal navigation
    bot_page = simulate_internal_navigation(validation_result["bot"])
    
    # Step 5: Bot page guard
    access_granted = simulate_bot_page_guard(session_state, validation_result["bot"])
    
    if not access_granted:
        print(f"\n✗ FLOW STOPPED: Access denied at bot page")
        return
    
    # Step 6: Bot usage
    simulate_bot_usage(session_state)
    
    # Summary
    print("\n" + "#"*60)
    print("#  FLOW COMPLETED SUCCESSFULLY")
    print("#"*60)
    print("\n✓ Student entered credentials once at portal")
    print("✓ Code validated and marked as used")
    print("✓ Internal navigation (no external URLs)")
    print("✓ Authentication guards protected bot access")
    print("✓ Centralized credentials used throughout")
    print("✓ No redirect loops or cross-domain issues")
    
    print("\n" + "="*60)
    print("Key Security & UX Improvements:")
    print("="*60)
    print("1. Single credential entry at portal")
    print("2. No external bot URLs exposed")
    print("3. Session-based authentication")
    print("4. Internal navigation only (st.switch_page)")
    print("5. Cached Google Sheets access")
    print("6. Compact, styled UI elements")


if __name__ == "__main__":
    main()
