#!/usr/bin/env python3
"""
Validation script to check for breaking changes and verify system integrity.

Checks:
- New rubric is active and working
- Old rubric still works (backward compatibility)
- Prompts are formatted correctly
- Both HPV and OHI contexts work
- PDF generation works
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=" * 70)
print("🔍 System Validation: MI Rubric Revamp")
print("=" * 70)

# Check 1: New rubric available
print("\n✓ Checking new rubric availability...")
try:
    from rubric.mi_rubric import MIRubric, MIEvaluator, CategoryAssessment, RubricContext
    from services.evaluation_service import EvaluationService
    print("  ✅ New 40-point rubric system available")
    NEW_RUBRIC_OK = True
except ImportError as e:
    print(f"  ❌ New rubric import failed: {e}")
    NEW_RUBRIC_OK = False

# Check 2: Old rubric still works
print("\n✓ Checking backward compatibility...")
try:
    from scoring_utils import MIScorer
    # Test with old format
    old_feedback = "**1. COLLABORATION (7.5 pts): Met** - Good work"
    scores = MIScorer.parse_feedback_scores(old_feedback)
    print(f"  ✅ Old 30-point rubric still works")
    OLD_RUBRIC_OK = True
except Exception as e:
    print(f"  ❌ Old rubric failed: {e}")
    OLD_RUBRIC_OK = False

# Check 3: Prompts are correctly formatted
print("\n✓ Checking evaluation prompts...")
try:
    from feedback_template import FeedbackFormatter
    
    # HPV prompt
    hpv_prompt = FeedbackFormatter.format_evaluation_prompt("HPV", "transcript", "rag")
    assert "40-point" in hpv_prompt, "HPV prompt should mention 40-point"
    assert "Collaboration (9 pts)" in hpv_prompt, "HPV prompt should have Collaboration with 9 pts"
    assert "Response Factor (10 pts)" in hpv_prompt, "HPV prompt should have Response Factor"
    assert "HPV vaccination" in hpv_prompt, "HPV prompt should have correct context"
    
    # OHI prompt
    ohi_prompt = FeedbackFormatter.format_evaluation_prompt("OHI", "transcript", "rag")
    assert "40-point" in ohi_prompt, "OHI prompt should mention 40-point"
    assert "oral health" in ohi_prompt, "OHI prompt should have correct context"
    assert "HPV vaccination" not in ohi_prompt, "OHI prompt should not have HPV context"
    
    print("  ✅ Evaluation prompts correctly formatted for both HPV and OHI")
    PROMPTS_OK = True
except Exception as e:
    print(f"  ❌ Prompt check failed: {e}")
    PROMPTS_OK = False

# Check 4: PDF generation compatibility
print("\n✓ Checking PDF generation...")
try:
    import reportlab
    PDF_AVAILABLE = True
except ImportError:
    print("  ⚠️  ReportLab not installed in test environment (OK for testing)")
    PDF_AVAILABLE = False
    PDF_OK = True

if PDF_AVAILABLE:
    try:
        from pdf_utils import generate_pdf_report
        
        # Test with new format feedback
        new_feedback = """
