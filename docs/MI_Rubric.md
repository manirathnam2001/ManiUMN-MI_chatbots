# MI Rubric Documentation

## Overview

The Motivational Interviewing (MI) Rubric has been updated to a **40-point binary assessment system** with 6 distinct categories. This rubric is used consistently across both the **HPV Vaccine** and **Oral Hygiene (OHI)** chatbot experiences to evaluate students' MI skills.

## Rubric Structure

### Total Points: 40

The rubric consists of 6 categories with different point values:

| Category | Points | Weight |
|----------|--------|--------|
| Collaboration | 9 | 22.5% |
| Acceptance | 6 | 15% |
| Compassion | 6 | 15% |
| Evocation | 6 | 15% |
| Summary | 3 | 7.5% |
| Response Factor | 10 | 25% |
| **TOTAL** | **40** | **100%** |

## Binary Scoring Model

Each category uses **binary assessment**:
- **Meets Criteria**: Full category points awarded
- **Needs Improvement**: 0 points awarded

There is **no partial credit** per category.

## Category Descriptions

### 1. Collaboration (9 points)

**Purpose**: Evaluate partnership building and rapport development.

#### Meets Criteria (9 points):
- Introduces self, role, is engaging, welcoming
- Collaborated with the patient by eliciting their ideas for change in {HPV vaccination / oral health} or by providing support as a partnership
- Did not lecture; Did not try to "fix" the patient

#### Needs Improvement (0 points):
- Did not introduce self/role/engaging/welcoming
- Did not collaborate by eliciting patient ideas or provide partnership support
- Lectured or tried to "fix" the patient

---

### 2. Acceptance (6 points)

**Purpose**: Demonstrate respect, autonomy, and reflective listening.

#### Meets Criteria (6 points):
- Asks permission before eliciting accurate information about the {HPV vaccination / oral health}
- Uses reflections to demonstrate listening

#### Needs Improvement (0 points):
- Did not ask permission and/or provided inaccurate information
- Did not use reflections to demonstrate listening

---

### 3. Compassion (6 points)

**Purpose**: Show no judgment, shaming, or belittling.

#### Meets Criteria (6 points):
- Tries to understand the patient's perceptions and/or concerns with the {HPV vaccination / oral health}
- Does not judge, shame or belittle the patient

#### Needs Improvement (0 points):
- Did not try to understand perceptions/concerns
- Judged, shamed or belittled the patient

---

### 4. Evocation (6 points)

**Purpose**: Evoke self-efficacy, confidence, intrinsic motivation; elicit understanding.

#### Meets Criteria (6 points):
- Uses open-ended questions for patient understanding OR stage of change OR eliciting change talk
- Supports self-efficacy; emphasizes patient autonomy regarding the {HPV vaccination / oral health} (rolls with resistance)

#### Needs Improvement (0 points):
- Did not ask open-ended questions
- Did not support self-efficacy/autonomy (did not roll with resistance)

---

### 5. Summary (3 points)

**Purpose**: Provide reflective summarization.

#### Meets Criteria (3 points):
- Reflects big picture; checks accuracy of information and/or next steps

#### Needs Improvement (0 points):
- Does not summarize appropriately

---

### 6. Response Factor (10 points)

**Purpose**: Evaluate timeliness and intuitiveness of responses.

#### Meets Criteria (10 points):
- Fast and intuitive responses to questions probed; acceptable average time throughout conversation

#### Needs Improvement (0 points):
- Delay in understanding and responding

**Implementation Details**:
- **Default Threshold**: 2.5 seconds average response latency
- **Configurable**: Set via `RESPONSE_FACTOR_THRESHOLD` environment variable
- **Automatic**: If response timing data is available, assessment is computed automatically
- **Manual**: Can be manually assessed if timing data is unavailable

---

## Context Substitution

The rubric text adapts based on the chatbot context:

| Context | Substitution Text |
|---------|------------------|
| HPV | "HPV vaccination" |
| OHI | "oral health" |

**Example**:
- HPV: "Collaborated with the patient by eliciting their ideas for change in **HPV vaccination**..."
- OHI: "Collaborated with the patient by eliciting their ideas for change in **oral health**..."

---

## Performance Bands

Overall performance is classified into 5 bands based on percentage:

| Percentage | Band | Message |
|------------|------|---------|
| ≥ 90% | **Excellent** | Excellent MI skills demonstrated |
| ≥ 75% | **Strong** | Strong MI performance with minor areas for growth |
| ≥ 60% | **Satisfactory** | Satisfactory MI foundation, continue practicing |
| ≥ 40% | **Basic** | Basic MI awareness, significant practice needed |
| < 40% | **Needs Significant Improvement** | Significant improvement needed in MI techniques |

---

