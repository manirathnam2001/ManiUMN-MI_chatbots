"""
Time utilities for consistent timezone handling across MI chatbot applications.

This module provides timezone conversion functions to ensure all timestamps
are displayed in the Minnesota timezone (America/Chicago) for consistency
across the OHI and HPV assessment applications.

Functions:
- get_formatted_utc_time(): Returns current time in Minnesota timezone
- convert_to_minnesota_time(): Converts UTC time strings to Minnesota timezone

All timestamps in the application use the format: 'YYYY-MM-DD HH:MM:SS AM/PM CST/CDT'
"""

from datetime import datetime
import pytz

def get_formatted_utc_time():
    """Returns current time in Minnesota timezone (America/Chicago) with timezone indicator and AM/PM format"""
    minnesota_tz = pytz.timezone('America/Chicago')
    mn_time = datetime.now(minnesota_tz)
    # Format: YYYY-MM-DD HH:MM:SS AM/PM CST/CDT
    time_str = mn_time.strftime("%Y-%m-%d %I:%M:%S %p")
    tz_abbr = mn_time.strftime("%Z")  # CST or CDT
    return f"{time_str} {tz_abbr}"

def convert_to_minnesota_time(utc_time_str):
    """Convert UTC time string to Minnesota timezone with timezone indicator and AM/PM format.
    
    Args:
        utc_time_str: UTC time string in format 'YYYY-MM-DD HH:MM:SS'
        
    Returns:
        Minnesota time string in format 'YYYY-MM-DD HH:MM:SS AM/PM CST/CDT'
    """
    minnesota_tz = pytz.timezone('America/Chicago')
    utc_dt = datetime.strptime(utc_time_str, '%Y-%m-%d %H:%M:%S')
    utc_dt = pytz.utc.localize(utc_dt)
    mn_time = utc_dt.astimezone(minnesota_tz)
    # Format: YYYY-MM-DD HH:MM:SS AM/PM CST/CDT
    time_str = mn_time.strftime('%Y-%m-%d %I:%M:%S %p')
    tz_abbr = mn_time.strftime('%Z')  # CST or CDT
    return f"{time_str} {tz_abbr}"
