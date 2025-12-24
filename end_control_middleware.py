"""
End-Control Middleware for MI Chatbots

This module implements conversation ending logic with two paths:

Path 1: Mutual Intent (default, no requirements)
- User signals end (bye/thanks/done) AND bot acknowledges (goodbye/you're welcome)
- Immediate ending without turn/MI requirements

Path 2: Semantic-Based (traditional, with requirements)
1. Minimum turn threshold (configurable, default 0 for mutual-intent mode)
2. MI coverage requirements met (open-ended Q, reflection, autonomy, summary)
3. Semantic signals (doctor closure + patient satisfaction)
4. Two-step confirmation flow

The middleware provides detailed tracing for diagnosing future incidents.

Conversation States:
- ACTIVE: Normal conversation in progress
- PENDING_END_CONFIRMATION: Awaiting student confirmation
- AWAITING_SECOND_CONFIRMATION: Asking for second confirmation if ambiguous
- ENDED: Conversation concluded
- PARKED: Session idle/disconnected but not ended
"""

import os
import logging
import re
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from enum import Enum

# Configure logging
logger = logging.getLogger(__name__)

# Configuration - can be overridden via environment variables
MIN_TURN_THRESHOLD = int(os.environ.get('MI_MIN_TURN_THRESHOLD', '0'))  # Default 0 for no turn requirement
END_TOKEN = os.environ.get('MI_END_TOKEN', '<<END>>')

# Conversation states
class ConversationState(Enum):
    """States for conversation flow control."""
    ACTIVE = "ACTIVE"
    END_SUGGESTED = "END_SUGGESTED"
    PENDING_END_CONFIRMATION = "PENDING_END_CONFIRMATION"
    AWAITING_SECOND_CONFIRMATION = "AWAITING_SECOND_CONFIRMATION"
    ENDED = "ENDED"
    PARKED = "PARKED"  # Session idle/disconnected but not ended

# Mutual-Intent Patterns for simple end condition
# User end intent - phrases indicating student wants to finish
USER_END_INTENT_PATTERNS = [
    r'\b(bye|goodbye|see you|farewell)\b',
    r'\b(thanks?|thank you|thx)\s*(for|so much)?\b',
    r'\b(done|finished|complete|all set)\b',
    r'\bthat\'s (all|it|everything)\b',
    r'\bwe\'re (done|finished|good)\b',
    r'\bi\'m (done|finished|good|all set)\b',
]

# Bot end acknowledgment - phrases indicating bot provided closing
BOT_END_ACK_PATTERNS = [
    r'\b(goodbye|bye|see you|take care)\b',
    r'\byou\'re welcome\b',
    r'\bglad (to help|i could help)\b',
    r'\bfeel free to (come back|reach out)\b',
    r'\bhave a (good|great|nice) (day|time)\b',
    r'\b(best wishes|good luck|all the best)\b',
]

# MI Coverage requirements - phrases/patterns to detect in assistant messages
MI_COVERAGE_PATTERNS = {
    'open_ended_question': [
        r'\bwhat\b.*\?',
        r'\bhow\b.*\?',
        r'\btell me\b',
        r'\bhelp me understand\b',
        r'\bdescribe\b',
        r'\bexplain\b',
        r'\bshare\b.*\bthoughts\b',
        r'\bwalk me through\b',
    ],
    'reflection': [
        r'\bit sounds like\b',
        r'\bit seems\b',
        r'\bso you\'re\b',
        r'\byou\'re feeling\b',
        r'\byou mentioned\b',
        r'\bif i understand\b',
        r'\bi hear\b.*\bsaying\b',
        r'\bon one hand\b.*\bon the other\b',
    ],
    'autonomy': [
        r'\byou can decide\b',
        r'\bit\'s up to you\b',
        r'\byour choice\b',
        r'\bwhat would work\b',
        r'\bwhat feels right\b',
        r'\byou know yourself\b',
        r'\bwhat do you think\b',
        r'\byou\'re in control\b',
    ],
    'summary': [
        r'\bto summarize\b',
        r'\blet me recap\b',
        r'\bso far we\'ve\b',
        r'\bwe\'ve talked about\b',
        r'\bin summary\b',
        r'\blooking back\b',
        r'\bto sum up\b',
    ],
}

# Student confirmation patterns - explicit closure phrases
# These must be clear affirmative closure intents
STUDENT_CONFIRMATION_PATTERNS = [
    r'\bno,?\s+(we\'re\s+)?done\b',
    r'\bwe\'re\s+done\b',
    r'\bi\s+think\s+we\'re\s+done\b',
    r'\bthat\'s\s+all\b',
    r'\bwe\s+can\s+end\b',
    r'\bno\s+more\s+to\s+discuss\b',
    r'\bfinish\b',
    r'\byes,?\s+(let\'s\s+)?end\b',
    r'\blet\'s\s+end\b',
    r'\bno\s+more\s+questions\b',
    r'\bi\'m\s+done\b',
    r'\bwe\s+can\s+finish\b',
    r'\bi\'m\s+ready\s+to\s+finish\b',
    r'\blet\'s\s+wrap\s+up\b',
    r'\bwe\'re\s+good\s+to\s+end\b',
    r'\bnothing\s+more\b',
    r'\ball\s+set\b',
]

# Ambiguous phrases that should NOT trigger ending
AMBIGUOUS_ENDING_PHRASES = [
    'thanks',
    'okay',
    'ok',
    'alright',
    'sure',
    'thank you',
    'i get it',
    'got it',
    'i understand',
    'makes sense',
    'i see',
    'yeah',
    'yep',
    'cool',
]

# Patient satisfaction patterns - indicates concerns are being addressed
PATIENT_SATISFACTION_PATTERNS = [
    r'\b(that\s+helps?|thank\s+you|makes?\s+sense|i\s+understand|feel\s+better)\b',
    r'\b(less\s+worried|good\s+to\s+know|appreciate|helpful)\b',
    r'\b(i\'ll\s+think\s+about\s+it|consider|might\s+try)\b',
    r'\b(that\s+answers|you\'ve\s+explained|clearer\s+now)\b',
    r'\b(that\'s\s+reassuring|makes\s+me\s+feel|sounds\s+reasonable)\b',
]

