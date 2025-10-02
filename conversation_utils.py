"""
Conversation utilities for detecting end-of-conversation phrases and managing chat flow.
"""

from typing import Tuple, Optional
import re


class ConversationEndDetector:
    """Detects end-of-conversation phrases in user input."""
    
    # Common end-of-conversation phrases
    END_PHRASES = [
        # Gratitude expressions
        r'\bthank you\b',
        r'\bthanks\b',
        r'\bthank\s+you\s+so\s+much\b',
        r'\bmany\s+thanks\b',
        r'\bappreciate\s+it\b',
        r'\bi\s+appreciate\b',
        
        # Farewell expressions
        r'\bgoodbye\b',
        r'\bgood\s+bye\b',
        r'\bbye\b',
        r'\bsee\s+you\b',
        r'\btake\s+care\b',
        r'\bhave\s+a\s+good\b',
        
        # Completion expressions
        r'\bi\'?m\s+done\b',
        r'\bthat\'?s\s+all\b',
        r'\bthat\'?s\s+it\b',
        r'\bwe\'?re\s+done\b',
        r'\bi\'?m\s+finished\b',
        r'\bi\'?m\s+good\b',
        r'\ball\s+set\b',
        r'\bnothing\s+else\b',
        r'\bno\s+more\s+questions\b',
        
        # Closing expressions
        r'\bi\s+should\s+go\b',
        r'\bi\s+need\s+to\s+go\b',
        r'\bi\s+have\s+to\s+go\b',
        r'\bgotta\s+go\b',
        r'\bgot\s+to\s+go\b',
    ]
    
    # Closing responses to provide when end phrase is detected
    CLOSING_MESSAGES = [
        "Thank you for practicing your Motivational Interviewing skills with me today! "
        "Feel free to request feedback whenever you're ready by clicking 'Finish Session & Get Feedback'.",
        
        "It was great talking with you! Remember, you can get detailed feedback on our conversation "
        "by clicking the 'Finish Session & Get Feedback' button when you're ready.",
        
        "Thanks for the conversation! When you're ready, click 'Finish Session & Get Feedback' "
        "to receive a detailed analysis of your MI techniques.",
        
        "Thank you! I hope this practice session was helpful. Don't forget to get your feedback "
        "by clicking 'Finish Session & Get Feedback' before starting a new conversation.",
    ]
    
    @classmethod
    def detect_end_phrase(cls, user_input: str) -> Tuple[bool, Optional[str]]:
        """
        Detect if user input contains an end-of-conversation phrase.
        
        Args:
            user_input: The user's message
            
        Returns:
            Tuple of (is_end_phrase_detected, matched_phrase)
        """
        if not user_input:
            return False, None
        
        # Normalize input for matching
        normalized_input = user_input.lower().strip()
        
        # Check each end phrase pattern
        for pattern in cls.END_PHRASES:
            match = re.search(pattern, normalized_input, re.IGNORECASE)
            if match:
                return True, match.group(0)
        
        return False, None
    
    @classmethod
    def get_closing_message(cls, message_index: int = 0) -> str:
        """
        Get a polite closing message.
        
        Args:
            message_index: Index of the closing message to use (cycles through available messages)
            
        Returns:
            Closing message string
        """
        return cls.CLOSING_MESSAGES[message_index % len(cls.CLOSING_MESSAGES)]
    
    @classmethod
    def should_show_feedback_prompt(cls, user_input: str, message_count: int) -> bool:
        """
        Determine if feedback prompt should be shown based on conversation state.
        
        Args:
            user_input: The user's latest message
            message_count: Total number of messages in the conversation
            
        Returns:
            True if feedback prompt should be shown
        """
        # Show feedback prompt if end phrase detected
        is_end, _ = cls.detect_end_phrase(user_input)
        if is_end:
            return True
        
        # Also suggest feedback after a reasonable conversation length (e.g., 10+ exchanges)
        if message_count >= 20:  # 20 messages = roughly 10 exchanges (user + assistant)
            return True
        
        return False


def format_closing_response(detected_phrase: str, closing_message: str) -> str:
    """
    Format a complete closing response including acknowledgment of the end phrase.
    
    Args:
        detected_phrase: The specific end phrase that was detected
        closing_message: The closing message to include
        
    Returns:
        Formatted closing response
    """
    # Simple acknowledgment based on phrase type
    if any(word in detected_phrase.lower() for word in ['thank', 'appreciate']):
        acknowledgment = "You're welcome! "
    elif any(word in detected_phrase.lower() for word in ['bye', 'goodbye', 'go']):
        acknowledgment = "Take care! "
    elif any(word in detected_phrase.lower() for word in ['done', 'finished', 'all']):
        acknowledgment = "Great! "
    else:
        acknowledgment = ""
    
    return acknowledgment + closing_message