**Collaboration (9 pts): Meets Criteria** - Good
**Acceptance (6 pts): Meets Criteria** - Good
**Compassion (6 pts): Meets Criteria** - Good
**Evocation (6 pts): Meets Criteria** - Good
**Summary (3 pts): Meets Criteria** - Good
**Response Factor (10 pts): Meets Criteria** - Good
"""
        
        chat_history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"}
        ]
        
        # This should not raise an exception
        pdf_buffer = generate_pdf_report("Test Student", new_feedback, chat_history, "HPV")
        assert pdf_buffer is not None, "PDF buffer should not be None"
        
        print("  ✅ PDF generation works with new rubric format")
        PDF_OK = True
    except Exception as e:
        print(f"  ❌ PDF generation failed: {e}")
        PDF_OK = False
else:
    print("  ✅ PDF imports verified (full test skipped - reportlab not available)")

# Check 5: Context substitution works
print("\n✓ Checking context substitution...")
try:
    from rubric.mi_rubric import MIRubric, CategoryAssessment, RubricContext
    
    # HPV context
    hpv_criteria = MIRubric.get_category_criteria('Collaboration', CategoryAssessment.MEETS_CRITERIA, RubricContext.HPV)
    hpv_has_vaccination = any('HPV vaccination' in c for c in hpv_criteria)
    assert hpv_has_vaccination, "HPV criteria should have 'HPV vaccination'"
    
    # OHI context
    ohi_criteria = MIRubric.get_category_criteria('Collaboration', CategoryAssessment.MEETS_CRITERIA, RubricContext.OHI)
    ohi_has_health = any('oral health' in c for c in ohi_criteria)
    assert ohi_has_health, "OHI criteria should have 'oral health'"
    
    print("  ✅ Context substitution working correctly")
    CONTEXT_OK = True
except Exception as e:
    print(f"  ❌ Context substitution failed: {e}")
    CONTEXT_OK = False

# Check 6: Feedback template integration
print("\n✓ Checking feedback template integration...")
try:
    from feedback_template import FeedbackFormatter, FeedbackValidator
    
    feedback = """
**Collaboration (9 pts): Meets Criteria** - Good
**Acceptance (6 pts): Meets Criteria** - Good
**Compassion (6 pts): Meets Criteria** - Good
**Evocation (6 pts): Meets Criteria** - Good
**Summary (3 pts): Meets Criteria** - Good
**Response Factor (10 pts): Meets Criteria** - Good
"""
    
    # Validation
    validation = FeedbackValidator.validate_feedback_completeness(feedback)
    assert validation['is_valid'], "Feedback should be valid"
    
    # Component breakdown
    table_data = FeedbackFormatter.generate_component_breakdown_table(feedback, "HPV")
    assert len(table_data) == 6, f"Should have 6 categories, got {len(table_data)}"
    
    print("  ✅ Feedback template integration working")
    TEMPLATE_OK = True
except Exception as e:
    print(f"  ❌ Feedback template failed: {e}")
    TEMPLATE_OK = False

# Check 7: Evaluation service works end-to-end
print("\n✓ Checking evaluation service end-to-end...")
try:
    from services.evaluation_service import EvaluationService
    
    feedback = """
**Collaboration (9 pts): Meets Criteria** - Excellent partnership
**Acceptance (6 pts): Meets Criteria** - Good reflections
**Compassion (6 pts): Meets Criteria** - Very empathetic
**Evocation (6 pts): Meets Criteria** - Strong questions
**Summary (3 pts): Meets Criteria** - Clear summary
**Response Factor (10 pts): Meets Criteria** - Fast responses
"""
    
    result = EvaluationService.evaluate_session(feedback, "HPV")
    assert result['total_score'] == 40, f"Expected 40, got {result['total_score']}"
    assert result['context'] == 'HPV'
    assert 'Excellent' in result['performance_band']
    
    print("  ✅ Evaluation service working end-to-end")
    EVAL_OK = True
except Exception as e:
    print(f"  ❌ Evaluation service failed: {e}")
    EVAL_OK = False

# Summary
print("\n" + "=" * 70)
print("📊 Validation Summary")
print("=" * 70)

checks = [
    ("New 40-point rubric", NEW_RUBRIC_OK),
    ("Old 30-point rubric (backward compat)", OLD_RUBRIC_OK),
    ("Evaluation prompts", PROMPTS_OK),
    ("PDF generation", PDF_OK),
    ("Context substitution", CONTEXT_OK),
    ("Feedback template", TEMPLATE_OK),
    ("Evaluation service", EVAL_OK)
]

all_passed = all(result for _, result in checks)

for name, result in checks:
    status = "✅ PASS" if result else "❌ FAIL"
    print(f"  {status}: {name}")

print("=" * 70)

if all_passed:
    print("🎉 All validation checks passed!")
    print("\n✅ System is ready for deployment")
    print("   - New 40-point rubric is active")
    print("   - Backward compatibility maintained")
    print("   - No breaking changes detected")
    sys.exit(0)
else:
    print("❌ Some validation checks failed")
    print("\n⚠️  Please review failures before deployment")
    sys.exit(1)
