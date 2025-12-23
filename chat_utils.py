"""
Shared utilities for chat handling across MI assessment applications.

This module provides common functions to reduce code redundancy between HPV.py and OHI.py,
including:
- Session state initialization and management
- Chat history display and interaction handling
- Conversation ending detection and role validation
- Feedback generation and PDF creation
- Persona selection UI components

All functions maintain consistent behavior across both OHI and HPV assessment bots.
"""

import streamlit as st
import logging
from groq import Groq
from time_utils import get_formatted_utc_time
from feedback_template import FeedbackFormatter
from scoring_utils import validate_student_name
from pdf_utils import generate_pdf_report
from end_control_middleware import (
    should_continue_v4,  # Use v4 with semantic-based ending
    prevent_ambiguous_ending,
    log_conversation_trace,
    MIN_TURN_THRESHOLD,
)

# Configure logging for chat utilities
logger = logging.getLogger(__name__)


def detect_conversation_ending(chat_history, turn_count):
    """
    Detect if the conversation should naturally end.
    
    Args:
        chat_history: List of chat messages
        turn_count: Current number of turns
        
    Returns:
        bool: True if conversation should end, False otherwise
    """
    # Check if we've reached reasonable conversation length (8-12 turns)
    if turn_count >= 12:
        return True
    
    # Check last assistant message for natural ending phrases
    if len(chat_history) > 0:
        last_message = chat_history[-1].get('content', '').lower()
        
        # Natural ending phrases that indicate conversation closure
        ending_phrases = [
            'thank you for',
            'best of luck',
            'take care',
            'good luck',
            'feel free to reach out',
            'i appreciate your time',
            'have a good day',
            'talk to you later',
            'see you',
            'goodbye',
            'bye',
        ]
        
        if any(phrase in last_message for phrase in ending_phrases):
            return True
    
    return False


def validate_response_role(response_content):
    """
    Validate that the response maintains patient role and doesn't switch to evaluator.
    
    Args:
        response_content: The assistant's response text
        
    Returns:
        tuple: (is_valid, cleaned_response) - is_valid is True if role is maintained
    """
    # Check for evaluator/feedback mode indicators
    evaluator_indicators = [
        'feedback report',
        'evaluation:',
        'score:',
        'rubric category',
        'criteria met',
        'partially met',
        'not met',
        'performance evaluation',
        'strengths:',
        'areas for improvement',
        'suggestions for improvement',
    ]
    
    response_lower = response_content.lower()
    
    # If response contains evaluator indicators, it's breaking role
    if any(indicator in response_lower for indicator in evaluator_indicators):
        return False, response_content
    
    return True, response_content


def initialize_session_state():
    """Initialize common session state variables."""
    if "selected_persona" not in st.session_state:
        st.session_state.selected_persona = None
    if "feedback" not in st.session_state:
        st.session_state.feedback = None
    if "conversation_state" not in st.session_state:
        st.session_state.conversation_state = "active"  # active or ended
    if "turn_count" not in st.session_state:
        st.session_state.turn_count = 0
    # New state variables for confirmation flow
    if "end_control_state" not in st.session_state:
        st.session_state.end_control_state = "ACTIVE"
    if "confirmation_flag" not in st.session_state:
        st.session_state.confirmation_flag = False
    if "termination_trigger" not in st.session_state:
        st.session_state.termination_trigger = "unknown"


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
            st.session_state.conversation_state = "active"
            st.session_state.turn_count = 0
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


