#!/usr/bin/env python3
"""
Test script for lenient scoring system with effort tracking and time-based bonuses.
"""

import sys
import traceback
from datetime import datetime


def test_effort_bonus_calculation():
    """Test that effort bonuses are calculated correctly."""
    try:
        from scoring_utils import MIScorer
        
        # Test with minimal engagement
        minimal_chat = [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello!"},
            {"role": "user", "content": "Thanks"},
            {"role": "assistant", "content": "You're welcome!"}
        ]
        
        effort_data = MIScorer.calculate_effort_bonus(minimal_chat)
        assert effort_data['bonus'] >= 0.0, "Bonus should be non-negative"
        assert effort_data['metrics']['num_turns'] == 2, "Should count 2 user turns"
        print(f"✅ Minimal effort bonus: {effort_data['bonus']:.2f} points")
        
        # Test with good engagement
        good_chat = [
            {"role": "user", "content": "I'd like to discuss my health concerns today, particularly about HPV vaccination."},
            {"role": "assistant", "content": "Great, let's talk about that."},
            {"role": "user", "content": "I'm worried about potential side effects and whether it's really necessary."},
            {"role": "assistant", "content": "Those are valid concerns."},
            {"role": "user", "content": "Can you explain what the research says about effectiveness?"},
            {"role": "assistant", "content": "Sure, the research shows..."},
            {"role": "user", "content": "That makes sense. I appreciate the detailed explanation."},
            {"role": "assistant", "content": "Glad I could help."},
            {"role": "user", "content": "I think I'm ready to move forward with scheduling an appointment."},
            {"role": "assistant", "content": "That's wonderful!"}
        ]
        
        good_effort = MIScorer.calculate_effort_bonus(good_chat)
        assert good_effort['bonus'] > effort_data['bonus'], "Good engagement should get higher bonus"
        assert good_effort['metrics']['num_turns'] == 5, "Should count 5 user turns"
        print(f"✅ Good effort bonus: {good_effort['bonus']:.2f} points (quality: {good_effort['metrics']['quality_score']}, engagement: {good_effort['metrics']['engagement_score']})")
        
        # Test with excellent engagement
        excellent_chat = [{"role": "user", "content": "This is a quality response that demonstrates thoughtful engagement and careful consideration." * 3}] * 12
        excellent_effort = MIScorer.calculate_effort_bonus(excellent_chat)
        assert excellent_effort['bonus'] > good_effort['bonus'], "Excellent engagement should get highest bonus"
        print(f"✅ Excellent effort bonus: {excellent_effort['bonus']:.2f} points")
        
        return True
    except Exception as e:
        print(f"❌ Effort bonus test error: {e}")
        traceback.print_exc()
        return False


def test_time_bonus_calculation():
    """Test that time bonuses are calculated correctly."""
    try:
        from scoring_utils import MIScorer
        
        # Test quick thoughtful responses (10-30s)
        quick_times = [15.0, 20.0, 25.0, 18.0]
        quick_data = MIScorer.calculate_time_bonus(quick_times)
        assert quick_data['multiplier'] > 0, "Quick thoughtful should get bonus"
        assert quick_data['metrics']['time_category'] == 'quick_thoughtful'
        print(f"✅ Quick thoughtful bonus: {quick_data['multiplier']:.2%} ({quick_data['metrics']['avg_response_time']:.1f}s)")
        
        # Test reasonable responses (30-60s)
        reasonable_times = [35.0, 45.0, 50.0, 40.0]
        reasonable_data = MIScorer.calculate_time_bonus(reasonable_times)
        assert reasonable_data['multiplier'] > 0, "Reasonable time should get bonus"
        assert reasonable_data['metrics']['time_category'] == 'reasonable'
        print(f"✅ Reasonable time bonus: {reasonable_data['multiplier']:.2%} ({reasonable_data['metrics']['avg_response_time']:.1f}s)")
        
        # Test slow responses (60-120s)
        slow_times = [70.0, 90.0, 80.0, 85.0]
        slow_data = MIScorer.calculate_time_bonus(slow_times)
        assert slow_data['multiplier'] >= 0, "Slow time should get small or no bonus"
        print(f"✅ Slow response bonus: {slow_data['multiplier']:.2%} ({slow_data['metrics']['avg_response_time']:.1f}s)")
        
        # Test very slow/timeout (>120s)
        timeout_times = [150.0, 200.0, 180.0]
        timeout_data = MIScorer.calculate_time_bonus(timeout_times)
        assert timeout_data['multiplier'] == 0.0, "Timeout should get no bonus"
        assert timeout_data['metrics']['time_category'] == 'timeout'
        print(f"✅ Timeout bonus: {timeout_data['multiplier']:.2%} (no bonus)")
        
        return True
    except Exception as e:
        print(f"❌ Time bonus test error: {e}")
        traceback.print_exc()
        return False


