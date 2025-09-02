from datetime import datetime

def get_formatted_utc_time():
    """Returns current UTC time in YYYY-MM-DD HH:MM:SS format"""
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")