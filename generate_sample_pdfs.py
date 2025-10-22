#!/usr/bin/env python3
"""
Generate sample PDFs to verify visual output with new 40-point rubric.
This creates actual PDF files that can be manually inspected.
"""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pdf_utils import generate_pdf_report
from services.evaluation_service import EvaluationService


def generate_sample_hpv_pdf():
    """Generate a sample HPV PDF with new rubric."""
    print("🔬 Generating Sample HPV PDF...")
    
    feedback = """
Evaluation Timestamp (Minnesota): 2025-01-15 14:30:00 CST

**Collaboration (9 pts): Meets Criteria** - The student introduced themselves warmly and effectively collaborated with the patient about HPV vaccination. They used inclusive language ("Let's explore this together") and created a true partnership atmosphere. Did not lecture or try to "fix" the patient's concerns.

**Acceptance (6 pts): Meets Criteria** - The student asked permission before discussing HPV vaccination details ("Would it be okay if we talked about the vaccine?"). They demonstrated excellent reflective listening with statements like "It sounds like you're concerned about side effects."

**Compassion (6 pts): Needs Improvement** - While the student was generally polite, they did not fully explore the patient's deeper concerns about HPV vaccination. Some responses felt rushed, and the student could have shown more empathy when the patient expressed hesitation.

**Evocation (6 pts): Meets Criteria** - Excellent use of open-ended questions: "What are your thoughts about HPV vaccination?" and "What would getting the vaccine mean for you?" The student supported autonomy by saying "This is your decision to make" and rolled with resistance appropriately.

**Summary (3 pts): Needs Improvement** - The student did not provide a clear summary of the discussion or check for accuracy of information. They missed an opportunity to reflect back what was discussed and confirm next steps.

**Response Factor (10 pts): Meets Criteria** - The chatbot provided fast, intuitive responses throughout the conversation. Average response time was under 2 seconds, showing good understanding and engagement.

**Overall Assessment:** Strong MI performance with minor areas for growth. The student demonstrated excellent collaboration, acceptance, and evocation skills. Focus areas for improvement include showing more compassion and providing comprehensive summaries. With practice in these areas, the student shows great potential for mastering MI techniques.
"""
    
    chat_history = [
        {"role": "assistant", "content": "Hi, I'm here for my appointment. I got a message about the HPV vaccine?"},
        {"role": "user", "content": "Hello! Yes, thanks for coming in. Would it be okay if we talked about the HPV vaccine today?"},
        {"role": "assistant", "content": "I guess so, but I'm not sure I want it. I've heard some things that worry me."},
        {"role": "user", "content": "I understand your concern. Can you tell me more about what worries you?"},
        {"role": "assistant", "content": "Well, I've heard it has side effects. And I'm not sure if it's really necessary for me."},
        {"role": "user", "content": "Those concerns are completely valid. What have you heard about side effects that concerns you the most?"},
        {"role": "assistant", "content": "Some people said they felt sick after getting it, and I have finals coming up."},
        {"role": "user", "content": "It sounds like you're worried about how it might affect your ability to study for finals. What would getting the vaccine mean for you right now?"},
        {"role": "assistant", "content": "I guess I'd rather wait until after finals if I decide to get it."},
        {"role": "user", "content": "That makes sense. This is your decision to make. Would you like to schedule a time after finals to discuss it more?"}
    ]
    
    pdf_buffer = generate_pdf_report(
        student_name="Alex Johnson",
        raw_feedback=feedback,
        chat_history=chat_history,
        session_type="HPV Vaccine"
    )
    
    # Save to file
    filename = f"sample_hpv_new_rubric_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    with open(filename, 'wb') as f:
        f.write(pdf_buffer.getvalue())
    
    # Get evaluation data for display
    result = EvaluationService.evaluate_session(feedback, "HPV Vaccine")
    
    print(f"✅ HPV PDF Generated: {filename}")
    print(f"   Total Score: {result['total_score']}/40 ({result['percentage']}%)")
    print(f"   Performance: {result['performance_band']}")
    print(f"   File Size: {os.path.getsize(filename)} bytes")
    print()
    return filename


