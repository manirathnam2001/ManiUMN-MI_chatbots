"""
HPV MI Practice Application - Motivational Interviewing Chatbot

This Streamlit application provides an interactive environment for healthcare providers
to practice Motivational Interviewing (MI) skills in HPV vaccination discussions.

Features:
- Multiple patient personas with different backgrounds and concerns
- Real-time conversation with AI-powered patient simulators
- RAG-based feedback using MI rubrics from hpv_rubrics/ directory
- Automated scoring on 30-point MI rubric (4 components × 7.5 points)
- Professional PDF reports with detailed feedback and conversation transcripts

The application uses:
- Groq LLM API for natural conversation
- FAISS for vector similarity search in rubric retrieval
- Sentence Transformers for embedding generation
- Streamlit for the user interface

Usage:
    streamlit run HPV.py

Requirements:
    - GROQ API key (enter in the UI or set as environment variable)
    - Student name for feedback reports
    - Internet connection for LLM API calls
"""

import os
import streamlit as st
from groq import Groq
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from time_utils import get_formatted_utc_time
from pdf_utils import generate_pdf_report
from feedback_template import FeedbackFormatter, FeedbackValidator
from scoring_utils import validate_student_name

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

**CRITICAL - Response Guidelines:**
- **Keep ALL responses CONCISE - maximum 2-3 sentences per reply**
- **Stay in patient role ONLY during the conversation - NO evaluation or feedback until the end**
- Use realistic, conversational language (e.g., "I just don't know much about the HPV vaccine" or "I'm still young, why is this needed?")
- Offer varying responses (curiosity, doubts, or agreement) depending on the provider's input
- **DO NOT provide any hints, feedback, scores, or evaluation during the conversation**
- **DO NOT switch to evaluator role until explicitly asked after the conversation ends**

**Natural Conversation Ending:**
- When the conversation has naturally reached a good stopping point (typically after 10-15 exchanges where the provider has used open-ended questions, reflections, autonomy support, and summary), you may signal readiness to end by including: <<END>>
- Example: "Thank you for taking the time to explain this. I feel more informed now. <<END>>"
- Only use <<END>> when the conversation feels complete and all MI components have been demonstrated

**Evaluation Focus (ONLY after conversation ends):**
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

**CRITICAL - Response Guidelines:**
- **Keep ALL responses CONCISE - maximum 2-3 sentences per reply**
- **Stay in patient role ONLY during the conversation - NO evaluation or feedback until the end**
- Use realistic, conversational language (e.g., "I'm pretty busy with school" or "I haven't really thought about vaccines much")
- Offer varying responses (curiosity, doubts, or agreement) depending on the provider's input
- **DO NOT provide any hints, feedback, scores, or evaluation during the conversation**
- **DO NOT switch to evaluator role until explicitly asked after the conversation ends**

**Natural Conversation Ending:**
- When the conversation has naturally reached a good stopping point (typically after 10-15 exchanges where the provider has used open-ended questions, reflections, autonomy support, and summary), you may signal readiness to end by including: <<END>>
- Example: "Thank you for taking the time to explain this. I feel more informed now. <<END>>"
- Only use <<END>> when the conversation feels complete and all MI components have been demonstrated

**Evaluation Focus (ONLY after conversation ends):**
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

**CRITICAL - Response Guidelines:**
- **Keep ALL responses CONCISE - maximum 2-3 sentences per reply**
- **Stay in patient role ONLY during the conversation - NO evaluation or feedback until the end**
- Use realistic, conversational language (e.g., "My kids are still young" or "I want to understand the long-term effects")
- Offer varying responses (curiosity, doubts, or agreement) depending on the provider's input
- **DO NOT provide any hints, feedback, scores, or evaluation during the conversation**
- **DO NOT switch to evaluator role until explicitly asked after the conversation ends**

**Natural Conversation Ending:**
- When the conversation has naturally reached a good stopping point (typically after 10-15 exchanges where the provider has used open-ended questions, reflections, autonomy support, and summary), you may signal readiness to end by including: <<END>>
- Example: "Thank you for taking the time to explain this. I feel more informed now. <<END>>"
- Only use <<END>> when the conversation feels complete and all MI components have been demonstrated

**Evaluation Focus (ONLY after conversation ends):**
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

**CRITICAL - Response Guidelines:**
- **Keep ALL responses CONCISE - maximum 2-3 sentences per reply**
- **Stay in patient role ONLY during the conversation - NO evaluation or feedback until the end**
- Use realistic, conversational language (e.g., "I've read some concerning things online" or "I prefer natural approaches")
- Offer varying responses (curiosity, doubts, or agreement) depending on the provider's input
- **DO NOT provide any hints, feedback, scores, or evaluation during the conversation**
- **DO NOT switch to evaluator role until explicitly asked after the conversation ends**

**Natural Conversation Ending:**
- When the conversation has naturally reached a good stopping point (typically after 10-15 exchanges where the provider has used open-ended questions, reflections, autonomy support, and summary), you may signal readiness to end by including: <<END>>
- Example: "Thank you for taking the time to explain this. I feel more informed now. <<END>>"
- Only use <<END>> when the conversation feels complete and all MI components have been demonstrated

**Evaluation Focus (ONLY after conversation ends):**
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

# --- Initialize session state ---
from chat_utils import initialize_session_state
initialize_session_state()

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
# Use CPU device explicitly to avoid Meta tensor initialization errors
import torch
device = 'cuda' if torch.cuda.is_available() else 'cpu'
embedding_model = SentenceTransformer('all-MiniLM-L6-v2', device=device)

# --- Initialize session state for persona selection ---
if "selected_persona" not in st.session_state:
    st.session_state.selected_persona = None

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
# Device already set above, reuse the same embedding model configuration
embedding_model = SentenceTransformer('all-MiniLM-L6-v2', device=device)

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
    # Only enable feedback button based on conversation state
    from chat_utils import should_enable_feedback_button
    from end_control_middleware import MIN_TURN_THRESHOLD
    
    feedback_enabled = should_enable_feedback_button()
    feedback_button_label = "Finish Session & Get Feedback"
    
    if not feedback_enabled:
        if st.session_state.turn_count < MIN_TURN_THRESHOLD:
            st.info(f"💬 Continue the conversation (Turn {st.session_state.turn_count}/{MIN_TURN_THRESHOLD} minimum). The feedback button will be enabled after sufficient interaction.")
        
    if st.button(feedback_button_label, disabled=not feedback_enabled):
        # Get current timestamp and bot name
        current_timestamp = get_formatted_utc_time()
        evaluator = "HPV Assessment Bot"
        
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
        
        # Store feedback in session state to prevent disappearing
        st.session_state.feedback = {
            'content': feedback,
            'timestamp': current_timestamp,
            'evaluator': evaluator
        }

    # PDF Generation section - only show PDF download
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
                session_type="HPV Vaccine"
            )
            
            # Generate standardized filename
            download_filename = FeedbackFormatter.create_download_filename(
                student_name, "HPV", st.session_state.selected_persona
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
                            session_type="HPV Vaccine"
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
                label="📥 Download HPV MI Performance Report (PDF)",
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
        
    # --- User Input (Using improved chat_utils) ---
    from chat_utils import handle_chat_input
    handle_chat_input(PERSONAS, client)

    # Add a button to start a new conversation with a different persona
    from chat_utils import handle_new_conversation_button
    handle_new_conversation_button()
