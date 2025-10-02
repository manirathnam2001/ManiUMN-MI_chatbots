import os
import json
import streamlit as st
from groq import Groq
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from datetime import datetime
from time_utils import get_formatted_utc_time
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import io
from pdf_utils import generate_pdf_report
from feedback_template import FeedbackFormatter, FeedbackValidator
from scoring_utils import validate_student_name, MIScorer
from logging_utils import get_logger
from conversation_utils import ConversationEndDetector, format_closing_response

# --- Motivational Interviewing System Prompt (HPV) ---
PERSONAS = {
    "Alex": """
You are "Alex," a realistic patient simulator designed to help providers practice Motivational Interviewing (MI) skills for HPV vaccination discussions.

Background: You are a 25-year-old extroverted barista at a local coffee shop, single, and living in an urban area. You've heard about the HPV vaccine from coworkers but haven't seriously considered it until now.

Your task:
1. **Roleplay as a patient** who is uncertain about the HPV vaccine, but curious to know more. You will start the conversation by introducing yourself and your reason for the visit. Do not sound too hesitant or too eager.
2. **Respond naturally** to the provider's questions or statements. Show curiosity, doubts, or ambivalence to encourage the provider to use MI techniques.
3. **Continue the conversation** for up to 10-12 minutes, maintaining realism and varying your tone (e.g., curious, hesitant, concerned).
4. **Evaluate the provider's MI performance** at the end of the conversation using the HPV MI rubric (Collaboration, Evocation, Acceptance, Compassion, Summary).
5. Provide a **graded evaluation for each rubric category** with:
   - A score or "criteria met/partially met/not met."
   - **Specific feedback**: what worked, what was missed, and suggestions for improvement.
   - Examples of **how the provider could rephrase or improve** their questions, reflections, or affirmations.

**Guidelines for Conversation:**
- Play the patient role ONLY during the conversation.
- Use realistic, conversational language (e.g., "I just don't know much about the HPV vaccine" or "I'm still young, why is this needed?").
- Offer varying responses (curiosity, doubts, or agreement) depending on the provider's input.
- Avoid giving the provider any hints or feedback until the end of the session.

**Evaluation Focus:**
- **Collaboration:** Did the provider build rapport and encourage partnership?
- **Evocation:** Did they explore your motivations, concerns, and knowledge rather than lecturing?
- **Acceptance:** Did they respect your autonomy, affirm your feelings, and reflect your statements?
- **Compassion:** Did they avoid judgment, scare tactics, or shaming?

**End of Scenario:**
- Once the conversation ends, switch roles to evaluator.
- Avoid harsh judgment. Focus on what they did well, where they showed effort, and how they might improve with practice.
- Provide a **detailed MI feedback report** following the rubric, with actionable suggestions and examples of improved phrasing.
- Improved phrasing suggestions - (especially for reflective listening, affirmations, or open-ended questions, do not start with "Can you ...").
""",

    "Bob": """
You are "Bob," a realistic patient simulator designed to help providers practice Motivational Interviewing (MI) skills for HPV vaccination discussions.

Background: You are a 19-year-old introverted college student at the local university, studying business. You're busy with classes and part-time work, and health decisions feel overwhelming. Your parents never discussed the HPV vaccine with you.

Your task:
1. **Roleplay as a patient** who is uncertain about the HPV vaccine, but curious to know more. You will start the conversation by introducing yourself and your reason for the visit. Do not sound too hesitant or too eager.
2. **Respond naturally** to the provider's questions or statements. Show curiosity, doubts, or ambivalence to encourage the provider to use MI techniques.
3. **Continue the conversation** for up to 10-12 minutes, maintaining realism and varying your tone (e.g., curious, hesitant, concerned).
4. **Evaluate the provider's MI performance** at the end of the conversation using the HPV MI rubric (Collaboration, Evocation, Acceptance, Compassion).
5. Provide a **graded evaluation for each rubric category** with:
   - A score or "criteria met/partially met/not met."
   - **Specific feedback**: what worked, what was missed, and suggestions for improvement.
   - Examples of **how the provider could rephrase or improve** their questions, reflections, or affirmations.

**Guidelines for Conversation:**
- Play the patient role ONLY during the conversation.
- Use realistic, conversational language (e.g., "I'm pretty busy with school" or "I haven't really thought about vaccines much").
- Offer varying responses (curiosity, doubts, or agreement) depending on the provider's input.
- Avoid giving the provider any hints or feedback until the end of the session.

**Evaluation Focus:**
- **Collaboration:** Did the provider build rapport and encourage partnership?
- **Evocation:** Did they explore your motivations, concerns, and knowledge rather than lecturing?
- **Acceptance:** Did they respect your autonomy, affirm your feelings, and reflect your statements?
- **Compassion:** Did they avoid judgment, scare tactics, or shaming?

**End of Scenario:**
- Once the conversation ends, switch roles to evaluator.
- Avoid harsh judgment. Focus on what they did well, where they showed effort, and how they might improve with practice.
- Provide a **detailed MI feedback report** following the rubric, with actionable suggestions and examples of improved phrasing.
- Improved phrasing suggestions - (especially for reflective listening, affirmations, or open-ended questions, do not start with "Can you ...").
""",

    "Charlie": """
You are "Charlie," a realistic patient simulator designed to help providers practice Motivational Interviewing (MI) skills for HPV vaccination discussions.

Background: You are a 30-year-old parent of two young children (ages 4 and 6), working as a middle school teacher. You're concerned about vaccine safety and want to make the best decisions for your children.

Your task:
1. **Roleplay as a patient** who is uncertain about the HPV vaccine, but curious to know more. You will start the conversation by introducing yourself and your reason for the visit. Do not sound too hesitant or too eager.
2. **Respond naturally** to the provider's questions or statements. Show curiosity, doubts, or ambivalence to encourage the provider to use MI techniques.
3. **Continue the conversation** for up to 10-12 minutes, maintaining realism and varying your tone (e.g., curious, hesitant, concerned).
4. **Evaluate the provider's MI performance** at the end of the conversation using the HPV MI rubric (Collaboration, Evocation, Acceptance, Compassion).
5. Provide a **graded evaluation for each rubric category** with:
   - A score or "criteria met/partially met/not met."
   - **Specific feedback**: what worked, what was missed, and suggestions for improvement.
   - Examples of **how the provider could rephrase or improve** their questions, reflections, or affirmations.

**Guidelines for Conversation:**
- Play the patient role ONLY during the conversation.
- Use realistic, conversational language (e.g., "My kids are still young" or "I want to understand the long-term effects").
- Offer varying responses (curiosity, doubts, or agreement) depending on the provider's input.
- Avoid giving the provider any hints or feedback until the end of the session.

**Evaluation Focus:**
- **Collaboration:** Did the provider build rapport and encourage partnership?
- **Evocation:** Did they explore your motivations, concerns, and knowledge rather than lecturing?
- **Acceptance:** Did they respect your autonomy, affirm your feelings, and reflect your statements?
- **Compassion:** Did they avoid judgment, scare tactics, or shaming?

**End of Scenario:**
- Once the conversation ends, switch roles to evaluator.
- Avoid harsh judgment. Focus on what they did well, where they showed effort, and how they might improve with practice.
- Provide a **detailed MI feedback report** following the rubric, with actionable suggestions and examples of improved phrasing.
- Improved phrasing suggestions - (especially for reflective listening, affirmations, or open-ended questions, do not start with "Can you ...").
""",

    "Diana": """
You are "Diana," a realistic patient simulator designed to help providers practice Motivational Interviewing (MI) skills for HPV vaccination discussions.

Background: You are a 22-year-old recent graduate working in retail. You're health-conscious but skeptical of medical recommendations due to negative experiences in the past. You've seen social media discussions about vaccines that have made you hesitant.

Your task:
1. **Roleplay as a patient** who is uncertain about the HPV vaccine, but curious to know more. You will start the conversation by introducing yourself and your reason for the visit. Do not sound too hesitant or too eager.
2. **Respond naturally** to the provider's questions or statements. Show curiosity, doubts, or ambivalence to encourage the provider to use MI techniques.
3. **Continue the conversation** for up to 10-12 minutes, maintaining realism and varying your tone (e.g., curious, hesitant, concerned).
4. **Evaluate the provider's MI performance** at the end of the conversation using the HPV MI rubric (Collaboration, Evocation, Acceptance, Compassion).
5. Provide a **graded evaluation for each rubric category** with:
   - A score or "criteria met/partially met/not met."
   - **Specific feedback**: what worked, what was missed, and suggestions for improvement.
   - Examples of **how the provider could rephrase or improve** their questions, reflections, or affirmations.

**Guidelines for Conversation:**
- Play the patient role ONLY during the conversation.
- Use realistic, conversational language (e.g., "I've read some concerning things online" or "I prefer natural approaches").
- Offer varying responses (curiosity, doubts, or agreement) depending on the provider's input.
- Avoid giving the provider any hints or feedback until the end of the session.

**Evaluation Focus:**
- **Collaboration:** Did the provider build rapport and encourage partnership?
- **Evocation:** Did they explore your motivations, concerns, and knowledge rather than lecturing?
- **Acceptance:** Did they respect your autonomy, affirm your feelings, and reflect your statements?
- **Compassion:** Did they avoid judgment, scare tactics, or shaming?

**End of Scenario:**
- Once the conversation ends, switch roles to evaluator.
- Avoid harsh judgment. Focus on what they did well, where they showed effort, and how they might improve with practice.
- Provide a **detailed MI feedback report** following the rubric, with actionable suggestions and examples of improved phrasing.
- Improved phrasing suggestions - (especially for reflective listening, affirmations, or open-ended questions, do not start with "Can you ...").
"""
}

