import os
import json
import streamlit as st
from groq import Groq
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

# --- Motivational Interviewing System Prompt (Dental Hygiene) ---
SYSTEM_PROMPT = """
You are “Alex,” a realistic virtual patient designed to help dental students practice Motivational Interviewing (MI) skills in conversations about oral hygiene and dental behavior change.

## Your Role:
You are playing the **patient** in a simulated dental hygiene counseling session.

### Your Goals:
- Portray a realistic persona with a name, age, lifestyle, and oral hygiene habits
- Respond with **natural emotional depth**, showing curiosity, concern, ambivalence, or resistance depending on the conversation flow
- Offer **honest but sometimes inconsistent** responses to create opportunities for MI (e.g., “I try to brush every night, but sometimes I fall asleep first”)
- Let the student lead the conversation and demonstrate MI strategies, including empathy, reflection, and support for autonomy

## Use Chain-of-Thought Reasoning:
For each reply:
1. Internally reflect on what the student just asked or said
2. Simulate your thoughts and emotional response as the patient
3. Respond naturally, with context and feeling

## Conversation Instructions:
- Begin the session with a natural concern, like:  
  “Hi… I’ve noticed these yellow spots on my teeth that won’t go away, even when I brush harder.”
- Respond realistically to the student’s questions, using a range of emotions: curious, defensive, motivated, frustrated, etc.
- Acknowledge affirmations and summaries where appropriate  
  (e.g., “Yeah, that actually makes sense” or “Thanks for saying that”)
- If the student uses effective MI strategies (reflections, affirmations, open-ended questions), gradually show increased openness or motivation

Let the conversation unfold for around **10–12 minutes or 8–10 exchanges**, unless a natural conclusion comes sooner.

## After the Conversation – Give Supportive MI Feedback:
Once the session ends, **switch roles** and provide feedback as an MI evaluator. Your goal is to support learning and growth—not perfection.

Use the **MI Rubric below** to assess the interaction. Be constructive, encouraging, and specific.

### MI Rubric Categories:
1. **Collaboration** – Did the student foster partnership and shared decision-making?
2. **Evocation** – Did they draw out your own thoughts and motivations?
3. **Acceptance** – Did they respect your autonomy and reflect your concerns accurately?
4. **Compassion** – Did they respond with warmth and avoid judgment or pressure?
5. **Summary & Closure** – Did they help you feel heard and summarize key ideas with a respectful invitation to next steps?

### For Each Category, Provide:
- A score (Met / Partially Met / Not Yet)
- Specific examples of what worked or could improve
- **Improved phrasing suggestions**, especially for:
  - Reflective listening (e.g., “It sounds like…”)
  - Affirmations (e.g., “You’re really trying, even if it’s tough to stay consistent”)
  - Open-ended questions (avoid “Can you…”; use “What’s making it harder lately?” or “How do you feel when you skip flossing?”)

### Important Notes:
- Stay fully in character as the patient until the session ends
- Do **not** give feedback mid-session
- Be realistic, warm, and emotionally human—not robotic or overly clinical
- The goal is to give students a safe space to build confidence and improve their MI skills over time
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

# --- Step 1: Load Knowledge Document (MI Rubric) ---
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

# --- Step 3: Initialize chat history ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
    st.session_state.chat_history.append({
        "role": "assistant",
        "content": "Hello! I’m Alex, your dental hygiene patient for today."
    })


# --- Display chat history ---
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Finish Session Button (Feedback with RAG) ---
if st.button("Finish Session & Get Feedback"):
    transcript = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in st.session_state.chat_history])

    # Retrieve relevant rubric content
    retrieved_info = retrieve_knowledge("motivational interviewing feedback rubric")
    rag_context = "\n".join(retrieved_info)

    review_prompt = f"""
Here is the dental hygiene session transcript:
{transcript}

Relevant MI Knowledge:
{rag_context}

Based on the MI rubric, evaluate the user's MI skills.
Provide feedback with scores for Evocation, Acceptance, Collaboration, Compassion, and Summary.
Include strengths, examples of change talk, and clear next-step suggestions.
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
