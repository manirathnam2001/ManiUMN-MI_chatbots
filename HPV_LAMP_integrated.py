"""
HPV_LAMP_integrated.py

Modified version of HPV.py showing integration with LAMP-stack PHP utilities.
This demonstrates how existing Streamlit MI chatbots can use the new PHP backend
for database storage, logging, and PDF generation.

Key changes from original HPV.py:
- Added PHP integration for session management
- Database storage for conversations and feedback
- Enhanced PDF generation via PHP backend
- Comprehensive logging and traceability
- Backwards compatibility with original functionality

Author: MI Chatbots System
Version: 1.0.0 (LAMP-integrated)
"""

import streamlit as st
import requests
import json
import time
from datetime import datetime
from groq import Groq
from sentence_transformers import SentenceTransformer
import numpy as np
import faiss

# Import the existing utilities (backwards compatibility)
from feedback_template import FeedbackFormatter
from scoring_utils import MIScorer, validate_student_name
from pdf_utils import generate_pdf_report
from chat_utils import initialize_session_state, display_chat_history

# Import PHP integration helper
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src', 'utils', 'examples'))

try:
    from php_integration import MIPhpIntegration, StreamlitMIIntegration, PHPIntegrationError
    PHP_INTEGRATION_AVAILABLE = True
except ImportError:
    st.warning("⚠️ PHP integration not available. Running in legacy mode.")
    PHP_INTEGRATION_AVAILABLE = False

# ============================================================================
# Configuration and Setup
# ============================================================================

# Configure Streamlit page
st.set_page_config(
    page_title="HPV MI Practice App (LAMP-Integrated)",
    page_icon="🧬",
    layout="wide"
)

# Initialize session state
initialize_session_state()

# PHP Integration Setup
if PHP_INTEGRATION_AVAILABLE:
    # Initialize PHP integration (adjust URL for your environment)
    PHP_BACKEND_URL = os.getenv('PHP_BACKEND_URL', 
                               'http://localhost/mi_chatbots/src/utils/examples/mi_bot_integration.php')
    
    if 'php_client' not in st.session_state:
        st.session_state.php_client = MIPhpIntegration(PHP_BACKEND_URL)
        st.session_state.streamlit_integration = StreamlitMIIntegration(st.session_state.php_client)
        st.session_state.streamlit_integration.initialize_session_state()

# Load configuration
try:
    with open("config.json") as f:
        config = json.load(f)
    client = Groq(api_key=config["groq_api_key"])
except FileNotFoundError:
    st.error("config.json file not found. Please add your Groq API key.")
    st.stop()

# ============================================================================
# Enhanced Persona Management with PHP Integration
# ============================================================================

# HPV Personas with enhanced metadata for database storage
hpv_personas = {
    "Alex - Hesitant Patient": {
        "description": "A hesitant patient with concerns about HPV vaccine safety and necessity",
        "initial_message": "Hi, I heard you wanted to discuss the HPV vaccine with me. To be honest, I have some concerns about it. I've read things online that worry me.",
        "personality_traits": ["cautious", "questioning", "research-oriented"],
        "key_concerns": ["safety", "necessity", "side_effects"]
    },
    "Jordan - Nervous Teen": {
        "description": "A nervous teenager uncomfortable discussing sexual health topics",
        "initial_message": "Um... hi. My mom said I should talk to you about some vaccine? I'm not really sure what it's for and I'm kind of nervous about it.",
        "personality_traits": ["nervous", "uninformed", "embarrassed"],
        "key_concerns": ["embarrassment", "pain", "parental_pressure"]
    },
    "Taylor - Informed but Conflicted": {
        "description": "An informed patient who understands benefits but has specific concerns",
        "initial_message": "Hello! I've been doing research about the HPV vaccine and I understand it can prevent certain cancers, but I have some specific questions about timing and effectiveness.",
        "personality_traits": ["informed", "analytical", "thorough"],
        "key_concerns": ["timing", "effectiveness", "cost"]
    }
}

# ============================================================================
# Main Application Interface
# ============================================================================

st.title("🧬 HPV MI Practice App (LAMP-Integrated)")
st.markdown("### Practice Motivational Interviewing Skills for HPV Vaccination Discussions")

