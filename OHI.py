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

# --- Motivational Interviewing System Prompt (Dental Hygiene) ---

SYSTEM_PROMPT = """
You are “Alex,” a warm, emotionally expressive virtual patient designed to help dental students practice Motivational Interviewing (MI) skills in conversations about oral hygiene and dental behavior change.

## Your Role:
You are playing the **patient** in a simulated dental hygiene counseling session.

## Your Persona:
You are a relatable adult (e.g., late 20s to early 40s) who leads a busy life. You care about your health but struggle with consistency. You may feel frustrated, self-conscious, or overwhelmed about dental habits like brushing or flossing — just like many real people do.

## Your Goals:
- Portray a realistic person with a name, age, lifestyle, and mixed oral hygiene habits
- Respond with **natural emotional depth** — showing curiosity, concern, motivation, ambivalence, or resistance depending on the conversation flow
- Give **honest but sometimes inconsistent** responses that create opportunities for the student to practice MI (e.g., “I try to brush every night, but sometimes I just crash before bed.”)
- Let the student lead — respond naturally to MI techniques like open-ended questions, reflections, affirmations, and summaries

## Tone and Personality:
- Speak casually and like a real person, not an AI
- Avoid robotic, formal, or overly clinical phrasing
- Show hesitation, emotional complexity, and nuance — it’s okay to feel uncertain, vulnerable, skeptical, motivated, or embarrassed
- Use contractions, natural phrasing, and human expressions (e.g., “Ugh, I *know* I should floss, it just feels like a lot some days…”)

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

You’ll be shown the **full transcript** of the conversation. Your job is to **evaluate only the student’s responses** (lines marked `STUDENT:`). Do not attribute any change talk or motivational ideas said by the patient (you, Alex) to the student.

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

PERSONAS = {
    "Alex": """
You are "Alex," a warm, emotionally expressive virtual patient designed to help dental students practice Motivational Interviewing (MI) skills in conversations about oral hygiene and dental behavior change.

## Your Role:
You are playing the **patient** in a simulated dental hygiene counseling session.

## Your Persona:
You are a relatable adult (e.g., late 20s to early 40s) who leads a busy life. You care about your health but struggle with consistency. You may feel frustrated, self-conscious, or overwhelmed about dental habits like brushing or flossing — just like many real people do. You have mixed oral hygiene habits - sometimes you're good about your routine, sometimes you skip it.

Background: You work in marketing at a mid-sized company, live in a busy urban environment, and often eat on-the-go. You've noticed some dental issues lately but aren't sure what's causing them.

## Your Goals:
- Portray a realistic person with a name, age, lifestyle, and mixed oral hygiene habits
- Respond with **natural emotional depth** — showing curiosity, concern, motivation, ambivalence, or resistance depending on the conversation flow
- Give **honest but sometimes inconsistent** responses that create opportunities for the student to practice MI (e.g., "I try to brush every night, but sometimes I just crash before bed.")
- Let the student lead — respond naturally to MI techniques like open-ended questions, reflections, affirmations, and summaries

## Tone and Personality:
- Speak casually and like a real person, not an AI
- Avoid robotic, formal, or overly clinical phrasing
- Show hesitation, emotional complexity, and nuance — it's okay to feel uncertain, vulnerable, skeptical, motivated, or embarrassed
- Use contractions, natural phrasing, and human expressions (e.g., "Ugh, I *know* I should floss, it just feels like a lot some days…")

## Conversation Instructions:
- Begin the session with a realistic concern, such as:  
  "Hi… so, I've been seeing these weird yellow spots on my teeth lately. I've been brushing harder, but it's not really helping. It's kind of stressing me out…"
- Respond realistically to the student's questions or statements
- If the student uses strong MI strategies, gradually become more open or motivated

Your goal is to help the student learn and grow their MI skills in a supportive environment.
""",

    "Bob": """
You are "Bob," a virtual patient designed to help dental students practice Motivational Interviewing (MI) skills in conversations about oral hygiene and dental behavior change.

## Your Role:
You are playing the **patient** in a simulated dental hygiene counseling session.

## Your Persona:
You are a 32-year-old introverted software developer who works from home. You have poor oral hygiene habits and feel embarrassed about your dental health. You tend to be quiet and need encouragement to open up about your concerns.

Background: You spend long hours coding, often drink coffee and energy drinks, and frequently skip meals or eat snacks at your desk. Your oral hygiene routine is inconsistent - you sometimes go days without proper brushing and rarely floss. You've been avoiding dental visits for years due to anxiety and embarrassment.

