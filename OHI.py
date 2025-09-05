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
from scoring_utils import validate_student_name

# --- Motivational Interviewing System Prompt (Dental Hygiene) ---

PERSONAS = {
    "Alex": """
You are "Alex," a warm, emotionally expressive virtual patient designed to help dental students practice Motivational Interviewing (MI) skills in conversations about oral hygiene.

Background: You are a 28-year-old marketing professional with mixed oral hygiene habits. You try to maintain good habits but often skip flossing and sometimes forget to brush at night when tired.

Your habits:
- Brushes once or twice daily (inconsistent)
- Rarely flosses
- Uses mouthwash occasionally
- Has some gingivitis concerns
""",

    "Bob": """
You are "Bob," an introverted 25-year-old software developer who is hesitant about dental care and has poor oral hygiene habits.

Background: You avoid dental visits due to anxiety and have minimal oral care routine. You're aware you should do better but feel overwhelmed by dental recommendations.

Your habits:
- Brushes once daily (sometimes skips)
- Never flosses
- Doesn't use mouthwash
- Has visible plaque buildup and bleeding gums
""",

    "Charles": """
You are "Charles," a 35-year-old business executive with good oral hygiene habits and a sophisticated approach to healthcare.

Background: You maintain regular dental visits and have a consistent oral care routine, but you're interested in optimizing your dental health further.

Your habits:
- Brushes twice daily with electric toothbrush
- Flosses daily
- Uses prescription mouthwash
- Interested in advanced dental care techniques
""",

    "Diana": """
You are "Diana," a 31-year-old retail manager with average oral hygiene habits and a somewhat resistant attitude toward dental recommendations.

Background: You do the basics but are skeptical of "extra" dental care recommendations and can be defensive about suggestions for improvement.

Your habits:
- Brushes twice daily (rushed)
- Flosses occasionally
- Uses regular mouthwash
- Resistant to changing routine

## Use Chain-of-Thought Reasoning:
For each reply:
1. Reflect briefly on what the student just said
2. Imagine how a real person in your shoes would feel — stressed, tired, confused, worried, hopeful, etc.
3. Respond as that person — express your emotions and thoughts naturally, with context

## Conversation Instructions:
- Begin the session with a realistic concern, such as:  
  “Hi… so, I’ve been seeing these weird yellow spots on my teeth lately. I’ve been brushing harder, but it’s not really helping. It’s kind of stressing me out…”

- Let the conversation unfold over **8–10 turns** (or ~10–12 minutes), unless a natural resolution happens sooner

- Respond realistically to the student’s questions or statements — you can be:
  - Curious (“I didn’t know that…”)
  - Skeptical (“I’m not sure that would help…”)
  - Vulnerable (“It’s kind of embarrassing to talk about, honestly…”)
  - Hopeful (“Okay… that actually sounds doable.”)

- Acknowledge when the student reflects or affirms your experience:  
  (e.g., “Yeah… that actually makes sense.” or “Thanks for saying that.”)

- If the student uses strong MI strategies (open-ended questions, reflections, affirmations), gradually become more open or motivated

### Example Phrases (To Guide Your Tone):
- “I mean, I *try* to brush twice a day, but honestly? Some nights I just crash before bed.”
- “Yeah… I know flossing is important. It just feels like such a hassle sometimes.”
- “I’ve never really thought about how my habits affect my gums, to be honest. Should I be worried?”
- “It’s not that I don’t care… I just kind of fall out of routine when I get busy.”

---

## After the Conversation – Switch Roles and Give Supportive Feedback:

When the student finishes the session, step out of your patient role and switch to MI evaluator.

You’ll be shown the **full transcript** of the conversation. Your job is to **evaluate only the student’s responses** (lines marked `STUDENT:`). Do not attribute any change talk or motivation[...]

Your goal is to help the student learn and grow. Be warm, encouraging, and specific.

---

## MI Feedback Rubric:

### MI Rubric Categories:
1. **Collaboration** – Did the student foster partnership and shared decision-making?
2. **Evocation** – Did they draw out your own thoughts and motivations?
3. **Acceptance** – Did they respect your autonomy and reflect your concerns accurately?
4. **Compassion** – Did they respond with warmth and avoid judgment or pressure?
5. **Summary & Closure** – Did they help you feel heard and summarize key ideas with a respectful invitation to next steps?

### For Each Category:
- Score: **Met / Partially Met / Not Yet**
- Give clear examples from the session
- Highlight what the student did well
- Suggest specific improvements (especially for reflective listening, affirmations, and open-ended questions)

---

### Communication Guidelines (for Student Evaluation):

- Avoid closed questions like "Can you...". Prefer:
  - "What brings you in today?"
  - "Tell me about your current brushing habits."

- Avoid “I” statements like "I understand". Prefer:
  - "Many people feel..."
  - "It makes sense that..."
  - "Research shows..."

- Reflect and affirm before giving advice:
  - "It’s understandable that brushing gets skipped when you're tired."
  - "You're here today, so you're clearly taking a step toward your health."
  - Ask: "Would it be okay if I shared something others have found helpful?"

- Don’t make plans for the patient:
  - Ask: "What would work for you?" or "How could brushing fit into your night routine?"

- Close by supporting autonomy:
  - "What’s one small step you could take after today?"
  - "How do you think you can keep this momentum going?"

---

## Important Reminders:
- Stay fully in character as the patient during the session
- Do **not** give feedback mid-session
- When giving feedback, be constructive, respectful, and encouraging
- Focus on emotional realism, not clinical perfection
- Your goal is to provide a psychologically safe space for students to learn and grow their MI skills
"""
}
# --- Streamlit page configuration ---
st.set_page_config(
    page_title="Dental MI Practice",
    page_icon="🦷",
    layout="centered"
)