def generate_and_display_feedback(personas_dict, session_type, student_name, retrieve_knowledge_func, client, bot_name="MI Assessment System"):
    """Generate and display feedback with PDF download capability.
    
    Args:
        personas_dict: Dictionary of persona definitions
        session_type: Type of session (e.g., "dental hygiene", "hpv")
        student_name: Name of the student
        retrieve_knowledge_func: Function to retrieve knowledge from RAG
        client: Groq client for LLM calls
        bot_name: Name of the bot/system for the evaluator field (default: "MI Assessment System")
    """
    # Get current UTC timestamp and use bot name as evaluator
    current_timestamp = get_formatted_utc_time()
    evaluator = bot_name
    
    transcript = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in st.session_state.chat_history])

    # Retrieve relevant rubric content
    retrieved_info = retrieve_knowledge_func("motivational interviewing feedback rubric")
    rag_context = "\n".join(retrieved_info)

    # Use standardized evaluation prompt
    review_prompt = FeedbackFormatter.format_evaluation_prompt(
        session_type.lower(), transcript, rag_context
    )

    try:
        feedback_response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": personas_dict[st.session_state.selected_persona]},
                {"role": "user", "content": review_prompt}
            ]
        )
        feedback = feedback_response.choices[0].message.content
    except Exception as e:
        # Handle authentication errors gracefully
        error_msg = str(e).lower()
        if "401" in error_msg or "invalid api key" in error_msg or "authentication" in error_msg:
            st.error("❌ Invalid API Key detected. Please check your Groq API key and try again.")
            st.info("💡 To fix this: Enter a valid Groq API key in the field at the top of the page and reload the page.")
            return
        else:
            # Re-raise other unexpected errors
            raise
    
    # Store feedback in session state to prevent disappearing
    st.session_state.feedback = {
        'content': feedback,
        'timestamp': current_timestamp,
        'evaluator': evaluator
    }
    
    # Display feedback using standardized formatting
    display_format = FeedbackFormatter.format_feedback_for_display(
        feedback, current_timestamp, evaluator
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


def handle_chat_input(personas_dict, client, domain_name=None, domain_keywords=None):
    """Handle user chat input and AI response with persona guard integration.
    
    Args:
        personas_dict: Dictionary of persona definitions
        client: Groq API client
        domain_name: Name of the domain (e.g., "HPV vaccination", "oral hygiene")
        domain_keywords: List of domain-relevant keywords for off-topic detection
    """
    if st.session_state.selected_persona is not None:
        # Check conversation state
        if st.session_state.conversation_state == "ended":
            st.info("💬 This conversation has ended. Please click 'Finish Session & Get Feedback' to receive your evaluation, or start a new conversation.")
            return
            
        user_prompt = st.chat_input("Your response...")

        if user_prompt:
            # Block feedback requests during conversation
            feedback_request_phrases = [
                'feedback',
                'evaluate',
                'how did i do',
                'rate my performance',
                'score',
                'assessment',
            ]
            
            if any(phrase in user_prompt.lower() for phrase in feedback_request_phrases):
                st.warning("⏸️ Feedback will be provided after the conversation ends. Please continue the conversation naturally.")
                return
            
            # Apply persona guardrails if domain metadata is provided
            guard_message = None
            if domain_name and domain_keywords:
                from persona_guard import apply_guardrails
                needs_intervention, guard_message = apply_guardrails(
                    user_prompt, domain_name, domain_keywords
                )
                
                if needs_intervention:
                    logger.warning(f"Guardrail intervention triggered for user message: '{user_prompt[:50]}'")
            
            # Prevent premature ending from ambiguous phrases
            if prevent_ambiguous_ending(user_prompt):
                logger.info(f"Ambiguous phrase detected from user: '{user_prompt}' - continuing conversation")
            
            st.session_state.chat_history.append({"role": "user", "content": user_prompt})
            st.chat_message("user").markdown(user_prompt)
            
            # Increment turn count
            st.session_state.turn_count += 1

            # Enhanced turn instruction with conciseness, role consistency, and end token
            turn_instruction = {
                "role": "system",
                "content": f"""Follow the MI chain-of-thought steps: identify routine, ask open question, reflect, elicit change talk, summarize & plan.

CRITICAL INSTRUCTIONS:
- Keep your responses CONCISE (2-3 sentences maximum)
- Stay in character as the PATIENT throughout the entire conversation
- DO NOT provide feedback, evaluation, or scores during the conversation
- DO NOT switch to evaluator role until explicitly asked at the end
- Respond naturally as the patient would, showing emotions and reactions
- When you are ready to naturally end the conversation after a full MI session, include the end token: {END_TOKEN}
- Only use the end token when the conversation has covered all MI components and feels complete"""
            }
            
            # Build messages array with guard message if intervention needed
            messages = [
                {"role": "system", "content": personas_dict[st.session_state.selected_persona]},
                turn_instruction,
            ]
            
            # Add guard message before chat history if intervention needed
            if guard_message:
                messages.append(guard_message)
            
            messages.extend(st.session_state.chat_history)
            
            try:
                response = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=messages,
                    max_tokens=150,  # Limit response length to enforce conciseness
                    temperature=0.7
                )
                assistant_response = response.choices[0].message.content
            except Exception as e:
                # Handle authentication errors gracefully
                error_msg = str(e).lower()
                if "401" in error_msg or "invalid api key" in error_msg or "authentication" in error_msg:
                    st.error("❌ Invalid API Key detected. Please check your Groq API key and try again.")
                    st.info("💡 To fix this: Enter a valid Groq API key in the field at the top of the page and reload the page.")
                    return
                else:
                    # Re-raise other unexpected errors
                    raise
            
            # Check response guardrails if domain metadata is provided
            if domain_name:
                from persona_guard import check_response_guardrails
                needs_correction, correction_message = check_response_guardrails(
                    assistant_response, domain_name
                )
                
                if needs_correction:
                    logger.warning(f"Response guardrail triggered, re-generating response")
                    # Re-generate response with correction message
                    correction_messages = messages + [
                        {"role": "assistant", "content": assistant_response},
                        correction_message
                    ]
                    
                    try:
                        correction_response = client.chat.completions.create(
                            model="llama-3.1-8b-instant",
                            messages=correction_messages,
                            max_tokens=150,
                            temperature=0.7
                        )
                        assistant_response = correction_response.choices[0].message.content
                        logger.info(f"Corrected response generated")
                    except Exception as e:
                        # Handle authentication errors gracefully
                        error_msg = str(e).lower()
                        if "401" in error_msg or "invalid api key" in error_msg or "authentication" in error_msg:
                            st.error("❌ Invalid API Key detected. Please check your Groq API key and try again.")
                            st.info("💡 To fix this: Enter a valid Groq API key in the field at the top of the page and reload the page.")
                            return
                        else:
                            # Re-raise other unexpected errors
                            raise
            
            # Validate role consistency (legacy check, now supplemented by persona_guard)
            is_valid_role, cleaned_response = validate_response_role(assistant_response)
            
            if not is_valid_role:
                # If bot breaks role, provide a generic patient response instead
                assistant_response = "I appreciate you taking the time to talk with me. Is there anything else you'd like to discuss?"
                logger.warning("Bot broke role - forcing generic response")
            
            st.session_state.chat_history.append({"role": "assistant", "content": assistant_response})
            with st.chat_message("assistant"):
                st.markdown(assistant_response)
            
            # Use end-control middleware v4 for semantic-based ending
            from end_control_middleware import should_continue_v4, log_termination_metrics
            from config_loader import ConfigLoader
            
            config = ConfigLoader()
            flags = config.get_feature_flags()
            
            # Build conversation context with all required fields
            conversation_context = {
                'chat_history': st.session_state.chat_history,
                'turn_count': st.session_state.turn_count,
                'end_control_state': st.session_state.get('end_control_state', 'ACTIVE'),
                'confirmation_flag': st.session_state.get('confirmation_flag', False),
                'termination_trigger': st.session_state.get('termination_trigger', 'unknown')
            }
            
            # Use v4 with semantic-based ending
            if flags.get('require_end_confirmation', True):
                decision = should_continue_v4(
                    conversation_context,
                    assistant_response,
                    user_prompt
                )
                
                # Log metrics for monitoring
                log_termination_metrics(decision.get('metrics', {}))
                
                # Update session state with new conversation state
                st.session_state.end_control_state = decision['state']
                st.session_state.confirmation_flag = conversation_context.get('confirmation_flag', False)
                
                # Handle confirmation prompt if needed
                if decision.get('requires_confirmation') and decision.get('confirmation_prompt'):
                    # Add confirmation prompt as system message (patient voice)
                    confirmation_msg = decision['confirmation_prompt']
                    st.session_state.chat_history.append({"role": "assistant", "content": confirmation_msg})
                    with st.chat_message("assistant"):
                        st.markdown(confirmation_msg)
                    logger.info(f"Showing confirmation prompt: {confirmation_msg}")
                
                # Only end if decision says so
                if not decision['continue']:
                    st.session_state.conversation_state = "ended"
                    st.info("💬 The conversation has concluded with mutual confirmation. Click 'Finish Session & Get Feedback' to receive your evaluation.")
                    logger.info(f"Conversation ended: {decision['reason']}")
                elif decision['state'] == 'PARKED':
                    st.warning("💬 Session paused. Reconnect to continue the conversation.")
                    logger.info(f"Session parked: {decision['reason']}")
            else:
                # Fallback: Use semantic-based v4 even if confirmation flag is disabled
                # This ensures consistent behavior
                decision = should_continue_v4(
                    conversation_context,
                    assistant_response,
                    user_prompt
                )
                
                # Log the decision for diagnostics
                log_conversation_trace(conversation_context, decision, {
                    'last_user_message': user_prompt,
                    'last_assistant_message': assistant_response,
                })
                
                # Update session state
                st.session_state.end_control_state = decision['state']
                st.session_state.confirmation_flag = conversation_context.get('confirmation_flag', False)
                
                # Only end if decision says not to continue
                if not decision['continue']:
                    st.session_state.conversation_state = "ended"
                    st.info("💬 The conversation has concluded. Click 'Finish Session & Get Feedback' to receive your evaluation.")
                    logger.info(f"Conversation ended: {decision['reason']}")