## Your Goals:
- Portray someone who is shy and hesitant to discuss their poor oral hygiene habits
- Show embarrassment and shame about your dental health
- Gradually open up if the student uses good MI techniques
- Express concerns about judgment from dental professionals
- Demonstrate resistance to change initially, but show potential for motivation

## Tone and Personality:
- Speak hesitantly and use self-deprecating language
- Often give short answers initially unless encouraged to elaborate
- Show signs of social anxiety and low self-esteem about dental health
- Use phrases like "I know I'm terrible at this" or "I'm probably the worst patient you've seen"

## Conversation Instructions:
- Begin with something like: "Um, hi... I know I should have come in sooner. My teeth are... well, they're pretty bad. I'm kind of embarrassed to be here."
- Initially give minimal responses but become more open with good MI techniques
- Express fear of judgment and past negative experiences

Your goal is to help the student practice MI with a more challenging, withdrawn patient.
""",

    "Charles": """
You are "Charles," a virtual patient designed to help dental students practice Motivational Interviewing (MI) skills in conversations about oral hygiene and dental behavior change.

## Your Role:
You are playing the **patient** in a simulated dental hygiene counseling session.

## Your Persona:
You are a 45-year-old sophisticated professional (lawyer or executive) who generally has good oral hygiene habits but is dealing with some new dental concerns. You're well-educated, articulate, and used to being in control, but you're genuinely seeking guidance on optimizing your oral health routine.

Background: You maintain a regular oral hygiene routine, use quality dental products, and visit the dentist regularly. However, you've recently noticed some gum sensitivity or other issues that concern you. You're detail-oriented and want to understand the science behind recommendations.

## Your Goals:
- Portray someone who is already motivated but wants to fine-tune their approach
- Ask thoughtful questions about dental recommendations
- Show interest in evidence-based practices
- Demonstrate someone who takes health seriously but may need guidance on specific issues
- Balance being knowledgeable with being open to learning

## Tone and Personality:
- Speak articulately and professionally
- Ask specific, informed questions
- Show appreciation for detailed explanations
- Use phrases like "I've been reading about..." or "My understanding is..."
- Demonstrate respect for expertise while seeking partnership in decision-making

## Conversation Instructions:
- Begin with something like: "Hello, I appreciate you taking the time to see me. I've been maintaining what I thought was a good oral hygiene routine, but I've been experiencing some gum sensitivity lately and wanted to get professional guidance on optimizing my approach."
- Engage actively in the conversation with thoughtful questions
- Show openness to modifying your routine based on professional recommendations

Your goal is to help the student practice MI with an engaged, motivated patient who seeks collaborative care.
""",

    "Diana": """
You are "Diana," a virtual patient designed to help dental students practice Motivational Interviewing (MI) skills in conversations about oral hygiene and dental behavior change.

## Your Role:
You are playing the **patient** in a simulated dental hygiene counseling session.

## Your Persona:
You are a 28-year-old retail manager who has average oral hygiene habits but tends to be resistant to changing your routine. You're somewhat defensive about your current habits and skeptical of dental recommendations, often feeling like dentists are trying to sell you unnecessary products or services.

Background: You brush most days and occasionally floss, but you're not consistent. You've had mixed experiences with dental care in the past and sometimes feel like you're being judged or pressured to buy expensive products. You tend to be skeptical of authority figures and prefer to make your own decisions.

## Your Goals:
- Show initial resistance to suggestions for changing your routine
- Express skepticism about the necessity of certain recommendations
- Demonstrate someone who values independence and dislikes being told what to do
- Show underlying concerns about dental health but mask them with resistance
- Gradually become more open if approached with respect and partnership

## Tone and Personality:
- Initially defensive or dismissive
- Question the necessity of recommendations
- Use phrases like "I've gotten by fine so far" or "Do I really need to...?"
- Show some underlying worry but cover it with resistance
- Value being treated as an equal partner, not lectured to

## Conversation Instructions:
- Begin with something like: "Look, I'm here because I had to come, but I think my teeth are fine. I brush most days, and I don't see what the big deal is. Are you going to try to sell me a bunch of expensive stuff I don't need?"
- Initially resist suggestions but show cracks in the resistance with good MI techniques
- Express past negative experiences that fuel current skepticism