# Doctor closure signals - student wrapping up
DOCTOR_CLOSURE_PATTERNS = [
    r'\b(any\s+other\s+questions?|anything\s+else|is\s+there\s+more)\b',
    r'\b(glad\s+i\s+could\s+help|happy\s+to\s+help)\b',
    r'\b(take\s+care|feel\s+free\s+to\s+come\s+back)\b',
    r'\b(let\s+me\s+know\s+if|don\'t\s+hesitate)\b',
    r'\b(we\s+covered|discussed\s+everything)\b',
    r'\b(before\s+we\s+wrap\s+up|before\s+we\s+end|before\s+we\s+finish)\b',
]

# Patient explicit end confirmation
PATIENT_END_CONFIRMATION_PATTERNS = [
    r'\b(no,?\s+that\'s\s+all|no\s+more\s+questions?)\b',
    r'\b(i\'m\s+good|i\'m\s+all\s+set|nothing\s+else)\b',
    r'\b(that\'s\s+everything|covered\s+everything)\b',
    r'\b(ready\s+to\s+go|can\s+leave\s+now)\b',
    r'\b(i\s+think\s+we\'re\s+done|i\s+think\s+that\'s\s+it)\b',
]


def detect_user_end_intent(user_message: str) -> bool:
    """
    Detect if the user (student) is signaling intent to end the conversation.
    
    Looks for simple goodbye, thanks, or done phrases.
    
    Args:
        user_message: The user's message
        
    Returns:
        bool: True if user shows intent to end
    """
    if not user_message:
        return False
    
    message_lower = user_message.lower().strip()
    
    for pattern in USER_END_INTENT_PATTERNS:
        if re.search(pattern, message_lower):
            logger.info(f"User end intent detected: '{user_message[:50]}...'")
            return True
    
    return False


def detect_bot_end_ack(bot_message: str) -> bool:
    """
    Detect if the bot (assistant) has provided a closing acknowledgment.
    
    Looks for goodbye, farewell, or closing phrases.
    
    Args:
        bot_message: The bot's message
        
    Returns:
        bool: True if bot provided closing acknowledgment
    """
    if not bot_message:
        return False
    
    message_lower = bot_message.lower().strip()
    
    for pattern in BOT_END_ACK_PATTERNS:
        if re.search(pattern, message_lower):
            logger.info(f"Bot end acknowledgment detected: '{bot_message[:50]}...'")
            return True
    
    return False


def check_mutual_intent(
    conversation_context: Dict,
    last_assistant_text: str,
    last_user_text: Optional[str] = None
) -> Dict:
    """
    Early-exit check for mutual-intent end condition.
    
    This function provides a simple ending mechanism based on mutual intent:
    - user_end_intent: Student signals they want to end (bye/thanks/done)
    - bot_end_ack: Bot provides closing acknowledgment
    
    When BOTH flags are set, the conversation can end without requiring
    turn thresholds or MI coverage checks.
    
    Args:
        conversation_context: Dictionary containing:
            - user_end_intent: Flag set when user signals end
            - bot_end_ack: Flag set when bot acknowledges end
        last_assistant_text: The most recent bot message
        last_user_text: The most recent user message (optional)
        
    Returns:
        Dictionary with:
            - continue: bool (False if mutual intent detected)
            - state: str (ENDED if mutual intent)
            - reason: str (explanation)
            - mutual_intent: bool (True if both flags set)
    """
    user_end_intent = conversation_context.get('user_end_intent', False)
    bot_end_ack = conversation_context.get('bot_end_ack', False)
    
    # Check if user message signals end intent
    if last_user_text and detect_user_end_intent(last_user_text):
        user_end_intent = True
        conversation_context['user_end_intent'] = True
        logger.info("User end intent flag set")
    
    # Check if bot message provides closing acknowledgment
    if last_assistant_text and detect_bot_end_ack(last_assistant_text):
        bot_end_ack = True
        conversation_context['bot_end_ack'] = True
        logger.info("Bot end acknowledgment flag set")
    
    # If both intents are set, allow ending
    if user_end_intent and bot_end_ack:
        logger.info("Mutual intent detected - allowing conversation to end")
        return {
            'continue': False,
            'state': ConversationState.ENDED.value,
            'reason': 'Mutual intent: both student and bot signaled end',
            'mutual_intent': True,
            'requires_confirmation': False,
            'confirmation_prompt': None,
            'metrics': {
                'user_end_intent': True,
                'bot_end_ack': True,
                'mutual_intent': True
            }
        }
    
    # Mutual intent not yet achieved
    return {
        'continue': True,
        'state': ConversationState.ACTIVE.value,
        'reason': f'Mutual intent not complete (user_end_intent={user_end_intent}, bot_end_ack={bot_end_ack})',
        'mutual_intent': False,
        'requires_confirmation': False,
        'confirmation_prompt': None,
        'metrics': {
            'user_end_intent': user_end_intent,
            'bot_end_ack': bot_end_ack,
            'mutual_intent': False
        }
    }


def detect_patient_satisfaction(chat_history: List[Dict]) -> bool:
    """
    Detect if patient shows satisfaction with the conversation.
    
    Analyzes assistant (patient) messages for satisfaction indicators.
    
    Args:
        chat_history: List of chat messages with 'role' and 'content'
        
    Returns:
        bool: True if patient satisfaction signals detected
    """
    # Look at recent assistant messages (patient responses)
    satisfaction_count = 0
    recent_messages = [msg for msg in chat_history[-6:] if msg.get('role') == 'assistant']
    
    for message in recent_messages:
        content = message.get('content', '').lower()
        for pattern in PATIENT_SATISFACTION_PATTERNS:
            if re.search(pattern, content):
                satisfaction_count += 1
                break  # Count each message only once
    
    # Need at least 2 satisfaction signals
    satisfied = satisfaction_count >= 2
    if satisfied:
        logger.debug(f"Patient satisfaction detected ({satisfaction_count} signals)")
    return satisfied


