"""
End-Control Middleware for MI Chatbots

This module implements hardened conversation ending logic with two-way confirmation
to prevent premature session termination. It ensures conversations only conclude 
when all policy conditions are met:

1. Minimum turn threshold reached (configurable, default 10)
2. MI coverage requirements met (open-ended Q, reflection, autonomy, summary)
3. Two-step ending confirmation:
   - Bot suggests ending (END_SUGGESTED state)
   - Student explicitly confirms closure
4. Assistant emits explicit end token (<<END>>)

The middleware provides detailed tracing for diagnosing future incidents.

Conversation States:
- ACTIVE: Normal conversation in progress
- END_SUGGESTED: Bot has proposed ending, awaiting student confirmation
- ENDED: Conversation concluded with student confirmation
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
MIN_TURN_THRESHOLD = int(os.environ.get('MI_MIN_TURN_THRESHOLD', '10'))
END_TOKEN = os.environ.get('MI_END_TOKEN', '<<END>>')

# Conversation states
class ConversationState(Enum):
    """States for conversation flow control."""
    ACTIVE = "ACTIVE"
    END_SUGGESTED = "END_SUGGESTED"
    ENDED = "ENDED"

# Configuration - can be overridden via environment variables
MIN_TURN_THRESHOLD = int(os.environ.get('MI_MIN_TURN_THRESHOLD', '10'))
END_TOKEN = os.environ.get('MI_END_TOKEN', '<<END>>')

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
STUDENT_CONFIRMATION_PATTERNS = [
    r'\byes.*end\b',
    r'\blet\'s end\b',
    r'\bno more questions\b',
    r'\bi\'m done\b',
    r'\bthat\'s all\b',
    r'\bthank you.*that\'s enough\b',
    r'\bi think we\'re done\b',
    r'\bwe can finish\b',
    r'\bi\'m ready to finish\b',
    r'\blet\'s wrap up\b',
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
    Determine if bot can suggest ending based on conversation completeness.
    
    Checks:
    - Minimum turn threshold
    - MI coverage requirements
    
    Args:
        conversation_state: Dictionary containing chat_history and turn_count
        
    Returns:
        bool: True if conditions met for suggesting end
    """
    chat_history = conversation_state.get('chat_history', [])
    turn_count = conversation_state.get('turn_count', 0)
    
    # Check minimum turns
    if turn_count < MIN_TURN_THRESHOLD:
        logger.debug(f"Cannot suggest ending: only {turn_count}/{MIN_TURN_THRESHOLD} turns")
        return False
    
    # Check MI coverage
    mi_coverage = check_mi_coverage(chat_history)
    missing_components = [comp for comp, present in mi_coverage.items() if not present]
    
    if missing_components:
        logger.debug(f"Cannot suggest ending: missing MI components {missing_components}")
        return False
    
    logger.debug("All conditions met for suggesting ending")
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
