#!/usr/bin/env python3
"""
Test script for internal scoring modifiers functionality.
Validates that internal modifiers work correctly while maintaining max score of 30.
"""

import sys
import traceback
from scoring_utils import MIScorer, calculate_engagement_metrics
from time_utils import calculate_response_times, get_time_based_modifier


def test_max_score_never_exceeds_30():
    """Test that final score never exceeds 30 regardless of modifiers."""
    print("🧪 Testing Maximum Score Cap")
    
    # Perfect feedback (all Met = 30 points base)
    perfect_feedback = """
**1. COLLABORATION (7.5 pts): Met** - Excellent
**2. EVOCATION (7.5 pts): Met** - Excellent
**3. ACCEPTANCE (7.5 pts): Met** - Excellent
**4. COMPASSION (7.5 pts): Met** - Excellent
"""
    
    try:
        # Test with high multipliers that would exceed 30
        high_engagement = {
            'turn_count': 15,  # High turn count
            'avg_message_length': 150,  # Long messages
            'question_count': 10  # Many questions
        }
        
        high_time = {
            'avg_response_time': 20  # Ideal timing
        }
        
        breakdown = MIScorer.get_score_breakdown(
            perfect_feedback,
            engagement_metrics=high_engagement,
            time_metrics=high_time
        )
        
        # Final score should be capped at 30
        assert breakdown['total_score'] == 30.0, f"Score should be capped at 30, got {breakdown['total_score']}"
        assert breakdown['total_score'] <= 30.0, f"Score exceeded maximum: {breakdown['total_score']}"
        
        # Check internal metrics show the adjustment
        internal = breakdown.get('_internal', {})
        assert 'base_score' in internal, "Internal metrics missing base_score"
        assert 'effort_multiplier' in internal, "Internal metrics missing effort_multiplier"
        assert 'time_multiplier' in internal, "Internal metrics missing time_multiplier"
        
        print(f"✅ Score correctly capped at {breakdown['total_score']}/30.0")
        print(f"   Base score: {internal['base_score']}, Effort: {internal['effort_multiplier']:.2f}x, Time: {internal['time_multiplier']:.2f}x")
        return True
        
    except Exception as e:
        print(f"❌ Max score cap test failed: {e}")
        traceback.print_exc()
        return False


def test_internal_modifiers_work():
    """Test that internal modifiers are applied correctly."""
    print("🧪 Testing Internal Modifiers")
    
    # Medium performance feedback (should benefit from modifiers)
    medium_feedback = """
**1. COLLABORATION (7.5 pts): Partially Met** - Good effort
**2. EVOCATION (7.5 pts): Met** - Excellent
**3. ACCEPTANCE (7.5 pts): Partially Met** - Good
**4. COMPASSION (7.5 pts): Partially Met** - Good
"""
    
    try:
        # Test without modifiers
        breakdown_no_modifiers = MIScorer.get_score_breakdown(medium_feedback)
        base_only_score = breakdown_no_modifiers['_internal']['base_score']
        
        # Test with positive modifiers
        good_engagement = {
            'turn_count': 10,
            'avg_message_length': 80,
            'question_count': 5
        }
        
        good_time = {
            'avg_response_time': 25  # Good timing
        }
        
        breakdown_with_modifiers = MIScorer.get_score_breakdown(
            medium_feedback,
            engagement_metrics=good_engagement,
            time_metrics=good_time
        )
        
        modified_score = breakdown_with_modifiers['total_score']
        internal = breakdown_with_modifiers['_internal']
        
        # Modified score should be higher than base (with modifiers > 1.0)
        if internal['effort_multiplier'] > 1.0 or internal['time_multiplier'] > 1.0:
            assert modified_score >= base_only_score, f"Modified score {modified_score} should be >= base {base_only_score}"
        
        # But still within valid range
        assert 0 <= modified_score <= 30.0, f"Score {modified_score} outside valid range"
        
        print(f"✅ Internal modifiers working correctly")
        print(f"   Base: {base_only_score:.2f}, Modified: {modified_score:.2f}")
        print(f"   Effort: {internal['effort_multiplier']:.2f}x, Time: {internal['time_multiplier']:.2f}x")
        return True
        
    except Exception as e:
        print(f"❌ Internal modifiers test failed: {e}")
        traceback.print_exc()
        return False


