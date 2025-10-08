"""
Time utilities for consistent timezone handling across MI chatbot applications.

This module provides timezone conversion functions to ensure all timestamps
are displayed in the Minnesota timezone (America/Chicago) for consistency
across the OHI and HPV assessment applications.

Functions:
- get_formatted_utc_time(): Returns current time in Minnesota timezone (24-hour format)
- get_current_utc_time(): Returns current time in UTC timezone
- get_current_minnesota_time(): Returns current time in Minnesota timezone with AM/PM
- convert_to_minnesota_time(): Converts UTC time strings to Minnesota timezone with AM/PM

Timestamp formats:
- Internal format: 'YYYY-MM-DD HH:MM:SS' (24-hour)
- Display format: 'YYYY-MM-DD HH:MM:SS AM/PM TIMEZONE' (12-hour with timezone)
"""

from datetime import datetime
import pytz

def get_formatted_utc_time():
    """Returns current time in Minnesota timezone (America/Chicago) in YYYY-MM-DD HH:MM:SS format
    
    Note: Despite the function name, this returns Minnesota time for backward compatibility.
    The timestamp is properly localized to US/Central (America/Chicago) timezone.
    """
    minnesota_tz = pytz.timezone('America/Chicago')
    mn_time = datetime.now(minnesota_tz)
    return mn_time.strftime("%Y-%m-%d %H:%M:%S")

def get_current_utc_time():
    """Returns current time in UTC timezone in YYYY-MM-DD HH:MM:SS format"""
    utc_time = datetime.now(pytz.UTC)
    return utc_time.strftime("%Y-%m-%d %H:%M:%S")

def get_current_minnesota_time():
    """Returns current time in Minnesota timezone with AM/PM and timezone abbreviation.
    
    Returns:
        Minnesota time string in format 'YYYY-MM-DD HH:MM:SS AM/PM TIMEZONE'
        Example: '2025-10-07 11:14:23 PM CDT'
    """
    minnesota_tz = pytz.timezone('America/Chicago')
    mn_time = datetime.now(minnesota_tz)
    # Format with AM/PM and timezone abbreviation
    formatted_time = mn_time.strftime('%Y-%m-%d %I:%M:%S %p')
    tz_abbr = mn_time.strftime('%Z')
    return f"{formatted_time} {tz_abbr}"

def convert_to_minnesota_time(utc_time_str):
    """Convert UTC time string to Minnesota timezone with AM/PM and timezone abbreviation.
    
    Args:
        utc_time_str: UTC time string in format 'YYYY-MM-DD HH:MM:SS'
        
    Returns:
        Minnesota time string in format 'YYYY-MM-DD HH:MM:SS AM/PM TIMEZONE'
        Example: '2025-10-07 10:50:21 PM CDT'
    """
    minnesota_tz = pytz.timezone('America/Chicago')
    utc_dt = datetime.strptime(utc_time_str, '%Y-%m-%d %H:%M:%S')
    utc_dt = pytz.utc.localize(utc_dt)
    mn_time = utc_dt.astimezone(minnesota_tz)
    # Format with AM/PM and timezone abbreviation
    formatted_time = mn_time.strftime('%Y-%m-%d %I:%M:%S %p')
    tz_abbr = mn_time.strftime('%Z')
    return f"{formatted_time} {tz_abbr}"
