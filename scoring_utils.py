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
    
    # Valid status values and their scoring multipliers (more lenient)
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
    
    # Effort tracking thresholds
    EFFORT_THRESHOLDS = {
        'min_response_length': 20,  # Minimum characters for quality response
        'quality_response_length': 50,  # Length for high-quality response
        'min_turns': 4,  # Minimum conversation turns for engagement
        'good_engagement_turns': 8,  # Turns for good engagement
        'excellent_engagement_turns': 12  # Turns for excellent engagement
    }
    
    # Time-based scoring modifiers
    TIME_BONUSES = {
        'quick_thoughtful': 0.05,  # 5% bonus for quick but thoughtful (10-30s)
        'reasonable': 0.02,  # 2% bonus for reasonable time (30-60s)
        'slow_but_complete': 0.01  # 1% bonus for slower but thorough responses
    }
    
    @classmethod
    def calculate_effort_bonus(cls, chat_history: List[Dict], debug: bool = False) -> Dict[str, any]:
        """
        Calculate effort-based bonus points based on conversation metrics.
        
        Args:
            chat_history: List of chat messages with 'role' and 'content'
            debug: Enable debug logging
            
        Returns:
            Dictionary with effort metrics and bonus points
        """
        if not chat_history:
            return {'bonus': 0.0, 'metrics': {}}
        
        # Extract user messages only
        user_messages = [msg for msg in chat_history if msg.get('role') == 'user']
        
        # Calculate metrics
        num_turns = len(user_messages)
        avg_length = sum(len(msg.get('content', '')) for msg in user_messages) / max(len(user_messages), 1)
        total_length = sum(len(msg.get('content', '')) for msg in user_messages)
        
        # Calculate response quality score (0-1)
        quality_score = 0.0
        if avg_length >= cls.EFFORT_THRESHOLDS['quality_response_length']:
            quality_score = 1.0
        elif avg_length >= cls.EFFORT_THRESHOLDS['min_response_length']:
            quality_score = 0.5
        
        # Calculate engagement score (0-1)
        engagement_score = 0.0
        if num_turns >= cls.EFFORT_THRESHOLDS['excellent_engagement_turns']:
            engagement_score = 1.0
        elif num_turns >= cls.EFFORT_THRESHOLDS['good_engagement_turns']:
            engagement_score = 0.7
        elif num_turns >= cls.EFFORT_THRESHOLDS['min_turns']:
            engagement_score = 0.4
        
        # Calculate effort bonus (max 3 points - 10% of total possible)
        effort_bonus = (quality_score + engagement_score) * 1.5
        
        metrics = {
            'num_turns': num_turns,
            'avg_response_length': avg_length,
            'total_response_length': total_length,
            'quality_score': quality_score,
            'engagement_score': engagement_score
        }
        
        if debug:
            print(f"DEBUG: Effort tracking - turns: {num_turns}, avg_length: {avg_length:.1f}")
            print(f"DEBUG: Quality score: {quality_score}, Engagement score: {engagement_score}")
            print(f"DEBUG: Effort bonus: {effort_bonus:.2f} points")
        
        return {'bonus': effort_bonus, 'metrics': metrics}
    
    @classmethod
    def calculate_time_bonus(cls, response_times: List[float], debug: bool = False) -> Dict[str, any]:
        """
        Calculate time-based bonus for response patterns.
        
        Args:
            response_times: List of response times in seconds
            debug: Enable debug logging
            
        Returns:
            Dictionary with time metrics and bonus multiplier
        """
        if not response_times:
            return {'multiplier': 0.0, 'metrics': {}}
        
        avg_time = sum(response_times) / len(response_times)
        
        # Determine time category and bonus
        time_multiplier = 0.0
        time_category = 'timeout'
        
        if 10 <= avg_time <= 30:
            time_multiplier = cls.TIME_BONUSES['quick_thoughtful']
            time_category = 'quick_thoughtful'
        elif 30 < avg_time <= 60:
            time_multiplier = cls.TIME_BONUSES['reasonable']
            time_category = 'reasonable'
        elif 60 < avg_time <= 120:
            time_multiplier = cls.TIME_BONUSES['slow_but_complete']
            time_category = 'slow_but_complete'
        
        metrics = {
            'avg_response_time': avg_time,
            'time_category': time_category,
            'num_responses': len(response_times)
        }
        
        if debug:
            print(f"DEBUG: Time tracking - avg: {avg_time:.1f}s, category: {time_category}")
            print(f"DEBUG: Time multiplier: {time_multiplier:.2%}")
        
        return {'multiplier': time_multiplier, 'metrics': metrics}
    
    @classmethod
    def validate_score_range(cls, score: float) -> bool:
        """Validate that a score is within acceptable range (including bonuses)."""
        # Allow for bonuses up to ~13% extra (3 effort + 5% time)
        max_with_bonus = cls.TOTAL_POSSIBLE_SCORE * 1.13
        return 0.0 <= score <= max_with_bonus
    
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
    def get_score_breakdown(cls, feedback_text: str, chat_history: List[Dict] = None, 
                          response_times: List[float] = None, debug: bool = False) -> Dict[str, any]:
        """
        Get complete score breakdown from feedback text with optional effort/time bonuses.
        
        Args:
            feedback_text: The feedback text to parse
            chat_history: Optional list of chat messages for effort tracking
            response_times: Optional list of response times for time bonuses
            debug: Enable debug logging
        """
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
        
        # Calculate base total from the deduplicated components (ensures consistency)
        base_score = sum(c['score'] for c in all_components.values())
        
        # Calculate effort bonus if chat history provided
        effort_data = {'bonus': 0.0, 'metrics': {}}
        if chat_history:
            effort_data = cls.calculate_effort_bonus(chat_history, debug=debug)
        
        # Calculate time bonus if response times provided
        time_data = {'multiplier': 0.0, 'metrics': {}}
        if response_times:
            time_data = cls.calculate_time_bonus(response_times, debug=debug)
        
        # Apply bonuses
        effort_bonus = effort_data['bonus']
        time_multiplier = time_data['multiplier']
        time_bonus = base_score * time_multiplier
        
        total_score = base_score + effort_bonus + time_bonus
        
        # Validate that total score is within acceptable range (with bonuses)
        if not cls.validate_score_range(total_score):
            # If over max, cap at max with bonus
            max_with_bonus = cls.TOTAL_POSSIBLE_SCORE * 1.13
            total_score = min(total_score, max_with_bonus)
            if debug:
                print(f"DEBUG: Score capped at maximum: {total_score}")
        
        if debug:
            print(f"DEBUG: Base score: {base_score:.2f}")
            print(f"DEBUG: Effort bonus: {effort_bonus:.2f}")
            print(f"DEBUG: Time bonus: {time_bonus:.2f}")
            print(f"DEBUG: Total score: {total_score:.2f}")
        
        breakdown = {
            'components': all_components,
            'base_score': base_score,
            'effort_bonus': effort_bonus,
            'time_bonus': time_bonus,
            'total_score': total_score,
            'total_possible': cls.TOTAL_POSSIBLE_SCORE,
            'percentage': (base_score / cls.TOTAL_POSSIBLE_SCORE) * 100,
            'adjusted_percentage': (total_score / cls.TOTAL_POSSIBLE_SCORE) * 100,
            'effort_metrics': effort_data.get('metrics', {}),
            'time_metrics': time_data.get('metrics', {})
        }
        
        # Validate that component scores sum to base score (should always be true now)
        component_sum = sum(c['score'] for c in all_components.values())
        if abs(component_sum - base_score) > 0.001:  # Allow for floating point errors
            raise ValueError(
                f"Score validation failed: component sum ({component_sum}) "
                f"does not match base score ({base_score})"
            )
        
        if debug:
            print(f"DEBUG: Final breakdown - Total: {breakdown['total_score']:.2f}/{breakdown['total_possible']} ({breakdown['adjusted_percentage']:.1f}%)")
            print(f"DEBUG: Validation passed - component sum matches base score")
        
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