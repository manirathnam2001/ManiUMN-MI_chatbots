#!/usr/bin/env python3
"""
Test to verify scoring consistency fixes.
Tests the fix for duplicate components and score validation.
"""

import sys
import traceback
from scoring_utils import MIScorer, format_score_for_display


def test_integer_score_formatting():
    """Test that format_score_for_display returns integer scores."""
    print("🧪 Testing Integer Score Formatting")
    
    test_cases = [
        (7.5, 8),
        (3.333, 3),
        (6.666, 7),
        (0.0, 0),
        (10.0, 10),
        (2.499, 2),
        (2.5, 2),  # Standard rounding: 2.5 rounds to 2 (banker's rounding)
        (3.5, 4),  # Standard rounding: 3.5 rounds to 4
    ]
    
    try:
        for score_float, expected_int in test_cases:
            result = format_score_for_display(score_float)
            assert isinstance(result, int), f"Result should be int, got {type(result)}"
            assert result == expected_int, f"format_score_for_display({score_float}) should be {expected_int}, got {result}"
        
        print(f"✅ All integer formatting tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Integer formatting test failed: {e}")
        traceback.print_exc()
        return False


def test_duplicate_components():
    """Test that duplicate components are handled correctly."""
    print("🧪 Testing Duplicate Component Handling")
    
    # Simulate AI-generated feedback with duplicate components
    duplicate_feedback = """
**1. COLLABORATION (7.5 pts): Met** - Good partnership building
**2. COLLABORATION (7.5 pts): Partially Met** - Could improve (duplicate, should use this)
**3. EVOCATION (7.5 pts): Met** - Excellent questioning
"""
    
    try:
        breakdown = MIScorer.get_score_breakdown(duplicate_feedback)
        
        # Check that we only have one COLLABORATION score (the last one)
        collab_score = breakdown['components']['COLLABORATION']['score']
        collab_status = breakdown['components']['COLLABORATION']['status']
        
        # Last occurrence was "Partially Met" = 3.75 points
        assert collab_score == 3.75, f"Expected 3.75 (last occurrence), got {collab_score}"
        assert collab_status == "Partially Met", f"Expected 'Partially Met', got '{collab_status}'"
        
        # Check total score consistency
        component_sum = sum(c['score'] for c in breakdown['components'].values())
        total_score = breakdown['total_score']
        
        assert component_sum == total_score, f"Component sum ({component_sum}) != Total ({total_score})"
        
        # Expected: COLLABORATION (3.75) + EVOCATION (7.5) + ACCEPTANCE (0) + COMPASSION (0) = 11.25
        expected_total = 11.25
        assert total_score == expected_total, f"Expected {expected_total}, got {total_score}"
        
        print(f"✅ Duplicate components handled correctly: {total_score}/30.0")
        return True
        
    except Exception as e:
        print(f"❌ Duplicate component test failed: {e}")
        traceback.print_exc()
        return False


def test_score_consistency_validation():
    """Test that score consistency validation works."""
    print("🧪 Testing Score Consistency Validation")
    
    normal_feedback = """
**1. COLLABORATION (7.5 pts): Met** - Excellent
**2. EVOCATION (7.5 pts): Partially Met** - Good
**3. ACCEPTANCE (7.5 pts): Met** - Great
**4. COMPASSION (7.5 pts): Not Met** - Needs work
"""
    
    try:
        breakdown = MIScorer.get_score_breakdown(normal_feedback)
        
        # Test the validation method
        is_consistent = MIScorer.validate_score_consistency(breakdown)
        assert is_consistent, "Score consistency validation failed"
        
        # Verify the actual values
        component_sum = sum(c['score'] for c in breakdown['components'].values())
        total_score = breakdown['total_score']
        
        assert abs(component_sum - total_score) < 0.001, f"Scores don't match: {component_sum} vs {total_score}"
        
        # Expected: 7.5 + 3.75 + 7.5 + 0 = 18.75
        assert total_score == 18.75, f"Expected 18.75, got {total_score}"
        
        print(f"✅ Score consistency validation works: {total_score}/30.0")
        return True
        
    except Exception as e:
        print(f"❌ Score consistency validation failed: {e}")
        traceback.print_exc()
        return False