def test_integrated_scoring():
    """Test integrated scoring with base score + effort + time bonuses."""
    try:
        from scoring_utils import MIScorer
        
        # Sample feedback with good scores
        feedback = """
1. COLLABORATION: [Met] - Student demonstrated excellent partnership building
2. EVOCATION: [Met] - Strong questioning techniques  
3. ACCEPTANCE: [Partially Met] - Generally respected autonomy
4. COMPASSION: [Met] - Showed empathy throughout
"""
        
        # Good chat history
        chat_history = [
            {"role": "user", "content": "I'd like to discuss my concerns about the HPV vaccine today."},
            {"role": "assistant", "content": "I'd be happy to talk about that with you."},
            {"role": "user", "content": "I've heard some concerning things about side effects."},
            {"role": "assistant", "content": "What have you heard specifically?"},
            {"role": "user", "content": "Some people say it causes serious health problems later."},
            {"role": "assistant", "content": "Let me share what the research actually shows."},
            {"role": "user", "content": "That's helpful. I appreciate you taking time to explain this."},
            {"role": "assistant", "content": "Of course! What other questions do you have?"},
            {"role": "user", "content": "How effective is it really at preventing HPV?"},
            {"role": "assistant", "content": "The vaccine is highly effective..."}
        ]
        
        # Good response times
        response_times = [20.0, 25.0, 18.0, 22.0, 15.0]
        
        # Get breakdown without bonuses
        base_breakdown = MIScorer.get_score_breakdown(feedback)
        base_score = base_breakdown['total_score']
        print(f"📊 Base score: {base_score:.2f}/30.0 ({base_breakdown['percentage']:.1f}%)")
        
        # Get breakdown with bonuses
        full_breakdown = MIScorer.get_score_breakdown(feedback, chat_history, response_times)
        total_score = full_breakdown['total_score']
        effort_bonus = full_breakdown['effort_bonus']
        time_bonus = full_breakdown['time_bonus']
        
        print(f"📊 Effort bonus: +{effort_bonus:.2f} points")
        print(f"📊 Time bonus: +{time_bonus:.2f} points")
        print(f"📊 Total score: {total_score:.2f}/30.0 ({full_breakdown['adjusted_percentage']:.1f}%)")
        
        assert total_score > base_score, "Total score should include bonuses"
        assert full_breakdown['effort_bonus'] > 0, "Should have effort bonus"
        assert full_breakdown['time_bonus'] > 0, "Should have time bonus"
        
        print("✅ Integrated scoring works correctly")
        return True
        
    except Exception as e:
        print(f"❌ Integrated scoring test error: {e}")
        traceback.print_exc()
        return False


def test_partial_credit_scenarios():
    """Test various partial credit scenarios."""
    try:
        from scoring_utils import MIScorer
        
        # All partially met
        partial_feedback = """
1. COLLABORATION: [Partially Met] - Some partnership building
2. EVOCATION: [Partially Met] - Some questioning  
3. ACCEPTANCE: [Partially Met] - Some respect shown
4. COMPASSION: [Partially Met] - Some empathy
"""
        breakdown = MIScorer.get_score_breakdown(partial_feedback)
        expected = 7.5 * 4 * 0.5  # 15.0
        assert breakdown['base_score'] == expected, f"Expected {expected}, got {breakdown['base_score']}"
        print(f"✅ All partial credit: {breakdown['base_score']:.1f}/30.0")
        
        # Mixed scores
        mixed_feedback = """
1. COLLABORATION: [Met] - Excellent
2. EVOCATION: [Partially Met] - Some good work  
3. ACCEPTANCE: [Not Met] - Needs improvement
4. COMPASSION: [Met] - Great empathy
"""
        mixed = MIScorer.get_score_breakdown(mixed_feedback)
        expected_mixed = 7.5 + 3.75 + 0.0 + 7.5  # 18.75
        assert mixed['base_score'] == expected_mixed, f"Expected {expected_mixed}, got {mixed['base_score']}"
        print(f"✅ Mixed scores: {mixed['base_score']:.1f}/30.0")
        
        return True
        
    except Exception as e:
        print(f"❌ Partial credit test error: {e}")
        traceback.print_exc()
        return False