def detect_doctor_closure_signal(user_message: str) -> bool:
    """
    Detect if doctor (student) is signaling readiness to wrap up.
    
    Args:
        user_message: The latest user (doctor) message
        
    Returns:
        bool: True if doctor closure signal detected
    """
    message_lower = user_message.lower().strip()
    
    for pattern in DOCTOR_CLOSURE_PATTERNS:
        if re.search(pattern, message_lower):
            logger.debug(f"Doctor closure signal detected: '{user_message[:50]}...'")
            return True
    
    return False


def detect_patient_end_confirmation(assistant_message: str) -> bool:
    """
    Detect if patient explicitly confirms they have no more questions.
    
    Args:
        assistant_message: The patient's response
        
    Returns:
        bool: True if patient confirms readiness to end
    """
    message_lower = assistant_message.lower().strip()
    
    for pattern in PATIENT_END_CONFIRMATION_PATTERNS:
        if re.search(pattern, message_lower):
            logger.debug(f"Patient end confirmation detected: '{assistant_message[:50]}...'")
            return True
    
    return False


def get_conversation_state(conversation_context: Dict) -> ConversationState:
    """
    Get current conversation state from context.
    
    Args:
        conversation_context: Dictionary containing conversation metadata
        
    Returns:
        ConversationState enum value (default: ACTIVE)
    """
    state_str = conversation_context.get('end_control_state', 'ACTIVE')
    try:
        return ConversationState(state_str)
    except ValueError:
        logger.warning(f"Invalid conversation state '{state_str}', defaulting to ACTIVE")
        return ConversationState.ACTIVE


def set_conversation_state(conversation_context: Dict, state: ConversationState) -> None:
    """
    Set conversation state in context.
    
    Args:
        conversation_context: Dictionary containing conversation metadata
        state: ConversationState to set
    """
    conversation_context['end_control_state'] = state.value
    logger.info(f"Conversation state changed to: {state.value}")


def can_suggest_ending(conversation_state: Dict) -> bool:
    """
    Determine if bot can suggest ending based on SEMANTIC signals, not turn count.
    
    CRITICAL: Do NOT use MIN_TURN_THRESHOLD as a trigger to suggest ending.
    Only use it as a minimum floor.
    
    Checks:
    - Minimum turn threshold (as a floor only, not a trigger)
    - MI coverage requirements
    - Doctor has offered closure (semantic signal)
    - Patient shows satisfaction (semantic signal)
    
    Args:
        conversation_state: Dictionary containing chat_history and turn_count
        
    Returns:
        bool: True if conditions met for suggesting end
    """
    chat_history = conversation_state.get('chat_history', [])
    turn_count = conversation_state.get('turn_count', 0)
    
    # Minimum floor - need at least minimum exchanges
    if turn_count < MIN_TURN_THRESHOLD:
        logger.debug(f"Cannot suggest ending: only {turn_count}/{MIN_TURN_THRESHOLD} turns")
        return False
    
    # Check MI coverage (still required)
    mi_coverage = check_mi_coverage(chat_history)
    missing_components = [comp for comp, present in mi_coverage.items() if not present]
    
    if missing_components:
        logger.debug(f"Cannot suggest ending: missing MI components {missing_components}")
        return False
    
    # NEW: Only suggest ending when doctor has offered closure AND patient seems satisfied
    # Get last user message to check for doctor closure
    user_messages = [m for m in chat_history if m.get('role') == 'user']
    if not user_messages:
        return False
    
    last_user_message = user_messages[-1].get('content', '')
    if not detect_doctor_closure_signal(last_user_message):
        logger.debug("Cannot suggest ending: doctor has not offered closure")
        return False
    
    if not detect_patient_satisfaction(chat_history):
        logger.debug("Cannot suggest ending: patient has not shown satisfaction")
        return False
    
    logger.debug("All semantic conditions met for suggesting ending")
    return True


def detect_mi_component(text: str, component: str) -> bool:
    """
    Detect if a specific MI component is present in the text.
    
    Args:
        text: Text to analyze (typically assistant message)
        component: MI component to detect ('open_ended_question', 'reflection', 'autonomy', 'summary')
        
    Returns:
        bool: True if component is detected
    """
    if component not in MI_COVERAGE_PATTERNS:
        logger.warning(f"Unknown MI component requested: {component}")
        return False
    
    patterns = MI_COVERAGE_PATTERNS[component]
    text_lower = text.lower()
    
    for pattern in patterns:
        if re.search(pattern, text_lower):
            logger.debug(f"MI component '{component}' detected with pattern: {pattern}")
            return True
    
    return False


def check_mi_coverage(chat_history: List[Dict]) -> Dict[str, bool]:
    """
    Check which MI components have been demonstrated in the conversation.
    
    Args:
        chat_history: List of chat messages with 'role' and 'content'
        
    Returns:
        Dict mapping component names to boolean (present or not)
    """
    coverage = {
        'open_ended_question': False,
        'reflection': False,
        'autonomy': False,
        'summary': False,
    }
    
    # Check all assistant messages for MI components
    for message in chat_history:
        if message.get('role') == 'assistant':
            content = message.get('content', '')
            for component in coverage.keys():
                if not coverage[component]:  # Only check if not already found
                    if detect_mi_component(content, component):
                        coverage[component] = True
    
    logger.info(f"MI Coverage check: {coverage}")
    return coverage


def detect_student_confirmation(user_message: str) -> bool:
    """
    Detect if student explicitly confirms they want to end the conversation.
    
    Args:
        user_message: The latest user message
        
    Returns:
        bool: True if explicit confirmation detected
    """
    message_lower = user_message.lower().strip()
    
    # Check for explicit confirmation patterns
    for pattern in STUDENT_CONFIRMATION_PATTERNS:
        if re.search(pattern, message_lower):
            logger.info(f"Student confirmation detected: '{user_message}'")
            return True
    
    # Check if message is ONLY an ambiguous phrase (should not count as confirmation)
    if message_lower in AMBIGUOUS_ENDING_PHRASES:
        logger.debug(f"Ambiguous phrase detected, not counting as confirmation: '{user_message}'")
        return False
    
    return False


