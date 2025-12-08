"""
End-Control Middleware for MI Chatbots

This module implements hardened conversation ending logic to prevent premature 
session termination. It ensures conversations only conclude when all policy 
conditions are met:

1. Minimum turn threshold reached (configurable, default 10)
2. MI coverage requirements met (open-ended Q, reflection, autonomy, summary)
3. Student explicitly confirms closure
4. Assistant emits explicit end token (<<END>>)

The middleware provides detailed tracing for diagnosing future incidents.
"""

import os
import logging
import re
from typing import Dict, List, Tuple, Optional
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

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


def should_continue(
    conversation_state: Dict,
    last_assistant_text: str,
    last_user_text: Optional[str] = None
) -> Dict:
    """
    Determine if the conversation should continue or can be ended.
    
    This is the main guard function that checks all policy conditions.
    
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
