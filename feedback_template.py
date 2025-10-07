"""
Standardized feedback template system for MI assessments.
Provides consistent feedback formatting between HPV and OHI assessments.
"""

from datetime import datetime
from typing import Dict, List
from scoring_utils import MIScorer
from time_utils import convert_to_minnesota_time


class FeedbackFormatter:
    """Handles standardized feedback formatting for MI assessments."""
    
    @staticmethod
    def format_evaluation_prompt(session_type: str, transcript: str, rag_context: str) -> str:
        """Generate standardized evaluation prompt for both HPV and OHI assessments."""
        return f"""
        ## Motivational Interviewing Assessment - {session_type} Session

        You are evaluating a student's Motivational Interviewing (MI) skills based on their conversation with a simulated patient. Your role is to provide constructive, educational feedback that helps the student improve their MI competencies.

        ### Session Transcript:
        {transcript}

        **Important Instructions:**
        - Only evaluate the **student's responses** (lines marked 'STUDENT' or similar indicators)
        - Do not attribute change talk or motivational statements made by the patient to the student
        - Focus on the student's use of MI techniques, not the patient's responses

        ### MI Knowledge Base:
        {rag_context}

        ### Assessment Framework:
        Evaluate the student's MI skills using the 30-point scoring system (7.5 points per component).
        
        **Scoring Guidelines:**
        - **Met** (7.5 pts): Student demonstrates proficient use of the MI component
        - **Partially Met** (3.75 pts): Student shows some understanding but needs improvement
        - **Not Met** (0 pts): Student does not demonstrate the component or uses techniques contrary to MI

        ### Required Evaluation Format:
        Please structure your feedback exactly as follows for each component:

        **1. COLLABORATION (7.5 pts): [Met/Partially Met/Not Met] - [Specific feedback about partnership building and rapport development]**
        
        **2. EVOCATION (7.5 pts): [Met/Partially Met/Not Met] - [Specific feedback about drawing out patient motivations and exploring their perspective]**
        
        **3. ACCEPTANCE (7.5 pts): [Met/Partially Met/Not Met] - [Specific feedback about respecting patient autonomy and using reflective listening]**
        
        **4. COMPASSION (7.5 pts): [Met/Partially Met/Not Met] - [Specific feedback about demonstrating warmth and non-judgmental approach]**

        ### Additional Requirements:
        - For each component, provide specific examples from the conversation
        - Highlight what the student did well (strengths)
        - Offer concrete suggestions for improvement with specific MI techniques
        - Include overall recommendations for continued learning and skill development
        - Maintain a supportive and educational tone throughout your feedback

        Remember: Your feedback should help the student understand both what they did well and how they can improve their MI skills in future conversations.
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
        start_idx = 0
        for idx, line in enumerate(feedback_lines):
            # Look for lines that start with "1. ", "2. ", "3. ", or "4. " (component numbers)
            # or lines that start with "**1.", "**2.", etc. (bold markdown)
            stripped = line.strip()
            if any(stripped.startswith(f"{i}. ") or stripped.startswith(f"**{i}.") for i in range(1, 5)):
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
    def generate_component_breakdown_table(feedback: str) -> List[Dict[str, str]]:
        """Generate table data for component breakdown in PDF."""
        try:
            component_scores = MIScorer.parse_feedback_scores(feedback)
            table_data = []
            
            for score in component_scores:
                # Format score with proper parentheses and max score context
                max_score = MIScorer.COMPONENTS[score.component]
                score_display = f"{score.score:.1f} pts ({score.score/max_score*100:.0f}%)"
                
                table_data.append({
                    'component': score.component,
                    'status': score.status,
                    'score': score_display,
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