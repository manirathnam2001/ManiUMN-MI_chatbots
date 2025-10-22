# MI Rubric Quick Reference

## 🎯 New Rubric at a Glance

### 40-Point Binary System
| Category | Points | Assessment |
|----------|--------|------------|
| Collaboration | 9 | Meets Criteria = 9 pts, Needs Improvement = 0 pts |
| Acceptance | 6 | Meets Criteria = 6 pts, Needs Improvement = 0 pts |
| Compassion | 6 | Meets Criteria = 6 pts, Needs Improvement = 0 pts |
| Evocation | 6 | Meets Criteria = 6 pts, Needs Improvement = 0 pts |
| Summary | 3 | Meets Criteria = 3 pts, Needs Improvement = 0 pts |
| Response Factor | 10 | Meets Criteria = 10 pts, Needs Improvement = 0 pts |
| **TOTAL** | **40** | **No partial credit per category** |

## 🏆 Performance Bands
- **90%+** (36-40 pts): Excellent MI skills demonstrated
- **75%+** (30-35 pts): Strong MI performance with minor areas for growth
- **60%+** (24-29 pts): Satisfactory MI foundation, continue practicing
- **40%+** (16-23 pts): Basic MI awareness, significant practice needed
- **<40%** (0-15 pts): Significant improvement needed in MI techniques

## 🔄 Context Substitution
- **HPV chatbot**: Uses "HPV vaccination" in criteria
- **OHI chatbot**: Uses "oral health" in criteria

## ⚡ Response Factor
- **Threshold**: 2.5 seconds (configurable)
- **Meets Criteria**: Average latency ≤ 2.5s → 10 points
- **Needs Improvement**: Average latency > 2.5s → 0 points

## 📝 LLM Feedback Format
```
**Collaboration (9 pts): Meets Criteria** - [feedback text]
**Acceptance (6 pts): Meets Criteria** - [feedback text]
**Compassion (6 pts): Needs Improvement** - [feedback text]
**Evocation (6 pts): Meets Criteria** - [feedback text]
**Summary (3 pts): Needs Improvement** - [feedback text]
**Response Factor (10 pts): Meets Criteria** - [feedback text]
```

## 🧪 Testing
```bash
# Unit tests (8 tests)
python3 test_mi_rubric.py

# Integration tests (7 tests)
python3 test_integration_mi_rubric.py

# Legacy tests (5 tests)
python3 test_scoring_consistency.py

# System validation (7 checks)
python3 validate_system.py
```

## 📚 Documentation
- **Complete Docs**: `docs/MI_Rubric.md`
- **Implementation Summary**: `RUBRIC_REVAMP_SUMMARY.md`
- **This Quick Reference**: `QUICK_REFERENCE.md`

## 🔧 Configuration
```bash
# Set Response Factor threshold
export RESPONSE_FACTOR_THRESHOLD=2.5
```

## 💻 Code Usage

### Python
```python
from services.evaluation_service import EvaluationService

result = EvaluationService.evaluate_session(
    feedback_text="**Collaboration (9 pts): Meets Criteria** - ...",
    session_type="HPV"
)

print(f"{result['total_score']}/40 - {result['performance_band']}")
```

### PHP
```php
require_once 'src/Service/EvaluationService.php';

$result = EvaluationService::evaluateSession($feedbackText, 'HPV');
echo "{$result['total_score']}/40\n";
```

## ✅ Status
- **Implementation**: Complete
- **Tests**: 27/27 passing (100%)
- **Security**: 0 vulnerabilities
- **Documentation**: Complete
- **Ready**: Production

## 📊 Example Score
**Input**: HPV student evaluation
- Collaboration: ✅ Meets Criteria → 9 pts
- Acceptance: ✅ Meets Criteria → 6 pts
- Compassion: ❌ Needs Improvement → 0 pts
- Evocation: ✅ Meets Criteria → 6 pts
- Summary: ❌ Needs Improvement → 0 pts
- Response Factor: ✅ Meets Criteria → 10 pts

**Output**: 31/40 (77.5%) - Strong MI performance with minor areas for growth

## 🔗 Quick Links
- Full Rubric Details: `docs/MI_Rubric.md`
- Implementation Summary: `RUBRIC_REVAMP_SUMMARY.md`
- Main README: `README.md`
