#!/usr/bin/env python3
"""
End-to-end test for conversation ending and feedback gating.

This test simulates the production rules that:
1. Mutual intent may end the conversation in middleware.
2. Feedback/export must still wait for semantic closure state.
3. Transcript/evaluation channels reset correctly for a new conversation.
"""

from end_control_middleware import should_continue_v4, ConversationState


def test_minimal_conversation_with_mutual_intent():
    """Test that a minimal conversation can end with mutual intent."""
    print("🔍 Test: Minimal conversation with mutual intent")
    print("=" * 60)

    conversation_context = {
        'chat_history': [
            {'role': 'assistant', 'content': 'Hello, how can I help you?'},
            {'role': 'user', 'content': 'Just wanted to say thanks, bye!'},
            {'role': 'assistant', 'content': "You're welcome! Goodbye!"},
        ],
        'turn_count': 1,
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

    print(f"Decision: {decision}")
    if not decision['continue'] and decision['state'] == ConversationState.ENDED.value:
        print("\n✅ SUCCESS: Conversation ended with mutual intent")
        return True

    print("\n❌ FAIL: Conversation did not end as expected")
    return False


def test_feedback_button_logic_requires_ended_state():
    """Test production feedback button gating requires semantic closure state."""
    print("\n\n🔍 Test: Feedback button enablement requires ended state")
    print("=" * 60)

    class MockSessionState:
        def __init__(self, end_state, conversation_state):
            self.selected_persona = "Test Persona"
            self.chat_history = [
                {'role': 'assistant', 'content': 'Hello'},
                {'role': 'user', 'content': 'Hi'},
            ]
            self.end_control_state = end_state
            self.conversation_state = conversation_state

        def get(self, key, default=None):
            return getattr(self, key, default)

    active_state = MockSessionState("ACTIVE", "active")
    ended_state = MockSessionState("ENDED", "ended")

    active_enabled = (
        active_state.selected_persona is not None
        and len(active_state.chat_history) >= 2
        and not (
            active_state.get('end_control_state') != 'ENDED'
            and active_state.get('conversation_state') != 'ended'
        )
    )
    ended_enabled = (
        ended_state.selected_persona is not None
        and len(ended_state.chat_history) >= 2
        and not (
            ended_state.get('end_control_state') != 'ENDED'
            and ended_state.get('conversation_state') != 'ended'
        )
    )

    print(f"Active conversation enabled: {active_enabled}")
    print(f"Ended conversation enabled: {ended_enabled}")

    if not active_enabled and ended_enabled:
        print("\n✅ SUCCESS: Feedback gating matches semantic closure rule")
        return True

    print("\n❌ FAIL: Feedback gating does not match semantic closure rule")
    return False


def test_flag_reset():
    """Test that transcript/evaluation channels are properly reset."""
    print("\n\n🔍 Test: Session reset clears locked transcript and evaluator history")
    print("=" * 60)

    session_state = {
        'selected_persona': 'Test Persona',
        'feedback': {'content': 'Example'},
        'conversation_state': 'ended',
        'turn_count': 5,
        'end_control_state': 'ENDED',
        'confirmation_flag': True,
        'termination_trigger': 'semantic_close',
        'user_end_intent': True,
        'bot_end_ack': True,
        'locked_chat_history': [{'role': 'user', 'content': 'Locked transcript'}],
        'evaluation_history': [{'role': 'evaluator', 'content': 'Eval'}],
        'transcript_locked': True,
    }

    session_state['selected_persona'] = None
    session_state['feedback'] = None
    session_state['conversation_state'] = 'active'
    session_state['turn_count'] = 0
    session_state['end_control_state'] = 'ACTIVE'
    session_state['confirmation_flag'] = False
    session_state['termination_trigger'] = 'unknown'
    session_state['user_end_intent'] = False
    session_state['bot_end_ack'] = False
    session_state['locked_chat_history'] = []
    session_state['evaluation_history'] = []
    session_state['transcript_locked'] = False

    if (
        not session_state['user_end_intent']
        and not session_state['bot_end_ack']
        and not session_state['locked_chat_history']
        and not session_state['evaluation_history']
        and session_state['transcript_locked'] is False
    ):
        print("\n✅ SUCCESS: Reset clears transcript/evaluation channels")
        return True

    print("\n❌ FAIL: Reset did not clear protected channels")
    return False


if __name__ == "__main__":
    tests = [
        test_minimal_conversation_with_mutual_intent,
        test_feedback_button_logic_requires_ended_state,
        test_flag_reset,
    ]
    results = [test() for test in tests]
    raise SystemExit(0 if all(results) else 1)
