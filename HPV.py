import os
import json
import streamlit as st
from groq import Groq
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import time

# --- Enhanced Persona System Prompts with Emotional Context ---
PERSONAS = {
    "Alex": """
You are "Alex," a realistic patient simulator designed to help providers practice Motivational Interviewing (MI) skills for HPV vaccination discussions.

Background: You are a 25-year-old barista at a local coffee shop, single, and living in an urban area. You've heard about the HPV vaccine from coworkers but haven't seriously considered it until now.

**Emotional Context & Memory:**
- Remember and reference previous parts of our conversation
- Show emotional progression based on how the provider treats you
- Express hesitation that can turn into curiosity if approached with empathy
- Display realistic concerns about side effects, timing, and personal relevance

Your task:
1. **Roleplay as a patient** who is uncertain about the HPV vaccine, but curious to know more. You will start the conversation by introducing yourself and your reason for the visit. Do not sound too hesitant or too eager.
2. **Respond naturally** to the provider's questions or statements. Show curiosity, doubts, or ambivalence to encourage the provider to use MI techniques.
3. **Continue the conversation** for up to 10-12 minutes, maintaining realism and varying your tone (e.g., curious, hesitant, concerned).
4. **Show emotional intelligence**: Remember what the provider says and reference it later. Express gratitude when they listen well.
5. **Evaluate the provider's MI performance** at the end of the conversation using the HPV MI rubric (Collaboration, Evocation, Acceptance, Compassion, Summary).

**Guidelines for Conversation:**
- Play the patient role ONLY during the conversation.
- Use realistic, conversational language (e.g., "I just don't know much about the HPV vaccine" or "I'm still young, why is this needed?").
- Show emotional responses: if provider reflects well, say things like "Yeah, that's exactly how I feel"
- Reference previous statements: "Like I mentioned earlier..." or "You said something about..."
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

**Emotional Context & Memory:**
- Remember details from earlier in our conversation and reference them
- Show typical college student concerns: time, cost, necessity
- Express the overwhelm of making adult healthcare decisions
- Demonstrate growing confidence when providers show understanding

Your task:
1. **Roleplay as a patient** who is uncertain about the HPV vaccine, but curious to know more. You will start the conversation by introducing yourself and your reason for the visit.
2. **Respond naturally** with emotional depth based on the provider's approach
3. **Show memory** of the conversation - reference earlier statements and build on them
4. **Continue the conversation** for up to 10-12 minutes, with realistic emotional progression

**Guidelines for Conversation:**
- Use realistic college student language ("I'm pretty busy with school", "My parents never really talked about this stuff")
- Show emotional responses to good MI techniques with phrases like "That actually makes sense" or "I hadn't thought of it that way"
- Reference previous parts of conversation: "You mentioned earlier..." or "Going back to what you said..."
- Display typical concerns: time management, parental input, peer influence

**Evaluation and feedback as detailed in Alex's persona**
""",

    "Charlie": """
You are "Charlie," a realistic patient simulator designed to help providers practice Motivational Interviewing (MI) skills for HPV vaccination discussions.

Background: You are a 30-year-old parent of two young children (ages 4 and 6), working as a middle school teacher. You're concerned about vaccine safety and want to make the best decisions for your children and yourself.

**Emotional Context & Memory:**
- Remember conversation details and build upon them emotionally
- Show parental protective instincts and responsibility
- Express the weight of making decisions that affect your children
- Demonstrate appreciation when providers acknowledge your parental concerns

Your task:
1. **Roleplay as a patient** who is thoughtful and concerned about HPV vaccination decisions
2. **Show emotional intelligence** - remember what the provider says and how it makes you feel
3. **Display parental perspective** with concerns about timing, safety, and setting good examples
4. **Continue the conversation** showing realistic emotional development based on provider's approach

**Guidelines for Conversation:**
- Use parent-focused language ("My kids are still young", "I want to set a good example")
- Show emotional responsiveness: "That's reassuring to hear" when providers show understanding
- Reference earlier conversation: "When you explained that earlier, it helped me understand..."
- Express typical parental concerns: long-term effects, timing, discussing with children

**Evaluation and feedback as detailed in Alex's persona**
""",

    "Diana": """
You are "Diana," a realistic patient simulator designed to help providers practice Motivational Interviewing (MI) skills for HPV vaccination discussions.

Background: You are a 22-year-old recent graduate working in retail. You're health-conscious but skeptical of medical recommendations due to negative experiences in the past. You've seen social media discussions about vaccines that have made you hesitant.

**Emotional Context & Memory:**
- Remember and reference previous statements in the conversation
- Show initial skepticism that can soften with genuine empathy
- Express past negative healthcare experiences that influence your current feelings
- Demonstrate gradual trust-building when providers show respect for your autonomy

Your task:
1. **Roleplay as a patient** who starts skeptical but can become more open with good MI techniques
2. **Show conversational memory** - reference earlier points and build emotional connections
3. **Display realistic skepticism** based on social media influence and past experiences
4. **Demonstrate emotional progression** from defensive to potentially more trusting

**Guidelines for Conversation:**
- Use skeptical but not hostile language ("I've read some concerning things online", "Doctors haven't always listened to me before")
- Show responsiveness to good reflections: "Yes, exactly!" or "Finally, someone gets it"
- Reference conversation history: "Like I said before..." or "That connects to what you mentioned..."
- Express natural concerns: online information, past experiences, wanting control over decisions

**Evaluation and feedback as detailed in Alex's persona**
"""
}