def test_lenient_scoring():
    """Test that lenient scoring gives higher scores."""
    print("🧪 Testing Lenient Scoring")
    
    # Partially Met feedback (now 0.6 instead of 0.5)
    partial_feedback = """
**1. COLLABORATION (7.5 pts): Partially Met** - Good
**2. EVOCATION (7.5 pts): Partially Met** - Good
**3. ACCEPTANCE (7.5 pts): Partially Met** - Good
**4. COMPASSION (7.5 pts): Partially Met** - Good
"""
    
    try:
        breakdown = MIScorer.get_score_breakdown(partial_feedback)
        
        # Each component: 7.5 * 0.6 = 4.5
        # Total: 4.5 * 4 = 18.0 (more lenient than old 15.0 with 0.5 multiplier)
        expected_base = 18.0
        actual_base = breakdown['_internal']['base_score']
        
        assert actual_base == expected_base, f"Expected base {expected_base}, got {actual_base}"
        
        # Final score might be even higher with modifiers
        assert breakdown['total_score'] >= expected_base, f"Final score should be >= base score"
        
        print(f"✅ Lenient scoring working: {breakdown['total_score']:.1f}/30.0")
        print(f"   Base score: {actual_base:.1f} (0.6 multiplier for Partially Met)")
        return True
        
    except Exception as e:
        print(f"❌ Lenient scoring test failed: {e}")
        traceback.print_exc()
        return False


def test_time_tracking():
    """Test that time tracking works behind the scenes."""
    print("🧪 Testing Time Tracking")
    
    try:
        # Test with mock chat history
        chat_history = [
            {'role': 'assistant', 'content': 'Hello'},
            {'role': 'user', 'content': 'Hi there'},
            {'role': 'assistant', 'content': 'How can I help?'},
            {'role': 'user', 'content': 'I need advice'},
        ]
        
        # Test without timestamps (should use defaults)
        time_metrics = calculate_response_times(chat_history)
        
        assert 'avg_response_time' in time_metrics, "Missing avg_response_time"
        assert 'total_time' in time_metrics, "Missing total_time"
        assert 'response_count' in time_metrics, "Missing response_count"
        
        # Test modifier calculation
        modifier = get_time_based_modifier(time_metrics)
        assert 0.9 <= modifier <= 1.2, f"Modifier {modifier} outside valid range"
        
        print(f"✅ Time tracking working correctly")
        print(f"   Avg response time: {time_metrics['avg_response_time']:.1f}s, Modifier: {modifier:.2f}x")
        return True
        
    except Exception as e:
        print(f"❌ Time tracking test failed: {e}")
        traceback.print_exc()
        return False


def test_engagement_tracking():
    """Test that engagement tracking works behind the scenes."""
    print("🧪 Testing Engagement Tracking")
    
    try:
        # Test with mock chat history
        chat_history = [
            {'role': 'assistant', 'content': 'Hello'},
            {'role': 'user', 'content': 'Hi, how are you? I have a question about health.'},
            {'role': 'assistant', 'content': 'Great!'},
            {'role': 'user', 'content': 'Can you tell me more? What should I know?'},
            {'role': 'assistant', 'content': 'Sure'},
            {'role': 'user', 'content': 'That helps, thanks! Is there anything else?'},
        ]
        
        metrics = calculate_engagement_metrics(chat_history)
        
        assert 'turn_count' in metrics, "Missing turn_count"
        assert 'avg_message_length' in metrics, "Missing avg_message_length"
        assert 'question_count' in metrics, "Missing question_count"
        
        # Verify calculations
        assert metrics['turn_count'] == 3, f"Expected 3 user turns, got {metrics['turn_count']}"
        assert metrics['question_count'] >= 2, f"Expected at least 2 questions, got {metrics['question_count']}"
        assert metrics['avg_message_length'] > 0, "Average message length should be positive"
        
        # Test multiplier calculation
        multiplier = MIScorer.calculate_effort_multiplier(metrics)
        assert 1.0 <= multiplier <= 1.3, f"Multiplier {multiplier} outside valid range"
        
        print(f"✅ Engagement tracking working correctly")
        print(f"   Turns: {metrics['turn_count']}, Questions: {metrics['question_count']}, Multiplier: {multiplier:.2f}x")
        return True
        
    except Exception as e:
        print(f"❌ Engagement tracking test failed: {e}")
        traceback.print_exc()
        return False