def is_ambiguous_response(user_message: str) -> bool:
    """
    Check if user response is ambiguous and should not trigger ending.
    
    Args:
        user_message: The user's message
        
    Returns:
        bool: True if message is ambiguous
    """
    message_lower = user_message.lower().strip()
    
    # Check if entire message is just an ambiguous phrase
    if message_lower in AMBIGUOUS_ENDING_PHRASES:
        return True
    
    # Check if message is very short and only contains ambiguous words
    words = message_lower.split()
    if len(words) <= 2 and all(word in AMBIGUOUS_ENDING_PHRASES for word in words):
        return True
    
    return False


def generate_patient_confirmation_prompt(first_ask: bool = True) -> str:
    """
    Generate confirmation prompt in patient voice.
    
    Args:
        first_ask: If True, first confirmation ask. If False, second confirmation.
        
    Returns:
        str: Confirmation prompt in patient persona
    """
    if first_ask:
        return "Before we wrap up, doctor, is there anything more you'd like to discuss about this case?"
    else:
        return "Just to confirm, doctor—are you okay ending here?"


def detect_end_token(assistant_message: str) -> bool:
    """
    Detect if the assistant message contains the explicit end token.
    
    Args:
        assistant_message: The assistant's message
        
    Returns:
        bool: True if end token is present
    """
    has_token = END_TOKEN in assistant_message
    if has_token:
        logger.info(f"End token '{END_TOKEN}' detected in assistant message")
    return has_token


def should_continue_v3(
    conversation_context: Dict,
    last_assistant_text: str,
    last_user_text: Optional[str] = None
) -> Dict:
    """
    Production-ready conversation ending with explicit student confirmation.
    
    Implements a state machine with patient-persona confirmation:
    - ACTIVE: Normal conversation
    - PENDING_END_CONFIRMATION: Bot asks patient-voice confirmation (first)
    - AWAITING_SECOND_CONFIRMATION: Bot asks second confirmation if ambiguous
    - ENDED: Conversation concluded with explicit confirmation
    - PARKED: Session idle/disconnected but not ended
    
    Args:
        conversation_context: Dictionary containing:
            - chat_history: List of messages
            - turn_count: Number of student turns
            - end_control_state: Current state (optional, defaults to ACTIVE)
            - confirmation_flag: Whether confirmation was explicitly given
            - termination_trigger: What/who triggered the end process
        last_assistant_text: The most recent assistant message
        last_user_text: The most recent user message (optional)
        
    Returns:
        Dictionary with:
            - continue: bool (True = continue conversation, False = allow ending)
            - state: str (new conversation state)
            - reason: str (explanation for the decision)
            - confirmation_prompt: str (patient-voice confirmation question if needed)
            - requires_confirmation: bool (if confirmation prompt should be shown)
            - metrics: dict (for logging/monitoring)
    """
    from config_loader import ConfigLoader
    
    # Load feature flags
    config = ConfigLoader()
    flags = config.get_feature_flags()
    require_confirmation = flags.get('require_end_confirmation', True)
    
    chat_history = conversation_context.get('chat_history', [])
    turn_count = conversation_context.get('turn_count', 0)
    current_state = get_conversation_state(conversation_context)
    confirmation_flag = conversation_context.get('confirmation_flag', False)
    termination_trigger = conversation_context.get('termination_trigger', 'unknown')
    
    timestamp = datetime.now().isoformat()
    logger.info(f"[{timestamp}] Evaluating v3: state={current_state.value}, turns={turn_count}, require_conf={require_confirmation}")
    
    # Metrics for monitoring
    metrics = {
        'timestamp': timestamp,
        'state': current_state.value,
        'turn_count': turn_count,
        'termination_trigger': termination_trigger,
        'confirmation_flag': confirmation_flag
    }
    
    # State: ENDED - conversation already concluded with confirmation
    if current_state == ConversationState.ENDED:
        if not confirmation_flag:
            logger.warning(f"[{timestamp}] ALERT: Session ended without confirmation flag!")
            metrics['alert'] = 'ended_without_confirmation'
        
        return {
            'continue': False,
            'state': ConversationState.ENDED.value,
            'reason': 'Conversation already ended with confirmation',
            'confirmation_prompt': None,
            'requires_confirmation': False,
            'metrics': metrics
        }
    
    # State: PARKED - session idle/disconnected but not ended
    if current_state == ConversationState.PARKED:
        return {
            'continue': True,
            'state': ConversationState.PARKED.value,
            'reason': 'Session parked (disconnected/idle), awaiting reconnect',
            'confirmation_prompt': "Welcome back, doctor. Shall we continue our discussion?",
            'requires_confirmation': False,
            'metrics': metrics
        }
    
    # State: AWAITING_SECOND_CONFIRMATION - already asked once, checking second response
    if current_state == ConversationState.AWAITING_SECOND_CONFIRMATION:
        if last_user_text:
            # Check for explicit affirmative closure
            if detect_student_confirmation(last_user_text):
                logger.info(f"[{timestamp}] Student confirmed ending on second ask")
                set_conversation_state(conversation_context, ConversationState.ENDED)
                conversation_context['confirmation_flag'] = True
                metrics['confirmation_result'] = 'confirmed_second_ask'
                
                return {
                    'continue': False,
                    'state': ConversationState.ENDED.value,
                    'reason': 'Student confirmed ending after second confirmation',
                    'confirmation_prompt': None,
                    'requires_confirmation': False,
                    'metrics': metrics
                }
            else:
                # Still no clear affirmative or ambiguous - park the session
                logger.info(f"[{timestamp}] No clear confirmation after second ask, parking session")
                set_conversation_state(conversation_context, ConversationState.PARKED)
                metrics['confirmation_result'] = 'parked_after_second_ask'
                
                return {
                    'continue': True,
                    'state': ConversationState.PARKED.value,
                    'reason': 'No clear confirmation after two asks, session parked',
                    'confirmation_prompt': None,
                    'requires_confirmation': False,
                    'metrics': metrics
                }
        else:
            # Still waiting for response
            return {
                'continue': True,
                'state': ConversationState.AWAITING_SECOND_CONFIRMATION.value,
                'reason': 'Awaiting student response to second confirmation',
                'confirmation_prompt': None,
                'requires_confirmation': False,
                'metrics': metrics
            }
    
    # State: PENDING_END_CONFIRMATION - awaiting first confirmation response
    if current_state == ConversationState.PENDING_END_CONFIRMATION:
        if last_user_text:
            # Check if response is explicit affirmative closure
            if detect_student_confirmation(last_user_text):
                logger.info(f"[{timestamp}] Student confirmed ending on first ask")
                set_conversation_state(conversation_context, ConversationState.ENDED)
                conversation_context['confirmation_flag'] = True
                metrics['confirmation_result'] = 'confirmed_first_ask'
                
                return {
                    'continue': False,
                    'state': ConversationState.ENDED.value,
                    'reason': 'Student confirmed ending',
                    'confirmation_prompt': None,
                    'requires_confirmation': False,
                    'metrics': metrics
                }
            elif is_ambiguous_response(last_user_text):
                # Ambiguous response - ask second time
                logger.info(f"[{timestamp}] Ambiguous response to confirmation, asking second time")
                set_conversation_state(conversation_context, ConversationState.AWAITING_SECOND_CONFIRMATION)
                metrics['confirmation_result'] = 'ambiguous_first_response'
                
                return {
                    'continue': True,
                    'state': ConversationState.AWAITING_SECOND_CONFIRMATION.value,
                    'reason': 'Ambiguous response, requesting second confirmation',
                    'confirmation_prompt': generate_patient_confirmation_prompt(first_ask=False),
                    'requires_confirmation': True,
                    'metrics': metrics
                }
            else:
                # Student wants to continue - return to ACTIVE
                logger.info(f"[{timestamp}] Student indicated continuation, returning to ACTIVE")
                set_conversation_state(conversation_context, ConversationState.ACTIVE)
                metrics['confirmation_result'] = 'student_wants_continue'
                
                return {
                    'continue': True,
                    'state': ConversationState.ACTIVE.value,
                    'reason': 'Student indicated they want to continue',
                    'confirmation_prompt': None,
                    'requires_confirmation': False,
                    'metrics': metrics
                }
        else:
            # Still waiting for first confirmation response
            return {
                'continue': True,
                'state': ConversationState.PENDING_END_CONFIRMATION.value,
                'reason': 'Awaiting student confirmation to end',
                'confirmation_prompt': None,
                'requires_confirmation': False,
                'metrics': metrics
            }
    
    # State: ACTIVE - normal conversation flow
    # Check if conditions met to request ending confirmation
    if can_suggest_ending(conversation_context):
        logger.info(f"[{timestamp}] Conditions met to request ending confirmation")
        set_conversation_state(conversation_context, ConversationState.PENDING_END_CONFIRMATION)
        conversation_context['termination_trigger'] = 'system_mi_complete'
        metrics['termination_trigger'] = 'system_mi_complete'
        
        # If feature flag disabled, skip confirmation (legacy behavior)
        if not require_confirmation:
            logger.warning(f"[{timestamp}] Confirmation disabled by feature flag, allowing end")
            set_conversation_state(conversation_context, ConversationState.ENDED)
            conversation_context['confirmation_flag'] = False
            metrics['alert'] = 'confirmation_bypassed_by_flag'
            
            return {
                'continue': False,
                'state': ConversationState.ENDED.value,
                'reason': 'Confirmation disabled by feature flag',
                'confirmation_prompt': None,
                'requires_confirmation': False,
                'metrics': metrics
            }
        
        return {
            'continue': True,
            'state': ConversationState.PENDING_END_CONFIRMATION.value,
            'reason': 'All MI requirements met, requesting confirmation',
            'confirmation_prompt': generate_patient_confirmation_prompt(first_ask=True),
            'requires_confirmation': True,
            'metrics': metrics
        }
    
    # Continue conversation normally
    return {
        'continue': True,
        'state': ConversationState.ACTIVE.value,
        'reason': 'Conversation continuing normally',
        'confirmation_prompt': None,
        'requires_confirmation': False,
        'metrics': metrics
    }


