#!/usr/bin/env python3
"""
Integration test to verify the complete scoring system implementation.
Tests that internal tracking works correctly and remains hidden from UI.
"""

import sys
import traceback
from scoring_utils import MIScorer


def test_score_never_exceeds_30():
    """Test that scores are always capped at 30 points."""
    print("🧪 Testing Score Cap at 30 Points")
    
    test_cases = [
        # Perfect score without tracking
        ("Perfect score no tracking", """
**1. COLLABORATION: [Met]** - Excellent
**2. EVOCATION: [Met]** - Excellent
**3. ACCEPTANCE: [Met]** - Excellent
**4. COMPASSION: [Met]** - Excellent
""", False, 1),
        # Perfect score with tracking
        ("Perfect score with tracking", """
**1. COLLABORATION: [Met]** - Excellent work in establishing partnership throughout the entire conversation
**2. EVOCATION: [Met]** - Outstanding questioning techniques
**3. ACCEPTANCE: [Met]** - Exemplary respect for autonomy
**4. COMPASSION: [Met]** - Exceptional warmth and empathy
""", True, 1),
        # High score with tracking and multiple attempts
        ("High score with tracking", """
**1. COLLABORATION: [Met]** - Very good partnership building
**2. EVOCATION: [Met]** - Strong questioning
**3. ACCEPTANCE: [Partially Met]** - Generally respectful
**4. COMPASSION: [Met]** - Good empathy shown
""", True, 5),
    ]
    
    try:
        for name, feedback, enable_tracking, attempt in test_cases:
            breakdown = MIScorer.get_score_breakdown(
                feedback, 
                enable_internal_adjustments=enable_tracking,
                attempt_number=attempt
            )
            
            score = breakdown['total_score']
            assert score <= 30.0, f"{name}: Score {score} exceeds 30 points!"
            assert score >= 0.0, f"{name}: Score {score} is negative!"
            
            print(f"  ✓ {name}: {score:.2f}/30.0 (within range)")
        
        print("✅ All scores properly capped at 30 points")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        traceback.print_exc()
        return False


def test_internal_tracking_hidden_from_ui():
    """Test that internal tracking data is not visible in standard UI fields."""
    print("🧪 Testing Internal Tracking Hidden from UI")
    
    feedback = """
**1. COLLABORATION: [Met]** - Good work
**2. EVOCATION: [Partially Met]** - Some effort
**3. ACCEPTANCE: [Met]** - Respectful
**4. COMPASSION: [Partially Met]** - Generally warm
"""
    
    try:
        # Get breakdown with internal tracking enabled
        breakdown = MIScorer.get_score_breakdown(feedback, enable_internal_adjustments=True)
        
        # Standard UI fields should be present
        ui_fields = ['components', 'total_score', 'total_possible', 'percentage']
        for field in ui_fields:
            assert field in breakdown, f"UI field '{field}' missing"
        
        # Internal tracking should be prefixed with underscore (convention for private)
        if '_internal_tracking' in breakdown:
            # Verify it's marked as internal
            assert breakdown['_internal_tracking']['enabled'] is True
            print("  ✓ Internal tracking data properly marked with underscore prefix")
        
        # Simulate UI display - only standard fields would be shown
        ui_display = {k: v for k, v in breakdown.items() if not k.startswith('_')}
        
        # Verify internal data not in UI display
        assert '_internal_tracking' not in ui_display
        assert 'effort_bonus' not in ui_display
        assert 'time_factor' not in ui_display
        
        print(f"  ✓ UI shows only: {list(ui_display.keys())}")
        print(f"  ✓ Final score displayed: {ui_display['total_score']:.2f}/30.0")
        print("✅ Internal tracking successfully hidden from UI")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        traceback.print_exc()
        return False


