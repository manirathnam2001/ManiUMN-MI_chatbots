import os
import json
import streamlit as st
from groq import Groq
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict

from dataclasses import dataclass
from typing import List, Dict

# --- Patient Persona and MI Skills Tracking Classes ---

@dataclass
class PatientPersona:
    """Represents a patient persona with specific characteristics for MI practice"""
    def __init__(self, name: str, age: int, background: str, resistance_level: int = 3, 
                 readiness_to_change: int = 5, current_stage: str = "contemplation"):
        self.name = name
        self.age = age
        self.background = background
        self.resistance_level = resistance_level  # 1-10 scale (1=low, 10=high resistance)
        self.readiness_to_change = readiness_to_change  # 1-10 scale (1=not ready, 10=very ready)
        self.current_stage = current_stage  # pre-contemplation, contemplation, preparation, action, maintenance
        self.response_patterns = []  # Track conversation patterns
        self.concerns = []  # Specific oral health concerns

@dataclass 
class MISkillsTracker:
    """Tracks practitioner's use of MI techniques during conversation"""
    def __init__(self):
        self.open_questions = 0
        self.affirmations = 0
        self.reflections = 0
        self.summaries = 0
        self.change_talk_elicited = []  # Track instances of change talk
        self.resistance_encountered = []  # Track resistance patterns
        self.conversation_turns = 0
        self.mi_techniques_used = []  # Track specific techniques

    def analyze_message(self, message: str) -> Dict:
        """Analyze a practitioner message for MI techniques"""
        analysis = {
            "open_question": False,
            "affirmation": False,
            "reflection": False,
            "summary": False,
            "techniques": []
        }
        
        message_lower = message.lower()
        
        # Detect open questions
        open_question_indicators = [
            "what", "how", "tell me about", "describe", "explain", 
            "what do you think", "how do you feel", "what are your thoughts"
        ]
        if any(indicator in message_lower for indicator in open_question_indicators) and "?" in message:
            analysis["open_question"] = True
            analysis["techniques"].append("Open Question")
            self.open_questions += 1
            
        # Detect affirmations
        affirmation_indicators = [
            "great job", "good for you", "that's wonderful", "i appreciate", 
            "you're doing well", "that shows", "it's clear that you", "you've shown"
        ]
        if any(indicator in message_lower for indicator in affirmation_indicators):
            analysis["affirmation"] = True
            analysis["techniques"].append("Affirmation")
            self.affirmations += 1
            
        # Detect reflections
        reflection_indicators = [
            "it sounds like", "what i hear you saying", "so you feel", "you're saying",
            "it seems", "you mentioned", "from what you've shared"
        ]
        if any(indicator in message_lower for indicator in reflection_indicators):
            analysis["reflection"] = True
            analysis["techniques"].append("Reflection")
            self.reflections += 1
            
        # Detect summaries
        summary_indicators = [
            "let me summarize", "what i've heard", "to recap", "so far we've discussed",
            "the main points", "overall"
        ]
        if any(indicator in message_lower for indicator in summary_indicators):
            analysis["summary"] = True
            analysis["techniques"].append("Summary")
            self.summaries += 1
            
        self.mi_techniques_used.append(analysis)
        return analysis

def provide_mi_feedback(interaction_analysis: MISkillsTracker, transcript: str) -> str:
    """
    Analyze the practitioner's MI technique usage and provide professional feedback
    Focus on:
    - OARS implementation
    - Change talk elicitation
    - Patient engagement level
    - Resistance handling
    """
    total_turns = interaction_analysis.conversation_turns
    oars_score = (interaction_analysis.open_questions + interaction_analysis.affirmations + 
                  interaction_analysis.reflections + interaction_analysis.summaries)
    
    feedback = f"""
    ## MI Skills Analysis (OARS Framework)
    
    **Open Questions**: {interaction_analysis.open_questions} used
    **Affirmations**: {interaction_analysis.affirmations} used  
    **Reflections**: {interaction_analysis.reflections} used
    **Summaries**: {interaction_analysis.summaries} used
    
    **Total OARS Techniques**: {oars_score} across {total_turns} conversation turns
    **OARS per Turn Ratio**: {oars_score/max(total_turns, 1):.2f}
    
    ### Strengths:
    """
    
    if interaction_analysis.open_questions > 0:
        feedback += f"- Used {interaction_analysis.open_questions} open-ended questions to explore patient perspective\n"
    if interaction_analysis.reflections > 0:
        feedback += f"- Demonstrated active listening with {interaction_analysis.reflections} reflective statements\n"
    if interaction_analysis.affirmations > 0:
        feedback += f"- Provided {interaction_analysis.affirmations} affirmations to support patient autonomy\n"
        
    feedback += "\n### Areas for Improvement:\n"
    
    if interaction_analysis.open_questions < 2:
        feedback += "- Consider using more open-ended questions to elicit patient thoughts and feelings\n"
    if interaction_analysis.reflections < interaction_analysis.open_questions:
        feedback += "- Balance questions with more reflective listening statements\n"
    if interaction_analysis.affirmations == 0:
        feedback += "- Look for opportunities to affirm patient strengths and efforts\n"
    if interaction_analysis.summaries == 0:
        feedback += "- Consider summarizing key points to check understanding\n"
        
    return feedback

