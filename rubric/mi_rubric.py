"""
Updated MI Rubric System with Granular Scoring

This module implements the Motivational Interviewing rubric with:
- 6 categories totaling 40 points
- Granular scoring per category (0/3, 1/3, 2/3, 3/3 of full points)
- Context-aware criteria text (HPV vaccination vs oral health vs tobacco cessation vs periodontitis)
- Performance band messages

Categories:
- Collaboration: 9 points
- Acceptance: 6 points
- Compassion: 6 points
- Evocation: 6 points
- Summary: 3 points
- Response Factor: 10 points

Scoring Levels:
- Not Met (0/3): 0% of category points
- Minimally Met (1/3): 33.3% of category points
- Partially Met (2/3): 66.7% of category points  
- Fully Met (3/3): 100% of category points
"""

from typing import Dict, List, Optional, Tuple
from enum import Enum


class RubricContext(Enum):
    """Context for rubric criteria text substitution."""
    HPV = "HPV"
    OHI = "OHI"
    TOBACCO = "Tobacco"
    PERIO = "Perio"


class CategoryAssessment(Enum):
    """Granular assessment levels for each category."""
    NOT_MET = "Not Met"
    MINIMALLY_MET = "Minimally Met"
    PARTIALLY_MET = "Partially Met"
    FULLY_MET = "Fully Met"
    
    # Legacy support for binary scoring
    NEEDS_IMPROVEMENT = "Needs Improvement"  # Maps to NOT_MET
    MEETS_CRITERIA = "Meets Criteria"  # Maps to FULLY_MET


