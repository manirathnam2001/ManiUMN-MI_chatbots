import os
import json
import streamlit as st
from groq import Groq
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from datetime import datetime

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

# --- Warn and stop if key not provided ---
if not api_key:
    st.warning("Please enter your GROQ API key above to continue.")
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
        "content": "Hello! I’m Alex, your dental hygiene patient for today."
    })

# --- Display chat history with role labels ---
for message in st.session_state.chat_history:
    role_label = "🧑‍⚕️ Student" if message["role"] == "user" else "🧕 Patient (Alex)"
    with st.chat_message(message["role"]):
        st.markdown(f"**{role_label}**: {message['content']}")

# --- Feedback section ---
if st.button("Finish Session & Get Feedback"):
    transcript = "\n".join([
        f"STUDENT: {msg['content']}" if msg['role'] == "user" else f"PATIENT (Alex): {msg['content']}"
        for msg in st.session_state.chat_history
    ])
    retrieved_info = retrieve_knowledge("motivational interviewing feedback rubric")
    rag_context = "\n".join(retrieved_info)

    review_prompt = f"""
    Here is the dental hygiene session transcript:
    {transcript}

    Important: Please only evaluate the **student's responses** (lines marked 'STUDENT'). Do not attribute change talk or motivational statements made by the patient (Alex) to the student.

    Relevant MI Knowledge:
    {rag_context}

    Based on the MI rubric, evaluate the user's MI skills.
    Provide feedback with scores for Evocation, Acceptance, Collaboration, Compassion, and Summary.
    Include strengths, example questions, and clear next-step suggestions.
    """

    feedback_response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": review_prompt}
        ]
    )
    feedback = feedback_response.choices[0].message.content
    st.markdown("### Session Feedback")
    st.markdown(feedback)

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
        {"role": "system", "content": SYSTEM_PROMPT},
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