def test_time_utils_functions():
    """Test time utilities for response tracking."""
    try:
        from time_utils import (
            calculate_response_time, 
            get_time_category, 
            calculate_time_modifier,
            handle_timeout
        )
        
        # Test response time calculation
        time_diff = calculate_response_time("2024-01-01 10:00:00", "2024-01-01 10:00:25")
        assert time_diff == 25.0, f"Expected 25.0s, got {time_diff}"
        print(f"✅ Response time calculation: {time_diff}s")
        
        # Test time categories
        assert get_time_category(5.0) == 'too_quick'
        assert get_time_category(20.0) == 'quick_thoughtful'
        assert get_time_category(45.0) == 'reasonable'
        assert get_time_category(90.0) == 'slow_but_complete'
        assert get_time_category(200.0) == 'very_slow'
        assert get_time_category(400.0) == 'timeout'
        print("✅ Time categorization works")
        
        # Test time modifiers
        assert calculate_time_modifier(20.0) > 0, "Quick thoughtful should get bonus"
        assert calculate_time_modifier(45.0) > 0, "Reasonable should get bonus"
        assert calculate_time_modifier(5.0) == 0.0, "Too quick should get no bonus"
        assert calculate_time_modifier(200.0) == 0.0, "Very slow should get no bonus"
        print("✅ Time modifiers work correctly")
        
        # Test timeout handling
        is_timeout, msg = handle_timeout(350.0, 300)
        assert is_timeout == True, "Should detect timeout"
        assert msg is not None, "Should provide timeout message"
        print(f"✅ Timeout handling: {msg}")
        
        is_ok, _ = handle_timeout(50.0, 300)
        assert is_ok == False, "Should not timeout for reasonable time"
        print("✅ Normal response time handling works")
        
        return True
        
    except Exception as e:
        print(f"❌ Time utils test error: {e}")
        traceback.print_exc()
        return False


def test_fairness_and_reasonableness():
    """Test that the scoring system is fair and reasonable."""
    try:
        from scoring_utils import MIScorer
        
        # Test that poor engagement doesn't get excessive bonus
        poor_chat = [{"role": "user", "content": "ok"}] * 2
        poor_effort = MIScorer.calculate_effort_bonus(poor_chat)
        assert poor_effort['bonus'] < 1.0, "Poor engagement should not get high bonus"
        print(f"✅ Poor engagement appropriately scored: {poor_effort['bonus']:.2f} points")
        
        # Test that excellent engagement gets meaningful bonus
        excellent_chat = [{"role": "user", "content": "This is a thoughtful and detailed response demonstrating real engagement with the conversation." * 2}] * 12
        excellent_effort = MIScorer.calculate_effort_bonus(excellent_chat)
        assert excellent_effort['bonus'] >= 2.0, "Excellent engagement should get meaningful bonus"
        assert excellent_effort['bonus'] <= 3.0, "Bonus should be capped reasonably"
        print(f"✅ Excellent engagement appropriately rewarded: {excellent_effort['bonus']:.2f} points")
        
        # Test that total score doesn't exceed reasonable bounds
        max_feedback = """
1. COLLABORATION: [Met] - Perfect
2. EVOCATION: [Met] - Perfect  
3. ACCEPTANCE: [Met] - Perfect
4. COMPASSION: [Met] - Perfect
"""
        max_breakdown = MIScorer.get_score_breakdown(max_feedback, excellent_chat, [20.0] * 10)
        assert max_breakdown['total_score'] <= 34.0, "Total should not exceed ~33.9 (30 + 3 effort + ~1.5 time)"
        print(f"✅ Maximum score is reasonable: {max_breakdown['total_score']:.2f}")
        
        # Test score range validation
        assert MIScorer.validate_score_range(30.0), "30 should be valid"
        assert MIScorer.validate_score_range(33.0), "33 should be valid (with bonuses)"
        assert not MIScorer.validate_score_range(35.0), "35 should be invalid"
        print("✅ Score range validation works correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Fairness test error: {e}")
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("🧪 Testing Lenient Scoring System with Effort & Time Tracking\n")
    
    tests = [
        ("Effort Bonus Calculation", test_effort_bonus_calculation),
        ("Time Bonus Calculation", test_time_bonus_calculation),
        ("Integrated Scoring", test_integrated_scoring),
        ("Partial Credit Scenarios", test_partial_credit_scenarios),
        ("Time Utils Functions", test_time_utils_functions),
        ("Fairness and Reasonableness", test_fairness_and_reasonableness),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}:")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} failed")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All lenient scoring tests passed!")
        return 0
    else:
        print(f"⚠️  {total - passed} tests failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