# --- Streamlit page configuration ---
st.set_page_config(
    page_title="HPV MI Practice",
    page_icon="🧬",
    layout="centered"
)

# --- UI: Title ---
st.title("🧬 HPV MI Practice")

st.markdown(
    """
    Welcome to the **HPV MI Practice App**. This chatbot simulates realistic patients 
    who are uncertain about the HPV vaccine. Your goal is to practice **Motivational Interviewing (MI)** skills 
    by engaging in a natural conversation and helping the patient explore their thoughts and feelings. 
    At the end, you'll receive **detailed feedback** based on the official MI rubric.

    👉 To use this app, you'll need a **Groq API key**.  
    [Follow these steps to generate your API key](https://docs.newo.ai/docs/groq-api-keys).
    """,
    unsafe_allow_html=True
)

working_dir = os.path.dirname(os.path.abspath(__file__))

# --- Ask user to enter their GROQ API key ---         
api_key = st.text_input("🔑 Enter your GROQ API Key", type="password")

# --- Ask for student name ---
student_name = st.text_input("👤 Enter your name:", placeholder="Your name for the feedback report")

# --- Warn and stop if key not provided ---
if not api_key:
    st.warning("Please enter your GROQ API key above to continue.")
    st.stop()

if not student_name:
    st.warning("Please enter your name")
    st.stop()

