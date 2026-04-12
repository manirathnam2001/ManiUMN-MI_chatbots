#!/usr/bin/env python3
"""
Test suite for end-control middleware.

This tests the hardened conversation ending logic to ensure:
- Minimum turn threshold is enforced
- MI coverage requirements are checked
- Student confirmation is required
- End token is detected
- Ambiguous phrases don't trigger premature ending
"""

import sys
import traceback
from end_control_middleware import (
    detect_mi_component,
    check_mi_coverage,
    detect_student_confirmation,
    detect_end_token,
    should_continue,
    prevent_ambiguous_ending,
    MIN_TURN_THRESHOLD,
    END_TOKEN,
)


def test_detect_mi_component():
    """Test detection of individual MI components."""
    try:
        # Test open-ended questions
        assert detect_mi_component("What brings you here today?", "open_ended_question")
        assert detect_mi_component("How do you feel about that?", "open_ended_question")
        assert detect_mi_component("Tell me more about your concerns.", "open_ended_question")
        
        # Test reflections
        assert detect_mi_component("It sounds like you're concerned.", "reflection")
        assert detect_mi_component("So you're feeling uncertain about this.", "reflection")
        assert detect_mi_component("You mentioned you're worried.", "reflection")
        
        # Test autonomy
        assert detect_mi_component("You can decide what works best.", "autonomy")
        assert detect_mi_component("It's up to you to choose.", "autonomy")
        assert detect_mi_component("What would work for your situation?", "autonomy")
        
        # Test summary
        assert detect_mi_component("To summarize, we've discussed...", "summary")
        assert detect_mi_component("Let me recap what we've covered.", "summary")
        assert detect_mi_component("So far we've talked about your goals.", "summary")
        
        # Test negatives
        assert not detect_mi_component("Can you do this?", "open_ended_question")  # Closed question
        assert not detect_mi_component("I think you should try this.", "reflection")  # Not a reflection
        
        print("✅ MI component detection works correctly")
        return True
    except Exception as e:
        print(f"❌ MI component detection test failed: {e}")
        traceback.print_exc()
        return False


def test_check_mi_coverage():
    """Test checking MI coverage across conversation."""
    try:
        # Complete conversation with all MI components
        complete_chat = [
            {"role": "assistant", "content": "What brings you here today?"},  # open-ended
            {"role": "user", "content": "I'm worried about the vaccine."},
            {"role": "assistant", "content": "It sounds like you have concerns."},  # reflection
            {"role": "user", "content": "Yes, I do."},
            {"role": "assistant", "content": "What would work best for you?"},  # autonomy
            {"role": "user", "content": "I'm not sure."},
            {"role": "assistant", "content": "To summarize, we've discussed your concerns."},  # summary
        ]
        
        coverage = check_mi_coverage(complete_chat)
        assert coverage['open_ended_question'], "Should detect open-ended question"
        assert coverage['reflection'], "Should detect reflection"
        assert coverage['autonomy'], "Should detect autonomy"
        assert coverage['summary'], "Should detect summary"
        
        # Incomplete conversation - missing summary
        incomplete_chat = [
            {"role": "assistant", "content": "What do you think?"},
            {"role": "user", "content": "I'm not sure."},
            {"role": "assistant", "content": "It sounds like you're uncertain."},
        ]
        
        coverage = check_mi_coverage(incomplete_chat)
        assert coverage['open_ended_question'], "Should detect open-ended question"
        assert coverage['reflection'], "Should detect reflection"
        assert not coverage['summary'], "Should not detect summary"
        
        print("✅ MI coverage checking works correctly")
        return True
    except Exception as e:
        print(f"❌ MI coverage checking test failed: {e}")
        traceback.print_exc()
        return False


def test_detect_student_confirmation():
    """Test detection of student confirmation to end."""
    try:
        # Explicit confirmations
        assert detect_student_confirmation("Yes, let's end the session")
        assert detect_student_confirmation("I'm done, no more questions")
        assert detect_student_confirmation("That's all I wanted to know")
        assert detect_student_confirmation("I think we're done here")
        assert detect_student_confirmation("Let's wrap up")
        
        # Ambiguous phrases that should NOT confirm
        assert not detect_student_confirmation("thanks")
        assert not detect_student_confirmation("okay")
        assert not detect_student_confirmation("thank you")
        assert not detect_student_confirmation("sure")
        
        # Regular conversation (not confirmation)
        assert not detect_student_confirmation("Can you tell me more?")
        assert not detect_student_confirmation("I have another question")
        
        print("✅ Student confirmation detection works correctly")
        return True
    except Exception as e:
        print(f"❌ Student confirmation detection test failed: {e}")
        traceback.print_exc()
        return False


def test_detect_end_token():
    """Test detection of end token in assistant messages."""
    try:
        # With end token
        assert detect_end_token(f"Thank you for the conversation. {END_TOKEN}")
        assert detect_end_token(f"{END_TOKEN} Goodbye!")
        
        # Without end token
        assert not detect_end_token("Thank you for the conversation.")
        assert not detect_end_token("Goodbye!")
        
        print("✅ End token detection works correctly")
        return True
    except Exception as e:
        print(f"❌ End token detection test failed: {e}")
        traceback.print_exc()
        return False