# Enhanced sidebar with PHP integration status
with st.sidebar:
    st.header("🎭 Choose Your Patient")
    
    # PHP Integration Status
    if PHP_INTEGRATION_AVAILABLE:
        try:
            health = st.session_state.php_client.check_health()
            if health.get('status') == 'healthy':
                st.success("🔗 PHP Backend: Connected")
            else:
                st.warning("🔗 PHP Backend: Limited")
        except:
            st.error("🔗 PHP Backend: Unavailable")
            st.info("Running in legacy mode")
    else:
        st.info("🔗 Running in legacy mode (no PHP backend)")
    
    # Student Information (required for database integration)
    st.markdown("#### Student Information")
    student_name = st.text_input("Your Name", 
                                help="Required for session tracking and PDF reports")
    
    # Persona Selection
    selected_persona_name = st.selectbox("Select a patient persona:", list(hpv_personas.keys()))
    
    if selected_persona_name:
        persona_info = hpv_personas[selected_persona_name]
        st.markdown(f"**{selected_persona_name}**")
        st.write(persona_info["description"])
        
        with st.expander("Persona Details"):
            st.write("**Personality Traits:**", ", ".join(persona_info["personality_traits"]))
            st.write("**Key Concerns:**", ", ".join(persona_info["key_concerns"]))
    
    # Session Management
    if st.button("🚀 Start New Session"):
        if not student_name:
            st.error("Please enter your name to start a session")
        else:
            try:
                # Validate student name
                validated_name = validate_student_name(student_name)
                
                # Clear existing session state
                st.session_state.selected_persona = selected_persona_name
                st.session_state.chat_history = []
                st.session_state.feedback = None
                
                # Start PHP session if available
                if PHP_INTEGRATION_AVAILABLE:
                    session_id = st.session_state.streamlit_integration.start_session(
                        validated_name, "HPV", selected_persona_name
                    )
                    if session_id:
                        st.success(f"Session started: {session_id[:12]}...")
                    else:
                        st.warning("Session started in legacy mode")
                
                st.rerun()
                
            except ValueError as e:
                st.error(f"Invalid student name: {e}")
            except Exception as e:
                st.error(f"Failed to start session: {e}")

# ============================================================================
# Chat Interface with Enhanced Integration
# ============================================================================

if st.session_state.selected_persona is not None:
    persona = hpv_personas[st.session_state.selected_persona]
    
    # Display chat history
    display_chat_history()
    
    # Initialize conversation with persona's opening message
    if not st.session_state.chat_history:
        initial_message = {
            "role": "assistant", 
            "content": persona["initial_message"]
        }
        st.session_state.chat_history.append(initial_message)
        
        # Sync with PHP backend
        if PHP_INTEGRATION_AVAILABLE:
            st.session_state.streamlit_integration.sync_conversation([initial_message])
        
        st.rerun()

    # Chat input
    user_prompt = st.chat_input("Your response...")
    
    if user_prompt:
        # Add user message
        user_message = {"role": "user", "content": user_prompt}
        st.session_state.chat_history.append(user_message)
        st.chat_message("user").markdown(user_prompt)
        
        # Generate AI response with enhanced context
        try:
            # Prepare enhanced system message with persona context
            system_message = {
                "role": "system",
                "content": f"""You are roleplaying as {st.session_state.selected_persona}. 
                
Persona Details:
- Description: {persona['description']}
- Personality: {', '.join(persona['personality_traits'])}
- Key Concerns: {', '.join(persona['key_concerns'])}

Stay in character and respond naturally to the healthcare provider's motivational interviewing techniques. 
Be realistic about your concerns and reactions. Allow yourself to be gradually influenced by good MI techniques, 
but maintain your character's personality throughout the conversation.

Current conversation context: This is an HPV vaccine discussion where you're talking with a healthcare provider 
who is practicing motivational interviewing skills."""
            }
            
            # Prepare messages for AI
            messages = [system_message] + st.session_state.chat_history
            
            # Get AI response
            response = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=messages,
                max_tokens=500,
                temperature=0.8
            )
            
            # Add AI response
            assistant_message = {
                "role": "assistant", 
                "content": response.choices[0].message.content
            }
            st.session_state.chat_history.append(assistant_message)
            st.chat_message("assistant").markdown(assistant_message["content"])
            
            # Enhanced sync with PHP backend (include metadata)
            if PHP_INTEGRATION_AVAILABLE:
                # Add metadata for better tracking
                enhanced_user_message = {
                    **user_message,
                    "timestamp": datetime.utcnow().isoformat(),
                    "persona": st.session_state.selected_persona
                }
                enhanced_assistant_message = {
                    **assistant_message,
                    "timestamp": datetime.utcnow().isoformat(),
                    "model": "llama3-8b-8192",
                    "persona": st.session_state.selected_persona
                }
                
                st.session_state.streamlit_integration.sync_conversation([
                    enhanced_user_message,
                    enhanced_assistant_message
                ])
            
        except Exception as e:
            st.error(f"Error generating response: {e}")

