"""
Periodontitis MI Practice Application - Motivational Interviewing Chatbot

This Streamlit application provides an interactive environment for dental professionals
to practice Motivational Interviewing (MI) skills in periodontitis counseling.

Features:
- Multiple patient personas based on "Ava Johnson" case study showing disease progression
- Real-time conversation with AI-powered patient simulators
- RAG-based feedback using MI rubrics from perio_rubrics/ directory
- Automated scoring on 40-point MI rubric
- Professional PDF reports with detailed feedback and conversation transcripts

The application uses:
- Groq LLM API for natural conversation
- FAISS for vector similarity search in rubric retrieval
- Sentence Transformers for embedding generation
- Streamlit for the user interface

Usage:
    This page is part of a multipage app. Access via the portal at secret_code_portal.py

Requirements:
    - Authentication via secret code portal
    - Groq API key and student name from session state
    - Internet connection for LLM API calls
"""

import os
import logging
import streamlit as st
from pathlib import Path
from groq import Groq
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from time_utils import get_formatted_utc_time
from pdf_utils import generate_pdf_report
from feedback_template import FeedbackFormatter, FeedbackValidator
from scoring_utils import validate_student_name
from persona_texts import (
    PERIO_PERSONAS,
    get_perio_persona,
    PERIO_DOMAIN_NAME,
    PERIO_DOMAIN_KEYWORDS
)

# Configure logging
logger = logging.getLogger(__name__)

# Convert structured personas to simple dict for backward compatibility
PERSONAS = {name: persona['system_prompt'] for name, persona in PERIO_PERSONAS.items()}

# --- Streamlit page configuration ---
st.set_page_config(
    page_title="Periodontitis MI Practice",
    page_icon="🦷",
    layout="centered"
)

# --- AUTHENTICATION GUARD ---
# Check if user is authenticated and authorized for this bot
if not st.session_state.get('authenticated', False):
    st.error("⚠️ Access Denied: You must enter through the secret code portal.")
    st.info("Please go back to the main portal and enter your secret code.")
    if st.button("← Return to Portal"):
        st.switch_page("secret_code_portal.py")
    st.stop()

# Check if authorized for Perio bot (allow instructors access to all bots)
user_role = st.session_state.get('user_role', '')
redirect_info = st.session_state.get('redirect_info', {})
assigned_bot = redirect_info.get('bot', '')

# Instructors have access to all bots
if user_role != 'INSTRUCTOR':
    # For non-instructors, check bot assignment (case-insensitive)
    if assigned_bot.upper() != 'PERIO' and assigned_bot != 'ALL':
        st.error("⚠️ Access Denied: You are not authorized for this chatbot. "
                f"You are assigned to the {assigned_bot.upper()} chatbot.")
        if st.button("← Return to Portal"):
            st.switch_page("secret_code_portal.py")
        st.stop()

# Check if credentials are available
if 'groq_api_key' not in st.session_state or 'student_name' not in st.session_state:
    st.error("⚠️ Session Error: Missing credentials.")
    st.info("Please go back to the portal and re-enter your information.")
    if st.button("← Return to Portal"):
        st.switch_page("secret_code_portal.py")
    st.stop()

# --- UI: Title ---
st.title("🦷 Periodontitis MI Practice")

st.markdown(
    """
    Welcome to the **Periodontitis MI Practice App**. This chatbot simulates realistic patients 
    at different stages of gum disease based on the "Ava Johnson" case study. Your goal is to practice **Motivational Interviewing (MI)** skills 
    by engaging in a natural conversation and helping the patient explore their thoughts and feelings about their periodontal health. 
    At the end, you'll receive **detailed feedback** based on the official MI rubric.

    """,
    unsafe_allow_html=True
)

# --- Working directory ---
working_dir = os.path.dirname(os.path.abspath(__file__))

# --- Get credentials from session state ---
api_key = st.session_state.groq_api_key
student_name = st.session_state.student_name

# --- Set API key and initialize client ---
os.environ["GROQ_API_KEY"] = api_key
client = Groq()

# --- Initialize session state ---
from chat_utils import initialize_session_state
initialize_session_state()

# --- Step 1: Load Knowledge Document (MI Rubric) for RAG feedback ---
# Robust path resolution for rubrics directory
# Works whether this file is at repo root or under pages/
current_file = Path(__file__).resolve()
repo_root = current_file.parent.parent if current_file.parent.name == "pages" else current_file.parent

# Try to find perio_rubrics directory
rubrics_dir = None
possible_paths = [
    repo_root / "perio_rubrics",  # Standard location at repo root
    current_file.parent / "perio_rubrics",  # Fallback: same directory as script
]

for path in possible_paths:
    if path.exists() and path.is_dir():
        rubrics_dir = path
        break

if rubrics_dir is None:
    st.error("⚠️ Configuration Error: Rubric files not found.")
    st.info("The Perio rubric files are missing from the expected locations. Please contact your administrator.")
    logger.error(f"Failed to find perio_rubrics directory. Tried: {[str(p) for p in possible_paths]}")
    st.stop()