def should_continue_v4(
    conversation_context: Dict,
    last_assistant_text: str,
    last_user_text: Optional[str] = None
) -> Dict:
    """
    Semantic-based conversation ending with mutual confirmation.
    
    This version removes hard turn limits as ending triggers and uses semantic signals:
    - Patient satisfaction detection (concerns being addressed)
    - Doctor closure signals (ready to wrap up)
    - Mutual confirmation (both parties signal completion)
    
    The MIN_TURN_THRESHOLD is kept only as a minimum conversation length requirement,
    NOT as a trigger to suggest ending.
    
    States:
    - ACTIVE: Normal conversation
    - PENDING_END_CONFIRMATION: Waiting for mutual confirmation
    - AWAITING_SECOND_CONFIRMATION: Asking for second confirmation if ambiguous
    - ENDED: Conversation concluded with mutual agreement
    
    Args:
        conversation_context: Dictionary containing:
            - chat_history: List of messages
            - turn_count: Number of student turns
            - end_control_state: Current state (optional, defaults to ACTIVE)
            - confirmation_flag: Whether confirmation was explicitly given
        last_assistant_text: The most recent assistant (patient) message
        last_user_text: The most recent user (doctor) message (optional)
        
    Returns:
        Dictionary with:
            - continue: bool (True = continue conversation, False = allow ending)
            - state: str (new conversation state)
            - reason: str (explanation for the decision)
            - confirmation_prompt: str (confirmation question if needed)
            - requires_confirmation: bool (if confirmation prompt should be shown)
            - metrics: dict (for logging/monitoring)
    """
    from config_loader import ConfigLoader
    
    # Load feature flags
    config = ConfigLoader()
    flags = config.get_feature_flags()
    require_confirmation = flags.get('require_end_confirmation', True)
    
    chat_history = conversation_context.get('chat_history', [])
    turn_count = conversation_context.get('turn_count', 0)
    current_state = get_conversation_state(conversation_context)
    confirmation_flag = conversation_context.get('confirmation_flag', False)
    
    timestamp = datetime.now().isoformat()
    logger.info(f"[{timestamp}] Evaluating v4 (semantic): state={current_state.value}, turns={turn_count}")
    
    # Metrics for monitoring
    metrics = {
        'timestamp': timestamp,
        'state': current_state.value,
        'turn_count': turn_count,
        'confirmation_flag': confirmation_flag,
        'version': 'v4_semantic'
    }
    
    # State: ENDED - conversation already concluded
    if current_state == ConversationState.ENDED:
        return {
            'continue': False,
            'state': ConversationState.ENDED.value,
            'reason': 'Conversation already ended with mutual confirmation',
            'confirmation_prompt': None,
            'requires_confirmation': False,
            'metrics': metrics
        }
    
    # State: PARKED - session idle/disconnected
    if current_state == ConversationState.PARKED:
        return {
            'continue': True,
            'state': ConversationState.PARKED.value,
            'reason': 'Session parked, awaiting reconnect',
            'confirmation_prompt': "Welcome back, doctor. Shall we continue?",
            'requires_confirmation': False,
            'metrics': metrics
        }
    
    # EARLY EXIT: Check for mutual intent (simple end condition)
    # This runs BEFORE other strict checks and allows ending without turn/MI requirements
    mutual_intent_decision = check_mutual_intent(
        conversation_context,
        last_assistant_text,
        last_user_text
    )
    
    # If mutual intent is achieved, end immediately
    if mutual_intent_decision['mutual_intent']:
        logger.info(f"[{timestamp}] Mutual intent achieved - ending conversation")
        set_conversation_state(conversation_context, ConversationState.ENDED)
        conversation_context['confirmation_flag'] = True
        return mutual_intent_decision
    
    # State: AWAITING_SECOND_CONFIRMATION
    if current_state == ConversationState.AWAITING_SECOND_CONFIRMATION:
        if last_user_text:
            if detect_student_confirmation(last_user_text):
                logger.info(f"[{timestamp}] Student confirmed ending on second ask")
                set_conversation_state(conversation_context, ConversationState.ENDED)
                conversation_context['confirmation_flag'] = True
                metrics['confirmation_result'] = 'confirmed_second_ask'
                
                return {
                    'continue': False,
                    'state': ConversationState.ENDED.value,
                    'reason': 'Student confirmed ending after second confirmation',
                    'confirmation_prompt': None,
                    'requires_confirmation': False,
                    'metrics': metrics
                }
            else:
                logger.info(f"[{timestamp}] No clear confirmation after second ask, parking")
                set_conversation_state(conversation_context, ConversationState.PARKED)
                metrics['confirmation_result'] = 'parked_after_second_ask'
                
                return {
                    'continue': True,
                    'state': ConversationState.PARKED.value,
                    'reason': 'No clear confirmation after two asks, session parked',
                    'confirmation_prompt': None,
                    'requires_confirmation': False,
                    'metrics': metrics
                }
        else:
            return {
                'continue': True,
                'state': ConversationState.AWAITING_SECOND_CONFIRMATION.value,
                'reason': 'Awaiting student response to second confirmation',
                'confirmation_prompt': None,
                'requires_confirmation': False,
                'metrics': metrics
            }
    
    # State: PENDING_END_CONFIRMATION
    if current_state == ConversationState.PENDING_END_CONFIRMATION:
        if last_user_text:
            if detect_student_confirmation(last_user_text):
                logger.info(f"[{timestamp}] Student confirmed ending")
                set_conversation_state(conversation_context, ConversationState.ENDED)
                conversation_context['confirmation_flag'] = True
                metrics['confirmation_result'] = 'confirmed_first_ask'
                
                return {
                    'continue': False,
                    'state': ConversationState.ENDED.value,
                    'reason': 'Student confirmed ending',
                    'confirmation_prompt': None,
                    'requires_confirmation': False,
                    'metrics': metrics
                }
            elif is_ambiguous_response(last_user_text):
                logger.info(f"[{timestamp}] Ambiguous response, asking second time")
                set_conversation_state(conversation_context, ConversationState.AWAITING_SECOND_CONFIRMATION)
                metrics['confirmation_result'] = 'ambiguous_first_response'
                
                return {
                    'continue': True,
                    'state': ConversationState.AWAITING_SECOND_CONFIRMATION.value,
                    'reason': 'Ambiguous response, requesting second confirmation',
                    'confirmation_prompt': generate_patient_confirmation_prompt(first_ask=False),
                    'requires_confirmation': True,
                    'metrics': metrics
                }
            else:
                logger.info(f"[{timestamp}] Student wants to continue, returning to ACTIVE")
                set_conversation_state(conversation_context, ConversationState.ACTIVE)
                metrics['confirmation_result'] = 'student_wants_continue'
                
                return {
                    'continue': True,
                    'state': ConversationState.ACTIVE.value,
                    'reason': 'Student indicated they want to continue',
                    'confirmation_prompt': None,
                    'requires_confirmation': False,
                    'metrics': metrics
                }
        else:
            return {
                'continue': True,
                'state': ConversationState.PENDING_END_CONFIRMATION.value,
                'reason': 'Awaiting student confirmation',
                'confirmation_prompt': None,
                'requires_confirmation': False,
                'metrics': metrics
            }
    
    # State: ACTIVE - Check for semantic ending conditions
    # MIN_TURN_THRESHOLD is kept ONLY as minimum requirement, NOT as trigger
    if turn_count < MIN_TURN_THRESHOLD:
        logger.debug(f"Minimum turns not met ({turn_count}/{MIN_TURN_THRESHOLD})")
        return {
            'continue': True,
            'state': ConversationState.ACTIVE.value,
            'reason': f'Minimum turn threshold not met ({turn_count}/{MIN_TURN_THRESHOLD})',
            'confirmation_prompt': None,
            'requires_confirmation': False,
            'metrics': metrics
        }
    
    # Check MI coverage (still required)
    mi_coverage = check_mi_coverage(chat_history)
    missing_components = [comp for comp, present in mi_coverage.items() if not present]
    
    if missing_components:
        logger.debug(f"MI coverage incomplete: {missing_components}")
        return {
            'continue': True,
            'state': ConversationState.ACTIVE.value,
            'reason': f'MI coverage incomplete: {missing_components}',
            'confirmation_prompt': None,
            'requires_confirmation': False,
            'metrics': metrics
        }
    
    # NEW: Semantic-based ending detection
    # Check if BOTH patient AND doctor signal readiness
    patient_satisfied = detect_patient_satisfaction(chat_history)
    doctor_closing = last_user_text and detect_doctor_closure_signal(last_user_text)
    patient_confirms = detect_patient_end_confirmation(last_assistant_text)
    
    metrics['patient_satisfied'] = patient_satisfied
    metrics['doctor_closing'] = doctor_closing
    metrics['patient_confirms'] = patient_confirms
    
    # Only suggest ending when BOTH parties show readiness
    if patient_satisfied and doctor_closing and patient_confirms:
        logger.info(f"[{timestamp}] Mutual completion signals detected - requesting confirmation")
        set_conversation_state(conversation_context, ConversationState.PENDING_END_CONFIRMATION)
        metrics['trigger'] = 'mutual_semantic_signals'
        
        if not require_confirmation:
            logger.warning(f"[{timestamp}] Confirmation disabled by flag, allowing end")
            set_conversation_state(conversation_context, ConversationState.ENDED)
            conversation_context['confirmation_flag'] = False
            metrics['alert'] = 'confirmation_bypassed_by_flag'
            
            return {
                'continue': False,
                'state': ConversationState.ENDED.value,
                'reason': 'Confirmation disabled by feature flag',
                'confirmation_prompt': None,
                'requires_confirmation': False,
                'metrics': metrics
            }
        
        return {
            'continue': True,
            'state': ConversationState.PENDING_END_CONFIRMATION.value,
            'reason': 'Mutual completion signals detected, requesting confirmation',
            'confirmation_prompt': generate_patient_confirmation_prompt(first_ask=True),
            'requires_confirmation': True,
            'metrics': metrics
        }
    
    # Continue conversation normally
    return {
        'continue': True,
        'state': ConversationState.ACTIVE.value,
        'reason': 'Conversation continuing - no mutual completion signals',
        'confirmation_prompt': None,
        'requires_confirmation': False,
        'metrics': metrics
    }


