#!/usr/bin/env python3
"""
Test suite for internal time and effort tracking in the scoring system.
These tests verify that internal tracking works correctly while keeping
the metrics internal (not visible to users in the UI).
"""

import sys
import traceback
from scoring_utils import MIScorer


def test_internal_tracking_disabled_by_default():
    """Test that internal tracking is disabled by default for backwards compatibility."""
    print("🧪 Testing Internal Tracking Disabled by Default")
    
    feedback = """
**1. COLLABORATION (7.5 pts): Met** - Good partnership
**2. EVOCATION (7.5 pts): Partially Met** - Some questioning
**3. ACCEPTANCE (7.5 pts): Met** - Respected autonomy
**4. COMPASSION (7.5 pts): Partially Met** - Generally warm
"""
    
    try:
        # Without enabling internal adjustments, score should match component sum
        breakdown = MIScorer.get_score_breakdown(feedback)
        
        # Expected: 7.5 + 3.75 + 7.5 + 3.75 = 22.5
        expected_score = 22.5
        assert breakdown['total_score'] == expected_score, f"Expected {expected_score}, got {breakdown['total_score']}"
        
        # Should not have internal tracking data
        assert '_internal_tracking' not in breakdown, "Internal tracking should not be present when disabled"
        
        print(f"✅ Internal tracking disabled by default: {breakdown['total_score']}/30.0")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        traceback.print_exc()
        return False


def test_internal_tracking_enabled():
    """Test that internal tracking provides lenient bonuses when enabled."""
    print("🧪 Testing Internal Tracking Enabled")
    
    # Longer feedback to trigger time bonus
    feedback = """
**1. COLLABORATION (7.5 pts): Met** - The student demonstrated excellent partnership building skills throughout the conversation. They actively involved the patient in decision-making and created a collaborative atmosphere that fostered trust and open communication.

**2. EVOCATION (7.5 pts): Partially Met** - The student made some effort to elicit the patient's own motivations and thoughts. While they asked some good questions, there were missed opportunities to explore the patient's perspective more deeply.

**3. ACCEPTANCE (7.5 pts): Met** - The student consistently respected the patient's autonomy and right to make their own decisions. They demonstrated acceptance of the patient's current situation without judgment.

**4. COMPASSION (7.5 pts): Partially Met** - The student showed warmth and attempted to be non-judgmental, though there were moments where more empathy could have been demonstrated.
"""
    
    try:
        # Enable internal adjustments
        breakdown = MIScorer.get_score_breakdown(feedback, enable_internal_adjustments=True)
        
        # Base score: 7.5 + 3.75 + 7.5 + 3.75 = 22.5
        base_score = 22.5
        
        # With internal tracking, score should be higher due to bonuses
        assert breakdown['total_score'] >= base_score, f"Score with bonuses should be >= base score"
        assert breakdown['total_score'] <= 30.0, f"Score should never exceed 30 points"
        
        # Should have internal tracking data
        assert '_internal_tracking' in breakdown, "Internal tracking data should be present"
        assert breakdown['_internal_tracking']['enabled'] is True
        assert breakdown['_internal_tracking']['base_score'] == base_score
        
        # Verify bonuses were calculated
        effort_bonus = breakdown['_internal_tracking']['effort_bonus']
        time_factor = breakdown['_internal_tracking']['time_factor']
        
        assert effort_bonus > 0, "Effort bonus should be positive for engaged student"
        assert time_factor > 1.0, "Time factor should be > 1.0 for substantial feedback"
        
        print(f"✅ Internal tracking enabled: {base_score} -> {breakdown['total_score']}/30.0")
        print(f"   Effort bonus: +{effort_bonus:.2f} points, Time factor: {time_factor:.2f}x")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        traceback.print_exc()
        return False


def test_multiple_attempts_bonus():
    """Test that multiple attempts get additional leniency."""
    print("🧪 Testing Multiple Attempts Bonus")
    
    feedback = """
**1. COLLABORATION (7.5 pts): Partially Met** - Some partnership
**2. EVOCATION (7.5 pts): Partially Met** - Some questioning
**3. ACCEPTANCE (7.5 pts): Partially Met** - Some respect
**4. COMPASSION (7.5 pts): Partially Met** - Some warmth
"""
    
    try:
        # First attempt
        breakdown1 = MIScorer.get_score_breakdown(feedback, enable_internal_adjustments=True, attempt_number=1)
        
        # Third attempt (should get additional bonus)
        breakdown3 = MIScorer.get_score_breakdown(feedback, enable_internal_adjustments=True, attempt_number=3)
        
        # Base score: 3.75 * 4 = 15.0
        base_score = 15.0
        
        # Third attempt should have higher score due to attempt bonus
        assert breakdown3['total_score'] > breakdown1['total_score'], "Third attempt should score higher than first"
        assert breakdown3['total_score'] <= 30.0, "Score should never exceed 30 points"
        
        # Verify attempt tracking
        assert breakdown3['_internal_tracking']['attempt_number'] == 3
        
        print(f"✅ Multiple attempts bonus works: Attempt 1: {breakdown1['total_score']:.2f}, Attempt 3: {breakdown3['total_score']:.2f}")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        traceback.print_exc()
        return False