## Example Evaluation Payloads

### Perfect Score Example (40/40)

```json
{
  "total_score": 40,
  "max_possible_score": 40,
  "percentage": 100.0,
  "performance_band": "Excellent MI skills demonstrated",
  "context": "HPV",
  "categories": {
    "Collaboration": {
      "points": 9,
      "max_points": 9,
      "assessment": "Meets Criteria",
      "criteria_text": [
        "Introduces self, role, is engaging, welcoming",
        "Collaborated with the patient by eliciting their ideas for change in HPV vaccination or by providing support as a partnership",
        "Did not lecture; Did not try to \"fix\" the patient"
      ],
      "notes": "Excellent rapport building throughout the conversation"
    },
    "Acceptance": {
      "points": 6,
      "max_points": 6,
      "assessment": "Meets Criteria",
      "criteria_text": [
        "Asks permission before eliciting accurate information about the HPV vaccination",
        "Uses reflections to demonstrate listening"
      ],
      "notes": "Asked permission and used reflective listening effectively"
    },
    "Compassion": {
      "points": 6,
      "max_points": 6,
      "assessment": "Meets Criteria",
      "criteria_text": [
        "Tries to understand the patient's perceptions and/or concerns with the HPV vaccination",
        "Does not judge, shame or belittle the patient"
      ],
      "notes": "Showed genuine empathy and understanding"
    },
    "Evocation": {
      "points": 6,
      "max_points": 6,
      "assessment": "Meets Criteria",
      "criteria_text": [
        "Uses open-ended questions for patient understanding OR stage of change OR eliciting change talk",
        "Supports self-efficacy; emphasizes patient autonomy regarding the HPV vaccination (rolls with resistance)"
      ],
      "notes": "Excellent use of open-ended questions"
    },
    "Summary": {
      "points": 3,
      "max_points": 3,
      "assessment": "Meets Criteria",
      "criteria_text": [
        "Reflects big picture; checks accuracy of information and/or next steps"
      ],
      "notes": "Provided clear summary with next steps"
    },
    "Response Factor": {
      "points": 10,
      "max_points": 10,
      "assessment": "Meets Criteria",
      "criteria_text": [
        "Fast and intuitive responses to questions probed; acceptable average time throughout conversation"
      ],
      "notes": "Average response latency: 1.8s (threshold: 2.5s)"
    }
  }
}
```

### Mixed Score Example (21/40)

```json
{
  "total_score": 21,
  "max_possible_score": 40,
  "percentage": 52.5,
  "performance_band": "Basic MI awareness, significant practice needed",
  "context": "OHI",
  "categories": {
    "Collaboration": {
      "points": 9,
      "max_points": 9,
      "assessment": "Meets Criteria",
      "notes": "Good introduction and partnership building"
    },
    "Acceptance": {
      "points": 6,
      "max_points": 6,
      "assessment": "Meets Criteria",
      "notes": "Asked permission and used reflections"
    },
    "Compassion": {
      "points": 0,
      "max_points": 6,
      "assessment": "Needs Improvement",
      "notes": "Some judgmental language used; could be more empathetic"
    },
    "Evocation": {
      "points": 6,
      "max_points": 6,
      "assessment": "Meets Criteria",
      "notes": "Good open-ended questions to elicit change talk"
    },
    "Summary": {
      "points": 0,
      "max_points": 3,
      "assessment": "Needs Improvement",
      "notes": "Did not provide adequate summary of conversation"
    },
    "Response Factor": {
      "points": 0,
      "max_points": 10,
      "assessment": "Needs Improvement",
      "notes": "Average response latency: 3.2s (threshold: 2.5s)"
    }
  }
}
```

---

## LLM Feedback Format

The LLM should generate feedback in the following format for proper parsing:

```
**Collaboration (9 pts): Meets Criteria** - Excellent rapport building and partnership throughout the conversation. The student introduced themselves warmly and collaborated effectively with the patient.

**Acceptance (6 pts): Meets Criteria** - Asked permission before discussing oral health and used reflective listening to show understanding.

**Compassion (6 pts): Needs Improvement** - While generally supportive, some statements came across as slightly judgmental. Work on maintaining a completely non-judgmental tone.

**Evocation (6 pts): Meets Criteria** - Used open-ended questions effectively to understand patient's readiness for change and supported autonomy.

**Summary (3 pts): Needs Improvement** - The conversation ended abruptly without summarizing key points or discussing next steps.

**Response Factor (10 pts): Meets Criteria** - Responses were timely and showed good understanding of patient concerns.
```

---

## Configuration

### Response Factor Threshold

The Response Factor threshold can be configured via environment variable:

```bash
# Set threshold to 3.0 seconds
export RESPONSE_FACTOR_THRESHOLD=3.0
```

