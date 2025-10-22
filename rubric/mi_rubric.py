"""
New 40-point Binary MI Rubric System

This module implements the revamped Motivational Interviewing rubric with:
- 6 categories totaling 40 points
- Binary scoring per category (Meets Criteria = full points, Needs Improvement = 0)
- Context-aware criteria text (HPV vaccination vs oral health)
- Performance band messages

Categories:
- Collaboration: 9 points
- Acceptance: 6 points
- Compassion: 6 points
- Evocation: 6 points
- Summary: 3 points
- Response Factor: 10 points
"""

from typing import Dict, List, Optional, Tuple
from enum import Enum


class RubricContext(Enum):
    """Context for rubric criteria text substitution."""
    HPV = "HPV"
    OHI = "OHI"


class CategoryAssessment(Enum):
    """Binary assessment for each category."""
    MEETS_CRITERIA = "Meets Criteria"
    NEEDS_IMPROVEMENT = "Needs Improvement"


class MIRubric:
    """
    New 40-point MI Rubric with binary scoring.
    
    Total = 40 points across 6 categories.
    Each category: Meets Criteria = full points, Needs Improvement = 0.
    """
    
    # Category definitions with point values
    CATEGORIES = {
        'Collaboration': {
            'points': 9,
            'criteria': {
                CategoryAssessment.MEETS_CRITERIA: [
                    'Introduces self, role, is engaging, welcoming',
                    'Collaborated with the patient by eliciting their ideas for change in {context} or by providing support as a partnership',
                    'Did not lecture; Did not try to "fix" the patient'
                ],
                CategoryAssessment.NEEDS_IMPROVEMENT: [
                    'Did not introduce self/role/engaging/welcoming',
                    'Did not collaborate by eliciting patient ideas or provide partnership support',
                    'Lectured or tried to "fix" the patient'
                ]
            }
        },
        'Acceptance': {
            'points': 6,
            'criteria': {
                CategoryAssessment.MEETS_CRITERIA: [
                    'Asks permission before eliciting accurate information about the {context}',
                    'Uses reflections to demonstrate listening'
                ],
                CategoryAssessment.NEEDS_IMPROVEMENT: [
                    'Did not ask permission and/or provided inaccurate information',
                    'Did not use reflections to demonstrate listening'
                ]
            }
        },
        'Compassion': {
            'points': 6,
            'criteria': {
                CategoryAssessment.MEETS_CRITERIA: [
                    'Tries to understand the patient\'s perceptions and/or concerns with the {context}',
                    'Does not judge, shame or belittle the patient'
                ],
                CategoryAssessment.NEEDS_IMPROVEMENT: [
                    'Did not try to understand perceptions/concerns',
                    'Judged, shamed or belittled the patient'
                ]
            }
        },
        'Evocation': {
            'points': 6,
            'criteria': {
                CategoryAssessment.MEETS_CRITERIA: [
                    'Uses open-ended questions for patient understanding OR stage of change OR eliciting change talk',
                    'Supports self-efficacy; emphasizes patient autonomy regarding the {context} (rolls with resistance)'
                ],
                CategoryAssessment.NEEDS_IMPROVEMENT: [
                    'Did not ask open-ended questions',
                    'Did not support self-efficacy/autonomy (did not roll with resistance)'
                ]
            }
        },
        'Summary': {
            'points': 3,
            'criteria': {
                CategoryAssessment.MEETS_CRITERIA: [
                    'Reflects big picture; checks accuracy of information and/or next steps'
                ],
                CategoryAssessment.NEEDS_IMPROVEMENT: [
                    'Does not summarize appropriately'
                ]
            }
        },
        'Response Factor': {
            'points': 10,
            'criteria': {
                CategoryAssessment.MEETS_CRITERIA: [
                    'Fast and intuitive responses to questions probed; acceptable average time throughout conversation'
                ],
                CategoryAssessment.NEEDS_IMPROVEMENT: [
                    'Delay in understanding and responding'
                ]
            }
        }
    }
    
    TOTAL_POSSIBLE = 40
    
    # Performance band thresholds (based on percentage)
    PERFORMANCE_BANDS = [
        (90, "Excellent MI skills demonstrated"),
        (75, "Strong MI performance with minor areas for growth"),
        (60, "Satisfactory MI foundation, continue practicing"),
        (40, "Basic MI awareness, significant practice needed"),
        (0, "Significant improvement needed in MI techniques")
    ]
    
    @classmethod
    def get_total_possible(cls) -> int:
        """Get total possible score."""
        return cls.TOTAL_POSSIBLE
    
    @classmethod
    def get_category_points(cls, category: str) -> int:
        """Get point value for a specific category."""
        if category not in cls.CATEGORIES:
            raise ValueError(f"Unknown category: {category}")
        return cls.CATEGORIES[category]['points']
    
    @classmethod
    def get_category_criteria(cls, category: str, assessment: CategoryAssessment, 
                             context: RubricContext = RubricContext.HPV) -> List[str]:
        """
        Get criteria text for a category and assessment level.
        
        Args:
            category: Category name
            assessment: CategoryAssessment enum value
            context: RubricContext for text substitution
            
        Returns:
            List of criteria strings with context substitution applied
        """
        if category not in cls.CATEGORIES:
            raise ValueError(f"Unknown category: {category}")
        
        criteria = cls.CATEGORIES[category]['criteria'][assessment]
        
        # Apply context substitution
        context_text = "HPV vaccination" if context == RubricContext.HPV else "oral health"
        return [c.replace('{context}', context_text) for c in criteria]
    
    @classmethod
    def get_performance_band(cls, total_score: int) -> str:
        """
        Get performance band message based on total score.
        
        Args:
            total_score: Total score (0-40)
            
        Returns:
            Performance band message
        """
        percentage = (total_score / cls.TOTAL_POSSIBLE) * 100
        
        for threshold, message in cls.PERFORMANCE_BANDS:
            if percentage >= threshold:
                return message
        
        return cls.PERFORMANCE_BANDS[-1][1]


