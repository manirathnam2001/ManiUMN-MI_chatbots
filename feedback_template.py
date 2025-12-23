"""
Standardized feedback template system for MI assessments.

This module provides consistent feedback formatting between HPV and OHI assessments,
including:
- Evaluation prompt generation for LLM-based assessment
- Feedback formatting for display and PDF output
- Component score breakdown and table generation
- Feedback validation and completeness checking
- Special character sanitization for PDF compatibility

The FeedbackFormatter class ensures consistent evaluation across both assessment types
while the FeedbackValidator class maintains data quality and completeness.
"""

from datetime import datetime
from typing import Dict, List
from time_utils import convert_to_minnesota_time

# Import new rubric system
try:
    from services.evaluation_service import EvaluationService
    from rubric.mi_rubric import MIRubric, RubricContext
    NEW_RUBRIC_AVAILABLE = True
except ImportError:
    NEW_RUBRIC_AVAILABLE = False

# Keep old scorer for backward compatibility during transition
try:
    from scoring_utils import MIScorer
    OLD_SCORER_AVAILABLE = True
except ImportError:
    OLD_SCORER_AVAILABLE = False


class FeedbackFormatter:
    """Handles standardized feedback formatting for MI assessments."""
    
    @staticmethod
    def format_evaluation_prompt(session_type: str, transcript: str, rag_context: str) -> str:
        """Generate standardized evaluation prompt for both HPV and OHI assessments using updated 40-point rubric with granular scoring."""
        # Determine context for criteria text
        context_map = {
            "HPV": "HPV vaccination",
            "OHI": "oral health",
            "TOBACCO": "tobacco cessation",
            "PERIO": "periodontitis and gum health"
        }
        
        context_text = "the health topic"
        for key, value in context_map.items():
            if key in session_type.upper():
                context_text = value
                break
        
        return f"""
        ## Motivational Interviewing Assessment - {session_type} Session

        You are evaluating a student's Motivational Interviewing (MI) skills based on their conversation with a simulated patient. Your role is to provide constructive, educational feedback that helps the student improve their MI competencies.

        ### Session Transcript:
        {transcript}

        **Important Instructions:**
        - Only evaluate the **student's responses** (lines marked 'User:', 'Student:', or similar indicators)
        - Do not attribute change talk or motivational statements made by the patient to the student
        - Focus on the student's use of MI techniques, not the patient's responses
        - **CRITICAL**: Include specific quotes from the student's responses to justify your assessment

        ### MI Knowledge Base:
        {rag_context}

        ### Assessment Framework:
        Evaluate the student's MI skills using the UPDATED 40-point rubric with granular scoring (6 categories, total 40 points).
        
        **Granular Scoring Guidelines:**
        - **Fully Met (3/3)**: Student demonstrates excellent competency = 100% of category points
        - **Partially Met (2/3)**: Student demonstrates good competency with room for improvement = 67% of category points
        - **Minimally Met (1/3)**: Student demonstrates basic competency but significant improvement needed = 33% of category points
        - **Not Met (0/3)**: Student does not adequately demonstrate the competency = 0 points

        ### Required Evaluation Format:
        Please structure your feedback exactly as follows for each category:

        **Collaboration (9 pts): [Fully Met/Partially Met/Minimally Met/Not Met] - [Specific feedback with conversation quotes]**
        Criteria for evaluation:
        - Introduces self, role, is engaging, welcoming
        - Collaborated with the patient by eliciting their ideas for change in {context_text} or by providing support as a partnership
        - Did not lecture; Did not try to "fix" the patient
        **Example quote(s) from conversation:** "[Direct quote from student that demonstrates this criterion]"
        
        **Acceptance (6 pts): [Fully Met/Partially Met/Minimally Met/Not Met] - [Specific feedback with conversation quotes]**
        Criteria for evaluation:
        - Asks permission before eliciting accurate information about the {context_text}
        - Uses reflections to demonstrate listening
        **Example quote(s) from conversation:** "[Direct quote from student]"
        
        **Compassion (6 pts): [Fully Met/Partially Met/Minimally Met/Not Met] - [Specific feedback with conversation quotes]**
        Criteria for evaluation:
        - Tries to understand the patient's perceptions and/or concerns with the {context_text}
        - Does not judge, shame or belittle the patient
        **Example quote(s) from conversation:** "[Direct quote from student]"
        
        **Evocation (6 pts): [Fully Met/Partially Met/Minimally Met/Not Met] - [Specific feedback with conversation quotes]**
        Criteria for evaluation:
        - Uses open-ended questions for patient understanding OR stage of change OR eliciting change talk
        - Supports self-efficacy; emphasizes patient autonomy regarding the {context_text} (rolls with resistance)
        **Example quote(s) from conversation:** "[Direct quote from student]"
        
        **Summary (3 pts): [Fully Met/Partially Met/Minimally Met/Not Met] - [Specific feedback with conversation quotes]**
        Criteria for evaluation:
        - Reflects big picture; checks accuracy of information and/or next steps
        **Example quote(s) from conversation:** "[Direct quote from student]"
        
        **Response Factor (10 pts): [Fully Met/Partially Met/Minimally Met/Not Met] - [Specific feedback]**
        Criteria for evaluation:
        - Fast and intuitive responses to questions probed; acceptable average time throughout conversation

        ### Additional Requirements:
        - **MUST include direct quotes** from the student's conversation to justify each score
        - For each category, cite 1-2 specific examples from the transcript
        - Highlight what the student did well (strengths)
        - Offer concrete suggestions for improvement with specific MI techniques
        - Include overall recommendations for continued learning and skill development
        - Maintain a supportive and educational tone throughout your feedback
        - Use granular scoring levels: Fully Met, Partially Met, Minimally Met, or Not Met

        Remember: Your feedback should help the student understand both what they did well and how they can improve their MI skills in future conversations. Total possible score is 40 points. **Always include conversation quotes to support your assessment.**
        """

    @staticmethod
    def format_feedback_common(feedback: str, timestamp: str, evaluator: str = None) -> str:
        """Common formatting for both display and PDF."""
        mn_timestamp = convert_to_minnesota_time(timestamp)
        parts = [
            "MI Performance Report",
            f"Evaluation Timestamp (Minnesota): {mn_timestamp}",
            f"Evaluator: {evaluator}" if evaluator else None,
            "---",
            feedback
        ]
        return "\n".join(filter(None, parts))

    @staticmethod
    def format_feedback_for_display(feedback: str, timestamp: str, evaluator: str) -> str:
        """Format feedback for display in app - show only core feedback content."""
        # Remove headers and metadata, only return the core feedback
        feedback_lines = feedback.split('\n')
        
        # Find where the actual feedback content starts
        # Look for category names (new rubric) or numbered components (old rubric)
        start_idx = 0
        category_names = ['Collaboration', 'Acceptance', 'Compassion', 'Evocation', 'Summary', 'Response Factor']
        
        for idx, line in enumerate(feedback_lines):
            stripped = line.strip()
            # Check for new rubric categories
            if any(cat in stripped for cat in category_names):
                start_idx = idx
                break
            # Check for old rubric numbered components (1-4)
            if any(stripped.startswith(f"{i}. ") or stripped.startswith(f"**{i}.") for i in range(1, 7)):
                start_idx = idx
                break
        
        # Join only the feedback content lines
        return '\n'.join(feedback_lines[start_idx:])

    @staticmethod
    def format_feedback_for_pdf(feedback: str, timestamp: str, evaluator: str = None) -> str:
        """Format feedback for PDF with complete header information."""
        mn_timestamp = convert_to_minnesota_time(timestamp)
        parts = [
            "MI Performance Report",
            f"Evaluation Timestamp (Minnesota): {mn_timestamp}",
            f"Evaluator: {evaluator}" if evaluator else None,
            "---",
            feedback
        ]
        return '\n'.join(filter(None, parts))

    @staticmethod
    def generate_component_breakdown_table(feedback: str, session_type: str = "HPV") -> List[Dict[str, str]]:
        """Generate table data for component breakdown in PDF using new 40-point rubric."""
        try:
            if NEW_RUBRIC_AVAILABLE:
                # Use new evaluation service
                result = EvaluationService.evaluate_session(feedback, session_type)
                table_data = []
                
                for category_name, category_data in result['categories'].items():
                    # Format scores as integers for user-facing display
                    points = int(round(category_data['points']))
                    max_points = category_data['max_points']
                    percentage = int(round((category_data['points'] / max_points) * 100))
                    score_display = f"{points} pts ({percentage}%)"
                    
                    table_data.append({
                        'component': category_name,
                        'status': category_data['assessment'],
                        'score': score_display,
                        'feedback': category_data['notes']
                    })
                
                return table_data
            elif OLD_SCORER_AVAILABLE:
                # Fallback to old scorer with integer formatting
                from scoring_utils import format_score_for_display
                component_scores = MIScorer.parse_feedback_scores(feedback)
                table_data = []
                
                for score in component_scores:
                    # Format score as integers for user-facing display
                    max_score = MIScorer.COMPONENTS[score.component]
                    points_int = format_score_for_display(score.score)
                    percentage = int(round((score.score / max_score) * 100))
                    score_display = f"{points_int} pts ({percentage}%)"
                    
                    table_data.append({
                        'component': score.component,
                        'status': score.status,
                        'score': score_display,
                        'feedback': score.feedback
                    })
                
                return table_data
            else:
                return []
        except Exception:
            # Fallback to empty table if parsing fails
            return []

    @staticmethod
    def extract_suggestions_from_feedback(feedback: str) -> List[str]:
        """Extract improvement suggestions from feedback text."""
        suggestions = []
        lines = feedback.split('\n')
        in_suggestions = False
        
        # Define category keywords for both old and new rubrics
        old_components = ['COLLABORATION', 'EVOCATION', 'ACCEPTANCE', 'COMPASSION']
        new_categories = ['Collaboration', 'Acceptance', 'Compassion', 'Evocation', 'Summary', 'Response Factor']
        all_categories = old_components + new_categories
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Look for suggestion indicators
            suggestion_indicators = [
                'suggestions for improvement',
                'next steps',
                'recommendations',
                'areas to focus',
                'improvement suggestions',
                'overall strengths',
                'continued learning'
            ]
            
            if any(indicator in line.lower() for indicator in suggestion_indicators):
                in_suggestions = True
                suggestions.append(line)
                continue
            
            if in_suggestions:
                # Stop when we hit a new section or component/category
                if line.startswith(('1.', '2.', '3.', '4.', '5.', '6.')) and any(cat in line for cat in all_categories):
                    in_suggestions = False
                    continue
                
                # Add suggestion lines
                if line.startswith('-') or line.startswith('•') or line.startswith('*'):
                    suggestions.append(line)
                elif line and not line.isupper():  # Avoid section headers
                    suggestions.append(line)
        
        return suggestions

    @staticmethod
    def create_download_filename(student_name: str, session_type: str, persona: str = None) -> str:
        """
        Create standardized filename for PDF downloads.
        
        Uses the new centralized naming convention: [Student]-[Bot]-[Persona] Feedback.pdf
        
        Args:
            student_name: Student's name
            session_type: Session type (e.g., "HPV Vaccine", "OHI", "Perio", "Tobacco")
            persona: Optional persona name
            
        Returns:
            Standardized filename string
        """
        from pdf_utils import construct_feedback_filename
        
        # Determine bot name from session type
        session_upper = session_type.upper()
        if 'HPV' in session_upper:
            bot_name = 'HPV'
        elif 'OHI' in session_upper or 'ORAL' in session_upper or 'DENTAL' in session_upper:
            bot_name = 'OHI'
        elif 'TOBACCO' in session_upper or 'SMOK' in session_upper or 'CESSATION' in session_upper:
            bot_name = 'Tobacco'
        elif 'PERIO' in session_upper or 'GUM' in session_upper or 'PERIODON' in session_upper:
            bot_name = 'Perio'
        else:
            # Fallback to extracting first word or using session type
            bot_name = session_type.split()[0] if session_type else 'MI'
        
        # Use centralized function
        return construct_feedback_filename(student_name, bot_name, persona)


