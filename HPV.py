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
from pdf_utils import parse_feedback_response, generate_pdf_report

# --- Persona System Prompts ---
PERSONAS = {
    "Alex": """
You are "Alex," a realistic patient simulator designed to help providers practice Motivational Interviewing (MI) skills for HPV vaccination discussions.

Background: You are a 25-year-old barista at a local coffee shop, single, and living in an urban area. You've heard about the HPV vaccine from coworkers but haven't seriously considered it until now.

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
- **Summary:** Did they wrap up with a reflective summary and clear next steps?

**End of Scenario:**
- Once the conversation ends, switch roles to evaluator.
- Avoid harsh judgment. Focus on what they did well, where they showed effort, and how they might improve with practice.
- Provide a **detailed MI feedback report** following the rubric, with actionable suggestions and examples of improved phrasing.
- Improved phrasing suggestions - (especially for reflective listening, affirmations, or open-ended questions, do not start with "Can you ...").
""",

    "Bob": """
You are "Bob," a realistic patient simulator designed to help providers practice Motivational Interviewing (MI) skills for HPV vaccination discussions.

Background: You are a 19-year-old college student at the local university, studying business. You're busy with classes and part-time work, and health decisions feel overwhelming. Your parents never discussed the HPV vaccine with you.

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
- Use realistic, conversational language (e.g., "I'm pretty busy with school" or "I haven't really thought about vaccines much").
- Offer varying responses (curiosity, doubts, or agreement) depending on the provider's input.
- Avoid giving the provider any hints or feedback until the end of the session.

**Evaluation Focus:**
- **Collaboration:** Did the provider build rapport and encourage partnership?
- **Evocation:** Did they explore your motivations, concerns, and knowledge rather than lecturing?
- **Acceptance:** Did they respect your autonomy, affirm your feelings, and reflect your statements?
- **Compassion:** Did they avoid judgment, scare tactics, or shaming?
- **Summary:** Did they wrap up with a reflective summary and clear next steps?

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
4. **Evaluate the provider's MI performance** at the end of the conversation using the HPV MI rubric (Collaboration, Evocation, Acceptance, Compassion, Summary).
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
- **Summary:** Did they wrap up with a reflective summary and clear next steps?

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
4. **Evaluate the provider's MI performance** at the end of the conversation using the HPV MI rubric (Collaboration, Evocation, Acceptance, Compassion, Summary).
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
- **Summary:** Did they wrap up with a reflective summary and clear next steps?

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
    st.warning("Please enter your name for the feedback report.")
    st.stop()

# --- Set API key and initialize client ---
os.environ["GROQ_API_KEY"] = api_key
client = Groq()

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
    
    if st.button("Start Conversation"):
        st.session_state.selected_persona = selected
        st.session_state.chat_history = []
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": f"Hello! I'm {selected}, nice to meet you today."
        })
        st.rerun()

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

    # --- Finish Session Button (Feedback with RAG) ---
 if st.button("Finish Session & Get Feedback"):
        # Get current UTC timestamp and user login
        current_timestamp = get_formatted_utc_time()
        user_login = "manirathnam2001"
        
        transcript = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in st.session_state.chat_history])

        # Retrieve relevant rubric content
        retrieved_info = retrieve_knowledge("motivational interviewing feedback rubric")
        rag_context = "\n".join(retrieved_info)

        review_prompt = f"""
    Evaluation Timestamp (UTC): {current_timestamp}
    Evaluator: {user_login}
    
    Here is the dental hygiene session transcript:
    {transcript}

    Relevant MI Knowledge:
    {rag_context}
    
    Based on the MI rubric, evaluate the user's MI skills using the 30-point scoring system (7.5 points × 4 components).
    Provide feedback with scores for Evocation (7.5 pts), Acceptance (7.5 pts), Collaboration (7.5 pts), and Compassion (7.5 pts).
    Include a Summary section (without points) that provides strengths, examples of change talk, and clear next-step suggestions.
    
    Please evaluate each MI component and clearly state for each one:
    1. COLLABORATION: [Met/Partially Met/Not Met] - [specific feedback about partnership and rapport]
    2. EVOCATION: [Met/Partially Met/Not Met] - [specific feedback about drawing out patient motivations]
    3. ACCEPTANCE: [Met/Partially Met/Not Met] - [specific feedback about respecting autonomy and reflecting]
    4. COMPASSION: [Met/Partially Met/Not Met] - [specific feedback about warmth and non-judgmental approach]
    5. SUMMARY: [Met/Partially Met/Not Met] - [specific feedback about closure and next steps]
    
    For each component, also provide specific suggestions for improvement.
    Include overall strengths and clear next-step suggestions for continued learning.
    """

        feedback_response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": PERSONAS[st.session_state.selected_persona]},
                {"role": "user", "content": review_prompt}
            ]
        )
        feedback = feedback_response.choices[0].message.content
         # Display feedback with timestamp header
        st.markdown("### Session Feedback")
        st.markdown(f"**Evaluation Timestamp (UTC):** {current_timestamp}")
        st.markdown(f"**Evaluator:** {user_login}")
        st.markdown("---")
        st.markdown(feedback)
        
        # --- PDF Generation ---
        st.markdown("### 📄 Download PDF Report")
        
        # Parse feedback response for structured data
        components = parse_feedback_response(feedback)
        
        # Generate PDF report
        pdf_buffer = generate_pdf_report(student_name, components, "HPV Vaccine")
        
        # Add download button
        st.download_button(
            label="📥 Download MI Performance Report (PDF)",
            data=pdf_buffer.getvalue(),
            file_name=f"MI_Feedback_Report_{student_name.replace(' ', '_')}_{st.session_state.selected_persona}.pdf",
            mime="application/pdf"
        )

    # --- User Input ---
    user_prompt = st.chat_input("Your response...")

    if user_prompt:
        st.session_state.chat_history.append({"role": "user", "content": user_prompt})
        st.chat_message("user").markdown(user_prompt)

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
            model="openai/gpt-oss-120b",
            messages=messages
        )
        assistant_response = response.choices[0].message.content

        st.session_state.chat_history.append({"role": "assistant", "content": assistant_response})
        with st.chat_message("assistant"):
            st.markdown(assistant_response)

    # Add a button to start a new conversation with a different persona
    if st.button("Start New Conversation"):
        st.session_state.selected_persona = None
        st.session_state.chat_history = []
        st.rerun()
