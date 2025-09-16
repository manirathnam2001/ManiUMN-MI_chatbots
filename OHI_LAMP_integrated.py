"""
OHI_LAMP_integrated.py

Modified version of OHI.py showing integration with LAMP-stack PHP utilities.
This demonstrates how existing Streamlit MI chatbots can use the new PHP backend
for database storage, logging, and PDF generation.

Key changes from original OHI.py:
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
    page_title="OHI MI Practice App (LAMP-Integrated)",
    page_icon="🦷",
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

# OHI Personas with enhanced metadata for database storage
ohi_personas = {
    "Jasmine - College Student": {
        "description": "A busy college student who struggles with consistent oral hygiene habits",
        "initial_message": "Hi there! I've been having some issues with my teeth lately. I've noticed some yellow spots and my gums bleed sometimes when I brush. I know I should probably take better care of my teeth, but college is just so busy, you know?",
        "personality_traits": ["busy", "stressed", "aware_of_issues", "seeking_help"],
        "key_concerns": ["time_management", "pain", "cost", "habits"],
        "background": "21-year-old college student, irregular brushing, drinks coffee frequently"
    },
    "Sydney - Working Professional": {
        "description": "A working professional concerned about appearance and long-term oral health",
        "initial_message": "Hello! I'm here because I've been noticing some changes in my mouth health. My gums seem more sensitive lately, and I'm worried about how this might affect my professional appearance. I have client meetings regularly and want to make sure my smile looks good.",
        "personality_traits": ["professional", "appearance_conscious", "motivated", "detail_oriented"],
        "key_concerns": ["appearance", "professional_image", "long_term_health", "effectiveness"],
        "background": "32-year-old professional, concerned about aesthetics and career impact"
    },
    "Morgan - Skeptical Patient": {
        "description": "A patient who is skeptical about dental advice and prefers natural approaches",
        "initial_message": "Well, I'm here because my family keeps telling me I need to see someone about my oral health. Honestly, I'm not sure I buy into all these dental recommendations. I've been using natural methods like oil pulling and herbal rinses. Why do I need all these complicated routines?",
        "personality_traits": ["skeptical", "independent", "natural_preference", "questioning"],
        "key_concerns": ["natural_alternatives", "necessity", "commercial_interests", "side_effects"],
        "background": "45-year-old who prefers natural health approaches, resistant to conventional advice"
    }
}

# ============================================================================
# Main Application Interface
# ============================================================================

st.title("🦷 OHI MI Practice App (LAMP-Integrated)")
st.markdown("### Practice Motivational Interviewing Skills for Oral Hygiene Discussions")

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
    selected_persona_name = st.selectbox("Select a patient persona:", list(ohi_personas.keys()))
    
    if selected_persona_name:
        persona_info = ohi_personas[selected_persona_name]
        st.markdown(f"**{selected_persona_name}**")
        st.write(persona_info["description"])
        
        with st.expander("Persona Details"):
            st.write("**Personality Traits:**", ", ".join(persona_info["personality_traits"]))
            st.write("**Key Concerns:**", ", ".join(persona_info["key_concerns"]))
            st.write("**Background:**", persona_info["background"])
    
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
                        validated_name, "OHI", selected_persona_name
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
    persona = ohi_personas[st.session_state.selected_persona]
    
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
- Background: {persona['background']}

Stay in character and respond naturally to the healthcare provider's motivational interviewing techniques. 
Be realistic about your oral health concerns and reactions. Allow yourself to be gradually influenced by good MI techniques, 
but maintain your character's personality and specific concerns throughout the conversation.

Current conversation context: This is an oral health discussion where you're talking with a dental healthcare provider 
who is practicing motivational interviewing skills to help you improve your oral hygiene habits."""
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
                    "persona": st.session_state.selected_persona,
                    "session_type": "OHI"
                }
                enhanced_assistant_message = {
                    **assistant_message,
                    "timestamp": datetime.utcnow().isoformat(),
                    "model": "llama3-8b-8192",
                    "persona": st.session_state.selected_persona,
                    "session_type": "OHI"
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
    
    # Display MI techniques tips for OHI
    with st.expander("💡 OHI-Specific MI Techniques"):
        st.markdown("**Effective techniques for oral health discussions:**")
        st.markdown("- Explore patient's understanding of oral health risks")
        st.markdown("- Ask about current oral hygiene routines and barriers") 
        st.markdown("- Reflect on patient's concerns about pain, time, or cost")
        st.markdown("- Support patient autonomy in choosing improvement strategies")
        st.markdown("- Collaborate on realistic, achievable oral health goals")
    
    if st.button("Generate Feedback"):
        if not student_name:
            st.error("Please enter your name in the sidebar to generate feedback")
        else:
            with st.spinner("Analyzing your MI skills for oral health counseling..."):
                try:
                    # Prepare conversation transcript
                    transcript = "\n\n".join([
                        f"{'STUDENT' if msg['role'] == 'user' else 'PATIENT'}: {msg['content']}"
                        for msg in st.session_state.chat_history
                    ])
                    
                    # Load RAG context for OHI
                    try:
                        with open("ohi_rubrics/ohi_jasmine.txt", "r") as f:
                            rag_context = f.read()
                    except FileNotFoundError:
                        try:
                            with open("ohi_rubrics/ohi_sydney.txt", "r") as f:
                                rag_context = f.read()
                        except FileNotFoundError:
                            rag_context = "Standard MI evaluation criteria for oral health counseling"
                    
                    # Generate evaluation prompt
                    evaluation_prompt = FeedbackFormatter.format_evaluation_prompt(
                        "Oral Health Interview", transcript, rag_context
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
                    evaluator = "AI Assistant (OHI-Enhanced)"
                    
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
                    
                    st.success("✅ OHI MI feedback generated successfully!")
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
    st.markdown("### 📄 Download Enhanced OHI Report")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("Generate a comprehensive OHI MI performance report with:")
        st.markdown("- 🦷 Oral health-specific MI assessment")
        st.markdown("- 📊 Detailed component scoring and breakdown")
        st.markdown("- 💬 Complete conversation transcript")
        st.markdown("- 💡 OHI-specific improvement suggestions")
        st.markdown("- 📈 Performance metrics and progress tracking")
        if PHP_INTEGRATION_AVAILABLE:
            st.markdown("- 🔗 Database integration for longitudinal tracking")
    
    with col2:
        # PHP-integrated PDF generation
        if PHP_INTEGRATION_AVAILABLE and st.button("📥 Generate Enhanced PDF", type="primary"):
            if not student_name:
                st.error("Please enter your name in the sidebar")
            else:
                success = st.session_state.streamlit_integration.generate_pdf_download(
                    f"OHI_MI_Report_{student_name.replace(' ', '_')}_{int(time.time())}.pdf"
                )
                if success:
                    st.success("✅ Enhanced OHI PDF generated with database integration!")
        
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
                        session_type="OHI"
                    )
                    
                    # Create download filename
                    download_filename = FeedbackFormatter.create_download_filename(
                        student_name, "OHI", st.session_state.selected_persona
                    )
                    
                    # Provide download button
                    st.download_button(
                        label="📥 Download OHI MI Performance Report (PDF)",
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
    st.markdown("### 📊 Your OHI Practice History")
    
    with st.expander("View Previous OHI Sessions"):
        try:
            validated_name = validate_student_name(student_name)
            st.session_state.streamlit_integration.display_session_history(validated_name)
        except Exception as e:
            st.error(f"Could not load session history: {e}")

# ============================================================================
# OHI-Specific Resources and Tips
# ============================================================================

with st.expander("🦷 OHI-Specific MI Resources"):
    st.markdown("### Oral Health Interview Focus Areas")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Common Patient Barriers:**")
        st.markdown("- Time constraints and busy schedules")
        st.markdown("- Pain or sensitivity during brushing")
        st.markdown("- Cost of dental products or treatments")
        st.markdown("- Lack of knowledge about proper techniques")
        st.markdown("- Embarrassment about current oral health")
        
        st.markdown("**Effective MI Responses:**")
        st.markdown("- 'What has worked for you in the past?'")
        st.markdown("- 'Help me understand your daily routine'")
        st.markdown("- 'What concerns you most about oral health?'")
    
    with col2:
        st.markdown("**Change Talk Opportunities:**")
        st.markdown("- Desire: 'I want to have healthier gums'")
        st.markdown("- Ability: 'I could brush twice a day'")
        st.markdown("- Reasons: 'To avoid painful dental procedures'")
        st.markdown("- Need: 'I need to take better care of my teeth'")
        
        st.markdown("**Goal Setting Examples:**")
        st.markdown("- Start with one small change (e.g., flossing 3x/week)")
        st.markdown("- Focus on specific times (e.g., before bed)")
        st.markdown("- Address immediate concerns first")

# ============================================================================
# System Information and Health-Specific Help
# ============================================================================

with st.expander("ℹ️ System Information & OHI-Specific Help"):
    st.markdown("### LAMP-Integrated OHI MI Practice App")
    st.markdown("**Version:** 1.0.0 (LAMP-integrated)")
    st.markdown("**Backend Integration:** " + ("✅ Active" if PHP_INTEGRATION_AVAILABLE else "❌ Legacy Mode"))
    st.markdown("**Specialization:** Oral Health Interview (OHI)")
    
    if PHP_INTEGRATION_AVAILABLE:
        st.markdown("### Enhanced Features Available:")
        st.markdown("- 🗄️ **Database Storage**: All OHI sessions stored for progress tracking")
        st.markdown("- 📊 **OHI Analytics**: Oral health-specific performance metrics")
        st.markdown("- 🔗 **Longitudinal Tracking**: Compare oral health counseling improvements")
        st.markdown("- 📄 **Specialized PDFs**: OHI-focused reports with clinical relevance")
        st.markdown("- 🦷 **Clinical Context**: Dental health-specific MI assessment")
    
    st.markdown("### OHI-Specific Usage Guide:")
    st.markdown("1. **Pre-Session**: Review patient persona's oral health background")
    st.markdown("2. **Assessment**: Ask about current oral hygiene habits and barriers")
    st.markdown("3. **Exploration**: Use MI techniques to understand patient's perspective")
    st.markdown("4. **Collaboration**: Work together on realistic oral health goals")
    st.markdown("5. **Follow-up**: Generate feedback focused on oral health counseling skills")
    
    st.markdown("### OHI MI Competencies Assessed:")
    st.markdown("- **Collaboration**: Building partnership in oral health decisions")
    st.markdown("- **Evocation**: Drawing out patient's oral health motivations")
    st.markdown("- **Acceptance**: Respecting patient's autonomy in oral care choices")
    st.markdown("- **Compassion**: Showing empathy for oral health concerns and barriers")

# ============================================================================
# Footer with Enhanced OHI Information
# ============================================================================

st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**🦷 OHI MI Practice**")
    st.markdown("Enhanced with LAMP-stack integration")
    st.markdown("Specialized for oral health counseling")

with col2:
    st.markdown("**📚 OHI Resources**")
    if st.button("View OHI Guidelines"):
        st.info("Oral Health Interviews should focus on understanding patient barriers, exploring motivations for oral health behavior change, and collaboratively setting realistic goals.")

with col3:
    st.markdown("**🔧 Technical Info**")
    st.markdown(f"Session State: {'Active' if st.session_state.selected_persona else 'None'}")
    if PHP_INTEGRATION_AVAILABLE:
        st.markdown(f"PHP Session: {'Connected' if st.session_state.get('php_session_id') else 'Legacy'}")
    st.markdown("OHI Mode: Enabled")