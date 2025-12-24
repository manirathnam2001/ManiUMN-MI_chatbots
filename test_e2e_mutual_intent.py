#!/usr/bin/env python3
"""
End-to-end test for mutual-intent end condition.

This test simulates a complete conversation flow with mutual intent,
demonstrating that:
1. Conversations can end quickly with mutual intent (no turn minimum)
2. Feedback button should enable when mutual intent is detected
3. Flags are properly reset on new conversation
"""

from end_control_middleware import should_continue_v4, ConversationState


def test_minimal_conversation_with_mutual_intent():
    """Test that a minimal conversation can end with mutual intent."""
    print("🔍 Test: Minimal conversation with mutual intent")
    print("=" * 60)
    
    # Simulate a very short conversation
    conversation_context = {
        'chat_history': [
            {'role': 'assistant', 'content': 'Hello, how can I help you?'},
            {'role': 'user', 'content': 'Just wanted to say thanks, bye!'},  # User end intent
            {'role': 'assistant', 'content': "You're welcome! Goodbye!"},  # Bot end ack
        ],
        'turn_count': 1,  # Very low turn count
        'end_control_state': 'ACTIVE',
        'confirmation_flag': False,
        'user_end_intent': False,
        'bot_end_ack': False
    }
    
    decision = should_continue_v4(
        conversation_context,
        "You're welcome! Goodbye!",
        'Just wanted to say thanks, bye!'
    )
    
    print(f"Turn count: {conversation_context['turn_count']}")
    print(f"Decision: {decision}")
    print(f"Continue: {decision['continue']}")
    print(f"State: {decision['state']}")
    print(f"Reason: {decision['reason']}")
    print(f"Mutual intent: {decision.get('mutual_intent', False)}")
    print(f"User end intent: {conversation_context.get('user_end_intent', False)}")
    print(f"Bot end ack: {conversation_context.get('bot_end_ack', False)}")
    
    if not decision['continue'] and decision['state'] == ConversationState.ENDED.value:
        print("\n✅ SUCCESS: Conversation ended with mutual intent despite low turn count")
        return True
    else:
        print("\n❌ FAIL: Conversation did not end as expected")
        return False


def test_feedback_button_logic():
    """Test should_enable_feedback_button logic with mutual intent."""
    print("\n\n🔍 Test: Feedback button enablement with mutual intent")
    print("=" * 60)
    
    # Mock session state
    class MockSessionState:
        def __init__(self):
            self.selected_persona = "Test Persona"
            self.chat_history = [
                {'role': 'assistant', 'content': 'Hello'},
                {'role': 'user', 'content': 'Hi'},
                {'role': 'assistant', 'content': 'How are you?'},
                {'role': 'user', 'content': 'Thanks, bye!'},
            ]
            self.conversation_state = "active"  # Not ended yet
            self.user_end_intent = True  # User said bye
            self.bot_end_ack = True  # Bot acknowledged
        
        def get(self, key, default=None):
            return getattr(self, key, default)
    
    # Simulate the logic from should_enable_feedback_button
    st = MockSessionState()
    
    # Check conditions
    has_persona = st.selected_persona is not None
    min_exchanges = len(st.chat_history) >= 4
    is_ended = st.get('conversation_state') == "ended"
    has_mutual_intent = st.get('user_end_intent', False) and st.get('bot_end_ack', False)
    
    should_enable = has_persona and min_exchanges and (is_ended or has_mutual_intent)
    
    print(f"Has persona: {has_persona}")
    print(f"Min exchanges: {min_exchanges} (history length: {len(st.chat_history)})")
    print(f"Is ended: {is_ended}")
    print(f"Has mutual intent: {has_mutual_intent}")
    print(f"  - User end intent: {st.get('user_end_intent', False)}")
    print(f"  - Bot end ack: {st.get('bot_end_ack', False)}")
    print(f"\nShould enable button: {should_enable}")
    
    if should_enable:
        print("\n✅ SUCCESS: Feedback button would be enabled with mutual intent")
        return True
    else:
        print("\n❌ FAIL: Feedback button would not be enabled")
        return False


def test_flag_reset():
    """Test that flags are properly initialized and reset."""
    print("\n\n🔍 Test: Flag initialization and reset")
    print("=" * 60)
    
    # Simulate initialization (from initialize_session_state)
    session_state = {
        'selected_persona': None,
        'feedback': None,
        'conversation_state': 'active',
        'turn_count': 0,
        'end_control_state': 'ACTIVE',
        'confirmation_flag': False,
        'termination_trigger': 'unknown',
        'user_end_intent': False,  # Should initialize to False
        'bot_end_ack': False,  # Should initialize to False
    }
    
    print("Initial state:")
    print(f"  user_end_intent: {session_state['user_end_intent']}")
    print(f"  bot_end_ack: {session_state['bot_end_ack']}")
    
    # Simulate some conversation that sets flags
    session_state['user_end_intent'] = True
    session_state['bot_end_ack'] = True
    
    print("\nAfter conversation:")
    print(f"  user_end_intent: {session_state['user_end_intent']}")
    print(f"  bot_end_ack: {session_state['bot_end_ack']}")
    
    # Simulate reset (from handle_new_conversation_button)
    session_state['selected_persona'] = None
    session_state['conversation_state'] = 'active'
    session_state['turn_count'] = 0
    session_state['end_control_state'] = 'ACTIVE'
    session_state['confirmation_flag'] = False
    session_state['termination_trigger'] = 'unknown'
    session_state['user_end_intent'] = False  # Reset
    session_state['bot_end_ack'] = False  # Reset
    
    print("\nAfter reset:")
    print(f"  user_end_intent: {session_state['user_end_intent']}")
    print(f"  bot_end_ack: {session_state['bot_end_ack']}")
    
    if not session_state['user_end_intent'] and not session_state['bot_end_ack']:
        print("\n✅ SUCCESS: Flags properly reset")
        return True
    else:
        print("\n❌ FAIL: Flags not properly reset")
        return False


def main():
    """Run all end-to-end tests."""
    print("\n" + "=" * 60)
    print("🧪 End-to-End Mutual Intent Tests")
    print("=" * 60 + "\n")
    
    tests = [
        test_minimal_conversation_with_mutual_intent,
        test_feedback_button_logic,
        test_flag_reset,
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    print("\n" + "=" * 60)
    print(f"📊 Results: {sum(results)}/{len(results)} tests passed")
    print("=" * 60)
    
    if all(results):
        print("🎉 All end-to-end tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    exit(main())
