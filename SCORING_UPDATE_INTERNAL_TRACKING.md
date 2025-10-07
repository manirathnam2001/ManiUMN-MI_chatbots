# Scoring System Update - Internal Time and Effort Tracking

## Overview

The scoring system has been updated to include internal time and effort tracking that makes the scoring more lenient while maintaining the 30-point maximum. These internal metrics are tracked but **not displayed to users**, keeping the UI clean and focused on the final score.

## Key Changes

### 1. Internal Tracking Parameters (scoring_utils.py)

Added internal parameters to the `MIScorer` class:

```python
# Internal tracking parameters (not displayed to users)
_EFFORT_BONUS_THRESHOLD = 0.3  # Effort bonus threshold
_TIME_FACTOR_MAX = 1.05  # Maximum time-based bonus multiplier
_INTERNAL_TRACKING_ENABLED = False  # Disabled by default for backwards compatibility
```

### 2. More Lenient Scoring Algorithm

The system now includes:

- **Effort Bonus**: Awards up to 3 points for student engagement
  - Any effort shown (components with Met or Partially Met) receives a bonus
  - Formula: `min(2.0, effort_ratio * 2.5)` for base bonus
  - Additional 0.5 points per retry attempt (up to 1.0 point)

- **Time Factor**: Multiplies base score by up to 1.05x
  - Based on feedback length as a proxy for time invested
  - 1.05x for substantial engagement (>800 chars)
  - 1.03x for moderate engagement (>400 chars)
  - 1.0x otherwise

- **Score Calculation**: 
  ```
  adjusted_score = (base_score * time_factor) + effort_bonus
  final_score = min(adjusted_score, 30.0)  # Always capped at 30
  ```

### 3. Internal Data Structure

When internal tracking is enabled, the score breakdown includes (but does not display):

```python
'_internal_tracking': {
    'base_score': 22.5,          # Score before adjustments
    'effort_bonus': 2.0,         # Effort bonus in points
    'time_factor': 1.05,         # Time multiplier
    'attempt_number': 1,         # Attempt count
    'enabled': True              # Tracking flag
}
```

**Note**: Fields prefixed with `_` follow Python convention for internal/private data.

## Usage

### Default Behavior (Backwards Compatible)

```python
from scoring_utils import MIScorer

feedback = """
**1. COLLABORATION: [Met]** - Good work
**2. EVOCATION: [Partially Met]** - Some effort
**3. ACCEPTANCE: [Met]** - Respectful
**4. COMPASSION: [Partially Met]** - Generally warm
"""

# Standard call - no internal adjustments
breakdown = MIScorer.get_score_breakdown(feedback)
print(f"Score: {breakdown['total_score']}/30.0")
# Output: Score: 22.5/30.0
```

### With Internal Tracking Enabled

```python
# Enable internal adjustments for more lenient scoring
breakdown = MIScorer.get_score_breakdown(
    feedback, 
    enable_internal_adjustments=True
)
print(f"Score: {breakdown['total_score']}/30.0")
# Output: Score: 24.5/30.0 (higher due to bonuses)

# Access internal tracking data (for debugging only)
if '_internal_tracking' in breakdown:
    tracking = breakdown['_internal_tracking']
    print(f"Base score: {tracking['base_score']}")
    print(f"Effort bonus: +{tracking['effort_bonus']} points")
    print(f"Time factor: {tracking['time_factor']}x")
```

### Multiple Attempts (Even More Lenient)

```python
# Track multiple attempts - each attempt gets additional bonus
for attempt in [1, 2, 3]:
    breakdown = MIScorer.get_score_breakdown(
        feedback,
        enable_internal_adjustments=True,
        attempt_number=attempt
    )
    print(f"Attempt {attempt}: {breakdown['total_score']}/30.0")

# Output:
# Attempt 1: 24.5/30.0
# Attempt 2: 25.0/30.0
# Attempt 3: 25.5/30.0
```

## UI Display Guidelines

### What to Show Users

The UI should **only** display these fields:

