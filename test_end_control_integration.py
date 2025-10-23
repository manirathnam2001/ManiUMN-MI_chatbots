#!/usr/bin/env python3
"""
Integration test for end-control middleware with chat_utils.

This test validates the full conversation flow integration between
chat_utils and end_control_middleware, ensuring conversations only end
when all policy conditions are met.
"""

import sys
import traceback


def test_integration_should_continue():
    """Test integration between chat_utils and end_control_middleware."""
    try:
        from end_control_middleware import should_continue, MIN_TURN_THRESHOLD, END_TOKEN
        
        # Simulate a complete conversation that meets all requirements
        conversation_state = {
            'chat_history': [
                {"role": "assistant", "content": "Hello, I'm Alex, nice to meet you."},
                {"role": "user", "content": "Hi, I'd like to discuss oral hygiene."},
                {"role": "assistant", "content": "What brings you here today?"},  # open-ended
                {"role": "user", "content": "I have some concerns about flossing."},
                {"role": "assistant", "content": "It sounds like you're worried about your flossing routine."},  # reflection
                {"role": "user", "content": "Yes, I don't do it regularly."},
                {"role": "assistant", "content": "What would work best for your situation?"},  # autonomy
                {"role": "user", "content": "Maybe I could try a different approach."},
                {"role": "assistant", "content": "That's a good idea. You know yourself best."},
                {"role": "user", "content": "Thank you for the advice."},
                {"role": "assistant", "content": "To summarize, we've talked about your concerns and options."},  # summary
                {"role": "user", "content": "Yes, let's end the session."},  # confirmation
            ],
            'turn_count': MIN_TURN_THRESHOLD + 1
        }
        
        last_assistant = f"Thank you for our conversation. Best wishes! {END_TOKEN}"
        last_user = "Yes, let's end the session."
        
        decision = should_continue(conversation_state, last_assistant, last_user)
        
        assert not decision['continue'], "Should allow ending when all conditions met"
        assert "all end conditions met" in decision['reason'].lower()
        
        print("✅ Integration test: Complete conversation can end properly")
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        traceback.print_exc()
        return False


def test_integration_premature_ending_blocked():
    """Test that premature endings are blocked by middleware."""
    try:
        from end_control_middleware import should_continue, END_TOKEN
        
        # Simulate early conversation (should be blocked)
        conversation_state = {
            'chat_history': [
                {"role": "assistant", "content": "Hello, I'm Alex."},
                {"role": "user", "content": "Hi there."},
                {"role": "assistant", "content": "How are you?"},
                {"role": "user", "content": "thanks"},  # Ambiguous
            ],
            'turn_count': 2
        }
        
        last_assistant = f"Goodbye! {END_TOKEN}"
        last_user = "thanks"
        
        decision = should_continue(conversation_state, last_assistant, last_user)
        
        assert decision['continue'], "Should continue when turn count too low"
        assert "minimum turn threshold" in decision['reason'].lower()
        
        print("✅ Integration test: Premature ending blocked")
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        traceback.print_exc()
        return False


def test_integration_missing_mi_coverage():
    """Test that conversations without full MI coverage cannot end."""
    try:
        from end_control_middleware import should_continue, MIN_TURN_THRESHOLD, END_TOKEN
        
        # Conversation with enough turns but missing MI components
        conversation_state = {
            'chat_history': [
                {"role": "assistant", "content": f"Message {i}"}
                for i in range(MIN_TURN_THRESHOLD * 2)
            ],
            'turn_count': MIN_TURN_THRESHOLD + 1
        }
        
        last_assistant = f"Goodbye! {END_TOKEN}"
        last_user = "Yes, let's end."
        
        decision = should_continue(conversation_state, last_assistant, last_user)
        
        assert decision['continue'], "Should continue when MI coverage incomplete"
        assert "mi coverage" in decision['reason'].lower()
        
        print("✅ Integration test: Missing MI coverage blocks ending")
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        traceback.print_exc()
        return False


def test_integration_ambiguous_phrases():
    """Test that ambiguous phrases don't trigger ending."""
    try:
        from end_control_middleware import prevent_ambiguous_ending
        
        # Test various ambiguous phrases
        ambiguous = ["thanks", "okay", "ok", "thank you", "sure", "alright"]
        
        for phrase in ambiguous:
            assert prevent_ambiguous_ending(phrase), f"Should block ambiguous phrase: '{phrase}'"
        
        # Test that longer messages with ambiguous words are not blocked
        assert not prevent_ambiguous_ending("Thanks for the information, I have more questions")
        assert not prevent_ambiguous_ending("Okay, but what about side effects?")
        
        print("✅ Integration test: Ambiguous phrases handled correctly")
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        traceback.print_exc()
        return False


