"""
Shared utilities for chat handling across MI assessment applications.
Provides common functions to reduce code redundancy between HPV.py and OHI.py.
"""

import streamlit as st
from groq import Groq
from time_utils import get_formatted_utc_time
from feedback_template import FeedbackFormatter
from scoring_utils import validate_student_name
from pdf_utils import generate_pdf_report


def initialize_session_state():
    """Initialize common session state variables."""
    if "selected_persona" not in st.session_state:
        st.session_state.selected_persona = None
    if "feedback" not in st.session_state:
        st.session_state.feedback = None


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
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": f"Hello! I'm {selected}, nice to meet you today."
            })
            st.rerun()


def display_chat_history():
    """Display the chat history."""
    if st.session_state.selected_persona is not None:
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])


def generate_and_display_feedback(personas_dict, session_type, student_name, retrieve_knowledge_func, client):
    """Generate and display feedback with PDF download capability."""
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
                session_type=session_type
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
                from scoring_utils import MIScorer
                score_breakdown = MIScorer.get_score_breakdown(formatted_feedback)
                st.success(f"**Total Score: {score_breakdown['total_score']:.1f} / {score_breakdown['total_possible']:.1f} ({score_breakdown['percentage']:.1f}%)**")
            except Exception:
                pass  # Skip score display if parsing fails
                
        except ValueError as e:
            st.error(f"Error generating PDF: {e}")
            st.info("Please check your student name and try again.")
        except Exception as e:
            st.error(f"Unexpected error: {e}")
            st.info("There was an issue generating the PDF. Please try again.")


def handle_chat_input(personas_dict, client):
    """Handle user chat input and AI response."""
    if st.session_state.selected_persona is not None:
        user_prompt = st.chat_input("Your response...")

        if user_prompt:
            st.session_state.chat_history.append({"role": "user", "content": user_prompt})
            st.chat_message("user").markdown(user_prompt)

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


def handle_new_conversation_button():
    """Handle the start new conversation button."""
    if st.button("Start New Conversation"):
        st.session_state.selected_persona = None
        st.session_state.chat_history = []
        st.session_state.feedback = None  # Clear feedback when starting new conversation
        st.rerun()