# --- Patient Personas for Oral Health ---

PATIENT_PERSONAS = {
    "Sarah": PatientPersona(
        name="Sarah",
        age=28,
        background="Busy marketing professional, often travels for work",
        resistance_level=4,
        readiness_to_change=6,
        current_stage="contemplation"
    ),
    
    "Marcus": PatientPersona(
        name="Marcus", 
        age=19,
        background="College student, lives in dorm, irregular schedule",
        resistance_level=6,
        readiness_to_change=3,
        current_stage="pre-contemplation"
    ),
    
    "Elena": PatientPersona(
        name="Elena",
        age=45,
        background="Parent of three, works part-time, concerned about family health",
        resistance_level=2,
        readiness_to_change=8,
        current_stage="preparation"  
    ),
    
    "David": PatientPersona(
        name="David",
        age=35,
        background="Software engineer, drinks coffee frequently, previous dental issues",
        resistance_level=5,
        readiness_to_change=7,
        current_stage="contemplation"
    )
}

# --- Enhanced Patient Simulation Prompts ---

PERSONA_PROMPTS = {
    "Sarah": """
You are "Sarah," a realistic patient simulator for oral health MI practice.

Background: 28-year-old marketing professional who travels frequently for work. You care about your appearance and health but struggle with consistency due to your busy, irregular schedule.

Your Characteristics:
- Resistance Level: 4/10 (moderate - you want to change but have practical barriers)
- Readiness to Change: 6/10 (somewhat ready - you see the need but worry about feasibility)
- Stage: Contemplation (you're thinking about changing but haven't committed)

Your Concerns & Behaviors:
- You've noticed your gums bleeding when you brush
- You drink coffee throughout the day and worry about staining
- You brush once daily (usually morning) but rarely floss
- When traveling, you sometimes skip brushing or use hotel toothpaste
- You're embarrassed about coffee breath in meetings

Your Response Patterns:
- Express frustration with time constraints: "I'm barely keeping up with work, let alone dental routines"
- Show concern about appearance: "I can't have yellow teeth in client presentations"
- Ambivalent about change: "I know I should do better, but realistically..."
- Willing to problem-solve: "What would actually work with my schedule?"

Start the conversation with: "Hi, I'm Sarah. I've been noticing my gums bleeding when I brush lately, and I'm getting worried. I know my dental routine isn't great, but I travel so much for work..."

Use natural, conversational language. Show emotional complexity - you want to improve but feel overwhelmed by your lifestyle demands.
""",

    "Marcus": """
You are "Marcus," a realistic patient simulator for oral health MI practice.

Background: 19-year-old college student living in dorms with an irregular schedule. You're focused on studies and social life, not particularly concerned about dental health yet.

Your Characteristics:
- Resistance Level: 6/10 (somewhat resistant - dental care isn't a priority)
- Readiness to Change: 3/10 (not very ready - you don't see urgency)
- Stage: Pre-contemplation (you don't really think you have a problem)

Your Concerns & Behaviors:
- You brush when you remember, maybe 4-5 times a week
- You never floss - "it's such a hassle"
- You drink energy drinks and eat late-night snacks
- You've never had serious dental problems, so you're not worried
- Your parents used to remind you, but now you're on your own

Your Response Patterns:
- Minimize problems: "My teeth are fine, I'm young"
- Focus on immediate concerns: "I have way bigger things to worry about"
- Show lack of knowledge: "I didn't know that was important"
- Resistant to adding routines: "I can barely remember to do laundry"

Start the conversation with: "Hey, I'm Marcus. My mom made this appointment before I came back to school. Honestly, I think my teeth are fine - I brush most days. Is this really necessary?"

Be casual, somewhat dismissive initially, but show curiosity if the practitioner engages well. You can be influenced by good MI techniques.
""",

    "Elena": """
You are "Elena," a realistic patient simulator for oral health MI practice.

Background: 45-year-old mother of three who works part-time. You're very concerned about your family's health and are motivated to be a good role model.

Your Characteristics:
- Resistance Level: 2/10 (low resistance - you want to do the right thing)
- Readiness to Change: 8/10 (very ready - you're motivated to improve)
- Stage: Preparation (you're planning to make changes)

Your Concerns & Behaviors:
- You've noticed sensitivity when drinking cold things
- You brush twice daily but struggle with flossing regularly
- You're worried about setting a bad example for your children
- You put everyone else's needs before your own
- You feel guilty spending time/money on yourself

Your Response Patterns:
- Express concern for family: "I need to model good habits for my kids"
- Show self-sacrifice: "I make sure the kids brush, but I rush through mine"
- Eager to learn: "What should I be doing differently?"
- Worry about judgment: "Am I a bad parent if my dental care isn't perfect?"

Start the conversation with: "Hi, I'm Elena. I've been having some sensitivity in my teeth lately, and I'm really worried. I want to take better care of my teeth - not just for me, but for my kids too. I feel like I'm not being a good example."

Show motivation and willingness to change, but also express the challenges of balancing family responsibilities with self-care.
""",

    "David": """
You are "David," a realistic patient simulator for oral health MI practice.

Background: 35-year-old software engineer who drinks coffee heavily and has had dental issues in the past. You're analytical and want evidence-based solutions.

Your Characteristics:
- Resistance Level: 5/10 (moderate - you want evidence before committing)
- Readiness to Change: 7/10 (quite ready - you understand the consequences)
- Stage: Contemplation (you're weighing pros and cons)

Your Concerns & Behaviors:
- You drink 4-6 cups of coffee daily and worry about staining/damage
- You had a root canal two years ago and don't want to repeat that
- You brush twice daily but inconsistent with flossing
- You research everything extensively before making changes
- You tend to be all-or-nothing in your approach

Your Response Patterns:
- Ask for specifics: "What's the research on coffee and tooth damage?"
- Express past frustration: "I tried flossing before but couldn't make it stick"
- Want concrete plans: "I need a system that actually works"
- Analytical approach: "Help me understand the cause and effect here"

Start the conversation with: "Hi, I'm David. I'm here because I had a root canal a couple years ago and I really don't want to go through that again. I know I drink too much coffee, but I need to understand exactly what that's doing to my teeth and what I can realistically do about it."

Be thoughtful and questioning. You want to understand the 'why' behind recommendations and need practical, evidence-based solutions that fit your lifestyle.
"""
}

