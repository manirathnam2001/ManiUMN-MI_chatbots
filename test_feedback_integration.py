#!/usr/bin/env python3
"""
Integration test to verify the complete feedback flow works correctly.
Simulates the actual flow in HPV.py and OHI.py.
"""

from feedback_template import FeedbackFormatter


def test_hpv_feedback_flow():
    """Test the complete HPV feedback flow."""
    print("\nTesting HPV feedback flow...")
    
    # Simulated AI-generated feedback
    ai_feedback = """**1. COLLABORATION (7.5 pts): Met** - Student demonstrated excellent partnership building by starting with open-ended questions like "What brings you in today?" and actively listening to Alex's concerns. They created a collaborative environment throughout the conversation.

**2. EVOCATION (7.5 pts): Partially Met** - Good exploration of motivations with questions like "What are your thoughts about the HPV vaccine?" However, could have gone deeper into exploring Alex's specific values and concerns about health decisions.

**3. ACCEPTANCE (7.5 pts): Met** - Strong respect for autonomy shown by not pushing for immediate decision. Used reflective listening effectively: "It sounds like you want to make an informed decision." Affirmed Alex's desire to learn more.

**4. COMPASSION (7.5 pts): Met** - Demonstrated warmth and non-judgmental approach throughout. Avoided scare tactics and maintained an empathetic tone even when discussing vaccine benefits."""
    
    timestamp = "2025-01-06 14:30:00"
    evaluator = "manirathnam2001"
    
    # Step 1: Display feedback (what the app shows)
    print("\n  Step 1: Display feedback in app")
    display_output = FeedbackFormatter.format_feedback_for_display(ai_feedback, timestamp, evaluator)
    
    assert "**1. COLLABORATION" in display_output, "Display should contain collaboration feedback"
    assert "MI Performance Report" not in display_output, "Display should NOT contain header"
    assert "Evaluation Timestamp" not in display_output, "Display should NOT contain timestamp"
    assert "Evaluator:" not in display_output, "Display should NOT contain evaluator"
    print(f"    ✅ App display shows only core feedback (no headers)")
    print(f"    Preview: {display_output[:120]}...")
    
    # Step 2: Format for PDF (what gets downloaded)
    print("\n  Step 2: Format feedback for PDF download")
    pdf_output = FeedbackFormatter.format_feedback_for_pdf(ai_feedback, timestamp, evaluator)
    
    assert "MI Performance Report" in pdf_output, "PDF should contain header"
    assert "Evaluation Timestamp (Minnesota):" in pdf_output, "PDF should contain timestamp"
    assert f"Evaluator: {evaluator}" in pdf_output, "PDF should contain evaluator"
    assert "**1. COLLABORATION" in pdf_output, "PDF should contain feedback content"
    print(f"    ✅ PDF includes full headers and metadata")
    print(f"    Preview: {pdf_output[:180]}...")
    
    return True


def test_ohi_feedback_flow():
    """Test the complete OHI feedback flow."""
    print("\nTesting OHI feedback flow...")
    
    # Simulated AI-generated feedback (different format without bold)
    ai_feedback = """1. COLLABORATION (7.5 pts): Met - Student established good rapport by greeting Diana warmly and asking about her current oral health routine without judgment.

2. EVOCATION (7.5 pts): Met - Effectively explored Diana's motivations and concerns about dental care using open-ended questions and reflective listening.

3. ACCEPTANCE (7.5 pts): Partially Met - Showed respect for autonomy but could have used more reflective statements to demonstrate deeper understanding of Diana's perspective.

4. COMPASSION (7.5 pts): Met - Maintained a warm, non-judgmental tone throughout and acknowledged Diana's efforts to maintain her dental health."""
    
    timestamp = "2025-01-06 15:00:00"
    evaluator = "manirathnam2001"
    
    # Step 1: Display feedback
    print("\n  Step 1: Display feedback in app")
    display_output = FeedbackFormatter.format_feedback_for_display(ai_feedback, timestamp, evaluator)
    
    assert "1. COLLABORATION" in display_output, "Display should contain collaboration feedback"
    assert "MI Performance Report" not in display_output, "Display should NOT contain header"
    print(f"    ✅ App display shows only core feedback")
    
    # Step 2: Format for PDF
    print("\n  Step 2: Format feedback for PDF download")
    pdf_output = FeedbackFormatter.format_feedback_for_pdf(ai_feedback, timestamp, evaluator)
    
    assert "MI Performance Report" in pdf_output, "PDF should contain header"
    assert "1. COLLABORATION" in pdf_output, "PDF should contain feedback content"
    print(f"    ✅ PDF includes full headers and metadata")
    
    return True


def test_persistence_across_sessions():
    """Test that feedback can be redisplayed correctly (simulating session state)."""
    print("\nTesting feedback persistence across sessions...")
    
    # Original feedback
    feedback_content = """**1. COLLABORATION (7.5 pts): Met** - Good rapport building.
**2. EVOCATION (7.5 pts): Met** - Effective motivation exploration."""
    
    timestamp = "2025-01-06 14:30:00"
    evaluator = "manirathnam2001"
    
    # First display
    display1 = FeedbackFormatter.format_feedback_for_display(feedback_content, timestamp, evaluator)
    
    # Simulated: User downloads PDF (feedback should persist)
    pdf = FeedbackFormatter.format_feedback_for_pdf(feedback_content, timestamp, evaluator)
    
    # Second display (after PDF download)
    display2 = FeedbackFormatter.format_feedback_for_display(feedback_content, timestamp, evaluator)
    
    # Both displays should be identical
    assert display1 == display2, "Feedback should display consistently"
    assert "MI Performance Report" not in display1, "Display should not have headers"
    assert "MI Performance Report" not in display2, "Display should not have headers after PDF download"
    
    print(f"    ✅ Feedback displays consistently before and after PDF download")
    return True


def main():
    """Run all integration tests."""
    print("🧪 Testing Complete Feedback Flow Integration\n")
    
    tests = [
        ("HPV Feedback Flow", test_hpv_feedback_flow),
        ("OHI Feedback Flow", test_ohi_feedback_flow),
        ("Feedback Persistence", test_persistence_across_sessions),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Testing {test_name}:")
        try:
            if test_func():
                passed += 1
                print(f"  ✅ {test_name} passed")
            else:
                print(f"  ❌ {test_name} failed")
        except Exception as e:
            print(f"  ❌ {test_name} failed with error: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All integration tests passed! Feedback flow is working correctly.")
        return 0
    else:
        print(f"⚠️  {total - passed} tests failed.")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