def handle_new_conversation_button():
    """Handle the start new conversation button."""
    if st.button("Start New Conversation"):
        st.session_state.selected_persona = None
        st.session_state.chat_history = []
        st.session_state.feedback = None  # Clear feedback when starting new conversation
        st.session_state.conversation_state = "active"
        st.session_state.turn_count = 0
        # Reset confirmation flow states
        st.session_state.end_control_state = "ACTIVE"
        st.session_state.confirmation_flag = False
        st.session_state.termination_trigger = "unknown"
        st.rerun()


def should_enable_feedback_button():
    """
    Determine if the feedback button should be enabled.
    
    Uses semantic-based mutual confirmation logic instead of hard turn limits.
    
    Returns:
        bool: True if feedback can be requested, False otherwise
    """
    from end_control_middleware import MIN_TURN_THRESHOLD
    
    # Only enable feedback if:
    # 1. A persona is selected
    # 2. There's a conversation history with at least a few exchanges
    # 3. The conversation has ended via mutual confirmation
    if st.session_state.selected_persona is None:
        return False
    
    if len(st.session_state.chat_history) < 4:  # At least 2 exchanges
        return False
    
    # Primary condition: conversation ended via semantic mutual confirmation
    if st.session_state.conversation_state == "ended":
        return True
    
    # Fallback: Allow if minimum turns met (for manual ending if needed)
    # But this should rarely be used with semantic ending
    if st.session_state.turn_count >= MIN_TURN_THRESHOLD:
        return True
    
    return False