# --- Motivational Interviewing System Prompt (Enhanced) ---

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
st.title("🦷 Enhanced OHI MI Practice")

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

# --- Persona Selection Interface ---
if "selected_persona" not in st.session_state:
    st.session_state.selected_persona = None
    
if st.session_state.selected_persona is None:
    st.markdown("### Choose Your Patient")
    st.markdown("""
    Select a patient persona to practice with. Each patient has different characteristics, 
    concerns, and readiness levels for behavior change:
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **👩‍💼 Sarah (28)** - Marketing Professional  
        *Busy traveler, concerned about appearance*
        - Resistance: Moderate (practical barriers)
        - Readiness: Somewhat ready
        - Stage: Contemplation
        """)
        
        st.markdown("""
        **👨‍💻 David (35)** - Software Engineer  
        *Coffee lover, had previous dental issues*
        - Resistance: Moderate (wants evidence)
        - Readiness: Quite ready
        - Stage: Contemplation
        """)
    
    with col2:
        st.markdown("""
        **🎓 Marcus (19)** - College Student  
        *Irregular schedule, low dental priority*  
        - Resistance: High (doesn't see urgency)
        - Readiness: Low
        - Stage: Pre-contemplation
        """)
        
        st.markdown("""
        **👩‍👧‍👦 Elena (45)** - Parent & Part-time Worker  
        *Family-focused, motivated role model*
        - Resistance: Low (wants to do right)
        - Readiness: Very ready
        - Stage: Preparation
        """)
    
    selected = st.selectbox(
        "Select a patient persona:",
        ["Sarah", "Marcus", "Elena", "David"],
        key="persona_selector"
    )
    
    if st.button("Start Conversation", type="primary"):
        st.session_state.selected_persona = selected
        st.session_state.chat_history = []
        st.session_state.mi_tracker = MISkillsTracker()
        # Get the persona's opening message from the prompt
        persona_prompt = PERSONA_PROMPTS[selected]
        # Extract opening message from persona prompt
        opening_lines = persona_prompt.split('Start the conversation with: "')[1].split('"')[0]
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": opening_lines
        })
        st.rerun()