# ============================================================================
# Enhanced Feedback and Assessment
# ============================================================================

if st.session_state.selected_persona is not None and len(st.session_state.chat_history) > 2:
    st.markdown("---")
    st.markdown("### 📋 Get MI Assessment")
    
    if st.button("Generate Feedback"):
        if not student_name:
            st.error("Please enter your name in the sidebar to generate feedback")
        else:
            with st.spinner("Analyzing your MI skills..."):
                try:
                    # Prepare conversation transcript
                    transcript = "\n\n".join([
                        f"{'STUDENT' if msg['role'] == 'user' else 'PATIENT'}: {msg['content']}"
                        for msg in st.session_state.chat_history
                    ])
                    
                    # Load RAG context for HPV
                    try:
                        with open("hpv_rubrics/hpv_rubric_1.txt", "r") as f:
                            rag_context = f.read()
                    except FileNotFoundError:
                        rag_context = "Standard MI evaluation criteria"
                    
                    # Generate evaluation prompt
                    evaluation_prompt = FeedbackFormatter.format_evaluation_prompt(
                        "HPV Vaccine", transcript, rag_context
                    )
                    
                    # Get AI feedback
                    feedback_response = client.chat.completions.create(
                        model="llama3-70b-8192",
                        messages=[{"role": "user", "content": evaluation_prompt}],
                        max_tokens=2000,
                        temperature=0.3
                    )
                    
                    feedback_content = feedback_response.choices[0].message.content
                    current_timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
                    evaluator = "AI Assistant (Enhanced)"
                    
                    # Store feedback in session state
                    st.session_state.feedback = {
                        'content': feedback_content,
                        'timestamp': current_timestamp,
                        'evaluator': evaluator
                    }
                    
                    # Submit to PHP backend if available
                    if PHP_INTEGRATION_AVAILABLE:
                        score_breakdown = st.session_state.streamlit_integration.submit_feedback_with_display(
                            feedback_content, evaluator
                        )
                    
                    st.success("✅ Feedback generated successfully!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error generating feedback: {e}")

# ============================================================================
# Enhanced Feedback Display and PDF Generation
# ============================================================================

if st.session_state.feedback is not None:
    st.markdown("---")
    
    # Display feedback with enhanced formatting
    feedback_data = st.session_state.feedback
    display_format = FeedbackFormatter.format_feedback_for_display(
        feedback_data['content'], 
        feedback_data['timestamp'], 
        feedback_data['evaluator']
    )
    
    st.markdown(display_format['header'])
    st.markdown(display_format['timestamp'])
    st.markdown(display_format['evaluator'])
    st.markdown(display_format['separator'])
    st.markdown(display_format['content'])
    
    # Enhanced PDF Generation Section
    st.markdown("### 📄 Download Enhanced PDF Report")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("Generate a comprehensive MI performance report with:")
        st.markdown("- 📊 Detailed component scoring and breakdown")
        st.markdown("- 💬 Complete conversation transcript")
        st.markdown("- 💡 Personalized improvement suggestions")
        st.markdown("- 📈 Performance metrics and trends")
        if PHP_INTEGRATION_AVAILABLE:
            st.markdown("- 🔗 Database integration for tracking progress")
    
    with col2:
        # PHP-integrated PDF generation
        if PHP_INTEGRATION_AVAILABLE and st.button("📥 Generate Enhanced PDF", type="primary"):
            if not student_name:
                st.error("Please enter your name in the sidebar")
            else:
                success = st.session_state.streamlit_integration.generate_pdf_download(
                    f"HPV_MI_Report_{student_name.replace(' ', '_')}_{int(time.time())}.pdf"
                )
                if success:
                    st.success("✅ Enhanced PDF generated with database integration!")
        
        # Fallback to legacy PDF generation
        if st.button("📄 Generate Legacy PDF"):
            if not student_name:
                st.error("Please enter your name in the sidebar")
            else:
                try:
                    validated_name = validate_student_name(student_name)
                    
                    # Format feedback for PDF
                    formatted_feedback = FeedbackFormatter.format_feedback_for_pdf(
                        feedback_data['content'], 
                        feedback_data['timestamp'], 
                        feedback_data['evaluator']
                    )
                    
                    # Generate PDF
                    pdf_buffer = generate_pdf_report(
                        student_name=validated_name,
                        raw_feedback=formatted_feedback,
                        chat_history=st.session_state.chat_history,
                        session_type="HPV Vaccine"
                    )
                    
                    # Create download filename
                    download_filename = FeedbackFormatter.create_download_filename(
                        student_name, "HPV", st.session_state.selected_persona
                    )
                    
                    # Provide download button
                    st.download_button(
                        label="📥 Download HPV MI Performance Report (PDF)",
                        data=pdf_buffer.getvalue(),
                        file_name=download_filename,
                        mime="application/pdf",
                        help="Download comprehensive PDF report with scores, feedback, and conversation transcript"
                    )
                    
                    # Display score summary
                    try:
                        score_breakdown = MIScorer.get_score_breakdown(formatted_feedback)
                        st.success(f"**Total Score: {score_breakdown['total_score']:.1f} / {score_breakdown['total_possible']:.1f} ({score_breakdown['percentage']:.1f}%)**")
                    except Exception:
                        pass
                        
                except ValueError as e:
                    st.error(f"Error generating PDF: {e}")
                except Exception as e:
                    st.error(f"Unexpected error: {e}")

