"""
Test semantic-based conversation ending logic.

This test verifies that the conversation ending system:
1. Does NOT end based on turn count alone
2. Requires doctor closure signals AND patient satisfaction
3. Requires mutual confirmation before ending
"""

from end_control_middleware import (
    can_suggest_ending,
    detect_patient_satisfaction,
    detect_doctor_closure_signal,
    detect_patient_end_confirmation,
    MIN_TURN_THRESHOLD
)

def test_turn_count_alone_does_not_trigger_ending():
    """Test that reaching MIN_TURN_THRESHOLD alone does not trigger ending."""
    print("🔍 Test 1: Turn count alone should NOT trigger ending")
    
    # Create conversation with minimum turns but no semantic signals
    conversation_state = {
        'chat_history': [
            {'role': 'user', 'content': 'Hello'},
            {'role': 'assistant', 'content': 'Hi there'},
            {'role': 'user', 'content': 'Tell me about vaccines'},
            {'role': 'assistant', 'content': 'Vaccines are important'},
            {'role': 'user', 'content': 'I see'},
            {'role': 'assistant', 'content': 'Any questions?'},
            {'role': 'user', 'content': 'Not really'},
            {'role': 'assistant', 'content': 'Okay'},
            {'role': 'user', 'content': 'Thanks'},
            {'role': 'assistant', 'content': 'You are welcome. What do you think about getting vaccinated?'},
            {'role': 'user', 'content': 'I do not know'},
            {'role': 'assistant', 'content': 'It sounds like you have some uncertainty'},
        ],
        'turn_count': MIN_TURN_THRESHOLD  # Exactly at threshold
    }
    
    result = can_suggest_ending(conversation_state)
    
    if result:
        print("   ❌ FAIL: Ending suggested based on turn count alone!")
        return False
    else:
        print("   ✅ PASS: Turn count alone does not trigger ending")
        return True


def test_semantic_signals_required():
    """Test that both doctor closure and patient satisfaction are required."""
    print("\n🔍 Test 2: Semantic signals required for ending")
    
    # Test with satisfaction but no doctor closure
    conversation_state_1 = {
        'chat_history': [
            {'role': 'user', 'content': 'Tell me about vaccines'},
            {'role': 'assistant', 'content': 'That helps, thank you. I feel better about this'},
            {'role': 'user', 'content': 'Great'},
            {'role': 'assistant', 'content': 'That makes sense'},
            {'role': 'user', 'content': 'Good'},
            {'role': 'assistant', 'content': 'I appreciate the information'},
            {'role': 'user', 'content': 'Sure'},
            {'role': 'assistant', 'content': 'That answers my questions'},
            {'role': 'user', 'content': 'Okay'},  # No closure signal
            {'role': 'assistant', 'content': 'I understand better now'},
        ],
        'turn_count': MIN_TURN_THRESHOLD
    }
    
    result_1 = can_suggest_ending(conversation_state_1)
    
    if result_1:
        print("   ❌ FAIL: Ending suggested without doctor closure signal")
        return False
    
    # Test with doctor closure but no patient satisfaction
    conversation_state_2 = {
        'chat_history': [
            {'role': 'user', 'content': 'Tell me about vaccines'},
            {'role': 'assistant', 'content': 'Okay'},
            {'role': 'user', 'content': 'I see'},
            {'role': 'assistant', 'content': 'Hmm'},
            {'role': 'user', 'content': 'Right'},
            {'role': 'assistant', 'content': 'Sure'},
            {'role': 'user', 'content': 'Any other questions?'},  # Closure signal
            {'role': 'assistant', 'content': 'Maybe'},  # No satisfaction
            {'role': 'user', 'content': 'Okay'},
            {'role': 'assistant', 'content': 'I guess'},
        ],
        'turn_count': MIN_TURN_THRESHOLD
    }
    
    result_2 = can_suggest_ending(conversation_state_2)
    
    if result_2:
        print("   ❌ FAIL: Ending suggested without patient satisfaction")
        return False
    
    print("   ✅ PASS: Both semantic signals are required")
    return True


