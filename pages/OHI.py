"""
OHI MI Practice Application - Oral Hygiene Motivational Interviewing Chatbot

This Streamlit application provides an interactive environment for dental students
to practice Motivational Interviewing (MI) skills in oral hygiene counseling.

Features:
- Multiple patient personas with varying oral hygiene habits and attitudes
- Real-time conversation with AI-powered patient simulators
- RAG-based feedback using MI rubrics from ohi_rubrics/ directory
- Automated scoring on 30-point MI rubric (4 components × 7.5 points)
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
from pathlib import Path
import streamlit as st
from groq import Groq
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from time_utils import get_formatted_utc_time
from pdf_utils import generate_pdf_report
from feedback_template import FeedbackFormatter, FeedbackValidator
from scoring_utils import validate_student_name
from persona_texts import (
    OHI_PERSONAS,
    get_ohi_persona,
    OHI_DOMAIN_NAME,
    OHI_DOMAIN_KEYWORDS
)

# Configure logging
logger = logging.getLogger(__name__)

# Convert structured personas to simple dict for backward compatibility
PERSONAS = {name: persona['system_prompt'] for name, persona in OHI_PERSONAS.items()}

# --- Streamlit page configuration ---
st.set_page_config(
    page_title="Dental MI Practice",
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

# Check if authorized for OHI bot
redirect_info = st.session_state.get('redirect_info', {})
if redirect_info.get('bot') != 'OHI':
    st.error("⚠️ Access Denied: You are not authorized for this chatbot.")
    st.info(f"You are assigned to the {redirect_info.get('bot', 'unknown')} chatbot.")
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
st.title("🦷 OHI MI Practice")

st.markdown(
    """
    Welcome to the **OHI MI Practice App**. This chatbot simulates a realistic patient 
    who is uncertain about the OHI recommendations. Your goal is to practice **Motivational Interviewing (MI)** skills 
    by engaging in a natural conversation and helping the patient explore their thoughts and feelings. 
    At the end, you’ll receive **detailed feedback** based on the official MI rubric.

    """,
    unsafe_allow_html=True
)

# --- Robust Path Resolution for Rubrics ---
# Compute both script directory and repository root
script_dir = Path(__file__).resolve().parent
repo_root = script_dir.parent

# Search for rubrics directory in priority order
rubrics_dir = None
search_locations = [
    repo_root / "ohi_rubrics",  # Primary: repo root (matches independent layout)
    script_dir / "ohi_rubrics"  # Fallback: pages subdirectory
]

for location in search_locations:
    if location.exists() and location.is_dir():
        rubrics_dir = location
        break

# Show clear error if rubrics directory not found
if rubrics_dir is None:
    st.error("⚠️ **Missing ohi_rubrics directory**")
    st.markdown("""
    The OHI rubric files could not be found. Please ensure:
    - The `ohi_rubrics` directory exists at the repository root
    - It contains the required `.txt` rubric files
    - The directory has proper read permissions
    
    Expected locations searched:
    - `{repo_root}/ohi_rubrics`
    - `{pages}/ohi_rubrics`
    """)
    if st.button("← Return to Portal"):
        st.switch_page("secret_code_portal.py")
    st.stop()

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
# Load multiple example rubrics from the ohi_rubrics folder
knowledge_texts = []

for filename in os.listdir(rubrics_dir):
    if filename.endswith(".txt"):
        with open(rubrics_dir / filename, "r", encoding="utf-8", errors="ignore") as f:
            knowledge_texts.append(f.read())

# Combine all documents into a single knowledge base
knowledge_text = "\n\n".join(knowledge_texts)

# --- Step 2: Initialize RAG (Embeddings + FAISS) ---
# Use CPU device explicitly to avoid Meta tensor initialization errors
import torch
device = 'cuda' if torch.cuda.is_available() else 'cpu'
embedding_model = SentenceTransformer('all-MiniLM-L6-v2', device=device)

# Add after the student name input section:

# --- Initialize session state for persona selection ---
if "selected_persona" not in st.session_state:
    st.session_state.selected_persona = None

# --- Persona Selection ---
if st.session_state.selected_persona is None:
    st.markdown("### Choose a Patient Persona")
    st.markdown("""
    Select a patient persona to practice with:
    
    - **Alex**: 28-year-old marketing professional with mixed oral hygiene habits
    - **Bob**: 25-year-old software developer, introverted with poor oral hygiene
    - **Charles**: 35-year-old executive with good oral hygiene habits
    - **Diana**: 31-year-old retail manager with average habits and resistant attitude
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
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": f"Hello! I'm {selected}, nice to meet you today."
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
    evaluator = "OHI Assessment Bot"
    
    transcript = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in st.session_state.chat_history])
    
    retrieved_info = retrieve_knowledge("motivational interviewing feedback rubric")
    rag_context = "\n".join(retrieved_info)

    # Use standardized evaluation prompt
    review_prompt = FeedbackFormatter.format_evaluation_prompt(
        "dental hygiene", transcript, rag_context
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
            session_type="OHI"
        )
        
        # Generate standardized filename
        download_filename = FeedbackFormatter.create_download_filename(
            student_name, "OHI", st.session_state.selected_persona
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
                        session_type="OHI"
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
            label="📥 Download OHI MI Performance Report (PDF)",
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

# Try to call with domain parameters for backward compatibility
try:
    handle_chat_input(PERSONAS, client,
                     domain_name=OHI_DOMAIN_NAME,
                     domain_keywords=OHI_DOMAIN_KEYWORDS)
except TypeError as e:
    # Fall back to older signature without domain parameters
    if "domain_name" in str(e) or "domain_keywords" in str(e):
        logger.warning("Using older chat_utils signature without domain parameters")
        handle_chat_input(PERSONAS, client)
    else:
        # Re-raise if it's a different TypeError
        raise

# Add a button to start a new conversation with a different persona
from chat_utils import handle_new_conversation_button
handle_new_conversation_button()