# ============================================================================
# Enhanced Session History and Analytics
# ============================================================================

if PHP_INTEGRATION_AVAILABLE and student_name:
    st.markdown("---")
    st.markdown("### 📊 Your MI Practice History")
    
    with st.expander("View Previous Sessions"):
        try:
            validated_name = validate_student_name(student_name)
            st.session_state.streamlit_integration.display_session_history(validated_name)
        except Exception as e:
            st.error(f"Could not load session history: {e}")

# ============================================================================
# System Information and Help
# ============================================================================

with st.expander("ℹ️ System Information & Help"):
    st.markdown("### LAMP-Integrated HPV MI Practice App")
    st.markdown("**Version:** 1.0.0 (LAMP-integrated)")
    st.markdown("**Backend Integration:** " + ("✅ Active" if PHP_INTEGRATION_AVAILABLE else "❌ Legacy Mode"))
    
    if PHP_INTEGRATION_AVAILABLE:
        st.markdown("### Enhanced Features Available:")
        st.markdown("- 🗄️ **Database Storage**: All sessions stored for progress tracking")
        st.markdown("- 📊 **Analytics**: Performance metrics and improvement trends")
        st.markdown("- 🔗 **Traceability**: Complete audit trail of all interactions")
        st.markdown("- 📄 **Enhanced PDFs**: Professional reports with database integration")
        st.markdown("- 🔍 **Session History**: View and compare previous practice sessions")
    
    st.markdown("### How to Use:")
    st.markdown("1. Enter your name in the sidebar")
    st.markdown("2. Choose a patient persona to practice with")
    st.markdown("3. Start a conversation using motivational interviewing techniques")
    st.markdown("4. Generate feedback to assess your MI skills")
    st.markdown("5. Download a comprehensive PDF report")
    
    st.markdown("### MI Techniques to Practice:")
    st.markdown("- **Open-ended questions**: 'What concerns do you have about the vaccine?'")
    st.markdown("- **Reflective listening**: 'It sounds like you're worried about...'")
    st.markdown("- **Summarizing**: 'Let me make sure I understand...'")
    st.markdown("- **Supporting autonomy**: 'The decision is ultimately yours'")

# ============================================================================
# Footer with Enhanced Information
# ============================================================================

st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**🧬 HPV MI Practice**")
    st.markdown("Enhanced with LAMP-stack integration")

with col2:
    st.markdown("**📚 Resources**")
    if st.button("View MI Guidelines"):
        st.info("Motivational Interviewing focuses on collaboration, evocation, acceptance, and compassion.")

with col3:
    st.markdown("**🔧 Technical Info**")
    st.markdown(f"Session State: {'Active' if st.session_state.selected_persona else 'None'}")
    if PHP_INTEGRATION_AVAILABLE:
        st.markdown(f"PHP Session: {'Connected' if st.session_state.get('php_session_id') else 'Legacy'}")