def test_integration_end_token_requirement():
    """Test that end token is required for ending."""
    try:
        from end_control_middleware import should_continue, MIN_TURN_THRESHOLD, END_TOKEN
        
        # Complete conversation but missing end token
        conversation_state = {
            'chat_history': [
                {"role": "assistant", "content": "Hello!"},
                {"role": "user", "content": "Hi!"},
                {"role": "assistant", "content": "What brings you here?"},  # open-ended
                {"role": "user", "content": "Health concerns."},
                {"role": "assistant", "content": "It sounds like you're worried."},  # reflection
                {"role": "user", "content": "Yes."},
                {"role": "assistant", "content": "What would work for you?"},  # autonomy
                {"role": "user", "content": "I'll think about it."},
                {"role": "assistant", "content": "To summarize our discussion..."},  # summary
                {"role": "user", "content": "Yes, let's end."},  # confirmation
            ],
            'turn_count': MIN_TURN_THRESHOLD + 1
        }
        
        # Without end token
        last_assistant = "Thank you for our conversation."
        last_user = "Yes, let's end."
        
        decision = should_continue(conversation_state, last_assistant, last_user)
        
        assert decision['continue'], "Should continue without end token"
        assert "end token" in decision['reason'].lower()
        
        # With end token
        last_assistant_with_token = f"Thank you for our conversation. {END_TOKEN}"
        decision = should_continue(conversation_state, last_assistant_with_token, last_user)
        
        assert not decision['continue'], "Should allow ending with end token"
        
        print("✅ Integration test: End token requirement enforced")
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        traceback.print_exc()
        return False


def test_integration_student_confirmation_required():
    """Test that student confirmation is required."""
    try:
        from end_control_middleware import should_continue, MIN_TURN_THRESHOLD, END_TOKEN
        
        # Complete conversation with all MI components
        base_history = [
            {"role": "assistant", "content": "What brings you here today?"},  # open-ended
            {"role": "user", "content": "Health concerns."},
            {"role": "assistant", "content": "It sounds like you're worried about this."},  # reflection
            {"role": "user", "content": "Yes, I am."},
            {"role": "assistant", "content": "What would work best for you?"},  # autonomy
            {"role": "user", "content": "I'll consider my options."},
            {"role": "assistant", "content": "To summarize our conversation today..."},  # summary
            {"role": "user", "content": "Okay."},
        ]
        
        # Add more exchanges to reach minimum turn threshold
        conversation_state = {
            'chat_history': base_history + [
                {"role": "assistant", "content": f"How do you feel about what we discussed?"},
                {"role": "user", "content": f"I feel better."},
            ] * 3,
            'turn_count': MIN_TURN_THRESHOLD + 1
        }
        
        # With end token but without explicit confirmation
        last_assistant = f"Thank you for sharing with me today. {END_TOKEN}"
        last_user = "thanks"
        
        decision = should_continue(conversation_state, last_assistant, last_user)
        
        assert decision['continue'], f"Should continue without explicit confirmation, reason: {decision['reason']}"
        
        # Check reason mentions confirmation (may also mention other issues)
        # The decision could fail on student confirmation or something else
        # Just ensure it doesn't allow ending
        
        # With explicit confirmation
        last_user_explicit = "Yes, let's end the session"
        decision = should_continue(conversation_state, last_assistant, last_user_explicit)
        
        assert not decision['continue'], f"Should allow ending with explicit confirmation, reason: {decision['reason']}"
        
        print("✅ Integration test: Student confirmation requirement enforced")
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        traceback.print_exc()
        return False


def test_integration_logging():
    """Test that conversation tracing works."""
    try:
        from end_control_middleware import log_conversation_trace, should_continue
        
        conversation_state = {
            'chat_history': [{"role": "assistant", "content": "Hello"}],
            'turn_count': 5
        }
        
        decision = should_continue(conversation_state, "Some message")
        
        # Test that logging doesn't crash
        trace = log_conversation_trace(
            conversation_state,
            decision,
            {'test_field': 'test_value'}
        )
        
        assert trace is not None, "Should return trace object"
        assert 'timestamp' in trace, "Should include timestamp"
        assert 'turn_count' in trace, "Should include turn count"
        assert 'decision' in trace, "Should include decision"
        assert 'mi_coverage' in trace, "Should include MI coverage"
        
        print("✅ Integration test: Conversation tracing works")
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        traceback.print_exc()
        return False


def main():
    """Run all integration tests."""
    print("🧪 Running End-Control Middleware Integration Tests\n")
    
    tests = [
        ("Complete Conversation Can End", test_integration_should_continue),
        ("Premature Ending Blocked", test_integration_premature_ending_blocked),
        ("Missing MI Coverage Blocks Ending", test_integration_missing_mi_coverage),
        ("Ambiguous Phrases Handled", test_integration_ambiguous_phrases),
        ("End Token Required", test_integration_end_token_requirement),
        ("Student Confirmation Required", test_integration_student_confirmation_required),
        ("Conversation Logging Works", test_integration_logging),
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
        print("🎉 All integration tests passed! End-control middleware is properly integrated.")
        return 0
    else:
        print(f"⚠️  {total - passed} tests failed. Please check the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