# Load rubric files
knowledge_texts = []
try:
    rubric_files = list(rubrics_dir.glob("*.txt"))
    if not rubric_files:
        st.error("⚠️ Configuration Error: No rubric files found.")
        st.info("The Perio rubric directory exists but contains no rubric files. Please contact your administrator.")
        logger.error(f"No .txt files found in {rubrics_dir}")
        st.stop()
    
    for rubric_file in rubric_files:
        try:
            with open(rubric_file, "r", encoding="utf-8", errors="ignore") as f:
                knowledge_texts.append(f.read())
        except Exception as e:
            logger.warning(f"Failed to read rubric file {rubric_file}: {e}")
            continue
    
    if not knowledge_texts:
        st.error("⚠️ Configuration Error: Could not load rubric content.")
        st.info("Failed to read rubric files. Please contact your administrator.")
        logger.error(f"Failed to load any rubric content from {rubrics_dir}")
        st.stop()
        
except Exception as e:
    st.error("⚠️ Configuration Error: Unable to access rubric files.")
    st.info(f"An error occurred while loading rubrics. Please contact your administrator.")
    logger.error(f"Error accessing rubrics directory {rubrics_dir}: {e}")
    st.stop()

# Combine all documents into a single knowledge base
knowledge_text = "\n\n".join(knowledge_texts)

# --- Step 2: Initialize RAG (Embeddings + FAISS) ---
# Use CPU device explicitly to avoid Meta tensor initialization errors
import torch
device = 'cuda' if torch.cuda.is_available() else 'cpu'
embedding_model = SentenceTransformer('all-MiniLM-L6-v2', device=device)

# --- Initialize session state for persona selection ---
if "selected_persona" not in st.session_state:
    st.session_state.selected_persona = None

# --- Persona Selection ---
if st.session_state.selected_persona is None:
    st.markdown("### Choose a Patient Persona (Ava Johnson Case Study)")
    st.markdown("""
    Select a stage of Ava's journey with periodontitis:
    
    - **Ava_Stage1**: Early stage - noticing bleeding gums, unaware of risk
    - **Ava_Stage2**: Progression - diagnosed with early periodontitis, needs deep cleaning
    - **Ava_Stage3**: Management - maintaining after treatment, struggling with consistency
    - **Ava_Stage4**: Advanced - severe bone loss, facing possible tooth extractions
    """)
    
    selected = st.selectbox(
        "Select a persona:",
        list(PERSONAS.keys()),
        key="persona_selector"
    )
    
    # Move "Start Conversation" button inside persona selection block
    if st.button("Start Conversation"):
        st.session_state.selected_persona = selected
        st.session_state.chat_history = []
        st.session_state.conversation_state = "active"
        st.session_state.turn_count = 0
        
        # Customize greeting based on stage
        stage_greetings = {
            "Ava_Stage1": "Hi, I'm Ava. I wanted to ask about something I've noticed with my gums...",
            "Ava_Stage2": "Hello, I'm Ava. My dentist just told me I have periodontitis and I'm honestly pretty worried.",
            "Ava_Stage3": "Hi there, I'm Ava. I've been managing gum disease for a while now, but I'm having trouble staying consistent.",
            "Ava_Stage4": "Hi, I'm Ava. I'm dealing with advanced periodontitis and facing some difficult decisions."
        }
        
        greeting = stage_greetings.get(selected, f"Hello! I'm {selected}, nice to meet you today.")
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": greeting
        })
        st.rerun()
    
    # Stop here if persona not selected yet
    st.stop()
      
def split_text(text, max_length=200):
    words = text.split()
    chunks, current_chunk = [], []
    for word in words:
        if len(" ".join(current_chunk + [word])) > max_length:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
        current_chunk.append(word)
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    return chunks

knowledge_chunks = split_text(knowledge_text)
dimension = 384  # for all-MiniLM-L6-v2
faiss_index = faiss.IndexFlatL2(dimension)
embeddings = embedding_model.encode(knowledge_chunks)
faiss_index.add(np.array(embeddings))

def retrieve_knowledge(query, top_k=2):
    query_embedding = embedding_model.encode([query])
    distances, indices = faiss_index.search(np.array(query_embedding), top_k)
    return [knowledge_chunks[i] for i in indices[0]]

# --- Display chat history ---
if st.session_state.selected_persona is not None:
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# --- Store feedback in session state ---
if "feedback" not in st.session_state:
  st.session_state.feedback = None
    
# --- Finish Session Button (Feedback with RAG) ---
# Only enable feedback button based on conversation state
from chat_utils import should_enable_feedback_button
from end_control_middleware import MIN_TURN_THRESHOLD

feedback_enabled = should_enable_feedback_button()
feedback_button_label = "Finish Session & Get Feedback"