**Default**: 2.5 seconds

**Behavior**:
- Average latency ≤ threshold → **Meets Criteria** (10 points)
- Average latency > threshold → **Needs Improvement** (0 points)

---

## API Usage

### Python

```python
from services.evaluation_service import EvaluationService
from rubric.mi_rubric import CategoryAssessment

# Evaluate from LLM feedback text
result = EvaluationService.evaluate_session(
    feedback_text="**Collaboration (9 pts): Meets Criteria** - ...",
    session_type="HPV",
    response_latency=2.0,  # Optional
    response_threshold=2.5  # Optional
)

print(f"Total Score: {result['total_score']}/40")
print(f"Performance: {result['performance_band']}")

# Manual evaluation
from rubric.mi_rubric import MIEvaluator, RubricContext

assessments = {
    'Collaboration': CategoryAssessment.MEETS_CRITERIA,
    'Acceptance': CategoryAssessment.MEETS_CRITERIA,
    'Compassion': CategoryAssessment.NEEDS_IMPROVEMENT,
    'Evocation': CategoryAssessment.MEETS_CRITERIA,
    'Summary': CategoryAssessment.NEEDS_IMPROVEMENT,
    'Response Factor': CategoryAssessment.MEETS_CRITERIA
}

result = MIEvaluator.evaluate(
    assessments=assessments,
    context=RubricContext.HPV,
    notes={'Compassion': 'Work on non-judgmental language'}
)
```

### PHP

```php
require_once 'src/Service/EvaluationService.php';

// Evaluate from LLM feedback
$result = EvaluationService::evaluateSession(
    $feedbackText,
    'HPV',
    2.0,  // Optional response latency
    2.5   // Optional threshold
);

echo "Total Score: {$result['total_score']}/40\n";
echo "Performance: {$result['performance_band']}\n";

// Manual evaluation
require_once 'src/Rubric/MIRubric.php';

$assessments = [
    'Collaboration' => CategoryAssessment::MEETS_CRITERIA,
    'Acceptance' => CategoryAssessment::MEETS_CRITERIA,
    'Compassion' => CategoryAssessment::NEEDS_IMPROVEMENT,
    'Evocation' => CategoryAssessment::MEETS_CRITERIA,
    'Summary' => CategoryAssessment::NEEDS_IMPROVEMENT,
    'Response Factor' => CategoryAssessment::MEETS_CRITERIA
];

$result = MIEvaluator::evaluate(
    $assessments,
    RubricContext::HPV,
    ['Compassion' => 'Work on non-judgmental language']
);
```

---

## Migration from Old Rubric

### Key Changes

| Aspect | Old Rubric | New Rubric |
|--------|------------|------------|
| **Total Points** | 30 | 40 |
| **Categories** | 4 (Collaboration, Evocation, Acceptance, Compassion) | 6 (+ Summary, Response Factor) |
| **Scoring** | 3-level (Met: 7.5, Partially Met: 3.75, Not Met: 0) | Binary (Meets: Full points, Needs: 0) |
| **Points per Category** | 7.5 each | Variable (9, 6, 6, 6, 3, 10) |
| **Performance Bands** | 5 levels (90%, 80%, 70%, 60%) | 5 levels (90%, 75%, 60%, 40%) |

### Backward Compatibility

The codebase maintains backward compatibility during transition:
- Both old and new rubric systems can coexist
- PDF generation supports both formats
- Feedback template defaults to new rubric but falls back to old if unavailable

---

## Testing

Run the comprehensive test suite:

```bash
python3 test_mi_rubric.py
```

**Test Coverage**:
- Perfect score (40/40)
- Zero score (0/40)
- Mixed scoring scenarios
- Context substitution (HPV vs OHI)
- Response Factor threshold boundaries
- Performance band thresholds
- LLM feedback parsing
- Integration with EvaluationService

---

## Changelog

### Version 2.0.0 (Current)
- **NEW**: 40-point binary rubric system
- **NEW**: 6 categories including Summary and Response Factor
- **NEW**: Context-aware criteria text substitution
- **NEW**: Configurable Response Factor threshold
- **NEW**: Python and PHP implementations
- **NEW**: Comprehensive test suite

### Version 1.0.0 (Legacy)
- 30-point rubric with 4 components
- 3-level scoring (Met, Partially Met, Not Met)
- Fixed 7.5 points per component

---

## Support

For questions or issues:
1. Check test suite: `python3 test_mi_rubric.py`
2. Review example payloads above
3. Verify environment configuration
4. Check logs for parsing errors

## Future Enhancements

Potential future improvements:
- Real-time response latency tracking in UI
- Advanced analytics dashboard
- Historical performance tracking
- Peer comparison metrics
- Adaptive threshold recommendations
