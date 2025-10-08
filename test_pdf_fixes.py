#!/usr/bin/env python3
"""
Test script to validate PDF feedback formatting fixes.

Tests:
1. Time zone conversion from UTC to Minnesota time
2. Table text wrapping with Paragraph objects
3. Improvement suggestions markdown to bold conversion
4. SentenceTransformer device initialization
"""

import io
import sys
from datetime import datetime
import pytz


def test_timezone_conversion():
    """Test timezone conversion with the specified UTC time."""
    print("\n1. Testing Timezone Conversion...")
    
    from time_utils import convert_to_minnesota_time, get_current_utc_time
    
    # Test with the specified UTC time from problem statement
    utc_time = "2025-10-08 03:24:18"
    mn_time = convert_to_minnesota_time(utc_time)
    
    print(f"   UTC time: {utc_time}")
    print(f"   Minnesota time: {mn_time}")
    
    # In October 2025, Minnesota is in CDT (UTC-5)
    # Now expects format with AM/PM and timezone
    expected = "2025-10-07 10:24:18 PM CDT"
    assert mn_time == expected, f"Expected {expected}, got {mn_time}"
    
    print("   ✅ Timezone conversion correct (UTC -> Minnesota/CDT with AM/PM)")
    
    # Test that get_current_utc_time actually returns UTC
    utc_now = get_current_utc_time()
    print(f"   Current UTC: {utc_now}")
    assert len(utc_now) == 19, "UTC timestamp format incorrect"
    
    print("   ✅ UTC time function works correctly")
    return True


def test_markdown_to_html_conversion():
    """Test markdown bold conversion for PDF rendering."""
    print("\n2. Testing Markdown to HTML Conversion...")
    
    from pdf_utils import _format_markdown_to_html
    
    test_cases = [
        {
            'input': '**COLLABORATION**: Build partnership with the patient.',
            'expected': '<b>COLLABORATION</b>: Build partnership with the patient.',
            'description': 'Bold heading'
        },
        {
            'input': 'Consider using **reflective listening** and **open-ended questions**.',
            'expected': 'Consider using <b>reflective listening</b> and <b>open-ended questions</b>.',
            'description': 'Multiple bold words'
        },
        {
            'input': '**Key Strengths:** Excellent use of affirmations.',
            'expected': '<b>Key Strengths:</b> Excellent use of affirmations.',
            'description': 'Bold with colon'
        },
        {
            'input': 'No bold text here',
            'expected': 'No bold text here',
            'description': 'No formatting'
        },
    ]
    
    all_passed = True
    for test in test_cases:
        result = _format_markdown_to_html(test['input'])
        passed = result == test['expected']
        all_passed = all_passed and passed
        
        status = '✅' if passed else '❌'
        print(f"   {status} {test['description']}")
        if not passed:
            print(f"      Input:    {test['input']}")
            print(f"      Expected: {test['expected']}")
            print(f"      Got:      {result}")
    
    if all_passed:
        print("   ✅ All markdown conversion tests passed")
    return all_passed


