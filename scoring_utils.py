"""
Standardized scoring utilities for MI assessment feedback.
Provides consistent scoring calculation and validation across HPV and OHI assessments.
"""

import re
from typing import Dict, List, Tuple, Optional


class MIComponentScore:
    """Represents a score for an individual MI component."""
    
    def __init__(self, component: str, status: str, score: float, feedback: str):
        self.component = component
        self.status = status
        self.score = score
        self.feedback = feedback
        
    def __str__(self):
        return f"{self.component}: {self.status} ({self.score} pts) - {self.feedback}"


class MIScorer:
    """Handles MI component scoring with validation and standardization."""
    
    # Standard MI components and their maximum scores
    COMPONENTS = {
        'COLLABORATION': 7.5,
        'EVOCATION': 7.5,
        'ACCEPTANCE': 7.5,
        'COMPASSION': 7.5
    }
    
    # Valid status values and their scoring multipliers
    STATUS_MULTIPLIERS = {
        'Met': 1.0,
        'Partially Met': 0.5,
        'Not Met': 0.0,
        # Case variations
        'met': 1.0,
        'partially met': 0.5,
        'not met': 0.0,
        'MET': 1.0,
        'PARTIALLY MET': 0.5,
        'NOT MET': 0.0,
        'partially MET': 0.5,
        'not MET': 0.0,
        # Common alternatives
        'Not Yet Met': 0.0,
        'not yet met': 0.0,
        'NOT YET MET': 0.0,
        'Partially Achieved': 0.5,
        'partially achieved': 0.5,
        'PARTIALLY ACHIEVED': 0.5,
        'Achieved': 1.0,
        'achieved': 1.0,
        'ACHIEVED': 1.0,
        'Fully Met': 1.0,
        'fully met': 1.0,
        'FULLY MET': 1.0,
    }
    
    TOTAL_POSSIBLE_SCORE = sum(COMPONENTS.values())
    
    @classmethod
    def validate_score_range(cls, score: float) -> bool:
        """Validate that a score is within acceptable range."""
        return 0.0 <= score <= cls.TOTAL_POSSIBLE_SCORE
    
    @classmethod
    def validate_score_consistency(cls, breakdown: Dict[str, any]) -> bool:
        """
        Validate that component scores sum to the total score.
        
        Args:
            breakdown: Score breakdown dictionary from get_score_breakdown
            
        Returns:
            bool: True if scores are consistent, False otherwise
        """
        if 'components' not in breakdown or 'total_score' not in breakdown:
            return False
        
        component_sum = sum(c['score'] for c in breakdown['components'].values())
        total_score = breakdown['total_score']
        
        # Allow for small floating point errors
        return abs(component_sum - total_score) < 0.001
    
    @classmethod
    def calculate_component_score(cls, component: str, status: str) -> float:
        """Calculate score for a specific component based on status."""
        if component not in cls.COMPONENTS:
            raise ValueError(f"Unknown component: {component}")
        
        if status not in cls.STATUS_MULTIPLIERS:
            raise ValueError(f"Invalid status: {status}")
        
        max_score = cls.COMPONENTS[component]
        multiplier = cls.STATUS_MULTIPLIERS[status]
        return max_score * multiplier
    
    @classmethod
    def parse_component_line(cls, line: str, debug: bool = False) -> Optional[MIComponentScore]:
        """Parse a single component line from feedback text."""
        line = line.strip()
        
        # Debug logging to help diagnose parsing issues
        if debug:
            print(f"DEBUG: Parsing line: {repr(line)}")
        
        # Enhanced regex patterns to handle multiple formats including bold markdown:
        # Format 1: "1. COMPONENT: [Status] - feedback"
        # Format 2: "COMPONENT: [Status] - feedback" 
        # Format 3: "● COMPONENT: [Status] - feedback"
        # Format 4: "• COMPONENT: [Status] - feedback"
        # Format 5: "COMPONENT (7.5 pts): [Status] - feedback"
        # Format 6: "COMPONENT: Status - feedback" (without brackets)
        # Format 7: "**COMPONENT (7.5 pts): Status** - feedback" (bold markdown)
        # Format 8: "**1. COMPONENT: [Status]** - feedback" (bold with brackets)
        component_patterns = [
            # Pattern with brackets: [Status] (handles bold markdown around entire component)
            r'^(?:\*+)?(?:\d+\.\s*|[●•]\s*)?(COLLABORATION|EVOCATION|ACCEPTANCE|COMPASSION)(?:\s*\([0-9.]+\s*(?:pts?)?\))?\s*:\s*\[([^\]]+)\](?:\*+)?\s*[-–—]\s*(.+)$',
            
            # Pattern without brackets but with bold markdown around status (handles multiple asterisks)
            r'^(?:\*+)?(?:\d+\.\s*|[●•]\s*)?(COLLABORATION|EVOCATION|ACCEPTANCE|COMPASSION)(?:\s*\([0-9.]+\s*(?:pts?)?\))?\s*:\s*(?:\*+)?(Met|Partially Met|Not Met|met|partially met|not met|Not Yet Met|not yet met|Partially Achieved|partially achieved|Achieved|achieved|Fully Met|fully met|PARTIALLY MET|NOT MET|FULLY MET|partially MET|not MET)(?:\*+)?\s*[-–—]\s*(.+)$',
            
            # Pattern for bold markdown around entire component section
            r'^\*+(?:\d+\.\s*|[●•]\s*)?(COLLABORATION|EVOCATION|ACCEPTANCE|COMPASSION)(?:\s*\([0-9.]+\s*(?:pts?)?\))?\s*:\s*(Met|Partially Met|Not Met|met|partially met|not met|Not Yet Met|not yet met|Partially Achieved|partially achieved|Achieved|achieved|Fully Met|fully met|PARTIALLY MET|NOT MET|FULLY MET|partially MET|not MET)\*+\s*[-–—]\s*(.+)$',
            
            # Original patterns (for backward compatibility)
            r'^(?:\d+\.\s*|[●•]\s*)?(COLLABORATION|EVOCATION|ACCEPTANCE|COMPASSION)(?:\s*\([0-9.]+\s*(?:pts?)?\))?\s*:\s*\[([^\]]+)\]\s*[-–—]\s*(.+)$',
            r'^(?:\d+\.\s*|[●•]\s*)?(COLLABORATION|EVOCATION|ACCEPTANCE|COMPASSION)(?:\s*\([0-9.]+\s*(?:pts?)?\))?\s*:\s*(Met|Partially Met|Not Met|met|partially met|not met|Not Yet Met|not yet met|Partially Achieved|partially achieved|Achieved|achieved|Fully Met|fully met)\s*[-–—]\s*(.+)$'
        ]
        
        for i, pattern in enumerate(component_patterns):
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                component = match.group(1).upper()
                status = match.group(2).strip()
                feedback = match.group(3).strip()
                
                if debug:
                    print(f"DEBUG: Pattern {i} matched - Component: {component}, Status: {status}")
                
                # Clean up any remaining markdown from status
                status = status.replace('*', '').strip()
                
                # Validate and calculate score
                try:
                    score = cls.calculate_component_score(component, status)
                    if debug:
                        print(f"DEBUG: Score calculated: {score} for {component} with status {status}")
                    return MIComponentScore(component, status, score, feedback)
                except ValueError as e:
                    if debug:
                        print(f"DEBUG: Score calculation failed for {component} with status '{status}': {e}")
                    # If status is invalid, default to 0 score
                    return MIComponentScore(component, status, 0.0, feedback)
        
        if debug:
            print(f"DEBUG: No pattern matched for line: {repr(line)}")
        return None
    
    @classmethod
    def parse_feedback_scores(cls, feedback_text: str, debug: bool = False) -> List[MIComponentScore]:
        """Parse all component scores from feedback text."""
        scores = []
        lines = feedback_text.split('\n')
        
        if debug:
            print(f"DEBUG: Parsing {len(lines)} lines of feedback")
        
        for line in lines:
            component_score = cls.parse_component_line(line, debug=debug)
            if component_score:
                scores.append(component_score)
        
        if debug:
            print(f"DEBUG: Found {len(scores)} component scores")
        
        return scores
    
    @classmethod
    def calculate_total_score(cls, component_scores: List[MIComponentScore]) -> float:
        """Calculate total score from component scores."""
        total = sum(score.score for score in component_scores)
        if not cls.validate_score_range(total):
            raise ValueError(f"Total score {total} is outside valid range (0-{cls.TOTAL_POSSIBLE_SCORE})")
        return total
    
    @classmethod
    def get_score_breakdown(cls, feedback_text: str, debug: bool = False) -> Dict[str, any]:
        """Get complete score breakdown from feedback text."""
        if debug:
            print(f"DEBUG: Starting score breakdown for feedback of length {len(feedback_text)}")
        
        component_scores = cls.parse_feedback_scores(feedback_text, debug=debug)
        
        if debug:
            print(f"DEBUG: Parsed {len(component_scores)} components:")
            for score in component_scores:
                print(f"  - {score.component}: {score.status} = {score.score} pts")
        
        # Ensure all required components are present with 0 scores if missing
        # AND handle duplicates by taking the LAST occurrence of each component
        all_components = {}
        for component in cls.COMPONENTS.keys():
            # Find ALL matching scores for this component
            matching_scores = [s for s in component_scores if s.component == component]
            
            if matching_scores:
                # Take the LAST occurrence (most recent/final evaluation)
                found_score = matching_scores[-1]
                
                if debug and len(matching_scores) > 1:
                    print(f"DEBUG: Component {component} has {len(matching_scores)} occurrences, using last one")
                
                all_components[component] = {
                    'status': found_score.status,
                    'score': found_score.score,
                    'max_score': cls.COMPONENTS[component],
                    'feedback': found_score.feedback
                }
            else:
                # Component missing - set to 0
                if debug:
                    print(f"DEBUG: Component {component} missing, setting to 0")
                all_components[component] = {
                    'status': 'Not Found',
                    'score': 0.0,
                    'max_score': cls.COMPONENTS[component],
                    'feedback': 'No feedback found for this component'
                }
        
        # Calculate total from the deduplicated components (ensures consistency)
        total_score = sum(c['score'] for c in all_components.values())
        
        # Validate that total score is within acceptable range
        if not cls.validate_score_range(total_score):
            raise ValueError(f"Total score {total_score} is outside valid range (0-{cls.TOTAL_POSSIBLE_SCORE})")
        
        if debug:
            print(f"DEBUG: Total score calculated from components: {total_score}")
        
        breakdown = {
            'components': all_components,
            'total_score': total_score,
            'total_possible': cls.TOTAL_POSSIBLE_SCORE,
            'percentage': (total_score / cls.TOTAL_POSSIBLE_SCORE) * 100
        }
        
        # Validate that component scores sum to total (should always be true now)
        component_sum = sum(c['score'] for c in all_components.values())
        if abs(component_sum - total_score) > 0.001:  # Allow for floating point errors
            raise ValueError(
                f"Score validation failed: component sum ({component_sum}) "
                f"does not match total score ({total_score})"
            )
        
        if debug:
            print(f"DEBUG: Final breakdown - Total: {breakdown['total_score']}/{breakdown['total_possible']} ({breakdown['percentage']:.1f}%)")
            print(f"DEBUG: Validation passed - component sum matches total")
        
        return breakdown


def validate_student_name(name: str) -> str:
    """Validate and sanitize student name for file naming."""
    if not name or not name.strip():
        raise ValueError("Student name cannot be empty")
    
    # Remove special characters for file naming
    sanitized = re.sub(r'[^\w\s-]', '', name.strip())
    sanitized = re.sub(r'\s+', '_', sanitized)
    
    if not sanitized:
        raise ValueError("Student name contains only invalid characters")
    
    return sanitized


def validate_feedback_format(feedback: str) -> bool:
    """Validate that feedback contains required MI components."""
    required_components = set(MIScorer.COMPONENTS.keys())
    found_components = set()
    
    lines = feedback.split('\n')
    for line in lines:
        for component in required_components:
            if component in line.upper():
                found_components.add(component)
    
    return found_components == required_components