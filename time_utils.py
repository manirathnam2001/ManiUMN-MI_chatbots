"""
Time utilities for consistent timezone handling across MI chatbot applications.

This module provides timezone conversion functions to ensure all timestamps
are displayed in the Minnesota timezone (America/Chicago) for consistency
across the OHI and HPV assessment applications.

Functions:
- get_formatted_utc_time(): Returns current time in Minnesota timezone
- convert_to_minnesota_time(): Converts UTC time strings to Minnesota timezone

All timestamps in the application use the format: 'YYYY-MM-DD HH:MM:SS'
"""

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
                      Can also handle strings with additional content after the timestamp
        
    Returns:
        Minnesota time string in format 'YYYY-MM-DD HH:MM:SS AM/PM TZ'
    """
    try:
        # Parse UTC time - handle case where there might be extra content after timestamp
        utc_dt = datetime.strptime(utc_time_str.split()[0] + ' ' + utc_time_str.split()[1], '%Y-%m-%d %H:%M:%S')
        utc_dt = pytz.utc.localize(utc_dt)
        
        # Convert to Minnesota time
        mn_tz = pytz.timezone('America/Chicago')
        mn_time = utc_dt.astimezone(mn_tz)
        
        # Format with AM/PM and timezone
        return mn_time.strftime('%Y-%m-%d %I:%M:%S %p %Z')
    except Exception as e:
        return f"{utc_time_str} (UTC)"
