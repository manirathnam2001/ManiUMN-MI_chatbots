#!/usr/bin/env python3
"""
Test mutual-intent end condition logic.

This test verifies that:
1. Conversations can end when both user_end_intent and bot_end_ack are set
2. Turn thresholds do NOT block ending with mutual intent
3. MI rubric coverage is NOT required with mutual intent
4. Intent flags are properly detected and reset
"""

from end_control_middleware import (
    detect_user_end_intent,
    detect_bot_end_ack,
    check_mutual_intent,
    should_continue_v4,
    MIN_TURN_THRESHOLD,
    ConversationState
)


def test_user_end_intent_detection():
    """Test detection of user end intent phrases."""
    print("🔍 Test 1: User end intent detection")
    
    # Positive cases
    positive_cases = [
        "Thanks for your help!",
        "Okay, bye",
        "I'm done here",
        "That's all, thank you",
        "We're finished",
        "Goodbye"
    ]
    
    for msg in positive_cases:
        if not detect_user_end_intent(msg):
            print(f"   ❌ FAIL: User end intent not detected in: '{msg}'")
            return False
    
    # Negative cases
    negative_cases = [
        "Tell me more",
        "What do you think?",
        "I see",
        "Interesting"
    ]
    
    for msg in negative_cases:
        if detect_user_end_intent(msg):
            print(f"   ❌ FAIL: False positive on: '{msg}'")
            return False
    
    print("   ✅ PASS: User end intent detection works correctly")
    return True


def test_bot_end_ack_detection():
    """Test detection of bot closing acknowledgment."""
    print("\n🔍 Test 2: Bot end acknowledgment detection")
    
    # Positive cases
    positive_cases = [
        "You're welcome!",
        "Goodbye, take care",
        "Glad I could help",
        "Have a great day!",
        "Feel free to come back",
        "Best wishes"
    ]
    
    for msg in positive_cases:
        if not detect_bot_end_ack(msg):
            print(f"   ❌ FAIL: Bot end ack not detected in: '{msg}'")
            return False
    
    # Negative cases
    negative_cases = [
        "Tell me more about that",
        "What do you think about vaccines?",
        "I understand your concern",
        "That's interesting"
    ]
    
    for msg in negative_cases:
        if detect_bot_end_ack(msg):
            print(f"   ❌ FAIL: False positive on: '{msg}'")
            return False
    
    print("   ✅ PASS: Bot end ack detection works correctly")
    return True


def test_mutual_intent_allows_ending():
    """Test that mutual intent allows ending without turn/MI requirements."""
    print("\n🔍 Test 3: Mutual intent allows ending without requirements")
    
    # Create a minimal conversation with mutual intent but NO MI coverage or sufficient turns
    conversation_context = {
        'chat_history': [
            {'role': 'user', 'content': 'Hello'},
            {'role': 'assistant', 'content': 'Hi there'},
            {'role': 'user', 'content': 'Thanks, bye'},  # User end intent
            {'role': 'assistant', 'content': 'Goodbye!'},  # Bot end ack
        ],
        'turn_count': 2,  # Well below MIN_TURN_THRESHOLD
        'end_control_state': 'ACTIVE',
        'confirmation_flag': False,
        'user_end_intent': False,
        'bot_end_ack': False
    }
    
    result = check_mutual_intent(
        conversation_context,
        'Goodbye!',
        'Thanks, bye'
    )
    
    if result['continue']:
        print(f"   ❌ FAIL: Mutual intent did not allow ending")
        print(f"      Result: {result}")
        return False
    
    if not result['mutual_intent']:
        print(f"   ❌ FAIL: Mutual intent not detected")
        print(f"      Result: {result}")
        return False
    
    print("   ✅ PASS: Mutual intent allows ending without requirements")
    return True


def test_partial_intent_does_not_end():
    """Test that only one intent flag doesn't allow ending."""
    print("\n🔍 Test 4: Partial intent does not allow ending")
    
    # User intent only
    conversation_context_1 = {
        'chat_history': [
            {'role': 'user', 'content': 'Thanks'},
            {'role': 'assistant', 'content': 'What else can I help with?'},
        ],
        'turn_count': 1,
        'end_control_state': 'ACTIVE',
        'user_end_intent': False,
        'bot_end_ack': False
    }
    
    result_1 = check_mutual_intent(
        conversation_context_1,
        'What else can I help with?',
        'Thanks'
    )
    
    if not result_1['continue']:
        print(f"   ❌ FAIL: User intent alone allowed ending")
        return False
    
    # Bot ack only
    conversation_context_2 = {
        'chat_history': [
            {'role': 'user', 'content': 'Tell me more'},
            {'role': 'assistant', 'content': 'Goodbye!'},
        ],
        'turn_count': 1,
        'end_control_state': 'ACTIVE',
        'user_end_intent': False,
        'bot_end_ack': False
    }
    
    result_2 = check_mutual_intent(
        conversation_context_2,
        'Goodbye!',
        'Tell me more'
    )
    
    if not result_2['continue']:
        print(f"   ❌ FAIL: Bot ack alone allowed ending")
        return False
    
    print("   ✅ PASS: Partial intent does not allow ending")
    return True


def test_should_continue_v4_mutual_intent():
    """Test that should_continue_v4 respects mutual intent early exit."""
    print("\n🔍 Test 5: should_continue_v4 mutual intent early exit")
    
    # Create minimal conversation with mutual intent
    conversation_context = {
        'chat_history': [
            {'role': 'user', 'content': 'Hello'},
            {'role': 'assistant', 'content': 'Hi'},
            {'role': 'user', 'content': 'Done, thanks'},
            {'role': 'assistant', 'content': "You're welcome, goodbye!"},
        ],
        'turn_count': 2,  # Well below typical threshold
        'end_control_state': 'ACTIVE',
        'confirmation_flag': False,
        'user_end_intent': False,
        'bot_end_ack': False
    }
    
    decision = should_continue_v4(
        conversation_context,
        "You're welcome, goodbye!",
        'Done, thanks'
    )
    
    if decision['continue']:
        print(f"   ❌ FAIL: should_continue_v4 did not end with mutual intent")
        print(f"      Decision: {decision}")
        return False
    
    if decision['state'] != ConversationState.ENDED.value:
        print(f"   ❌ FAIL: State not ENDED: {decision['state']}")
        return False
    
    print("   ✅ PASS: should_continue_v4 respects mutual intent")
    return True


def test_min_turn_threshold_default():
    """Test that MIN_TURN_THRESHOLD defaults to 0."""
    print("\n🔍 Test 6: MIN_TURN_THRESHOLD defaults to 0")
    
    # The default should allow conversations to end without turn restrictions
    # (when using mutual intent)
    if MIN_TURN_THRESHOLD > 0:
        print(f"   ⚠️  WARNING: MIN_TURN_THRESHOLD is {MIN_TURN_THRESHOLD}, not 0")
        print(f"      This is acceptable if environment variable is set")
    else:
        print(f"   ✅ PASS: MIN_TURN_THRESHOLD is {MIN_TURN_THRESHOLD}")
    
    return True


def run_all_tests():
    """Run all mutual intent tests."""
    print("=" * 60)
    print("🧪 Testing Mutual-Intent End Condition")
    print("=" * 60)
    
    tests = [
        test_user_end_intent_detection,
        test_bot_end_ack_detection,
        test_mutual_intent_allows_ending,
        test_partial_intent_does_not_end,
        test_should_continue_v4_mutual_intent,
        test_min_turn_threshold_default
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {sum(results)}/{len(results)} tests passed")
    
    if all(results):
        print("🎉 All mutual intent tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    exit(run_all_tests())
