from datetime import datetime

def get_formatted_utc_time():
    """Returns current UTC time in MM-DD-YYYY HH:MM:SS format"""
    return datetime.utcnow().strftime("%m-%d-%y %H:%M:%S")