def test_maximum_score_cap():
    """Test that scores never exceed 30 points even with bonuses."""
    print("🧪 Testing Maximum Score Cap")
    
    # Perfect score feedback
    feedback = """
**1. COLLABORATION (7.5 pts): Met** - Excellent partnership building demonstrated throughout the entire conversation. The student created a truly collaborative environment.

**2. EVOCATION (7.5 pts): Met** - Outstanding questioning techniques that effectively elicited the patient's own motivations, values, and goals. The student demonstrated mastery of evocation.

**3. ACCEPTANCE (7.5 pts): Met** - Exemplary respect for patient autonomy and acceptance of their current situation without any judgment whatsoever.

**4. COMPASSION (7.5 pts): Met** - Exceptional warmth, empathy, and compassion displayed consistently throughout the interaction. The student created a safe and supportive environment.
"""
    
    try:
        # Enable internal adjustments with high attempt number
        breakdown = MIScorer.get_score_breakdown(feedback, enable_internal_adjustments=True, attempt_number=5)
        
        # Base score is already 30 (perfect)
        assert breakdown['total_score'] == 30.0, f"Perfect score with bonuses should be capped at 30.0"
        assert breakdown['total_score'] <= 30.0, f"Score should never exceed 30 points"
        
        print(f"✅ Maximum score cap enforced: {breakdown['total_score']}/30.0")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        traceback.print_exc()
        return False


def test_internal_data_not_visible():
    """Test that internal tracking data is marked as internal."""
    print("🧪 Testing Internal Data Not Visible in Standard Usage")
    
    feedback = """
**1. COLLABORATION (7.5 pts): Met** - Good work
**2. EVOCATION (7.5 pts): Met** - Good work
**3. ACCEPTANCE (7.5 pts): Met** - Good work
**4. COMPASSION (7.5 pts): Met** - Good work
"""
    
    try:
        # Get breakdown with internal tracking
        breakdown = MIScorer.get_score_breakdown(feedback, enable_internal_adjustments=True)
        
        # Internal data should be prefixed with underscore (Python convention for "private")
        assert '_internal_tracking' in breakdown, "Internal tracking should be present"
        
        # The main visible fields should not include internal details
        visible_keys = [k for k in breakdown.keys() if not k.startswith('_')]
        expected_visible = ['components', 'total_score', 'total_possible', 'percentage']
        
        for key in expected_visible:
            assert key in visible_keys, f"Expected visible key {key} not found"
        
        print(f"✅ Internal tracking data properly marked as internal (underscore prefix)")
        print(f"   Visible keys: {visible_keys}")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        traceback.print_exc()
        return False


def test_score_consistency_with_tracking():
    """Test that score consistency validation works with internal tracking."""
    print("🧪 Testing Score Consistency with Internal Tracking")
    
    feedback = """
**1. COLLABORATION (7.5 pts): Met** - Good
**2. EVOCATION (7.5 pts): Partially Met** - Okay
**3. ACCEPTANCE (7.5 pts): Met** - Good
**4. COMPASSION (7.5 pts): Not Met** - Needs work
"""
    
    try:
        # With internal tracking
        breakdown = MIScorer.get_score_breakdown(feedback, enable_internal_adjustments=True)
        
        # Validation should pass even though total != component sum
        is_valid = MIScorer.validate_score_consistency(breakdown)
        assert is_valid, "Consistency validation should pass with internal tracking"
        
        # Without internal tracking
        breakdown_no_tracking = MIScorer.get_score_breakdown(feedback, enable_internal_adjustments=False)
        is_valid_no_tracking = MIScorer.validate_score_consistency(breakdown_no_tracking)
        assert is_valid_no_tracking, "Consistency validation should pass without internal tracking"
        
        print(f"✅ Score consistency validation works with and without internal tracking")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        traceback.print_exc()
        return False


def main():
    """Run all internal tracking tests."""
    print("🧪 Testing Internal Time and Effort Tracking\n")
    
    tests = [
        ("Internal Tracking Disabled by Default", test_internal_tracking_disabled_by_default),
        ("Internal Tracking Enabled", test_internal_tracking_enabled),
        ("Multiple Attempts Bonus", test_multiple_attempts_bonus),
        ("Maximum Score Cap", test_maximum_score_cap),
        ("Internal Data Not Visible", test_internal_data_not_visible),
        ("Score Consistency with Tracking", test_score_consistency_with_tracking),
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
        print("🎉 All internal tracking tests passed!")
        return 0
    else:
        print(f"⚠️  {total - passed} tests failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