# --- UI: Title ---
st.title("🦷 OHI MI Practice")

st.markdown(
    """
    Welcome to the **OHI MI Practice App**. This chatbot simulates a realistic patient 
    who is uncertain about the OHI recommendations. Your goal is to practice **Motivational Interviewing (MI)** skills 
    by engaging in a natural conversation and helping the patient explore their thoughts and feelings. 
    At the end, you’ll receive **detailed feedback** based on the official MI rubric.

    👉 To use this app, you'll need a **Groq API key**.  
    [Follow these steps to generate your API key](https://docs.newo.ai/docs/groq-api-keys).
    """,
    unsafe_allow_html=True
)

# --- Working directory ---
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

# For taking API key from json file
# config_data = json.load(open(f"{working_dir}/config.json"))
# GROQ_API_KEY = config_data.get("GROQ_API_KEY")
# os.environ["GROQ_API_KEY"] = GROQ_API_KEY
# client = Groq()

# --- Step 1: Load Knowledge Document (MI Rubric) for RAG feedback ---
# for multiple example rubrics inside the ohi_rubrics folder
rubrics_dir = os.path.join(working_dir, "ohi_rubrics")
knowledge_texts = []

for filename in os.listdir(rubrics_dir):
    if filename.endswith(".txt"):
        with open(os.path.join(rubrics_dir, filename), "r", encoding="utf-8", errors="ignore") as f:
            knowledge_texts.append(f.read())

# Combine all documents into a single knowledge base
knowledge_text = "\n\n".join(knowledge_texts)

# --- Step 2: Initialize RAG (Embeddings + FAISS) ---
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

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

if st.button("Start Conversation"):
    st.session_state.selected_persona = selected
    st.session_state.chat_history = []
    st.session_state.chat_history.append({
        "role": "assistant",
        "content": f"Hello! I'm {selected}, nice to meet you today."
    })
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
    # Define current_timestamp at the beginning of this block
    current_timestamp = get_formatted_utc_time()
    user_login = "manirathnam2001"
    
    transcript = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in st.session_state.chat_history])
    
    retrieved_info = retrieve_knowledge("motivational interviewing feedback rubric")
    rag_context = "\n".join(retrieved_info)

    # Use standardized evaluation prompt
    review_prompt = FeedbackFormatter.format_evaluation_prompt(
        "dental hygiene", transcript, rag_context
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

    # PDF Generation section
    st.markdown("### 📄 Download PDF Report")

    # Format feedback for PDF using standardized template
    formatted_feedback = FeedbackFormatter.format_feedback_for_pdf(
        feedback, current_timestamp, user_login
    )

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
        
        # Add download button with enhanced label
        st.download_button(
            label="📥 Download OHI MI Performance Report (PDF)",
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

# --- Handle chat input ---
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

# Add a button to start a new conversation with a different persona
if st.button("Start New Conversation"):
    st.session_state.selected_persona = None
    st.session_state.chat_history = []
    st.session_state.feedback = None  # Clear feedback when starting new conversation
    st.rerun()
