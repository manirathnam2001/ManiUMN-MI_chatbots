from datetime import datetime
import pytz
from typing import List, Tuple, Optional

def get_formatted_utc_time():
    """Returns current time in Minnesota timezone (America/Chicago) in YYYY-MM-DD HH:MM:SS format"""
    minnesota_tz = pytz.timezone('America/Chicago')
    mn_time = datetime.now(minnesota_tz)
    return mn_time.strftime("%Y-%m-%d %H:%M:%S")

def convert_to_minnesota_time(utc_time_str):
    """Convert UTC time string to Minnesota timezone.
    
    Args:
        utc_time_str: UTC time string in format 'YYYY-MM-DD HH:MM:SS'
        
    Returns:
        Minnesota time string in format 'YYYY-MM-DD HH:MM:SS'
    """
    minnesota_tz = pytz.timezone('America/Chicago')
    utc_dt = datetime.strptime(utc_time_str, '%Y-%m-%d %H:%M:%S')
    utc_dt = pytz.utc.localize(utc_dt)
    mn_time = utc_dt.astimezone(minnesota_tz)
    return mn_time.strftime('%Y-%m-%d %H:%M:%S')

def parse_timestamp(timestamp_str: str) -> datetime:
    """Parse a timestamp string to datetime object.
    
    Args:
        timestamp_str: Timestamp string in format 'YYYY-MM-DD HH:MM:SS'
        
    Returns:
        datetime object
    """
    return datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')

def calculate_response_time(start_time: str, end_time: str) -> float:
    """Calculate response time between two timestamps in seconds.
    
    Args:
        start_time: Start timestamp string in format 'YYYY-MM-DD HH:MM:SS'
        end_time: End timestamp string in format 'YYYY-MM-DD HH:MM:SS'
        
    Returns:
        Response time in seconds
    """
    start = parse_timestamp(start_time)
    end = parse_timestamp(end_time)
    delta = end - start
    return delta.total_seconds()

def track_conversation_times(chat_history: List[dict]) -> List[float]:
    """Track response times throughout a conversation.
    
    Args:
        chat_history: List of chat messages with 'role', 'content', and 'timestamp' fields
        
    Returns:
        List of response times in seconds for user responses
    """
    response_times = []
    last_assistant_time = None
    
    for msg in chat_history:
        timestamp = msg.get('timestamp')
        role = msg.get('role')
        
        if not timestamp:
            continue
            
        if role == 'assistant':
            last_assistant_time = timestamp
        elif role == 'user' and last_assistant_time:
            # Calculate time from last assistant message to user response
            try:
                response_time = calculate_response_time(last_assistant_time, timestamp)
                # Filter out unrealistic times (negative or > 10 minutes)
                if 0 < response_time <= 600:
                    response_times.append(response_time)
            except (ValueError, TypeError):
                pass  # Skip invalid timestamps
    
    return response_times

def get_time_category(response_time: float) -> str:
    """Categorize a response time.
    
    Args:
        response_time: Response time in seconds
        
    Returns:
        Time category string
    """
    if response_time < 10:
        return 'too_quick'
    elif 10 <= response_time <= 30:
        return 'quick_thoughtful'
    elif 30 < response_time <= 60:
        return 'reasonable'
    elif 60 < response_time <= 120:
        return 'slow_but_complete'
    elif 120 < response_time <= 300:
        return 'very_slow'
    else:
        return 'timeout'

def calculate_time_modifier(avg_response_time: float) -> float:
    """Calculate a time-based scoring modifier.
    
    Args:
        avg_response_time: Average response time in seconds
        
    Returns:
        Scoring modifier (0.0 to 0.05)
    """
    category = get_time_category(avg_response_time)
    
    modifiers = {
        'too_quick': 0.0,  # No bonus for very quick responses (might be shallow)
        'quick_thoughtful': 0.05,  # Best bonus
        'reasonable': 0.02,  # Good bonus
        'slow_but_complete': 0.01,  # Small bonus
        'very_slow': 0.0,  # No bonus
        'timeout': 0.0  # No bonus
    }
    
    return modifiers.get(category, 0.0)

def handle_timeout(response_time: float, timeout_threshold: float = 300) -> Tuple[bool, Optional[str]]:
    """Handle timeout scenarios.
    
    Args:
        response_time: Response time in seconds
        timeout_threshold: Maximum acceptable response time in seconds (default 5 minutes)
        
    Returns:
        Tuple of (is_timeout, message)
    """
    if response_time > timeout_threshold:
        return True, f"Response took {response_time:.0f}s (exceeded {timeout_threshold}s timeout)"
    return False, None