def should_continue_v2(
    conversation_context: Dict,
    last_assistant_text: str,
    last_user_text: Optional[str] = None
) -> Dict:
    """
    Determine if the conversation should continue using two-way confirmation.
    
    Implements a state machine:
    - ACTIVE: Normal conversation
    - END_SUGGESTED: Bot has proposed ending, awaiting confirmation
    - ENDED: Conversation concluded
    
    Args:
        conversation_context: Dictionary containing:
            - chat_history: List of messages
            - turn_count: Number of student turns
            - end_control_state: Current state (optional, defaults to ACTIVE)
        last_assistant_text: The most recent assistant message
        last_user_text: The most recent user message (optional)
        
    Returns:
        Dictionary with:
            - continue: bool (True = continue conversation, False = allow ending)
            - state: str (new conversation state)
            - reason: str (explanation for the decision)
            - suggest_ending: bool (whether bot should suggest ending)
    """
    chat_history = conversation_context.get('chat_history', [])
    turn_count = conversation_context.get('turn_count', 0)
    current_state = get_conversation_state(conversation_context)
    
    timestamp = datetime.now().isoformat()
    logger.info(f"[{timestamp}] Evaluating continuation: state={current_state.value}, turns={turn_count}")
    
    # State: ENDED - conversation already concluded
    if current_state == ConversationState.ENDED:
        return {
            'continue': False,
            'state': ConversationState.ENDED.value,
            'reason': 'Conversation already ended',
            'suggest_ending': False
        }
    
    # State: END_SUGGESTED - awaiting student confirmation
    if current_state == ConversationState.END_SUGGESTED:
        if last_user_text:
            # Check if student confirmed ending
            if detect_student_confirmation(last_user_text):
                logger.info(f"[{timestamp}] Student confirmed ending")
                set_conversation_state(conversation_context, ConversationState.ENDED)
                return {
                    'continue': False,  # Can end now
                    'state': ConversationState.ENDED.value,
                    'reason': 'Student confirmed ending',
                    'suggest_ending': False
                }
            else:
                # Student wants to continue - return to ACTIVE
                logger.info(f"[{timestamp}] Student wants to continue, returning to ACTIVE")
                set_conversation_state(conversation_context, ConversationState.ACTIVE)
                return {
                    'continue': True,  # Continue conversation
                    'state': ConversationState.ACTIVE.value,
                    'reason': 'Student indicated they want to continue',
                    'suggest_ending': False
                }
        else:
            # Still waiting for student response
            return {
                'continue': True,
                'state': ConversationState.END_SUGGESTED.value,
                'reason': 'Awaiting student confirmation to end',
                'suggest_ending': False
            }
    
    # State: ACTIVE - normal conversation flow
    # Check if we can suggest ending
    if can_suggest_ending(conversation_context):
        logger.info(f"[{timestamp}] Conditions met to suggest ending")
        set_conversation_state(conversation_context, ConversationState.END_SUGGESTED)
        return {
            'continue': True,  # Continue to allow suggestion
            'state': ConversationState.END_SUGGESTED.value,
            'reason': 'All MI requirements met, suggesting end to student',
            'suggest_ending': True  # Signal to generate end suggestion
        }
    
    # Continue conversation normally
    return {
        'continue': True,
        'state': ConversationState.ACTIVE.value,
        'reason': 'Conversation continuing normally',
        'suggest_ending': False
    }


