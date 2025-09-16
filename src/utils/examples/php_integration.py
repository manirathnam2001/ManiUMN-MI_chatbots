"""
php_integration.py

Python helper module to integrate existing Streamlit MI chatbots with the new 
LAMP-stack PHP utilities for database storage, logging, and PDF generation.

This module provides a clean interface for Python applications to interact 
with PHP backend services through HTTP requests.

Author: MI Chatbots System
Version: 1.0.0
"""

import requests
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import time

class PHPIntegrationError(Exception):
    """Custom exception for PHP integration errors"""
    pass

class MIPhpIntegration:
    """
    Integration client for connecting Python MI chatbots with PHP utilities
    """
    
    def __init__(self, base_url: str = "http://localhost/mi_chatbots/src/utils/examples/mi_bot_integration.php"):
        """
        Initialize the PHP integration client
        
        Args:
            base_url: Base URL of the PHP integration endpoint
        """
        self.base_url = base_url
        self.session_id = None
        self.logger = self._setup_logging()
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for the integration client"""
        logger = logging.getLogger('mi_php_integration')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
        
    def _make_request(self, action: str, method: str = 'POST', data: Optional[Dict] = None, 
                     params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make HTTP request to PHP backend
        
        Args:
            action: Action to perform
            method: HTTP method (GET, POST)
            data: Data to send in request body
            params: URL parameters
            
        Returns:
            Response data as dictionary
            
        Raises:
            PHPIntegrationError: If request fails
        """
        try:
            url = self.base_url
            
            # Add action to parameters
            if params is None:
                params = {}
            params['action'] = action
            
            # Make request
            if method.upper() == 'POST':
                response = requests.post(
                    url,
                    params=params,
                    json=data,
                    headers={'Content-Type': 'application/json'},
                    timeout=30
                )
            else:
                response = requests.get(
                    url,
                    params=params,
                    timeout=30
                )
            
            # Parse response
            if response.headers.get('content-type', '').startswith('application/json'):
                result = response.json()
            else:
                # Handle PDF or other binary responses
                return {
                    'success': True,
                    'content': response.content,
                    'content_type': response.headers.get('content-type', 'application/octet-stream'),
                    'filename': self._extract_filename_from_headers(response.headers)
                }
            
            # Check for errors
            if response.status_code != 200 or not result.get('success', False):
                error_msg = result.get('error', f'HTTP {response.status_code}')
                raise PHPIntegrationError(f"Request failed: {error_msg}")
                
            return result
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed: {e}")
            raise PHPIntegrationError(f"Network error: {e}")
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error: {e}")
            raise PHPIntegrationError(f"Invalid JSON response: {e}")
            
    def _extract_filename_from_headers(self, headers: Dict[str, str]) -> Optional[str]:
        """Extract filename from Content-Disposition header"""
        disposition = headers.get('content-disposition', '')
        if 'filename=' in disposition:
            return disposition.split('filename=')[1].strip('"')
        return None
        
    def create_session(self, student_name: str, session_type: str = 'HPV', 
                      persona: Optional[str] = None) -> str:
        """
        Create a new MI session
        
        Args:
            student_name: Name of the student
            session_type: Type of session (HPV, OHI, etc.)
            persona: Selected persona/patient character
            
        Returns:
            Session ID
            
        Raises:
            PHPIntegrationError: If session creation fails
        """
        try:
            data = {
                'student_name': student_name,
                'session_type': session_type,
                'persona': persona
            }
            
            result = self._make_request('create_session', data=data)
            self.session_id = result['session_id']
            
            self.logger.info(f"Session created: {self.session_id} for student: {student_name}")
            return self.session_id
            
        except Exception as e:
            self.logger.error(f"Failed to create session: {e}")
            raise
            
    def store_conversation(self, messages: List[Dict[str, str]], 
                          session_id: Optional[str] = None) -> bool:
        """
        Store conversation messages in database
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            session_id: Session ID (uses current session if None)
            
        Returns:
            True if successful
            
        Raises:
            PHPIntegrationError: If storage fails
        """
        try:
            if session_id is None:
                session_id = self.session_id
                
            if not session_id:
                raise PHPIntegrationError("No active session")
                
            data = {
                'session_id': session_id,
                'messages': messages
            }
            
            result = self._make_request('store_conversation', data=data)
            
            self.logger.info(f"Stored {len(messages)} messages for session: {session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to store conversation: {e}")
            raise
            
    def submit_feedback(self, feedback_content: str, evaluator: str = 'AI Assistant',
                       session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Submit feedback for MI assessment
        
        Args:
            feedback_content: Complete feedback text with component scoring
            evaluator: Name of the evaluator
            session_id: Session ID (uses current session if None)
            
        Returns:
            Dictionary with score breakdown and success status
            
        Raises:
            PHPIntegrationError: If submission fails
        """
        try:
            if session_id is None:
                session_id = self.session_id
                
            if not session_id:
                raise PHPIntegrationError("No active session")
                
            data = {
                'session_id': session_id,
                'feedback_content': feedback_content,
                'evaluator': evaluator,
                'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            result = self._make_request('submit_feedback', data=data)
            
            self.logger.info(f"Feedback submitted for session: {session_id}")
            return result.get('score_breakdown', {})
            
        except Exception as e:
            self.logger.error(f"Failed to submit feedback: {e}")
            raise
            
    def generate_pdf(self, session_id: Optional[str] = None, 
                    download_mode: str = 'attachment') -> bytes:
        """
        Generate PDF performance report
        
        Args:
            session_id: Session ID (uses current session if None)
            download_mode: 'attachment' or 'inline'
            
        Returns:
            PDF content as bytes
            
        Raises:
            PHPIntegrationError: If PDF generation fails
        """
        try:
            if session_id is None:
                session_id = self.session_id
                
            if not session_id:
                raise PHPIntegrationError("No active session")
                
            params = {
                'session_id': session_id,
                'download': download_mode
            }
            
            result = self._make_request('generate_pdf', method='GET', params=params)
            
            if 'content' in result:
                self.logger.info(f"PDF generated for session: {session_id}")
                return result['content']
            else:
                raise PHPIntegrationError("No PDF content in response")
                
        except Exception as e:
            self.logger.error(f"Failed to generate PDF: {e}")
            raise
            
    def get_session_data(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve complete session data
        
        Args:
            session_id: Session ID (uses current session if None)
            
        Returns:
            Complete session data including conversation, feedback, and metrics
            
        Raises:
            PHPIntegrationError: If retrieval fails
        """
        try:
            if session_id is None:
                session_id = self.session_id
                
            if not session_id:
                raise PHPIntegrationError("No active session")
                
            params = {'session_id': session_id}
            result = self._make_request('get_session', method='GET', params=params)
            
            self.logger.info(f"Retrieved session data for: {session_id}")
            return result.get('data', {})
            
        except Exception as e:
            self.logger.error(f"Failed to get session data: {e}")
            raise
            
    def get_student_sessions(self, student_name: str, limit: int = 50, 
                           offset: int = 0) -> List[Dict[str, Any]]:
        """
        Retrieve session history for a student
        
        Args:
            student_name: Name of the student
            limit: Maximum number of sessions to return
            offset: Pagination offset
            
        Returns:
            List of session dictionaries
            
        Raises:
            PHPIntegrationError: If retrieval fails
        """
        try:
            params = {
                'student_name': student_name,
                'limit': limit,
                'offset': offset
            }
            
            result = self._make_request('get_student_sessions', method='GET', params=params)
            
            sessions = result.get('sessions', [])
            self.logger.info(f"Retrieved {len(sessions)} sessions for student: {student_name}")
            
            return sessions
            
        except Exception as e:
            self.logger.error(f"Failed to get student sessions: {e}")
            raise
            
    def check_health(self) -> Dict[str, Any]:
        """
        Check system health status
        
        Returns:
            System health information
            
        Raises:
            PHPIntegrationError: If health check fails
        """
        try:
            result = self._make_request('health_check', method='GET')
            
            self.logger.info("Health check completed")
            return result
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            raise

# ============================================================================
# Streamlit Integration Helpers
# ============================================================================

class StreamlitMIIntegration:
    """
    Helper class specifically for Streamlit MI applications
    """
    
    def __init__(self, php_client: MIPhpIntegration):
        self.php = php_client
        
    def initialize_session_state(self):
        """Initialize Streamlit session state for PHP integration"""
        import streamlit as st
        
        if 'php_session_id' not in st.session_state:
            st.session_state.php_session_id = None
        if 'php_integration_enabled' not in st.session_state:
            st.session_state.php_integration_enabled = True
        if 'session_data_synced' not in st.session_state:
            st.session_state.session_data_synced = False
            
    def start_session(self, student_name: str, session_type: str, persona: str = None):
        """Start session with automatic Streamlit state management"""
        import streamlit as st
        
        try:
            session_id = self.php.create_session(student_name, session_type, persona)
            st.session_state.php_session_id = session_id
            st.session_state.session_data_synced = False
            return session_id
        except Exception as e:
            st.error(f"Failed to start database session: {e}")
            return None
            
    def sync_conversation(self, chat_history: List[Dict[str, str]]):
        """Sync conversation with database"""
        import streamlit as st
        
        if not st.session_state.get('php_integration_enabled', False):
            return
            
        try:
            session_id = st.session_state.get('php_session_id')
            if session_id and chat_history:
                self.php.store_conversation(chat_history, session_id)
                st.session_state.session_data_synced = True
        except Exception as e:
            st.warning(f"Failed to sync conversation: {e}")
            
    def submit_feedback_with_display(self, feedback_content: str, evaluator: str = 'AI'):
        """Submit feedback and display results in Streamlit"""
        import streamlit as st
        
        try:
            session_id = st.session_state.get('php_session_id')
            if session_id:
                score_breakdown = self.php.submit_feedback(feedback_content, evaluator, session_id)
                
                # Display score summary
                if score_breakdown and 'total_score' in score_breakdown:
                    st.success(
                        f"**Total Score: {score_breakdown['total_score']:.1f} / "
                        f"{score_breakdown['total_possible']:.1f} "
                        f"({score_breakdown['percentage']:.1f}%)**"
                    )
                    
                return score_breakdown
        except Exception as e:
            st.error(f"Failed to submit feedback: {e}")
            return None
            
    def generate_pdf_download(self, filename_override: str = None):
        """Generate PDF with Streamlit download button"""
        import streamlit as st
        import io
        
        try:
            session_id = st.session_state.get('php_session_id')
            if not session_id:
                st.error("No active session for PDF generation")
                return
                
            # Show generation status
            with st.spinner('Generating PDF report...'):
                pdf_content = self.php.generate_pdf(session_id)
                
            # Create download button
            filename = filename_override or f"MI_Performance_Report_{int(time.time())}.pdf"
            
            st.download_button(
                label="📥 Download MI Performance Report (PDF)",
                data=pdf_content,
                file_name=filename,
                mime="application/pdf",
                help="Download comprehensive PDF report with scores, feedback, and conversation transcript"
            )
            
            return True
            
        except Exception as e:
            st.error(f"Failed to generate PDF: {e}")
            return False
            
    def display_session_history(self, student_name: str):
        """Display session history for a student"""
        import streamlit as st
        import pandas as pd
        
        try:
            sessions = self.php.get_student_sessions(student_name, limit=20)
            
            if sessions:
                # Convert to DataFrame for display
                df_data = []
                for session in sessions:
                    df_data.append({
                        'Date': session.get('created_at', 'Unknown'),
                        'Session Type': session.get('session_type', 'Unknown'),
                        'Persona': session.get('persona', 'None'),
                        'Status': session.get('status', 'Unknown'),
                        'Score': f"{session.get('percentage_score', 0):.1f}%" if session.get('percentage_score') else 'N/A'
                    })
                    
                df = pd.DataFrame(df_data)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No previous sessions found for this student.")
                
        except Exception as e:
            st.error(f"Failed to load session history: {e}")

# ============================================================================
# Example Usage Functions
# ============================================================================

def example_basic_usage():
    """Example of basic PHP integration usage"""
    
    # Initialize client
    client = MIPhpIntegration("http://localhost/mi_chatbots/src/utils/examples/mi_bot_integration.php")
    
    try:
        # Check system health
        health = client.check_health()
        print(f"System status: {health['status']}")
        
        # Create session
        session_id = client.create_session("John Doe", "HPV", "Alex - Hesitant Patient")
        print(f"Created session: {session_id}")
        
        # Store conversation
        messages = [
            {"role": "assistant", "content": "Hello! I heard you wanted to discuss the HPV vaccine?"},
            {"role": "user", "content": "Yes, I have some concerns about it."},
            {"role": "assistant", "content": "I understand. What specific concerns do you have?"}
        ]
        
        client.store_conversation(messages)
        print("Conversation stored successfully")
        
        # Submit feedback
        feedback = """**1. COLLABORATION (7.5 pts): [Met] - Excellent partnership building**
        
**2. EVOCATION (7.5 pts): [Partially Met] - Good questions, could explore more**

**3. ACCEPTANCE (7.5 pts): [Met] - Respected patient autonomy**

**4. COMPASSION (7.5 pts): [Not Met] - Needs more warmth and empathy**"""
        
        score_breakdown = client.submit_feedback(feedback)
        print(f"Feedback submitted. Total score: {score_breakdown.get('total_score', 'N/A')}")
        
        # Generate PDF
        pdf_content = client.generate_pdf()
        with open("mi_report.pdf", "wb") as f:
            f.write(pdf_content)
        print("PDF generated and saved")
        
        # Get session data
        session_data = client.get_session_data()
        print(f"Session has {len(session_data.get('conversation', []))} messages")
        
    except PHPIntegrationError as e:
        print(f"Integration error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

def example_streamlit_integration():
    """Example of Streamlit-specific integration"""
    
    # This would be used within a Streamlit app
    code_example = '''
import streamlit as st
from php_integration import MIPhpIntegration, StreamlitMIIntegration

# Initialize integration
php_client = MIPhpIntegration("http://your-server.com/mi_bot_integration.php")
st_integration = StreamlitMIIntegration(php_client)

# Initialize session state
st_integration.initialize_session_state()

# Student name input
student_name = st.text_input("Student Name")

if student_name and st.button("Start Session"):
    session_id = st_integration.start_session(student_name, "HPV", "Alex")
    if session_id:
        st.success(f"Session started: {session_id}")

# Chat interface (existing code)
if st.session_state.chat_history:
    # Sync conversation periodically
    st_integration.sync_conversation(st.session_state.chat_history)

# Feedback submission (existing code)
if feedback_generated:
    score_breakdown = st_integration.submit_feedback_with_display(feedback)
    
    # PDF download
    st_integration.generate_pdf_download()
    
    # Show session history
    st_integration.display_session_history(student_name)
'''
    
    print("Streamlit integration example:")
    print(code_example)

if __name__ == "__main__":
    # Run examples
    print("Running basic usage example...")
    example_basic_usage()
    
    print("\nStreamlit integration example:")
    example_streamlit_integration()