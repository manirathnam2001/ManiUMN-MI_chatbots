"""
Shared utilities for chat handling across MI assessment applications.
Provides common functions to reduce code redundancy between HPV.py and OHI.py.
"""

import streamlit as st
from groq import Groq
from time_utils import get_formatted_utc_time
from feedback_template import FeedbackFormatter
from scoring_utils import validate_student_name, MIScorer
from pdf_utils import generate_pdf_report
from logging_utils import get_logger
from conversation_utils import ConversationEndDetector, format_closing_response


def initialize_session_state():
    """Initialize common session state variables."""
    if "selected_persona" not in st.session_state:
        st.session_state.selected_persona = None
    if "feedback" not in st.session_state:
        st.session_state.feedback = None
    if "conversation_ended" not in st.session_state:
        st.session_state.conversation_ended = False
    if "session_logged" not in st.session_state:
        st.session_state.session_logged = False


def display_persona_selection(personas_dict, app_title):
    """Display persona selection UI."""
    if st.session_state.selected_persona is None:
        st.markdown("### Choose a Patient Persona")
        
        # Create persona descriptions based on personas_dict
        persona_descriptions = []
        for name, description in personas_dict.items():
            # Extract background info from persona description
            lines = description.split('\n')
            background_line = next((line for line in lines if line.startswith('Background:')), '')
            if background_line:
                # Clean up the background description
                background = background_line.replace('Background: You are a ', '').strip()
                persona_descriptions.append(f"- **{name}**: {background}")
        
        st.markdown("Select a patient persona to practice with:\n\n" + '\n'.join(persona_descriptions))
        
        selected = st.selectbox(
            "Select a persona:",
            list(personas_dict.keys()),
            key="persona_selector"
        )
        
        if st.button("Start Conversation"):
            st.session_state.selected_persona = selected
            st.session_state.chat_history = []
            st.session_state.conversation_ended = False
            st.session_state.session_logged = False
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": f"Hello! I'm {selected}, nice to meet you today."
            })
            st.rerun()


def log_session_start_if_needed(student_name: str, session_type: str):
    """Log session start once per session."""
    if not st.session_state.get('session_logged', False):
        logger = get_logger()
        logger.log_session_start(
            student_name, 
            session_type,
            st.session_state.get('selected_persona')
        )
        st.session_state.session_logged = True


def display_chat_history():
    """Display the chat history."""
    if st.session_state.selected_persona is not None:
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])


def generate_and_display_feedback(personas_dict, session_type, student_name, retrieve_knowledge_func, client):
    """Generate and display feedback with PDF download capability."""
    logger = get_logger()
    
    # Get current UTC timestamp and user login
    current_timestamp = get_formatted_utc_time()
    user_login = "manirathnam2001"
    
    transcript = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in st.session_state.chat_history])

    # Retrieve relevant rubric content
    retrieved_info = retrieve_knowledge_func("motivational interviewing feedback rubric")
    rag_context = "\n".join(retrieved_info)

    # Use standardized evaluation prompt
    review_prompt = FeedbackFormatter.format_evaluation_prompt(
        session_type.lower(), transcript, rag_context
    )

    feedback_response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": personas_dict[st.session_state.selected_persona]},
            {"role": "user", "content": review_prompt}
        ]
    )
    feedback = feedback_response.choices[0].message.content
    
    # Calculate score for logging
    try:
        score_breakdown = MIScorer.get_score_breakdown(feedback)
        total_score = score_breakdown['total_score']
        percentage = score_breakdown['percentage']
    except Exception:
        total_score = 0.0
        percentage = 0.0
    
    # Log feedback generation
    logger.log_feedback_generated(
        student_name, session_type, total_score, percentage,
        st.session_state.selected_persona
    )
    
    # Store feedback in session state to prevent disappearing
    st.session_state.feedback = {
        'content': feedback,
        'timestamp': current_timestamp,
        'evaluator': user_login
    }
    
    # Display feedback using standardized formatting
    display_format = FeedbackFormatter.format_feedback_for_display(
        feedback, current_timestamp, user_login
    )
    
    st.markdown(display_format['header'])
    st.markdown(display_format['timestamp'])
    st.markdown(display_format['evaluator'])
    st.markdown(display_format['separator'])
    st.markdown(display_format['content'])


def display_existing_feedback():
    """Display existing feedback if it exists (prevents disappearing after PDF download)."""
    if st.session_state.feedback is not None:
        feedback_data = st.session_state.feedback
        display_format = FeedbackFormatter.format_feedback_for_display(
            feedback_data['content'], feedback_data['timestamp'], feedback_data['evaluator']
        )
        
        st.markdown(display_format['header'])
        st.markdown(display_format['timestamp'])
        st.markdown(display_format['evaluator'])
        st.markdown(display_format['separator'])
        st.markdown(display_format['content'])
        
        # Show PDF download section for existing feedback
        st.markdown("### 📄 Download PDF Report")