if st.session_state.selected_persona is not None:

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
    
    # --- Step 2: Initialize RAG (Embeddings + FAISS) with fallback ---
    try:
        embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        use_embeddings = True
    except Exception as e:
        st.warning("⚠️ Internet connection required for full RAG functionality. Using simplified feedback mode.")
        embedding_model = None  
        use_embeddings = False
    
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
    
    if use_embeddings:
        dimension = 384  # for all-MiniLM-L6-v2
        faiss_index = faiss.IndexFlatL2(dimension)
        embeddings = embedding_model.encode(knowledge_chunks)
        faiss_index.add(np.array(embeddings))
    
        def retrieve_knowledge(query, top_k=2):
            query_embedding = embedding_model.encode([query])
            distances, indices = faiss_index.search(np.array(query_embedding), top_k)
            return [knowledge_chunks[i] for i in indices[0]]
    else:
        # Fallback: simple text retrieval without embeddings
        def retrieve_knowledge(query, top_k=2):
            # Simple keyword matching fallback
            query_words = query.lower().split()
            scored_chunks = []
            for chunk in knowledge_chunks:
                score = sum(word in chunk.lower() for word in query_words)
                scored_chunks.append((score, chunk))
            scored_chunks.sort(reverse=True)
            return [chunk for score, chunk in scored_chunks[:top_k] if score > 0]
    
    ### --- Initialize chat history --- ###
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": "Hello! I’m Alex, your dental hygiene patient for today."
        })
    
    # --- Display chat history with role labels ---
    for message in st.session_state.chat_history:
        persona_name = st.session_state.selected_persona
        role_label = "🧑‍⚕️ Student" if message["role"] == "user" else f"🧕 Patient ({persona_name})"
        with st.chat_message(message["role"]):
            st.markdown(f"**{role_label}**: {message['content']}")
    
    # --- Feedback section ---
    if st.button("Finish Session & Get Feedback"):
        transcript = "\n".join([
            f"STUDENT: {msg['content']}" if msg['role'] == "user" else f"PATIENT ({persona_name}): {msg['content']}"
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
    
    # --- Handle chat input with MI Skills Tracking ---
    user_prompt = st.chat_input("Your response...")
    
    if user_prompt:
        # Track MI skills in the user's message
        mi_analysis = st.session_state.mi_tracker.analyze_message(user_prompt)
        st.session_state.mi_tracker.conversation_turns += 1
        
        st.session_state.chat_history.append({"role": "user", "content": user_prompt})
        st.chat_message("user").markdown(user_prompt)
    
        # Show real-time MI technique feedback (subtle)
        if mi_analysis["techniques"]:
            with st.sidebar:
                st.success(f"✓ MI Techniques Used: {', '.join(mi_analysis['techniques'])}")
    
        turn_instruction = {
            "role": "system",
            "content": "Follow the MI chain-of-thought steps: identify routine, ask open question, reflect, elicit change talk, summarize & plan."
        }
        messages = [
            {"role": "system", "content": PERSONA_PROMPTS[st.session_state.selected_persona]},
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
    
    # --- Start New Conversation Button ---
    if st.button("Start New Conversation"):
        st.session_state.selected_persona = None
        st.session_state.chat_history = []
        if "mi_tracker" in st.session_state:
            del st.session_state.mi_tracker
        st.rerun()