class FeedbackValidator:
    """Validates feedback content for consistency and completeness."""
    
    @staticmethod
    def validate_feedback_completeness(feedback: str) -> Dict[str, any]:
        """Validate that feedback contains all required components/categories."""
        validation_result = {
            'is_valid': True,
            'missing_components': [],
            'warnings': []
        }
        
        # Check for new rubric categories first
        if NEW_RUBRIC_AVAILABLE:
            new_categories = ['Collaboration', 'Acceptance', 'Compassion', 'Evocation', 'Summary', 'Response Factor']
            found_categories = set()
            
            lines = feedback.split('\n')
            for line in lines:
                for category in new_categories:
                    if category in line:
                        found_categories.add(category)
            
            missing = set(new_categories) - found_categories
            if missing:
                validation_result['is_valid'] = False
                validation_result['missing_components'] = list(missing)
        elif OLD_SCORER_AVAILABLE:
            # Fallback to old rubric validation
            from scoring_utils import validate_feedback_format
            
            if not validate_feedback_format(feedback):
                validation_result['is_valid'] = False
                
                # Find which components are missing
                required_components = set(MIScorer.COMPONENTS.keys())
                found_components = set()
                
                lines = feedback.split('\n')
                for line in lines:
                    for component in required_components:
                        if component in line.upper():
                            found_components.add(component)
                
                validation_result['missing_components'] = list(required_components - found_components)
        
        # Check for score parsing issues
        try:
            if NEW_RUBRIC_AVAILABLE:
                result = EvaluationService.parse_llm_feedback(feedback)
                if len(result) < 6:
                    validation_result['warnings'].append("Some categories may not have parseable assessments")
            elif OLD_SCORER_AVAILABLE:
                component_scores = MIScorer.parse_feedback_scores(feedback)
                if len(component_scores) < len(MIScorer.COMPONENTS):
                    validation_result['warnings'].append("Some components may not have parseable scores")
        except Exception as e:
            validation_result['warnings'].append(f"Assessment parsing issue: {str(e)}")
        
        return validation_result

    @staticmethod
    def sanitize_special_characters(text: str) -> str:
        """Sanitize special characters for PDF compatibility."""
        if not text:
            return ""
        
        # Replace common problematic characters
        replacements = {
            '"': '"',  # Smart quotes
            '"': '"',
            ''': "'",
            ''': "'",
            '–': '-',  # En dash
            '—': '--', # Em dash
            '…': '...',
            '\u2013': '-',  # En dash unicode
            '\u2014': '--', # Em dash unicode
            '\u2018': "'",  # Left single quote
            '\u2019': "'",  # Right single quote
            '\u201c': '"',  # Left double quote
            '\u201d': '"',  # Right double quote
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        # Remove any remaining non-printable characters except common whitespace
        import re
        text = re.sub(r'[^\x20-\x7E\n\r\t]', '', text)
        
        return text