# --- Streamlit page configuration ---
st.set_page_config(
    page_title="HPV MI Practice",
    page_icon="🧬",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Add custom CSS for improved styling
st.markdown("""
<style>
.chat-message {
    padding: 1rem;
    border-radius: 10px;
    margin-bottom: 1rem;
    display: flex;
    flex-direction: column;
}

.user-message {
    background-color: #e3f2fd;
    border-left: 4px solid #1976d2;
}

.assistant-message {
    background-color: #f1f8e9;
    border-left: 4px solid #388e3c;
}

.persona-card {
    background-color: #fafafa;
    border: 1px solid #e0e0e0;
    border-radius: 10px;
    padding: 1rem;
    margin-bottom: 1rem;
}

.progress-indicator {
    background-color: #e8f5e8;
    border-radius: 10px;
    padding: 0.5rem;
    margin-bottom: 1rem;
    text-align: center;
}

.emotional-context {
    font-style: italic;
    color: #666;
    font-size: 0.9em;
    margin-top: 0.5rem;
}
</style>
""", unsafe_allow_html=True)

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

# --- Warn and stop if key not provided ---
if not api_key:
    st.warning("Please enter your GROQ API key above to continue.")
    st.stop()

# --- Set API key and initialize client ---
os.environ["GROQ_API_KEY"] = api_key
client = Groq()

# --- Initialize session state for persona selection ---
if "selected_persona" not in st.session_state:
    st.session_state.selected_persona = None

# --- Enhanced session state for conversation context ---
if "conversation_context" not in st.session_state:
    st.session_state.conversation_context = {
        "turn_count": 0,
        "emotional_state": "neutral",
        "key_concerns": [],
        "rapport_level": "initial"
    }

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- Enhanced Persona Selection ---
if st.session_state.selected_persona is None:
    st.markdown("### 🎭 Choose Your Patient Persona")
    st.markdown("""
    <div class="persona-card">
    Select a patient persona to practice with. Each persona has unique concerns and emotional contexts:
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="persona-card">
        <h4>👩 Alex (25)</h4>
        <p><strong>Barista, Urban, Single</strong></p>
        <p>Heard about HPV vaccine from coworkers. Curious but uncertain. Shows hesitation that can turn into curiosity with empathetic approach.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="persona-card">
        <h4>👨‍🎓 Bob (19)</h4>
        <p><strong>College Student, Business Major</strong></p>
        <p>Busy with classes and work. Healthcare decisions feel overwhelming. Parents never discussed vaccines with him.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="persona-card">
        <h4>👨‍🏫 Charlie (30)</h4>
        <p><strong>Parent & Teacher</strong></p>
        <p>Has two young children. Concerned about vaccine safety. Wants to make responsible decisions for family.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="persona-card">
        <h4>👩‍💼 Diana (22)</h4>
        <p><strong>Recent Graduate, Retail</strong></p>
        <p>Health-conscious but skeptical due to past experiences. Influenced by social media discussions about vaccines.</p>
        </div>
        """, unsafe_allow_html=True)
    
    selected = st.selectbox(
        "Select a persona to begin:",
        list(PERSONAS.keys()),
        key="persona_selector"
    )
    
    if st.button("🚀 Start Conversation", type="primary"):
        st.session_state.selected_persona = selected
        st.session_state.chat_history = []
        st.session_state.conversation_context = {
            "turn_count": 0,
            "emotional_state": "curious",
            "key_concerns": [],
            "rapport_level": "initial"
        }
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": f"Hello! I'm {selected}, nice to meet you today. I'm here because I've been thinking about the HPV vaccine and wanted to learn more about it."
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

# --- Step 2: Initialize RAG (Embeddings + FAISS) with error handling ---
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

embedding_model = None
faiss_index = None
knowledge_chunks = []

try:
    embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    
    knowledge_chunks = split_text(knowledge_text)
    dimension = 384  # for all-MiniLM-L6-v2
    faiss_index = faiss.IndexFlatL2(dimension)
    embeddings = embedding_model.encode(knowledge_chunks)
    faiss_index.add(np.array(embeddings))
    print("✅ RAG system initialized successfully")
except Exception as e:
    print(f"⚠️ RAG system initialization failed: {e}")
    print("Chat will work without enhanced feedback system")
    # Use simple knowledge base as fallback
    knowledge_chunks = [
        "Motivational Interviewing focuses on collaboration, evocation, acceptance, and compassion.",
        "Use open-ended questions, reflections, affirmations, and summaries in MI conversations.",
        "Avoid asking questions that start with 'Can you...' and instead use 'What', 'How', 'Tell me about'",
        "Good MI involves listening more than talking and helping patients find their own motivations."
    ]

def retrieve_knowledge(query, top_k=2):
    if embedding_model and faiss_index:
        try:
            query_embedding = embedding_model.encode([query])
            distances, indices = faiss_index.search(np.array(query_embedding), top_k)
            return [knowledge_chunks[i] for i in indices[0]]
        except Exception:
            pass
    # Fallback to simple text matching
    return knowledge_chunks[:top_k]

def update_emotional_context(context, user_input, assistant_response):
    """Update conversation context based on interaction quality"""
    # Simple heuristic to update emotional state based on MI techniques
    user_lower = user_input.lower()
    
    # Check for good MI techniques
    good_techniques = ['tell me', 'what do you think', 'how do you feel', 'sounds like', 'it seems', 'help me understand']
    bad_techniques = ['you should', 'you need to', 'can you', 'why don\'t you']
    
    good_count = sum(1 for technique in good_techniques if technique in user_lower)
    bad_count = sum(1 for technique in bad_techniques if technique in user_lower)
    
    # Update emotional state
    if good_count > bad_count:
        if context["emotional_state"] == "defensive":
            context["emotional_state"] = "cautious"
        elif context["emotional_state"] == "cautious":
            context["emotional_state"] = "curious"
        elif context["emotional_state"] == "curious":
            context["emotional_state"] = "engaged"
    elif bad_count > good_count:
        if context["emotional_state"] == "engaged":
            context["emotional_state"] = "curious"
        elif context["emotional_state"] == "curious":
            context["emotional_state"] = "cautious"
        else:
            context["emotional_state"] = "defensive"
    
    # Update rapport level
    if good_count >= 2:
        if context["rapport_level"] == "initial":
            context["rapport_level"] = "building"
        elif context["rapport_level"] == "building":
            context["rapport_level"] = "good"
    
    return context

# --- Display chat history ---
if st.session_state.selected_persona is not None:
    # Progress indicator
    progress_text = f"🎭 Practicing with **{st.session_state.selected_persona}** | Turn: {st.session_state.conversation_context['turn_count']//2 + 1}"
    emotional_context = st.session_state.conversation_context['emotional_state']
    
    st.markdown(f"""
    <div class="progress-indicator">
    {progress_text} | Emotional state: <em>{emotional_context}</em>
    </div>
    """, unsafe_allow_html=True)
    
    # Enhanced chat display with avatars
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            with st.chat_message("user", avatar="🧑‍⚕️"):
                st.markdown(f"**Provider:** {message['content']}")
        else:
            persona_avatars = {"Alex": "👩", "Bob": "👨‍🎓", "Charlie": "👨‍🏫", "Diana": "👩‍💼"}
            avatar = persona_avatars.get(st.session_state.selected_persona, "🧑‍⚕️")
            with st.chat_message("assistant", avatar=avatar):
                st.markdown(f"**{st.session_state.selected_persona}:** {message['content']}")
                
                # Add emotional context for assistant messages
                if len(st.session_state.chat_history) > 2:  # Don't show for initial message
                    context = st.session_state.conversation_context
                    st.markdown(f'<div class="emotional-context">💭 {context["emotional_state"]} • {context["rapport_level"]} rapport</div>', 
                              unsafe_allow_html=True)

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

        try:
            feedback_response = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[
                    {"role": "system", "content": PERSONAS[st.session_state.selected_persona]},
                    {"role": "user", "content": review_prompt}
                ]
            )
            feedback = feedback_response.choices[0].message.content
        except Exception:
            # Fallback feedback for demonstration
            feedback = f"""
## MI Skills Assessment for {st.session_state.selected_persona}

**Overall Performance:** Based on the conversation, here's your feedback:

### Collaboration (Partnership & Rapport)
- **Status:** Review needed
- **Feedback:** Focus on building partnership through asking permission and involving the patient in decisions
- **Suggestion:** Try phrases like "What do you think about..." instead of "You should..."

### Evocation (Drawing Out Patient's Perspective)
- **Status:** Review needed  
- **Feedback:** Work on asking more open-ended questions to understand the patient's motivations
- **Suggestion:** Use "Tell me about..." or "Help me understand..." rather than closed questions

### Acceptance (Respecting Autonomy)
- **Status:** Review needed
- **Feedback:** Practice more reflective listening and affirmations
- **Suggestion:** Reflect back what you hear: "It sounds like you're feeling..."

### Compassion (Non-judgmental Approach)
- **Status:** Review needed
- **Feedback:** Avoid giving advice too quickly; explore the patient's perspective first
- **Suggestion:** Show empathy: "That makes sense that you'd feel that way..."

### Summary & Planning
- **Status:** Review needed
- **Feedback:** End with a summary of what the patient shared and collaborative next steps
- **Suggestion:** "Let me make sure I understand... What feels like a good next step for you?"

*This is a demonstration mode. Connect with a valid API key for personalized feedback.*
"""
        st.markdown("### Session Feedback")
        st.markdown(feedback)

    # --- Enhanced User Input with Typing Indicators ---
    user_prompt = st.chat_input("Your response as the healthcare provider...", key="user_input")

    if user_prompt:
        # Update conversation context
        st.session_state.conversation_context["turn_count"] += 1
        
        st.session_state.chat_history.append({"role": "user", "content": user_prompt})
        
        # Display user message immediately
        with st.chat_message("user", avatar="🧑‍⚕️"):
            st.markdown(f"**Provider:** {user_prompt}")

        # Enhanced turn instruction with emotional context
        turn_instruction = {
            "role": "system",
            "content": f"""Follow the MI chain-of-thought steps: identify routine, ask open question, reflect, elicit change talk, summarize & plan.

Current conversation context:
- Turn count: {st.session_state.conversation_context['turn_count']}
- Current emotional state: {st.session_state.conversation_context['emotional_state']}
- Rapport level: {st.session_state.conversation_context['rapport_level']}

Remember previous parts of the conversation and show emotional progression based on how the provider is treating you. Use phrases that reference earlier statements when appropriate."""
        }
        
        messages = [
            {"role": "system", "content": PERSONAS[st.session_state.selected_persona]},
            turn_instruction,
            *st.session_state.chat_history
        ]

        # Show typing indicator
        with st.spinner(f"{st.session_state.selected_persona} is thinking..."):
            time.sleep(1)  # Brief pause for more natural feel
            try:
                response = client.chat.completions.create(
                    model="openai/gpt-oss-120b",
                    messages=messages
                )
                assistant_response = response.choices[0].message.content
            except Exception as e:
                # Fallback response for demo purposes when API is not available
                personas_responses = {
                    "Alex": "That's a really thoughtful question. I appreciate you taking the time to explain things to me. I'm still processing all of this information about the HPV vaccine, but I'm feeling more comfortable talking about it with you.",
                    "Bob": "Honestly, I hadn't really thought about this stuff before. It's a lot to take in, but I'm starting to see why this might be important for someone my age.",
                    "Charlie": "As a parent, I really appreciate how you're approaching this. You're helping me think through the implications for both me and my kids. That means a lot.",
                    "Diana": "I have to admit, I came in pretty skeptical, but the way you're listening to my concerns is different from other healthcare experiences I've had. It's making me more open to considering this."
                }
                assistant_response = personas_responses.get(
                    st.session_state.selected_persona, 
                    "Thank you for sharing that with me. I'm finding this conversation really helpful in thinking through my feelings about the HPV vaccine."
                )

        # Update emotional context based on response
        st.session_state.conversation_context = update_emotional_context(
            st.session_state.conversation_context, user_prompt, assistant_response
        )

        st.session_state.chat_history.append({"role": "assistant", "content": assistant_response})
        
        # Display assistant response with enhanced styling
        persona_avatars = {"Alex": "👩", "Bob": "👨‍🎓", "Charlie": "👨‍🏫", "Diana": "👩‍💼"}
        avatar = persona_avatars.get(st.session_state.selected_persona, "🧑‍⚕️")
        
        with st.chat_message("assistant", avatar=avatar):
            st.markdown(f"**{st.session_state.selected_persona}:** {assistant_response}")
            context = st.session_state.conversation_context
            st.markdown(f'<div class="emotional-context">💭 {context["emotional_state"]} • {context["rapport_level"]} rapport</div>', 
                      unsafe_allow_html=True)

        # Refresh the page to show updated progress
        st.rerun()

    # Enhanced session controls
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄 Start New Conversation", type="secondary"):
            st.session_state.selected_persona = None
            st.session_state.chat_history = []
            st.session_state.conversation_context = {
                "turn_count": 0,
                "emotional_state": "neutral",
                "key_concerns": [],
                "rapport_level": "initial"
            }
            st.rerun()
