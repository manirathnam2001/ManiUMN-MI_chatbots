"""
Evaluation Service for MI Assessment

Provides a clean API for evaluating MI conversations using the new 40-point rubric.
Handles parsing of LLM feedback, context determination, and score calculation.
"""

import os
import re
from typing import Dict, List, Optional, Tuple
from rubric.mi_rubric import MIRubric, MIEvaluator, CategoryAssessment, RubricContext


class EvaluationService:
    """
    Service for evaluating MI conversations with the new 40-point rubric.
    """
    
    # Default Response Factor threshold (configurable via env var)
    DEFAULT_RESPONSE_FACTOR_THRESHOLD = 2.5
    
    @classmethod
    def get_response_factor_threshold(cls) -> float:
        """
        Get Response Factor threshold from config or environment.
        
        Returns:
            Threshold in seconds (default 2.5s)
        """
        try:
            threshold = float(os.environ.get('RESPONSE_FACTOR_THRESHOLD', cls.DEFAULT_RESPONSE_FACTOR_THRESHOLD))
            return threshold
        except (ValueError, TypeError):
            return cls.DEFAULT_RESPONSE_FACTOR_THRESHOLD
    
    @staticmethod
    def parse_llm_feedback(feedback_text: str) -> Dict[str, CategoryAssessment]:
        """
        Parse LLM-generated feedback to extract category assessments.
        
        Expected format patterns:
        - "Collaboration: Meets Criteria - ..."
        - "Collaboration (9 pts): Meets Criteria - ..."
        - "1. Collaboration: Meets Criteria - ..."
        - "**Collaboration**: Meets Criteria - ..."
        
        Args:
            feedback_text: Raw feedback text from LLM
            
        Returns:
            Dict mapping category names to CategoryAssessment values
        """
        assessments = {}
        lines = feedback_text.split('\n')
        
        # Regex patterns to match category lines
        patterns = [
            # Pattern: "Collaboration: Meets Criteria - ..." or with bold markdown
            r'^\*{0,2}(?:\d+\.\s*)?(?:\*{0,2})?(Collaboration|Acceptance|Compassion|Evocation|Summary|Response Factor)(?:\s*\([\d.]+\s*pts?\))?\s*:?\s*(?:\*{0,2})?\s*(Meets Criteria|Needs Improvement)(?:\*{0,2})?\s*[-–—]',
            # Pattern with brackets: "Collaboration: [Meets Criteria] - ..."
            r'^\*{0,2}(?:\d+\.\s*)?(?:\*{0,2})?(Collaboration|Acceptance|Compassion|Evocation|Summary|Response Factor)(?:\s*\([\d.]+\s*pts?\))?\s*:?\s*\[\s*(Meets Criteria|Needs Improvement)\s*\]\s*[-–—]',
        ]
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            for pattern in patterns:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    category = match.group(1).strip()
                    assessment_text = match.group(2).strip()
                    
                    # Normalize category name (handle variations)
                    category_normalized = category.title()
                    
                    # Map to CategoryAssessment enum
                    if 'meets' in assessment_text.lower() and 'needs' not in assessment_text.lower():
                        assessment = CategoryAssessment.MEETS_CRITERIA
                    else:
                        assessment = CategoryAssessment.NEEDS_IMPROVEMENT
                    
                    assessments[category_normalized] = assessment
                    break
        
        return assessments
    
    @staticmethod
    def determine_context(session_type: str) -> RubricContext:
        """
        Determine rubric context from session type.
        
        Args:
            session_type: Session type string (e.g., "HPV", "OHI", "HPV Vaccine", "Oral Health")
            
        Returns:
            RubricContext enum value
        """
        session_type_upper = session_type.upper()
        
        if 'HPV' in session_type_upper:
            return RubricContext.HPV
        elif 'OHI' in session_type_upper or 'ORAL' in session_type_upper:
            return RubricContext.OHI
        
        # Default to HPV if unclear
        return RubricContext.HPV
    
    @staticmethod
    def extract_evaluator_notes(feedback_text: str) -> Dict[str, str]:
        """
        Extract evaluator notes/feedback for each category from LLM feedback.
        
        Args:
            feedback_text: Raw feedback text from LLM
            
        Returns:
            Dict mapping category names to note strings
        """
        notes = {}
        lines = feedback_text.split('\n')
        
        # Pattern to extract category and notes
        pattern = r'^\*{0,2}(?:\d+\.\s*)?(?:\*{0,2})?(Collaboration|Acceptance|Compassion|Evocation|Summary|Response Factor)(?:\s*\([\d.]+\s*pts?\))?\s*:?\s*(?:\[)?\s*(?:Meets Criteria|Needs Improvement)\s*(?:\])?\s*(?:\*{0,2})?\s*[-–—]\s*(.+)$'
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                category = match.group(1).strip().title()
                note = match.group(2).strip()
                notes[category] = note
        
        return notes
    
    @classmethod
    def evaluate_session(
        cls,
        feedback_text: str,
        session_type: str = "HPV",
        response_latency: Optional[float] = None,
        response_threshold: Optional[float] = None
    ) -> Dict:
        """
        Complete evaluation of an MI session from LLM feedback.
        
        Args:
            feedback_text: Raw feedback text from LLM evaluation
            session_type: Type of session ("HPV", "OHI", etc.)
            response_latency: Optional average bot response latency in seconds
            response_threshold: Optional Response Factor threshold (default from config)
            
        Returns:
            Complete evaluation result dict from MIEvaluator.evaluate()
        """
        # Parse assessments from feedback
        assessments = cls.parse_llm_feedback(feedback_text)
        
        # Determine context
        context = cls.determine_context(session_type)
        
        # Extract notes
        notes = cls.extract_evaluator_notes(feedback_text)
        
        # Get threshold
        threshold = response_threshold or cls.get_response_factor_threshold()
        
        # Evaluate using MIEvaluator
        result = MIEvaluator.evaluate(
            assessments=assessments,
            context=context,
            notes=notes,
            response_factor_latency=response_latency,
            response_factor_threshold=threshold
        )
        
        return result
    
    @staticmethod
    def format_evaluation_summary(evaluation_result: Dict) -> str:
        """
        Format evaluation result as a human-readable summary.
        
        Args:
            evaluation_result: Result dict from evaluate_session()
            
        Returns:
            Formatted summary string
        """
        lines = []
        lines.append(f"Total Score: {evaluation_result['total_score']}/{evaluation_result['max_possible_score']}")
        lines.append(f"Percentage: {evaluation_result['percentage']:.1f}%")
        lines.append(f"Performance: {evaluation_result['performance_band']}")
        lines.append("")
        lines.append("Category Breakdown:")
        
        for category_name, category_data in evaluation_result['categories'].items():
            points = category_data['points']
            max_points = category_data['max_points']
            assessment = category_data['assessment']
            lines.append(f"  {category_name}: {points}/{max_points} - {assessment}")
            if category_data.get('notes'):
                lines.append(f"    {category_data['notes']}")
        
        return '\n'.join(lines)