def test_mutual_signals_allow_ending():
    """Test that BOTH doctor closure AND patient satisfaction allow ending."""
    print("\n🔍 Test 3: Mutual signals allow ending")
    
    # Note: In this system, the ASSISTANT (bot/patient) demonstrates MI techniques in responses
    # The USER is the student doctor practicing
    conversation_state = {
        'chat_history': [
            {'role': 'user', 'content': 'Hello, tell me about your concerns'},
            {'role': 'assistant', 'content': 'What brings you here today?'},  # Open-ended
            {'role': 'user', 'content': 'I want to discuss vaccines'},
            {'role': 'assistant', 'content': 'It sounds like you want to explore vaccination. That helps, thank you'},  # Reflection + satisfaction
            {'role': 'user', 'content': 'Yes, exactly'},
            {'role': 'assistant', 'content': 'You can decide what works best for you. I feel better now'},  # Autonomy + satisfaction
            {'role': 'user', 'content': 'That is good'},
            {'role': 'assistant', 'content': 'To sum up, we talked about vaccines. I appreciate your help'},  # Summary + satisfaction
            {'role': 'user', 'content': 'Any other questions?'},  # Doctor closure - MUST be last user message
            {'role': 'assistant', 'content': 'No, I think that answers everything. Thank you!'},  # Confirmation
        ],
        'turn_count': MIN_TURN_THRESHOLD
    }
    
    result = can_suggest_ending(conversation_state)
    
    if not result:
        print("   ❌ FAIL: Ending not suggested despite mutual signals")
        # Debug
        from end_control_middleware import check_mi_coverage
        coverage = check_mi_coverage(conversation_state['chat_history'])
        print(f"      Debug - MI Coverage: {coverage}")
        return False
    else:
        print("   ✅ PASS: Mutual signals allow ending")
        return True


def test_patient_satisfaction_detection():
    """Test patient satisfaction detection."""
    print("\n🔍 Test 4: Patient satisfaction detection")
    
    # Positive cases
    satisfied_messages = [
        "That helps, thank you",
        "I feel better about this",
        "That makes sense",
        "Good to know",
        "I appreciate the information",
        "That answers my questions"
    ]
    
    chat_history = [{'role': 'assistant', 'content': msg} for msg in satisfied_messages]
    
    if not detect_patient_satisfaction(chat_history):
        print("   ❌ FAIL: Patient satisfaction not detected")
        return False
    
    # Negative cases
    unsatisfied_messages = [
        "Okay",
        "I see",
        "Hmm",
        "Maybe",
        "I guess"
    ]
    
    chat_history = [{'role': 'assistant', 'content': msg} for msg in unsatisfied_messages]
    
    if detect_patient_satisfaction(chat_history):
        print("   ❌ FAIL: False positive on patient satisfaction")
        return False
    
    print("   ✅ PASS: Patient satisfaction detection works correctly")
    return True


def test_doctor_closure_detection():
    """Test doctor closure signal detection."""
    print("\n🔍 Test 5: Doctor closure signal detection")
    
    # Positive cases
    closure_messages = [
        "Any other questions?",
        "Is there anything else?",
        "Glad I could help",
        "Feel free to come back",
        "Let me know if you have any concerns"
    ]
    
    for msg in closure_messages:
        if not detect_doctor_closure_signal(msg):
            print(f"   ❌ FAIL: Closure signal not detected in: '{msg}'")
            return False
    
    # Negative cases
    non_closure_messages = [
        "Tell me more",
        "That is interesting",
        "I see",
        "What do you think?"
    ]
    
    for msg in non_closure_messages:
        if detect_doctor_closure_signal(msg):
            print(f"   ❌ FAIL: False positive on: '{msg}'")
            return False
    
    print("   ✅ PASS: Doctor closure detection works correctly")
    return True


def test_minimum_floor_enforced():
    """Test that minimum turn count is still enforced as a floor."""
    print("\n🔍 Test 6: Minimum turn floor still enforced")
    
    # Even with all semantic signals, should not end before minimum turns
    conversation_state = {
        'chat_history': [
            {'role': 'user', 'content': 'Any other questions?'},  # Closure
            {'role': 'assistant', 'content': 'No, that helps, thank you'},  # Satisfaction + confirmation
        ],
        'turn_count': MIN_TURN_THRESHOLD - 1  # Below threshold
    }
    
    result = can_suggest_ending(conversation_state)
    
    if result:
        print("   ❌ FAIL: Ending suggested before minimum turns")
        return False
    else:
        print("   ✅ PASS: Minimum turn floor enforced")
        return True


def run_all_tests():
    """Run all semantic ending tests."""
    print("=" * 60)
    print("🧪 Testing Semantic-Based Conversation Ending")
    print("=" * 60)
    
    tests = [
        test_turn_count_alone_does_not_trigger_ending,
        test_semantic_signals_required,
        test_mutual_signals_allow_ending,
        test_patient_satisfaction_detection,
        test_doctor_closure_detection,
        test_minimum_floor_enforced
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {sum(results)}/{len(results)} tests passed")
    
    if all(results):
        print("🎉 All semantic ending tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    exit(run_all_tests())
