from datetime import datetime
import pytz

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

def calculate_response_times(chat_history, timestamps=None):
    """
    Calculate response times for a conversation (internal tracking).
    This function tracks timing metrics without displaying them to users.
    
    Args:
        chat_history: List of chat messages
        timestamps: Optional list of timestamps for each message
        
    Returns:
        dict: Time metrics including avg_response_time, total_time
    """
    if not chat_history or len(chat_history) < 2:
        return {
            'avg_response_time': 0,
            'total_time': 0,
            'response_count': 0
        }
    
    # If timestamps provided, calculate actual response times
    if timestamps and len(timestamps) == len(chat_history):
        response_times = []
        for i in range(1, len(timestamps)):
            try:
                prev_time = datetime.strptime(timestamps[i-1], '%Y-%m-%d %H:%M:%S')
                curr_time = datetime.strptime(timestamps[i], '%Y-%m-%d %H:%M:%S')
                delta = (curr_time - prev_time).total_seconds()
                if delta > 0:  # Only count positive deltas
                    response_times.append(delta)
            except:
                continue
        
        if response_times:
            return {
                'avg_response_time': sum(response_times) / len(response_times),
                'total_time': sum(response_times),
                'response_count': len(response_times)
            }
    
    # Fallback: estimate based on message count (assume ~20 seconds per response)
    user_messages = [msg for msg in chat_history if msg.get('role') == 'user']
    estimated_avg = 20.0  # Reasonable default
    
    return {
        'avg_response_time': estimated_avg,
        'total_time': estimated_avg * len(user_messages),
        'response_count': len(user_messages)
    }

def get_time_based_modifier(time_metrics):
    """
    Calculate time-based score modifier (internal use only).
    This is used by the scoring system but not displayed to users.
    
    Args:
        time_metrics: Dictionary with time-related metrics
        
    Returns:
        float: Time-based multiplier between 0.9 and 1.2
    """
    avg_response_time = time_metrics.get('avg_response_time', 20)
    
    # Ideal response time range: 10-30 seconds
    if 10 <= avg_response_time <= 30:
        return 1.2  # Bonus for well-paced responses
    elif 5 <= avg_response_time < 10:
        return 1.1  # Good response time
    elif 30 < avg_response_time <= 60:
        return 1.05  # Acceptable
    elif avg_response_time > 60:
        return 0.95  # Slower responses
    elif avg_response_time < 5:
        return 0.9  # Too fast may indicate lack of thought
    
    return 1.0  # Neutral