def handle_pdf_generation(student_name, session_type, app_name):
    """Handle PDF generation and download."""
    if st.session_state.feedback is not None:
        feedback_data = st.session_state.feedback
        
        # Format feedback for PDF using standardized template
        formatted_feedback = FeedbackFormatter.format_feedback_for_pdf(
            feedback_data['content'], feedback_data['timestamp'], feedback_data['evaluator']
        )
        
        # Validate student name and generate PDF
        try:
            validated_name = validate_student_name(student_name)
            
            pdf_buffer = generate_pdf_report(
                student_name=validated_name,
                raw_feedback=formatted_feedback,
                chat_history=st.session_state.chat_history,
                session_type=session_type,
                persona=st.session_state.selected_persona
            )
            
            # Generate standardized filename
            download_filename = FeedbackFormatter.create_download_filename(
                student_name, session_type, st.session_state.selected_persona
            )
            
            # Add download button with enhanced label
            st.download_button(
                label=f"📥 Download {app_name} MI Performance Report (PDF)",
                data=pdf_buffer.getvalue(),
                file_name=download_filename,
                mime="application/pdf",
                help="Download a comprehensive PDF report with scores, feedback, and conversation transcript"
            )
            
            # Display score summary if parsing is successful
            try:
                score_breakdown = MIScorer.get_score_breakdown(formatted_feedback)
                st.success(f"**Total Score: {score_breakdown['total_score']:.1f} / {score_breakdown['total_possible']:.1f} ({score_breakdown['percentage']:.1f}%)**")
            except Exception:
                pass  # Skip score display if parsing fails
                
        except ValueError as e:
            logger = get_logger()
            logger.log_pdf_generation_error(student_name, session_type, str(e), 'validation_error')
            st.error(f"Error generating PDF: {e}")
            st.info("Please check your student name and try again.")
        except Exception as e:
            logger = get_logger()
            logger.log_pdf_generation_error(student_name, session_type, str(e), 'unexpected_error')
            st.error(f"Unexpected error: {e}")
            st.info("There was an issue generating the PDF. Please try again.")


def handle_chat_input(personas_dict, client):
    """Handle user chat input and AI response."""
    if st.session_state.selected_persona is not None:
        # Disable input if conversation ended
        if st.session_state.get('conversation_ended', False):
            st.info("This conversation has ended. Please click 'Finish Session & Get Feedback' to get your evaluation, or start a new conversation.")
            return
        
        user_prompt = st.chat_input("Your response...")

        if user_prompt:
            # Check for end-of-conversation phrases
            is_end_phrase, detected_phrase = ConversationEndDetector.detect_end_phrase(user_prompt)
            
            st.session_state.chat_history.append({"role": "user", "content": user_prompt})
            st.chat_message("user").markdown(user_prompt)
            
            # If end phrase detected, provide closing message
            if is_end_phrase:
                logger = get_logger()
                logger.log_end_phrase_detected(
                    "Current User",  # Will be replaced with actual student name when available
                    "Current Session",  # Will be replaced with actual session type when available
                    detected_phrase,
                    len(st.session_state.chat_history)
                )
                
                # Generate closing response
                closing_message = ConversationEndDetector.get_closing_message(
                    len(st.session_state.chat_history)
                )
                assistant_response = format_closing_response(detected_phrase, closing_message)
                
                # Mark conversation as ended
                st.session_state.conversation_ended = True
                
            else:
                # Normal conversation flow
                turn_instruction = {
                    "role": "system",
                    "content": "Follow the MI chain-of-thought steps: identify routine, ask open question, reflect, elicit change talk, summarize & plan."
                }
                messages = [
                    {"role": "system", "content": personas_dict[st.session_state.selected_persona]},
                    turn_instruction,
                    *st.session_state.chat_history
                ]
                
                response = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=messages
                )
                assistant_response = response.choices[0].message.content
            
            st.session_state.chat_history.append({"role": "assistant", "content": assistant_response})
            with st.chat_message("assistant"):
                st.markdown(assistant_response)
                
            # Show feedback prompt if conversation naturally ended
            if is_end_phrase or ConversationEndDetector.should_show_feedback_prompt(
                user_prompt, len(st.session_state.chat_history)
            ):
                st.info("💡 Ready for feedback? Click 'Finish Session & Get Feedback' to receive your detailed MI assessment.")


def handle_new_conversation_button():
    """Handle the start new conversation button."""
    if st.button("Start New Conversation"):
        # Log session end if there was an active session
        if st.session_state.chat_history:
            logger = get_logger()
            logger.log_session_end(
                "Current User",  # Will be replaced with actual student name
                "Current Session",  # Will be replaced with actual session type
                len(st.session_state.chat_history),
                'new_conversation_started'
            )
        
        st.session_state.selected_persona = None
        st.session_state.chat_history = []
        st.session_state.feedback = None  # Clear feedback when starting new conversation
        st.session_state.conversation_ended = False
        st.session_state.session_logged = False
        st.rerun()