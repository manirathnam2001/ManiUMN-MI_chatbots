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
