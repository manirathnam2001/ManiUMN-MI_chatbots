#!/usr/bin/env python3
"""
Integration test demonstrating the complete internal scoring workflow.
Shows how engagement and timing metrics boost scores while maintaining 30-point cap.
"""

from scoring_utils import MIScorer, calculate_engagement_metrics
from time_utils import calculate_response_times


def demo_scoring_system():
    """Demonstrate the complete scoring system with realistic examples."""
    
    print("=" * 70)
    print("INTERNAL SCORING MODIFIERS - COMPLETE DEMO")
    print("=" * 70)
    
    # Realistic feedback from AI evaluator
    feedback = """
**1. COLLABORATION (7.5 pts): Partially Met** - You demonstrated partnership by asking permission and involving the patient in decisions. However, you could improve by checking for understanding more frequently and inviting more collaboration on the action plan.

**2. EVOCATION (7.5 pts): Met** - Excellent use of open-ended questions! You effectively elicited the patient's own motivations and concerns. Your questions like "What concerns you most about this?" were particularly effective.

**3. ACCEPTANCE (7.5 pts): Partially Met** - You showed respect for the patient's autonomy and acknowledged their perspective. Consider using more affirmations to reinforce positive behaviors and validate their experiences more explicitly.

**4. COMPASSION (7.5 pts): Partially Met** - Your tone was generally supportive, but you could deepen empathy by reflecting feelings more often. When the patient expressed worry, a simple "That sounds concerning" would have strengthened the connection.
"""
    
    # Simulate a good conversation
    chat_history = [
        {'role': 'assistant', 'content': 'Hello! I\'m Sarah. Thanks for meeting with me today.'},
        {'role': 'user', 'content': 'Hi Sarah, I wanted to talk about my dental health. I know I should floss more, but I just never remember.'},
        {'role': 'assistant', 'content': 'I appreciate you bringing this up. What made you want to discuss this today?'},
        {'role': 'user', 'content': 'Well, my dentist mentioned my gums were bleeding. That worried me. How bad is that?'},
        {'role': 'assistant', 'content': 'That must feel concerning. Tell me more about your current routine?'},
        {'role': 'user', 'content': 'I brush twice a day usually, in the morning and before bed. But flossing... I maybe do it once a week at most. Is that enough?'},
        {'role': 'assistant', 'content': 'It sounds like brushing is already part of your routine. What do you think about the flossing?'},
        {'role': 'user', 'content': 'I know it\'s important. I just forget. When I do remember, I\'m usually too tired. What should I do?'},
        {'role': 'assistant', 'content': 'You mentioned forgetting and being tired. What time of day might work better for you?'},
        {'role': 'user', 'content': 'Maybe in the morning? I have more energy then. But I\'m always rushed. Could I do it after breakfast?'},
    ]
    
    print("\n📊 SCENARIO: Good Student Performance")
    print("-" * 70)
    
    # Calculate metrics
    engagement = calculate_engagement_metrics(chat_history)
    time_metrics = calculate_response_times(chat_history)
    
    print(f"\n🎯 Engagement Metrics (Hidden from Student):")
    print(f"   • Turn Count: {engagement['turn_count']}")
    print(f"   • Avg Message Length: {engagement['avg_message_length']:.0f} characters")
    print(f"   • Questions Asked: {engagement['question_count']}")
    
    print(f"\n⏱️  Time Metrics (Hidden from Student):")
    print(f"   • Avg Response Time: {time_metrics['avg_response_time']:.1f} seconds")
    print(f"   • Total Conversation Time: {time_metrics['total_time']:.0f} seconds")
    
    # Get score breakdown WITHOUT modifiers (old system)
    print("\n🔴 OLD SYSTEM (Without Internal Modifiers):")
    breakdown_old = MIScorer.get_score_breakdown(feedback)
    base = breakdown_old['_internal']['base_score']
    print(f"   Base Score: {base:.1f}/30.0")
    print(f"   Final Score: {base:.1f}/30.0 ({base/30*100:.1f}%)")
    print(f"   ⚠️  Note: With old 0.5 multiplier, this would have been {base/0.6*0.5:.1f}/30.0")
    
    # Get score breakdown WITH modifiers (new system)
    print("\n🟢 NEW SYSTEM (With Internal Modifiers):")
    breakdown_new = MIScorer.get_score_breakdown(
        feedback,
        engagement_metrics=engagement,
        time_metrics=time_metrics
    )
    
    internal = breakdown_new['_internal']
    print(f"   Base Score: {internal['base_score']:.1f}/30.0")
    print(f"   × Effort Multiplier: {internal['effort_multiplier']:.2f}x (from engagement)")
    print(f"   × Time Multiplier: {internal['time_multiplier']:.2f}x (from timing)")
    print(f"   = Raw Adjusted: {internal['raw_adjusted_score']:.2f}")
    print(f"   → Final Score (capped): {breakdown_new['total_score']:.1f}/30.0 ({breakdown_new['percentage']:.1f}%)")
    
    improvement = breakdown_new['total_score'] - base
    print(f"\n✨ IMPACT: +{improvement:.1f} points from internal modifiers!")
    print(f"   Student sees: {breakdown_new['total_score']:.1f}/30.0")
    print(f"   Internal calculation: Base {internal['base_score']:.1f} × {internal['effort_multiplier']:.2f} × {internal['time_multiplier']:.2f}")
    
    # Show component breakdown
    print("\n📋 Component Breakdown (Shown to Student):")
    for comp, details in breakdown_new['components'].items():
        print(f"   • {comp}: {details['status']} - {details['score']:.1f}/{details['max_score']:.1f} pts")
    
    print("\n" + "=" * 70)
    print("COMPARISON SUMMARY")
    print("=" * 70)
    
    old_multiplier_score = base / 0.6 * 0.5  # What it would have been with 0.5
    print(f"\n📊 Score Progression:")
    print(f"   1. Old System (0.5 multiplier, no modifiers): {old_multiplier_score:.1f}/30.0")
    print(f"   2. New Base (0.6 multiplier, no modifiers):   {base:.1f}/30.0")
    print(f"   3. New Full (0.6 + modifiers):                {breakdown_new['total_score']:.1f}/30.0")
    
    print(f"\n📈 Improvements:")
    print(f"   • Lenient scoring: +{base - old_multiplier_score:.1f} points")
    print(f"   • Internal modifiers: +{breakdown_new['total_score'] - base:.1f} points")
    print(f"   • Total improvement: +{breakdown_new['total_score'] - old_multiplier_score:.1f} points ({(breakdown_new['total_score'] - old_multiplier_score)/old_multiplier_score*100:.1f}%)")
    
    print("\n" + "=" * 70)
    print("KEY BENEFITS")
    print("=" * 70)
    print("\n✅ Maximum score always capped at 30 points")
    print("✅ More lenient base scoring rewards partial achievement")
    print("✅ Effort and engagement are recognized and rewarded")
    print("✅ Good timing and pacing provide additional boost")
    print("✅ Internal mechanics hidden from students")
    print("✅ Fair evaluation considering multiple factors")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    demo_scoring_system()