def test_should_continue_min_turns():
    """Test minimum turn threshold enforcement."""
    try:
        # If MIN_TURN_THRESHOLD is 0, skip this test
        if MIN_TURN_THRESHOLD == 0:
            print("✅ Minimum turn threshold is 0 (mutual-intent mode) - skipping turn threshold test")
            return True
        
        # Below threshold - should continue
        state = {
            'chat_history': [],
            'turn_count': 5
        }
        result = should_continue(state, "Some message")
        assert result['continue'], "Should continue when below min turns"
        assert "minimum turn threshold" in result['reason'].lower()
        
        # At threshold with everything else - should still need other conditions
        state['turn_count'] = MIN_TURN_THRESHOLD
        result = should_continue(state, "Some message")
        assert result['continue'], "Should still need other conditions"
        
        print("✅ Minimum turn threshold enforcement works correctly")
        return True
    except Exception as e:
        print(f"❌ Minimum turn threshold test failed: {e}")
        traceback.print_exc()
        return False


def test_should_continue_mi_coverage():
    """Test MI coverage requirement enforcement."""
    try:
        # Complete conversation with MI coverage
        state = {
            'chat_history': [
                {"role": "assistant", "content": "What brings you here?"},
                {"role": "assistant", "content": "It sounds like you're concerned."},
                {"role": "assistant", "content": "You can decide what's best."},
                {"role": "assistant", "content": "To summarize our discussion..."},
            ],
            'turn_count': MIN_TURN_THRESHOLD
        }
        
        # Should still continue without student confirmation and end token
        result = should_continue(state, "Some message")
        assert result['continue'], "Should continue without student confirmation"
        
        # Incomplete MI coverage
        state['chat_history'] = [
            {"role": "assistant", "content": "What brings you here?"},
        ]
        result = should_continue(state, "Some message")
        assert result['continue'], "Should continue with incomplete MI coverage"
        assert "mi coverage" in result['reason'].lower()
        
        print("✅ MI coverage requirement works correctly")
        return True
    except Exception as e:
        print(f"❌ MI coverage requirement test failed: {e}")
        traceback.print_exc()
        return False


def test_should_continue_all_conditions():
    """Test that all conditions must be met to allow ending."""
    try:
        # All conditions met
        state = {
            'chat_history': [
                {"role": "assistant", "content": "What brings you here today?"},  # open-ended
                {"role": "user", "content": "I'm worried."},
                {"role": "assistant", "content": "It sounds like you're concerned."},  # reflection
                {"role": "user", "content": "Yes."},
                {"role": "assistant", "content": "You can decide what's best."},  # autonomy
                {"role": "user", "content": "Thanks."},
                {"role": "assistant", "content": "To summarize our conversation... <<END>>"},  # summary + token
            ],
            'turn_count': MIN_TURN_THRESHOLD
        }
        
        last_assistant = f"To summarize our conversation... {END_TOKEN}"
        last_user = "Yes, let's end the session"
        
        result = should_continue(state, last_assistant, last_user)
        assert not result['continue'], "Should allow ending when all conditions met"
        assert "all end conditions met" in result['reason'].lower()
        
        # Missing end token
        result = should_continue(state, "To summarize our conversation...", last_user)
        assert result['continue'], "Should continue without end token"
        
        # Missing student confirmation
        result = should_continue(state, last_assistant, "thanks")
        assert result['continue'], "Should continue without explicit confirmation"
        
        print("✅ All conditions requirement works correctly")
        return True
    except Exception as e:
        print(f"❌ All conditions requirement test failed: {e}")
        traceback.print_exc()
        return False


def test_prevent_ambiguous_ending():
    """Test prevention of ambiguous phrase endings."""
    try:
        # Single ambiguous words
        assert prevent_ambiguous_ending("thanks")
        assert prevent_ambiguous_ending("okay")
        assert prevent_ambiguous_ending("ok")
        assert prevent_ambiguous_ending("sure")
        
        # Short ambiguous combinations
        assert prevent_ambiguous_ending("ok thanks")
        assert prevent_ambiguous_ending("thank you")
        
        # Should not prevent meaningful messages
        assert not prevent_ambiguous_ending("Thanks for the information, I have more questions")
        assert not prevent_ambiguous_ending("Okay, but what about side effects?")
        assert not prevent_ambiguous_ending("I'm done with my questions")
        
        print("✅ Ambiguous phrase prevention works correctly")
        return True
    except Exception as e:
        print(f"❌ Ambiguous phrase prevention test failed: {e}")
        traceback.print_exc()
        return False


def test_configuration():
    """Test that configuration values are set correctly."""
    try:
        # MIN_TURN_THRESHOLD can be 0 or positive (0 allows mutual-intent only ending)
        assert MIN_TURN_THRESHOLD >= 0, "MIN_TURN_THRESHOLD should be non-negative"
        assert END_TOKEN, "END_TOKEN should be defined"
        assert isinstance(MIN_TURN_THRESHOLD, int), "MIN_TURN_THRESHOLD should be integer"
        
        print(f"✅ Configuration correct: MIN_TURN_THRESHOLD={MIN_TURN_THRESHOLD}, END_TOKEN='{END_TOKEN}'")
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("🧪 Running End-Control Middleware Tests\n")
    
    tests = [
        ("Configuration", test_configuration),
        ("MI Component Detection", test_detect_mi_component),
        ("MI Coverage Checking", test_check_mi_coverage),
        ("Student Confirmation Detection", test_detect_student_confirmation),
        ("End Token Detection", test_detect_end_token),
        ("Minimum Turn Threshold", test_should_continue_min_turns),
        ("MI Coverage Requirement", test_should_continue_mi_coverage),
        ("All Conditions Requirement", test_should_continue_all_conditions),
        ("Ambiguous Phrase Prevention", test_prevent_ambiguous_ending),
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
        print("🎉 All tests passed! End-control middleware is working correctly.")
        return 0
    else:
        print(f"⚠️  {total - passed} tests failed. Please check the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