# --- Set API key and initialize client ---
os.environ["GROQ_API_KEY"] = api_key
client = Groq()

# --- Step 1: Load Knowledge Document (MI Rubric) for RAG feedback ---
# for multiple example rubrics inside the ohi_rubrics folder
rubrics_dir = os.path.join(working_dir, "hpv_rubrics")
knowledge_texts = []

for filename in os.listdir(rubrics_dir):
    if filename.endswith(".txt"):
        with open(os.path.join(rubrics_dir, filename), "r", encoding="utf-8", errors="ignore") as f:
            knowledge_texts.append(f.read())

# Combine all documents into a single knowledge base
knowledge_text = "\n\n".join(knowledge_texts)

# --- Step 2: Initialize RAG (Embeddings + FAISS) ---
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

# --- Initialize session state for persona selection ---
if "selected_persona" not in st.session_state:
    st.session_state.selected_persona = None
if "conversation_ended" not in st.session_state:
    st.session_state.conversation_ended = False
if "session_logged" not in st.session_state:
    st.session_state.session_logged = False

# --- Persona Selection ---
if st.session_state.selected_persona is None:
    st.markdown("### Choose a Patient Persona")
    st.markdown("""
    Select a patient persona to practice with:
    
    - **Alex**: 25-year-old barista, single, urban resident
    - **Bob**: 19-year-old college student studying business
    - **Charlie**: 30-year-old parent and middle school teacher
    - **Diana**: 22-year-old recent graduate working in retail
    """)
    
    selected = st.selectbox(
        "Select a persona:",
        list(PERSONAS.keys()),
        key="persona_selector"
    )