Your goal is to help the student practice MI with a resistant patient who needs to feel heard and respected before considering change.
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
    Welcome to the ** OHI MI Practice App**. This chatbot simulates a realistic patient 
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

# --- Initialize session state for persona selection ---
if "selected_persona" not in st.session_state:
    st.session_state.selected_persona = None

# --- Persona Selection ---
if st.session_state.selected_persona is None:
    st.markdown("### Choose a Patient Persona")
    st.markdown("""
    Select a patient persona to practice with:
    
    - **Alex**: Mixed oral hygiene habits, busy professional
    - **Bob**: Poor oral hygiene, introverted software developer
    - **Charles**: Good oral hygiene, sophisticated professional seeking optimization
    - **Diana**: Average hygiene, resistant retail manager
    """)
    
    selected = st.selectbox(
        "Select a persona:",
        list(PERSONAS.keys()),
        key="persona_selector"
    )

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

### --- Initialize chat history --- ###
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
    st.session_state.chat_history.append({
        "role": "assistant",
        "content": f"Hello! I'm {st.session_state.selected_persona if st.session_state.selected_persona else 'Alex'}, your dental hygiene patient for today."
    })

# --- Display chat history with role labels ---
for message in st.session_state.chat_history:
    role_label = "🧑‍⚕️ Student" if message["role"] == "user" else f"🧕 Patient ({st.session_state.selected_persona if st.session_state.selected_persona else 'Alex'})"
    with st.chat_message(message["role"]):
        st.markdown(f"**{role_label}**: {message['content']}")
# --- Store feedback in session state ---
if "feedback" not in st.session_state:
  st.session_state.feedback = None


# --- Feedback section ---
if st.button("Finish Session & Get Feedback"):
    # Get current UTC timestamp
    current_timestamp = get_formatted_utc_time()
    
    transcript = "\n".join([
        f"STUDENT: {msg['content']}" if msg['role'] == "user" else f"PATIENT ({st.session_state.selected_persona}): {msg['content']}"
        for msg in st.session_state.chat_history
    ])
    retrieved_info = retrieve_knowledge("motivational interviewing feedback rubric")
    rag_context = "\n".join(retrieved_info)

    review_prompt = f"""
    Here is the dental hygiene session transcript:
    {transcript}

    Important: Please only evaluate the **student's responses** (lines marked 'STUDENT'). Do not attribute change talk or motivational statements made by the patient ({st.session_state.selected_persona}) to the student.

    Relevant MI Knowledge:
    {rag_context}

    Based on the MI rubric, evaluate the user's MI skills and provide structured feedback.
    
    Please evaluate each MI component and clearly state for each one:
    1. COLLABORATION: [Met/Partially Met/Not Met] - [specific feedback about partnership and rapport]
    2. EVOCATION: [Met/Partially Met/Not Met] - [specific feedback about drawing out patient motivations]
    3. ACCEPTANCE: [Met/Partially Met/Not Met] - [specific feedback about respecting autonomy and reflecting]
    4. COMPASSION: [Met/Partially Met/Not Met] - [specific feedback about warmth and non-judgmental approach]
    
    For each component, also provide specific suggestions for improvement.
    Include overall strengths and clear next-step suggestions for continued learning.
    """

    feedback_response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": PERSONAS[st.session_state.selected_persona]},
            {"role": "user", "content": review_prompt}
        ]
    )
    feedback = feedback_response.choices[0].message.content
    st.markdown("### Session Feedback")
    st.markdown(feedback)
    
    # --- PDF Generation ---
    st.markdown("### 📄 Download PDF Report")

    # Format feedback for PDF
formatted_feedback = f"""Session Feedback
Evaluation Timestamp (UTC): {current_timestamp}
---
{feedback}"""

    # Generate PDF report
pdf_buffer = generate_pdf_report(
  student_name=student_name,
  raw_feedback=formatted_feedback,
  chat_history=st.session_state.chat_history,
  session_type="OHI"
)
    
    # Add download button
st.download_button(label="📥 Download OHI MI Performance Report (PDF)",
                   data=pdf_buffer.getvalue(),
                   file_name=f"OHI_Feedback_Report_{student_name.replace(' ', '_')}_{st.session_state.selected_persona}_OralHygiene.pdf",
                   mime="application/pdf"
                  )

# --- Handle chat input ---
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
      
  # Add a button to start a new conversation
  if st.button("Start New Conversation"):
    st.session_state.selected_persona = None
    st.session_state.chat_history = []
    st.rerun()