- `total_score` - Final score out of 30
- `total_possible` - Maximum possible score (always 30.0)
- `percentage` - Percentage score
- `components` - Individual component breakdowns

### What NOT to Show Users

Do **not** display:

- `_internal_tracking` - Internal tracking data
- Effort bonus calculations
- Time factor multipliers
- Attempt numbers
- Base scores before adjustments

### Example UI Code

```python
def display_score(breakdown):
    """Display score to user - only shows public fields."""
    # Filter out internal data (anything starting with _)
    public_data = {k: v for k, v in breakdown.items() 
                   if not k.startswith('_')}
    
    # Display
    print(f"Your Score: {public_data['total_score']:.1f}/{public_data['total_possible']}")
    print(f"Percentage: {public_data['percentage']:.1f}%")
    
    # Show component details
    for component, details in public_data['components'].items():
        print(f"  {component}: {details['score']}/{details['max_score']} pts")
```

## Testing

Three test suites are provided:

### 1. test_internal_tracking.py
Tests internal tracking functionality:
- Disabled by default (backwards compatibility)
- Effort and time bonuses calculated correctly
- Multiple attempts bonus
- Maximum score cap
- Internal data marked as internal

### 2. test_scoring_integration.py
Integration tests verifying:
- Scores never exceed 30 points
- Internal data hidden from UI
- More lenient scoring works
- Multiple attempts handled correctly
- Backwards compatibility maintained

### 3. test_scoring_consistency.py
Original consistency tests (all still pass):
- Duplicate component handling
- Score consistency validation
- Zero score for no conversation
- Score range validation

Run all tests:
```bash
python test_internal_tracking.py
python test_scoring_integration.py
python test_scoring_consistency.py
```

## Benefits

1. **More Lenient Scoring**: Students showing effort get bonus points (up to ~3 points)
2. **Encourages Retries**: Multiple attempts receive additional bonuses
3. **Fair Time Recognition**: Longer, more thoughtful responses rewarded
4. **Clean UI**: Internal metrics stay internal, UI shows only final score
5. **Backwards Compatible**: Existing code works without changes
6. **Always Capped at 30**: No score can exceed the maximum

## Score Comparison Examples

### Example 1: Partial Effort
```
Components: 2 Met, 2 Partially Met
Base Score: 22.5/30.0

Without tracking: 22.5/30.0
With tracking (1st attempt): 24.5/30.0 (+2.0 points)
With tracking (3rd attempt): 25.5/30.0 (+3.0 points)
```

### Example 2: Lower Performance
```
Components: 0 Met, 4 Partially Met
Base Score: 15.0/30.0

Without tracking: 15.0/30.0
With tracking (1st attempt): 17.0/30.0 (+2.0 points, 13% improvement)
With tracking (3rd attempt): 18.0/30.0 (+3.0 points, 20% improvement)
```

### Example 3: Perfect Score
```
Components: 4 Met, 0 Partially Met
Base Score: 30.0/30.0

Without tracking: 30.0/30.0
With tracking (any attempt): 30.0/30.0 (capped at maximum)
```

## Implementation Notes

- Internal tracking is **opt-in** via `enable_internal_adjustments` parameter
- Default behavior unchanged for backwards compatibility
- All existing tests pass without modification
- UI components (PDF generators, display functions) unmodified
- Maximum score enforcement at multiple levels (calculation + validation)

## Migration Path

### For New Code
Enable internal tracking for more lenient scoring:
```python
breakdown = MIScorer.get_score_breakdown(
    feedback,
    enable_internal_adjustments=True,
    attempt_number=attempt_num
)
```

### For Existing Code
No changes needed - works as before:
```python
breakdown = MIScorer.get_score_breakdown(feedback)
```

### To Enable Globally
Change the class default:
```python
MIScorer._INTERNAL_TRACKING_ENABLED = True
```

## Security & Privacy

- Internal tracking data marked with underscore prefix (Python convention)
- No PII or sensitive data in internal tracking
- Tracking data never sent to external services
- Used only for score calculation
- Can be fully disabled by not enabling internal adjustments