def should_continue(
    conversation_state: Dict,
    last_assistant_text: str,
    last_user_text: Optional[str] = None
) -> Dict:
    """
    Determine if the conversation should continue or can be ended.
    
    LEGACY FUNCTION - Use should_continue_v2 for new implementations.
    This is kept for backward compatibility with existing code.
    
    Args:
        conversation_state: Dictionary containing:
            - chat_history: List of messages
            - turn_count: Number of student turns
        last_assistant_text: The most recent assistant message
        last_user_text: The most recent user message (optional)
        
    Returns:
        Dictionary with:
            - continue: bool (True = continue conversation, False = allow ending)
            - reason: str (explanation for the decision)
            - rewrite_text: Optional[str] (alternative text if needed)
    """
    chat_history = conversation_state.get('chat_history', [])
    turn_count = conversation_state.get('turn_count', 0)
    
    timestamp = datetime.now().isoformat()
    logger.info(f"[{timestamp}] Evaluating should_continue: turn_count={turn_count}")
    
    # Condition 1: Minimum turn threshold
    if turn_count < MIN_TURN_THRESHOLD:
        reason = f"Minimum turn threshold not met ({turn_count}/{MIN_TURN_THRESHOLD})"
        logger.info(f"[{timestamp}] {reason}")
        return {
            'continue': True,
            'reason': reason,
            'rewrite_text': None
        }
    
    # Condition 2: MI coverage requirements
    mi_coverage = check_mi_coverage(chat_history)
    missing_components = [comp for comp, present in mi_coverage.items() if not present]
    
    if missing_components:
        reason = f"MI coverage incomplete. Missing: {', '.join(missing_components)}"
        logger.info(f"[{timestamp}] {reason}")
        return {
            'continue': True,
            'reason': reason,
            'rewrite_text': None
        }
    
    # Condition 3: Student explicit confirmation
    student_confirmed = False
    if last_user_text:
        student_confirmed = detect_student_confirmation(last_user_text)
    
    if not student_confirmed:
        reason = "Student has not explicitly confirmed desire to end conversation"
        logger.info(f"[{timestamp}] {reason}")
        return {
            'continue': True,
            'reason': reason,
            'rewrite_text': None
        }
    
    # Condition 4: Explicit end token from assistant
    has_end_token = detect_end_token(last_assistant_text)
    
    if not has_end_token:
        reason = f"End token '{END_TOKEN}' not present in assistant message"
        logger.info(f"[{timestamp}] {reason}")
        return {
            'continue': True,
            'reason': reason,
            'rewrite_text': None
        }
    
    # All conditions met - allow ending
    reason = "All end conditions met: min turns, MI coverage, student confirmation, end token"
    logger.info(f"[{timestamp}] {reason}")
    return {
        'continue': False,
        'reason': reason,
        'rewrite_text': None
    }


