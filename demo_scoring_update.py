#!/usr/bin/env python3
"""
Demonstration of the updated scoring system with internal tracking.
Shows how scores change with and without internal adjustments.
"""

from scoring_utils import MIScorer


def print_separator(title=""):
    """Print a visual separator."""
    if title:
        print(f"\n{'=' * 70}")
        print(f"  {title}")
        print('=' * 70)
    else:
        print('-' * 70)


def demonstrate_scenario(name, feedback, show_tracking=True):
    """Demonstrate a scoring scenario."""
    print(f"\n📋 Scenario: {name}")
    print(f"Feedback length: {len(feedback)} characters")
    
    # Without internal tracking (traditional scoring)
    breakdown_traditional = MIScorer.get_score_breakdown(feedback, enable_internal_adjustments=False)
    traditional_score = breakdown_traditional['total_score']
    
    print(f"\n📊 Traditional Scoring (no internal adjustments):")
    print(f"   Final Score: {traditional_score:.2f}/30.0 ({breakdown_traditional['percentage']:.1f}%)")
    
    # Show component breakdown
    for component, details in breakdown_traditional['components'].items():
        status = details['status']
        score = details['score']
        max_score = details['max_score']
        print(f"   • {component}: {status} = {score}/{max_score} pts")
    
    if show_tracking:
        # With internal tracking (lenient scoring)
        print(f"\n📈 Lenient Scoring (with internal adjustments):")
        
        for attempt in [1, 2, 3]:
            breakdown_lenient = MIScorer.get_score_breakdown(
                feedback,
                enable_internal_adjustments=True,
                attempt_number=attempt
            )
            lenient_score = breakdown_lenient['total_score']
            improvement = lenient_score - traditional_score
            improvement_pct = (improvement / traditional_score * 100) if traditional_score > 0 else 0
            
            tracking = breakdown_lenient['_internal_tracking']
            
            print(f"\n   Attempt {attempt}:")
            print(f"   • Final Score: {lenient_score:.2f}/30.0 ({breakdown_lenient['percentage']:.1f}%)")
            print(f"   • Improvement: +{improvement:.2f} points (+{improvement_pct:.1f}%)")
            print(f"   • Base Score: {tracking['base_score']:.2f}")
            print(f"   • Effort Bonus: +{tracking['effort_bonus']:.2f} points")
            print(f"   • Time Factor: {tracking['time_factor']:.2f}x")
    
    print_separator()


def main():
    """Run scoring system demonstration."""
    print_separator("SCORING SYSTEM DEMONSTRATION")
    print("\nThis demo shows how the updated scoring system works with")
    print("internal time and effort tracking for more lenient scoring.")
    
    # Scenario 1: Perfect Performance
    print_separator("Scenario 1: Perfect Performance")
    perfect_feedback = """
**1. COLLABORATION (7.5 pts): Met** - Excellent partnership building throughout the conversation
**2. EVOCATION (7.5 pts): Met** - Outstanding questioning techniques that elicited patient motivations
**3. ACCEPTANCE (7.5 pts): Met** - Exemplary respect for patient autonomy and decision-making
**4. COMPASSION (7.5 pts): Met** - Exceptional warmth, empathy, and non-judgmental approach
"""
    demonstrate_scenario("Perfect Performance", perfect_feedback, show_tracking=False)
    breakdown = MIScorer.get_score_breakdown(perfect_feedback, enable_internal_adjustments=True, attempt_number=1)
    print(f"Note: Even with internal adjustments, perfect scores remain at 30.0/30.0 (capped)")
    print(f"      Score with adjustments: {breakdown['total_score']:.2f}/30.0")
    
    # Scenario 2: Good Performance with Room for Improvement
    print_separator("Scenario 2: Good Performance with Room for Improvement")
    good_feedback = """
**1. COLLABORATION (7.5 pts): Met** - Good partnership building and collaborative approach shown
**2. EVOCATION (7.5 pts): Partially Met** - Some good questions asked, could explore motivations more
**3. ACCEPTANCE (7.5 pts): Met** - Respected patient autonomy throughout the conversation
**4. COMPASSION (7.5 pts): Partially Met** - Generally warm, though empathy could be enhanced
"""
    demonstrate_scenario("Good Performance", good_feedback)
    
    # Scenario 3: Moderate Effort
    print_separator("Scenario 3: Moderate Effort - Shows Leniency")
    moderate_feedback = """
**1. COLLABORATION (7.5 pts): Partially Met** - Attempted partnership building with patient
**2. EVOCATION (7.5 pts): Partially Met** - Asked some questions about patient's perspective
**3. ACCEPTANCE (7.5 pts): Partially Met** - Generally respectful of patient choices
**4. COMPASSION (7.5 pts): Partially Met** - Showed some warmth and attempted to be supportive
"""
    demonstrate_scenario("Moderate Effort", moderate_feedback)
    
    # Scenario 4: Struggling Student
    print_separator("Scenario 4: Struggling Student - Significant Help")
    struggling_feedback = """
**1. COLLABORATION (7.5 pts): Partially Met** - Made some effort to involve the patient in decisions
**2. EVOCATION (7.5 pts): Not Met** - Mostly told patient information rather than exploring their views
**3. ACCEPTANCE (7.5 pts): Partially Met** - Showed some respect for autonomy
**4. COMPASSION (7.5 pts): Not Met** - Approach felt somewhat clinical and distant
"""
    demonstrate_scenario("Struggling Student", struggling_feedback)
    
    # Summary
    print_separator("KEY BENEFITS")
    print("""
✅ More Lenient Scoring:
   • Students showing effort get bonus points (up to 3 points)
   • Longer, more thoughtful responses rewarded (up to 5% multiplier)
   
✅ Encourages Retries:
   • Each retry attempt gets additional 0.5 point bonus
   • Helps students learn from mistakes
   
✅ Clean UI:
   • Users only see final score out of 30
   • Internal calculations remain hidden
   
✅ Always Capped:
   • Maximum score is always 30.0 points
   • No score can exceed the limit
   
✅ Backwards Compatible:
   • Existing code works without changes
   • Internal tracking opt-in only
""")
    
    print_separator("END OF DEMONSTRATION")


if __name__ == "__main__":
    main()