def test_more_lenient_scoring():
    """Test that the scoring system is more lenient with internal tracking."""
    print("🧪 Testing More Lenient Scoring")
    
    # Student showing effort but not perfect
    feedback = """
**1. COLLABORATION: [Partially Met]** - The student made efforts to build partnership
**2. EVOCATION: [Partially Met]** - Some good questions were asked
**3. ACCEPTANCE: [Partially Met]** - Generally respectful of autonomy
**4. COMPASSION: [Partially Met]** - Attempted to show empathy
"""
    
    try:
        # Without internal tracking (strict)
        breakdown_strict = MIScorer.get_score_breakdown(feedback, enable_internal_adjustments=False)
        strict_score = breakdown_strict['total_score']
        
        # With internal tracking (lenient)
        breakdown_lenient = MIScorer.get_score_breakdown(feedback, enable_internal_adjustments=True)
        lenient_score = breakdown_lenient['total_score']
        
        # Lenient should be higher due to bonuses
        assert lenient_score > strict_score, "Lenient scoring should give higher score"
        
        # Both should be valid
        assert 0 <= strict_score <= 30.0
        assert 0 <= lenient_score <= 30.0
        
        improvement = lenient_score - strict_score
        print(f"  ✓ Strict scoring: {strict_score:.2f}/30.0")
        print(f"  ✓ Lenient scoring: {lenient_score:.2f}/30.0")
        print(f"  ✓ Improvement: +{improvement:.2f} points ({improvement/strict_score*100:.1f}%)")
        print("✅ More lenient scoring verified")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        traceback.print_exc()
        return False


def test_multiple_attempts_handling():
    """Test that multiple attempts are handled more leniently."""
    print("🧪 Testing Multiple Attempts Handling")
    
    feedback = """
**1. COLLABORATION: [Partially Met]** - Some partnership
**2. EVOCATION: [Not Met]** - Limited questioning
**3. ACCEPTANCE: [Partially Met]** - Some respect
**4. COMPASSION: [Not Met]** - Needs work
"""
    
    try:
        # Track scores across attempts
        scores = []
        for attempt in [1, 2, 3]:
            breakdown = MIScorer.get_score_breakdown(
                feedback, 
                enable_internal_adjustments=True,
                attempt_number=attempt
            )
            scores.append(breakdown['total_score'])
        
        # Each attempt should give same or higher score (more lenient)
        for i in range(1, len(scores)):
            assert scores[i] >= scores[i-1], f"Attempt {i+1} should score >= attempt {i}"
        
        print(f"  ✓ Attempt 1: {scores[0]:.2f}/30.0")
        print(f"  ✓ Attempt 2: {scores[1]:.2f}/30.0")
        print(f"  ✓ Attempt 3: {scores[2]:.2f}/30.0")
        print("✅ Multiple attempts handled more leniently")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        traceback.print_exc()
        return False


def test_backwards_compatibility():
    """Test that existing code still works without changes."""
    print("🧪 Testing Backwards Compatibility")
    
    feedback = """
**1. COLLABORATION: [Met]** - Good
**2. EVOCATION: [Partially Met]** - Okay
**3. ACCEPTANCE: [Met]** - Good
**4. COMPASSION: [Partially Met]** - Okay
"""
    
    try:
        # Old style call (no new parameters)
        breakdown = MIScorer.get_score_breakdown(feedback)
        
        # Should work and give expected score
        expected = 7.5 + 3.75 + 7.5 + 3.75  # 22.5
        assert breakdown['total_score'] == expected, f"Expected {expected}, got {breakdown['total_score']}"
        
        # Should not have internal tracking
        assert '_internal_tracking' not in breakdown
        
        print(f"  ✓ Legacy call works: {breakdown['total_score']}/30.0")
        print("✅ Backwards compatibility maintained")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        traceback.print_exc()
        return False


def main():
    """Run all integration tests."""
    print("🧪 Running Scoring System Integration Tests\n")
    
    tests = [
        ("Score Never Exceeds 30", test_score_never_exceeds_30),
        ("Internal Tracking Hidden from UI", test_internal_tracking_hidden_from_ui),
        ("More Lenient Scoring", test_more_lenient_scoring),
        ("Multiple Attempts Handling", test_multiple_attempts_handling),
        ("Backwards Compatibility", test_backwards_compatibility),
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
        print("🎉 All integration tests passed!")
        print("\n✅ Summary:")
        print("   • Scores always capped at 30 points")
        print("   • Internal tracking works correctly")
        print("   • Internal data hidden from UI")
        print("   • More lenient scoring implemented")
        print("   • Multiple attempts handled correctly")
        print("   • Backwards compatibility maintained")
        return 0
    else:
        print(f"⚠️  {total - passed} tests failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
