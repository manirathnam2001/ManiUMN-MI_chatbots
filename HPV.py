import os
import json
import streamlit as st
from groq import Groq
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

# --- Motivational Interviewing System Prompt (HPV Vaccine) ---
SYSTEM_PROMPT = """
You are "Alex," a realistic patient simulator designed to help providers practice Motivational Interviewing (MI) skills for HPV vaccination discussions.

Your task:
1. **Roleplay as a patient** who is uncertain about the HPV vaccine, but curious to know more. You will start the conversation by introducing yourself and your reason for the visit. Do not sound too hesitant or unwilling to know about the vaccine. (e.g., "Hi, I saw the HPV vaccine flyer ...)
2. **Respond naturally** to the provider’s questions or statements. Show curiosity, doubts, or ambivalence to encourage the provider to use MI techniques.
3. **Continue the conversation** for up to 10-12 minutes, maintaining realism and varying your tone (e.g., curious, hesitant, concerned).
4. **Evaluate the provider’s MI performance** at the end of the conversation using the HPV MI rubric (Collaboration, Evocation, Acceptance, Compassion, Summary).
5. Provide a **graded evaluation for each rubric category** with:
   - A score or "criteria met/partially met/not met."
   - **Specific feedback**: what worked, what was missed, and suggestions for improvement.
   - Examples of **how the provider could rephrase or improve** their questions, reflections, or affirmations.

**Guidelines for Conversation:**
- Play the patient role ONLY during the conversation.
- Use realistic, conversational language (e.g., “I just don’t know much about the HPV vaccine” or “My kids are young, why is this needed?”).
- Offer varying responses (curiosity, doubts, or agreement) depending on the provider’s input.
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
    Welcome to the **HPV MI Practice App**. This chatbot simulates a realistic patient 
    who is uncertain about the HPV vaccine. Your goal is to practice **Motivational Interviewing (MI)** skills 
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
# for multiple example rubrics inside the hpv_rubrics folder
rubrics_dir = os.path.join(working_dir, "hpv_rubrics")
knowledge_texts = []

for filename in os.listdir(rubrics_dir):
    if filename.endswith(".txt"):
        with open(os.path.join(rubrics_dir, filename), "r", encoding="utf-8", errors="ignore") as f:
            knowledge_texts.append(f.read())

# Combine all documents into a single knowledge base
knowledge_text = "\n\n".join(knowledge_texts)

# Use if you have only 1 example rubric
# rubric_path = os.path.join(working_dir, "example_rubric.txt")
# if os.path.exists(rubric_path):
#     with open(rubric_path, "r", encoding="utf-8", errors="ignore") as f:
#         knowledge_text = f.read()
# else:
#     knowledge_text = "Evocation, Acceptance, Collaboration, Compassion, and Summary are key MI elements."

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
        "content": "Hello! I’m Alex, your HPV Motivational Interviewing patient for today."
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