def generate_sample_ohi_pdf():
    """Generate a sample OHI PDF with new rubric."""
    print("🔬 Generating Sample OHI PDF...")
    
    feedback = """
Evaluation Timestamp (Minnesota): 2025-01-15 15:45:00 CST

**Collaboration (9 pts): Meets Criteria** - The student introduced themselves professionally and built excellent partnership with the patient around oral health changes. They used collaborative language throughout and never lectured or tried to "fix" the patient.

**Acceptance (6 pts): Meets Criteria** - The student asked permission before discussing oral health information and consistently used reflective listening. Example: "It sounds like you feel brushing is time-consuming."

**Compassion (6 pts): Meets Criteria** - Excellent demonstration of empathy and understanding regarding the patient's oral health struggles. The student validated feelings without judgment and showed genuine care for the patient's wellbeing.

**Evocation (6 pts): Meets Criteria** - Strong use of open-ended questions to understand the patient's stage of change and elicit change talk about oral health. The student supported self-efficacy and emphasized patient autonomy throughout.

**Summary (3 pts): Meets Criteria** - The student provided a clear summary at the end: "So we've talked about the challenges you face with brushing and some ideas that might work for you. What feels like a good next step?" This reflected the big picture and checked accuracy.

**Response Factor (10 pts): Meets Criteria** - Maintained excellent response time with fast, intuitive replies. The conversation flowed naturally with appropriate pacing.

**Overall Assessment:** Excellent MI skills demonstrated. The student showed mastery across all MI spirit components with particular strength in compassion and evocation. This performance demonstrates readiness to apply MI techniques in clinical settings.
"""
    
    chat_history = [
        {"role": "assistant", "content": "Hi, I know I should brush my teeth more, but it's hard for me."},
        {"role": "user", "content": "Thanks for sharing that with me. Can you tell me more about what makes it hard?"},
        {"role": "assistant", "content": "I'm just so busy, and by the time I get to bed, I'm too tired."},
        {"role": "user", "content": "It sounds like you feel brushing is time-consuming, especially when you're tired. What have you tried before?"},
        {"role": "assistant", "content": "I used to brush in the morning, but I rush out the door for work."},
        {"role": "user", "content": "So mornings are rushed. What would need to change for brushing to fit into your routine?"},
        {"role": "assistant", "content": "Maybe if I could find a time that doesn't feel rushed..."},
        {"role": "user", "content": "That's a great insight. What time during the day feels less rushed for you?"},
        {"role": "assistant", "content": "Actually, right after dinner might work. I usually have a few minutes then."},
        {"role": "user", "content": "That sounds like a plan you came up with that could work for you. So we've talked about the challenges you face with brushing and some ideas that might work for you. What feels like a good next step?"}
    ]
    
    pdf_buffer = generate_pdf_report(
        student_name="Morgan Smith",
        raw_feedback=feedback,
        chat_history=chat_history,
        session_type="OHI"
    )
    
    # Save to file
    filename = f"sample_ohi_new_rubric_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    with open(filename, 'wb') as f:
        f.write(pdf_buffer.getvalue())
    
    # Get evaluation data for display
    result = EvaluationService.evaluate_session(feedback, "OHI")
    
    print(f"✅ OHI PDF Generated: {filename}")
    print(f"   Total Score: {result['total_score']}/40 ({result['percentage']}%)")
    print(f"   Performance: {result['performance_band']}")
    print(f"   File Size: {os.path.getsize(filename)} bytes")
    print()
    return filename


def generate_perfect_score_pdf():
    """Generate a PDF with perfect score to test all categories at max points."""
    print("🔬 Generating Perfect Score PDF...")
    
    feedback = """
**Collaboration (9 pts): Meets Criteria** - Perfect collaboration demonstrated.
**Acceptance (6 pts): Meets Criteria** - Perfect acceptance demonstrated.
**Compassion (6 pts): Meets Criteria** - Perfect compassion demonstrated.
**Evocation (6 pts): Meets Criteria** - Perfect evocation demonstrated.
**Summary (3 pts): Meets Criteria** - Perfect summary provided.
**Response Factor (10 pts): Meets Criteria** - Perfect response timing.
"""
    
    chat_history = [
        {"role": "user", "content": "Perfect conversation example."}
    ]
    
    pdf_buffer = generate_pdf_report(
        student_name="Perfect Student",
        raw_feedback=feedback,
        chat_history=chat_history,
        session_type="HPV"
    )
    
    filename = f"sample_perfect_score_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    with open(filename, 'wb') as f:
        f.write(pdf_buffer.getvalue())
    
    result = EvaluationService.evaluate_session(feedback, "HPV")
    
    print(f"✅ Perfect Score PDF Generated: {filename}")
    print(f"   Total Score: {result['total_score']}/40 (100%)")
    print(f"   All categories: Meets Criteria")
    print()
    return filename


def main():
    """Generate all sample PDFs."""
    print("=" * 70)
    print("📄 Generating Sample PDFs - New 40-Point MI Rubric")
    print("=" * 70)
    print()
    
    files_generated = []
    
    try:
        # Generate HPV sample
        hpv_file = generate_sample_hpv_pdf()
        files_generated.append(hpv_file)
        
        # Generate OHI sample
        ohi_file = generate_sample_ohi_pdf()
        files_generated.append(ohi_file)
        
        # Generate perfect score
        perfect_file = generate_perfect_score_pdf()
        files_generated.append(perfect_file)
        
        print("=" * 70)
        print("✅ Sample PDFs Generated Successfully")
        print("=" * 70)
        print("\nGenerated Files:")
        for f in files_generated:
            print(f"  📄 {f}")
        
        print("\n📝 Manual Verification Checklist:")
        print("  1. Open each PDF and verify it displays correctly")
        print("  2. Check that total score shows X/40 (not X/30)")
        print("  3. Verify 6 categories are shown (not 4)")
        print("  4. Confirm category names: Collaboration, Acceptance, Compassion,")
        print("     Evocation, Summary, Response Factor")
        print("  5. Check max points: 9, 6, 6, 6, 3, 10 respectively")
        print("  6. Verify 'Meets Criteria' or 'Needs Improvement' labels")
        print("  7. Confirm performance band text appears in total row")
        print("  8. Verify HPV PDF uses 'HPV vaccination' in context")
        print("  9. Verify OHI PDF uses 'oral health' in context")
        print("  10. Ensure overall layout/styling is unchanged from before")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error generating PDFs: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