class MIRubric:
    """
    Updated 40-point MI Rubric with granular scoring.
    
    Total = 40 points across 6 categories.
    Each category supports granular assessment:
    - Not Met (0/3): 0% of category points
    - Minimally Met (1/3): 33.3% of category points
    - Partially Met (2/3): 66.7% of category points
    - Fully Met (3/3): 100% of category points
    
    Also supports legacy binary scoring for backward compatibility.
    """
    
    # Scoring multipliers for granular assessment
    ASSESSMENT_MULTIPLIERS = {
        CategoryAssessment.NOT_MET: 0.0,
        CategoryAssessment.MINIMALLY_MET: 0.333,
        CategoryAssessment.PARTIALLY_MET: 0.667,
        CategoryAssessment.FULLY_MET: 1.0,
        # Legacy binary scoring support
        CategoryAssessment.NEEDS_IMPROVEMENT: 0.0,
        CategoryAssessment.MEETS_CRITERIA: 1.0,
    }
    
    # Category definitions with point values and criteria
    CATEGORIES = {
        'Collaboration': {
            'points': 9,
            'criteria': {
                CategoryAssessment.FULLY_MET: [
                    'Introduces self, role, is engaging, welcoming',
                    'Collaborated with the patient by eliciting their ideas for change in {context} or by providing support as a partnership',
                    'Did not lecture; Did not try to "fix" the patient'
                ],
                CategoryAssessment.PARTIALLY_MET: [
                    'Mostly introduced self/role and was engaging',
                    'Some collaboration but could elicit more patient ideas',
                    'Mostly avoided lecturing but occasional directive language'
                ],
                CategoryAssessment.MINIMALLY_MET: [
                    'Brief introduction, limited engagement',
                    'Limited collaboration or partnership building',
                    'Some lecturing or fixing behavior evident'
                ],
                CategoryAssessment.NOT_MET: [
                    'Did not introduce self/role/engaging/welcoming',
                    'Did not collaborate by eliciting patient ideas or provide partnership support',
                    'Lectured or tried to "fix" the patient'
                ],
                # Legacy binary support
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
                CategoryAssessment.FULLY_MET: [
                    'Asks permission before eliciting accurate information about the {context}',
                    'Uses reflections to demonstrate listening'
                ],
                CategoryAssessment.PARTIALLY_MET: [
                    'Usually asks permission before sharing information',
                    'Some reflections but could be more consistent'
                ],
                CategoryAssessment.MINIMALLY_MET: [
                    'Occasionally asks permission',
                    'Few reflections or basic listening acknowledgments'
                ],
                CategoryAssessment.NOT_MET: [
                    'Did not ask permission and/or provided inaccurate information',
                    'Did not use reflections to demonstrate listening'
                ],
                # Legacy binary support
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
                CategoryAssessment.FULLY_MET: [
                    'Tries to understand the patient\'s perceptions and/or concerns with the {context}',
                    'Does not judge, shame or belittle the patient'
                ],
                CategoryAssessment.PARTIALLY_MET: [
                    'Shows interest in patient perceptions but could explore more deeply',
                    'Mostly non-judgmental with occasional directive tone'
                ],
                CategoryAssessment.MINIMALLY_MET: [
                    'Limited exploration of patient perceptions',
                    'Neutral tone but not actively empathetic'
                ],
                CategoryAssessment.NOT_MET: [
                    'Did not try to understand perceptions/concerns',
                    'Judged, shamed or belittled the patient'
                ],
                # Legacy binary support
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
                CategoryAssessment.FULLY_MET: [
                    'Uses open-ended questions for patient understanding OR stage of change OR eliciting change talk',
                    'Supports self-efficacy; emphasizes patient autonomy regarding the {context} (rolls with resistance)'
                ],
                CategoryAssessment.PARTIALLY_MET: [
                    'Uses some open-ended questions but also closed-ended ones',
                    'Some support for autonomy but could emphasize more'
                ],
                CategoryAssessment.MINIMALLY_MET: [
                    'Few open-ended questions, mostly closed-ended',
                    'Limited emphasis on patient autonomy'
                ],
                CategoryAssessment.NOT_MET: [
                    'Did not ask open-ended questions',
                    'Did not support self-efficacy/autonomy (did not roll with resistance)'
                ],
                # Legacy binary support
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
                CategoryAssessment.FULLY_MET: [
                    'Reflects big picture; checks accuracy of information and/or next steps'
                ],
                CategoryAssessment.PARTIALLY_MET: [
                    'Brief summary provided but could be more comprehensive'
                ],
                CategoryAssessment.MINIMALLY_MET: [
                    'Attempted summary but missed key points'
                ],
                CategoryAssessment.NOT_MET: [
                    'Does not summarize appropriately'
                ],
                # Legacy binary support
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
                CategoryAssessment.FULLY_MET: [
                    'Fast and intuitive responses to questions probed; acceptable average time throughout conversation'
                ],
                CategoryAssessment.PARTIALLY_MET: [
                    'Generally responsive but occasional delays'
                ],
                CategoryAssessment.MINIMALLY_MET: [
                    'Noticeably slow responses affecting conversation flow'
                ],
                CategoryAssessment.NOT_MET: [
                    'Delay in understanding and responding'
                ],
                # Legacy binary support
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
        context_map = {
            RubricContext.HPV: "HPV vaccination",
            RubricContext.OHI: "oral health",
            RubricContext.TOBACCO: "tobacco cessation",
            RubricContext.PERIO: "periodontitis and gum health"
        }
        context_text = context_map.get(context, "the health topic")
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
    Evaluates MI performance using the updated 40-point rubric with granular scoring.
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
                - total_score: float (0-40, with granular fractional scoring)
                - max_possible_score: int (40)
                - percentage: float
                - performance_band: str
                - categories: Dict with per-category details
        """
        notes = notes or {}
        category_results = {}
        total_score = 0.0
        
        # Process each category
        for category_name, category_info in MIRubric.CATEGORIES.items():
            # Handle Response Factor specially if latency data provided
            if category_name == 'Response Factor':
                if response_factor_latency is not None:
                    # Auto-determine assessment based on latency (using legacy for auto-calc)
                    assessment = (CategoryAssessment.MEETS_CRITERIA 
                                if response_factor_latency <= response_factor_threshold
                                else CategoryAssessment.NEEDS_IMPROVEMENT)
                else:
                    # Use provided assessment or default to Not Met if not provided
                    assessment = assessments.get(category_name, CategoryAssessment.NOT_MET)
            else:
                # Get assessment from provided assessments, default to Not Met
                assessment = assessments.get(category_name, CategoryAssessment.NOT_MET)
            
            # Calculate score using granular multiplier
            multiplier = MIRubric.ASSESSMENT_MULTIPLIERS.get(assessment, 0.0)
            points = category_info['points'] * multiplier
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