if not feedback_enabled:
    if st.session_state.turn_count < MIN_TURN_THRESHOLD:
        st.info(f"💬 Continue the conversation (Turn {st.session_state.turn_count}/{MIN_TURN_THRESHOLD} minimum). The feedback button will be enabled after sufficient interaction.")

if st.button(feedback_button_label, disabled=not feedback_enabled):
    # Define current_timestamp and bot name at the beginning of this block
    current_timestamp = get_formatted_utc_time()
    evaluator = "Periodontitis Assessment Bot"
    
    transcript = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in st.session_state.chat_history])
    
    retrieved_info = retrieve_knowledge("motivational interviewing feedback rubric")
    rag_context = "\n".join(retrieved_info)

    # Use standardized evaluation prompt
    review_prompt = FeedbackFormatter.format_evaluation_prompt(
        "periodontitis and gum health", transcript, rag_context
    )

    try:
        feedback_response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": PERSONAS[st.session_state.selected_persona]},
                {"role": "user", "content": review_prompt}
            ]
        )
        feedback = feedback_response.choices[0].message.content
    except Exception as e:
        # Handle authentication errors gracefully
        error_msg = str(e).lower()
        if "401" in error_msg or "invalid api key" in error_msg or "authentication" in error_msg:
            st.error("❌ Invalid API Key detected. Please check your Groq API key and try again.")
            st.info("💡 To fix this: Enter a valid Groq API key in the field at the top of the page and restart the conversation.")
            st.stop()
        else:
            # Re-raise other unexpected errors
            raise
    
    # Store feedback in session state to prevent disappearing
    st.session_state.feedback = {
        'content': feedback,
        'timestamp': current_timestamp,
        'evaluator': evaluator
    }

# Show only PDF download section if feedback exists
if st.session_state.feedback is not None:
    feedback_data = st.session_state.feedback
    
    # Format feedback for PDF using standardized template
    formatted_feedback = FeedbackFormatter.format_feedback_for_pdf(
        feedback_data['content'], feedback_data['timestamp'], feedback_data['evaluator']
    )

    # Show only PDF download section
    st.markdown("### 📄 Download Feedback Report")
    st.info("Your feedback has been generated! Click below to download the PDF report.")

    # Validate student name and generate PDF
    try:
        validated_name = validate_student_name(student_name)
        
        pdf_buffer = generate_pdf_report(
            student_name=validated_name,
            raw_feedback=formatted_feedback,
            chat_history=st.session_state.chat_history,
            session_type="Periodontitis"
        )
        
        # Generate standardized filename
        download_filename = FeedbackFormatter.create_download_filename(
            student_name, "Perio", st.session_state.selected_persona
        )
        
        # Send email backup to Box (fail-safe - won't break if it fails)
        if 'email_backup_sent' not in st.session_state:
            st.session_state.email_backup_sent = False
            
        if not st.session_state.email_backup_sent:
            try:
                from pdf_utils import send_pdf_to_box
                with st.spinner("Backing up report to Box..."):
                    email_result = send_pdf_to_box(
                        pdf_buffer=pdf_buffer,
                        filename=download_filename,
                        student_name=validated_name,
                        session_type="Perio"
                    )
                    
                    if email_result['success']:
                        st.success("✅ Report successfully backed up to Box!")
                        st.session_state.email_backup_sent = True
                    else:
                        st.warning(f"⚠️ Box backup failed after {email_result['attempts']} attempts. "
                                 "Your PDF is still available for download below.")
                        if email_result.get('error'):
                            st.info(f"Details: {email_result['error']}")
            except Exception as e:
                st.warning(f"⚠️ Box backup unavailable. Your PDF is still available for download below.")
                # Don't show technical error to user, but log it
                import logging
                logging.error(f"Email backup error: {e}")
        
        # Add download button with enhanced label
        st.download_button(
            label="📥 Download Periodontitis MI Performance Report (PDF)",
            data=pdf_buffer.getvalue(),
            file_name=download_filename,
            mime="application/pdf",
            help="Download your complete feedback report as a PDF"
        )
            
    except ValueError as e:
        st.error(f"Error generating PDF: {e}")
        st.info("Please check your student name and try again.")
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        st.info("There was an issue generating the PDF. Please try again.")

# --- Handle chat input (Using improved chat_utils with persona guards) ---
from chat_utils import handle_chat_input
import inspect

# Check if handle_chat_input supports domain parameters
handle_chat_params = inspect.signature(handle_chat_input).parameters
supports_domain_params = 'domain_name' in handle_chat_params and 'domain_keywords' in handle_chat_params

if supports_domain_params:
    handle_chat_input(PERSONAS, client,
                     domain_name=PERIO_DOMAIN_NAME,
                     domain_keywords=PERIO_DOMAIN_KEYWORDS)
else:
    # Fall back to older signature without domain parameters
    logger.warning("Using older chat_utils signature without domain parameters")
    handle_chat_input(PERSONAS, client)

# Add a button to start a new conversation with a different persona
from chat_utils import handle_new_conversation_button
handle_new_conversation_button()
