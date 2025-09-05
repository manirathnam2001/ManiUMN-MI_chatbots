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
        'Not Met': 0.0
    }
    
    TOTAL_POSSIBLE_SCORE = sum(COMPONENTS.values())
    
    @classmethod
    def validate_score_range(cls, score: float) -> bool:
        """Validate that a score is within acceptable range."""
        return 0.0 <= score <= cls.TOTAL_POSSIBLE_SCORE
    
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
    def parse_component_line(cls, line: str) -> Optional[MIComponentScore]:
        """Parse a single component line from feedback text."""
        line = line.strip()
        
        # Look for component pattern: "COMPONENT: [Status] - feedback"
        component_pattern = r'(\d+\.\s*)?(COLLABORATION|EVOCATION|ACCEPTANCE|COMPASSION):\s*\[([^\]]+)\]\s*-\s*(.+)'
        match = re.match(component_pattern, line, re.IGNORECASE)
        
        if not match:
            return None
        
        component = match.group(2).upper()
        status = match.group(3).strip()
        feedback = match.group(4).strip()
        
        # Validate and calculate score
        try:
            score = cls.calculate_component_score(component, status)
            return MIComponentScore(component, status, score, feedback)
        except ValueError:
            # If status is invalid, default to 0 score
            return MIComponentScore(component, status, 0.0, feedback)
    
    @classmethod
    def parse_feedback_scores(cls, feedback_text: str) -> List[MIComponentScore]:
        """Parse all component scores from feedback text."""
        scores = []
        lines = feedback_text.split('\n')
        
        for line in lines:
            component_score = cls.parse_component_line(line)
            if component_score:
                scores.append(component_score)
        
        return scores
    
    @classmethod
    def calculate_total_score(cls, component_scores: List[MIComponentScore]) -> float:
        """Calculate total score from component scores."""
        total = sum(score.score for score in component_scores)
        if not cls.validate_score_range(total):
            raise ValueError(f"Total score {total} is outside valid range (0-{cls.TOTAL_POSSIBLE_SCORE})")
        return total
    
    @classmethod
    def get_score_breakdown(cls, feedback_text: str) -> Dict[str, any]:
        """Get complete score breakdown from feedback text."""
        component_scores = cls.parse_feedback_scores(feedback_text)
        total_score = cls.calculate_total_score(component_scores)
        
        breakdown = {
            'components': {score.component: {
                'status': score.status,
                'score': score.score,
                'max_score': cls.COMPONENTS[score.component],
                'feedback': score.feedback
            } for score in component_scores},
            'total_score': total_score,
            'total_possible': cls.TOTAL_POSSIBLE_SCORE,
            'percentage': (total_score / cls.TOTAL_POSSIBLE_SCORE) * 100
        }
        
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