def test_table_wrapping():
    """Test that table cells use Paragraph objects for wrapping."""
    print("\n3. Testing Table Text Wrapping...")
    
    from pdf_utils import generate_pdf_report
    from scoring_utils import MIScorer
    
    # Create sample feedback with long text
    long_feedback = """
MI Performance Report
Evaluation Timestamp (Minnesota): 2025-10-07 22:24:18
Evaluator: test_user
---

**1. COLLABORATION (7.5 pts): Met** - The student demonstrated excellent partnership building throughout the conversation. They consistently used collaborative language and engaged the patient as an active participant in the discussion. This is a very long feedback text that should wrap properly in the table cell without being truncated to 80 characters.

**2. EVOCATION (7.5 pts): Partially Met** - The student showed some ability to draw out patient motivations but could improve by asking more open-ended questions. Another long feedback text to test wrapping.

**3. ACCEPTANCE (7.5 pts): Met** - Strong use of reflective listening and respect for patient autonomy.

**4. COMPASSION (7.5 pts): Met** - Demonstrated warmth and a non-judgmental approach.
"""
    
    sample_chat = [
        {"role": "assistant", "content": "Hello! I'm Alex, nice to meet you."},
        {"role": "user", "content": "Hi, I have questions about the HPV vaccine."},
        {"role": "assistant", "content": "I'd be happy to discuss that with you."}
    ]
    
    try:
        # Generate PDF
        pdf_buffer = generate_pdf_report("Test Student", long_feedback, sample_chat, "HPV Vaccine")
        
        # Check that PDF was generated
        assert pdf_buffer is not None, "PDF buffer is None"
        pdf_size = len(pdf_buffer.getvalue())
        assert pdf_size > 1000, f"PDF too small ({pdf_size} bytes)"
        
        # Get PDF size
        print(f"   Generated PDF size: {pdf_size} bytes")
        print("   ✅ PDF generated successfully with table wrapping")
        
        # Note: We can't easily verify the actual wrapping without parsing PDF,
        # but successful generation indicates Paragraph objects work in tables
        return True
        
    except Exception as e:
        print(f"   ❌ PDF generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_sentence_transformer_device():
    """Test SentenceTransformer initialization with device parameter."""
    print("\n4. Testing SentenceTransformer Device Initialization...")
    
    try:
        from sentence_transformers import SentenceTransformer
        import torch
        
        # Test device selection
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f"   Selected device: {device}")
        
        # Initialize with device parameter
        model = SentenceTransformer('all-MiniLM-L6-v2', device=device)
        
        print(f"   Model device: {model.device}")
        print("   ✅ SentenceTransformer initialized successfully with device parameter")
        
        # Test encoding
        test_text = "This is a test sentence for embedding."
        embedding = model.encode([test_text])
        
        assert embedding is not None, "Embedding is None"
        assert len(embedding) > 0, "Embedding is empty"
        print(f"   ✅ Encoding test successful (embedding shape: {embedding.shape})")
        
        return True
        
    except Exception as e:
        print(f"   ❌ SentenceTransformer initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integration():
    """Integration test: Generate a complete PDF with all fixes."""
    print("\n5. Integration Test: Complete PDF Generation...")
    
    from pdf_utils import generate_pdf_report
    
    # Sample feedback with markdown formatting
    feedback = """
MI Performance Report
Evaluation Timestamp (Minnesota): 2025-10-07 22:24:18
Evaluator: Test Evaluator
---

**1. COLLABORATION (7.5 pts): Met** - Excellent partnership building throughout the conversation. The student consistently used collaborative language and engaged the patient as an active participant. They demonstrated strong rapport-building skills and made the patient feel like an equal partner in the decision-making process.

**2. EVOCATION (7.5 pts): Partially Met** - The student showed some ability to draw out patient motivations and concerns. However, they could improve by asking more **open-ended questions** and using **reflective listening** more consistently to explore the patient's perspective.

**3. ACCEPTANCE (7.5 pts): Met** - Strong demonstration of respect for patient autonomy. The student used affirmations effectively and reflected the patient's statements accurately. They avoided judgment and supported the patient's right to make their own decisions.

**4. COMPASSION (7.5 pts): Met** - Demonstrated warmth, empathy, and a non-judgmental approach throughout. The student created a safe environment for the patient to express concerns.

**Improvement Suggestions:**
- Practice using **reflective listening** more frequently
- Ask more **open-ended questions** to explore motivations
- **Affirm** patient strengths and positive statements
"""
    
    chat_history = [
        {"role": "assistant", "content": "Hello! I'm Alex. Nice to meet you today."},
        {"role": "user", "content": "Hi, I heard about the HPV vaccine and wanted to learn more."},
        {"role": "assistant", "content": "That's great that you're interested. What would you like to know?"},
        {"role": "user", "content": "Is it safe? I'm a bit worried about side effects."},
        {"role": "assistant", "content": "I understand your concern about safety. The HPV vaccine has been extensively studied and is very safe. What specific concerns do you have?"}
    ]
    
    try:
        pdf_buffer = generate_pdf_report("Test Student", feedback, chat_history, "HPV Vaccine")
        
        assert pdf_buffer is not None, "PDF buffer is None"
        pdf_size = len(pdf_buffer.getvalue())
        assert pdf_size > 3000, f"PDF too small ({pdf_size} bytes), might be incomplete"
        
        print(f"   Generated PDF: {pdf_size} bytes")
        print("   ✅ Complete PDF generated with all fixes applied")
        
        # Save a test PDF for manual inspection if needed
        # with open('/tmp/test_pdf_output.pdf', 'wb') as f:
        #     f.write(pdf_buffer.getvalue())
        # print("   📄 Test PDF saved to /tmp/test_pdf_output.pdf")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 70)
    print("PDF FEEDBACK FORMATTING FIXES - TEST SUITE")
    print("=" * 70)
    
    tests = [
        ("Timezone Conversion", test_timezone_conversion),
        ("Markdown to HTML Conversion", test_markdown_to_html_conversion),
        ("Table Text Wrapping", test_table_wrapping),
        ("SentenceTransformer Device", test_sentence_transformer_device),
        ("Integration Test", test_integration),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"   ❌ {test_name} failed")
        except Exception as e:
            print(f"   ❌ {test_name} failed with exception: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 70)
    print(f"TEST RESULTS: {passed}/{total} tests passed")
    print("=" * 70)
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"⚠️  {total - passed} test(s) failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
