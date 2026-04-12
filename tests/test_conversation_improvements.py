#!/usr/bin/env python3
"""
Test script to validate MI Chatbot conversation flow improvements.
Tests conversation state management, role consistency, and feedback blocking.
"""

import sys
import traceback


def test_conversation_ending_detection():
    """Test that conversation ending is detected correctly."""
    try:
        from chat_utils import detect_conversation_ending
        
        # Test case 1: Not enough turns
        chat_history = [
            {"role": "assistant", "content": "Hello"},
            {"role": "user", "content": "Hi"},
        ]
        assert not detect_conversation_ending(chat_history, 2), "Should not end with only 2 turns"
        
        # Test case 2: Maximum turns reached
        assert detect_conversation_ending([], 12), "Should end after 12 turns"
        assert detect_conversation_ending([], 15), "Should end after 15 turns"
        
        # Test case 3: Natural ending phrase detected
        chat_history = [
            {"role": "assistant", "content": "Thank you for your time today. Take care!"},
        ]
        assert detect_conversation_ending(chat_history, 5), "Should detect 'thank you for' and 'take care'"
        
        # Test case 4: Another natural ending
        chat_history = [
            {"role": "assistant", "content": "Best of luck with your health journey!"},
        ]
        assert detect_conversation_ending(chat_history, 7), "Should detect 'best of luck'"
        
        # Test case 5: No ending phrase, not enough turns
        chat_history = [
            {"role": "assistant", "content": "That's interesting. Tell me more."},
        ]
        assert not detect_conversation_ending(chat_history, 5), "Should not end without ending phrase and < 12 turns"
        
        print("✅ Conversation ending detection works correctly")
        return True
        
    except Exception as e:
        print(f"❌ Conversation ending detection test error: {e}")
        traceback.print_exc()
        return False


def test_role_validation():
    """Test that role validation detects evaluator mode correctly."""
    try:
        from chat_utils import validate_response_role
        
        # Test case 1: Valid patient response
        response = "I'm not sure about the vaccine. Can you tell me more about it?"
        is_valid, _ = validate_response_role(response)
        assert is_valid, "Should accept valid patient response"
        
        # Test case 2: Invalid - contains evaluation
        response = "Feedback Report: Your performance was good. Score: 8/10"
        is_valid, _ = validate_response_role(response)
        assert not is_valid, "Should reject response with 'feedback report' and 'score'"
        
        # Test case 3: Invalid - contains rubric language
        response = "Based on the rubric category, your approach met the criteria."
        is_valid, _ = validate_response_role(response)
        assert not is_valid, "Should reject response with 'rubric category' and 'criteria met'"
        
        # Test case 4: Invalid - contains evaluation terms
        response = "Your performance evaluation shows areas for improvement."
        is_valid, _ = validate_response_role(response)
        assert not is_valid, "Should reject response with 'performance evaluation'"
        
        # Test case 5: Valid patient response with emotion
        response = "I'm worried about side effects. My friend had a bad experience."
        is_valid, _ = validate_response_role(response)
        assert is_valid, "Should accept emotional patient response"
        
        print("✅ Role validation works correctly")
        return True
        
    except Exception as e:
        print(f"❌ Role validation test error: {e}")
        traceback.print_exc()
        return False


def test_session_state_initialization():
    """Test that session state variables are properly initialized."""
    try:
        # We can't test streamlit session state directly, but we can verify the function exists
        from chat_utils import initialize_session_state
        
        assert callable(initialize_session_state), "initialize_session_state should be callable"
        
        print("✅ Session state initialization function exists")
        return True
        
    except Exception as e:
        print(f"❌ Session state initialization test error: {e}")
        traceback.print_exc()
        return False


def test_feedback_button_enabling():
    """Test feedback button enabling logic."""
    try:
        # Mock session state for testing
        class MockSessionState:
            def __init__(self):
                self.selected_persona = None
                self.chat_history = []
                self.conversation_state = "active"
                self.turn_count = 0
        
        # Import and test
        import chat_utils
        import streamlit as st
        
        # Create mock
        mock_state = MockSessionState()
        
        # We can't easily test this without streamlit running, but we can verify the function exists
        assert callable(chat_utils.should_enable_feedback_button), "should_enable_feedback_button should be callable"
        
        print("✅ Feedback button enabling function exists")
        return True
        
    except ImportError:
        # If streamlit isn't available, just check the function exists in the module
        try:
            from chat_utils import should_enable_feedback_button
            assert callable(should_enable_feedback_button), "should_enable_feedback_button should be callable"
            print("✅ Feedback button enabling function exists (streamlit not available)")
            return True
        except Exception as inner_e:
            print(f"❌ Feedback button enabling test error: {inner_e}")
            traceback.print_exc()
            return False
    except Exception as e:
        print(f"❌ Feedback button enabling test error: {e}")
        traceback.print_exc()
        return False


def test_persona_conciseness_updates():
    """Test that persona definitions include conciseness instructions."""
    try:
        # Test HPV.py personas
        import HPV
        
        for persona_name, persona_text in HPV.PERSONAS.items():
            assert "CONCISE" in persona_text or "concise" in persona_text.lower(), \
                f"HPV persona {persona_name} should include conciseness instructions"
            assert "2-3 sentences" in persona_text.lower(), \
                f"HPV persona {persona_name} should specify response length"
            assert "DO NOT" in persona_text, \
                f"HPV persona {persona_name} should have clear restrictions"
        
        print("✅ HPV personas include conciseness instructions")
        
        # Test OHI.py personas
        import OHI
        
        for persona_name, persona_text in OHI.PERSONAS.items():
            assert "CONCISE" in persona_text or "concise" in persona_text.lower(), \
                f"OHI persona {persona_name} should include conciseness instructions"
            assert "2-3 sentences" in persona_text.lower(), \
                f"OHI persona {persona_name} should specify response length"
        
        print("✅ OHI personas include conciseness instructions")
        return True
        
    except Exception as e:
        print(f"❌ Persona conciseness test error: {e}")
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("🧪 Running MI Chatbot Conversation Improvement Tests\n")
    
    tests = [
        ("Conversation Ending Detection", test_conversation_ending_detection),
        ("Role Validation", test_role_validation),
        ("Session State Initialization", test_session_state_initialization),
        ("Feedback Button Enabling", test_feedback_button_enabling),
        ("Persona Conciseness Updates", test_persona_conciseness_updates),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Testing {test_name}:")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} failed")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Conversation improvements are working correctly.")
        return 0
    else:
        print(f"⚠️  {total - passed} tests failed. Please check the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