def test_score_consistency_with_modifiers():
    """Test that score validation works with internal modifiers."""
    print("🧪 Testing Score Consistency with Modifiers")
    
    feedback = """
**1. COLLABORATION (7.5 pts): Met** - Good
**2. EVOCATION (7.5 pts): Partially Met** - OK
**3. ACCEPTANCE (7.5 pts): Met** - Great
**4. COMPASSION (7.5 pts): Not Met** - Needs work
"""
    
    try:
        engagement = {'turn_count': 8, 'avg_message_length': 70, 'question_count': 4}
        time = {'avg_response_time': 22}
        
        breakdown = MIScorer.get_score_breakdown(
            feedback,
            engagement_metrics=engagement,
            time_metrics=time
        )
        
        # Validate consistency
        is_consistent = MIScorer.validate_score_consistency(breakdown)
        assert is_consistent, "Score consistency validation failed"
        
        # Validate range
        assert MIScorer.validate_score_range(breakdown['total_score']), "Score outside valid range"
        
        # Verify internal structure
        assert '_internal' in breakdown, "Missing internal metrics"
        internal = breakdown['_internal']
        
        # Component sum should match base score
        component_sum = sum(c['score'] for c in breakdown['components'].values())
        assert abs(component_sum - internal['base_score']) < 0.001, "Component sum doesn't match base"
        
        # Total should be <= 30
        assert breakdown['total_score'] <= 30.0, f"Total exceeds maximum: {breakdown['total_score']}"
        
        print(f"✅ Score consistency validated with modifiers: {breakdown['total_score']:.1f}/30.0")
        return True
        
    except Exception as e:
        print(f"❌ Score consistency test failed: {e}")
        traceback.print_exc()
        return False


def test_zero_score_with_modifiers():
    """Test that zero score remains zero even with modifiers."""
    print("🧪 Testing Zero Score with Modifiers")
    
    empty_feedback = ""
    
    try:
        # Even with high modifiers, zero base should stay zero
        high_metrics = {
            'turn_count': 15,
            'avg_message_length': 200,
            'question_count': 10
        }
        
        breakdown = MIScorer.get_score_breakdown(
            empty_feedback,
            engagement_metrics=high_metrics,
            time_metrics={'avg_response_time': 20}
        )
        
        assert breakdown['total_score'] == 0.0, f"Expected 0, got {breakdown['total_score']}"
        assert breakdown['_internal']['base_score'] == 0.0, "Base score should be 0"
        
        print(f"✅ Zero score remains zero with modifiers")
        return True
        
    except Exception as e:
        print(f"❌ Zero score test failed: {e}")
        traceback.print_exc()
        return False


def main():
    """Run all internal modifier tests."""
    print("🧪 Testing Internal Scoring Modifiers\n")
    
    tests = [
        ("Max Score Never Exceeds 30", test_max_score_never_exceeds_30),
        ("Internal Modifiers Work", test_internal_modifiers_work),
        ("Lenient Scoring", test_lenient_scoring),
        ("Time Tracking", test_time_tracking),
        ("Engagement Tracking", test_engagement_tracking),
        ("Score Consistency with Modifiers", test_score_consistency_with_modifiers),
        ("Zero Score with Modifiers", test_zero_score_with_modifiers),
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
        print("🎉 All internal modifier tests passed!")
        return 0
    else:
        print(f"⚠️  {total - passed} tests failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
