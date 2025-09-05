"""
Standardized feedback template system for MI assessments.
Provides consistent feedback formatting between HPV and OHI assessments.
"""

from datetime import datetime
from typing import Dict, List, Optional
from scoring_utils import MIScorer


class FeedbackFormatter:
    """Handles standardized feedback formatting for MI assessments."""
    
    @staticmethod
    def format_evaluation_prompt(session_type: str, transcript: str, rag_context: str) -> str:
        """Generate standardized evaluation prompt for both HPV and OHI assessments."""
        return f"""
        Here is the {session_type} session transcript:
        {transcript}

        Important: Please only evaluate the **student's responses** (lines marked 'STUDENT'). Do not attribute change talk or motivational statements made by the patient to the student.

        Relevant MI Knowledge:
        {rag_context}

        Based on the MI rubric, evaluate the user's MI skills using the 30-point scoring system (7.5 points × 4 components).
        Provide feedback with scores for Collaboration (7.5 pts), Evocation (7.5 pts), Acceptance (7.5 pts), and Compassion (7.5 pts).

        Please evaluate each MI component and clearly state for each one:
        1. COLLABORATION: [Met/Partially Met/Not Met] - [specific feedback about partnership and rapport]
        2. EVOCATION: [Met/Partially Met/Not Met] - [specific feedback about drawing out patient motivations]
        3. ACCEPTANCE: [Met/Partially Met/Not Met] - [specific feedback about respecting autonomy and reflecting]
        4. COMPASSION: [Met/Partially Met/Not Met] - [specific feedback about warmth and non-judgmental approach]

        For each component, also provide specific suggestions for improvement.
        Include overall strengths and clear next-step suggestions for continued learning.
        """

    @staticmethod
    def format_feedback_for_display(feedback: str, timestamp: str, evaluator: str) -> Dict[str, str]:
        """Format feedback for consistent display in Streamlit."""
        return {
            'header': "### Session Feedback",
            'timestamp': f"**Evaluation Timestamp (UTC):** {timestamp}",
            'evaluator': f"**Evaluator:** {evaluator}",
            'separator': "---",
            'content': feedback
        }

    @staticmethod
    def format_feedback_for_pdf(feedback: str, timestamp: str, evaluator: str = None) -> str:
        """Format feedback for PDF generation with consistent structure."""
        header_parts = [
            "Session Feedback",
            f"Evaluation Timestamp (UTC): {timestamp}"
        ]
        
        if evaluator:
            header_parts.append(f"Evaluator: {evaluator}")
        
        header_parts.append("---")
        header_parts.append(feedback)
        
        return "\n".join(header_parts)

    @staticmethod
    def generate_component_breakdown_table(feedback: str) -> List[Dict[str, str]]:
        """Generate table data for component breakdown in PDF."""
        try:
            component_scores = MIScorer.parse_feedback_scores(feedback)
            table_data = []
            
            for score in component_scores:
                table_data.append({
                    'component': score.component,
                    'status': score.status,
                    'score': f"{score.score}",
                    'feedback': score.feedback
                })
            
            return table_data
        except Exception:
            # Fallback to empty table if parsing fails
            return []

    @staticmethod
    def extract_suggestions_from_feedback(feedback: str) -> List[str]:
        """Extract improvement suggestions from feedback text."""
        suggestions = []
        lines = feedback.split('\n')
        in_suggestions = False
        
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
                # Stop when we hit a new section or component
                if line.startswith(('1.', '2.', '3.', '4.')) and any(comp in line.upper() for comp in MIScorer.COMPONENTS.keys()):
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
        """Create standardized filename for PDF downloads."""
        from scoring_utils import validate_student_name
        
        # Sanitize student name for filename
        safe_name = validate_student_name(student_name)
        
        # Create base filename
        filename_parts = ["MI_Feedback_Report", safe_name]
        
        if persona:
            filename_parts.append(persona)
        
        filename = "_".join(filename_parts) + ".pdf"
        
        # Session type specific prefix
        if "HPV" in session_type.upper():
            return f"HPV_{filename}"
        elif "OHI" in session_type.upper():
            return f"OHI_{filename}"
        else:
            return filename


class FeedbackValidator:
    """Validates feedback content for consistency and completeness."""
    
    @staticmethod
    def validate_feedback_completeness(feedback: str) -> Dict[str, any]:
        """Validate that feedback contains all required components."""
        from scoring_utils import validate_feedback_format
        
        validation_result = {
            'is_valid': True,
            'missing_components': [],
            'warnings': []
        }
        
        # Check for required components
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
            component_scores = MIScorer.parse_feedback_scores(feedback)
            if len(component_scores) < len(MIScorer.COMPONENTS):
                validation_result['warnings'].append("Some components may not have parseable scores")
        except Exception as e:
            validation_result['warnings'].append(f"Score parsing issue: {str(e)}")
        
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