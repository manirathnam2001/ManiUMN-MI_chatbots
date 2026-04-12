"""
Evaluation Service for MI Assessment

Provides a clean API for evaluating MI conversations using the new 40-point rubric.
Handles parsing of LLM feedback, context determination, and score calculation.
"""

import os
import re
import logging
from typing import Dict, List, Optional, Tuple
from rubric.mi_rubric import MIRubric, MIEvaluator, CategoryAssessment, RubricContext

logger = logging.getLogger(__name__)


class EvaluationService:
    """
    Service for evaluating MI conversations with the new 40-point rubric.
    """
    
    # Default Response Factor threshold (configurable via env var)
    DEFAULT_RESPONSE_FACTOR_THRESHOLD = 2.5
    REQUIRED_CATEGORIES = ['Collaboration', 'Acceptance', 'Compassion', 'Evocation', 'Summary', 'Response Factor']
    
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
        
        Expected format patterns (supports both binary and granular scoring):
        - "Collaboration: Fully Met - ..."
        - "Collaboration: Partially Met (2/3) - ..."
        - "Collaboration (9 pts): Not Met - ..."
        - "1. Collaboration: Minimally Met - ..."
        - "**Collaboration**: Fully Met - ..."
        - Legacy: "Collaboration: Meets Criteria - ..."
        
        Args:
            feedback_text: Raw feedback text from LLM
            
        Returns:
            Dict mapping category names to CategoryAssessment values
        """
        assessments = {}
        lines = feedback_text.split('\n')
        
        # Regex patterns to match category lines (ordered most-specific to broadest)
        patterns = [
            # Pattern with dash: "Collaboration: Fully Met - ..." or with bold markdown
            r'^\*{0,2}(?:\d+\.\s*)?(?:\*{0,2})?(Collaboration|Acceptance|Compassion|Evocation|Summary|Response Factor)(?:\s*\([\d.]+\s*pts?\))?\s*:?\s*(?:\*{0,2})?\s*(Fully Met|Partially Met|Minimally Met|Not Met|Meets Criteria|Needs Improvement)(?:\s*\([\d/]+\))?(?:\*{0,2})?\s*[-–—]',
            # Pattern without dash: "Collaboration: Fully Met" or with bold markdown
            r'^\*{0,2}(?:\d+\.\s*)?(?:\*{0,2})?(Collaboration|Acceptance|Compassion|Evocation|Summary|Response Factor)(?:\s*\([\d.]+\s*pts?\))?\s*:?\s*(?:\*{0,2})?\s*(Fully Met|Partially Met|Minimally Met|Not Met|Meets Criteria|Needs Improvement)(?:\s*\([\d/]+\))?(?:\*{0,2})?\s*$',
            # Pattern with brackets: "Collaboration: [Fully Met] - ..."
            r'^\*{0,2}(?:\d+\.\s*)?(?:\*{0,2})?(Collaboration|Acceptance|Compassion|Evocation|Summary|Response Factor)(?:\s*\([\d.]+\s*pts?\))?\s*:?\s*\[\s*(Fully Met|Partially Met|Minimally Met|Not Met|Meets Criteria|Needs Improvement)(?:\s*[\d/]+)?\s*\]',
            # Fallback: loose match — category name anywhere on line + assessment level
            r'(?:\*{0,2})?(Collaboration|Acceptance|Compassion|Evocation|Summary|Response Factor)\b.*?\b(Fully Met|Partially Met|Minimally Met|Not Met|Meets Criteria|Needs Improvement)\b',
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
                    
                    # Map to CategoryAssessment enum (case-insensitive)
                    assessment_lower = assessment_text.lower()
                    if 'fully met' in assessment_lower or ('meets' in assessment_lower and 'needs' not in assessment_lower):
                        assessment = CategoryAssessment.FULLY_MET
                    elif 'partially met' in assessment_lower:
                        assessment = CategoryAssessment.PARTIALLY_MET
                    elif 'minimally met' in assessment_lower:
                        assessment = CategoryAssessment.MINIMALLY_MET
                    elif 'not met' in assessment_lower or 'needs improvement' in assessment_lower:
                        assessment = CategoryAssessment.NOT_MET
                    else:
                        # Default to not met if unclear
                        assessment = CategoryAssessment.NOT_MET
                    
                    assessments[category_normalized] = assessment
                    break
        
        if len(assessments) < 6:
            logger.warning(
                "Incomplete parse: found %d/6 categories. Missing: %s",
                len(assessments),
                [c for c in ['Collaboration', 'Acceptance', 'Compassion', 'Evocation', 'Summary', 'Response Factor']
                 if c.title() not in assessments and c not in assessments]
            )

        return assessments

    @staticmethod
    def extract_narrative_score(feedback_text: str) -> Optional[float]:
        """
        Fallback: extract a total score from narrative text when structured parsing fails.
        Looks for patterns like 'Total score: 33/40', 'Score: 26/40', '33 out of 40', etc.

        Returns:
            The extracted score as a float, or None if not found.
        """
        patterns = [
            r'(?i)total\s*(?:score|points?)\s*:?\s*(\d+(?:\.\d+)?)\s*/\s*40',
            r'(?i)score\s*(?:of\s*)?:?\s*(\d+(?:\.\d+)?)\s*/\s*40',
            r'(?i)(\d+(?:\.\d+)?)\s*(?:out of|/)\s*40\s*(?:points?|pts?)',
            r'(?i)(\d+(?:\.\d+)?)\s*/\s*40',
        ]
        for pattern in patterns:
            match = re.search(pattern, feedback_text)
            if match:
                score = float(match.group(1))
                if 0 <= score <= 40:
                    logger.info("Extracted narrative score: %.1f/40", score)
                    return score
        return None

    @staticmethod
    def determine_context(session_type: str) -> RubricContext:
        """
        Determine rubric context from session type.
        
        Args:
            session_type: Session type string (e.g., "HPV", "OHI", "Tobacco", "Perio", etc.)
            
        Returns:
            RubricContext enum value
        """
        # Normalize for comparison
        session_type_normalized = session_type.upper().strip()
        
        # Use more specific matching to avoid false positives
        # Check for exact matches or specific keywords
        if session_type_normalized in ['TOBACCO', 'TOBACCO CESSATION'] or \
           session_type_normalized.startswith('TOBACCO'):
            return RubricContext.TOBACCO
        elif session_type_normalized in ['PERIO', 'PERIODONTITIS', 'PERIODONTITIS AND GUM HEALTH'] or \
             session_type_normalized.startswith('PERIO'):
            return RubricContext.PERIO
        elif session_type_normalized in ['HPV', 'HPV VACCINE', 'HPV VACCINATION'] or \
             session_type_normalized.startswith('HPV'):
            return RubricContext.HPV
        elif session_type_normalized in ['OHI', 'ORAL HEALTH', 'ORAL HYGIENE', 'DENTAL HYGIENE'] or \
             session_type_normalized.startswith('OHI') or \
             session_type_normalized.startswith('ORAL') or \
             session_type_normalized.startswith('DENTAL'):
            return RubricContext.OHI
        
        # Fallback: Use containment checks as last resort
        if 'TOBACCO' in session_type_normalized or 'SMOK' in session_type_normalized or 'CESSATION' in session_type_normalized:
            return RubricContext.TOBACCO
        elif 'PERIO' in session_type_normalized or 'GUM' in session_type_normalized:
            return RubricContext.PERIO
        elif 'HPV' in session_type_normalized:
            return RubricContext.HPV
        elif 'OHI' in session_type_normalized or 'ORAL' in session_type_normalized or 'DENTAL' in session_type_normalized:
            return RubricContext.OHI
        
        # Default to HPV if still unclear
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
        
        # Pattern to extract category and notes (supports both binary and granular scoring)
        pattern = r'^\*{0,2}(?:\d+\.\s*)?(?:\*{0,2})?(Collaboration|Acceptance|Compassion|Evocation|Summary|Response Factor)(?:\s*\([\d.]+\s*pts?\))?\s*:?\s*(?:\[)?\s*(?:Fully Met|Partially Met|Minimally Met|Not Met|Meets Criteria|Needs Improvement)(?:\s*\([\d/]+\))?\s*(?:\])?\s*(?:\*{0,2})?\s*[-–—]\s*(.+)$'
        
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
    
    @staticmethod
    def generate_default_notes(category: str, assessment: CategoryAssessment, context: RubricContext) -> str:
        """
        Generate constructive default notes when LLM feedback lacks specific details.

        Args:
            category: Category name
            assessment: CategoryAssessment enum value
            context: RubricContext (HPV, OHI, TOBACCO, PERIO)

        Returns:
            Constructive feedback note
        """
        context_map = {
            RubricContext.HPV: "HPV vaccination",
            RubricContext.OHI: "oral health",
            RubricContext.TOBACCO: "tobacco cessation",
            RubricContext.PERIO: "periodontitis and gum health",
        }
        context_text = context_map.get(context, "the health topic")

        # Positive notes for FULLY MET and legacy MEETS_CRITERIA
        if assessment in [CategoryAssessment.MEETS_CRITERIA, CategoryAssessment.FULLY_MET]:
            # Positive constructive feedback for meeting criteria
            positive_notes = {
                'Collaboration': f'Demonstrated effective partnership and collaboration skills in discussing {context_text}.',
                'Acceptance': f'Showed respect for patient autonomy and used reflective listening when discussing {context_text}.',
                'Compassion': f'Displayed empathy and understanding of patient concerns regarding {context_text}.',
                'Evocation': f'Successfully used open-ended questions and supported patient self-efficacy regarding {context_text}.',
                'Summary': 'Provided appropriate summarization of key discussion points.',
                'Response Factor': 'Maintained timely and intuitive responses throughout the conversation.'
            }
            return positive_notes.get(category, 'Criteria met for this category.')
        else:
            # Constructive improvement suggestions for needs improvement
            improvement_notes = {
                'Collaboration': f'Consider introducing yourself more clearly and building stronger partnership around {context_text} discussions.',
                'Acceptance': f'Focus on asking permission before sharing information and using more reflective listening about {context_text}.',
                'Compassion': f'Work on understanding patient perceptions and avoiding judgmental language when discussing {context_text}.',
                'Evocation': f'Practice using more open-ended questions and supporting patient autonomy regarding {context_text}.',
                'Summary': 'Try to provide a clear summary reflecting the key points and potential next steps.',
                'Response Factor': 'Work on providing more timely and intuitive responses during the conversation.'
            }
            return improvement_notes.get(category, 'This area needs further development.')
    
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
        
        # Generate default notes for categories with empty notes
        for category_name in ['Collaboration', 'Acceptance', 'Compassion', 'Evocation', 'Summary', 'Response Factor']:
            if category_name in assessments and (category_name not in notes or not notes[category_name]):
                assessment = assessments[category_name]
                notes[category_name] = cls.generate_default_notes(category_name, assessment, context)

        # Fix Bug 7: If a category is Fully Met but the LLM-generated note contains
        # improvement language (e.g., "Consider...", "Try to..."), replace with praise.
        improvement_words = ['consider', 'try to', 'work on', 'practice', 'focus on', 'could improve']
        for category_name in assessments:
            if assessments[category_name] in [CategoryAssessment.FULLY_MET, CategoryAssessment.MEETS_CRITERIA]:
                note = notes.get(category_name, '')
                if note and any(word in note.lower() for word in improvement_words):
                    notes[category_name] = cls.generate_default_notes(category_name, assessments[category_name], context)
        
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

    @classmethod
    def get_evaluation_status(
        cls,
        feedback_text: str,
        session_type: str = "HPV",
        chat_history: Optional[List[Dict]] = None
    ) -> Dict[str, bool]:
        """
        Build canonical evaluation status gates for safe PDF export.

        Returns a status object with:
            - transcript_complete
            - evaluator_complete
            - score_validation_passed
            - pdf_export_allowed
        """
        assessments = cls.parse_llm_feedback(feedback_text)
        notes = cls.extract_evaluator_notes(feedback_text)

        evaluator_complete = all(category in assessments for category in cls.REQUIRED_CATEGORIES)
        notes_present = all(bool(notes.get(category, '').strip()) for category in cls.REQUIRED_CATEGORIES)

        transcript_complete = True
        if chat_history is not None:
            has_user_turn = any(msg.get('role', '').lower() == 'user' and msg.get('content', '').strip() for msg in chat_history)
            has_assistant_turn = any(msg.get('role', '').lower() == 'assistant' and msg.get('content', '').strip() for msg in chat_history)
            transcript_complete = has_user_turn and has_assistant_turn and len(chat_history) >= 2

        score_validation_passed = False
        if evaluator_complete:
            try:
                result = cls.evaluate_session(feedback_text, session_type)
                category_sum = sum(category_data['points'] for category_data in result['categories'].values())
                score_validation_passed = abs(category_sum - result['total_score']) < 1e-6 and bool(notes_present)
            except Exception:
                score_validation_passed = False

        pdf_export_allowed = transcript_complete and evaluator_complete and score_validation_passed
        return {
            'transcript_complete': transcript_complete,
            'evaluator_complete': evaluator_complete,
            'score_validation_passed': score_validation_passed,
            'pdf_export_allowed': pdf_export_allowed
        }

    @classmethod
    def build_normalized_result(
        cls,
        feedback_text: str,
        session_type: str = "HPV",
        response_latency: Optional[float] = None,
        response_threshold: Optional[float] = None
    ) -> Dict:
        """
        Build canonical EvaluationResult used by all report sections.
        """
        result = cls.evaluate_session(
            feedback_text=feedback_text,
            session_type=session_type,
            response_latency=response_latency,
            response_threshold=response_threshold
        )

        category_scores = {}
        category_notes = {}
        for category_name, category_data in result['categories'].items():
            category_scores[category_name] = category_data['points']
            category_notes[category_name] = category_data.get('notes', '')

        total_score = result['total_score']
        if abs(sum(category_scores.values()) - total_score) > 1e-6:
            raise ValueError("Score validation failed: category sum does not match total score")

        recommendations = []
        for category_name, category_data in result['categories'].items():
            if category_data['points'] < category_data['max_points']:
                note = category_data.get('notes', '').strip()
                if note:
                    recommendations.append(f"{category_name}: {note}")

        return {
            'category_scores': category_scores,
            'total_score': total_score,
            'max_score': result['max_possible_score'],
            'category_notes': category_notes,
            'category_assessments': {k: v['assessment'] for k, v in result['categories'].items()},
            'performance_band': result['performance_band'],
            'percentage': result['percentage'],
            'recommendations': recommendations,
            'categories': result['categories']
        }
    
    @staticmethod
    def format_evaluation_summary(evaluation_result: Dict) -> str:
        """
        Format evaluation result as a human-readable summary.
        
        Args:
            evaluation_result: Result dict from evaluate_session()
            
        Returns:
            Formatted summary string
        """
        # Format scores as integers for user-facing display
        total_score = int(round(evaluation_result['total_score']))
        max_score = evaluation_result['max_possible_score']
        percentage = int(round(evaluation_result['percentage']))
        
        lines = []
        lines.append(f"Total Score: {total_score}/{max_score}")
        lines.append(f"Percentage: {percentage}%")
        lines.append(f"Performance: {evaluation_result['performance_band']}")
        lines.append("")
        lines.append("Category Breakdown:")
        
        for category_name, category_data in evaluation_result['categories'].items():
            # Format category scores as integers
            points = int(round(category_data['points']))
            max_points = category_data['max_points']
            assessment = category_data['assessment']
            lines.append(f"  {category_name}: {points}/{max_points} - {assessment}")
            if category_data.get('notes'):
                lines.append(f"    {category_data['notes']}")
        
        return '\n'.join(lines)