def log_conversation_trace(
    conversation_state: Dict,
    decision: Dict,
    additional_context: Optional[Dict] = None
):
    """
    Log detailed trace information for diagnostic purposes.
    
    Args:
        conversation_state: Current conversation state
        decision: Decision from should_continue()
        additional_context: Any additional context to log
    """
    timestamp = datetime.now().isoformat()
    turn_count = conversation_state.get('turn_count', 0)
    
    trace = {
        'timestamp': timestamp,
        'turn_count': turn_count,
        'decision': decision,
        'mi_coverage': check_mi_coverage(conversation_state.get('chat_history', [])),
        'min_threshold': MIN_TURN_THRESHOLD,
        'end_token': END_TOKEN,
    }
    
    if additional_context:
        trace.update(additional_context)
    
    logger.info(f"Conversation trace: {trace}")
    return trace


def prevent_ambiguous_ending(user_message: str) -> bool:
    """
    Check if user message is an ambiguous phrase that should not trigger ending.
    
    Args:
        user_message: The user's message
        
    Returns:
        bool: True if message is ambiguous (should prevent ending)
    """
    message_lower = user_message.lower().strip()
    
    # Check if entire message is just an ambiguous phrase
    if message_lower in AMBIGUOUS_ENDING_PHRASES:
        logger.info(f"Preventing ending due to ambiguous phrase: '{user_message}'")
        return True
    
    # Check if message is very short and only contains ambiguous words
    words = message_lower.split()
    if len(words) <= 2 and all(word in AMBIGUOUS_ENDING_PHRASES for word in words):
        logger.info(f"Preventing ending due to short ambiguous message: '{user_message}'")
        return True
    
    return False


# Metrics tracking for monitoring and alerts
_termination_metrics = {
    'sessions_ended_without_confirmation': 0,
    'sessions_ended_with_confirmation': 0,
    'sessions_parked': 0,
    'confirmation_triggers': [],
    'ambiguous_responses': 0
}


def log_termination_metrics(metrics: Dict) -> None:
    """
    Log termination metrics for monitoring and alerting.
    
    Args:
        metrics: Metrics dictionary from should_continue_v3
    """
    global _termination_metrics
    
    # Track confirmation status
    if metrics.get('alert') == 'ended_without_confirmation':
        _termination_metrics['sessions_ended_without_confirmation'] += 1
        logger.error(f"ALERT: Session ended without confirmation! Metrics: {metrics}")
    elif metrics.get('confirmation_result') in ['confirmed_first_ask', 'confirmed_second_ask']:
        _termination_metrics['sessions_ended_with_confirmation'] += 1
    
    # Track parked sessions
    if metrics.get('state') == ConversationState.PARKED.value:
        _termination_metrics['sessions_parked'] += 1
    
    # Track triggers
    trigger = metrics.get('termination_trigger')
    if trigger:
        _termination_metrics['confirmation_triggers'].append({
            'trigger': trigger,
            'timestamp': metrics.get('timestamp'),
            'result': metrics.get('confirmation_result')
        })
    
    # Track ambiguous responses
    if metrics.get('confirmation_result') == 'ambiguous_first_response':
        _termination_metrics['ambiguous_responses'] += 1
    
    # Log comprehensive metrics periodically (every 10th call)
    if _termination_metrics['sessions_ended_with_confirmation'] % 10 == 0:
        logger.info(f"Termination metrics summary: {_termination_metrics}")
    
    # Alert if ANY sessions ended without confirmation
    if _termination_metrics['sessions_ended_without_confirmation'] > 0:
        logger.error(f"CRITICAL: {_termination_metrics['sessions_ended_without_confirmation']} sessions ended without confirmation!")


def get_termination_metrics() -> Dict:
    """
    Get current termination metrics for dashboards/monitoring.
    
    Returns:
        Dictionary with current metrics
    """
    return _termination_metrics.copy()


def reset_termination_metrics() -> None:
    """Reset termination metrics (for testing or periodic cleanup)."""
    global _termination_metrics
    _termination_metrics = {
        'sessions_ended_without_confirmation': 0,
        'sessions_ended_with_confirmation': 0,
        'sessions_parked': 0,
        'confirmation_triggers': [],
        'ambiguous_responses': 0
    }