def test_no_conversation_zero_score():
    """Test that no conversation results in zero score."""
    print("🧪 Testing No Conversation Scenario")
    
    # Empty feedback (no conversation)
    empty_feedback = ""
    
    try:
        breakdown = MIScorer.get_score_breakdown(empty_feedback)
        
        # All scores should be 0
        assert breakdown['total_score'] == 0.0, f"Expected 0, got {breakdown['total_score']}"
        
        for component, details in breakdown['components'].items():
            assert details['score'] == 0.0, f"{component} should be 0, got {details['score']}"
            assert details['status'] == 'Not Found', f"{component} status should be 'Not Found'"
        
        # Validation should still pass
        assert MIScorer.validate_score_consistency(breakdown), "Validation failed for zero scores"
        
        print(f"✅ No conversation correctly results in 0/30.0 score")
        return True
        
    except Exception as e:
        print(f"❌ No conversation test failed: {e}")
        traceback.print_exc()
        return False


def test_score_range_validation():
    """Test that score range validation works."""
    print("🧪 Testing Score Range Validation")
    
    try:
        # Valid scores
        assert MIScorer.validate_score_range(0.0), "0.0 should be valid"
        assert MIScorer.validate_score_range(15.0), "15.0 should be valid"
        assert MIScorer.validate_score_range(30.0), "30.0 should be valid"
        
        # Invalid scores
        assert not MIScorer.validate_score_range(-1.0), "-1.0 should be invalid"
        assert not MIScorer.validate_score_range(31.0), "31.0 should be invalid"
        assert not MIScorer.validate_score_range(100.0), "100.0 should be invalid"
        
        print("✅ Score range validation works correctly")
        return True
        
    except Exception as e:
        print(f"❌ Score range validation failed: {e}")
        traceback.print_exc()
        return False


def test_triple_duplicate_components():
    """Test edge case with three duplicate components."""
    print("🧪 Testing Triple Duplicate Components")
    
    # Extreme case: three of the same component
    triple_feedback = """
**1. COMPASSION (7.5 pts): Not Met** - First
**2. COMPASSION (7.5 pts): Partially Met** - Second
**3. COMPASSION (7.5 pts): Met** - Third (should use this one)
"""
    
    try:
        breakdown = MIScorer.get_score_breakdown(triple_feedback)
        
        # Should use the last occurrence (Met = 7.5)
        compassion_score = breakdown['components']['COMPASSION']['score']
        assert compassion_score == 7.5, f"Expected 7.5 (last occurrence), got {compassion_score}"
        
        # Total should match component sum
        component_sum = sum(c['score'] for c in breakdown['components'].values())
        assert breakdown['total_score'] == component_sum, "Total doesn't match component sum"
        
        print(f"✅ Triple duplicates handled correctly: {breakdown['total_score']}/30.0")
        return True
        
    except Exception as e:
        print(f"❌ Triple duplicate test failed: {e}")
        traceback.print_exc()
        return False


def main():
    """Run all scoring consistency tests."""
    print("🧪 Testing Scoring Consistency Fixes\n")
    
    tests = [
        ("Integer Score Formatting", test_integer_score_formatting),
        ("Duplicate Components", test_duplicate_components),
        ("Score Consistency Validation", test_score_consistency_validation),
        ("No Conversation Zero Score", test_no_conversation_zero_score),
        ("Score Range Validation", test_score_range_validation),
        ("Triple Duplicate Components", test_triple_duplicate_components),
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
        print("🎉 All scoring consistency tests passed!")
        return 0
    else:
        print(f"⚠️  {total - passed} tests failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