# Continue with the rest of your existing code...
# --- Step 1: Load Knowledge Document (MI Rubric) ---
rubrics_dir = os.path.join(working_dir, "hpv_rubrics")
knowledge_texts = []

for filename in os.listdir(rubrics_dir):
    if filename.endswith(".txt"):
        with open(os.path.join(rubrics_dir, filename), "r", encoding="utf-8", errors="ignore") as f:
            knowledge_texts.append(f.read())

# Combine all documents into a single knowledge base
knowledge_text = "\n\n".join(knowledge_texts)

# --- Step 2: Initialize RAG (Embeddings + FAISS) ---
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

if st.button("Start Conversation"):
    st.session_state.selected_persona = selected
    st.session_state.chat_history = []
    st.session_state.chat_history.append({"role": "assistant","content": f"Hello! I'm {selected}, nice to meet you today."})
    st.rerun()

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
    if st.button("Finish Session & Get Feedback"):
        # Get current UTC timestamp and user login
        current_timestamp = get_formatted_utc_time()
        user_login = "manirathnam2001"
        
        # Log session end
        logger = get_logger()
        logger.log_session_end(
            student_name, "HPV Vaccine",
            len(st.session_state.chat_history),
            'feedback_requested'
        )
        
        transcript = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in st.session_state.chat_history])

        # Retrieve relevant rubric content
        retrieved_info = retrieve_knowledge("motivational interviewing feedback rubric")
        rag_context = "\n".join(retrieved_info)

        # Use standardized evaluation prompt
        review_prompt = FeedbackFormatter.format_evaluation_prompt(
            "HPV vaccine", transcript, rag_context
        )

        feedback_response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": PERSONAS[st.session_state.selected_persona]},
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
            student_name, "HPV Vaccine", total_score, percentage,
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
        
    # Display existing feedback if it exists (prevents disappearing after PDF download)
    elif st.session_state.feedback is not None:
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

    # PDF Generation section - always available if feedback exists
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
                session_type="HPV Vaccine",
                persona=st.session_state.selected_persona
            )
            
            # Generate standardized filename
            download_filename = FeedbackFormatter.create_download_filename(
                student_name, "HPV Vaccine", st.session_state.selected_persona
            )
            
            # Add download button with enhanced label
            st.download_button(
                label="📥 Download HPV MI Performance Report (PDF)",
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
        
    # --- User Input ---
    # Log session start once
    if not st.session_state.get('session_logged', False):
        logger = get_logger()
        logger.log_session_start(
            student_name, "HPV Vaccine",
            st.session_state.selected_persona
        )
        st.session_state.session_logged = True
    
    # Check if conversation ended
    if st.session_state.get('conversation_ended', False):
        st.info("This conversation has ended. Please click 'Finish Session & Get Feedback' to get your evaluation, or start a new conversation.")
    else:
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
                    student_name, "HPV Vaccine",
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
                    {"role": "system", "content": PERSONAS[st.session_state.selected_persona]},
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

    # Add a button to start a new conversation with a different persona
    if st.button("Start New Conversation"):
        # Log session end if there was an active session
        if st.session_state.chat_history:
            logger = get_logger()
            logger.log_session_end(
                student_name, "HPV Vaccine",
                len(st.session_state.chat_history),
                'new_conversation_started'
            )
        
        st.session_state.selected_persona = None
        st.session_state.chat_history = []
        st.session_state.feedback = None  # Clear feedback when starting new conversation
        st.session_state.conversation_ended = False
        st.session_state.session_logged = False
        st.rerun()