class MIEvaluator:
    """
    Evaluates MI performance using the new 40-point binary rubric.
    """
    
    @staticmethod
    def evaluate(assessments: Dict[str, CategoryAssessment], 
                context: RubricContext = RubricContext.HPV,
                notes: Optional[Dict[str, str]] = None,
                response_factor_latency: Optional[float] = None,
                response_factor_threshold: float = 2.5) -> Dict:
        """
        Evaluate MI performance based on category assessments.
        
        Args:
            assessments: Dict mapping category name to CategoryAssessment
            context: RubricContext for criteria text
            notes: Optional dict of evaluator notes per category
            response_factor_latency: Average bot response latency in seconds (for Response Factor)
            response_factor_threshold: Threshold in seconds for Response Factor (default 2.5s)
            
        Returns:
            Dict containing:
                - total_score: int (0-40)
                - max_possible_score: int (40)
                - percentage: float
                - performance_band: str
                - categories: Dict with per-category details
        """
        notes = notes or {}
        category_results = {}
        total_score = 0
        
        # Process each category
        for category_name, category_info in MIRubric.CATEGORIES.items():
            # Handle Response Factor specially if latency data provided
            if category_name == 'Response Factor':
                if response_factor_latency is not None:
                    # Auto-determine assessment based on latency
                    assessment = (CategoryAssessment.MEETS_CRITERIA 
                                if response_factor_latency <= response_factor_threshold
                                else CategoryAssessment.NEEDS_IMPROVEMENT)
                else:
                    # Use provided assessment or default to Needs Improvement if not provided
                    assessment = assessments.get(category_name, CategoryAssessment.NEEDS_IMPROVEMENT)
            else:
                # Get assessment from provided assessments
                assessment = assessments.get(category_name, CategoryAssessment.NEEDS_IMPROVEMENT)
            
            # Calculate score (binary: full points or 0)
            points = category_info['points'] if assessment == CategoryAssessment.MEETS_CRITERIA else 0
            total_score += points
            
            # Get criteria text with context substitution
            criteria_text = MIRubric.get_category_criteria(category_name, assessment, context)
            
            category_results[category_name] = {
                'points': points,
                'max_points': category_info['points'],
                'assessment': assessment.value,
                'criteria_text': criteria_text,
                'notes': notes.get(category_name, '')
            }
        
        # Calculate percentage
        percentage = (total_score / MIRubric.TOTAL_POSSIBLE) * 100
        
        # Get performance band
        performance_band = MIRubric.get_performance_band(total_score)
        
        return {
            'total_score': total_score,
            'max_possible_score': MIRubric.TOTAL_POSSIBLE,
            'percentage': percentage,
            'performance_band': performance_band,
            'categories': category_results,
            'context': context.value
        }
    
    @staticmethod
    def calculate_response_factor_assessment(
        average_latency: float, 
        threshold: float = 2.5
    ) -> CategoryAssessment:
        """
        Helper to calculate Response Factor assessment from latency.
        
        Args:
            average_latency: Average response latency in seconds
            threshold: Threshold in seconds (default 2.5s)
            
        Returns:
            CategoryAssessment.MEETS_CRITERIA if latency <= threshold, else NEEDS_IMPROVEMENT
        """
        return (CategoryAssessment.MEETS_CRITERIA 
                if average_latency <= threshold 
                else CategoryAssessment.NEEDS_IMPROVEMENT)
